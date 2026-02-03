"""
api/routes.py — FastAPI route definitions
==========================================
All HTTP endpoints are defined here and wired into the app via
`app.include_router(router)` in `api/app.py`.

Endpoint summary
----------------
    GET  /health              — Liveness probe
    POST /metadata            — Set user demographics (age, gender, height, weight)
    POST /scan/start          — Begin a 30–45 s rPPG scan (background thread)
    GET  /scan/status         — Poll scan progress & state
    GET  /scan/result         — Retrieve the full vitals JSON once scan is complete
    POST /scan/reset          — Reset session to idle
    GET  /docs                — Auto-generated Swagger UI (FastAPI built-in)
"""

from fastapi import APIRouter, HTTPException
from api.schemas import (
    UserMetadata,
    ScanRequest,
    StatusResponse,
    VitalsResponse,
)
from api.session import ScanSession
from utils.logger import get_logger

logger = get_logger("api.routes")

router = APIRouter()

# ── Global session instance ──────────────────────────────────────────────────
# One session for the entire application lifetime.  In a multi-user
# deployment you would key sessions by user/token; for an MVP this is fine.
_session = ScanSession()


# ── Health ────────────────────────────────────────────────────────────────────

@router.get("/health")
async def health():
    """Simple liveness check."""
    return {"status": "ok", "service": "rPPG Vital Signs Estimator"}


# ── Metadata ──────────────────────────────────────────────────────────────────

@router.post("/metadata")
async def set_metadata(metadata: UserMetadata):
    """
    Store user demographic data required by the BP estimation model.
    Must be called before starting a scan.

    Body (JSON):
        age        : int     (10–120)
        gender     : str     ("male" | "female" | "other")
        height_cm  : float   (100–250)
        weight_kg  : float   (20–300)
    """
    _session.set_metadata(metadata)
    return {
        "status": "ok",
        "message": "Metadata stored. You can now start a scan via POST /scan/start.",
    }


# ── Scan Control ──────────────────────────────────────────────────────────────

@router.post("/scan/start")
async def start_scan(request: ScanRequest = ScanRequest()):
    """
    Begin an rPPG scan.  The scan runs in a background thread so this
    endpoint returns immediately.

    Body (JSON, all optional):
        algorithm         : "pos" | "chrom"   (default "pos")
        duration_seconds  : int               (20–120, default 45)

    Returns 409 if a scan is already running, or 422 if metadata is missing.
    """
    success = _session.start_scan(
        algorithm=request.algorithm,
        duration_seconds=request.duration_seconds,
    )
    if not success:
        current_status = _session.status
        if current_status == "scanning":
            raise HTTPException(status_code=409, detail="A scan is already in progress.")
        raise HTTPException(
            status_code=422,
            detail="Cannot start scan. Set user metadata first via POST /metadata.",
        )

    return {
        "status": "scanning",
        "message": (
            f"Scan started ({request.algorithm}, {request.duration_seconds}s). "
            "Poll GET /scan/status for progress."
        ),
    }


@router.get("/scan/status")
async def scan_status() -> StatusResponse:
    """
    Poll the current scan state and progress percentage.

    Returns
    -------
    StatusResponse
        status           : "idle" | "scanning" | "complete" | "error"
        progress_percent : 0–100  (only meaningful when scanning)
        message          : human-readable description
    """
    status = _session.status
    progress = _session.progress

    messages = {
        "idle":     "No scan in progress. POST /scan/start to begin.",
        "scanning": f"Scan in progress — {progress:.0f}% complete. Keep your face visible.",
        "complete": "Scan complete! Retrieve results via GET /scan/result.",
        "error":    "Scan encountered an error. Check logs or restart.",
    }

    return StatusResponse(
        status=status,
        message=messages.get(status, "Unknown state."),
        progress_percent=progress if status == "scanning" else None,
    )


@router.get("/scan/result")
async def scan_result():
    """
    Retrieve the full vitals JSON after a successful scan.

    Returns 404 if the scan is not yet complete, or 500 if it errored.
    """
    status = _session.status

    if status == "scanning":
        raise HTTPException(status_code=202, detail="Scan still in progress.")
    if status == "idle":
        raise HTTPException(status_code=404, detail="No scan has been run yet.")
    if status == "error":
        raise HTTPException(status_code=500, detail="Scan failed. Reset and try again.")

    result = _session.get_result()
    if result is None:
        raise HTTPException(status_code=500, detail="Result unavailable.")

    return result


@router.post("/scan/reset")
async def scan_reset():
    """Reset the session to idle state so a new scan can be started."""
    _session.reset()
    return {"status": "ok", "message": "Session reset. Ready for a new scan."}
