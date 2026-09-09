The scaffold had no shared development workflow or automated checks. This
foundation gives agents a working baseline and general collaboration guidelines.
Concrete feature specs, service choices, and interfaces are supplied when launching
tasks using a reusable brief template.

## Changes

- Add general working agreements, a task brief template, and a tmux/worktree/PR
  review process with an example auth/database/R2/API/frontend split.
- Add Make setup/run/check targets, pytest and Vitest/Testing Library harnesses,
  independent backend/frontend CI jobs, and a PR template.
- Add a service-independent `/health` endpoint and one smoke test per app.
- Fix backend package discovery and frontend typechecking; stop emitting Vite
  configuration artifacts and remove the three previously tracked generated files.
- Upgrade frontend tooling to Vite 7.3.6, React plugin 5.2.0, and Vitest 4.1.11
  after dependency audit findings. Frontend requires Node 22.12+.
- Keep environment examples provider-neutral and ignore credentials, local audio
  data, caches, and agent worktrees.

## Validation

- Fresh Python virtual environment and editable development install: passed.
- `npm ci --offline --no-audit`: passed using the freshly populated package cache.
- `make check`: backend lint, backend smoke test, frontend smoke test, TypeScript,
  and production build passed on macOS with Python 3.13 and Node 24.14.
- npm audit after the toolchain update: zero reported vulnerabilities.
- CI YAML parse and `git diff --check`: passed. Hosted CI has not run locally;
  the configured runner uses Ubuntu, Python 3.13, and Node 22.
- Backend tests currently emit two upstream Starlette/httpx/AnyIO deprecation
  warnings; tests pass. These are not audio feature tests.

## Handoff

Define the next round's feature scope and interfaces in launch briefs, then assign
agents. Merge this foundation before creating their worktrees. No agents have been
started, no credentials are included, and no database, authentication provider, or
cloud integration has been configured.
