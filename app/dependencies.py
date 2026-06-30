from typing import Annotated

from fastapi import Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import SessionLocal
from app.core.security import get_user_id_from_token
from app.models.user import User


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DBSession = Annotated[Session, Depends(get_db)]


def get_pagination_params(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100)
) -> dict:
    return {
        "skip": skip,
        "limit": limit
    }


PaginationParams = Annotated[dict, Depends(get_pagination_params)]


def get_authorization_token(
    authorization: Annotated[str | None, Header()] = None
) -> str | None:
    if authorization is None:
        return None

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Format du token invalide"
        )

    return authorization.replace("Bearer ", "").strip()


AuthToken = Annotated[str | None, Depends(get_authorization_token)]


def require_auth_token(token: AuthToken) -> str:
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentification requise"
        )

    return token


RequiredAuthToken = Annotated[str, Depends(require_auth_token)]


def require_admin_user(token: AuthToken, db: Session = Depends(get_db)) -> User:
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentification requise"
        )

    user_id = get_user_id_from_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur introuvable"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ce compte est désactivé"
        )

    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès administrateur requis"
        )

    return user


AdminUser = Annotated[User, Depends(require_admin_user)]


def get_app_settings():
    return settings


AppSettings = Annotated[type(settings), Depends(get_app_settings)]


def validate_installation_type(installation_type: str) -> str:
    allowed_types = ["on-grid", "off-grid", "hybride"]

    if installation_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Type d'installation invalide. Valeurs autorisées : on-grid, off-grid, hybride"
        )

    return installation_type


def validate_coordinates(latitude: float, longitude: float) -> None:
    if latitude < -90 or latitude > 90:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Latitude invalide"
        )

    if longitude < -180 or longitude > 180:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Longitude invalide"
        )
