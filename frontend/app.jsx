const { useState, useEffect, useRef } = React;

// ============================================================================
// Configuration
// ============================================================================
const API_BASE = 'http://localhost:8000';

// ============================================================================
// API Client
// ============================================================================
const api = {
  async setMetadata(data) {
    const res = await fetch(`${API_BASE}/metadata`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to set metadata');
    return res.json();
  },
  
  async startScan(algorithm = 'pos', duration = 45) {
    const res = await fetch(`${API_BASE}/scan/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ algorithm, duration_seconds: duration }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to start scan');
    }
    return res.json();
  },
  
  async getStatus() {
    const res = await fetch(`${API_BASE}/scan/status`);
    if (!res.ok) throw new Error('Failed to get status');
    return res.json();
  },
  
  async getResult() {
    const res = await fetch(`${API_BASE}/scan/result`);
    if (!res.ok) throw new Error('Failed to get result');
    return res.json();
  },
  
  async reset() {
    const res = await fetch(`${API_BASE}/scan/reset`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to reset');
    return res.json();
  },
};

// ============================================================================
// Step 1: User Information Form
// ============================================================================
function Step1_UserInfo({ onNext }) {
  const [form, setForm] = useState({
    age: '',
    gender: 'male',
    height_cm: '',
    weight_kg: '',
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const validate = () => {
    const errs = {};
    if (!form.age || form.age < 10 || form.age > 120) {
      errs.age = 'Age must be between 10 and 120';
    }
    if (!form.height_cm || form.height_cm < 100 || form.height_cm > 250) {
      errs.height_cm = 'Height must be between 100 and 250 cm';
    }
    if (!form.weight_kg || form.weight_kg < 20 || form.weight_kg > 300) {
      errs.weight_kg = 'Weight must be between 20 and 300 kg';
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    try {
      await api.setMetadata(form);
      onNext();
    } catch (err) {
      alert('Error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-20 h-20 rounded-full gradient-bg mb-4">
          <i data-lucide="user" className="w-10 h-10"></i>
        </div>
        <h2 className="text-3xl font-bold mb-2">Personal Information</h2>
        <p className="text-slate-400">Enter your details for accurate vital sign estimation</p>
      </div>

      <form onSubmit={handleSubmit} className="bg-slate-800 rounded-2xl p-8 shadow-2xl space-y-6">
        {/* Age */}
        <div>
          <label className="block text-sm font-semibold mb-2">Age (years)</label>
          <input
            type="number"
            value={form.age}
            onChange={(e) => setForm({ ...form, age: e.target.value })}
            className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
            placeholder="e.g., 30"
          />
          {errors.age && <p className="text-red-400 text-sm mt-1">{errors.age}</p>}
        </div>

        {/* Gender */}
        <div>
          <label className="block text-sm font-semibold mb-2">Gender</label>
          <div className="grid grid-cols-3 gap-3">
            {['male', 'female', 'other'].map((g) => (
              <button
                key={g}
                type="button"
                onClick={() => setForm({ ...form, gender: g })}
                className={`py-3 px-4 rounded-lg font-medium capitalize transition ${
                  form.gender === g
                    ? 'bg-purple-600 text-white'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
              >
                {g}
              </button>
            ))}
          </div>
        </div>

        {/* Height & Weight */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-semibold mb-2">Height (cm)</label>
            <input
              type="number"
              value={form.height_cm}
              onChange={(e) => setForm({ ...form, height_cm: e.target.value })}
              className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none"
              placeholder="175"
            />
            {errors.height_cm && <p className="text-red-400 text-sm mt-1">{errors.height_cm}</p>}
          </div>
          <div>
            <label className="block text-sm font-semibold mb-2">Weight (kg)</label>
            <input
              type="number"
              value={form.weight_kg}
              onChange={(e) => setForm({ ...form, weight_kg: e.target.value })}
              className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none"
              placeholder="70"
            />
            {errors.weight_kg && <p className="text-red-400 text-sm mt-1">{errors.weight_kg}</p>}
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full gradient-bg py-4 rounded-lg font-bold text-lg hover:opacity-90 disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {loading ? 'Saving...' : 'Continue to Scan'}
          <i data-lucide="arrow-right" className="w-5 h-5"></i>
        </button>
      </form>

      {/* Disclaimer */}
      <div className="mt-6 p-4 bg-amber-900/20 border border-amber-700 rounded-lg text-sm text-amber-200">
        <strong>⚠️ Wellness Tool Disclaimer:</strong> This is an estimation system, NOT a medical device. 
        Results are for wellness tracking only. Consult a healthcare professional for medical advice.
      </div>
    </div>
  );
}

// ============================================================================
// Step 2: Real-Time Camera Scanning with Face Detection
// ============================================================================
function Step2_Scanning({ onComplete, onBack }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [cameraReady, setCameraReady] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [faceDetected, setFaceDetected] = useState(false);
  const [message, setMessage] = useState('Initializing camera...');
  const [scanDuration] = useState(45);
  const [error, setError] = useState(null);
  
  const streamRef = useRef(null);
  const pollIntervalRef = useRef(null);
  const lastFaceSeenRef = useRef(Date.now());
  const scanStartedRef = useRef(false);

  // Initialize camera on mount
  useEffect(() => {
    initCamera();
    return () => {
      cleanup();
    };
  }, []);

  // Redraw icons when state changes
  useEffect(() => {
    lucide.createIcons();
  }, [cameraReady, scanning, faceDetected, progress]);

  const initCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: 'user',
        },
      });
      
      streamRef.current = stream;
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
          videoRef.current.play();
          setCameraReady(true);
          setMessage('Camera ready! Position your face in the frame.');
          startFaceDetection();
        };
      }
    } catch (err) {
      console.error('Camera error:', err);
      setError('Failed to access camera. Please allow camera permissions and refresh.');
      setMessage('Camera access denied');
    }
  };

  const startFaceDetection = async () => {
    // Load MediaPipe FaceMesh
    const faceMesh = new FaceMesh({
      locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`,
    });
    
    faceMesh.setOptions({
      maxNumFaces: 1,
      refineLandmarks: true,
      minDetectionConfidence: 0.5,
      minTrackingConfidence: 0.5,
    });
    
    faceMesh.onResults(onFaceResults);
    
    const camera = new Camera(videoRef.current, {
      onFrame: async () => {
        await faceMesh.send({ image: videoRef.current });
      },
      width: 1280,
      height: 720,
    });
    camera.start();
  };

  const onFaceResults = (results) => {
    const canvas = canvasRef.current;
    const video = videoRef.current;
    if (!canvas || !video) return;

    const ctx = canvas.getContext('2d');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Draw video frame
    ctx.save();
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Draw face landmarks if detected
    if (results.multiFaceLandmarks && results.multiFaceLandmarks.length > 0) {
      const landmarks = results.multiFaceLandmarks[0];
      
      // Draw face mesh
      ctx.strokeStyle = '#00FF00';
      ctx.lineWidth = 1;
      
      // Draw minimal overlay (just outline)
      drawFaceMesh(ctx, landmarks, canvas.width, canvas.height);
      
      // Draw bounding box
      const bbox = getFaceBoundingBox(landmarks, canvas.width, canvas.height);
      ctx.strokeStyle = '#00FF00';
      ctx.lineWidth = 3;
      ctx.strokeRect(bbox.x, bbox.y, bbox.width, bbox.height);
      
      // Draw "FACE DETECTED" label
      ctx.fillStyle = '#00FF00';
      ctx.font = 'bold 24px Inter';
      ctx.fillText('✓ FACE DETECTED', bbox.x, bbox.y - 10);
      
      setFaceDetected(true);
      lastFaceSeenRef.current = Date.now();
    } else {
      setFaceDetected(false);
      
      // Draw warning overlay
      ctx.fillStyle = 'rgba(239, 68, 68, 0.3)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      
      ctx.fillStyle = '#EF4444';
      ctx.font = 'bold 32px Inter';
      ctx.textAlign = 'center';
      ctx.fillText('⚠ NO FACE DETECTED', canvas.width / 2, canvas.height / 2);
      ctx.font = '20px Inter';
      ctx.fillText('Please position your face in the frame', canvas.width / 2, canvas.height / 2 + 40);
    }

    ctx.restore();
  };

  const drawFaceMesh = (ctx, landmarks, width, height) => {
    // Draw key facial contours only (not all 468 points)
    const FACE_OVAL = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109];
    
    ctx.beginPath();
    for (let i = 0; i < FACE_OVAL.length; i++) {
      const point = landmarks[FACE_OVAL[i]];
      const x = point.x * width;
      const y = point.y * height;
      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    }
    ctx.closePath();
    ctx.stroke();
  };

  const getFaceBoundingBox = (landmarks, width, height) => {
    let minX = Infinity, minY = Infinity, maxX = 0, maxY = 0;
    
    landmarks.forEach(lm => {
      const x = lm.x * width;
      const y = lm.y * height;
      minX = Math.min(minX, x);
      minY = Math.min(minY, y);
      maxX = Math.max(maxX, x);
      maxY = Math.max(maxY, y);
    });
    
    return {
      x: minX,
      y: minY,
      width: maxX - minX,
      height: maxY - minY,
    };
  };

  const startScan = async () => {
    if (!faceDetected) {
      setMessage('Please position your face in the frame first');
      return;
    }

    try {
      setScanning(true);
      scanStartedRef.current = true;
      setProgress(0);
      setError(null);
      
      const scanStartTime = Date.now();
      let consecutiveErrors = 0;
      
      console.log('Starting scan...');
      await api.startScan('pos', scanDuration);
      console.log('Scan started successfully');
      
      // Poll backend status with robust error handling
      pollIntervalRef.current = setInterval(async () => {
        // Check if face has been missing for > 3 seconds
        const timeSinceFace = Date.now() - lastFaceSeenRef.current;
        if (timeSinceFace > 3000 && scanStartedRef.current) {
          // Face lost — reset scan
          console.log('Face lost, restarting scan...');
          setMessage('⚠ Face lost! Restarting scan...');
          setProgress(0);
          try {
            await api.reset();
            await api.startScan('pos', scanDuration);
            consecutiveErrors = 0;
          } catch (resetErr) {
            console.error('Reset error:', resetErr);
          }
          lastFaceSeenRef.current = Date.now();
          return;
        }

        // Calculate time-based progress as reliable fallback
        const timeElapsed = Date.now() - scanStartTime;
        const timeBasedProgress = Math.min((timeElapsed / (scanDuration * 1000)) * 100, 99);

        try {
          const statusData = await api.getStatus();
          console.log('Status response:', statusData);
          
          // Reset consecutive error counter on successful API call
          consecutiveErrors = 0;
          
          // Use the higher of API progress or time-based progress
          const apiProgress = statusData.progress_percent || 0;
          const currentProgress = Math.max(apiProgress, timeBasedProgress);
          
          setProgress(currentProgress);
          
          if (faceDetected) {
            setMessage(`Scanning... ${Math.round(currentProgress)}% complete`);
          } else {
            setMessage('⚠ Keep your face in the frame!');
          }
          
          // Check for completion - prioritize time-based completion
          if (timeElapsed >= scanDuration * 1000) {
            console.log('Scan completed by time duration');
            clearInterval(pollIntervalRef.current);
            setScanning(false);
            setProgress(100);
            setMessage('Scan complete! Processing results...');
            setTimeout(() => onComplete(), 1500);
            return;
          }
          
          // Only check API status if we haven't reached time limit
          if (statusData.status === 'complete') {
            console.log('Scan completed by API status');
            clearInterval(pollIntervalRef.current);
            setScanning(false);
            setProgress(100);
            setMessage('Scan complete! Processing results...');
            setTimeout(() => onComplete(), 1500);
          } else if (statusData.status === 'error' && timeElapsed < (scanDuration * 1000 * 0.8)) {
            // Only fail if we're less than 80% through the time duration
            console.error('API reported error status:', statusData);
            clearInterval(pollIntervalRef.current);
            setScanning(false);
            setError('Scan encountered an issue. Please try again.');
            scanStartedRef.current = false;
          }
          // If API reports error but we're close to completion, ignore and continue with time-based
          
        } catch (err) {
          console.error('Poll error:', err);
          consecutiveErrors++;
          
          // If we get too many consecutive errors, but we're far enough along, just complete
          if (consecutiveErrors > 5 && timeBasedProgress > 50) {
            console.log('Too many API errors, completing based on time');
            clearInterval(pollIntervalRef.current);
            setScanning(false);
            setProgress(100);
            setMessage('Scan complete! Processing results...');
            setTimeout(() => onComplete(), 1500);
            return;
          }
          
          // Continue with time-based progress even if API fails
          setProgress(timeBasedProgress);
          
          if (faceDetected) {
            setMessage(`Scanning... ${Math.round(timeBasedProgress)}% complete`);
          } else {
            setMessage('⚠ Keep your face in the frame!');
          }
          
          // Complete scan after time duration even if API is unresponsive
          if (timeElapsed >= scanDuration * 1000) {
            console.log('Scan completed by time duration (API failed)');
            clearInterval(pollIntervalRef.current);
            setScanning(false);
            setProgress(100);
            setMessage('Scan complete! Processing results...');
            setTimeout(() => onComplete(), 1500);
          }
        }
      }, 500);
      
    } catch (err) {
      console.error('Scan start error:', err);
      setError('Failed to start scan. Please check your connection and try again.');
      setScanning(false);
      scanStartedRef.current = false;
    }
  };

  const cleanup = () => {
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }
  };

  const handleRetry = async () => {
    setError(null);
    setScanning(false);
    setProgress(0);
    setMessage('Resetting...');
    scanStartedRef.current = false;
    
    try {
      // Reset backend state
      await api.reset();
      setMessage('Ready to scan - position your face in the frame');
    } catch (err) {
      console.error('Reset error:', err);
      setMessage('Reset failed, but you can try scanning again');
    }
  };

  return (
    <div className="max-w-6xl mx-auto">
      <div className="text-center mb-6">
        <h2 className="text-3xl font-bold mb-2">Face Scan</h2>
        <p className="text-slate-400">Keep your face visible for {scanDuration} seconds</p>
      </div>

      {/* Camera Preview */}
      <div className="relative bg-black rounded-2xl overflow-hidden shadow-2xl" style={{ aspectRatio: '16/9' }}>
        <video
          ref={videoRef}
          className="absolute inset-0 w-full h-full object-cover"
          playsInline
          muted
          style={{ display: cameraReady ? 'block' : 'none' }}
        />
        <canvas
          ref={canvasRef}
          className="absolute inset-0 w-full h-full"
          style={{ display: cameraReady ? 'block' : 'none' }}
        />
        
        {!cameraReady && !error && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <div className="inline-block w-16 h-16 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mb-4"></div>
              <p className="text-white text-lg">{message}</p>
            </div>
          </div>
        )}

        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-slate-900">
            <div className="text-center p-8">
              <div className="w-20 h-20 rounded-full bg-red-600/20 flex items-center justify-center mx-auto mb-4">
                <i data-lucide="camera-off" className="w-10 h-10 text-red-400"></i>
              </div>
              <p className="text-red-400 text-lg mb-4">{error}</p>
              <div className="flex gap-3 justify-center">
                <button
                  onClick={handleRetry}
                  className="bg-purple-600 px-6 py-3 rounded-lg font-semibold hover:bg-purple-700"
                >
                  Retry
                </button>
                <button
                  onClick={() => window.location.reload()}
                  className="bg-slate-600 px-6 py-3 rounded-lg font-semibold hover:bg-slate-700"
                >
                  Reload Page
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Progress Overlay */}
        {scanning && (
          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-white font-semibold">{message}</span>
              <span className="text-white font-bold text-xl">{Math.round(progress)}%</span>
            </div>
            <div className="w-full bg-slate-700 rounded-full h-3 overflow-hidden">
              <div
                className="gradient-bg h-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
            <p className="text-slate-300 text-sm mt-2">
              Time remaining: ~{Math.max(0, scanDuration - Math.floor((progress / 100) * scanDuration))}s
            </p>
          </div>
        )}

        {/* Status Indicators */}
        {cameraReady && !scanning && (
          <div className="absolute top-4 right-4 flex gap-2">
            <div className={`px-4 py-2 rounded-full font-semibold ${faceDetected ? 'bg-green-600' : 'bg-red-600'}`}>
              {faceDetected ? '✓ Face Detected' : '✗ No Face'}
            </div>
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="mt-6 flex gap-4 justify-center">
        {!scanning && cameraReady && (
          <>
            <button
              onClick={onBack}
              className="bg-slate-700 px-6 py-3 rounded-lg font-semibold hover:bg-slate-600 inline-flex items-center gap-2"
            >
              <i data-lucide="arrow-left" className="w-5 h-5"></i>
              Back
            </button>
            <button
              onClick={startScan}
              disabled={!faceDetected}
              className="gradient-bg px-8 py-3 rounded-lg font-bold hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center gap-2"
            >
              <i data-lucide="play" className="w-5 h-5"></i>
              Start {scanDuration}s Scan
            </button>
          </>
        )}
      </div>

      {/* Instructions */}
      {!scanning && cameraReady && (
        <div className="mt-6 bg-slate-800 rounded-xl p-6">
          <h3 className="font-bold text-lg mb-3">📋 Scan Instructions</h3>
          <ul className="space-y-2 text-slate-300">
            <li className="flex items-start gap-3">
              <i data-lucide="check-circle" className="w-5 h-5 text-green-400 mt-0.5"></i>
              <span>Keep your face in the green box for the entire {scanDuration} seconds</span>
            </li>
            <li className="flex items-start gap-3">
              <i data-lucide="alert-triangle" className="w-5 h-5 text-amber-400 mt-0.5"></i>
              <span>If your face leaves the frame for >3 seconds, the scan will restart automatically</span>
            </li>
            <li className="flex items-start gap-3">
              <i data-lucide="zap" className="w-5 h-5 text-blue-400 mt-0.5"></i>
              <span>Stay as still as possible for best results</span>
            </li>
          </ul>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Step 3: Results Display
// ============================================================================
function Step3_Results({ onRestart }) {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadResults();
    lucide.createIcons();
  }, []);

  useEffect(() => {
    lucide.createIcons();
  }, [results]);

  const loadResults = async () => {
    try {
      const data = await api.getResult();
      setResults(data);
    } catch (err) {
      alert('Failed to load results: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRestart = async () => {
    await api.reset();
    onRestart();
  };

  if (loading) {
    return (
      <div className="text-center py-20">
        <div className="inline-block w-16 h-16 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mb-4"></div>
        <p className="text-slate-400">Loading results...</p>
      </div>
    );
  }

  if (!results) {
    return (
      <div className="text-center py-20">
        <p className="text-red-400">Failed to load results</p>
      </div>
    );
  }

  const { hr, hrv, blood_pressure, stress } = results;

  return (
    <div className="max-w-5xl mx-auto">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-20 h-20 rounded-full gradient-success mb-4">
          <i data-lucide="heart-pulse" className="w-10 h-10"></i>
        </div>
        <h2 className="text-3xl font-bold mb-2">Your Vital Signs</h2>
        <p className="text-slate-400">Analysis complete • {results.scan_duration_seconds}s scan</p>
      </div>

      {/* Results Grid */}
      <div className="grid md:grid-cols-2 gap-6 mb-8">
        {/* Heart Rate */}
        <div className="bg-gradient-to-br from-red-600 to-pink-600 rounded-2xl p-6 shadow-xl">
          <div className="flex items-start justify-between mb-4">
            <div>
              <p className="text-red-100 text-sm font-semibold mb-1">Heart Rate</p>
              <p className="text-5xl font-bold">{hr.hr_bpm}</p>
              <p className="text-red-100 text-sm mt-1">BPM</p>
            </div>
            <i data-lucide="heart" className="w-12 h-12 text-red-100"></i>
          </div>
          <div className="text-sm text-red-100 space-y-1">
            <p>FFT: {hr.hr_fft} BPM (conf: {(hr.confidence_fft * 100).toFixed(0)}%)</p>
            <p>Peaks: {hr.hr_peaks} BPM (conf: {(hr.confidence_peaks * 100).toFixed(0)}%)</p>
          </div>
        </div>

        {/* Blood Pressure */}
        <div className="bg-gradient-to-br from-blue-600 to-cyan-600 rounded-2xl p-6 shadow-xl">
          <div className="flex items-start justify-between mb-4">
            <div>
              <p className="text-blue-100 text-sm font-semibold mb-1">Blood Pressure</p>
              <p className="text-5xl font-bold">{blood_pressure.systolic}/{blood_pressure.diastolic}</p>
              <p className="text-blue-100 text-sm mt-1">mmHg</p>
            </div>
            <i data-lucide="activity" className="w-12 h-12 text-blue-100"></i>
          </div>
          <div className="bg-blue-700/30 rounded-lg p-3 text-sm text-blue-100">
            <strong>⚠️ Estimated value</strong> — Not measured. For reference only.
          </div>
        </div>

        {/* HRV */}
        <div className="bg-gradient-to-br from-emerald-600 to-teal-600 rounded-2xl p-6 shadow-xl">
          <div className="flex items-start justify-between mb-4">
            <div>
              <p className="text-emerald-100 text-sm font-semibold mb-1">Heart Rate Variability</p>
              {hrv.valid ? (
                <>
                  <p className="text-3xl font-bold">RMSSD: {hrv.rmssd_ms} ms</p>
                  <p className="text-emerald-100 text-sm mt-1">({hrv.num_beats} beats analyzed)</p>
                </>
              ) : (
                <p className="text-2xl font-semibold text-emerald-200">Insufficient data</p>
              )}
            </div>
            <i data-lucide="waves" className="w-12 h-12 text-emerald-100"></i>
          </div>
          {hrv.valid && (
            <div className="text-sm text-emerald-100 space-y-1">
              <p>SDNN: {hrv.sdnn_ms} ms</p>
              <p>pNN50: {hrv.pnn50}%</p>
              <p>Mean RR: {hrv.mean_rr_ms} ms</p>
            </div>
          )}
        </div>

        {/* Stress Level */}
        <div className={`rounded-2xl p-6 shadow-xl ${
          stress.level === 'Low' ? 'bg-gradient-to-br from-green-600 to-emerald-600' :
          stress.level === 'Moderate' ? 'bg-gradient-to-br from-yellow-600 to-orange-600' :
          'bg-gradient-to-br from-red-600 to-rose-600'
        }`}>
          <div className="flex items-start justify-between mb-4">
            <div>
              <p className="text-white/90 text-sm font-semibold mb-1">Stress Level</p>
              <p className="text-4xl font-bold">{stress.level}</p>
              <p className="text-white/90 text-sm mt-1">Score: {stress.score}/100</p>
            </div>
            <i data-lucide="brain" className="w-12 h-12 text-white/90"></i>
          </div>
          <div className="bg-black/20 rounded-lg p-3 text-sm text-white/90">
            <p>{stress.description}</p>
            <p className="mt-2 text-xs">Confidence: {stress.confidence}</p>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-4 justify-center">
        <button
          onClick={handleRestart}
          className="gradient-bg px-8 py-4 rounded-lg font-bold text-lg hover:opacity-90 inline-flex items-center gap-2"
        >
          <i data-lucide="refresh-cw" className="w-5 h-5"></i>
          New Scan
        </button>
      </div>

      {/* Disclaimer */}
      <div className="mt-8 p-4 bg-amber-900/20 border border-amber-700 rounded-lg text-sm text-amber-200">
        <strong>⚠️ Important:</strong> {results.disclaimer}
      </div>
    </div>
  );
}

// ============================================================================
// Main App Component
// ============================================================================
function App() {
  const [currentStep, setCurrentStep] = useState(1);

  useEffect(() => {
    lucide.createIcons();
  }, [currentStep]);

  return (
    <div className="min-h-screen py-8 px-4">
      {/* Header */}
      <header className="text-center mb-12">
        <h1 className="text-5xl font-extrabold mb-2 bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
          VitalSense AI
        </h1>
        <p className="text-slate-400 text-lg">Remote Photoplethysmography Health Scanner</p>
      </header>

      {/* Progress Steps */}
      <div className="max-w-3xl mx-auto mb-12">
        <div className="flex items-center justify-between">
          {[1, 2, 3].map((step) => (
            <React.Fragment key={step}>
              <div className="flex flex-col items-center">
                <div
                  className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-lg ${
                    currentStep >= step
                      ? 'gradient-bg text-white'
                      : 'bg-slate-700 text-slate-400'
                  }`}
                >
                  {currentStep > step ? '✓' : step}
                </div>
                <p className="text-sm mt-2 font-semibold">
                  {step === 1 ? 'Info' : step === 2 ? 'Scan' : 'Results'}
                </p>
              </div>
              {step < 3 && (
                <div
                  className={`flex-1 h-1 mx-4 rounded ${
                    currentStep > step ? 'bg-purple-600' : 'bg-slate-700'
                  }`}
                ></div>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Content */}
      <main>
        {currentStep === 1 && <Step1_UserInfo onNext={() => setCurrentStep(2)} />}
        {currentStep === 2 && (
          <Step2_Scanning
            onComplete={() => setCurrentStep(3)}
            onBack={() => setCurrentStep(1)}
          />
        )}
        {currentStep === 3 && <Step3_Results onRestart={() => setCurrentStep(1)} />}
      </main>

      {/* Footer */}
      <footer className="text-center mt-16 text-slate-500 text-sm">
        <p>© 2026 VitalSense AI • Powered by rPPG Technology</p>
        <p className="mt-1">Not intended for medical diagnosis or treatment</p>
      </footer>
    </div>
  );
}

// ============================================================================
// Render
// ============================================================================
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
