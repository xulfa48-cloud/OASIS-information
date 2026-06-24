# API Gateway Contract

The API Gateway routes external requests and enforces authentication, rate-limiting and TLS termination.

- Authentication: validate bearer JWTs issued by auth-service.
- Rate limiting: per-IP and per-API key limits.
- Routing: /api/v1/auth -> auth-service
           /api/v1/papers -> paper-service
           /api/v1/kg -> knowledge-graph-service
