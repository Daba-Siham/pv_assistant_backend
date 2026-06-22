from datetime import timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.config import settings
from app.core.security import create_access_token, get_user_id_from_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import TokenResponse, UserCreate, UserLogin, UserResponse


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register_user(self, request: UserCreate) -> UserResponse:
        existing_user = self.db.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un utilisateur avec cet email existe déjà."
            )
        user = User(
            full_name=request.full_name,
            email=request.email,
            hashed_password=hash_password(request.password),
            knowledge_level=request.knowledge_level,
            is_active=True,
            is_admin=False
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return UserResponse.model_validate(user)

    def login_user(self, request: UserLogin) -> TokenResponse:
        user = self.db.query(User).filter(User.email == request.email).first()
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou mot de passe incorrect.")
        if not verify_password(request.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou mot de passe incorrect.")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ce compte est désactivé.")
        access_token = create_access_token(
            subject=user.id,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.model_validate(user)
        )

    def get_current_user(self, token: str) -> UserResponse:
        user_id = get_user_id_from_token(token)
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide ou expiré.")
        user = self.db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable.")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ce compte est désactivé.")
        return UserResponse.model_validate(user)