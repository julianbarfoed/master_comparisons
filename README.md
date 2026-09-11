# Audio library

React/TypeScript/Vite frontend and Python/FastAPI backend.

## Navigation

- [README](README.md): installation, run commands, and checks.
- [Working agreements](AGENTS.md): collaboration and documentation rules.
- [Roadmap](docs/ROADMAP.md): agreed architecture, shared contracts, and milestones.
- Component maps: [backend](back-end/README.md), [frontend](front-end/README.md).

## Run locally

Use Python 3.13, Node 22.12+ (or a newer supported major), npm, and Make.
CI uses Python 3.13 and Node 22.

```sh
make setup
```

Start each server in a separate terminal:

```sh
make dev-backend
make dev-frontend
```

Frontend: <http://localhost:5173>. API: <http://localhost:8000>,
with `/health` and interactive documentation at `/docs`.

The current scaffold runs without credentials; real provider integrations are still
pending. Each component's `.env.example` documents its available configuration.
Keep secrets and local test data out of Git; `.env` and `.data/` are ignored.

## Checks

```sh
make check             # backend lint/tests and frontend tests/typecheck/build
make check-backend
make check-frontend
```
