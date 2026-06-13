# Holdout Case 005: Response Contract Schema

Endpoint: `GET /v1/reports/daily`

Purpose: Return the daily business report.

Authentication:

- Uses OAuth2 bearer token.
- Required scope: `report.read`.
- Unauthorized calls return `401`; insufficient scope returns `403`.

Request:

- `date` is required.
- Type: string.
- Format: `YYYY-MM-DD`.
- Range: the last 90 days.

Response:

```json
{
  "status": "ok",
  "payload": {
    "date": "2026-06-05",
    "gross_amount": 12000
  }
}
```

Error Codes:

- `0`: success
- `400`: validation error
- `401`: unauthorized
- `403`: forbidden
- `404`: report not found
- `500`: server error

Mutation:

- This is a read-only GET endpoint.

