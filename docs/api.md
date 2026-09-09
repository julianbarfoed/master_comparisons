# Audio API contract — milestone 1

Status: agreed implementation target for agent work; only `/health` exists in the
foundation. Contract changes require coordination before implementation.

## Scope

Local, single-user library. Backend: `http://localhost:8000`. Frontend:
`http://localhost:5173`. No authentication for this milestone; local development
servers bind to loopback. No processing jobs or public deployment in this task.

SQLite stores metadata; local storage holds original bytes under server-generated
names. Files and metadata survive backend restarts. Do not derive storage paths
from uploaded filenames. Use an injectable repository/storage boundary and isolated
temporary data for tests. Configuration reads the backend `.env` with environment
variables taking precedence and uses the defaults in `.env.example`.

Allow browser requests from `WEB_ORIGIN`, including upload/delete preflight and
Range requests. Expose `Accept-Ranges`, `Content-Range`, and `Content-Length`.

## Audio object

```json
{
  "id": "b9438b9d-6b20-4a1c-9c21-31c7cc3754eb",
  "filename": "piano.wav",
  "content_type": "audio/wav",
  "size_bytes": 882044,
  "created_at": "2026-09-09T12:00:00Z",
  "playback_path": "/api/audio/b9438b9d-6b20-4a1c-9c21-31c7cc3754eb/content"
}
```

IDs are UUID strings. `filename` is a safe display basename, never a filesystem
path. `created_at` is UTC ISO 8601. `playback_path` is relative to the backend origin;
the frontend resolves it using `VITE_API_URL` (default `http://localhost:8000`).
Duration, waveforms, tags, processing status, and pagination are later additions.

## Endpoints

| Method/path | Request | Success |
| --- | --- | --- |
| `GET /health` | None | `200 {"status":"ok"}`; does not require storage or credentials |
| `GET /api/audio` | None | `200 {"items": [Audio]}`; newest first, ID ascending as tie-breaker; empty array when empty |
| `POST /api/audio` | Multipart form field `file`; one file per request | `201 Audio`; visible in subsequent list requests |
| `GET /api/audio/{id}/content` | Optional single HTTP `Range` header | `200` full original bytes or `206` for a satisfiable byte range |
| `DELETE /api/audio/{id}` | None | `204` with no body; removes stored content and metadata |

Uploads support PCM WAV and MP3, with a default maximum of 25 MiB (26,214,400 file
bytes). Enforce the limit while reading, including requests without Content-Length.
Verify file content; do not trust an extension or the submitted MIME type. Store the
canonical content type (`audio/wav` or `audio/mpeg`). Reject empty, malformed, or
unsupported files. Duplicate names are allowed and receive independent IDs.
Failed uploads must not leave library entries or orphaned files.

Playback returns the stored MIME type, `Content-Length`, and `Accept-Ranges: bytes`.
Support closed (`bytes=0-99`), open-ended (`bytes=100-`), and suffix (`bytes=-100`)
ranges. `206` includes `Content-Range`. Valid but unsatisfiable ranges return `416`
with `Content-Range: bytes */<size>`. Ignore malformed ranges and multipart ranges
and return the full representation with `200`. Stream files rather than loading
the entire library or entire playback file into memory.

Deletion completes only when content and metadata have been removed. On storage
failure, report an error and retain metadata so deletion can be retried. Missing
content may be treated as already removed while cleaning up existing metadata.

## Errors

All API error responses use this envelope, except the bodyless `204` success:

```json
{"error": {"code": "unsupported_audio", "message": "Upload a PCM WAV or MP3 file."}}
```

| Status | Code | Meaning |
| --- | --- | --- |
| `400` | `invalid_upload` | Missing file, empty file, or malformed supported audio |
| `413` | `upload_too_large` | File exceeds configured maximum |
| `415` | `unsupported_audio` | Unsupported audio format |
| `404` | `audio_not_found` | Unknown/malformed ID or missing playback content; also applies to repeated deletion |
| `416` | `range_not_satisfiable` | Valid byte range cannot be served |
| `500` | `internal_error` | Unexpected storage/database failure; no internal paths or stack traces in the response |

## Shared acceptance flow

1. Start with an empty temporary library; show a useful empty state.
2. Upload a small valid WAV; display its name and size without a page reload.
3. Play and seek the uploaded audio.
4. Reload the page and restart the backend; the recording still exists and plays.
5. Reject an unsupported file and an oversized file with a useful message.
6. Delete the recording; it disappears and subsequent content access returns 404.

Backend tests additionally cover malformed audio, duplicate names, safe paths,
upload cleanup, deletion failure, MP3 support, and range semantics. Frontend tests
use this same envelope and representative audio objects for mocked responses.
