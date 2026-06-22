from fastapi import APIRouter, status

from app.dependencies import DBSession, RequiredAuthToken
from app.schemas.auth import UserCreate, UserLogin, UserResponse, TokenResponse
from app.services.auth.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(request: UserCreate, db: DBSession):
    auth_service = AuthService(db)
    return auth_service.register_user(request)


@router.post("/login", response_model=TokenResponse)
def login_user(request: UserLogin, db: DBSession):
    auth_service = AuthService(db)
    return auth_service.login_user(request)


@router.get("/me", response_model=UserResponse)
def get_current_user(token: RequiredAuthToken, db: DBSession):
    auth_service = AuthService(db)
    return auth_service.get_current_user(token)