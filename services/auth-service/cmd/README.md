# cmd/ directory

This directory contains the entrypoint executable(s) declarations for the auth-service.

Conventions

- cmd/server is the composition root for the application binary used in deployment.
- Keep the binary thin: wire together the configuration, logging, storage, and HTTP server from internal/ packages.

