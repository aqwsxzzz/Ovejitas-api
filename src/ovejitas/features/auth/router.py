from typing import Annotated

from fastapi import APIRouter, Depends, status

from ovejitas.core.deps import DBSession
from ovejitas.features.auth.deps import CurrentUser
from ovejitas.features.auth.schemas import (
    LoginInput,
    MeResponse,
    RefreshInput,
    RegisterInput,
    TokenPair,
)
from ovejitas.features.auth.service import AuthService


def get_auth_service(db: DBSession) -> AuthService:
    return AuthService(db)


AuthSvc = Annotated[AuthService, Depends(get_auth_service)]

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterInput, svc: AuthSvc) -> TokenPair:
    return await svc.register(data)


@router.post("/login", response_model=TokenPair)
async def login(data: LoginInput, svc: AuthSvc) -> TokenPair:
    return await svc.login(data)


@router.post("/refresh", response_model=TokenPair)
async def refresh(data: RefreshInput, svc: AuthSvc) -> TokenPair:
    return await svc.refresh(data.refresh_token)


@router.get("/me", response_model=MeResponse)
async def me(user: CurrentUser, svc: AuthSvc) -> MeResponse:
    return await svc.me(user)
