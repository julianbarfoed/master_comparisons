import json
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt import PyJWK
from jwt.algorithms import RSAAlgorithm
from jwt.exceptions import PyJWKClientConnectionError

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
        self.signing_key = signing_key
        self.refreshes = 0

    def get_signing_keys(self, refresh: bool = False) -> list[PyJWK]:
        if refresh:
            self.refreshes += 1
        return [self.signing_key]


class UnavailableSigningKeyProvider:
    def get_signing_keys(self, refresh: bool = False) -> list[PyJWK]:
        raise PyJWKClientConnectionError("JWKS endpoint unavailable")


@pytest.fixture(scope="module")
def private_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture(scope="module")
def signing_key(private_key) -> PyJWK:
    jwk = json.loads(RSAAlgorithm.to_jwk(private_key.public_key()))
    jwk.update({"kid": KEY_ID, "alg": "RS256", "use": "sig"})
    return PyJWK.from_dict(jwk)


@pytest.fixture
def verifier(signing_key: PyJWK) -> SupabaseIdentityVerifier:
    return SupabaseIdentityVerifier(
        issuer=ISSUER,
        audience=AUDIENCE,
        jwks_url="https://project-ref.supabase.co/auth/v1/.well-known/jwks.json",
        signing_key_provider=StaticSigningKeyProvider(signing_key),
    )


def encode_token(private_key, **claim_overrides) -> str:
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
    identity = verifier.verify(encode_token(private_key))

    assert identity == VerifiedIdentity(subject="user-123")


def test_rejects_a_token_with_an_invalid_signature(verifier):
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    with pytest.raises(AuthenticationFailed):
        verifier.verify(encode_token(other_key))


def test_rejects_a_shared_secret_token(verifier):
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
    with pytest.raises(AuthenticationFailed):
        verifier.verify(encode_token(private_key, **{claim: value}))


def test_rejects_an_unknown_signing_key(signing_key, private_key):
    provider = StaticSigningKeyProvider(signing_key)
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

    assert provider.refreshes == 1


def test_reports_signing_key_service_outages(private_key):
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
    with pytest.raises(ValueError, match="subject must not be blank"):
        VerifiedIdentity(subject=subject)
