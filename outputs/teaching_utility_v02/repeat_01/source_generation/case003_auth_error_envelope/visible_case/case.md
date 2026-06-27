# Holdout Case 003: Auth, Error Codes, Response Envelope

Endpoint: `GET /v1/orders/{order_id}`

Purpose: Return one order summary for the current user.

Authentication:

- The endpoint says "login required".
- It does not define roles, scopes, or authorization failure behavior.

Request:

- `order_id` is a string path parameter.
- It is required and must match `ORD-[0-9]{8}`.

Response:

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "order_id": "ORD-20260605",
    "status": "paid"
  }
}
```

Error Codes:

- `0`: success
- `500`: server error

