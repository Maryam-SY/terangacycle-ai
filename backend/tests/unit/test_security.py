"""Principal unique `core.security.principal()` (AD-9, story 1.11)."""

import base64
import hashlib
import hmac
from collections.abc import Iterator

import pytest
from pydantic import SecretStr
from starlette.requests import Request

from app.core import security
from app.core.config import Settings, get_settings
from app.core.errors import DomainError, ErrorCode
from tests.reports import TEST_PEPPER, new_device_id


@pytest.fixture(autouse=True)
def pepper(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("DEVICE_ID_PEPPER", TEST_PEPPER)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _request(*headers: tuple[str, str]) -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/v1/reports",
        "headers": [(name.lower().encode(), value.encode("latin-1")) for name, value in headers],
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
    key = base64.b64encode(b"une-autre-cle-de-32-octets......").decode()
    assert security.device_principal(device_id, base64.b64decode(key)) != first


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


def test_pepper_of_32_bytes_is_the_hmac_key() -> None:
    assert security.device_id_key() == base64.b64decode(TEST_PEPPER)
    # Fin de ligne d'un fichier de secret : ignorée.
    padded = Settings.model_construct(device_id_pepper=SecretStr(TEST_PEPPER + "\n"))
    assert security.device_id_key(padded) == base64.b64decode(TEST_PEPPER)
