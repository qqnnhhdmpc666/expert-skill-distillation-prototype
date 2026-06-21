# Independent Judge Gate Status

Date: 2026-06-22

```text
independent_llm_judge = blocked_by_wrong_environment_variable_with_contract_tests
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
- Same-process diagnosis: `DEEPSEEK_API_KEY` absent; `OPENAI_API_KEY` fallback selected.
- Valid Judge response received: no.
- Independent pass attestation generated: no.
- API key value was not printed or persisted.

The formal gate therefore cannot pass. The precise diagnosis is `wrong_var`, not evidence that a DeepSeek-specific key was revoked. See `reports/DEEPSEEK_AUTH_DIAGNOSIS.md`.

## Contract evidence

`tests/v1/test_independent_judge_gate.py` verifies that malformed output and HTTP 401 are hard failures, critical findings block eligibility, a blind valid response is accepted, and credentials are absent from provenance. Fresh focused result: `5 passed` as part of the 9-test external-gate slice.

## Next external requirement

A newly rotated DeepSeek credential must be made available through `DEEPSEEK_API_KEY` in the same shell that launches `eskill`. No code change can legitimately convert the current 401 into a formal pass.
