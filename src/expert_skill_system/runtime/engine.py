from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from packaging.markers import InvalidMarker, Marker
from packaging.utils import canonicalize_name
from packaging.version import InvalidVersion, Version

from ..core.models import (
    ArtifactRef,
    DomainDecision,
    DomainOutcome,
    ExecutionEnvelope,
    FailureDetail,
    KnowledgeQuery,
    SourceRef,
)
from ..registry.artifacts import ArtifactCorruptionError
from ..registry.workspace import Workspace
from ..sources import OSVSnapshotProvider, SourceIngestionService
from .bundle import BundleBuilder, ReleaseBundle


class PythonAdvisoryRuntime:
    binding_key = "python-advisory"

    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace
        self.bundles = BundleBuilder(workspace)

    def run(
        self,
        *,
        requirements_path: Path,
        environment_path: Path,
        advisory_id: str,
        bundle_digest: str | None = None,
    ) -> ExecutionEnvelope:
        session_id = f"session-{uuid.uuid4()}"
        resolved_digest = bundle_digest
        if resolved_digest is None:
            active = self.workspace.metadata.get_active_binding(self.binding_key)
            if active is None:
                return self._unstarted_failure(session_id, "blocked", "NO_ACTIVE_BUNDLE")
            resolved_digest = active.bundle_digest
        self.workspace.metadata.start_session(
            session_id=session_id,
            binding_key=self.binding_key,
            bundle_digest=resolved_digest,
            payload={"advisory_id": advisory_id, "phase": "started"},
        )
        try:
            bundle = self.bundles.load(resolved_digest)
        except (FileNotFoundError, ArtifactCorruptionError, KeyError, ValueError) as exc:
            envelope = ExecutionEnvelope(
                execution_status="runtime_failure",
                failure=FailureDetail(category="bundle_integrity", reason_codes=(type(exc).__name__,), retryable=False),
                session_id=session_id,
                bundle_digest=resolved_digest,
            )
            self._finish(session_id, envelope, {"error": str(exc)})
            return envelope
        try:
            envelope, trace = self._execute(
                session_id=session_id,
                bundle=bundle,
                requirements_path=requirements_path,
                environment_path=environment_path,
                advisory_id=advisory_id,
            )
        except Exception as exc:  # runtime boundary: provider/schema failures must not become domain unresolved
            envelope = ExecutionEnvelope(
                execution_status="runtime_failure",
                failure=FailureDetail(category="runtime_exception", reason_codes=(type(exc).__name__,), retryable=False),
                session_id=session_id,
                bundle_digest=resolved_digest,
            )
            trace = {"error": str(exc)}
        self._finish(session_id, envelope, trace)
        return envelope

    def _execute(
        self,
        *,
        session_id: str,
        bundle: ReleaseBundle,
        requirements_path: Path,
        environment_path: Path,
        advisory_id: str,
    ) -> tuple[ExecutionEnvelope, dict[str, Any]]:
        manifest = bundle.manifest
        binding_refs = manifest.get("knowledge_access_binding_refs", [])
        if not binding_refs:
            return self._blocked(session_id, bundle.bundle_digest, "KNOWLEDGE_BINDING_UNAVAILABLE")
        binding_ref = ArtifactRef.from_dict(binding_refs[0])
        binding = self.workspace.artifacts.get_json(binding_ref)
        if binding.get("freshness_mode") != "immutable_snapshot":
            return self._blocked(session_id, bundle.bundle_digest, "KNOWLEDGE_FRESHNESS_UNSATISFIED")
        index_ref = ArtifactRef.from_dict(binding["native_index_ref"])
        index_path = self._materialize_index(index_ref)
        provider = OSVSnapshotProvider(index_path, binding["snapshot_ref"]["digest"])
        query = KnowledgeQuery(
            provider_id=provider.provider_id,
            query_type="advisory_package",
            parameters={"advisory_id": advisory_id},
        )
        evidence = provider.query(query)
        if not evidence.evidence_units:
            decision = DomainDecision(
                dependency_name="",
                normalized_name="",
                resolved_version=None,
                advisory_id=advisory_id,
                verdict="unresolved",
                reason_codes=("ADVISORY_NOT_FOUND",),
                evidence_refs=({"result_digest": evidence.result_digest},),
            )
            return self._completed(session_id, bundle.bundle_digest, decision), self._trace(bundle, query, evidence, decision)

        requirements = SourceIngestionService(self.workspace).add(
            SourceRef(
                source_id=f"requirements:{session_id}",
                uri=str(requirements_path),
                adapter_type="requirements",
                visibility="runtime",
            )
        )
        if requirements.metadata.get("diagnostics"):
            outcome = DomainOutcome(task_status="parse_error", parse_diagnostics=tuple(requirements.metadata["diagnostics"]))
            envelope = ExecutionEnvelope(
                execution_status="completed",
                domain_outcome=outcome,
                session_id=session_id,
                bundle_digest=bundle.bundle_digest,
            )
            return envelope, {**self._trace(bundle, query, evidence, None), "parse_diagnostics": requirements.metadata["diagnostics"]}
        inventory = self._load_inventory(requirements)
        environment = json.loads(environment_path.read_text(encoding="utf-8"))
        record = evidence.evidence_units[0]
        package_name = canonicalize_name(str(record["package_name"]))
        requirement = inventory.get(package_name)
        if requirement is None:
            decision = self._decision(record, advisory_id, None, "advisory_not_applicable", ("PACKAGE_NOT_PRESENT",), evidence)
        else:
            marker_status = self._marker_status(requirement.get("marker"), environment)
            if marker_status == "false":
                decision = self._decision(record, advisory_id, requirement, "advisory_not_applicable", ("MARKER_FALSE",), evidence)
            elif marker_status == "unknown":
                decision = self._decision(record, advisory_id, requirement, "unresolved", ("MARKER_UNKNOWN",), evidence)
            else:
                applicability = _version_applicability(requirement["version"], record["ranges"], record["versions"])
                if applicability is None:
                    decision = self._decision(record, advisory_id, requirement, "unresolved", ("VERSION_UNKNOWN",), evidence)
                elif applicability:
                    decision = self._decision(record, advisory_id, requirement, "advisory_applicable", ("VERSION_IN_RANGE",), evidence)
                else:
                    decision = self._decision(record, advisory_id, requirement, "advisory_not_applicable", ("VERSION_OUT_OF_RANGE",), evidence)
        return self._completed(session_id, bundle.bundle_digest, decision), self._trace(bundle, query, evidence, decision)

    def _load_inventory(self, snapshot) -> dict[str, dict[str, Any]]:
        inventory: dict[str, dict[str, Any]] = {}
        for payload in snapshot.evidence_refs:
            unit = self.workspace.artifacts.get_json(ArtifactRef.from_dict(payload))
            inventory[unit["attributes"]["normalized_name"]] = unit["attributes"]
        return inventory

    @staticmethod
    def _marker_status(marker: str | None, environment: dict[str, str]) -> str:
        if not marker:
            return "true"
        try:
            return "true" if Marker(marker).evaluate(environment=environment) else "false"
        except (InvalidMarker, KeyError, ValueError):
            return "unknown"

    @staticmethod
    def _decision(record, advisory_id, requirement, verdict, reasons, evidence) -> DomainDecision:
        return DomainDecision(
            dependency_name=str(record["package_name"]),
            normalized_name=canonicalize_name(str(record["package_name"])),
            resolved_version=requirement.get("version") if requirement else None,
            advisory_id=advisory_id,
            verdict=verdict,
            reason_codes=reasons,
            evidence_refs=(
                {
                    "snapshot_digest": evidence.snapshot_digest,
                    "query_contract_digest": evidence.query_contract_digest,
                    "result_digest": evidence.result_digest,
                },
            ),
        )

    @staticmethod
    def _completed(session_id: str, bundle_digest: str, decision: DomainDecision) -> ExecutionEnvelope:
        return ExecutionEnvelope(
            execution_status="completed",
            domain_outcome=DomainOutcome(task_status="decision", decision=decision),
            session_id=session_id,
            bundle_digest=bundle_digest,
        )

    @staticmethod
    def _blocked(session_id: str, bundle_digest: str, reason: str) -> tuple[ExecutionEnvelope, dict[str, Any]]:
        envelope = ExecutionEnvelope(
            execution_status="blocked",
            failure=FailureDetail(category="knowledge_unavailable", reason_codes=(reason,), retryable=False),
            session_id=session_id,
            bundle_digest=bundle_digest,
        )
        return envelope, {"reason_code": reason}

    @staticmethod
    def _unstarted_failure(session_id: str, status: str, reason: str) -> ExecutionEnvelope:
        return ExecutionEnvelope(
            execution_status=status,  # type: ignore[arg-type]
            failure=FailureDetail(category="binding", reason_codes=(reason,), retryable=False),
            session_id=session_id,
            bundle_digest="sha256:" + "0" * 64,
        )

    def _materialize_index(self, ref: ArtifactRef) -> Path:
        target = self.workspace.root / "runtime_indexes" / f"{ref.digest.removeprefix('sha256:')}.sqlite"
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = self.workspace.artifacts.get_bytes(ref)
        if not target.exists() or target.read_bytes() != payload:
            target.write_bytes(payload)
        return target

    @staticmethod
    def _trace(bundle: ReleaseBundle, query: KnowledgeQuery, evidence, decision) -> dict[str, Any]:
        return {
            "schema_version": "execution_trace.v1",
            "bundle_digest": bundle.bundle_digest,
            "skill_ir_refs": bundle.manifest["skill_ir_refs"],
            "knowledge_projection_refs": bundle.manifest["knowledge_projection_refs"],
            "knowledge_access_binding_refs": bundle.manifest["knowledge_access_binding_refs"],
            "query": query.to_dict(),
            "evidence_envelope": evidence.to_dict(),
            "decision": decision.__dict__ if decision else None,
        }

    def _finish(self, session_id: str, envelope: ExecutionEnvelope, trace: dict[str, Any]) -> None:
        trace_ref = self.workspace.put_json(trace, schema_version="execution_trace.v1")
        self.workspace.metadata.complete_session(
            session_id=session_id,
            status=envelope.execution_status,
            payload={"execution_envelope": envelope.to_dict(), "trace_ref": trace_ref.to_dict()},
        )


def _version_applicability(version_text: str, ranges: list[dict[str, Any]], versions: list[str]) -> bool | None:
    try:
        version = Version(version_text)
    except InvalidVersion:
        return None
    if version_text in versions:
        return True
    supported_ranges = [item for item in ranges if item.get("type") in {"ECOSYSTEM", "SEMVER"}]
    if ranges and not supported_ranges:
        return None
    affected = False
    for range_item in supported_ranges:
        current = False
        for event in range_item.get("events", []):
            try:
                if "introduced" in event and (event["introduced"] == "0" or version >= Version(event["introduced"])):
                    current = True
                if "fixed" in event and version >= Version(event["fixed"]):
                    current = False
                if "last_affected" in event and version > Version(event["last_affected"]):
                    current = False
                if "limit" in event and version >= Version(event["limit"]):
                    current = False
            except InvalidVersion:
                return None
        affected = affected or current
    return affected
