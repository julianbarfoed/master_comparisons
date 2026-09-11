# Backend map

Run/setup/check commands: [root README](../README.md).
Shared contracts and milestones: [roadmap](../docs/ROADMAP.md).

- `app/main.py`, `app/routes/`: application wiring and HTTP endpoints.
- `app/auth.py`: identity verification boundary.
- `app/db.py`, `app/tracks.py`, `app/schemas.py`: persistence, track reads, response models.
- `app/storage.py`: object storage boundary.
- `app/config.py`, `sql/`: configuration and migrations.
- `tests/`: backend behavior checks.
