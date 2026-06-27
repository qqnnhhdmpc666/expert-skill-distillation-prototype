from __future__ import annotations

from scripts.diagnose_deepseek_auth import _sanitize, diagnose


def test_diagnosis_selects_deepseek_before_openai_and_never_returns_key(monkeypatch) -> None:
    secret = "sk-deepseek-secret-value"
    monkeypatch.setenv("DEEPSEEK_API_KEY", secret)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-secret-value")
    result = diagnose(base_url="https://api.deepseek.com", model="deepseek-chat", timeout=1, perform_request=False)
    assert result["selected_variable"] == "DEEPSEEK_API_KEY"
    assert secret not in str(result)
    assert result["variables"][0]["length"] == len(secret)


def test_openai_variable_is_never_selected_as_deepseek_fallback(monkeypatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-secret-value")
    result = diagnose(base_url="https://api.deepseek.com", model="deepseek-chat", timeout=1, perform_request=True)
    assert result["classification"] == "wrong_var"
    assert result["selected_variable"] is None
    assert result["request_attempted"] is False
    assert result["fallback_allowed"] is False


def test_sanitizer_removes_key_and_bearer_tokens() -> None:
    key = "sk-secret-value-123456"
    sanitized = _sanitize(f"bad {key} Authorization Bearer abc.def-123", key)
    assert key not in sanitized
    assert "abc.def-123" not in sanitized
