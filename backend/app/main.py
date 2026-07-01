"""
===============================================================================
GeoSentinel AI

Module:
    main.py

Description:
    FastAPI application factory and entry point.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from contextlib import asynccontextmanager

import yaml
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.routes import router
from src.utils.logger import logger
from src.utils.paths import paths


# =============================================================================
# Lifespan
# =============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.

    Startup: Log configuration and warm up dependencies.
    Shutdown: Log clean shutdown.
    """

    logger.info("GeoSentinel AI backend starting ...")

    # Ensure output directories exist
    paths.create_all_directories()

    logger.info(
        f"Project root: {paths.PROJECT_ROOT}"
    )

    yield

    logger.info("GeoSentinel AI backend shutting down.")


# =============================================================================
# Application Factory
# =============================================================================


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    """

    # Load API config
    api_config = {}
    api_config_path = paths.CONFIGS_DIR / "api.yaml"

    if api_config_path.exists():
        with open(api_config_path, "r") as f:
            raw = yaml.safe_load(f)
            api_config = raw.get("api", {})

    app = FastAPI(
        title=api_config.get("title", "GeoSentinel AI"),
        description=api_config.get(
            "description",
            "Cloud-native geospatial analytics platform.",
        ),
        version=api_config.get("version", "1.0.0"),
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------

    cors_config_path = paths.CONFIGS_DIR / "api.yaml"

    cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

    if cors_config_path.exists():
        with open(cors_config_path, "r") as f:
            raw = yaml.safe_load(f)
            cors_origins = raw.get("cors", {}).get(
                "allow_origins", cors_origins
            )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ------------------------------------------------------------------
    # Routes
    # ------------------------------------------------------------------

    prefix = api_config.get("prefix", "/api/v1")
    app.include_router(router, prefix=prefix)

    logger.info(f"API routes registered under: {prefix}")

    return app


# ------------------------------------------------------------------
# Module-level app instance
# ------------------------------------------------------------------

app = create_app()


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_config=None,
    )
