# Holdout Case 007: Auth Boundary with Sensitive Session Exposure

Endpoint: `GET /v1/admin/users/{user_id}/session`

Purpose: Return the current session summary for a support-console lookup.

Authentication:

- The endpoint says "internal login required".
- It does not define whether support staff, fraud analysts, or admins may access it.
- It does not define the scope or role required for cross-user access.

Request:

- `user_id` is a required path parameter and must be a UUID.

Response:

```json
{
  "code": 0,
  "message": "ok",
  "request_id": "req-9001",
  "data": {
    "user_id": "7e654b47-bf1c-4d9c-9155-7d3b28f1d73e",
    "session_status": "active",
    "email": "demo@example.com",
    "session_token": "tok_live_demo_session",
    "debug_trace": "StackTrace: controller/session_lookup.rb:14"
  }
}
```

Error Codes:

- `0`: success
- `400`: invalid user id
- `401`: unauthorized
- `403`: forbidden
- `404`: user not found
- `500`: server error
