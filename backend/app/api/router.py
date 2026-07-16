from fastapi import APIRouter

from app.api.routers import auth, workspace
from app.api import health


api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(workspace.router)
