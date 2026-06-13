# Holdout Case 006: Clean API False-Positive Control

Endpoint: `PUT /v1/orders/{order_id}/delivery-address`

Purpose: Update delivery address for an order.

Authentication:

- Uses OAuth2 bearer token.
- Required scope: `order.write`.
- Unauthorized calls return `401`; insufficient scope returns `403`.

Request:

- `order_id`: required string path parameter, pattern `ORD-[0-9]{8}`.
- `address_line1`: required string, length 1-120.
- `address_line2`: optional string, max length 120.
- `postal_code`: required string, pattern `[0-9]{5,6}`.
- `country`: required enum, one of `CN`, `US`, `SG`.

Response:

```json
{
  "code": 0,
  "message": "ok",
  "request_id": "req-456",
  "data": {
    "order_id": "ORD-20260605",
    "updated": true
  }
}
```

Error Codes:

- `0`: success
- `400`: validation error
- `401`: unauthorized
- `403`: forbidden
- `404`: order not found
- `409`: duplicate request
- `500`: server error

Idempotency:

- Clients must send `Idempotency-Key`.
- Repeated requests with the same key return the original result.

Sensitive Data:

- The response does not include tokens, secrets, internal traces, phone numbers, or identity numbers.

