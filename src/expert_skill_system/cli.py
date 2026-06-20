from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

from .compiler import DirectToSkillIRBuilder, KnowledgeCompiler
from .compiler.models import CompilerBuild
from .core.models import SourceRef, SourceSnapshot
from .core.schema_catalog import export_schemas
from .deployment import DeploymentService, PromotionRejected
from .registry.workspace import Workspace
from .runtime import BundleBuilder, PythonAdvisoryRuntime
from .sources import SourceIngestionService


def _print(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def _workspace(state_dir: str) -> Workspace:
    return Workspace.open(Path(state_dir))


def _latest_snapshot(workspace: Workspace, adapter_type: str) -> SourceSnapshot:
    candidates = [item for item in workspace.metadata.source_snapshots() if item["adapter_type"] == adapter_type]
    if not candidates:
        raise RuntimeError(f"no registered source for adapter {adapter_type!r}")
    row = candidates[-1]
    ref = workspace.metadata.artifact_ref(row["snapshot_digest"])
    snapshot = SourceSnapshot.from_dict(workspace.artifacts.get_json(ref))
    return replace(snapshot, metadata={**snapshot.metadata, "snapshot_ref": ref.to_dict()})


def _compiler_build(payload: dict[str, Any]) -> CompilerBuild:
    return CompilerBuild(
        build_id=payload["build_id"],
        method=payload["method"],
        stage_result_refs=tuple(payload["stage_result_refs"]),
        knowledge_ir_ref=payload["knowledge_ir_ref"],
        skill_ir_ref=payload["skill_ir_ref"],
        knowledge_projection_ref=payload["knowledge_projection_ref"],
        attestation_ref=payload["attestation_ref"],
        visibility_manifest_ref=payload["visibility_manifest_ref"],
    )


def cmd_init(args: argparse.Namespace) -> int:
    workspace = _workspace(args.state_dir)
    schemas = export_schemas(workspace.root / "schemas")
    _print(
        {
            "status": "initialized",
            "state_dir": str(workspace.root),
            "metadata": str(workspace.metadata.path),
            "schema_count": len(schemas),
        }
    )
    return 0


def cmd_source_add(args: argparse.Namespace) -> int:
    workspace = _workspace(args.state_dir)
    source_id = args.source_id or f"{args.adapter}:{Path(args.path).stem}"
    metadata = {"license": args.license, "source_url": args.source_url} if args.license or args.source_url else {}
    snapshot = SourceIngestionService(workspace).add(
        SourceRef(
            source_id=source_id,
            uri=str(Path(args.path).resolve()),
            adapter_type=args.adapter,
            visibility=args.visibility,
            metadata=metadata,
        )
    )
    _print(
        {
            "status": "registered",
            "source_id": source_id,
            "raw_digest": snapshot.raw_artifact_ref["digest"],
            "snapshot_digest": snapshot.metadata["snapshot_ref"]["digest"],
            "evidence_count": len(snapshot.evidence_refs),
            "visibility": snapshot.visibility,
        }
    )
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    if args.domain != "python-advisory":
        raise RuntimeError("V1 only supports python-advisory")
    workspace = _workspace(args.state_dir)
    expert = _latest_snapshot(workspace, "expert-document")
    osv = _latest_snapshot(workspace, "osv-snapshot")
    if args.profile == "direct-to-skill-ir":
        build = DirectToSkillIRBuilder(workspace).build(expert_snapshot=expert)
        _print({"status": "baseline_built", "build": build.to_dict(), "bundle_digest": None})
        return 0
    build = KnowledgeCompiler(workspace).build(expert_snapshot=expert, structured_snapshots=(osv,))
    bundle = BundleBuilder(workspace).build(build)
    workspace.metadata.add_build_record(
        build_id=build.build_id,
        status="candidate",
        payload=build.to_dict(),
        candidate_bundle_digest=bundle.bundle_digest,
    )
    _print(
        {
            "status": "candidate_built",
            "build_id": build.build_id,
            "bundle_digest": bundle.bundle_digest,
            "skill_ir_digest": build.skill_ir_ref["digest"],
            "knowledge_projection_digest": build.knowledge_projection_ref["digest"],
            "stage_count": len(build.stage_result_refs),
        }
    )
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    workspace = _workspace(args.state_dir)
    result = DeploymentService(workspace).validate(
        args.bundle_digest,
        regression_pass=not args.fail_regression,
        negative_control_pass=not args.fail_negative_control,
    )
    _print(result.to_dict())
    return 0 if result.status == "pass" else 2


def cmd_promote(args: argparse.Namespace) -> int:
    workspace = _workspace(args.state_dir)
    try:
        binding = DeploymentService(workspace).promote(args.bundle_digest, expected_generation=args.expected_generation)
    except PromotionRejected:
        _print({"status": "rejected", "bundle_digest": args.bundle_digest})
        return 2
    _print({"status": "promoted", **binding.to_dict()})
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    if args.domain != "python-advisory":
        raise RuntimeError("V1 only supports python-advisory")
    workspace = _workspace(args.state_dir)
    envelope = PythonAdvisoryRuntime(workspace).run(
        requirements_path=Path(args.requirements),
        environment_path=Path(args.environment),
        advisory_id=args.advisory,
        bundle_digest=args.bundle_digest,
    )
    _print(envelope.to_dict())
    return 0 if envelope.execution_status == "completed" else 2


def cmd_inspect_session(args: argparse.Namespace) -> int:
    _print(_workspace(args.state_dir).metadata.get_session(args.session_id))
    return 0


def cmd_inspect_bundle(args: argparse.Namespace) -> int:
    bundle = BundleBuilder(_workspace(args.state_dir)).load(args.bundle_digest)
    _print({"bundle_digest": bundle.bundle_digest, "manifest": bundle.manifest})
    return 0


def cmd_history(args: argparse.Namespace) -> int:
    _print(_workspace(args.state_dir).metadata.deployment_history(args.binding_key))
    return 0


def cmd_rollback(args: argparse.Namespace) -> int:
    binding = DeploymentService(_workspace(args.state_dir)).rollback(
        args.bundle_digest, expected_generation=args.expected_generation
    )
    _print({"status": "rolled_back", **binding.to_dict()})
    return 0


def cmd_baselines(args: argparse.Namespace) -> int:
    workspace = _workspace(args.state_dir)
    expert = _latest_snapshot(workspace, "expert-document")
    compiler = KnowledgeCompiler(workspace).build(expert_snapshot=expert, structured_snapshots=(_latest_snapshot(workspace, "osv-snapshot"),))
    direct = DirectToSkillIRBuilder(workspace).build(expert_snapshot=expert)
    result = {
        "schema_version": "v1_baseline_diagnostic.v1",
        "conditions": {
            "no_skill": {"status": "available", "evidence_scope": "reference_backend_plumbing_only"},
            "full_material": {
                "status": "available",
                "material_digest": expert.raw_artifact_ref["digest"],
                "evidence_scope": "reference_backend_plumbing_only",
            },
            "direct_to_skill_ir": {
                "status": "built",
                "skill_ir_digest": direct.skill_ir_ref["digest"],
                "target_schema": "skill_ir.v1",
            },
            "compiler_distilled_skill": {
                "status": "built",
                "skill_ir_digest": compiler.skill_ir_ref["digest"],
                "knowledge_ir_digest": compiler.knowledge_ir_ref["digest"],
            },
            "human_authored_reference_skill": {"status": "not_available", "is_gold": False},
        },
        "claim_boundary": "ReferenceDecisionBackend parity is not AgentHost effectiveness evidence.",
    }
    ref = workspace.put_json(result, schema_version=result["schema_version"])
    _print({**result, "artifact_ref": ref.to_dict()})
    return 0


def cmd_demo(args: argparse.Namespace) -> int:
    workspace = _workspace(args.state_dir)
    root = Path(args.data_dir).resolve()
    ingestion = SourceIngestionService(workspace)
    ingestion.add(
        SourceRef(
            source_id="expert-python-advisory-review",
            uri=str(root / "expert_spec" / "python_advisory_review.md"),
            adapter_type="expert-document",
            visibility="build",
            metadata={"source_url": "locally-authored-v1-specification", "license": "project-license"},
        )
    )
    ingestion.add(
        SourceRef(
            source_id="osv-pysec-2018-28",
            uri=str(root / "osv" / "PYSEC-2018-28.json"),
            adapter_type="osv-snapshot",
            visibility="build",
            metadata={"source_url": "https://api.osv.dev/v1/vulns/PYSEC-2018-28"},
        )
    )
    expert = _latest_snapshot(workspace, "expert-document")
    osv = _latest_snapshot(workspace, "osv-snapshot")
    build = KnowledgeCompiler(workspace).build(expert_snapshot=expert, structured_snapshots=(osv,))
    bundle = BundleBuilder(workspace).build(build)
    workspace.metadata.add_build_record(
        build_id=build.build_id, status="candidate", payload=build.to_dict(), candidate_bundle_digest=bundle.bundle_digest
    )
    deployment = DeploymentService(workspace)
    attestation = deployment.validate(bundle.bundle_digest, regression_pass=True, negative_control_pass=True)
    active = workspace.metadata.get_active_binding("python-advisory")
    if active is None:
        deployment.promote(bundle.bundle_digest, expected_generation=0)
    elif active.bundle_digest != bundle.bundle_digest:
        deployment.promote(bundle.bundle_digest, expected_generation=active.generation)
    envelope = PythonAdvisoryRuntime(workspace).run(
        requirements_path=root / "runtime_inputs" / "requirements.txt",
        environment_path=root / "runtime_inputs" / "environment.json",
        advisory_id="PYSEC-2018-28",
    )
    _print(
        {
            "status": "pass" if envelope.execution_status == "completed" else envelope.execution_status,
            "bundle_digest": bundle.bundle_digest,
            "build_attestation": attestation.status,
            "session_id": envelope.session_id,
            "decision": envelope.domain_outcome.decision.__dict__ if envelope.domain_outcome and envelope.domain_outcome.decision else None,
        }
    )
    return 0 if envelope.execution_status == "completed" else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="eskill", description="Evidence-grounded expert Skill compiler and runtime")
    parser.add_argument("--state-dir", default=".eskill")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.set_defaults(func=cmd_init)

    source = sub.add_parser("source")
    source_sub = source.add_subparsers(dest="source_command", required=True)
    add = source_sub.add_parser("add")
    add.add_argument("path")
    add.add_argument("--adapter", required=True, choices=["expert-document", "requirements", "osv-snapshot"])
    add.add_argument("--source-id")
    add.add_argument("--visibility", default="build", choices=["build", "dev", "runtime", "heldout"])
    add.add_argument("--source-url")
    add.add_argument("--license")
    add.set_defaults(func=cmd_source_add)

    build = sub.add_parser("build")
    build.add_argument("domain", choices=["python-advisory"])
    build.add_argument("--profile", default="compiler-v1", choices=["compiler-v1", "direct-to-skill-ir"])
    build.add_argument("--examples")
    build.set_defaults(func=cmd_build)

    validate = sub.add_parser("validate")
    validate.add_argument("kind", choices=["bundle"])
    validate.add_argument("bundle_digest")
    validate.add_argument("--suite", default="v1-build")
    validate.add_argument("--fail-regression", action="store_true")
    validate.add_argument("--fail-negative-control", action="store_true")
    validate.set_defaults(func=cmd_validate)

    promote = sub.add_parser("promote")
    promote.add_argument("domain", choices=["python-advisory"])
    promote.add_argument("bundle_digest")
    promote.add_argument("--expected-generation", type=int, required=True)
    promote.set_defaults(func=cmd_promote)

    run = sub.add_parser("run")
    run.add_argument("domain", choices=["python-advisory"])
    run.add_argument("--requirements", required=True)
    run.add_argument("--environment", required=True)
    run.add_argument("--advisory", required=True)
    run.add_argument("--bundle-digest")
    run.set_defaults(func=cmd_run)

    inspect = sub.add_parser("inspect")
    inspect_sub = inspect.add_subparsers(dest="inspect_command", required=True)
    session = inspect_sub.add_parser("session")
    session.add_argument("session_id")
    session.set_defaults(func=cmd_inspect_session)
    bundle = inspect_sub.add_parser("bundle")
    bundle.add_argument("bundle_digest")
    bundle.set_defaults(func=cmd_inspect_bundle)

    history = sub.add_parser("history")
    history.add_argument("--binding-key", default="python-advisory")
    history.set_defaults(func=cmd_history)
    rollback = sub.add_parser("rollback")
    rollback.add_argument("domain", choices=["python-advisory"])
    rollback.add_argument("bundle_digest")
    rollback.add_argument("--expected-generation", type=int, required=True)
    rollback.set_defaults(func=cmd_rollback)
    baselines = sub.add_parser("baselines")
    baselines.set_defaults(func=cmd_baselines)
    demo = sub.add_parser("demo")
    demo.add_argument("--data-dir", default="data/v1_walking_skeleton")
    demo.set_defaults(func=cmd_demo)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except Exception as exc:
        _print({"status": "error", "error_type": type(exc).__name__, "message": str(exc)})
        return 1


if __name__ == "__main__":
    sys.exit(main())
