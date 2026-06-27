service: analytics-api
environment: production
debug: false
external_api_url: https://metrics.example.com/v1
service_account:
  name: analytics-reader
  roles:
    - read_metrics
resources:
  limits:
audit:
  enabled: false
  export_sink:
