"""Principal unique `core.security.principal()` (AD-9, story 1.11)."""

import base64
import hashlib
import hmac
from types import SimpleNamespace

import pytest
from pydantic import SecretStr
from starlette.requests import Request

from app.core import security
from app.core.config import Settings
from app.core.errors import DomainError, ErrorCode
from tests.reports import TEST_PEPPER, new_device_id


def _app(pepper: str = TEST_PEPPER) -> SimpleNamespace:
    """Application minimale : les réglages avec lesquels elle a été construite."""
    settings = Settings.model_construct(device_id_pepper=SecretStr(pepper))
    return SimpleNamespace(state=SimpleNamespace(settings=settings))


def _request(*headers: tuple[str, str], app: SimpleNamespace | None = None) -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/v1/reports",
        "headers": [(name.lower().encode(), value.encode("latin-1")) for name, value in headers],
        "app": app or _app(),
    }
    return Request(scope)


def _expected_hash(device_id: str) -> str:
    key = base64.b64decode(TEST_PEPPER)
    return hmac.new(key, device_id.encode("ascii"), hashlib.sha256).hexdigest()


def test_valid_device_id_gives_a_device_principal() -> None:
    device_id = new_device_id()
    assert len(device_id) == 43
    req = _request(("X-Device-Id", device_id))
    principal = security.principal(req)
    assert principal.kind == "device"
    assert principal.device_hash == _expected_hash(device_id)
    assert principal.owner_key == f"device:{principal.device_hash}"
    # Journal d'accès : le type de principal, jamais l'identité.
    assert req.state.role == "device"


def test_hash_is_stable_and_depends_on_the_pepper() -> None:
    device_id = new_device_id()
    first = security.principal(_request(("X-Device-Id", device_id)))
    again = security.principal(_request(("X-Device-Id", device_id)))
    other = security.principal(_request(("X-Device-Id", new_device_id())))
    assert first.device_hash == again.device_hash != other.device_hash
    other_pepper = base64.b64encode(b"une-autre-cle-de-32-octets......").decode()
    elsewhere = security.principal(_request(("X-Device-Id", device_id), app=_app(other_pepper)))
    assert elsewhere.device_hash != first.device_hash


def test_identity_is_absent_from_the_repr() -> None:
    device_id = new_device_id()
    principal = security.principal(_request(("X-Device-Id", device_id)))
    text = repr(principal) + str(principal)
    assert device_id not in text
    assert principal.device_hash not in text
    assert "device:" not in text


@pytest.mark.parametrize(
    "headers",
    [
        (),
        (("X-Device-Id", ""),),
        (("X-Device-Id", "A" * 42),),
        (("X-Device-Id", "A" * 44),),
        (("X-Device-Id", "A" * 42 + "+"),),
        (("X-Device-Id", "A" * 42 + "="),),
        (("X-Device-Id", "A" * 42 + "."),),
        (("X-Device-Id", "A" * 42 + "é"),),
        (("X-Device-Id", " " + "A" * 42),),
        (("X-Device-Id", "A" * 43), ("X-Device-Id", "B" * 43)),
    ],
    ids=[
        "absent",
        "vide",
        "42-caracteres",
        "44-caracteres",
        "plus",
        "egal",
        "point",
        "non-ascii",
        "espace",
        "repete",
    ],
)
def test_invalid_device_id_is_400(headers: tuple[tuple[str, str], ...]) -> None:
    with pytest.raises(DomainError) as exc_info:
        security.principal(_request(*headers))
    assert (exc_info.value.code, exc_info.value.http_status) == (ErrorCode.INVALID_DEVICE_ID, 400)


@pytest.mark.parametrize("value", ["Bearer x", "", "Basic dXNlcjpwYXNz"])
def test_any_authorization_header_is_401(value: str) -> None:
    with pytest.raises(DomainError) as exc_info:
        security.principal(_request(("X-Device-Id", new_device_id()), ("Authorization", value)))
    assert (exc_info.value.code, exc_info.value.http_status) == (ErrorCode.INVALID_TOKEN, 401)


def test_device_id_is_checked_before_the_token() -> None:
    with pytest.raises(DomainError) as exc_info:
        security.principal(_request(("Authorization", "Bearer x")))
    assert exc_info.value.code is ErrorCode.INVALID_DEVICE_ID


@pytest.mark.parametrize(
    "value",
    [
        None,
        "pas du base64 !",
        base64.b64encode(b"16-octets-trop-c").decode(),
        "fake-device_id_pepper-Vq7",
    ],
    ids=["absent", "illisible", "trop-court", "texte"],
)
def test_malformed_pepper_is_refused_without_its_value(value: str | None) -> None:
    settings = Settings.model_construct(device_id_pepper=SecretStr(value) if value else None)
    with pytest.raises(security.InvalidPepperError) as exc_info:
        security.device_id_key(settings)
    assert "DEVICE_ID_PEPPER" in str(exc_info.value)
    if value:
        assert value not in str(exc_info.value)


def test_key_comes_from_the_app_settings_and_is_decoded_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _app()
    calls: list[Settings] = []
    original = security.device_id_key

    def counting(settings: Settings) -> bytes:
        calls.append(settings)
        return original(settings)

    monkeypatch.setattr(security, "device_id_key", counting)
    for _ in range(3):
        security.principal(_request(("X-Device-Id", new_device_id()), app=app))
    assert calls == [app.state.settings]
    assert app.state.device_id_key == base64.b64decode(TEST_PEPPER)
    # Clé posée au démarrage (lifespan) : jamais redécodée.
    started = _app()
    started.state.device_id_key = b"k" * 32
    device_id = new_device_id()
    found = security.principal(_request(("X-Device-Id", device_id), app=started))
    assert found.device_hash == hmac.new(b"k" * 32, device_id.encode(), hashlib.sha256).hexdigest()
    assert len(calls) == 1


def test_pepper_of_32_bytes_is_the_hmac_key() -> None:
    settings = Settings.model_construct(device_id_pepper=SecretStr(TEST_PEPPER))
    assert security.device_id_key(settings) == base64.b64decode(TEST_PEPPER)
    # Fin de ligne d'un fichier de secret : ignorée.
    padded = Settings.model_construct(device_id_pepper=SecretStr(TEST_PEPPER + "\n"))
    assert security.device_id_key(padded) == base64.b64decode(TEST_PEPPER)


# --- Principal générique (story 1.12) --------------------------------------------------


def test_user_principal_has_an_owner_key_and_no_device_hash() -> None:
    user_id = "6f1c2a4e-1b2c-4d3e-8f90-a1b2c3d4e5f6"
    principal = security.Principal(kind="user", owner_key=f"user:{user_id}")
    assert principal.kind == "user"
    assert principal.owner_key == f"user:{user_id}"
    assert principal.device_hash is None
    assert user_id not in repr(principal)


@pytest.mark.parametrize(
    ("kind", "owner_key"),
    [
        ("user", "device:" + "a" * 64),
        ("device", "user:Qz9"),
        ("device", "device:"),
        ("user", "Qz9"),
    ],
    ids=["user-cle-appareil", "appareil-cle-user", "identifiant-vide", "sans-prefixe"],
)
def test_owner_key_must_match_the_kind_without_echoing_it(kind: str, owner_key: str) -> None:
    with pytest.raises(ValueError) as exc_info:
        security.Principal(kind=kind, owner_key=owner_key)  # type: ignore[arg-type]
    assert owner_key not in str(exc_info.value)
