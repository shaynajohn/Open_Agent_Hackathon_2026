from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.errors import AppError
from app.routers import health, integrations, outreach, search


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="MeetMind API",
        version="0.1.0",
        summary="Find people worth meeting and draft a first note.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
    )

    @app.exception_handler(AppError)
    async def handle_app_error(_request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    app.include_router(health.router)
    app.include_router(integrations.router)
    app.include_router(search.router, prefix="/api")
    app.include_router(outreach.router, prefix="/api")
    return app


app = create_app()
