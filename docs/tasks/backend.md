# Backend agent

Branch: `feat/audio-backend`. Own `back-end/` and its tests.
Dependency: merged foundation and `docs/api.md`.

## To-do

1. Read the contract and existing storage/db/config boundaries. Install with
   `make setup-backend`; establish the baseline with `make check-backend`.
2. Implement environment configuration, SQLite persistence, local file storage,
   and the upload/list/content/delete endpoints. Add focused modules as needed;
   keep routes separate from persistence and file operations.
3. Enforce content/size validation, safe storage names, upload cleanup, CORS, and
   streaming/range playback. Preserve original bytes and restart persistence.
4. Test contract behavior and failure cases using temporary storage. Include WAV
   and MP3, range requests, restart persistence, duplicate filenames, path-like
   names, oversized/invalid files, and storage failures. Update backend README.
5. Run `make check-backend` and `git diff --check`; commit, push, and open a PR when
   authorized. Include check results and any frontend/QA handoff notes. Do not merge.

## Done when

All endpoints conform to `docs/api.md`, tests pass without external services, and
the frontend can complete the acceptance flow against this backend. Ask the
coordinator to handle shared contract/CI changes. No auth, processing, or cloud
integration in this task.
