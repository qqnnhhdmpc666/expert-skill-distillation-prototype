Task: Review this authorization handler defensively.

Snippet:
delete_invoice checks is_authenticated, then loads invoice by id without tenant_id or owner_id, and returns invoice_id in permission errors.

Requested output schema: capability_id, evidence_span, recommended_fix