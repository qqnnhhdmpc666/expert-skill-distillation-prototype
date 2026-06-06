service: export-job
environment: staging
debug: false
external_api_url: https://exports.example.com/v1
api_key: "plain-text-demo-key"
service_account:
  name: export-reader
  roles:
    - read_export
resources:
  requests:
audit:
  enabled: true
  retention_days: 30
