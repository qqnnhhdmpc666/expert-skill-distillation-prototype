from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from expert_skill_system.compiler import KnowledgeCompiler
from expert_skill_system.core.models import SourceRef
from expert_skill_system.evaluation.osv_benchmark import evaluate_predictions
from expert_skill_system.registry.workspace import Workspace
from expert_skill_system.runtime import BundleBuilder, PythonAdvisoryRuntime
from expert_skill_system.sources import SourceIngestionService


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data/public_osv_pilot")
    parser.add_argument("--state-dir", default=".tmp/public-osv-pilot-state")
    parser.add_argument("--output", default="outputs/public_osv_pilot/reference_runtime_results.json")
    args = parser.parse_args()
    data_dir = Path(args.data_dir)
    state_dir = Path(args.state_dir)
    if state_dir.exists():
        shutil.rmtree(state_dir)
    workspace = Workspace.open(state_dir)
    ingestion = SourceIngestionService(workspace)
    expert = ingestion.add(
        SourceRef(
            source_id="public-osv-pilot-expert-spec",
            uri=str(Path("data/v1_walking_skeleton/expert_spec/python_advisory_review.md").resolve()),
            adapter_type="expert-document",
            visibility="build",
        )
    )
    osv = ingestion.add(
        SourceRef(
            source_id="public-osv-pilot-snapshot",
            uri=str((data_dir / "osv_snapshot.json").resolve()),
            adapter_type="osv-snapshot",
            visibility="build",
        )
    )
    build = KnowledgeCompiler(workspace).build(expert_snapshot=expert, structured_snapshots=(osv,))
    bundle = BundleBuilder(workspace).build(build)
    runtime = PythonAdvisoryRuntime(workspace)
    inputs = read_jsonl(data_dir / "inputs.jsonl")
    gold = read_jsonl(data_dir / "gold.jsonl")
    run_dir = state_dir / "pilot_inputs"
    run_dir.mkdir(parents=True, exist_ok=True)
    predictions: list[dict[str, Any]] = []
    for case in inputs:
        case_dir = run_dir / case["case_id"]
        case_dir.mkdir(parents=True, exist_ok=True)
        requirements = case_dir / "requirements.txt"
        environment = case_dir / "environment.json"
        requirements.write_text(str(case["requirement"]) + "\n", encoding="utf-8")
        environment.write_text(json.dumps(case["environment"], sort_keys=True) + "\n", encoding="utf-8")
        envelope = runtime.run(
            requirements_path=requirements,
            environment_path=environment,
            advisory_id=str(case["advisory_id"]),
            bundle_digest=bundle.bundle_digest,
        )
        payload = envelope.to_dict()
        decision = (payload.get("domain_outcome") or {}).get("decision") or {}
        predictions.append(
            {
                "case_id": case["case_id"],
                "execution_status": payload["execution_status"],
                "verdict": decision.get("verdict"),
                "reason_codes": decision.get("reason_codes", []),
                "session_id": payload["session_id"],
                "bundle_digest": payload["bundle_digest"],
            }
        )
    evaluation = evaluate_predictions(inputs, gold, predictions)
    result = {
        "schema_version": "public_osv_reference_runtime_pilot.v1",
        "method": "compiler_distilled_bundle_with_reference_decision_backend",
        "bundle_digest": bundle.bundle_digest,
        "skill_ir_digest": build.skill_ir_ref["digest"],
        "knowledge_projection_digest": build.knowledge_projection_ref["digest"],
        "predictions": predictions,
        "evaluation": evaluation,
        "claim_boundary": (
            "Fresh public-data reference-runtime evidence only; not AgentHost effectiveness or compiler superiority."
        ),
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), **{key: evaluation[key] for key in ("case_count", "passed_count", "accuracy", "false_safe_count")}}, indent=2))
    return 0 if evaluation["passed_count"] == evaluation["case_count"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

