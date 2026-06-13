# Installed Package Marginal Utility Report

- Backend: `offline_deterministic`
- Cases: `4`

| Case | Variants | Key Gains |
|---|---|---|
| api_review_001 | installed_v1, installed_v2, active_installed | installed_v2_over_installed_v1_gain=0.4, active_installed_over_installed_v1_gain=0.4, active_installed_over_installed_v2_gain=0.0 |
| auth_access_control_001 | installed_v1, installed_v2, active_installed | installed_v2_over_installed_v1_gain=0.4, active_installed_over_installed_v1_gain=0.4, active_installed_over_installed_v2_gain=0.0 |
| config_security_001 | installed_v1, installed_v2, active_installed, candidate_v3_package | installed_v2_over_installed_v1_gain=0.4, active_installed_over_installed_v1_gain=0.4, active_installed_over_installed_v2_gain=0.0, candidate_v3_package_over_active_installed_gain=0.0 |
| upload_security_001 | installed_v1, installed_v2, active_installed | installed_v2_over_installed_v1_gain=0.3333, active_installed_over_installed_v1_gain=0.3333, active_installed_over_installed_v2_gain=0.0 |

## Boundary

This report compares real installed package variants and records active pointer snapshots plus package hashes.
