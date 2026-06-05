# Cost / Effect Table

| Case | Variant | Coverage | Critical Misses | False Positives | Total Tokens | Pass@1 |
|---|---|---:|---|---|---:|---|
| case003_auth_error_envelope | no_skill | 0.00 | R001, R003 | none | 4 | False |
| case003_auth_error_envelope | full_skill | 1.00 | none | none | 1499 | True |
| case003_auth_error_envelope | compact_v1 | 0.67 | none | none | 381 | False |
| case003_auth_error_envelope | patched_compact | 1.00 | none | none | 508 | True |
| case003_auth_error_envelope | patched_compact_selective_trace | 1.00 | none | none | 426 | True |
| case004_validation_sensitive_idempotency | no_skill | 0.00 | R002, R004 | none | 4 | False |
| case004_validation_sensitive_idempotency | full_skill | 1.00 | none | none | 1499 | True |
| case004_validation_sensitive_idempotency | compact_v1 | 0.67 | none | none | 375 | False |
| case004_validation_sensitive_idempotency | patched_compact | 1.00 | none | none | 508 | True |
| case004_validation_sensitive_idempotency | patched_compact_selective_trace | 1.00 | none | none | 428 | True |
| case005_response_contract_schema | no_skill | 0.00 | R005 | none | 4 | False |
| case005_response_contract_schema | full_skill | 1.00 | none | none | 1387 | True |
| case005_response_contract_schema | compact_v1 | 0.00 | R005 | none | 269 | False |
| case005_response_contract_schema | patched_compact | 1.00 | none | none | 396 | True |
| case005_response_contract_schema | patched_compact_selective_trace | 1.00 | none | none | 310 | True |
| case006_clean_false_positive_control | no_skill | 1.00 | none | none | 4 | True |
| case006_clean_false_positive_control | full_skill | 1.00 | none | none | 1334 | True |
| case006_clean_false_positive_control | compact_v1 | 1.00 | none | none | 269 | True |
| case006_clean_false_positive_control | patched_compact | 1.00 | none | none | 343 | True |
| case006_clean_false_positive_control | patched_compact_selective_trace | 1.00 | none | none | 176 | True |
