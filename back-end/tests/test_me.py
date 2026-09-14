"""HTTP tests for the authenticated identity endpoint and CORS behavior."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.auth import AuthenticationFailed, AuthenticationServiceUnavailable, VerifiedIdentity
from app.dependencies import get_identity_verifier
from app.main import app


class StubIdentityVerifier:
    def __init__(self, *, failure: Exception | None = None) -> None:
        """Return one identity or a requested typed auth failure."""
        self.failure = failure
        self.tokens: list[str] = []

    def verify(self, token: str, /) -> VerifiedIdentity:
        """Record the token and return the configured test outcome."""
        self.tokens.append(token)
        if self.failure is not None:
            raise self.failure
        return VerifiedIdentity(subject="user-123")


@pytest.fixture(autouse=True)
def clear_dependency_overrides() -> Iterator[None]:
    """Keep FastAPI overrides and the cached settings verifier isolated per test."""
    yield
    app.dependency_overrides.clear()
    get_identity_verifier.cache_clear()


def use_verifier(verifier: StubIdentityVerifier) -> None:
    """Replace the production verifier with a deterministic test double."""
    app.dependency_overrides[get_identity_verifier] = lambda: verifier


def test_me_returns_the_verified_subject():
    """Return the subject supplied by a successful verifier."""
    verifier = StubIdentityVerifier()
    use_verifier(verifier)

    with TestClient(app) as client:
        response = client.get("/me", headers={"Authorization": "Bearer valid-token"})

    assert response.status_code == 200
    assert response.json() == {"id": "user-123"}
    assert verifier.tokens == ["valid-token"]


def test_me_allows_authorization_preflight_from_the_frontend_origin():
    """Allow the frontend to preflight a bearer-authenticated GET request."""
    with TestClient(app) as client:
        response = client.options(
            "/me",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "authorization" in response.headers["access-control-allow-headers"].lower()


def test_me_rejects_missing_credentials():
    """Return 401 and a Bearer challenge when no authorization header exists."""
    use_verifier(StubIdentityVerifier())

    with TestClient(app) as client:
        response = client.get("/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}
    assert response.headers["www-authenticate"] == "Bearer"


def test_me_rejects_invalid_credentials():
    """Map verifier credential failures to 401."""
    use_verifier(StubIdentityVerifier(failure=AuthenticationFailed()))

    with TestClient(app) as client:
        response = client.get("/me", headers={"Authorization": "Bearer invalid-token"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}


def test_me_reports_verification_service_outages():
    """Map signing-key service failures to 503."""
    use_verifier(StubIdentityVerifier(failure=AuthenticationServiceUnavailable()))

    with TestClient(app) as client:
        response = client.get("/me", headers={"Authorization": "Bearer any-token"})

    assert response.status_code == 503
    assert response.json() == {"detail": "Authentication service unavailable"}


def test_me_reports_missing_auth_configuration(monkeypatch):
    """Treat absent Supabase settings as an unavailable auth dependency."""
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    get_identity_verifier.cache_clear()

    with TestClient(app) as client:
        response = client.get("/me", headers={"Authorization": "Bearer any-token"})

    assert response.status_code == 503
    assert response.json() == {"detail": "Authentication service unavailable"}
