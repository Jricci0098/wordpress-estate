# Security

## Implemented MVP controls

- Read-only inventory agent; no generic command execution.
- Unique agent identity and secret authentication.
- PBKDF2-HMAC secret hashes rather than plaintext database storage.
- Timestamp freshness checks and unique request IDs for replay resistance.
- Versioned, validated inventory payloads.
- Parameterized ORM queries.
- Append-only historical snapshots.
- PostgreSQL, Redis, and MariaDB are not host-published.
- Dashboard, API, and WordPress demo ports bind to `127.0.0.1`.
- Secrets belong in ignored `.env` files; `.env.example` contains local-only demo values.

## Deliberate limitations

This local MVP does not yet provide production TLS, OIDC, RBAC, CSRF policy, rate limiting, secrets-manager integration, immutable external audit storage, backup automation, or vulnerability-provider feeds. Do not expose it to an untrusted network.

Before production:

1. Put API/UI behind an HTTPS reverse proxy.
2. Replace all demo credentials and use a secrets manager.
3. Add OIDC and role-based authorization.
4. Add agent revocation, credential rotation, and rate limits.
5. Add structured audit events and log redaction tests.
6. Scan dependencies and container images.
7. Implement and test PostgreSQL backup restoration.
8. Perform a threat model and independent security review.

Automated updates must remain disabled until typed jobs, explicit authorization, dry runs, path/user validation, and audit logging are implemented and reviewed.
