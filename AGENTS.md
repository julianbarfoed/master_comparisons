# Working agreements

This repository is a practice project for independent agents working in separate
Git worktrees. Read `README.md`, `docs/api.md`, and your brief in `docs/tasks/`
before making changes.

## Scope and ownership

- First milestone: a local, single-user audio library with upload, list, playback,
  and delete. Use SQLite metadata and local files behind the storage boundary.
- Authentication, cloud providers, deployment, and audio processing are later work.
- Backend agent owns `back-end/`; frontend agent owns `front-end/`; QA owns `e2e/`
  and its fixtures. Each implementation agent owns tests for its own code.
- Root tooling, `.github/`, and `docs/api.md` have a coordinator owner. Flag needed
  changes to that owner rather than editing shared files in parallel.
- Treat `docs/api.md` as the agreed contract. Propose a contract change before
  implementing an incompatible behavior; do not silently invent a second contract.
- Avoid unrelated cleanup and preserve other people's changes.

## Workflow

- Use one task branch and one worktree per agent. Do not switch or edit another
  agent's worktree. The main checkout is reserved for coordination and review.
- Install dependencies inside your worktree. Keep local data, credentials, and
  generated outputs ignored. Never use production services for tests.
- Run the checks relevant to your changes. Backend: `make check-backend`.
  Frontend: `make check-frontend`. QA adds its commands under `e2e/README.md`.
- Tests must cover observable behavior and meaningful failure paths. Tests must
  use temporary storage and must not depend on an existing personal audio library.
- Before handoff, inspect `git diff --check` and your diff. Commit only scoped files.
- When authorized to publish, push the task branch and open a PR using the template.
  Include exact checks and outcomes; distinguish implemented behavior from plans.
- Leave merging to the user. Do not resolve cross-agent ownership conflicts by
  overwriting another agent's work; send a concise handoff with the affected paths.

## Design

- Keep HTTP routes thin; storage and metadata access belong behind explicit
  boundaries that tests can replace. Add modules as behavior requires them.
- Keep original audio bytes intact so later processing can create separate outputs.
- Validate uploads on the backend. Never use a client filename as a storage path.
- Frontend requests go through `front-end/src/lib/api.ts`. Use the documented API
  origin; do not hardcode backend URLs throughout components.
