from __future__ import annotations

import io
import urllib.error

from scripts.diagnose_deepseek_auth import _sanitize, diagnose


def test_diagnosis_selects_deepseek_before_openai_and_never_returns_key(monkeypatch) -> None:
    secret = "sk-deepseek-secret-value"
    monkeypatch.setenv("DEEPSEEK_API_KEY", secret)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-secret-value")
    result = diagnose(base_url="https://api.deepseek.com", model="deepseek-chat", timeout=1, perform_request=False)
    assert result["selected_variable"] == "DEEPSEEK_API_KEY"
    assert secret not in str(result)
    assert result["variables"][0]["length"] == len(secret)


def test_openai_fallback_401_is_classified_wrong_var(monkeypatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-secret-value")

    def reject(request, timeout):
        raise urllib.error.HTTPError(request.full_url, 401, "Unauthorized", {}, io.BytesIO(b'{"error":"bad key"}'))

    monkeypatch.setattr("urllib.request.urlopen", reject)
    result = diagnose(base_url="https://api.deepseek.com", model="deepseek-chat", timeout=1, perform_request=True)
    assert result["classification"] == "wrong_var"
    assert result["response_status"] == 401


def test_sanitizer_removes_key_and_bearer_tokens() -> None:
    key = "sk-secret-value-123456"
    sanitized = _sanitize(f"bad {key} Authorization Bearer abc.def-123", key)
    assert key not in sanitized
    assert "abc.def-123" not in sanitized
