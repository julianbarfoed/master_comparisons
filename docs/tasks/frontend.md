# Frontend agent

Branch: `feat/audio-frontend`. Own `front-end/` and its tests.
Dependency: merged foundation and `docs/api.md`; backend may still be in progress.

## To-do

1. Read the contract; install with `make setup-frontend` and establish the baseline
   with `make check-frontend`.
2. Add typed requests in `src/lib/api.ts` using `VITE_API_URL`, and contract-based
   mocks for development/tests. Implement upload, list, native audio playback,
   and delete using the existing UI as a starting point.
3. Handle empty/loading/error states, pending actions, and accessible form/button
   labels. Resolve playback paths against the backend origin. Reset the upload
   input so a user can retry the same file. Treat backend validation as authoritative.
4. Test the complete UI flow with mocked API responses and useful failure cases;
   verify actual playback in the browser against the backend when available.
   Update frontend README and include screenshots in the handoff.
5. Run `make check-frontend` and `git diff --check`; commit, push, and open a PR when
   authorized. Describe remaining backend dependencies accurately. Do not merge.

## Done when

The browser supports the shared acceptance flow and the UI tests/build pass.
Keep changes in the frontend; ask the coordinator about contract changes. No
authentication screens, processing controls, waveform editor, or deployment.
