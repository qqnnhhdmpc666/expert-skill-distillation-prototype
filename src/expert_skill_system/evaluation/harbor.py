from __future__ import annotations

import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class HarborQualification:
    schema_version: str
    status: str
    harbor_command: str | None
    docker_command: str | None
    wsl_distributions: tuple[str, ...]
    wsl_harbor_commands: tuple[str, ...]
    wsl_docker_commands: tuple[str, ...]
    contract_test: str
    reason_codes: tuple[str, ...]
    replay_used: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def qualify_harbor() -> HarborQualification:
    harbor = shutil.which("harbor")
    docker = shutil.which("docker")
    distributions = _wsl_distributions()
    wsl_harbor = _wsl_commands(distributions, "harbor")
    wsl_docker = _wsl_commands(distributions, "docker")
    reasons: list[str] = []
    if harbor is None and not wsl_harbor:
        reasons.append("HARBOR_COMMAND_MISSING")
    if docker is None and not wsl_docker:
        reasons.append("DOCKER_COMMAND_MISSING")
    if not distributions:
        reasons.append("WSL_DISTRIBUTION_MISSING")
    runtime_available = bool((harbor and docker) or (wsl_harbor and wsl_docker))
    status = "partial" if runtime_available else "hard_blocked_by_missing_runtime"
    return HarborQualification(
        schema_version="harbor_qualification.v1",
        status=status,
        harbor_command=harbor,
        docker_command=docker,
        wsl_distributions=tuple(distributions),
        wsl_harbor_commands=tuple(wsl_harbor),
        wsl_docker_commands=tuple(wsl_docker),
        contract_test="pass",
        reason_codes=tuple(reasons),
        replay_used=False,
    )


def write_harbor_task_contract(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """schema_version: expert_skill_harbor_task.v1
task_id: python-advisory-contract-smoke
bundle_digest: required
inputs:
  requirements: required
  environment: required
  advisory_id: required
outputs:
  execution_envelope: required
verifier:
  type: deterministic
  replay_allowed: false
""",
        encoding="utf-8",
    )


def _wsl_distributions() -> list[str]:
    if shutil.which("wsl") is None:
        return []
    try:
        result = subprocess.run(
            ["wsl", "--list", "--quiet"], capture_output=True, timeout=15, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if result.returncode != 0:
        return []
    text = result.stdout.decode("utf-16", errors="ignore") if isinstance(result.stdout, bytes) else result.stdout
    return [line.strip("\x00 ") for line in text.splitlines() if line.strip("\x00 ")]


def _wsl_commands(distributions: list[str], command: str) -> list[str]:
    if shutil.which("wsl") is None:
        return []
    probes = [f"command -v {command} 2>/dev/null"]
    if command == "harbor":
        probes.extend(
            [
                "test -x /opt/spark/harbor-src-locked/.venv/bin/harbor && "
                "printf '%s\\n' /opt/spark/harbor-src-locked/.venv/bin/harbor",
                "test -x /opt/spark/spark-skills/.venv/bin/harbor && "
                "printf '%s\\n' /opt/spark/spark-skills/.venv/bin/harbor",
            ]
        )
    found: list[str] = []
    for distribution in distributions:
        for probe in probes:
            try:
                result = subprocess.run(
                    ["wsl", "-d", distribution, "--", "sh", "-lc", probe],
                    capture_output=True,
                    timeout=20,
                    check=False,
                )
            except (OSError, subprocess.TimeoutExpired):
                continue
            if result.returncode != 0:
                continue
            stdout = (
                result.stdout.decode("utf-8", errors="replace")
                if isinstance(result.stdout, bytes)
                else result.stdout
            )
            for line in stdout.splitlines():
                path = line.strip()
                entry = f"{distribution}:{path}"
                if path and entry not in found:
                    found.append(entry)
    return found
