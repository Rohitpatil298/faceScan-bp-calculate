"""
api/app.py — FastAPI application factory
==========================================
Creates and configures the FastAPI instance.  All configuration is
centralised here so that `main.py` stays minimal.

CORS
----
We allow all origins by default (suitable for local development and
demos).  In a production deployment restrict `allow_origins` to your
frontend domain.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from config import API_TITLE, API_VERSION


def create_app() -> FastAPI:
    """
    Construct and return the configured FastAPI application.

    This is a *factory function* (rather than a module-level singleton)
    so that tests can create isolated app instances.
    """
    app = FastAPI(
        title=API_TITLE,
        version=API_VERSION,
        description=(
            "Remote photoplethysmography (rPPG) vital-signs estimation API. "
            "⚠️ WELLNESS TOOL ONLY — not a medical device."
        ),
    )

    # ── CORS ────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],           # Restrict in production!
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Mount routes ────────────────────────────────────────────────────
    app.include_router(router)

    return app
