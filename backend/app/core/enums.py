"""Énumérations de l'épine (conventions de cohérence), définies une seule fois.

Codes en anglais ; les libellés affichés passent par l'i18n de la PWA.
"""

from enum import StrEnum


class Env(StrEnum):
    DEV = "dev"
    DEMO = "demo"
    PROD = "prod"


class ZoneKind(StrEnum):
    """Niveau d'une Zone (table `zones`, AD-5) : Dakar et ses communes d'arrondissement
    sont des `commune`, leurs subdivisions des `quartier`."""

    COMMUNE = "commune"
    QUARTIER = "quartier"


class Role(StrEnum):
    """Rôles du Glossaire ; l'autorisation qui les applique arrive avec la story 2.5."""

    CITIZEN = "citizen"
    COLLECTOR = "collector"
    RECYCLER = "recycler"
    MODERATOR = "moderator"
    MUNICIPAL_ADMIN = "municipal_admin"


class OrganizationType(StrEnum):
    """Type d'une Organisation (AD-31). `platform` : la ligne système de l'Organisation
    plateforme, responsable des Signalements qu'aucune autre ne couvre."""

    COMMUNE = "commune"
    OPERATOR = "operator"
    COLLECTOR_GROUP = "collector_group"
    ENTERPRISE = "enterprise"
    RECYCLER = "recycler"
    PLATFORM = "platform"


class OrganizationStatus(StrEnum):
    """Statut d'une Organisation : seule une Organisation `active` reçoit des Signalements."""

    ACTIVE = "active"
    SUSPENDED = "suspended"


class ReportStatus(StrEnum):
    """Statut d'un Signalement (AD-3)."""

    PENDING_REVIEW = "pending_review"
    VALIDATED = "validated"
    ASSIGNED = "assigned"
    COLLECTED = "collected"
    REJECTED = "rejected"


class PhotoKind(StrEnum):
    """Nature d'une photo stockée : premier segment de sa clé dans le bucket (AD-13).

    `report_thumb` : miniature d'une photo de Signalement (story 1.18), dérivée par le
    worker, jamais reçue d'un client (`ingest_photo` la refuse).
    """

    REPORT = "report"
    PROOF = "proof"
    REPORT_THUMB = "report_thumb"


class MissionStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class WasteType(StrEnum):
    """Type de déchet ; l'ordre est celui des classes du Modèle (AD-7)."""

    PLASTIC = "plastic"
    METAL = "metal"
    GLASS = "glass"
    ORGANIC = "organic"
    MIXED = "mixed"


class HeapSize(StrEnum):
    """Taille de tas, obligatoire sur chaque Signalement."""

    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class WeightKind(StrEnum):
    """Poids déclaré."""

    WEIGHED = "weighed"
    ESTIMATED = "estimated"


class ProofReviewStatus(StrEnum):
    UNREVIEWED = "unreviewed"
    CONFIRMED = "confirmed"
    CONTESTED = "contested"


class LotStatus(StrEnum):
    AVAILABLE = "available"
    RESERVED = "reserved"


class RejectionReason(StrEnum):
    SPAM = "spam"
    NOT_WASTE = "not_waste"
    OUTSIDE_ZONE = "outside_zone"
    DUPLICATE = "duplicate"
    PERSON_OR_PLATE_VISIBLE = "person_or_plate_visible"
    OTHER = "other"


class ClassificationStatus(StrEnum):
    """État de la Classification serveur d'un Signalement (AD-8)."""

    PENDING = "pending"
    DONE = "done"
    FAILED = "failed"
