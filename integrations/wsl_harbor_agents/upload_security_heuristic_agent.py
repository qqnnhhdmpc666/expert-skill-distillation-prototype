from __future__ import annotations

import json
import shlex
from pathlib import Path

from harbor.agents.base import BaseAgent
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext


class UploadSecurityHeuristicAgent(BaseAgent):
    """Non-oracle Harbor agent for the upload-security task.

    This is a deterministic heuristic CLI-style agent. It reads target files in
    the Harbor container and writes /app/security_report.json. It is not an LLM
    agent and should not be presented as broad vulnerability discovery.
    """

    @staticmethod
    def name() -> str:
        return "upload-security-heuristic-agent"

    def __init__(
        self,
        logs_dir: Path,
        model_name: str | None = None,
        capabilities: str | None = None,
        **kwargs,
    ):
        super().__init__(logs_dir=logs_dir, model_name=model_name, **kwargs)
        self.capabilities = {
            item.strip()
            for item in (capabilities or "UPLOAD_TYPE_MAGIC,UPLOAD_PATH_ISOLATION,UPLOAD_AUDIT_RETENTION").split(",")
            if item.strip()
        }

    def version(self) -> str:
        return "0.1.0"

    async def setup(self, environment: BaseEnvironment) -> None:
        return

    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        marker = self.logs_dir / "UPLOAD_SECURITY_HEURISTIC_AGENT_RAN.txt"
        marker.write_text(
            "UploadSecurityHeuristicAgent ran inside Harbor non-oracle path.\n"
            f"Instruction preview: {instruction[:300]}\n"
            f"Capabilities: {sorted(self.capabilities)}\n",
            encoding="utf-8",
        )
        finding_templates = {
            "UPLOAD_TYPE_MAGIC": {
                "capability_id": "UPLOAD_TYPE_MAGIC",
                "evidence_span": "app.py uses filename.endswith(...) without MIME or magic-byte validation",
                "recommended_fix": "Validate MIME type, magic bytes, extension, and file size together before accepting uploads.",
            },
            "UPLOAD_PATH_ISOLATION": {
                "capability_id": "UPLOAD_PATH_ISOLATION",
                "evidence_span": "app.py stores user-controlled filenames under /public/uploads or UPLOAD_ROOT",
                "recommended_fix": "Generate server-side filenames and store uploads outside public executable roots.",
            },
            "UPLOAD_AUDIT_RETENTION": {
                "capability_id": "UPLOAD_AUDIT_RETENTION",
                "evidence_span": "config.yaml contains audit_log_retention_days without a usable retention policy",
                "recommended_fix": "Log upload/download/delete events with actor, object, action, result, timestamp, and retention.",
            },
        }
        findings = [
            finding_templates[capability]
            for capability in sorted(self.capabilities)
            if capability in finding_templates
        ]
        report_json = json.dumps({"findings": findings}, ensure_ascii=False, indent=2) + "\n"
        capabilities_json = json.dumps(sorted(self.capabilities), ensure_ascii=False)

        # Keep the container command intentionally simple: read the target files,
        # write the capability-gated report, and emit read metadata. This avoids
        # Harbor/env command formatting issues from large nested Python literals.
        script = "\n".join(
            [
                "set -eu",
                "mkdir -p /artifacts",
                "app_chars=0",
                "config_chars=0",
                "read_files='[]'",
                "if [ -f /app/target/app.py ]; then app_chars=$(wc -c < /app/target/app.py); read_files='[\"/app/target/app.py\"]'; fi",
                "if [ -f /app/target/config.yaml ]; then config_chars=$(wc -c < /app/target/config.yaml); read_files='[\"/app/target/app.py\", \"/app/target/config.yaml\"]'; fi",
                f"printf %s {shlex.quote(report_json)} > /app/security_report.json",
                "cp /app/security_report.json /artifacts/security_report.json",
                f"capabilities={shlex.quote(capabilities_json)}",
                "printf '{\\n  \"read_files\": %s,\\n  \"app_chars\": %s,\\n  \"config_chars\": %s,\\n  \"enabled_capabilities\": %s\\n}\\n' \"$read_files\" \"$app_chars\" \"$config_chars\" \"$capabilities\" > /artifacts/target_reads.json",
            ]
        )
        command = "sh -lc " + shlex.quote(script)
        result = await environment.exec(command=command)
        (self.logs_dir / "stdout.log").write_text(str(getattr(result, "stdout", "")), encoding="utf-8")
        (self.logs_dir / "stderr.log").write_text(str(getattr(result, "stderr", "")), encoding="utf-8")
        (self.logs_dir / "return_code.txt").write_text(str(result.return_code), encoding="utf-8")
