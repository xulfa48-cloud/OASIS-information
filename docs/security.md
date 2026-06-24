# Security

Guidelines for securing OASIS in production:

- Secrets Management: Use Vault or cloud KMS. Rotate keys on a schedule and after personnel changes.
- Least privilege: apply minimal IAM roles to services and operators.
- Network controls: use private subnets for databases, and restrict egress where possible.
- Dependencies: vulnerability scans on CI pipeline and block high-severity findings.
- Container images: sign and verify images before deployment.
