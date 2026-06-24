# Monitoring & SLOs

Metrics
- Each service exposes Prometheus metrics at /metrics.
- Example metrics:
  - requests_total (labels: service, handler, method, status)
  - request_duration_seconds_bucket
  - active_workers

SLOs
- 99.9% availability for Auth and Paper services.
- 95th percentile request latency under 500ms for read endpoints.

Alerting
- Error rate increase > 3x baseline triggers an alert.
- DB replication lag > 30s triggers a high-priority alert.
