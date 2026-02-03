#!/usr/bin/env python3
"""
demo_cli.py — Standalone command-line demo
============================================
Runs the full rPPG pipeline WITHOUT the FastAPI server.
Useful for quick testing, demos, and debugging.

Usage:
    python demo_cli.py --age 35 --gender male --height 175 --weight 70 --duration 30

⚠️  DISCLAIMER: See config.py and model/bp_model.py for full disclaimers.
    This is a WELLNESS ESTIMATION tool — NOT a medical device.
"""

import argparse
import time
import sys
import cv2
import numpy as np

from camera.capture import CameraCapture
from face.detector import FaceDetector
from rppg.pipeline import RPPGPipeline
from features.hr import estimate_hr
from features.hrv import compute_hrv
from model.bp_model import BPEstimator
from model.stress import estimate_stress
from config import CAMERA_FPS
from utils.logger import get_logger

logger = get_logger("demo_cli")


def _compute_bmi(height_cm: float, weight_kg: float) -> float:
    return weight_kg / ((height_cm / 100.0) ** 2)


def pretty_print(label: str, value, unit: str = "") -> None:
    """Colourised terminal output."""
    print(f"  \033[1;36m{label:<28}\033[0m \033[1;33m{value}\033[0m {unit}")


def main():
    parser = argparse.ArgumentParser(description="rPPG Vital Signs CLI Demo")
    parser.add_argument("--age", type=int, default=35, help="Age (years)")
    parser.add_argument("--gender", type=str, default="male", choices=["male", "female", "other"])
    parser.add_argument("--height", type=float, default=175.0, help="Height (cm)")
    parser.add_argument("--weight", type=float, default=70.0, help="Weight (kg)")
    parser.add_argument("--duration", type=int, default=30, help="Scan duration (seconds)")
    parser.add_argument("--algorithm", type=str, default="pos", choices=["pos", "chrom"])
    parser.add_argument("--show-feed", action="store_true", help="Show live camera feed with face overlay")
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("  rPPG VITAL SIGNS ESTIMATION — CLI DEMO")
    print("=" * 60)
    print("  ⚠️  This is a WELLNESS ESTIMATION tool — NOT medical grade.")
    print("=" * 60 + "\n")

    # ── Initialise components ────────────────────────────────────────────
    logger.info("Initialising camera…")
    camera = CameraCapture()
    if not camera.open():
        print("ERROR: Could not open camera. Exiting.")
        sys.exit(1)

    face_detector = FaceDetector()
    pipeline = RPPGPipeline(fps=CAMERA_FPS, algorithm=args.algorithm)

    print(f"  Algorithm    : {args.algorithm.upper()}")
    print(f"  Scan duration: {args.duration} s")
    print(f"  Demographics : age={args.age}, gender={args.gender}, "
          f"height={args.height}cm, weight={args.weight}kg\n")
    print("  Please look directly at the camera and stay still…\n")

    # ── Main capture loop ────────────────────────────────────────────────
    start = time.time()
    frame_count = 0
    face_detected_count = 0

    while True:
        elapsed = time.time() - start
        if elapsed >= args.duration:
            break

        frame = camera.get_latest_frame()
        if frame is None:
            time.sleep(0.02)
            continue

        frame_count += 1
        rois = face_detector.detect(frame)

        if rois.face_detected:
            face_detected_count += 1

        pipeline.add_frame(rois)

        # ── Optional live feed with overlay ──────────────────────────
        if args.show_feed:
            display = frame.copy()
            # Draw ROI rectangles on the display frame
            if rois.face_detected and rois.landmarks:
                # Simple bounding box around all landmarks
                xs = [l[0] for l in rois.landmarks]
                ys = [l[1] for l in rois.landmarks]
                cv2.rectangle(display,
                              (min(xs), min(ys)),
                              (max(xs), max(ys)),
                              (0, 255, 0), 2)

            # Progress bar
            pct = int((elapsed / args.duration) * 100)
            bar_w = 200
            filled = int(bar_w * pct / 100)
            cv2.rectangle(display, (20, 20), (20 + bar_w, 40), (255, 255, 255), 1)
            cv2.rectangle(display, (20, 20), (20 + filled, 40), (0, 200, 0), -1)
            cv2.putText(display, f"{pct}%", (230, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            cv2.imshow("rPPG Demo", display)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("\n  Scan cancelled by user.")
                camera.release()
                face_detector.close()
                if args.show_feed:
                    cv2.destroyAllWindows()
                sys.exit(0)

        # Small sleep to avoid 100 % CPU on the main thread
        time.sleep(0.01)

    # ── Cleanup camera ──────────────────────────────────────────────────
    camera.release()
    face_detector.close()
    if args.show_feed:
        cv2.destroyAllWindows()

    print(f"\n  Captured {frame_count} frames, face detected in {face_detected_count} "
          f"({100*face_detected_count/max(frame_count,1):.0f}%).\n")

    # ── Signal processing ────────────────────────────────────────────────
    try:
        pulse = pipeline.extract_pulse()
    except ValueError as e:
        print(f"  ERROR: {e}")
        sys.exit(1)

    hr_result = estimate_hr(pulse, CAMERA_FPS)
    hrv_result = compute_hrv(hr_result["rr_intervals"])

    # ── BP & Stress ──────────────────────────────────────────────────────
    bp_estimator = BPEstimator()
    bmi = _compute_bmi(args.height, args.weight)
    gender_male = 1 if args.gender == "male" else 0

    bp_result = bp_estimator.predict(
        hr=hr_result["hr_bpm"],
        rmssd=hrv_result["rmssd_ms"] or 30.0,
        sdnn=hrv_result["sdnn_ms"] or 20.0,
        pnn50=hrv_result["pnn50"] or 10.0,
        age=args.age,
        gender_male=gender_male,
        bmi=bmi,
    )

    stress_result = estimate_stress(
        hr_bpm=hr_result["hr_bpm"],
        rmssd_ms=hrv_result["rmssd_ms"],
        sdnn_ms=hrv_result["sdnn_ms"],
    )

    # ── Pretty-print results ─────────────────────────────────────────────
    print("=" * 60)
    print("  RESULTS")
    print("=" * 60)
    print("\n  ── Heart Rate ──")
    pretty_print("Heart Rate", hr_result["hr_bpm"], "BPM")
    pretty_print("  (FFautomatic)", hr_result["hr_fft"], "BPM")
    pretty_print("  (Peak detect)", hr_result["hr_peaks"], "BPM")
    pretty_print("  FFT confidence", hr_result["confidence_fft"])
    pretty_print("  Peak confidence", hr_result["confidence_peaks"])

    print("\n  ── Heart Rate Variability ──")
    if hrv_result["valid"]:
        pretty_print("SDNN", hrv_result["sdnn_ms"], "ms")
        pretty_print("RMSSD", hrv_result["rmssd_ms"], "ms")
        pretty_print("pNN50", hrv_result["pnn50"], "%")
        pretty_print("Mean RR", hrv_result["mean_rr_ms"], "ms")
        pretty_print("Beats detected", hrv_result["num_beats"])
    else:
        print("    ⚠️  Insufficient beats for HRV calculation.")

    print("\n  ── Blood Pressure (ESTIMATED) ──")
    pretty_print("Systolic", bp_result["systolic"], "mmHg")
    pretty_print("Diastolic", bp_result["diastolic"], "mmHg")

    print("\n  ── Stress Level (ESTIMATED) ──")
    pretty_print("Level", stress_result["level"])
    pretty_print("Score", stress_result["score"], "/ 100")
    pretty_print("Confidence", stress_result["confidence"])
    print(f"    {stress_result['description']}")

    print("\n" + "=" * 60)
    print("  ⚠️  DISCLAIMER: All values above are ESTIMATES.")
    print("      Do NOT use for medical diagnosis or treatment.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
