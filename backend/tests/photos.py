"""Images de test fabriquées avec Pillow, et lecture des segments d'un JPEG."""

import io
import random

from PIL import Image

GPS_IFD = 0x8825
ORIENTATION = 0x0112


def noise(width: int, height: int, mode: str = "RGB", seed: int = 7) -> Image.Image:
    """Image de bruit (peu compressible) : sa taille de fichier ressemble à une photo."""
    rng = random.Random(seed)  # noqa: S311 - pixels de test, pas de cryptographie
    channels = len(mode)
    return Image.frombytes(mode, (width, height), rng.randbytes(width * height * channels))


def encode(image: Image.Image, fmt: str, **params: object) -> bytes:
    out = io.BytesIO()
    image.save(out, fmt, **params)
    return out.getvalue()


def jpeg_with_exif_and_gps(width: int = 80, height: int = 60) -> bytes:
    """JPEG avec orientation 6 (rotation de 90°), EXIF, GPS, ICC et commentaire."""
    image = noise(width, height)
    exif = image.getexif()
    exif[ORIENTATION] = 6
    exif[0x010F] = "FabricantTest"  # Make
    gps = exif.get_ifd(GPS_IFD)
    gps[1] = "N"
    gps[2] = (14.0, 40.0, 15.0)
    gps[3] = "W"
    gps[4] = (17.0, 26.0, 17.0)
    return encode(
        image,
        "JPEG",
        exif=exif,
        icc_profile=b"\x00" * 128,
        comment=b"commentaire secret",
        quality=90,
    )


def jpeg_markers(data: bytes) -> list[int]:
    """Marqueurs des segments d'en-tête d'un JPEG, jusqu'au début des données (SOS)."""
    assert data[:2] == b"\xff\xd8", "pas un JPEG"
    markers = []
    pos = 2
    while pos + 4 <= len(data):
        assert data[pos] == 0xFF, "segment JPEG mal formé"
        marker = data[pos + 1]
        markers.append(marker)
        if marker == 0xDA:  # SOS : les données d'image suivent
            break
        length = int.from_bytes(data[pos + 2 : pos + 4], "big")
        pos += 2 + length
    return markers


def has_metadata(data: bytes) -> bool:
    """Vrai si le JPEG porte un EXIF/XMP (APP1), un ICC (APP2) ou un commentaire (COM)."""
    markers = jpeg_markers(data)
    return 0xE1 in markers or 0xE2 in markers or 0xFE in markers or b"Exif\x00\x00" in data
