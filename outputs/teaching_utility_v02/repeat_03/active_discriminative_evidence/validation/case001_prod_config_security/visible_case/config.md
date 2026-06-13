service: billing-worker
environment: production
debug: true
external_api_url: http://partner.example.com/v1
payment_token: "sk_live_demo_value"
service_account:
  name: billing-admin
  roles:
    - admin
audit:
  enabled: false
  retention_days:
