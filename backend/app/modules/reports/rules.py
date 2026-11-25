"""Règles pures de la création d'un Signalement (story 1.11), sans base ni horloge."""

TRACKING_PREFIX = "TC"
TRACKING_DIGITS = 6


def format_tracking_number(year: int, sequence: int) -> str:
    """Numéro de suivi `TC-AAAA-NNNNNN` : année de réception UTC, rang complété par des
    zéros."""
    return f"{TRACKING_PREFIX}-{year:04d}-{sequence:0{TRACKING_DIGITS}d}"


def is_imprecise(accuracy_m: float, threshold_m: float) -> bool:
    """Drapeau « position imprécise » : strictement au-delà du seuil (le seuil : non)."""
    return accuracy_m > threshold_m
