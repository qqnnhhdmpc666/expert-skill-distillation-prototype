# v0.2 Distilled Skill

This skill is distilled from domain materials plus trajectory lessons chosen under a matched budget.

# api_review base skill

## Objective

Review `api_review` tasks conservatively from visible evidence only.

## Domain Rules

- [R001] Authentication and authorization boundary: Document authentication method, roles/scopes, and authorization failure behavior.
- [R002] Request validation contract: Document required/optional status, type, range, length, and enum constraints for request fields.
- [R003] Stable error code coverage: Cover success, validation, unauthorized, forbidden, not found, duplicate, and server failures with stable codes.
- [R004] Sensitive response data suppression: Do not expose tokens, stack traces, raw secrets, or unnecessary personal data in responses.
- [R005] Response envelope contract: Use a stable envelope with code, message, request_id, and data.
- [R006] Mutation idempotency behavior: POST/PUT/PATCH endpoints should explain idempotency keys or duplicate submission behavior.

## Evidence Protocol

- Quote or tightly paraphrase visible case text only.
- Do not invent findings outside the listed rules.
- Clean controls should return no findings.

## Source Materials

# Source: api_design_guidelines.md

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

# Source: historical_review_comments.md

# Historical Review Comments

## Example 1: Missing Authorization Boundary

The endpoint says "login required" but does not say whether ordinary users, admins, or service accounts may call it. The design should specify roles or scopes, not just authentication.

## Example 2: Error Codes Too Vague

The design only lists `500 system error`. It should distinguish invalid input, unauthorized, forbidden, not found, and duplicate request. Otherwise client behavior and monitoring will be unstable.

## Example 3: Sensitive Field Exposure

The response example returns `access_token` and full phone number. The review should flag this as sensitive data exposure unless the endpoint is specifically designed for token issuance and the response is protected.

## Example 4: Good Pattern

The better design includes authentication scheme, required OAuth scope, request validation table, stable error code table, masked user fields, request_id, and pagination behavior.

# Source: review_checklist.md

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

# config_security base skill

## Objective

Review `config_security` tasks conservatively from visible evidence only.

## Domain Rules

- [C001] No hardcoded secrets: Do not hardcode tokens, passwords, API keys, or private credentials in configuration files.
- [C002] Production TLS: Production external endpoints must use TLS rather than plaintext HTTP.
- [C003] Least-privilege service account: Avoid admin, wildcard, or broad write roles for service accounts unless justified.
- [C004] Disable production debug: Production debug mode must be disabled.
- [C006] Audit logging and retention: Enable audit logging and define retention or export behavior.

## Evidence Protocol

- Quote or tightly paraphrase visible case text only.
- Do not invent findings outside the listed rules.
- Clean controls should return no findings.

## Source Materials

# Source: config_security_guidelines.md

# Configuration Security Guidelines

These guidelines describe review rules for deployment configuration files.

## Core Checks

- Secrets must not be hardcoded in configuration files. Use secret references or vault-backed environment variables.
- Production external endpoints must use TLS. Plain `http://` endpoints are not acceptable for production traffic.
- Service accounts should follow least privilege. Avoid `admin`, wildcard roles, or broad write permissions unless justified.
- Production debug mode must be disabled.
- Runtime resources should define CPU and memory requests or limits for deployed services.
- Security-sensitive services should enable audit logging and define retention or export behavior.

## Output Expectations

Each review finding should identify the rule, issue, severity, evidence from the configuration, and the configuration path or field that triggered the finding.

## Trajectory Lessons

Only trajectory-derived lessons selected within the matched budget are added below.

- seed::case003_auth_error_envelope: case003_auth_error_envelope: do not miss R005 when the visible case text exposes those triggers; repair the review checklist before adding broader findings.
- seed::case001_prod_config_security: case001_prod_config_security: do not miss C006 when the visible case text exposes those triggers; repair the review checklist before adding broader findings.
- query::case004_validation_sensitive_idempotency: case004_validation_sensitive_idempotency: do not miss R006 when the visible case text exposes those triggers; repair the review checklist before adding broader findings.

## Boundaries

- Do not use rules that are absent from the domain rule sections.
- Clean controls should return no findings.
- Unsupported families should not be invented from these two domains.
