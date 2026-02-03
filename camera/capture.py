"""
camera/capture.py — Thread-safe webcam capture
================================================
A background thread continuously grabs frames so the main processing
pipeline never blocks on I/O.  Other modules call `get_latest_frame()`
to retrieve the most recent BGR image without waiting.

Design notes
------------
* The capture thread runs as a daemon so it dies automatically when the
  main process exits — no explicit cleanup is strictly required, but
  `release()` should still be called for good practice.
* `_frame_ready` is a threading.Event that is set every time a new frame
  arrives.  Consumers can optionally wait on it with a timeout.
"""

import threading
import cv2
import numpy as np
from utils.logger import get_logger
from config import CAMERA_INDEX, CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS

logger = get_logger("camera.capture")


class CameraCapture:
    """Manages a single webcam and exposes its frames in a thread-safe way."""

    def __init__(self, device_index: int = CAMERA_INDEX):
        self._device_index = device_index
        self._cap: cv2.VideoCapture | None = None
        self._latest_frame: np.ndarray | None = None
        self._lock = threading.Lock()
        self._frame_ready = threading.Event()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self.is_open = False

    # ── Public API ───────────────────────────────────────────────────────────

    def open(self) -> bool:
        """
        Open the camera and start the background capture thread.

        Returns
        -------
        bool
            True if the camera was opened successfully.
        """
        if self.is_open:
            logger.warning("Camera already open — ignoring duplicate open().")
            return True

        self._cap = cv2.VideoCapture(self._device_index)
        # Set desired resolution & FPS (backend may ignore these)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
        self._cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)

        if not self._cap.isOpened():
            logger.error(
                "Failed to open camera at index %d. "
                "Check that a webcam is connected and not in use.",
                self._device_index,
            )
            return False

        # Log actual backend properties (may differ from what we requested)
        actual_w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = self._cap.get(cv2.CAP_PROP_FPS)
        logger.info("Camera opened — %dx%d @ %.1f FPS", actual_w, actual_h, actual_fps)

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        self.is_open = True
        return True

    def release(self) -> None:
        """Stop the capture thread and release the hardware device."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        if self._cap:
            self._cap.release()
            self._cap = None
        self.is_open = False
        logger.info("Camera released.")

    def get_latest_frame(self) -> np.ndarray | None:
        """
        Return the most-recently captured frame (BGR, uint8) or None if
        no frame is available yet.

        This is *non-blocking* — it simply returns whatever the background
        thread last wrote.
        """
        with self._lock:
            return self._latest_frame.copy() if self._latest_frame is not None else None

    def wait_for_frame(self, timeout: float = 1.0) -> np.ndarray | None:
        """
        Block until a new frame arrives or `timeout` seconds elapse.
        Useful for the very first frame after `open()`.
        """
        self._frame_ready.wait(timeout=timeout)
        self._frame_ready.clear()
        return self.get_latest_frame()

    # ── Private ──────────────────────────────────────────────────────────────

    def _capture_loop(self) -> None:
        """Continuously grab frames until the stop event is set."""
        while not self._stop_event.is_set():
            ret, frame = self._cap.read()  # type: ignore[union-attr]
            if not ret:
                logger.warning("Frame grab returned False — camera may have been disconnected.")
                break
            with self._lock:
                self._latest_frame = frame
            self._frame_ready.set()
        logger.debug("Capture loop exited.")
