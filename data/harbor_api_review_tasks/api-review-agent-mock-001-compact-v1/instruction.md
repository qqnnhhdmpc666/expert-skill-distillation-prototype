# API Review Mock Agent Task 001 - Compact v1

Run the scripted API review mock agent with the provided compact skill and API case, then write `/app/review.json`.

The output must be JSON with a `findings` array. Each finding must include:

- `rule_id`
- `issue`
- `severity`
- `evidence`

The verifier expects findings for all required rule ids in `expected_findings.json`.

This compact v1 task intentionally exposes only R001-R004 to the mock agent, so the verifier is expected to fail with missing R005/R006.
