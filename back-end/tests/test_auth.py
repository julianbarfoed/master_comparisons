import pytest

from app.auth import AuthenticationFailed, IdentityVerifier, VerifiedIdentity


class FakeIdentityVerifier:
    def verify(self, token: str, /) -> VerifiedIdentity:
        if token != "valid-token":
            raise AuthenticationFailed
        return VerifiedIdentity(subject="user-123")


def authenticate(verifier: IdentityVerifier, token: str) -> VerifiedIdentity:
    return verifier.verify(token)


def test_verifier_returns_a_provider_neutral_identity():
    identity = authenticate(FakeIdentityVerifier(), "valid-token")

    assert identity == VerifiedIdentity(subject="user-123")


def test_verifier_exposes_a_typed_authentication_failure():
    with pytest.raises(AuthenticationFailed):
        authenticate(FakeIdentityVerifier(), "invalid-token")


@pytest.mark.parametrize("subject", ["", " ", "\n\t"])
def test_verified_identity_rejects_a_blank_subject(subject: str):
    with pytest.raises(ValueError, match="subject must not be blank"):
        VerifiedIdentity(subject=subject)
