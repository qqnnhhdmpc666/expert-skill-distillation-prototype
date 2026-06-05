# Direct Summary API Review Skill

This is a direct first-pass summary of the expert materials. It is intentionally not a rule ledger, not evidence mapped, and not patch aware.

Review an API design for these common concerns:

- Authentication and authorization should be explicit.
- Request fields should document required status, types, constraints, and defaults.
- Error behavior should be clear enough for client handling and monitoring.
- Responses should avoid leaking tokens, secrets, internal traces, or unnecessary personal data.
- Response shape should be consistent and include useful request tracking metadata.

Return JSON findings with rule_id, issue, severity, and evidence when a concern applies.
