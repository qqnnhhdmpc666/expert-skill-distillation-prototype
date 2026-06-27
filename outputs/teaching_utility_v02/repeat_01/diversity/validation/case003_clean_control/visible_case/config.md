service: profile-api
environment: production
debug: false
external_api_url: https://profile.example.com/v1
payment_token: ${PROFILE_API_TOKEN}
service_account:
  name: profile-reader
  roles:
    - read_profile
resources:
  limits:
    cpu: "500m"
    memory: "512Mi"
audit:
  enabled: true
  retention_days: 90
