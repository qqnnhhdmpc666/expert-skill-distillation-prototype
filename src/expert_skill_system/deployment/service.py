from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Literal

from ..core.models import ActiveBinding, ArtifactRef, DeploymentEvent, utc_now
from ..registry.workspace import Workspace
from ..runtime.bundle import BundleBuilder


class PromotionRejected(RuntimeError):
    pass


@dataclass(frozen=True)
class EvaluationAttestation:
    schema_version: str
    attestation_id: str
    subject_digest: str
    status: Literal["pass", "fail"]
    checks: tuple[dict[str, Any], ...]
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "attestation_id": self.attestation_id,
            "subject_digest": self.subject_digest,
            "status": self.status,
            "checks": list(self.checks),
            "created_at": self.created_at,
        }


class DeploymentService:
    binding_key = "python-advisory"

    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace
        self.bundles = BundleBuilder(workspace)

    def validate(
        self,
        bundle_digest: str,
        *,
        regression_pass: bool,
        negative_control_pass: bool,
    ) -> EvaluationAttestation:
        checks: list[dict[str, Any]] = []
        try:
            bundle = self.bundles.load(bundle_digest)
            checks.append({"check": "bundle_closure", "status": "pass"})
        except Exception as exc:
            checks.append({"check": "bundle_closure", "status": "fail", "reason": type(exc).__name__})
            return self._record(bundle_digest, checks)

        manifest = bundle.manifest
        skill_ref = ArtifactRef.from_dict(manifest["skill_ir_refs"][0])
        skill = self.workspace.artifacts.get_json(skill_ref)
        provenance = self.workspace.artifacts.get_json(ArtifactRef.from_dict(manifest["provenance_manifest_ref"]))
        build = self.workspace.metadata.get_build_record(provenance["compiler_build_id"])
        build_payload = build["payload"]
        build_attestation = self.workspace.artifacts.get_json(ArtifactRef.from_dict(build_payload["attestation_ref"]))
        expected_subjects = {
            "knowledge_ir": manifest["knowledge_ir_ref"]["digest"],
            "skill_ir": skill_ref.digest,
            "knowledge_projection": manifest["knowledge_projection_refs"][0]["digest"],
        }
        subjects_match = all(
            build_attestation.get("subject_digests", {}).get(key) == digest for key, digest in expected_subjects.items()
        )
        checks.append({"check": "attestation_subject_identity", "status": "pass" if subjects_match else "fail"})
        checks.append(
            {
                "check": "build_source_grounding",
                "status": "pass" if build_attestation.get("eligible_for_candidate") is True else "fail",
            }
        )
        scope_ok = skill.get("invocation", {}).get("task_family") == "python-advisory"
        checks.append({"check": "scope_containment", "status": "pass" if scope_ok else "fail"})
        permission = self.workspace.artifacts.get_json(ArtifactRef.from_dict(manifest["permission_request_ref"]))
        permission_ok = permission == {
            "schema_version": "permission_request.v1",
            "filesystem": "read_declared_inputs",
            "network": "none",
        }
        checks.append({"check": "permission_non_expansion", "status": "pass" if permission_ok else "fail"})
        checks.append({"check": "regression_suite", "status": "pass" if regression_pass else "fail"})
        checks.append({"check": "negative_control", "status": "pass" if negative_control_pass else "fail"})
        return self._record(bundle_digest, checks)

    def promote(self, bundle_digest: str, *, expected_generation: int) -> ActiveBinding:
        attestation = self.workspace.metadata.latest_evaluation_attestation(bundle_digest)
        if attestation is None or attestation["status"] != "pass":
            self.workspace.metadata.record_rejection(
                binding_key=self.binding_key,
                candidate_digest=bundle_digest,
                reason_codes=("MISSING_PASSING_EVALUATION_ATTESTATION",),
            )
            raise PromotionRejected(bundle_digest)
        self.bundles.load(bundle_digest)
        return self.workspace.metadata.change_binding(
            binding_key=self.binding_key,
            target_digest=bundle_digest,
            expected_generation=expected_generation,
            event_type="promote",
            reason_codes=("EVALUATION_ATTESTATION_PASS",),
        )

    def reject(self, bundle_digest: str) -> DeploymentEvent:
        attestation = self.workspace.metadata.latest_evaluation_attestation(bundle_digest)
        reason_codes = tuple(
            f"{item['check'].upper()}_FAILED"
            for item in (attestation["payload"]["checks"] if attestation else [])
            if item["status"] == "fail"
        ) or ("NO_EVALUATION",)
        return self.workspace.metadata.record_rejection(
            binding_key=self.binding_key,
            candidate_digest=bundle_digest,
            reason_codes=reason_codes,
        )

    def rollback(self, target_digest: str, *, expected_generation: int) -> ActiveBinding:
        self.bundles.load(target_digest)
        return self.workspace.metadata.change_binding(
            binding_key=self.binding_key,
            target_digest=target_digest,
            expected_generation=expected_generation,
            event_type="rollback",
            reason_codes=("EXPLICIT_FULL_BUNDLE_ROLLBACK",),
        )

    def _record(self, subject_digest: str, checks: list[dict[str, Any]]) -> EvaluationAttestation:
        status = "pass" if checks and all(item["status"] == "pass" for item in checks) else "fail"
        attestation = EvaluationAttestation(
            schema_version="evaluation_attestation.v1",
            attestation_id=f"eval-{uuid.uuid4()}",
            subject_digest=subject_digest,
            status=status,
            checks=tuple(checks),
            created_at=utc_now(),
        )
        ref = self.workspace.put_json(attestation.to_dict(), schema_version=attestation.schema_version)
        payload = {**attestation.to_dict(), "artifact_ref": ref.to_dict()}
        self.workspace.metadata.add_evaluation_attestation(
            attestation_id=attestation.attestation_id,
            subject_digest=subject_digest,
            status=status,
            payload=payload,
        )
        return attestation
