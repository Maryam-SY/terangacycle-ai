"""Erreurs métier.

Un service lève `DomainError` ; jamais de `HTTPException` dans un service. Le
gestionnaire unique et l'énumération des codes arrivent avec la story 1.2.
"""


class DomainError(Exception):
    """Erreur métier portant un code stable et le statut HTTP à renvoyer."""

    def __init__(self, code: str, http_status: int, message: str | None = None) -> None:
        super().__init__(message or code)
        self.code = code
        self.http_status = http_status
        self.message = message or code

    def __repr__(self) -> str:
        return f"DomainError(code={self.code!r}, http_status={self.http_status})"
