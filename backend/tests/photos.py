"""Photos de test construites avec Pillow (story 1.10), partagées par les tests unitaires
et d'intégration de `core.storage`. Aucun fichier binaire dans le dépôt."""

import io
import struct
import zlib

from PIL import Image, ImageCms, ImageDraw

ORIENTATION_TAG = 0x0112
GPS_IFD_TAG = 0x8825
MAKE_TAG = 0x010F
# Marqueurs recherchés dans le JPEG stocké : aucun ne doit y figurer.
CAMERA_MAKE = "TerangaTestCam"
XMP_MARKER = b"terangacycle-xmp-secret"
COMMENT_MARKER = b"terangacycle-comment-secret"


def _drawing(size: tuple[int, int]) -> Image.Image:
    """Image simple (aplats) : se compresse bien, même en 4000 × 3000."""
    image = Image.new("RGB", size, (24, 122, 80))
    draw = ImageDraw.Draw(image)
    width, height = size
    draw.rectangle((0, 0, width // 2, height // 3), fill=(217, 72, 43))
    draw.ellipse((width // 4, height // 4, width * 3 // 4, height * 3 // 4), fill=(242, 183, 5))
    return image


def icc_profile() -> bytes:
    return ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()


def jpeg_with_metadata(size: tuple[int, int] = (400, 300), quality: int = 80) -> bytes:
    """JPEG avec EXIF (orientation 6, appareil), GPS, profil ICC, XMP et commentaire."""
    exif = Image.Exif()
    exif[ORIENTATION_TAG] = 6
    exif[MAKE_TAG] = CAMERA_MAKE
    exif[GPS_IFD_TAG] = {1: "N", 2: (14.0, 40.0, 15.0), 3: "W", 4: (17.0, 26.0, 17.0)}
    out = io.BytesIO()
    _drawing(size).save(
        out,
        format="JPEG",
        quality=quality,
        exif=exif,
        icc_profile=icc_profile(),
        comment=COMMENT_MARKER,
        xmp=b"<x:xmpmeta>" + XMP_MARKER + b"</x:xmpmeta>",
    )
    return out.getvalue()


def png_transparent(size: tuple[int, int] = (64, 48)) -> bytes:
    """PNG RVBA : transparent partout sauf un carré rouge opaque en haut à gauche."""
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(image).rectangle((0, 0, 15, 15), fill=(255, 0, 0, 255))
    out = io.BytesIO()
    image.save(out, format="PNG")
    return out.getvalue()


def png_palette_transparent(size: tuple[int, int] = (32, 32)) -> bytes:
    """PNG en palette dont la couleur d'index 0 est transparente."""
    image = Image.new("P", size, 0)
    image.putpalette([0, 0, 0, 0, 0, 255] + [0] * (256 * 3 - 6))
    ImageDraw.Draw(image).rectangle((0, 0, 7, 7), fill=1)
    out = io.BytesIO()
    image.save(out, format="PNG", transparency=0)
    return out.getvalue()


def encoded(fmt: str, size: tuple[int, int] = (48, 32), **params: object) -> bytes:
    out = io.BytesIO()
    image = _drawing(size)
    if fmt == "GIF":
        image = image.convert("P")
    image.save(out, format=fmt, **params)
    return out.getvalue()


def _chunk(kind: bytes, payload: bytes) -> bytes:
    crc = zlib.crc32(kind + payload) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", crc)


def png_header_only(width: int, height: int) -> bytes:
    """En-tête PNG valide (IHDR) suivi d'un IDAT illisible : décoder échouerait."""
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", b"not-zlib-data")
        + _chunk(b"IEND", b"")
    )


def jpeg_markers(data: bytes) -> list[int]:
    """Marqueurs des segments d'en-tête d'un JPEG (de SOI jusqu'à SOS exclu)."""
    assert data[:2] == b"\xff\xd8", "pas un JPEG"
    markers = []
    pos = 2
    while pos + 4 <= len(data):
        assert data[pos] == 0xFF, f"segment inattendu à {pos}"
        marker = data[pos + 1]
        if marker == 0xDA:  # SOS : début des données compressées
            break
        length = struct.unpack(">H", data[pos + 2 : pos + 4])[0]
        markers.append(marker)
        pos += 2 + length
    return markers


# APP1 (EXIF, XMP), APP2 (ICC), APP13 (IPTC), COM (commentaire), etc.
METADATA_MARKERS = frozenset({*range(0xE1, 0xF0), 0xFE})
