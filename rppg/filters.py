"""
rppg/filters.py — Butterworth bandpass filter
===============================================
Isolates the cardiac-frequency band (0.7–4.0 Hz by default) from the
raw rPPG colour-channel time-series.

Why Butterworth?
----------------
* Maximally flat magnitude response in the passband — no ripple.
* Simple design via scipy.signal, which is well-tested and widely used
  in biomedical signal-processing literature.

Why bandpass at 0.7–4.0 Hz?
----------------------------
* 0.7 Hz  →  42 BPM  — lower bound covers bradycardia / resting HR.
* 4.0 Hz  → 240 BPM  — upper bound covers extreme tachycardia while
  still rejecting most motion / lighting artefacts which tend to be
  either very low frequency (< 0.5 Hz) or very high frequency (> 5 Hz).
"""

import numpy as np
from scipy.signal import butter, filtfilt
from config import BP_LOW_HZ, BP_HIGH_HZ, FILTER_ORDER


def design_bandpass(fs: float) -> tuple[np.ndarray, np.ndarray]:
    """
    Return the (b, a) coefficients for a Butterworth bandpass filter
    tuned to the cardiac-frequency band at the given sampling rate.

    Parameters
    ----------
    fs : float
        Sampling frequency in Hz (typically the camera FPS).

    Returns
    -------
    b, a : ndarray
        Numerator and denominator polynomial coefficients.
    """
    # Nyquist frequency
    nyq = fs / 2.0

    # Normalise cutoff frequencies to [0, 1] relative to Nyquist
    low = BP_LOW_HZ / nyq
    high = BP_HIGH_HZ / nyq

    # Safety: if the camera FPS is too low the high cutoff would exceed
    # Nyquist.  Clamp it and warn.
    if high >= 1.0:
        high = 0.95   # Leave a small margin below Nyquist
        import warnings
        warnings.warn(
            f"Camera FPS ({fs}) is too low for the requested upper cutoff "
            f"({BP_HIGH_HZ} Hz).  Clamping to {high * nyq:.2f} Hz.",
            stacklevel=2,
        )

    b, a = butter(FILTER_ORDER, [low, high], btype="band")
    return b, a


def bandpass_filter(signal: np.ndarray, fs: float) -> np.ndarray:
    """
    Apply a zero-phase Butterworth bandpass filter to a 1-D signal.

    Zero-phase (filtfilt) eliminates the group-delay introduced by
    causal filtering — critical for accurate peak detection in HRV
    analysis.

    Parameters
    ----------
    signal : ndarray, shape (N,)
        Raw rPPG time-series (one channel).
    fs     : float
        Sampling frequency in Hz.

    Returns
    -------
    filtered : ndarray, shape (N,)
        Bandpass-filtered signal.
    """
    # filtfilt needs at least 3× the filter order samples
    min_samples = 3 * FILTER_ORDER + 1
    if len(signal) < min_samples:
        raise ValueError(
            f"Signal too short for filtfilt: need >= {min_samples} samples, got {len(signal)}."
        )

    b, a = design_bandpass(fs)
    return filtfilt(b, a, signal)
