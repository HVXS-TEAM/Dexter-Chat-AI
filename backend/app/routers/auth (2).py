from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.schemas.auth import (
    UserCreate,
    UserResponse,
    UserProfileUpdate,
    Token,
)
from app.services.auth_service import AuthService
from app.auth.dependencies import get_current_user
from app.db.session import get_db

router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/auth/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db=Depends(get_db)):
    service = AuthService(db)
    try:
        return service.register(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/auth/login", response_model=Token)
def login(payload: LoginRequest, db=Depends(get_db)):
    service = AuthService(db)
    try:
        return service.login(payload.email, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))


@router.post("/auth/refresh", response_model=Token)
def refresh(payload: RefreshRequest, db=Depends(get_db)):
    service = AuthService(db)
    try:
        return service.refresh(payload.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))


@router.get("/auth/me", response_model=UserResponse)
def get_profile(user=Depends(get_current_user), db=Depends(get_db)):
    service = AuthService(db)
    try:
        return service.get_profile(user["id"])
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.patch("/auth/me", response_model=UserResponse)
def update_profile(
    payload: UserProfileUpdate,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    service = AuthService(db)
    try:
        return service.update_profile(user["id"], payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
