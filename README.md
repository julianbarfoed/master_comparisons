# Audio library

React/TypeScript/Vite frontend and Python/FastAPI backend. This project is also an
exercise in parallel development using separate agent worktrees and reviewed PRs.

## Current state

The foundation includes a static UI, `GET /health`, test harnesses, and CI.
Upload, persistence, playback, and deletion are specified but **not implemented**.

The first milestone uses SQLite and local file storage for one local user.
Authentication, Supabase/R2, deployment, and audio processing are out of scope for
this milestone. Preserve originals so future processors can create derived audio.

## Local setup

Use Python 3.13, Node.js 22.12+ (or a newer supported major), npm, and Make. CI uses
Python 3.13 and Node 22.
Other versions may work (the package supports Python 3.11+).

```sh
make setup
```

This creates `back-end/.venv`, installs backend development dependencies, and runs
`npm ci` in `front-end`. Copy each `.env.example` to `.env` if you need overrides;
defaults require no secrets. Environment examples describe the target milestone;
the backend agent will implement settings and the frontend agent will connect the
API client. Vite loads frontend `.env` variables.

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

Audio data will live under `back-end/.data/` by default and stay out of Git. Tests
must use temporary directories. Never commit `.env`, uploaded audio, or credentials.

## Agent development

Read [working agreements](AGENTS.md), the [API contract](docs/api.md), and the
[worktree workflow](docs/workflow.md). Task briefs:

- [Backend](docs/tasks/backend.md)
- [Frontend](docs/tasks/frontend.md)
- [Integration/QA](docs/tasks/qa.md)

Merge the foundation before creating agent branches. Backend and frontend can then
work in parallel against the contract; QA prepares tests and validates integration.
