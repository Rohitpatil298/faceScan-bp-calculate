"""
features/hrv.py — Heart Rate Variability (HRV) time-domain features
=====================================================================
Computes the three most commonly used *time-domain* HRV metrics from a
sequence of RR intervals (the time between consecutive heartbeats):

    SDNN  — Standard Deviation of NN intervals
    RMSSD — Root Mean Square of Successive Differences
    pNN50 — Percentage of successive differences > 50 ms

These metrics are well-established in psychophysiology and are used here
as inputs to the blood-pressure and stress-level estimators.

Clinical context (for reference only — this system is NOT clinical)
-------------------------------------------------------------------
* SDNN reflects overall heart-rate variability (sympathetic + parasympathetic).
* RMSSD is dominated by parasympathetic (vagal) tone and is less sensitive
  to non-stationarity than SDNN.  It is the preferred short-term HRV metric.
* pNN50 is a simplified proxy for RMSSD.

⚠️  With only 30–45 seconds of data (≈ 30–60 beats) these estimates will
    have high variance compared to the clinical standard of 5-minute
    recordings.  They are suitable for *trend* and *relative* comparisons
    but should NOT be used for clinical assessment.
"""

import numpy as np
from utils.logger import get_logger
from config import HRV_MIN_PEAKS

logger = get_logger("features.hrv")


def compute_hrv(rr_intervals: list[float]) -> dict:
    """
    Compute time-domain HRV features from RR intervals.

    Parameters
    ----------
    rr_intervals : list[float]
        Successive RR intervals in **seconds**.  Typically extracted by
        `features.hr.estimate_hr()`.

    Returns
    -------
    dict with keys:
        sdnn_ms   : float | None   SDNN in milliseconds.
        rmssd_ms  : float | None   RMSSD in milliseconds.
        pnn50     : float | None   pNN50 as a percentage [0, 100].
        mean_rr_ms: float | None   Mean RR interval in ms.
        num_beats : int            Number of RR intervals used.
        valid     : bool           True if enough intervals were available.

    Notes
    -----
    Returns None for each metric if fewer than HRV_MIN_PEAKS intervals
    are available.
    """
    num_beats = len(rr_intervals)

    if num_beats < HRV_MIN_PEAKS:
        logger.warning(
            "Only %d RR intervals available (need %d for HRV). Returning None values.",
            num_beats,
            HRV_MIN_PEAKS,
        )
        return {
            "sdnn_ms": None,
            "rmssd_ms": None,
            "pnn50": None,
            "mean_rr_ms": None,
            "num_beats": num_beats,
            "valid": False,
        }

    # Convert to milliseconds for standard reporting
    rr_ms = np.array(rr_intervals) * 1000.0   # seconds → ms

    # ── SDNN ──────────────────────────────────────────────────────────────
    # Simple standard deviation of the NN interval series.
    sdnn_ms = float(np.std(rr_ms, ddof=1))   # ddof=1 for sample std

    # ── Mean RR ───────────────────────────────────────────────────────────
    mean_rr_ms = float(np.mean(rr_ms))

    # ── RMSSD ─────────────────────────────────────────────────────────────
    # Successive differences: ΔRR_i = RR_{i+1} − RR_i
    successive_diffs = np.diff(rr_ms)                        # shape (N-1,)
    rmssd_ms = float(np.sqrt(np.mean(successive_diffs ** 2)))

    # ── pNN50 ─────────────────────────────────────────────────────────────
    # Fraction of successive differences whose absolute value exceeds 50 ms.
    count_above_50 = np.sum(np.abs(successive_diffs) > 50.0)
    pnn50 = float(count_above_50 / len(successive_diffs) * 100.0)

    logger.info(
        "HRV — SDNN=%.1f ms, RMSSD=%.1f ms, pNN50=%.1f%%, mean_RR=%.1f ms (%d beats)",
        sdnn_ms, rmssd_ms, pnn50, mean_rr_ms, num_beats,
    )

    return {
        "sdnn_ms": round(sdnn_ms, 2),
        "rmssd_ms": round(rmssd_ms, 2),
        "pnn50": round(pnn50, 2),
        "mean_rr_ms": round(mean_rr_ms, 2),
        "num_beats": num_beats,
        "valid": True,
    }
