# Independent Judge Gate Status

Date: 2026-06-21

```text
independent_llm_judge = hard_blocked_by_auth_with_contract_tests
formal_pass = false
```

## Fresh attempt

```powershell
eskill --state-dir .tmp/goal-evidence-state build python-advisory `
  --require-judge `
  --judge-base-url https://api.deepseek.com `
  --judge-model deepseek-chat
```

- Provider/model: DeepSeek official OpenAI-compatible API / `deepseek-chat`.
- Restricted-network attempt: failed as `network` before a response.
- Approved external-network attempt: reached the provider and returned HTTP 401.
- Valid Judge response received: no.
- Independent pass attestation generated: no.
- API key value was not printed or persisted.

The formal gate therefore cannot pass. The failure category is authentication, not schema or promotion logic.

## Contract evidence

`tests/v1/test_independent_judge_gate.py` verifies that malformed output and HTTP 401 are hard failures, critical findings block eligibility, a blind valid response is accepted, and credentials are absent from provenance. Fresh focused result: `5 passed` as part of the 9-test external-gate slice.

## Next external requirement

A valid DeepSeek credential made available through `DEEPSEEK_API_KEY` is required. No code change can legitimately convert the current 401 into a formal pass.
