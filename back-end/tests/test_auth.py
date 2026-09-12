"""Unit tests for Supabase token verification and failure classification."""

import json
import time
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt import PyJWK, PyJWKClient
from jwt.algorithms import RSAAlgorithm
from jwt.exceptions import PyJWKClientConnectionError, PyJWKClientError, PyJWKSetError

from app.auth import (
    AuthenticationFailed,
    AuthenticationServiceUnavailable,
    SupabaseIdentityVerifier,
    VerifiedIdentity,
)

ISSUER = "https://project-ref.supabase.co/auth/v1"
AUDIENCE = "authenticated"
KEY_ID = "test-signing-key"


class StaticSigningKeyProvider:
    def __init__(self, signing_key: PyJWK) -> None:
        """Provide a deterministic public key without network access."""
        self.signing_key = signing_key
        self.calls = 0

    def get_signing_key_from_jwt(self, token: str | bytes) -> PyJWK:
        """Return the configured key and count lookup calls."""
        self.calls += 1
        return self.signing_key


class UnavailableSigningKeyProvider:
    def get_signing_key_from_jwt(self, token: str | bytes) -> PyJWK:
        """Simulate a signing-key network outage."""
        raise PyJWKClientConnectionError("JWKS endpoint unavailable")


class UnknownSigningKeyProvider:
    def get_signing_key_from_jwt(self, token: str | bytes) -> PyJWK:
        """Simulate an unknown token key ID returned by the provider."""
        raise PyJWKClientError('Unable to find a signing key that matches: "unknown-key"')


@pytest.fixture(scope="module")
def private_key():
    """Create an isolated RSA key for the test module."""
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture(scope="module")
def signing_key(private_key) -> PyJWK:
    """Convert the test private key's public half to a Supabase-style JWK."""
    jwk = json.loads(RSAAlgorithm.to_jwk(private_key.public_key()))
    jwk.update({"kid": KEY_ID, "alg": "RS256", "use": "sig"})
    return PyJWK.from_dict(jwk)


@pytest.fixture
def verifier(signing_key: PyJWK) -> SupabaseIdentityVerifier:
    """Build a verifier using the deterministic key provider."""
    return SupabaseIdentityVerifier(
        issuer=ISSUER,
        audience=AUDIENCE,
        jwks_url="https://project-ref.supabase.co/auth/v1/.well-known/jwks.json",
        signing_key_provider=StaticSigningKeyProvider(signing_key),
    )


def encode_token(private_key, **claim_overrides) -> str:
    """Create a signed token whose claims can be overridden per test."""
    now = datetime.now(UTC)
    claims = {
        "sub": "user-123",
        "iss": ISSUER,
        "aud": AUDIENCE,
        "iat": now,
        "exp": now + timedelta(minutes=5),
        **claim_overrides,
    }
    return jwt.encode(claims, private_key, algorithm="RS256", headers={"kid": KEY_ID})


def test_verifies_a_valid_supabase_access_token(verifier, private_key):
    """Accept a correctly signed token with the expected claims."""
    identity = verifier.verify(encode_token(private_key))

    assert identity == VerifiedIdentity(subject="user-123")


def test_rejects_a_token_with_an_invalid_signature(verifier):
    """Reject a token signed by a key different from the configured key."""
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    with pytest.raises(AuthenticationFailed):
        verifier.verify(encode_token(other_key))


def test_rejects_a_shared_secret_token(verifier):
    """Reject HS256 even when the token carries a familiar key ID."""
    now = datetime.now(UTC)
    token = jwt.encode(
        {
            "sub": "user-123",
            "iss": ISSUER,
            "aud": AUDIENCE,
            "exp": now + timedelta(minutes=5),
        },
        "untrusted-shared-secret-with-32-bytes",
        algorithm="HS256",
        headers={"kid": KEY_ID},
    )

    with pytest.raises(AuthenticationFailed):
        verifier.verify(token)


def test_rejects_an_expired_token(verifier, private_key):
    """Reject a token whose expiration timestamp has passed."""
    expired_at = datetime.now(UTC) - timedelta(seconds=1)

    with pytest.raises(AuthenticationFailed):
        verifier.verify(encode_token(private_key, exp=expired_at))


@pytest.mark.parametrize(
    ("claim", "value"),
    [
        ("iss", "https://other-project.supabase.co/auth/v1"),
        ("aud", "other-audience"),
    ],
)
def test_rejects_the_wrong_issuer_or_audience(verifier, private_key, claim, value):
    """Reject tokens issued for another project or consumer."""
    with pytest.raises(AuthenticationFailed):
        verifier.verify(encode_token(private_key, **{claim: value}))


def test_rejects_an_unknown_signing_key(signing_key, private_key):
    """Treat a key ID absent from the provider as an invalid credential."""
    provider = UnknownSigningKeyProvider()
    verifier = SupabaseIdentityVerifier(
        issuer=ISSUER,
        audience=AUDIENCE,
        jwks_url="https://project-ref.supabase.co/auth/v1/.well-known/jwks.json",
        signing_key_provider=provider,
    )
    token = jwt.encode(
        {
            "sub": "user-123",
            "iss": ISSUER,
            "aud": AUDIENCE,
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        private_key,
        algorithm="RS256",
        headers={"kid": "unknown-key"},
    )

    with pytest.raises(AuthenticationFailed):
        verifier.verify(token)


def test_bounds_repeated_unknown_key_refreshes(signing_key, private_key, monkeypatch):
    """Use PyJWT's cooldown so repeated unknown IDs do not refetch JWKS."""
    client = PyJWKClient("https://project-ref.supabase.co/auth/v1/.well-known/jwks.json")
    jwk = json.loads(RSAAlgorithm.to_jwk(private_key.public_key()))
    jwk.update({"kid": KEY_ID, "alg": "RS256", "use": "sig"})
    fetches = 0

    def fetch_data():
        nonlocal fetches
        fetches += 1
        client._last_successful_fetch = time.monotonic()
        client.jwk_set_cache.put({"keys": [jwk]})
        return {"keys": [jwk]}

    monkeypatch.setattr(client, "fetch_data", fetch_data)
    verifier = SupabaseIdentityVerifier(
        issuer=ISSUER,
        audience=AUDIENCE,
        jwks_url="https://project-ref.supabase.co/auth/v1/.well-known/jwks.json",
        signing_key_provider=client,
    )
    token = jwt.encode(
        {
            "sub": "user-123",
            "iss": ISSUER,
            "aud": AUDIENCE,
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        private_key,
        algorithm="RS256",
        headers={"kid": "unknown-key"},
    )

    for _ in range(5):
        with pytest.raises(AuthenticationFailed):
            verifier.verify(token)

    assert fetches == 1


@pytest.mark.parametrize(
    "provider_error",
    [
        PyJWKSetError("The JWK Set did not contain any keys"),
        PyJWKSetError("The JWKS endpoint did not return a JSON object"),
        ValueError("malformed JWKS"),
    ],
)
def test_reports_invalid_jwks_responses_as_service_outages(provider_error):
    """Map empty, malformed, and non-JSON key sets to service unavailability."""
    class BrokenSigningKeyProvider:
        def get_signing_key_from_jwt(self, token: str | bytes) -> PyJWK:
            """Return the configured provider failure."""
            raise provider_error

    verifier = SupabaseIdentityVerifier(
        issuer=ISSUER,
        audience=AUDIENCE,
        jwks_url="https://project-ref.supabase.co/auth/v1/.well-known/jwks.json",
        signing_key_provider=BrokenSigningKeyProvider(),
    )

    with pytest.raises(AuthenticationServiceUnavailable):
        verifier.verify("eyJhbGciOiJSUzI1NiIsImtpZCI6InRlc3QifQ.e30.c2lnbmF0dXJl")


def test_reports_signing_key_service_outages(private_key):
    """Map a signing-key connection failure to the service-unavailable error."""
    verifier = SupabaseIdentityVerifier(
        issuer=ISSUER,
        audience=AUDIENCE,
        jwks_url="https://project-ref.supabase.co/auth/v1/.well-known/jwks.json",
        signing_key_provider=UnavailableSigningKeyProvider(),
    )

    with pytest.raises(AuthenticationServiceUnavailable):
        verifier.verify(encode_token(private_key))


@pytest.mark.parametrize("subject", ["", " ", "\n\t"])
def test_verified_identity_rejects_a_blank_subject(subject: str):
    """Reject identities that cannot safely identify an owner."""
    with pytest.raises(ValueError, match="subject must not be blank"):
        VerifiedIdentity(subject=subject)
