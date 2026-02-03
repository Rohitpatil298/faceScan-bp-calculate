"""
face/detector.py — Face detection & skin-ROI extraction
========================================================
Uses Google's MediaPipe Face Mesh (468 landmarks) to:
  1. Detect the face in the current frame.
  2. Compute normalised landmark positions.
  3. Extract rectangular ROIs for the *forehead* and both *cheeks*.

Why these regions?
------------------
The forehead and cheeks are relatively flat, well-lit skin surfaces with
high blood-vessel density.  They produce the strongest rPPG signal while
being less susceptible to motion artefacts than the nose or chin.

ROI shrinking
-------------
Each bounding box is shrunk inward by `ROI_SHRINK` (default 15 %) on all
sides.  This eliminates edge pixels that may fall on hair, ear lobes, or
shadows, which would dilute the pulse signal.
"""

from dataclasses import dataclass, field
import cv2
import numpy as np
# NOTE: mediapipe is imported LAZILY inside FaceDetector.__init__(), not here.
# This lets the FastAPI server boot and serve /health, /metadata, etc.
# even if mediapipe is not yet installed.  A clear error with install
# instructions is raised only when you actually try to start a scan.
from utils.logger import get_logger
from config import (
    FOREHEAD_LANDMARKS,
    CHEEK_LEFT_LANDMARKS,
    CHEEK_RIGHT_LANDMARKS,
    ROI_SHRINK,
)

logger = get_logger("face.detector")


@dataclass
class FaceROIs:
    """Container returned by the detector for a single frame."""
    forehead: np.ndarray | None = None   # Cropped BGR image of the forehead
    cheek_left: np.ndarray | None = None
    cheek_right: np.ndarray | None = None
    landmarks: list = field(default_factory=list)  # Raw (x, y) pixel coords
    face_detected: bool = False


class FaceDetector:
    """
    Wraps MediaPipe FaceMesh and exposes a simple `detect(frame)` method.

    Parameters
    ----------
    max_faces : int
        Maximum number of faces to track simultaneously.  For rPPG we
        only need the closest / largest face, so default is 1.
    """

    def __init__(self, max_faces: int = 1):
        # ── Lazy import of mediapipe ──────────────────────────────────────
        # Intentionally done here (not at module level) so the rest of the
        # application can start even when mediapipe is missing.  The error
        # below lists every available 0.10.x wheel for Python 3.11 / Windows.
        try:
            import mediapipe as mp
        except ImportError:
            raise ImportError(
                "\n"
                "╔══════════════════════════════════════════════════════════════╗\n"
                "║  mediapipe is not installed.                                ║\n"
                "║                                                              ║\n"
                "║  Run ONE of these in your activated .venv:                   ║\n"
                "║                                                              ║\n"
                "║    pip install mediapipe                   ← latest          ║\n"
                "║    pip install mediapipe==0.10.32          ← last 0.10.x     ║\n"
                "║                                                              ║\n"
                "║  Known 0.10.x versions (Python 3.11, Windows):              ║\n"
                "║    0.10.5  0.10.7  0.10.8  0.10.9  0.10.10  0.10.11        ║\n"
                "║    0.10.13 0.10.14 0.10.18 0.10.20 0.10.21  0.10.30        ║\n"
                "║    0.10.31 0.10.32                                           ║\n"
                "║                                                              ║\n"
                "║  After installing, restart:  python main.py                  ║\n"
                "╚══════════════════════════════════════════════════════════════╝\n"
            )

        # MediaPipe FaceMesh solution object
        self._mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=max_faces,
            refine_landmarks=True,       # Uses iris landmarks for extra accuracy
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        logger.info("MediaPipe FaceMesh initialised (max_faces=%d).", max_faces)

    # ── Public API ───────────────────────────────────────────────────────────

    def detect(self, frame_bgr: np.ndarray) -> FaceROIs:
        """
        Run face-mesh inference on a single BGR frame and extract ROIs.

        Parameters
        ----------
        frame_bgr : np.ndarray
            The raw webcam frame in OpenCV BGR format (H×W×3, uint8).

        Returns
        -------
        FaceROIs
            Dataclass carrying the three ROI crops and a detection flag.
        """
        h, w = frame_bgr.shape[:2]

        # MediaPipe expects RGB input
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        results = self._mp_face_mesh.process(frame_rgb)

        roi = FaceROIs()

        if not results.multi_face_landmarks:
            # No face in frame — return empty ROIs
            return roi

        roi.face_detected = True

        # We only use the first (closest) face
        face_lms = results.multi_face_landmarks[0]

        # Convert normalised landmarks to pixel coordinates
        landmarks_px: list[tuple[int, int]] = []
        for lm in face_lms.landmark:
            landmarks_px.append((int(lm.x * w), int(lm.y * h)))
        roi.landmarks = landmarks_px

        # Extract the three ROIs
        roi.forehead = self._extract_roi(frame_bgr, landmarks_px, FOREHEAD_LANDMARKS, h, w)
        roi.cheek_left = self._extract_roi(frame_bgr, landmarks_px, CHEEK_LEFT_LANDMARKS, h, w)
        roi.cheek_right = self._extract_roi(frame_bgr, landmarks_px, CHEEK_RIGHT_LANDMARKS, h, w)

        return roi

    def close(self) -> None:
        """Release MediaPipe resources."""
        self._mp_face_mesh.close()
        logger.info("FaceMesh closed.")

    # ── Private helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _extract_roi(
        frame: np.ndarray,
        landmarks: list[tuple[int, int]],
        roi_landmark_indices: list[int],
        frame_h: int,
        frame_w: int,
    ) -> np.ndarray | None:
        """
        Given a set of landmark indices that define the corners of a region,
        compute the axis-aligned bounding box, shrink it inward, and return
        the cropped sub-image.

        Returns None if the resulting ROI has zero area (e.g. landmarks
        collapsed to a line).
        """
        # Gather the (x, y) pixel positions for the chosen landmarks
        points = [landmarks[i] for i in roi_landmark_indices]
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]

        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)

        # Shrink the box inward to exclude border artefacts
        roi_w = x_max - x_min
        roi_h = y_max - y_min
        shrink_x = int(roi_w * ROI_SHRINK)
        shrink_y = int(roi_h * ROI_SHRINK)

        x_min += shrink_x
        x_max -= shrink_x
        y_min += shrink_y
        y_max -= shrink_y

        # Clamp to frame boundaries
        x_min = max(0, x_min)
        y_min = max(0, y_min)
        x_max = min(frame_w, x_max)
        y_max = min(frame_h, y_max)

        # Guard against degenerate (zero-area) ROIs
        if x_max <= x_min or y_max <= y_min:
            return None

        return frame[y_min:y_max, x_min:x_max].copy()