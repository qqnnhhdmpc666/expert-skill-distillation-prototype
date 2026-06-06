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
