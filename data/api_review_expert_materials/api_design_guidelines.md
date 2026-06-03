# API Design Guidelines

## Authentication

Every endpoint must document its authentication method and authorization boundary. The API owner must state which roles or scopes can call the endpoint and what happens when authorization fails.

## Input Validation

Each request field must define whether it is required, its type, valid range, length limit, and allowed enum values. Optional fields must define default behavior.

## Error Codes

APIs should return stable error codes for success, invalid input, unauthorized access, forbidden access, resource not found, duplicate request, and server failure.

## Sensitive Data

Responses must not expose access tokens, internal stack traces, raw secrets, full identity numbers, or unnecessary personal data. If a field is sensitive, the API design must state whether it is masked, omitted, or separately authorized.

## Response Envelope

Responses should use a consistent envelope with `code`, `message`, `request_id`, and `data`. Paginated endpoints must document `page`, `page_size`, `total`, and empty result behavior.
