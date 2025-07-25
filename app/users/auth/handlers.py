# This Python code snippet is setting up API routes using FastAPI. Here's a breakdown of what each
# part does:
from fastapi import APIRouter

from app.users.auth import fastapi_users, auth_backend, UserRead
from app.users.auth.schemas import UserCreate, UserUpdate

router = APIRouter()

router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)
