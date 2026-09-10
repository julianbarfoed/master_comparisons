# Audio backend

FastAPI foundation for the audio service. See the root [README](../README.md) and
[agent workflow](../docs/workflow.md).

## Layout

- `app/main.py` — application entry point
- `app/auth.py` — authentication boundary
- `app/config.py` — configuration boundary
- `app/db.py` — database boundary
- `app/storage.py` — object-storage boundary
- `sql/` — database migrations

## Run locally

```sh
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --reload --port 8000
```

`GET /health` returns `{"status":"ok"}` without external services. Audio endpoints,
configuration loading, authentication, persistence, and storage are not implemented
yet. Their requirements and providers are defined in agent task briefs.

Run `make check-backend` from the repository root for lint and tests, or run
`python -m ruff check .` and `python -m pytest` inside the activated environment here.
