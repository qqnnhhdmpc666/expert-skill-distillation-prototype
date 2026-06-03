# Historical Review Comments

## Example 1: Missing Authorization Boundary

The endpoint says "login required" but does not say whether ordinary users, admins, or service accounts may call it. The design should specify roles or scopes, not just authentication.

## Example 2: Error Codes Too Vague

The design only lists `500 system error`. It should distinguish invalid input, unauthorized, forbidden, not found, and duplicate request. Otherwise client behavior and monitoring will be unstable.

## Example 3: Sensitive Field Exposure

The response example returns `access_token` and full phone number. The review should flag this as sensitive data exposure unless the endpoint is specifically designed for token issuance and the response is protected.

## Example 4: Good Pattern

The better design includes authentication scheme, required OAuth scope, request validation table, stable error code table, masked user fields, request_id, and pagination behavior.
