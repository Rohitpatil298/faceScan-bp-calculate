"""
api/session.py — Scan Session Manager
=======================================
Owns the camera, face detector, rPPG pipeline, and orchestrates a
single end-to-end scan in a background thread.  The FastAPI routes
interact with this object to start scans, poll progress, and retrieve
results.

Thread safety
-------------
All mutable state that is read by the FastAPI request handlers and
written by the scan thread is protected by `_lock`.  The public
properties (`status`, `progress`, `result`) acquire the lock before
reading.

Lifecycle
---------
    1. `set_metadata(...)` — store user demographics.
    2. `start_scan(...)` — launches the background capture thread.
    3. Poll `status` / `progress` from the client.
    4. When `status == "complete"`, call `get_result()`.
    5. `reset()` — prepare for the next scan.
"""

import time
import threading
import math
import numpy as np
from camera.capture import CameraCapture
# FaceDetector is imported lazily inside _run_scan() so the server
# boots cleanly even before mediapipe is installed.
from rppg.pipeline import RPPGPipeline
from features.hr import estimate_hr
from features.hrv import compute_hrv
from model.bp_model import BPEstimator
from model.stress import estimate_stress
from config import CAMERA_FPS, SCAN_DURATION_SECONDS
from utils.logger import get_logger
from api.schemas import UserMetadata

logger = get_logger("api.session")

# ── Disclaimer string injected into every response ──────────────────────────
DISCLAIMER = (
    "⚠️ This is a WELLNESS ESTIMATION tool — NOT a medical device. "
    "Heart rate, HRV, blood pressure, and stress values are ESTIMATES "
    "derived from remote photoplethysmography (rPPG) and lightweight ML. "
    "They have NOT been validated for clinical use. "
    "Do NOT make medical decisions based on these readings. "
    "Consult a qualified healthcare professional for diagnosis or treatment."
)


def _compute_bmi(height_cm: float, weight_kg: float) -> float:
    """BMI = weight (kg) / height (m)²."""
    height_m = height_cm / 100.0
    return weight_kg / (height_m ** 2)


class ScanSession:
    """
    Manages the full lifecycle of one rPPG vital-signs scan.

    Instantiate once at application startup and reuse across requests.
    """

    def __init__(self):
        self._lock = threading.Lock()

        # State
        self._status = "idle"            # idle | scanning | complete | error
        self._progress = 0.0             # 0–100
        self._error_message = ""
        self._result: dict | None = None
        self._metadata: UserMetadata | None = None

        # Heavy objects (created lazily)
        self._bp_estimator: BPEstimator | None = None

        logger.info("ScanSession initialised.")

    # ── Public API ─────────────────────────────────────────────────────────

    def set_metadata(self, metadata: UserMetadata) -> None:
        """Store the user's demographic data for BP estimation."""
        with self._lock:
            self._metadata = metadata
        logger.info("Metadata set: age=%d, gender=%s", metadata.age, metadata.gender)

    @property
    def status(self) -> str:
        with self._lock:
            return self._status

    @property
    def progress(self) -> float:
        with self._lock:
            return self._progress

    def get_result(self) -> dict | None:
        with self._lock:
            return self._result

    def start_scan(self, algorithm: str = "pos", duration_seconds: int = SCAN_DURATION_SECONDS) -> bool:
        """
        Launch the scan in a background thread.

        Returns False if a scan is already running or metadata is missing.
        """
        with self._lock:
            if self._status == "scanning":
                logger.warning("Scan already in progress.")
                return False
            if self._metadata is None:
                logger.error("Metadata not set — cannot start scan.")
                self._status = "error"
                self._error_message = "User metadata must be set before scanning."
                return False
            self._status = "scanning"
            self._progress = 0.0
            self._result = None
            self._error_message = ""

        # Lazily initialise the BP model (first call trains it)
        if self._bp_estimator is None:
            self._bp_estimator = BPEstimator()

        thread = threading.Thread(
            target=self._run_scan,
            args=(algorithm, duration_seconds),
            daemon=True,
        )
        thread.start()
        logger.info("Scan thread started (algo=%s, duration=%ds).", algorithm, duration_seconds)
        return True

    def reset(self) -> None:
        """Reset session to idle state."""
        with self._lock:
            self._status = "idle"
            self._progress = 0.0
            self._result = None
            self._error_message = ""
        logger.info("Session reset.")

    # ── Private: scan loop ─────────────────────────────────────────────────

    def _run_scan(self, algorithm: str, duration_seconds: int) -> None:
        """
        The entire scan pipeline runs here in a background thread:
            open camera → detect faces → collect RGB → extract pulse
            → compute HR → compute HRV → estimate BP → estimate stress.
        """
        # Lazy import — keeps the server bootable even without mediapipe.
        # The ImportError (with install instructions) surfaces here if missing.
        from face.detector import FaceDetector

        camera = CameraCapture()
        face_detector = FaceDetector()
        pipeline = RPPGPipeline(fps=CAMERA_FPS, algorithm=algorithm)

        try:
            # ── Open camera ─────────────────────────────────────────────
            if not camera.open():
                self._set_error("Failed to open camera. Check webcam permissions.")
                return

            # Wait for the first frame
            first = camera.wait_for_frame(timeout=3.0)
            if first is None:
                self._set_error("No frame received from camera.")
                return

            start_time = time.time()
            elapsed = 0.0

            logger.info("Capturing for %d seconds…", duration_seconds)

            # ── Main capture loop ───────────────────────────────────────
            while elapsed < duration_seconds:
                frame = camera.get_latest_frame()
                if frame is None:
                    time.sleep(0.02)
                    continue

                # Face detection + ROI extraction
                rois = face_detector.detect(frame)

                # Feed ROIs into the rPPG pipeline (skips if no face)
                pipeline.add_frame(rois)

                # Update progress
                elapsed = time.time() - start_time
                pct = min((elapsed / duration_seconds) * 100.0, 100.0)
                with self._lock:
                    self._progress = round(pct, 1)

                time.sleep(0.01)   # Avoid busy-spinning; ~100 iterations/s max

            # ── Signal processing ───────────────────────────────────────
            logger.info("Capture complete. Running signal processing…")

            pulse = pipeline.extract_pulse()   # May raise ValueError

            # Determine effective FPS from the pipeline buffer
            effective_fps = CAMERA_FPS   # Use configured value

            # ── HR estimation ───────────────────────────────────────────
            hr_result = estimate_hr(pulse, effective_fps)

            # ── HRV estimation ──────────────────────────────────────────
            hrv_result = compute_hrv(hr_result["rr_intervals"])

            # ── BP estimation ───────────────────────────────────────────
            meta = self._metadata  # guaranteed non-None by start_scan guard
            bmi = _compute_bmi(meta.height_cm, meta.weight_kg)
            gender_male = 1 if meta.gender == "male" else 0

            bp_result = self._bp_estimator.predict(  # type: ignore[union-attr]
                hr=hr_result["hr_bpm"],
                rmssd=hrv_result["rmssd_ms"] or 30.0,   # fallback if None
                sdnn=hrv_result["sdnn_ms"] or 20.0,
                pnn50=hrv_result["pnn50"] or 10.0,
                age=meta.age,
                gender_male=gender_male,
                bmi=bmi,
            )

            # ── Stress estimation ───────────────────────────────────────
            stress_result = estimate_stress(
                hr_bpm=hr_result["hr_bpm"],
                rmssd_ms=hrv_result["rmssd_ms"],
                sdnn_ms=hrv_result["sdnn_ms"],
            )

            # ── Assemble final response ─────────────────────────────────
            result = {
                "disclaimer": DISCLAIMER,
                "hr": {
                    "hr_bpm": hr_result["hr_bpm"],
                    "hr_fft": hr_result["hr_fft"],
                    "hr_peaks": hr_result["hr_peaks"],
                    "confidence_fft": hr_result["confidence_fft"],
                    "confidence_peaks": hr_result["confidence_peaks"],
                },
                "hrv": hrv_result,
                "blood_pressure": bp_result,
                "stress": stress_result,
                "scan_duration_seconds": round(elapsed, 1),
                "algorithm_used": algorithm,
            }

            with self._lock:
                self._status = "complete"
                self._progress = 100.0
                self._result = result

            logger.info("Scan complete. HR=%.1f BPM, BP=%s/%s mmHg",
                        hr_result["hr_bpm"],
                        bp_result["systolic"],
                        bp_result["diastolic"])

        except ValueError as e:
            self._set_error(f"Signal processing error: {e}")
        except Exception as e:
            self._set_error(f"Unexpected error during scan: {e}")
            logger.exception("Scan failed with exception:")
        finally:
            camera.release()
            face_detector.close()

    def _set_error(self, message: str) -> None:
        with self._lock:
            self._status = "error"
            self._error_message = message
        logger.error("Scan error: %s", message)
