# Docs: Enterprise Production Spec

This document describes the production-grade architecture, operational runbooks, security posture, and operational expectations for OASIS.

Executive summary
- OASIS is a microservice-based platform that stores, indexes and serves knowledge artifacts and documents. The core services include auth-service, paper-service, knowledge-graph-service, and others.
- The platform is designed for high-availability, observability, and secure production operation.

Architecture
- Services are stateless application servers behind an API gateway.
- Stateful components include: PostgreSQL clusters (primary + replicas), Redis for caching, Kafka for eventing, S3 for object storage.
- Services communicate over secure internal network; all traffic between services is mTLS when supported by the cluster.

Security
- Secrets in Vault or cloud secrets manager; no secrets in repo.
- RBAC enforced at the API gateway and cloud provider.
- Regular dependency scanning and container image signing.

Observability
- Prometheus + Grafana for metrics, ELK stack for logs, and Jaeger for tracing.
- Define SLOs for request latency and availability per service.

Operational runbooks and incident response are in docs/runbooks/
