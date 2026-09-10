# Audio library

React/TypeScript/Vite frontend and Python/FastAPI backend. This project is also an
exercise in parallel development using separate agent worktrees and reviewed PRs.

## Current state

The foundation includes a static UI, `GET /health`, test harnesses, and CI.
The first round added auth/storage/repository boundaries, a track-listing route
tested with fakes, and a library empty state. Real provider integrations and the
complete user journey are still to be implemented. See the
[product roadmap](docs/ROADMAP.md) for the current assessment and proposed milestones.

## Local setup

Use Python 3.13, Node.js 22.12+ (or a newer supported major), npm, and Make. CI uses
Python 3.13 and Node 22.
Other versions may work (the package supports Python 3.11+).

```sh
make setup
```

This creates `back-end/.venv`, installs backend development dependencies, and runs
`npm ci` in `front-end`. The current scaffold runs without secrets or external
services. Environment examples contain suggested local origins; settings and API
client modules are placeholders. Integration tasks should document any additional
configuration they introduce. Vite loads frontend `.env` variables.

In two terminals:

```sh
make dev-backend
```

```sh
make dev-frontend
```

Open <http://localhost:5173>; backend health is <http://localhost:8000/health> and
interactive API documentation is <http://localhost:8000/docs>.

```sh
make check             # backend lint/tests + frontend tests/typecheck/build
make check-backend
make check-frontend
```

`.data/` is available as an ignored directory for local development data if needed.
Tests must use isolated data. Never commit `.env`, uploaded audio, or credentials.

## Agent development

Read the [working agreements](AGENTS.md) and [worktree workflow](docs/workflow.md).
Use the [task brief template](docs/tasks/TEMPLATE.md) when launching an agent.

The workflow includes an example split across auth, database, R2 storage, API, and
frontend. It is a starting point for assigning work, not a fixed architecture or
feature specification. Merge the foundation before creating agent branches.
