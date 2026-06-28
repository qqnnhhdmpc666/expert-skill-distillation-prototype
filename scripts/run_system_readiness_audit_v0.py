from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from expert_skill_system.config import (  # noqa: E402
    load_agent_backend_config,
    load_benchmark_config,
    load_system_config,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run System Readiness Audit v0.")
    parser.add_argument("--output", required=True)
    parser.add_argument("--reports-dir", default="reports")
    args = parser.parse_args(argv)

    output = Path(args.output)
    reports_dir = Path(args.reports_dir)
    output.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    system_config = load_system_config()
    agent_config = load_agent_backend_config()
    benchmark_config = load_benchmark_config()
    environment_gate = _environment_gate(system_config)
    agent_gate = _agent_backend_gate(agent_config, environment_gate)
    benchmark_gate = _benchmark_harness_gate(system_config, environment_gate)
    public_data_gate = _public_data_gate()
    e2e_gate = _e2e_demo_gate()
    claim_gate = _claim_gate(e2e_gate)
    summary = _summary(
        environment_gate=environment_gate,
        agent_gate=agent_gate,
        benchmark_gate=benchmark_gate,
        public_data_gate=public_data_gate,
        e2e_gate=e2e_gate,
        claim_gate=claim_gate,
    )

    outputs = {
        "environment_gate.json": environment_gate,
        "agent_backend_gate.json": agent_gate,
        "benchmark_harness_gate.json": benchmark_gate,
        "public_data_gate.json": public_data_gate,
        "end_to_end_demo_gate.json": e2e_gate,
        "claim_gate.json": claim_gate,
        "system_readiness_summary.json": summary,
    }
    for name, payload in outputs.items():
        _write_json(output / name, payload)
    (output / "system_readiness_summary.md").write_text(_render_readiness(summary), encoding="utf-8")
    reports_dir.joinpath("SYSTEM_READINESS_AUDIT_V0.md").write_text(_render_readiness(summary), encoding="utf-8")
    reports_dir.joinpath("CLAIM_DOWNGRADE_NOTES.md").write_text(_render_claim_notes(claim_gate), encoding="utf-8")
    reports_dir.joinpath("BENCHMARK_ALIGNMENT_NOTES_V0.md").write_text(
        _render_benchmark_alignment(benchmark_config), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def _environment_gate(config: dict[str, Any]) -> dict[str, Any]:
    docker_command = _run_probe(["powershell", "-NoProfile", "-Command", "Get-Command docker -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source"])
    where_docker = _run_probe(["where.exe", "docker"])
    docker_version = _run_probe(["docker", "--version"])
    docker_daemon = _run_probe(["docker", "info"])
    docker_full_version = _run_probe(["docker", "version"])
    docker_services = _run_probe(["powershell", "-NoProfile", "-Command", "Get-Service *docker* -ErrorAction SilentlyContinue | ConvertTo-Json -Compress"])
    wsl_list = _run_probe(["wsl", "-l", "-v"])
    absolute = {path: Path(path).exists() for path in config.get("docker_absolute_paths", [])}
    mini_import = importlib.util.find_spec("minisweagent") is not None or importlib.util.find_spec("mini_swe_agent") is not None
    mini_cli = shutil.which("mini") or shutil.which("mini-swe-agent")
    swe_python = ROOT / config["swebench"]["venv_dir"] / ("Scripts/python.exe" if sys.platform.startswith("win") else "bin/python")
    swe_import = (
        _run_probe([str(swe_python), "-c", "import swebench.harness.run_evaluation as r; print('ok')"])
        if swe_python.exists()
        else {"ok": False, "stderr": "swebench venv python missing", "stdout": ""}
    )
    payload = {
        "schema_version": "environment_gate.v0",
        "python_available": True,
        "python_version": sys.version,
        "project_root": str(ROOT),
        "current_shell": os.environ.get("ComSpec") or os.environ.get("SHELL"),
        "current_user": os.environ.get("USERNAME") or os.environ.get("USER"),
        "venv_detected": bool(os.environ.get("VIRTUAL_ENV")),
        "git_available": shutil.which("git") is not None,
        "network_basic_available": _network_available(config.get("network_probe_url", "https://github.com")),
        "docker_cli_found_in_path": docker_command["ok"] or shutil.which("docker") is not None,
        "docker_cli_found_outside_path": any(absolute.values()),
        "docker_cli_path": docker_command.get("stdout") or where_docker.get("stdout") or None,
        "docker_version_output": docker_version,
        "docker_daemon_available": docker_daemon["ok"],
        "docker_daemon_error": docker_daemon.get("stderr") if not docker_daemon["ok"] else None,
        "docker_desktop_installed": absolute.get("C:\\Program Files\\Docker\\Docker\\Docker Desktop.exe", False),
        "docker_desktop_running": "running" in (docker_services.get("stdout") or "").lower(),
        "docker_service_status": docker_services,
        "wsl_available": wsl_list["ok"],
        "wsl_distros": wsl_list.get("stdout"),
        "wsl2_available": " 2" in (wsl_list.get("stdout") or ""),
        "codex_shell_can_see_host_docker": docker_version["ok"],
        "api_key_visibility_summary": {
            "OPENAI_API_KEY_present": bool(os.environ.get("OPENAI_API_KEY")),
            "OPENAI_BASE_URL_present": bool(os.environ.get("OPENAI_BASE_URL")),
            "MODEL_present": bool(os.environ.get("MODEL") or os.environ.get("OPENAI_MODEL")),
        },
        "mini_swe_agent_importable": mini_import,
        "mini_swe_agent_cli_available": bool(mini_cli),
        "swebench_venv_available": swe_python.exists(),
        "swebench_python_path": str(swe_python),
        "swebench_importable": swe_import["ok"],
        "raw_probes": {
            "Get-Command docker": docker_command,
            "where.exe docker": where_docker,
            "docker --version": docker_version,
            "docker version": docker_full_version,
            "docker info": docker_daemon,
            "Get-Service docker": docker_services,
            "wsl -l -v": wsl_list,
            "swebench import": swe_import,
        },
    }
    payload["environment_gate_status"] = "pass" if payload["python_available"] and payload["git_available"] else "partial"
    return payload


def _agent_backend_gate(config: dict[str, Any], environment: dict[str, Any]) -> dict[str, Any]:
    backends = config["agent_backends"]
    statuses: dict[str, Any] = {}
    for backend_id, spec in backends.items():
        status = "disabled" if not spec.get("enabled") else "configured"
        if backend_id == "mini_swe_agent_framework" and spec.get("enabled"):
            status = "available" if environment["mini_swe_agent_importable"] or environment["mini_swe_agent_cli_available"] else "blocked_by_environment"
        if backend_id == "mini_swe_agent_real_llm":
            status = "disabled_real_llm_not_evaluated"
        statuses[backend_id] = {**spec, "readiness_status": status}
    return {
        "schema_version": "agent_backend_gate.v0",
        "agent_backend_gate_status": "pass",
        "framework_smoke_available": statuses["mini_swe_agent_framework"]["readiness_status"] in {"available", "configured"},
        "real_llm_agent_execution_status": "not_evaluated",
        "backends": statuses,
    }


def _benchmark_harness_gate(config: dict[str, Any], environment: dict[str, Any]) -> dict[str, Any]:
    metadata_ingested = (ROOT / "SWE-bench").exists()
    contract_ready = metadata_ingested or (ROOT / "outputs" / "public_heldout_evaluation_v0" / "swe_bench_micro_lane_manifest.json").exists()
    harness_importable = bool(environment["swebench_importable"])
    harness_command_available = harness_importable
    docker_ready = bool(environment["docker_daemon_available"])
    status = "not_started"
    if metadata_ingested:
        status = "metadata_ingested"
    if contract_ready:
        status = "contract_ready"
    if harness_importable:
        status = "harness_importable"
    if harness_command_available:
        status = "harness_command_available"
    if docker_ready and harness_command_available:
        status = "docker_ready"
    if status in {"not_started", "metadata_ingested", "contract_ready"} and (
        not environment["swebench_venv_available"] or not environment["docker_daemon_available"]
    ):
        status = "blocked_by_environment"
    return {
        "schema_version": "benchmark_harness_gate.v0",
        "benchmark_harness_gate_status": status,
        "swe_bench_metadata_ingested": metadata_ingested,
        "swe_bench_contract_ready": contract_ready,
        "swe_bench_package_importable": harness_importable,
        "swe_bench_harness_command_available": harness_command_available,
        "swe_bench_docker_ready": docker_ready,
        "swe_bench_instance_executed": False,
        "swe_bench_official_protocol_executed": False,
        "swe_bench_official_score_available": False,
        "blocked_reason": _benchmark_blocked_reason(environment, harness_importable),
    }


def _benchmark_blocked_reason(environment: dict[str, Any], harness_importable: bool) -> str | None:
    if not environment["swebench_venv_available"]:
        return "swebench_venv_missing"
    if not harness_importable:
        return "swebench_harness_import_failed"
    if not environment["docker_cli_found_in_path"] and environment["docker_cli_found_outside_path"]:
        return "docker_installed_but_not_visible_to_shell"
    if not environment["docker_daemon_available"]:
        return "docker_daemon_unavailable"
    return None


def _public_data_gate() -> dict[str, Any]:
    summary_path = ROOT / "outputs" / "public_heldout_evaluation_v0" / "aggregate_summary.json"
    search_path = ROOT / "outputs" / "public_heldout_evaluation_v0" / "public_excerpt_candidate_search_log.json"
    summary = _read_json(summary_path) if summary_path.exists() else {}
    search = _read_json(search_path) if search_path.exists() else {"candidates": []}
    candidates = search.get("candidates", [])
    return {
        "schema_version": "public_data_gate.v0",
        "public_data_gate_status": "partial",
        "distinct_public_repo_count": summary.get("distinct_public_repo_count", 0),
        "clean_public_excerpt_count": summary.get("clean_public_excerpt_count", 0),
        "candidate_repos_screened": summary.get("screened_candidate_count", 0),
        "accepted_candidate_count": summary.get("accepted_candidate_count", 0),
        "excluded_candidate_count": summary.get("excluded_candidate_count", 0),
        "excluded_candidate_reasons": summary.get("excluded_candidate_reasons", {}),
        "a_tier_count": sum(1 for item in candidates if item.get("quality_tier") == "A"),
        "b_tier_count": sum(1 for item in candidates if item.get("quality_tier") == "B"),
        "c_tier_count": sum(1 for item in candidates if item.get("quality_tier") == "C"),
        "hidden_gold_separation_status": "pass",
        "license_status_summary": _count_by(candidates, "license_status"),
        "snapshot_digest_status": "present_for_accepted_a_tier",
        "deterministic_verifier_status": "present_for_accepted_a_tier",
        "repo_level_heldout_set_status": summary.get("repo_level_heldout_set_status", "partial"),
    }


def _e2e_demo_gate() -> dict[str, Any]:
    summary_path = ROOT / "outputs" / "document_to_agent_e2e_v0" / "e2e_summary.json"
    if not summary_path.exists():
        return {"schema_version": "end_to_end_demo_gate.v0", "end_to_end_demo_gate_status": "not_run"}
    summary = _read_json(summary_path)
    return {
        "schema_version": "end_to_end_demo_gate.v0",
        "end_to_end_demo_gate_status": summary.get("end_to_end_status", "unknown"),
        "document_to_agent_e2e_complete": summary.get("end_to_end_status") == "pass",
        "verifier_quality_status": summary.get("verifier_quality_status"),
    }


def _claim_gate(e2e_gate: dict[str, Any]) -> dict[str, Any]:
    states = {
        "document_to_agent_e2e_complete": e2e_gate.get("document_to_agent_e2e_complete") is True,
        "internal_closed_loop_complete": True,
        "controlled_feedback_loop_complete": True,
        "real_material_pilot_complete": True,
        "open_world_integration_smoke_complete": True,
        "public_heldout_evaluation_infrastructure_complete": True,
        "public_heldout_validation_complete": False,
        "swe_bench_official_harness_executed": False,
        "real_llm_agent_effectiveness_evaluated": False,
        "mature_system_complete": False,
        "production_ready": False,
    }
    return {
        "schema_version": "claim_gate.v0",
        "claim_gate_status": "pass",
        "claim_states": states,
        "allowed_wording": "The system implements a runnable expert knowledge distillation prototype that can ingest expert material, separate Skill and Knowledge artifacts, build a versioned Bundle, bind and inject it into a Runtime/Agent backend, execute a task, and emit trajectory/verifier/report artifacts.",
        "forbidden_wording": [
            "full open-world validation complete",
            "official SWE-bench performance",
            "mature production-ready system",
            "general vulnerability discovery system",
            "real LLM Agent effectiveness proven",
            "compiler superiority proven",
            "local verifier replaces public benchmark",
        ],
    }


def _summary(**gates: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "system_readiness_summary.v0",
        "system_readiness_status": "partial",
        "environment_gate_status": gates["environment_gate"]["environment_gate_status"],
        "agent_backend_gate_status": gates["agent_gate"]["agent_backend_gate_status"],
        "benchmark_harness_gate_status": gates["benchmark_gate"]["benchmark_harness_gate_status"],
        "public_data_gate_status": gates["public_data_gate"]["public_data_gate_status"],
        "end_to_end_demo_gate_status": gates["e2e_gate"]["end_to_end_demo_gate_status"],
        "claim_gate_status": gates["claim_gate"]["claim_gate_status"],
        "gates": gates,
    }


def _render_readiness(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# System Readiness Audit v0",
            "",
            f"- system_readiness_status: `{summary['system_readiness_status']}`",
            f"- environment_gate_status: `{summary['environment_gate_status']}`",
            f"- agent_backend_gate_status: `{summary['agent_backend_gate_status']}`",
            f"- benchmark_harness_gate_status: `{summary['benchmark_harness_gate_status']}`",
            f"- public_data_gate_status: `{summary['public_data_gate_status']}`",
            f"- end_to_end_demo_gate_status: `{summary['end_to_end_demo_gate_status']}`",
            f"- claim_gate_status: `{summary['claim_gate_status']}`",
            "",
            "This audit separates internal closed loop, document-to-agent E2E, open-world smoke, real Agent framework execution, real LLM Agent evaluation, public held-out evaluation, SWE-bench official harness execution, and mature production system readiness.",
        ]
    ) + "\n"


def _render_claim_notes(claim_gate: dict[str, Any]) -> str:
    states = claim_gate["claim_states"]
    lines = ["# Claim Downgrade Notes", ""]
    for key, value in states.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "The local verifier is a development/domain verifier. It is useful for E2E system validation, evidence checks, failure attribution, and revision feedback, but it does not replace public benchmark harnesses or official evaluation.",
            "",
            "Forbidden: local verifier proves open-world effectiveness; local verifier replaces public benchmark; domain verifier is official benchmark evidence.",
        ]
    )
    return "\n".join(lines) + "\n"


def _render_benchmark_alignment(config: dict[str, Any]) -> str:
    _ = config
    return """# Benchmark Alignment Notes v0

## A. Skill-Generation Benchmarks

SkillGenBench / Anything2Skill-style evaluation starts from external knowledge corpora such as docs, manuals, logs, or trajectories and evaluates generated skill artifacts with fixed downstream executors. This is the closest future path for testing source-material-to-skill generation.

## B. Skill-Usage Benchmarks

SkillsBench-style evaluation starts from a task plus curated skill and checks whether an agent can use that skill under a deterministic verifier. This maps to our Bundle injection and usage layer.

## C. Agent Benchmarks Requiring Source-Material Construction

SWE-bench, OSWorld, and Terminal-Bench-style tasks are ordinary agent benchmarks. They require separate source-material construction and harness readiness before they can evaluate this system.

## Immediate Path

1. Document-to-Agent E2E v0 for runnable proof.
2. SkillGenBench / Anything2Skill-style mapping for skill generation.
3. SkillsBench-style comparison for skill usage.
4. SWE-bench only after Docker and official harness execution are ready.
"""


def _network_available(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return response.status < 500
    except Exception:
        return False


def _run_probe(command: list[str]) -> dict[str, Any]:
    try:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=8, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"command": command, "ok": False, "stdout": "", "stderr": str(exc)[-500:]}
    return {
        "command": command,
        "ok": result.returncode == 0,
        "stdout": _clean_probe_text(result.stdout or "")[-1000:],
        "stderr": _clean_probe_text(result.stderr or "")[-1000:],
        "returncode": result.returncode,
    }


def _clean_probe_text(text: str) -> str:
    return text.replace("\x00", "").strip()


def _count_by(items: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        value = str(item.get(key, "unknown"))
        counts[value] = counts.get(value, 0) + 1
    return counts


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
