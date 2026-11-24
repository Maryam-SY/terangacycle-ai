"""`infra/gen-dev-secrets.py` : la clé S3 de Garage forme un seul jeu de trois fichiers."""

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

from app.core.config import REQUIRED_SECRETS

SCRIPT = Path(__file__).resolve().parents[3] / "infra" / "gen-dev-secrets.py"
ACCESS, SECRET = "GKexisting000000000000aa", "existing-secret-key"  # noqa: S105 (factices)


@pytest.fixture
def gen(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    spec = importlib.util.spec_from_file_location("gen_dev_secrets", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    secrets_dir = tmp_path / ".env.secrets"
    secrets_dir.mkdir()
    (tmp_path / ".env").write_text("ENV=demo\n", encoding="utf-8")  # pas de copie de .env
    monkeypatch.setattr(module, "REPO", tmp_path)
    monkeypatch.setattr(module, "SECRETS_DIR", secrets_dir)
    return module


def _read(gen: ModuleType, name: str) -> str:
    return (gen.SECRETS_DIR / name).read_text(encoding="utf-8")


def _garage_keys(gen: ModuleType) -> tuple[str, str]:
    keys = gen._read_garage_keys(gen.SECRETS_DIR / "garage.env")
    assert keys is not None
    return keys


def test_creates_the_whole_inventory(gen: ModuleType) -> None:
    assert gen.main([]) == 0
    for name in REQUIRED_SECRETS:
        assert _read(gen, name).strip(), name
    access, secret = _garage_keys(gen)
    assert (_read(gen, "s3_access_key_id"), _read(gen, "s3_secret_access_key")) == (access, secret)


def test_reuses_complete_garage_env(gen: ModuleType) -> None:
    (gen.SECRETS_DIR / "garage.env").write_text(
        f"GARAGE_DEFAULT_ACCESS_KEY={ACCESS}\nGARAGE_DEFAULT_SECRET_KEY={SECRET}\n",
        encoding="utf-8",
    )
    # Fichiers S3 d'une autre clé : réalignés sur garage.env.
    (gen.SECRETS_DIR / "s3_access_key_id").write_text("GKautre", encoding="utf-8")
    assert gen.main([]) == 0
    assert _garage_keys(gen) == (ACCESS, SECRET)
    assert _read(gen, "s3_access_key_id") == ACCESS
    assert _read(gen, "s3_secret_access_key") == SECRET


@pytest.mark.parametrize(
    "garage_env",
    [None, f"GARAGE_DEFAULT_ACCESS_KEY={ACCESS}\n"],
    ids=["absent", "partiel"],
)
def test_regenerates_the_set_together(gen: ModuleType, garage_env: str | None) -> None:
    if garage_env is not None:
        (gen.SECRETS_DIR / "garage.env").write_text(garage_env, encoding="utf-8")
    (gen.SECRETS_DIR / "s3_access_key_id").write_text(ACCESS, encoding="utf-8")
    (gen.SECRETS_DIR / "s3_secret_access_key").write_text(SECRET, encoding="utf-8")
    assert gen.main([]) == 0
    access, secret = _garage_keys(gen)
    assert access != ACCESS
    assert (_read(gen, "s3_access_key_id"), _read(gen, "s3_secret_access_key")) == (access, secret)


def test_other_secrets_are_kept(gen: ModuleType) -> None:
    (gen.SECRETS_DIR / "phone_pepper").write_text("pepper-existant", encoding="utf-8")
    assert gen.main([]) == 0
    assert _read(gen, "phone_pepper") == "pepper-existant"
