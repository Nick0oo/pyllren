import sentry_sdk
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import settings
from sqlmodel import Session
from app.core.db import engine, init_db


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)
# print("🔍 CORS origins cargados:", settings.all_cors_origins)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.on_event("startup")
def on_startup() -> None:
    """Initialize DB data on application startup (roles, first superuser) if missing.

    This mirrors the behaviour of `scripts/prestart.sh` => `python app/initial_data.py`.
    Running the server directly (without the prestart script) would otherwise leave
    the DB without initial roles which makes endpoints like `/signup` fail.
    """
    try:
        with Session(engine) as session:
            init_db(session)
    except Exception:
        # Don't raise on startup; let the app start and allow separate prestart/migrations
        # to be executed. This is defensive: if DB isn't available at startup the
        # prestart container or external orchestration should handle it.
        pass
