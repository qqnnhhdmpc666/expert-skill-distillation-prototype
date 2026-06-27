from __future__ import annotations

from pathlib import Path

from expert_skill_system.core.models import SourceRef
from expert_skill_system.evaluation import run_compiler_comparison, run_evolution_evaluation
from expert_skill_system.registry.workspace import Workspace
from expert_skill_system.sources import SourceIngestionService

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "v1_walking_skeleton"


def test_compiler_comparison_is_dev_only_and_does_not_claim_superiority(tmp_path: Path) -> None:
    workspace = Workspace.open(tmp_path / "comparison")
    ingestion = SourceIngestionService(workspace)
    ingestion.add(
        SourceRef(source_id="expert", uri=str(DATA / "expert_spec" / "python_advisory_review.md"), adapter_type="expert-document")
    )
    ingestion.add(
        SourceRef(source_id="osv", uri=str(DATA / "osv" / "PYSEC-2018-28.json"), adapter_type="osv-snapshot")
    )
    result = run_compiler_comparison(workspace, data_dir=DATA)
    assert result["compiler_superiority"] == "evaluated_on_dev_only"
    assert result["comparison_result"] == "inconclusive"
    assert all(row["condition_artifact_consumed_by_agent"] is False for row in result["rows"])


def test_evolution_records_improvement_rejection_and_original_digest_rollback(tmp_path: Path) -> None:
    workspace = Workspace.open(tmp_path / "evolution")
    result = run_evolution_evaluation(
        workspace, expert_path=DATA / "expert_spec" / "python_advisory_review.md"
    )
    assert result["safe_update_mechanism"] == "pass"
    assert result["measured_improvement"] == "partial"
    assert result["scores"]["delta"] == 1
    assert result["unsafe_update"]["active_binding_unchanged"] is True
    assert result["rollback"]["rebound_original_digest"] is True
    assert result["rollback"]["running_session_remained_pinned"] is True
