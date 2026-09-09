# Integration/QA agent

Branch: `test/audio-e2e`. Own `e2e/`, including its dependency manifest/lockfile,
test configuration, fixtures, and README. Do not change app code or shared CI.

## To-do

1. Read the contract and establish the app baseline with `make setup` and
   `make check`. Add a self-contained Playwright project under `e2e/`.
2. Prepare a small generated audio fixture and browser tests for the contract's
   acceptance flow. Use temporary data and deterministic startup/teardown;
   document dependency/browser installation and a single test command.
3. Cover upload, visible list state, playback/seek, refresh persistence, invalid
   upload feedback, and deletion. Add a restart check proving persistence across
   backend processes. Ensure tests require actual API responses, not app mocks.
4. Request a combined integration checkout from the coordinator when app branches
   are ready. Run tests against it and report candidate commit IDs and exact
   failures. Return fixes to the owning agent; keep integration merge commits out
   of this task branch. Propose the CI invocation to the coordinator.
5. Commit tests and instructions, push, and open a PR when authorized. Report
   unimplemented dependencies as blocked, never as passing. Do not merge.

## Done when

Tests pass against the combined implementation and on the final merged state;
another developer can reproduce them from `e2e/README.md`. No real credentials,
personal audio files, production services, or editing other agents' files.
