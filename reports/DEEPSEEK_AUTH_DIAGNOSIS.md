# DeepSeek Authentication Diagnosis

Date: 2026-06-22

## Classification

```text
classification = wrong_var
judge_pass = false
```

The observed HTTP 401 does not prove that a DeepSeek credential was revoked. The same process had no `DEEPSEEK_API_KEY`; the client fell back to `OPENAI_API_KEY` and sent that value to the DeepSeek endpoint.

## Client contract

Authoritative code:

```text
src/expert_skill_system/cli.py:108
  DEEPSEEK_API_KEY, then OPENAI_API_KEY fallback

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
  present: false

OPENAI_API_KEY:
  present: true
  length: 35
  prefix: sk-
  suffix: bNR
  leading_or_trailing_whitespace: false
  contains_newline: false
  contains_non_ascii: false

selected_variable: OPENAI_API_KEY
```

## Request/response

```text
base_url: https://api.deepseek.com
model: deepseek-chat
endpoint_path: /chat/completions
endpoint: https://api.deepseek.com/chat/completions
header_scheme: Authorization: Bearer <redacted>
response_status: 401
```

Sanitized response body:

```json
{"error":{"message":"Authentication Fails, Your api key: ****sbNR is invalid","type":"authentication_error","param":null,"code":"invalid_request_error"}}
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

This run matches `wrong_var` exactly. `header_error` is not supported by the evidence because the request used the expected Bearer scheme.

## Secret exposure audit

The repository scan found no real credential literal in `src/`, `scripts/`, `docs/`, `reports/`, `README.md`, or `review_package/`. Test files contain clearly synthetic placeholder keys used to test redaction.

However, full key material was previously supplied in conversation. Treat it as exposed outside the repository: rotate it immediately in the DeepSeek console, then set the replacement only as `DEEPSEEK_API_KEY` in the shell that launches `eskill`. Do not place it in committed `.env`, reports, command history, or artifacts.

## Next safe command

After rotation, in the same PowerShell session:

```powershell
$env:DEEPSEEK_API_KEY = '<new-rotated-key>'
& '.\.tmp\clean-core-venv\Scripts\python.exe' scripts\diagnose_deepseek_auth.py --request
```

Only if classification becomes `authenticated` should the formal Judge build be rerun. Until then, Judge remains blocked and no Judge pass is claimed.

