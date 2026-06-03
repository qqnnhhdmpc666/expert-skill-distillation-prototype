# API Review Checklist

- Confirm authentication method is explicit.
- Confirm authorization boundary is clear.
- Confirm required and optional request fields are documented.
- Confirm input type, range, length, and enum constraints are present.
- Confirm error code coverage includes validation, auth, permission, not found, duplicate, and server errors.
- Confirm response does not expose secrets or internal implementation details.
- Confirm response format is consistent with the standard envelope.
- Confirm POST, PUT, and PATCH endpoints explain idempotency or duplicate submission behavior.
- Confirm logs or response metadata include a request identifier for troubleshooting.
