Task: Review this access-control handler defensively.

Snippet:
archive_invoice checks is_authenticated, then loads invoice by id without tenant_id or owner_id filtering. The denial path returns invoice_id in the error body.

Requested output schema: capability_id, evidence_span, recommended_fix