"""
model/stress.py — Stress Level Estimation
============================================

⚠️  DISCLAIMER: This is a heuristic WELLNESS INDICATOR, not a validated
    clinical stress measure.  True psychological stress is multi-factorial
    and cannot be reliably inferred from a short rPPG recording alone.
    Use this as one data point among many.

────────────────────────────────────────────────────────────────────────
Rationale
────────────────────────────────────────────────────────────────────────
Autonomic nervous system (ANS) balance is one physiological correlate of
psychological stress.  Under acute stress the sympathetic branch
dominates, suppressing heart-rate variability — particularly the
parasympathetic (vagal) component captured by RMSSD.

A large body of psychophysiology research links low RMSSD with elevated
sympathetic tone / perceived stress (e.g., Thayer et al., 2012).

We therefore use RMSSD as a simple proxy:

    RMSSD ≥ 45 ms  →  "Low"      stress  (high vagal tone)
    25 ms ≤ RMSSD < 45 ms  →  "Moderate" stress
    RMSSD < 25 ms  →  "High"     stress  (low vagal tone)

These thresholds are *population averages* and will NOT be accurate for
every individual.  They are chosen to produce reasonable outputs across
a broad range of healthy adults.

We also factor in HR: a resting HR > 90 BPM nudges the stress category
one level higher (a very coarse heuristic).
────────────────────────────────────────────────────────────────────────
"""

from utils.logger import get_logger
from config import STRESS_RMSSD_HIGH, STRESS_RMSSD_MED

logger = get_logger("model.stress")


def estimate_stress(
    hr_bpm: float,
    rmssd_ms: float | None,
    sdnn_ms: float | None = None,
) -> dict:
    """
    Map HRV features to a categorical stress level.

    Parameters
    ----------
    hr_bpm   : float         Heart rate in BPM.
    rmssd_ms : float | None  RMSSD in ms (None if HRV computation failed).
    sdnn_ms  : float | None  SDNN in ms (used as secondary signal; optional).

    Returns
    -------
    dict with keys:
        level       : str     "Low", "Moderate", or "High".
        score       : float   Numeric score in [0, 100] (higher = more stressed).
        confidence  : str     "Low", "Medium", or "High" (data quality indicator).
        description : str     Human-readable explanation.
    """
    # ── Guard: if RMSSD is missing, we cannot estimate stress reliably ────
    if rmssd_ms is None:
        logger.warning("RMSSD unavailable — returning default stress estimate.")
        return {
            "level": "Unknown",
            "score": 50.0,
            "confidence": "Low",
            "description": (
                "Insufficient HRV data to estimate stress. "
                "Ensure your face is clearly visible for the full scan duration."
            ),
        }

    # ── Primary classification from RMSSD ─────────────────────────────────
    if rmssd_ms >= STRESS_RMSSD_HIGH:
        level = "Low"
        # Map RMSSD ∈ [45, ∞) linearly to score ∈ [0, 25]
        # Higher RMSSD → lower stress score
        score = max(0.0, 25.0 - (rmssd_ms - STRESS_RMSSD_HIGH) * 0.5)
    elif rmssd_ms >= STRESS_RMSSD_MED:
        level = "Moderate"
        # Map RMSSD ∈ [25, 45) linearly to score ∈ [25, 60]
        frac = (STRESS_RMSSD_HIGH - rmssd_ms) / (STRESS_RMSSD_HIGH - STRESS_RMSSD_MED)
        score = 25.0 + frac * 35.0
    else:
        level = "High"
        # Map RMSSD ∈ (0, 25) linearly to score ∈ [60, 95]
        frac = 1.0 - (rmssd_ms / STRESS_RMSSD_MED)
        score = 60.0 + frac * 35.0

    # ── Secondary adjustment: elevated HR nudges stress up ───────────────
    # A resting HR > 90 BPM is mildly indicative of sympathetic dominance.
    if hr_bpm > 90:
        score = min(score + 10.0, 100.0)
        if level == "Low":
            level = "Moderate"
        elif level == "Moderate":
            level = "High"

    # ── Confidence: based on how many HRV metrics are available ──────────
    # With a short recording (30–45 s) confidence is inherently limited.
    if sdnn_ms is not None and sdnn_ms > 0:
        confidence = "Medium"   # Both SDNN and RMSSD available
    else:
        confidence = "Low"      # Only RMSSD

    # ── Human-readable description ────────────────────────────────────────
    descriptions = {
        "Low": (
            "Your heart-rate variability suggests a relaxed autonomic state. "
            "This is a positive indicator for overall wellness."
        ),
        "Moderate": (
            "Your HRV indicates a moderate level of autonomic activation. "
            "Consider taking a short break or practising deep breathing."
        ),
        "High": (
            "Your HRV suggests elevated sympathetic nervous system activity, "
            "which may indicate stress or recent physical exertion. "
            "Try relaxation techniques and ensure adequate rest."
        ),
    }

    logger.info("Stress estimate: level=%s, score=%.1f, confidence=%s", level, score, confidence)

    return {
        "level": level,
        "score": round(score, 1),
        "confidence": confidence,
        "description": descriptions.get(level, ""),
    }
