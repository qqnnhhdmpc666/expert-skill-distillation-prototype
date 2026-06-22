# DeepSeek Authentication Diagnosis

Date: 2026-06-23

## Classification

```text
classification = authenticated
judge_pass = true
fallback_allowed = false
```

The fresh same-process request reached the official DeepSeek endpoint and returned HTTP 200. Only `DEEPSEEK_API_KEY` was eligible; an unrelated `OPENAI_API_KEY` present in the environment was neither selected nor transmitted.

## Client contract

Authoritative code:

```text
src/expert_skill_system/cli.py
  DEEPSEEK_API_KEY only; fallback is forbidden

src/expert_skill_system/compiler/judge.py:87-89
  POST {base_url}/chat/completions
  Authorization: Bearer <redacted>
  Content-Type: application/json
```

## Same-process environment diagnostics

Fresh command:

```powershell
& '.\.tmp\clean-core-venv\Scripts\python.exe' scripts\diagnose_deepseek_auth.py `
  --base-url https://api.deepseek.com `
  --model deepseek-chat `
  --request `
  --output .tmp\deepseek-auth-diagnosis-live.json
```

Only non-secret metadata was persisted:

```text
DEEPSEEK_API_KEY:
  present: true
  format_checks: pass

OPENAI_API_KEY:
  present: true
  selected: false

selected_variable: DEEPSEEK_API_KEY
fallback_allowed: false
```

## Request/response

```text
base_url: https://api.deepseek.com
model: deepseek-chat
endpoint_path: /chat/completions
endpoint: https://api.deepseek.com/chat/completions
header_scheme: Authorization: Bearer <redacted>
response_status: 200
```

No full credential is stored in this report or the diagnosis artifact.

## Classification rationale

The requested taxonomy is applied in this order:

- `env_missing`: neither supported variable is present;
- `wrong_var`: DeepSeek variable absent, fallback variable selected, DeepSeek returns 401/403;
- `malformed_key`: prefix/whitespace/newline/non-ASCII diagnostics fail;
- `endpoint_mismatch`: 404/405 from the configured endpoint;
- `revoked_or_invalid_key`: a present DeepSeek-specific variable receives 401/403;
- `unknown_auth_failure`: remaining network/auth cases.

This run matches `authenticated`. The former `wrong_var` diagnosis remains useful historical evidence, but it is superseded by the fresh authenticated run.

## Secret exposure audit

The repository scan found no real credential literal in `src/`, `scripts/`, `docs/`, `reports/`, `README.md`, or `review_package/`. Test files contain clearly synthetic placeholder keys used to test redaction.

Full key material was supplied in conversation, so it should still be rotated after this validation. Do not place the replacement in committed `.env`, reports, command history, or artifacts.

## Formal gate linkage

The authenticated credential was used in a fresh compiler build whose independent Judge attestation passed. See `reports/JUDGE_GATE_STATUS.md`. Authentication success alone is not treated as compiler effectiveness evidence.
