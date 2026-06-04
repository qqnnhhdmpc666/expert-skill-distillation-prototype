# Case 001: User Profile Update API

## Endpoint

`POST /api/v1/users/{user_id}/profile`

## Description

Update a user's display name, phone number, and avatar URL.

## Request

Path parameter:

- `user_id`: string

Body:

```json
{
  "display_name": "Alice",
  "phone": "13800138000",
  "avatar_url": "https://example.com/a.png"
}
```

## Response

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "user_id": "u123",
    "display_name": "Alice",
    "phone": "13800138000",
    "access_token": "debug-token"
  }
}
```

## Error Codes

| Code | Meaning |
|---|---|
| 0 | success |
| 500 | server error |

## Notes

The endpoint requires login.
