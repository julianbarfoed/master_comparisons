# Audio app roadmap

Agreed direction, 2026-09-11. Current priority: **M1 — signed-in persistent library**.

## Product and architecture

First release: sign in → upload → private library → play/seek → delete.
Use development services locally first; hosting and one useful processing operation
follow. Preserve original audio and store future processed output separately.
Sharing, teams, batch uploads, waveform editing, and generic job infrastructure are
outside this release.

| Component | Agreed solution |
| --- | --- |
| Browser | React/Vite; Supabase SDK manages email OTP sign-in and session refresh |
| API | Python/FastAPI; verifies bearer tokens and authorizes every track operation |
| Metadata | Supabase Postgres through Python, explicit SQL and a restricted backend role |
| Audio | Private Cloudflare R2; upload through Python, playback via signed R2 GET URLs |
| File support | PCM WAV and MP3; 100 MiB = 104,857,600 file bytes |
| Playback grants | Five minutes; URL holders retain access until expiry, including after sign-out |

Browser → Supabase Auth for sessions; browser → Python for app requests;
Python → Postgres/R2 for persistence; browser → R2 for authorized playback.

## Shared contracts

The API resource is a **track**. Keep persistence models and response DTOs explicitly
mapped. Reconcile the existing `AudioRepository.create/get_by_id` and
`TrackReader.list_tracks(user_id)` in M1-B; retain useful tests and in-memory adapters.

Track metadata: server-generated UUID `id`, opaque text `owner_id`, `title`,
positive `duration_seconds`, and UTC `created_at`. M2 adds private `object_key`,
sanitized `original_filename`, backend-determined `content_type`, and `size_bytes`.
M1 reconciles the currently required object key without inventing fake keys;
development seed rows are removed before M2's storage constraints are applied.
List newest first, ID as tie-breaker; index owner/creation time. Never persist signed URLs.

| Endpoint | Success | Milestone |
| --- | --- | --- |
| `GET /health` | `200 {"status":"ok"}` | Existing |
| `GET /me` | `200 {"id":"<verified-subject>"}` | M1 |
| `GET /tracks` | `200 [{id,title,duration_seconds}]`; empty library is `[]` | M1 |
| `POST /tracks` | Multipart `file`; `201` track summary | M2 |
| `GET /tracks/{id}/playback` | `200 {url,expires_at}`; expiry is UTC | M2 |
| `DELETE /tracks/{id}` | `204`; repeated deletion returns `404` | M3 |

Use FastAPI's `detail` errors: 401 invalid/missing credentials, 404 missing/not-owned
track, 413 oversize, 415 unsupported format, 400 malformed audio, 422 request-schema
validation, and 503 dependency failure. The client handles string and structured detail.

## Invariants for implementation

- Validate token signature, issuer, audience, expiry, and subject using a maintained
  verifier suited to the project's signing keys. An auth service outage is not an
  invalid credential. Sign-out clears browser library/player state.
- Derive ownership from the verified subject. Scope every database read/write to it.
  Keep application tables outside the browser Data API and enforce appropriate grants;
  direct SQL does not automatically inherit the user's identity or RLS context.
- Enforce the file limit while reading, even without Content-Length. Spool/stream
  uploads; avoid full-file memory buffers. Allow multipart overhead in request limits.
  Verify audio content and duration rather than trusting names or submitted MIME types.
- Upload object first, then metadata; clean up after metadata failure. Support orphan
  reconciliation with a grace period and dry-run mode. No automatic POST retries:
  upload retries may create duplicates. Failed uploads must not appear as playable rows.
- Delete object before metadata; retain metadata on storage failure. Missing objects
  permit metadata cleanup; database failure permits retry. Report partial failures.
- Authorize each playback grant, configure frontend/API and R2 CORS, and keep URLs out
  of logs. On expiry, renew once and restore playback position, then show a useful error.

## Milestones and delivery

| Milestone | Completed user capability | Required evidence |
| --- | --- | --- |
| M1: sign-in and library | Real session, identity, persistent owner-scoped listing, sign-out, loading/empty/error states | Two-user isolation; invalid tokens rejected; refresh/restart persistence; database outage handled |
| M2: upload and playback | Valid audio reaches R2 and metadata; visible upload result; playback and seeking | WAV/MP3; exactly 100 MiB accepted and one byte over rejected, including streamed requests; malformed inputs; provider/cleanup failures; real R2 seeking and URL renewal |
| M3: deletion | User removes their own audio and can retry failures | Cross-user denial; object and row removed; storage/database failure recovery; complete sign-in/upload/play/delete demo |

Authorization, failure handling, and tests ship with each feature. M3 completes the
first usable release. Hosting then adds HTTPS, migrations, secrets, origin/limit
configuration, and a deployment smoke check. Processing later adds one selected
operation with original/output comparison; its runtime determines execution needs.

## Current work and agent ownership

Baseline: merged PRs #1–#7 provide tested boundaries, a track route using fakes, and
a library empty state. Real auth, Postgres, R2, and browser integration remain pending.

| Next PR | Lead and scope | Dependency |
| --- | --- | --- |
| M1-A: authenticated identity | Auth: real verifier and `/me`; auth settings, app wiring, backend dependencies | Development Supabase project, email delivery/test users, signing-key configuration |
| M1-B: persistent listing | DB: Postgres adapter, metadata reconciliation, real `/tracks`; API supports integration | Develop adapter/tests alongside A; rebase onto A for shared settings/wiring |
| M1-C: sign-in and library UI | Frontend: browser session, API client, listing, sign-out and UI states | Develop against agreed responses; demonstrate with A+B |

API coordinates shared contracts and combined verification. R2 joins M2 with API
for backend upload/playback; Frontend builds its consumer alongside it. M3 has one
feature owner and DB/R2 review. Assign work where useful; five specialties do not
require five simultaneous PRs.

Use isolated Postgres integration tests and two-user checks, browser flow tests,
and recorded real-service verification at each milestone. CI can use fakes/local
dependencies without live auth/R2 secrets; handoffs state the tested commits and
remaining limitations. Separate ports, data, and object prefixes between worktrees.

Provider references: [OTP](https://supabase.com/docs/guides/auth/auth-email-passwordless),
[JWT verification](https://supabase.com/docs/guides/auth/jwts),
[Postgres connections](https://supabase.com/docs/guides/database/connecting-to-postgres),
[RLS](https://supabase.com/docs/guides/database/postgres/row-level-security),
[R2 signing](https://developers.cloudflare.com/r2/api/s3/presigned-urls/),
[R2 CORS](https://developers.cloudflare.com/r2/buckets/cors/).
