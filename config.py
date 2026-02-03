"""
config.py — Centralised configuration & hyper-parameters
=========================================================
Every tunable constant in the project lives here so that the rest of the
codebase can import from a single source of truth.
"""

# ─── Camera ──────────────────────────────────────────────────────────────────
CAMERA_INDEX: int = 0          # Device index passed to cv2.VideoCapture
CAMERA_WIDTH: int = 640
CAMERA_HEIGHT: int = 480
CAMERA_FPS: int = 15           # Requested FPS; actual FPS may differ

# ─── Scan Timing ─────────────────────────────────────────────────────────────
SCAN_DURATION_SECONDS: int = 45   # How long the rPPG capture window runs
WARMUP_FRAMES: int = 60           # Frames to discard before signal processing
                                  # (lets the face settle and auto-exposure stabilise)

# ─── Face / ROI ──────────────────────────────────────────────────────────────
# Normalised bounding-box coordinates relative to the 468-landmark face mesh.
# Forehead is sampled from the upper-centre region; cheeks from left and right.
FOREHEAD_LANDMARKS = [246, 7, 376, 383]   # Indices that bracket the forehead ROI
CHEEK_LEFT_LANDMARKS = [36, 194, 227, 116]
CHEEK_RIGHT_LANDMARKS = [266, 430, 447, 352]

# ROI shrink factor — pull each edge inward by this fraction to avoid skin/hair borders
ROI_SHRINK = 0.15

# ─── rPPG Signal Processing ──────────────────────────────────────────────────
# Butterworth bandpass filter band (Hz).
# 0.7 Hz  →  42 BPM   (lower physiological limit)
# 4.0 Hz  → 240 BPM   (upper safety margin)
BP_LOW_HZ: float = 0.7
BP_HIGH_HZ: float = 4.0
FILTER_ORDER: int = 4          # Butterworth filter order

# Sliding window for heart-rate estimation (seconds)
HR_WINDOW_SECONDS: float = 10.0

# ─── HRV ─────────────────────────────────────────────────────────────────────
# Minimum number of detected peaks needed to compute HRV metrics
HRV_MIN_PEAKS: int = 5

# ─── Blood Pressure Estimation ───────────────────────────────────────────────
# The BP model is a RandomForest regression trained on *synthetic* data.
# See model/bp_model.py for full disclaimer.
BP_MODEL_PATH: str = "model/bp_model.pkl"   # Serialised sklearn pipeline (optional)
BP_USE_PRETRAINED: bool = False             # Set True if a .pkl file exists

# ─── Stress Estimation ───────────────────────────────────────────────────────
# Thresholds used to map HRV → stress category (heuristic, not clinical)
# Based on general literature ranges for RMSSD (ms):
#   High RMSSD  → relaxed   |   Low RMSSD → stressed
STRESS_RMSSD_HIGH: float = 45.0   # Above this → Low stress
STRESS_RMSSD_MED: float = 25.0    # Between med and high → Moderate stress
# Below STRESS_RMSSD_MED        → High stress

# ─── API ─────────────────────────────────────────────────────────────────────
API_TITLE = "rPPG Vital-Signs Estimation API"
API_VERSION = "0.1.0"
