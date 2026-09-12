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

## Supabase Postgres metadata

Apply `sql/001_init.sql` once with a migration-capable direct connection. It creates
the backend-only `private.tracks` table and the read-only `audio_backend` role. The
migration user receives that role; grant it to a different runtime login if needed.

Set `DATABASE_URL` to the backend's Postgres connection string. In non-local
environments, require TLS in the connection string. The API uses explicit SQL and
switches each listing transaction to `audio_backend`; browser Data API roles have no
access to the private schema. `GET /tracks` reads only rows owned by the verified
token subject, ordered newest first and then by descending ID.

Postgres integration tests require an admin-capable, disposable database URL. The
fixture creates and drops a separate temporary database for every test:

```sh
TEST_DATABASE_URL=postgresql://postgres:password@localhost:5432/postgres \
  .venv/bin/python -m pytest tests/test_postgres_tracks.py
```
