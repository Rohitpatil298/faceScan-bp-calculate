"""
model/bp_model.py — Blood Pressure Estimation (ML)
====================================================

⚠️⚠️⚠️  CRITICAL DISCLAIMER ⚠️⚠️⚠️
This module provides an *ESTIMATED* blood pressure, NOT a measured one.
The model was trained on *synthetically generated* data that follows
plausible physiological correlations described in published literature.
It has NOT been validated on real clinical blood-pressure measurements.

USE THIS OUTPUT ONLY AS A ROUGH WELLNESS INDICATOR.
DO NOT make medical decisions based on these estimates.
Consult a qualified healthcare professional for actual blood-pressure
measurement and interpretation.
⚠️⚠️⚠️

────────────────────────────────────────────────────────────────────────
Design Rationale
────────────────────────────────────────────────────────────────────────
Several studies have demonstrated weak-to-moderate correlations between
resting heart rate, HRV, and blood pressure (e.g., Pinter et al. 2003;
Li et al. 2017).  BMI, age, and sex are also known confounders.  A
lightweight RandomForest regressor captures non-linear interactions
between these features without requiring a large labelled dataset.

Synthetic data generation
--------------------------
We simulate 5 000 "subjects" using the following heuristics (derived
from epidemiological population studies):

    Systolic  ≈ 100 + 0.3·age + 5·BMI_offset + 0.15·HR − 0.05·RMSSD + noise
    Diastolic ≈  65 + 0.2·age + 3·BMI_offset + 0.10·HR − 0.03·RMSSD + noise

where:
    * BMI_offset = BMI − 22  (centred on a normal reference)
    * noise      ~ N(0, σ²)  with σ = 8 mmHg (systolic) / 5 mmHg (diastolic)

These relationships are deliberately simplified.  The noise term
intentionally keeps the model from over-fitting to spurious patterns.

Feature vector (input)
-----------------------
    [HR, RMSSD, SDNN, pNN50, age, gender_male, BMI]

────────────────────────────────────────────────────────────────────────
"""

import os
import pickle
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from utils.logger import get_logger
from config import BP_MODEL_PATH, BP_USE_PRETRAINED

logger = get_logger("model.bp")

# ── Feature names (must match the order used during training) ────────────────
FEATURE_NAMES = ["hr", "rmssd", "sdnn", "pnn50", "age", "gender_male", "bmi"]
N_SYNTHETIC = 5000
RANDOM_SEED = 42


def _generate_synthetic_data() -> tuple[np.ndarray, np.ndarray]:
    """
    Generate a synthetic training set of (features, [systolic, diastolic]).

    The correlations are *heuristic*, not derived from real patient data.
    See module docstring for the formulae used.

    Returns
    -------
    X : ndarray, shape (N_SYNTHETIC, 7)   Feature matrix.
    y : ndarray, shape (N_SYNTHETIC, 2)   [Systolic, Diastolic] targets.
    """
    rng = np.random.default_rng(RANDOM_SEED)

    # Simulate demographic & physiological features
    age = rng.integers(18, 80, size=N_SYNTHETIC).astype(float)
    gender_male = rng.integers(0, 2, size=N_SYNTHETIC).astype(float)   # 1 = male
    bmi = rng.normal(loc=26.0, scale=5.0, size=N_SYNTHETIC)
    bmi = np.clip(bmi, 15.0, 50.0)

    # Heart rate: resting HR varies with age and fitness
    hr = rng.normal(loc=72, scale=10, size=N_SYNTHETIC)
    hr += 0.05 * age                           # slight age dependence
    hr += 3.0 * gender_male                    # males slightly higher on average
    hr = np.clip(hr, 40, 130)

    # HRV features: RMSSD decreases with age; gender effect is small
    rmssd = rng.normal(loc=40, scale=15, size=N_SYNTHETIC)
    rmssd -= 0.3 * age                         # decreases with age
    rmssd -= 2.0 * gender_male
    rmssd = np.clip(rmssd, 5, 120)

    sdnn = rmssd * rng.uniform(0.6, 1.4, size=N_SYNTHETIC)   # correlated with RMSSD
    sdnn = np.clip(sdnn, 3, 100)

    pnn50 = rmssd * rng.uniform(0.3, 0.8, size=N_SYNTHETIC)  # proxy for RMSSD
    pnn50 = np.clip(pnn50, 0, 100)

    # ── Target generation (synthetic BP) ──────────────────────────────────
    bmi_offset = bmi - 22.0

    systolic = (
        100.0
        + 0.30 * age
        + 5.0 * bmi_offset
        + 0.15 * hr
        - 0.05 * rmssd
        + 4.0 * gender_male                    # males slightly higher
        + rng.normal(0, 8.0, size=N_SYNTHETIC) # realistic scatter
    )
    systolic = np.clip(systolic, 80, 200)

    diastolic = (
        65.0
        + 0.20 * age
        + 3.0 * bmi_offset
        + 0.10 * hr
        - 0.03 * rmssd
        + 2.0 * gender_male
        + rng.normal(0, 5.0, size=N_SYNTHETIC)
    )
    diastolic = np.clip(diastolic, 50, 130)

    # Enforce systolic > diastolic (physiological constraint)
    mask = systolic <= diastolic
    systolic[mask] = diastolic[mask] + rng.uniform(10, 25, size=mask.sum())

    X = np.column_stack([hr, rmssd, sdnn, pnn50, age, gender_male, bmi])
    y = np.column_stack([systolic, diastolic])
    return X, y


def _train_model() -> Pipeline:
    """
    Train a RandomForest regressor on synthetic data.

    We wrap it in a sklearn Pipeline with a StandardScaler so that
    feature magnitudes are equalised before tree splits (not strictly
    necessary for RF, but good practice and allows easy swapping to
    gradient-boosted models later).

    Returns
    -------
    pipeline : sklearn.pipeline.Pipeline
    """
    logger.info("Generating %d synthetic training samples…", N_SYNTHETIC)
    X, y = _generate_synthetic_data()

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("rf", RandomForestRegressor(
            n_estimators=100,
            max_depth=8,
            min_samples_leaf=10,
            random_state=RANDOM_SEED,
            n_jobs=-1,
        )),
    ])

    logger.info("Training RandomForest BP model…")
    pipeline.fit(X, y)
    logger.info("Training complete.")

    # Optionally persist to disk for faster subsequent loads
    try:
        os.makedirs(os.path.dirname(BP_MODEL_PATH) or ".", exist_ok=True)
        with open(BP_MODEL_PATH, "wb") as f:
            pickle.dump(pipeline, f)
        logger.info("Model saved to %s", BP_MODEL_PATH)
    except OSError as e:
        logger.warning("Could not save model to disk: %s", e)

    return pipeline


def load_or_train_model() -> Pipeline:
    """
    Load a persisted model if available, otherwise train from scratch.

    Returns
    -------
    pipeline : sklearn.pipeline.Pipeline
    """
    if BP_USE_PRETRAINED and os.path.exists(BP_MODEL_PATH):
        logger.info("Loading pre-trained BP model from %s …", BP_MODEL_PATH)
        with open(BP_MODEL_PATH, "rb") as f:
            return pickle.load(f)

    return _train_model()


class BPEstimator:
    """
    High-level wrapper that holds the trained model and exposes a simple
    `predict(...)` interface.

    ⚠️  The returned values are ESTIMATES, not clinical measurements.
    """

    def __init__(self):
        self._model = load_or_train_model()

    def predict(
        self,
        hr: float,
        rmssd: float,
        sdnn: float,
        pnn50: float,
        age: int,
        gender_male: int,   # 1 = male, 0 = female
        bmi: float,
    ) -> dict:
        """
        Estimate systolic and diastolic blood pressure.

        Parameters
        ----------
        hr      : float   Heart rate in BPM.
        rmssd   : float   RMSSD in ms.
        sdnn    : float   SDNN in ms.
        pnn50   : float   pNN50 percentage.
        age     : int     Age in years.
        gender_male : int 1 if male, 0 otherwise.
        bmi     : float   Body Mass Index (kg/m²).

        Returns
        -------
        dict
            {"systolic": float, "diastolic": float, "unit": "mmHg"}
        """
        X = np.array([[hr, rmssd, sdnn, pnn50, age, gender_male, bmi]])
        preds = self._model.predict(X)[0]   # shape (2,)

        systolic = float(np.clip(round(preds[0], 1), 70, 220))
        diastolic = float(np.clip(round(preds[1], 1), 40, 140))

        # Enforce systolic > diastolic
        if systolic <= diastolic:
            systolic = diastolic + 15.0

        logger.info("BP estimate: %s/%s mmHg", systolic, diastolic)

        return {
            "systolic": systolic,
            "diastolic": diastolic,
            "unit": "mmHg",
        }
