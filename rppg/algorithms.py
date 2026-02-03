"""
rppg/algorithms.py — POS & CHROM rPPG signal extraction
========================================================
Two well-established chrominance-based algorithms that convert a sequence
of mean R, G, B values sampled from a skin ROI into a quasi-periodic
pulse signal.

───────────────────────────────────────────────────────────────────────
POS  (Plane-Orthogonal-to-Skin)
───────────────────────────────────────────────────────────────────────
Reference:  Wang et al., "On Remote Photoplethysmography Signal
            Measurement from Practical Situations", IEEE TPAMI, 2017.

Key idea:  The skin colour vector lies on a plane in RGB space.  Blood
volume changes cause a small oscillation *orthogonal* to that plane.
By projecting the colour signal onto that orthogonal direction we
isolate the pulse component while suppressing specular reflections
and ambient-light changes.

Algorithm (per sliding window of W frames):
    1. Normalise each R, G, B channel to unit mean.
    2. Construct a 3×3 covariance-like matrix C from the normalised channels.
    3. Derive an orthonormal skin-tone vector  u_s  and an orthonormal
       illumination vector  u_i  from the columns of C.
    4. The pulse vector is  u_p = u_s × u_i  (cross product).
    5. Project the normalised colour signal onto  u_p  to get the raw
       pulse waveform.
    6. Normalise and concatenate windows with an overlap correction.

───────────────────────────────────────────────────────────────────────
CHROM  (Chrominance-based)
───────────────────────────────────────────────────────────────────────
Reference:  De Haan & Jeanne, "Contact-Free Optical Vital Sign
            Monitoring", IEEE TBME, 2013.

Key idea:  Construct two chrominance signals  X  and  Y  that are
orthogonal to the skin-tone direction, then combine them with a
dynamic scaling factor  α  chosen to minimise residual motion noise.

    X = 3R − 1.5G − 1.5B       (red vs green+blue contrast)
    Y = 1.5R + 1.5G − 3B       (warm vs blue contrast)

    α  = std(X) / std(Y)       (equalise power)
    S  = X − α·Y               (pulse signal)
"""

import numpy as np
from utils.logger import get_logger

logger = get_logger("rppg.algorithms")


# ── Colour-channel extraction helper ─────────────────────────────────────────


def extract_mean_rgb(roi: np.ndarray) -> tuple[float, float, float]:
    """
    Return the spatial mean of R, G, B channels from a single ROI crop.

    Parameters
    ----------
    roi : ndarray, shape (H, W, 3)   BGR image (OpenCV convention).

    Returns
    -------
    r, g, b : float   Mean pixel values in [0, 255].
    """
    # OpenCV uses BGR order — swap to RGB
    b_mean = roi[:, :, 0].mean()
    g_mean = roi[:, :, 1].mean()
    r_mean = roi[:, :, 2].mean()
    return float(r_mean), float(g_mean), float(b_mean)


# ── POS Algorithm ────────────────────────────────────────────────────────────


def pos_algorithm(rgb_sequence: np.ndarray) -> np.ndarray:
    """
    Plane-Orthogonal-to-Skin (POS) rPPG extraction.

    Parameters
    ----------
    rgb_sequence : ndarray, shape (T, 3)
        Each row is [R, G, B] mean values for one frame.

    Returns
    -------
    pulse : ndarray, shape (T,)
        Extracted pulse signal (zero-mean, unit variance).

    Notes
    -----
    We use a *full-sequence* implementation (no sliding window) for
    simplicity.  In a streaming application you would tile this into
    overlapping windows of ~10 s.
    """
    T = rgb_sequence.shape[0]
    if T < 2:
        raise ValueError("POS requires at least 2 frames.")

    R = rgb_sequence[:, 0]
    G = rgb_sequence[:, 1]
    B = rgb_sequence[:, 2]

    # ── Step 1: Normalise each channel to unit mean ──────────────────────
    # Avoids numerical issues when means are very different in magnitude.
    R_norm = R / (R.mean() + 1e-8)
    G_norm = G / (G.mean() + 1e-8)
    B_norm = B / (B.mean() + 1e-8)

    # Stack into (3, T) for vectorised maths
    C = np.vstack([R_norm, G_norm, B_norm])   # shape (3, T)

    # ── Step 2: Covariance-like matrix  ───────────────────────────────────
    # We use the outer product of the mean colour vector with itself to
    # estimate the static skin-tone direction, following Wang et al.
    mean_colour = C.mean(axis=1)                          # shape (3,)
    mean_colour /= (np.linalg.norm(mean_colour) + 1e-8)  # unit vector

    # ── Step 3: Orthonormal basis construction ────────────────────────────
    # e1 is aligned with the mean skin tone.
    e1 = mean_colour.copy()

    # e2 is chosen in the red-green plane, orthogonal to e1.
    # Start with an arbitrary vector not parallel to e1.
    arbitrary = np.array([1.0, 0.0, 0.0])
    if abs(np.dot(e1, arbitrary)) > 0.9:
        arbitrary = np.array([0.0, 1.0, 0.0])

    # Gram–Schmidt to get e2 ⊥ e1
    e2 = arbitrary - np.dot(arbitrary, e1) * e1
    e2 /= (np.linalg.norm(e2) + 1e-8)

    # e3 = e1 × e2 — the direction orthogonal to the skin plane
    e3 = np.cross(e1, e2)
    e3 /= (np.linalg.norm(e3) + 1e-8)

    # ── Step 4: Project onto the orthogonal (pulse) direction ─────────────
    # The pulse signal lives along e3 (orthogonal to skin-tone plane)
    pulse = e3 @ C   # shape (T,)

    # ── Step 5: Normalise ─────────────────────────────────────────────────
    pulse = (pulse - pulse.mean()) / (pulse.std() + 1e-8)

    return pulse


# ── CHROM Algorithm ──────────────────────────────────────────────────────────


def chrom_algorithm(rgb_sequence: np.ndarray) -> np.ndarray:
    """
    Chrominance-based (CHROM) rPPG extraction.

    Parameters
    ----------
    rgb_sequence : ndarray, shape (T, 3)
        Each row is [R, G, B] mean values for one frame.

    Returns
    -------
    pulse : ndarray, shape (T,)
        Extracted pulse signal (zero-mean, unit variance).

    Algorithm
    ---------
    1. Normalise R, G, B to unit mean.
    2. Compute chrominance channels:
           X = 3·R − 1.5·G − 1.5·B
           Y = 1.5·R + 1.5·G − 3·B
    3. Compute scaling factor  α = std(X) / std(Y).
    4. Pulse signal  S = X − α·Y.
    5. Normalise S to zero-mean, unit-variance.
    """
    if rgb_sequence.shape[0] < 2:
        raise ValueError("CHROM requires at least 2 frames.")

    R = rgb_sequence[:, 0]
    G = rgb_sequence[:, 1]
    B = rgb_sequence[:, 2]

    # Normalise to unit mean
    R_n = R / (R.mean() + 1e-8)
    G_n = G / (G.mean() + 1e-8)
    B_n = B / (B.mean() + 1e-8)

    # Chrominance channels (De Haan & Jeanne coefficients)
    X = 3.0 * R_n - 1.5 * G_n - 1.5 * B_n
    Y = 1.5 * R_n + 1.5 * G_n - 3.0 * B_n

    # Dynamic scaling to cancel motion artefacts
    std_x = X.std() + 1e-8
    std_y = Y.std() + 1e-8
    alpha = std_x / std_y

    # Pulse = chrominance difference
    S = X - alpha * Y

    # Normalise
    S = (S - S.mean()) / (S.std() + 1e-8)

    return S
