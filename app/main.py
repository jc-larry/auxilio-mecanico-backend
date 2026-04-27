from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import init_db
from app.routers import (
    analytics,
    auth,
    inventory,
    mechanics,
    payments,
    ranking,
    roles,
    service_requests,
    uploads,
    users,
    workshops,
    clients,
    bitacora,
    service_types,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(service_requests.router, prefix="/api/v1")
    app.include_router(mechanics.router, prefix="/api/v1")
    app.include_router(inventory.router, prefix="/api/v1")
    app.include_router(analytics.router, prefix="/api/v1")
    app.include_router(users.router, prefix="/api/v1")
    app.include_router(roles.router, prefix="/api/v1")
    app.include_router(roles.permissions_router, prefix="/api/v1")
    app.include_router(ranking.router, prefix="/api/v1")
    app.include_router(uploads.router, prefix="/api/v1")
    app.include_router(payments.router, prefix="/api/v1")
    app.include_router(workshops.router, prefix="/api/v1")
    app.include_router(clients.router, prefix="/api/v1")
    app.include_router(bitacora.router, prefix="/api/v1")
    app.include_router(service_types.router, prefix="/api/v1")

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        return {"status": "ok", "version": settings.app_version}

    return app


app = create_app()
