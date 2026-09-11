# Backend map

Run/setup/check commands: [root README](../README.md).
Shared contracts and milestones: [roadmap](../docs/ROADMAP.md).

- `app/main.py`, `app/routes/`: application wiring and HTTP endpoints.
- `app/auth.py`: identity verification boundary and Supabase JWT verifier.
- `app/dependencies.py`: reusable authenticated-user dependency.
- `app/db.py`, `app/tracks.py`, `app/schemas.py`: persistence, track reads, response models.
- `app/storage.py`: object storage boundary.
- `app/config.py`, `sql/`: configuration and migrations.
- `tests/`: backend behavior checks.

## Supabase authentication

Set `SUPABASE_URL` to the project URL before calling authenticated endpoints. The
backend derives the expected issuer and JWKS URL from it and requires the
`authenticated` audience. `SUPABASE_JWT_ISSUER`, `SUPABASE_JWKS_URL`, and
`SUPABASE_JWT_AUDIENCE` can override those defaults for custom deployments.

The project must use Supabase asymmetric JWT signing keys (RS256 or ES256),
whose public keys are exposed through the project's JWKS endpoint. Shared-secret
HS256 tokens are deliberately not accepted by this verifier.

Send the Supabase access token as `Authorization: Bearer <token>`. `GET /me` returns
the verified token subject as `{"id":"<verified-subject>"}`. Missing or invalid
credentials return 401. Signing-key discovery failures return 503. `GET /health`
does not require auth configuration.
