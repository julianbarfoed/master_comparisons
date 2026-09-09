PYTHON ?= python3
BACKEND_PYTHON := back-end/.venv/bin/python

.PHONY: setup setup-backend setup-frontend dev-backend dev-frontend check check-backend check-frontend

setup: setup-backend setup-frontend

setup-backend:
	$(PYTHON) -m venv back-end/.venv
	$(BACKEND_PYTHON) -m pip install -e './back-end[dev]'

setup-frontend:
	npm --prefix front-end ci

dev-backend:
	cd back-end && .venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

dev-frontend:
	npm --prefix front-end run dev -- --host 127.0.0.1

check: check-backend check-frontend

check-backend:
	$(BACKEND_PYTHON) -m ruff check back-end
	cd back-end && .venv/bin/python -m pytest

check-frontend:
	npm --prefix front-end test
	npm --prefix front-end run build
