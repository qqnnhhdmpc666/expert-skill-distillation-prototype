Task: Independently authored holdout: defensive auth review.

Snippet:
cancel_invoice checks is_authenticated, loads invoice by id without tenant_id or owner_id filtering, and the denial body returns invoice_id.

Requested output schema: capability_id, evidence_span, recommended_fix