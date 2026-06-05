# Case 002: Order Refund API

## Endpoint

`POST /api/v1/orders/{order_id}/refund`

## Description

Create a refund request for an order and return refund status.

## Request

Path parameter:

- `order_id`: string

Body:

```json
{
  "amount": 125.50,
  "reason": "customer_request",
  "notify_customer": true
}
```

## Response

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "refund_id": "rf_123",
    "order_id": "ord_999",
    "internal_trace": "RefundService.java:88",
    "customer_phone": "13800138000"
  }
}
```

## Error Codes

| Code | Meaning |
|---|---|
| 0 | success |
| 500 | system error |

## Notes

The endpoint requires login.
