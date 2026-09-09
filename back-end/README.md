# Audio backend

FastAPI project skeleton for the audio service.

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

No API, authentication, persistence, or storage behavior has been implemented.
