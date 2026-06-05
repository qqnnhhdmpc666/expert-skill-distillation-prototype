# API Review Mock Agent Task 001 - Compact v2

Run the scripted API review mock agent with the provided compact skill and API case, then write `/app/review.json`.

The output must be JSON with a `findings` array. Each finding must include:

- `rule_id`
- `issue`
- `severity`
- `evidence`

The verifier expects findings for all required rule ids in `expected_findings.json`.

This compact v2 task exposes R001-R006 to the mock agent, so the verifier is expected to pass.
