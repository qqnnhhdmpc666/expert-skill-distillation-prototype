# Demo Pipeline Check

- Mode: `check-existing`
- Generated at: `2026-06-05T12:16:40.172534+00:00`

| Item | Status | Message |
|---|---|---|
| baseline_001 | ok | baseline comparison checked |
| harbor_api_review_001 | ok | feedback run checked |
| harbor_api_review_002 | ok | feedback run checked |
| agent_mock_api_review_001 | ok | feedback run checked |
| llm_agent_api_review_001 | ok | LLM matrix checked |

## Boundary

- This script checks or lightly reruns demo artifacts.
- It never writes API keys to files.
- Heavy Harbor and LLM reruns are opt-in; unavailable endpoints are marked rather than faked.
