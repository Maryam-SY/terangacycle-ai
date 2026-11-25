"""Routes du module reports.

`POST /v1/reports` : route publique du Citoyen anonyme (liste blanche d'AD-9), identifié
par `X-Device-Id`, exemptée d'`Idempotency-Key` (AD-5). Corps `multipart/form-data` :
`meta` (JSON, `ReportMeta`) et `photo`.

Route synchrone (`def`, pool de threads) : le service ouvre l'unité de travail synchrone
(`@transactional`). Le principal est contrôlé avant le corps (dépendance), puis `meta` ;
la photo est lue sur au plus 1 Mo + 1 octet avant d'être confiée à `ingest_photo()`.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.core import security
from app.core.security import Principal
from app.core.storage import MAX_PHOTO_BYTES
from app.modules.reports import service
from app.modules.reports.schemas import ReportCreated, parse_meta

router = APIRouter(prefix="/v1", tags=["reports"])

# Un octet de plus que le plafond : assez pour que `ingest_photo()` refuse (413) une photo
# trop lourde, sans jamais charger en mémoire un fichier énorme.
PHOTO_READ_LIMIT = MAX_PHOTO_BYTES + 1


@router.post("/reports", status_code=201, summary="Envoyer un Signalement")
def create_report(
    principal: Annotated[Principal, Depends(security.principal)],
    meta: Annotated[
        str,
        Form(
            description=(
                "Métadonnées en JSON : client_uuid, lat, lng, accuracy_m, heap_size, "
                "comment, waste_type, captured_at, consent {terms, training}."
            )
        ),
    ],
    photo: Annotated[
        UploadFile, File(description="Photo du dépôt : JPEG, PNG ou WebP, 1 Mo au plus.")
    ],
) -> ReportCreated:
    parsed = parse_meta(meta)
    data = photo.file.read(PHOTO_READ_LIMIT)
    return service.create_report(principal, parsed, data)
