#!/usr/bin/env python3
"""
test_camera.py — Camera & Face Detection Diagnostic
====================================================
Tests whether OpenCV can open your Iriun webcam and whether
MediaPipe Face Mesh can detect your face.

Run:  python test_camera.py
"""

import cv2
import sys

print("=" * 70)
print("  CAMERA & FACE DETECTION TEST")
print("=" * 70)

# ── Step 1: Try to open the camera ──────────────────────────────────────
print("\n[1/3] Opening camera at index 0...")
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("  ✗ FAILED — Could not open camera at index 0.")
    print("\nTroubleshooting:")
    print("  • Make sure Iriun Webcam is running on both PC and phone")
    print("  • Check Windows Camera privacy settings (Settings > Privacy > Camera)")
    print("  • Close any other apps using the camera (Teams, Zoom, etc.)")
    print("  • Try changing CAMERA_INDEX in config.py to 1 or 2")
    sys.exit(1)

# Get actual camera properties
actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
actual_fps = cap.get(cv2.CAP_PROP_FPS)

print(f"  ✓ Camera opened — {actual_w}×{actual_h} @ {actual_fps:.1f} FPS")

# ── Step 2: Grab a test frame ───────────────────────────────────────────
print("\n[2/3] Grabbing a test frame...")
ret, frame = cap.read()

if not ret or frame is None:
    print("  ✗ FAILED — Camera returned no frame.")
    print("\nTroubleshooting:")
    print("  • Restart Iriun Webcam app on both devices")
    print("  • Check that your phone camera has permissions")
    cap.release()
    sys.exit(1)

print(f"  ✓ Frame received — shape: {frame.shape}, dtype: {frame.dtype}")

# ── Step 3: Test MediaPipe Face Mesh ────────────────────────────────────
print("\n[3/3] Testing MediaPipe Face Mesh...")
try:
    import mediapipe as mp
except ImportError:
    print("  ✗ mediapipe not installed.")
    print("  Run:  pip install mediapipe")
    cap.release()
    sys.exit(1)

mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)

frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
results = mp_face_mesh.process(frame_rgb)

if results.multi_face_landmarks:
    print(f"  ✓ Face detected! ({len(results.multi_face_landmarks[0].landmark)} landmarks)")
else:
    print("  ✗ NO FACE DETECTED in the test frame.")
    print("\nTroubleshooting:")
    print("  • Make sure your face is clearly visible in the Iriun camera view")
    print("  • Check lighting — avoid backlighting or very dim rooms")
    print("  • Move closer to the camera (fill ~30% of the frame)")
    print("  • Remove glasses/hats that might obscure your forehead/cheeks")

mp_face_mesh.close()

# ── Step 4: Live preview (optional) ─────────────────────────────────────
print("\n" + "=" * 70)
print("  Opening live preview window...")
print("  Press 'q' to quit, 's' to save a test frame")
print("=" * 70)

mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)

frame_count = 0
face_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    frame_count += 1
    
    # Run face detection
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = mp_face_mesh.process(frame_rgb)
    
    # Draw landmarks if face detected
    if results.multi_face_landmarks:
        face_count += 1
        for face_landmarks in results.multi_face_landmarks:
            h, w, _ = frame.shape
            # Draw a bounding box
            xs = [int(lm.x * w) for lm in face_landmarks.landmark]
            ys = [int(lm.y * h) for lm in face_landmarks.landmark]
            x_min, x_max = min(xs), max(xs)
            y_min, y_max = min(ys), max(ys)
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
            cv2.putText(frame, "FACE DETECTED", (x_min, y_min - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    # Stats overlay
    detect_rate = (face_count / frame_count * 100) if frame_count > 0 else 0
    cv2.putText(frame, f"Frames: {frame_count}  |  Faces: {face_count}  ({detect_rate:.0f}%)",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    cv2.imshow("Camera Test — Press 'q' to quit, 's' to save", frame)
    
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('s'):
        cv2.imwrite("test_frame.jpg", frame)
        print(f"  Saved test_frame.jpg (face_detected={results.multi_face_landmarks is not None})")

cap.release()
cv2.destroyAllWindows()
mp_face_mesh.close()

print("\n" + "=" * 70)
print(f"  TEST COMPLETE")
print(f"  Face detection rate: {face_count}/{frame_count} frames ({detect_rate:.0f}%)")
print("=" * 70)

if detect_rate < 50:
    print("\n⚠️  LOW DETECTION RATE — Recommendations:")
    print("  • Improve lighting (diffuse, front-facing light)")
    print("  • Position your face to fill 30-50% of the frame")
    print("  • Ensure forehead and cheeks are clearly visible")
    print("  • If Iriun Webcam is laggy, try lowering the resolution in Iriun settings")
elif detect_rate >= 80:
    print("\n✓  GOOD — You should be able to run a scan successfully.")
    print("   Try POST /scan/start again and keep your face in frame for 30-45 seconds.")