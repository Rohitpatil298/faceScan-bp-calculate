"""
rppg/pipeline.py — End-to-end rPPG → Heart Rate pipeline
=========================================================
Orchestrates the full signal-processing chain:

    ROI crops  →  mean RGB  →  rPPG algorithm  →  bandpass filter
               →  peak detection  →  Heart Rate (BPM)

This module accumulates per-frame RGB samples into a growing buffer,
and once enough data is collected (controlled by `SCAN_DURATION_SECONDS`)
it runs the algorithm and returns a clean pulse waveform ready for
downstream HRV and HR analysis.
"""

import numpy as np
from face.detector import FaceROIs
from rppg.algorithms import extract_mean_rgb, pos_algorithm, chrom_algorithm
from rppg.filters import bandpass_filter
from config import CAMERA_FPS, WARMUP_FRAMES
from utils.logger import get_logger

logger = get_logger("rppg.pipeline")

# Supported algorithm names → callable
_ALGORITHMS = {
    "pos":   pos_algorithm,
    "chrom": chrom_algorithm,
}


class RPPGPipeline:
    """
    Stateful pipeline that collects per-frame colour samples and, when
    triggered, extracts a pulse signal.

    Parameters
    ----------
    fps       : float   Camera sampling rate (frames per second).
    algorithm : str     One of 'pos' or 'chrom'.
    """

    def __init__(self, fps: float = CAMERA_FPS, algorithm: str = "pos"):
        if algorithm not in _ALGORITHMS:
            raise ValueError(
                f"Unknown algorithm '{algorithm}'. Choose from {list(_ALGORITHMS)}."
            )
        self._fps = fps
        self._algo_fn = _ALGORITHMS[algorithm]
        self._algo_name = algorithm

        # Ring buffer: list of (R, G, B) tuples, one per frame
        self._rgb_buffer: list[tuple[float, float, float]] = []
        self._frame_count = 0   # Total frames seen (including warmup)
        logger.info("RPPGPipeline created — algo=%s, fps=%.1f", algorithm, fps)

    # ── Public API ───────────────────────────────────────────────────────────

    def add_frame(self, rois: FaceROIs) -> None:
        """
        Feed one frame's ROIs into the buffer.

        We average the mean-RGB values from all available ROIs (forehead,
        left cheek, right cheek) to get a more robust single-frame sample.
        If no ROI is available (face not detected), the frame is skipped.
        """
        self._frame_count += 1

        # During the warmup period we still accumulate data — the caller
        # should gate on `is_ready()` before calling `extract_pulse()`.
        samples: list[tuple[float, float, float]] = []
        for roi in (rois.forehead, rois.cheek_left, rois.cheek_right):
            if roi is not None and roi.size > 0:
                samples.append(extract_mean_rgb(roi))

        if not samples:
            # No valid ROI this frame — append NaN placeholder so time
            # alignment stays consistent, then interpolate later.
            self._rgb_buffer.append((float("nan"), float("nan"), float("nan")))
            return

        # Average across available ROIs
        r = np.mean([s[0] for s in samples])
        g = np.mean([s[1] for s in samples])
        b = np.mean([s[2] for s in samples])
        self._rgb_buffer.append((float(r), float(g), float(b)))

    @property
    def buffer_length(self) -> int:
        """Number of RGB samples collected so far (post-warmup)."""
        return max(0, len(self._rgb_buffer) - WARMUP_FRAMES)

    def is_ready(self, min_samples: int = 60) -> bool:
        """True once we have enough post-warmup samples to process."""
        return self.buffer_length >= min_samples

    def extract_pulse(self) -> np.ndarray:
        """
        Run the full rPPG + filter pipeline on the current buffer.

        Returns
        -------
        pulse : ndarray, shape (N,)
            Bandpass-filtered pulse waveform.  N ≤ buffer_length
            (NaN rows are dropped before processing).

        Raises
        ------
        ValueError
            If insufficient valid (non-NaN) samples exist.
        """
        # Discard warmup frames
        raw = np.array(self._rgb_buffer[WARMUP_FRAMES:], dtype=np.float64)

        # Drop rows where any channel is NaN (face was missing)
        valid_mask = ~np.isnan(raw).any(axis=1)
        raw_valid = raw[valid_mask]

        if raw_valid.shape[0] < 15:
            raise ValueError(
                f"Only {raw_valid.shape[0]} valid frames after warmup — "
                "need at least 15 for processing.  Keep your face visible."
            )

        logger.debug(
            "Processing %d valid frames (%.1f s of data).",
            raw_valid.shape[0],
            raw_valid.shape[0] / self._fps,
        )

        # ── rPPG algorithm ────────────────────────────────────────────────
        raw_pulse = self._algo_fn(raw_valid)

        # ── Bandpass filter ───────────────────────────────────────────────
        pulse = bandpass_filter(raw_pulse, self._fps)

        return pulse

    def reset(self) -> None:
        """Clear the buffer — call between scans."""
        self._rgb_buffer.clear()
        self._frame_count = 0
        logger.info("Pipeline buffer reset.")
