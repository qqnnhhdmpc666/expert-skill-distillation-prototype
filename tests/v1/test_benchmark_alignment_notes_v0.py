from __future__ import annotations

from pathlib import Path

from scripts.run_system_readiness_audit_v0 import main as run_audit


def test_benchmark_alignment_notes_classify_future_paths(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    assert run_audit(["--output", str(tmp_path / "audit"), "--reports-dir", str(reports)]) == 0
    notes = (reports / "BENCHMARK_ALIGNMENT_NOTES_V0.md").read_text(encoding="utf-8")
    assert "SkillGenBench" in notes
    assert "Anything2Skill" in notes
    assert "SkillsBench" in notes
    assert "SWE-bench" in notes
    assert "OSWorld" in notes
    assert "Terminal-Bench" in notes
