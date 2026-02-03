"""
api/schemas.py — Pydantic request & response models
=====================================================
Centralises all data-transfer objects so that FastAPI can auto-generate
OpenAPI docs and perform input validation for free.
"""

from pydantic import BaseModel, Field
from typing import Optional


# ── Request Models ───────────────────────────────────────────────────────────


class UserMetadata(BaseModel):
    """
    Demographic info needed by the BP estimation model.
    Supplied once via POST /metadata before starting a scan.
    """
    age: int = Field(..., ge=10, le=120, description="Age in years.")
    gender: str = Field(
        ...,
        pattern="^(male|female|other)$",
        description="Biological sex (male / female / other).",
    )
    height_cm: float = Field(..., gt=100, lt=250, description="Height in centimetres.")
    weight_kg: float = Field(..., gt=20, lt=300, description="Weight in kilograms.")


class ScanRequest(BaseModel):
    """Optionally override algorithm and scan duration at scan time."""
    algorithm: str = Field("pos", pattern="^(pos|chrom)$")
    duration_seconds: int = Field(45, ge=20, le=120)


# ── Response Models ──────────────────────────────────────────────────────────


class HRData(BaseModel):
    hr_bpm: float
    hr_fft: float
    hr_peaks: float
    confidence_fft: float
    confidence_peaks: float


class HRVData(BaseModel):
    sdnn_ms: Optional[float] = None
    rmssd_ms: Optional[float] = None
    pnn50: Optional[float] = None
    mean_rr_ms: Optional[float] = None
    num_beats: int
    valid: bool


class BPData(BaseModel):
    systolic: float
    diastolic: float
    unit: str = "mmHg"


class StressData(BaseModel):
    level: str
    score: float
    confidence: str
    description: str


class VitalsResponse(BaseModel):
    """Full vitals payload returned after a successful scan."""
    disclaimer: str
    hr: HRData
    hrv: HRVData
    blood_pressure: BPData
    stress: StressData
    scan_duration_seconds: float
    algorithm_used: str


class StatusResponse(BaseModel):
    status: str                          # "idle" | "scanning" | "error"
    message: str
    progress_percent: Optional[float] = None   # 0–100 during scan
