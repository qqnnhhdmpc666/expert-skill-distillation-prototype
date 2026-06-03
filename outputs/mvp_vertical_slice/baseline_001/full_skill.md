# API Review Full Skill Package

## Purpose

Distill API/code review expert knowledge into auditable rules with material evidence, examples, and behavior boundaries.

## Rules

### R001: auth

- Priority: high
- Status: supported
- Rule: Every API endpoint must document authentication method and authorization boundary.
- Rationale: Authentication alone is not enough; reviewers need roles, scopes, and failure behavior.
- Evidence:
  - api_design_guidelines.md (Authentication, line 3): ## Authentication
  - historical_review_comments.md (Example 1: Missing Authorization Boundary, line 3): ## Example 1: Missing Authorization Boundary
  - review_checklist.md (API Review Checklist, line 3): - Confirm authentication method is explicit.

### R002: input_validation

- Priority: high
- Status: supported
- Rule: Each request field must define required/optional status, type, range, length, and enum constraints.
- Rationale: Missing validation boundaries make client behavior and server-side protection ambiguous.
- Evidence:
  - api_design_guidelines.md (Input Validation, line 7): ## Input Validation
  - historical_review_comments.md (Example 1: Missing Authorization Boundary, line 5): The endpoint says "login required" but does not say whether ordinary users, admins, or service accounts may call it. The design should specify roles or scopes, not just authentication.
  - review_checklist.md (API Review Checklist, line 5): - Confirm required and optional request fields are documented.

### R003: error_codes

- Priority: high
- Status: supported
- Rule: APIs should provide stable error codes for success, invalid input, unauthorized, forbidden, not found, duplicate request, and server failure.
- Rationale: Overly vague error codes make client handling, monitoring, and repair unstable.
- Evidence:
  - api_design_guidelines.md (Error Codes, line 11): ## Error Codes
  - historical_review_comments.md (Example 2: Error Codes Too Vague, line 7): ## Example 2: Error Codes Too Vague
  - review_checklist.md (API Review Checklist, line 7): - Confirm error code coverage includes validation, auth, permission, not found, duplicate, and server errors.

### R004: sensitive_data

- Priority: high
- Status: supported
- Rule: API responses must not expose tokens, raw secrets, internal stack traces, full identity numbers, or unnecessary personal data.
- Rationale: Sensitive fields should be masked, omitted, or protected by separate authorization.
- Evidence:
  - api_design_guidelines.md (Sensitive Data, line 15): ## Sensitive Data
  - historical_review_comments.md (Example 3: Sensitive Field Exposure, line 11): ## Example 3: Sensitive Field Exposure
  - review_checklist.md (API Review Checklist, line 8): - Confirm response does not expose secrets or internal implementation details.

### R005: response_format

- Priority: medium
- Status: supported
- Rule: Responses should use a consistent envelope with code, message, request_id, and data.
- Rationale: A stable response envelope makes downstream parsing and troubleshooting predictable.
- Evidence:
  - api_design_guidelines.md (Error Codes, line 11): ## Error Codes
  - historical_review_comments.md (Example 2: Error Codes Too Vague, line 7): ## Example 2: Error Codes Too Vague
  - review_checklist.md (API Review Checklist, line 7): - Confirm error code coverage includes validation, auth, permission, not found, duplicate, and server errors.

### R006: idempotency

- Priority: medium
- Status: supported
- Rule: POST, PUT, and PATCH endpoints should explain idempotency or duplicate submission behavior.
- Rationale: Mutation endpoints often fail in retry paths unless duplicate handling is explicit.
- Evidence:
  - api_design_guidelines.md (Input Validation, line 7): ## Input Validation
  - historical_review_comments.md (Example 2: Error Codes Too Vague, line 9): The design only lists `500 system error`. It should distinguish invalid input, unauthorized, forbidden, not found, and duplicate request. Otherwise client behavior and monitoring will be unstable.
  - review_checklist.md (API Review Checklist, line 6): - Confirm input type, range, length, and enum constraints are present.

### R007: observability

- Priority: medium
- Status: supported
- Rule: APIs should expose request_id or equivalent trace metadata and document key audit logging requirements.
- Rationale: Troubleshooting and audit review need stable trace identifiers.
- Evidence:
  - api_design_guidelines.md (Response Envelope, line 21): Responses should use a consistent envelope with `code`, `message`, `request_id`, and `data`. Paginated endpoints must document `page`, `page_size`, `total`, and empty result behavior.
  - historical_review_comments.md (Example 4: Good Pattern, line 17): The better design includes authentication scheme, required OAuth scope, request validation table, stable error code table, masked user fields, request_id, and pagination behavior.
  - review_checklist.md (API Review Checklist, line 11): - Confirm logs or response metadata include a request identifier for troubleshooting.

## Required Review Output

Return JSON with `passed`, `failed_rules`, `findings`, and `suggested_patch`.
