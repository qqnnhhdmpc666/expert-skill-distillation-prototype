"""OpenAI-compatible text backend.

The LLM may generate capability candidates, findings, and patch explanations.
Verifier, gate, and artifact landing remain deterministic. This backend must
never be treated as proof of sandbox execution by itself.
"""

BACKEND_TYPE = "live_llm_text"
