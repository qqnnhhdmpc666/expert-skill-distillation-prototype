from __future__ import annotations

import shutil
from dataclasses import dataclass


@dataclass(frozen=True)
class OpenHandsProbe:
    status: str
    executable: str | None
    reason: str


class OpenHandsHostAdapter:
    """Availability probe only; it never substitutes a local mock for qualification."""

    @staticmethod
    def probe() -> OpenHandsProbe:
        executable = shutil.which("openhands")
        if executable is None:
            return OpenHandsProbe("hard_blocked", None, "OPENHANDS_BINARY_MISSING")
        return OpenHandsProbe("available_not_qualified", executable, "SMOKE_RUN_REQUIRED")
