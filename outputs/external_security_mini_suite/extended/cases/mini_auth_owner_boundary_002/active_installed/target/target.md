Task: Review this object-access path defensively.

Snippet:
update_invoice checks is_authenticated and loads invoice by id. The response returns invoice_id when access is denied.

Requested output schema: capability_id, evidence_span, recommended_fix