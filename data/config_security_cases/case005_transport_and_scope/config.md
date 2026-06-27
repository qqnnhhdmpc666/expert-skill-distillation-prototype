service: sync-gateway
environment: production
debug: false
external_api_url: http://partner.internal.example.com/v2
service_account:
  name: sync-writer
  roles:
    - write_all_projects
resources:
  requests:
    cpu: "500m"
    memory: "512Mi"
audit:
  enabled: true
  export_sink: s3://audit-prod/sync-gateway
