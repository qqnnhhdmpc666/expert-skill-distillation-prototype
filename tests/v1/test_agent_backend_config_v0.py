from __future__ import annotations

from expert_skill_system.config import load_agent_backend_config


def test_agent_backend_config_separates_framework_and_real_llm() -> None:
    config = load_agent_backend_config()
    backends = config["agent_backends"]
    assert backends["deterministic_reference"]["enabled"] is True
    assert backends["deterministic_reference"]["claim_level"] == "deterministic_runtime"
    assert backends["mini_swe_agent_framework"]["enabled"] is True
    assert backends["mini_swe_agent_framework"]["claim_level"] == "framework_smoke"
    assert backends["mini_swe_agent_real_llm"]["enabled"] is False
    assert backends["mini_swe_agent_real_llm"]["claim_level"] == "real_llm_agent_execution"
    assert backends["swe_agent"]["status"] == "not_integrated"
    assert backends["openhands"]["status"] == "not_integrated"
