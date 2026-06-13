# Holdout Case 004: Validation, Sensitive Data, Idempotency

Endpoint: `POST /v1/customers/update-profile`

Purpose: Update a customer's profile.

Authentication:

- Uses OAuth2 bearer token.
- Required scope: `customer.profile.write`.
- Unauthorized calls return `401`; insufficient scope returns `403`.

Request:

```json
{
  "display_name": "Alice",
  "age": 200,
  "email": "alice@example.com",
  "marketing_opt_in": "yes"
}
```

The request does not document required fields, types, ranges, length limits, or enum values.

Response:

```json
{
  "code": 0,
  "message": "ok",
  "request_id": "req-123",
  "data": {
    "customer_id": "C100",
    "access_token": "debug-token",
    "internal_trace": "svc.customer.ProfileUpdater:line87"
  }
}
```

Error Codes:

- `0`: success
- `400`: validation error
- `401`: unauthorized
- `403`: forbidden
- `409`: duplicate request
- `500`: server error

Idempotency:

- The API does not describe idempotency keys or duplicate submission behavior.

