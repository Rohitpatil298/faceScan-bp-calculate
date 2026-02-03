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
// Step 2: Face Scanning
// ============================================================================
function Step2_Scanning({ onComplete, onBack }) {
  const [status, setStatus] = useState('idle'); // idle | scanning | complete | error
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState('');
  const [scanDuration] = useState(45);
  const pollInterval = useRef(null);

  useEffect(() => {
    lucide.createIcons();
  }, [status, progress]);

  const startScan = async () => {
    try {
      await api.startScan('pos', scanDuration);
      setStatus('scanning');
      setProgress(0);
      
      // Poll status every 500ms
      pollInterval.current = setInterval(async () => {
        try {
          const statusData = await api.getStatus();
          setProgress(statusData.progress_percent || 0);
          setMessage(statusData.message || '');
          
          if (statusData.status === 'complete') {
            clearInterval(pollInterval.current);
            setStatus('complete');
            setTimeout(() => onComplete(), 1500);
          } else if (statusData.status === 'error') {
            clearInterval(pollInterval.current);
            setStatus('error');
            setMessage('Scan failed. Please try again.');
          }
        } catch (err) {
          console.error('Poll error:', err);
        }
      }, 500);
    } catch (err) {
      setStatus('error');
      setMessage(err.message);
    }
  };

  useEffect(() => {
    return () => {
      if (pollInterval.current) clearInterval(pollInterval.current);
    };
  }, []);

  return (
    <div className="max-w-3xl mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold mb-2">Face Scan</h2>
        <p className="text-slate-400">Position your face in the camera and stay still</p>
      </div>

      {/* Camera Preview Area */}
      <div className="bg-slate-800 rounded-2xl p-8 shadow-2xl">
        {status === 'idle' && (
          <div className="text-center">
            <div className="mb-8">
              <div className="inline-flex items-center justify-center w-32 h-32 rounded-full bg-slate-700 mb-4">
                <i data-lucide="camera" className="w-16 h-16 text-purple-400"></i>
              </div>
              <h3 className="text-2xl font-bold mb-4">Ready to Scan</h3>
              
              {/* Instructions */}
              <div className="bg-slate-700 rounded-xl p-6 mb-6 text-left space-y-3">
                <p className="font-semibold text-lg mb-3">📋 Before you start:</p>
                <div className="space-y-2 text-slate-300">
                  <div className="flex items-start gap-3">
                    <i data-lucide="check-circle" className="w-5 h-5 text-green-400 mt-0.5"></i>
                    <span>Sit 40-80 cm from your camera</span>
                  </div>
                  <div className="flex items-start gap-3">
                    <i data-lucide="check-circle" className="w-5 h-5 text-green-400 mt-0.5"></i>
                    <span>Ensure good, even lighting (avoid backlighting)</span>
                  </div>
                  <div className="flex items-start gap-3">
                    <i data-lucide="check-circle" className="w-5 h-5 text-green-400 mt-0.5"></i>
                    <span>Keep your forehead and cheeks visible</span>
                  </div>
                  <div className="flex items-start gap-3">
                    <i data-lucide="check-circle" className="w-5 h-5 text-green-400 mt-0.5"></i>
                    <span>Stay as still as possible for {scanDuration} seconds</span>
                  </div>
                  <div className="flex items-start gap-3">
                    <i data-lucide="alert-circle" className="w-5 h-5 text-amber-400 mt-0.5"></i>
                    <span>If your face isn't detected, the scan will pause</span>
                  </div>
                </div>
              </div>
            </div>

            <button
              onClick={startScan}
              className="gradient-bg px-8 py-4 rounded-lg font-bold text-lg hover:opacity-90 inline-flex items-center gap-2"
            >
              <i data-lucide="play" className="w-6 h-6"></i>
              Start {scanDuration}s Scan
            </button>
          </div>
        )}

        {status === 'scanning' && (
          <div className="text-center">
            {/* Animated Face Circle */}
            <div className="relative inline-block mb-6">
              <div className="w-48 h-48 rounded-full border-8 border-purple-600 flex items-center justify-center pulse-ring">
                <i data-lucide="scan-face" className="w-24 h-24 text-purple-400"></i>
              </div>
              <div className="absolute -top-2 -right-2 w-12 h-12 bg-green-500 rounded-full flex items-center justify-center animate-pulse">
                <i data-lucide="activity" className="w-6 h-6"></i>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="mb-6">
              <div className="flex justify-between mb-2">
                <span className="text-sm font-semibold">Scanning...</span>
                <span className="text-sm font-semibold">{Math.round(progress)}%</span>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-4 overflow-hidden">
                <div
                  className="gradient-bg h-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
            </div>

            {/* Status Message */}
            <p className="text-slate-300 text-lg mb-4">{message}</p>

            {/* Time Remaining */}
            <p className="text-slate-400 text-sm">
              Time remaining: ~{Math.max(0, scanDuration - Math.floor((progress / 100) * scanDuration))}s
            </p>
          </div>
        )}

        {status === 'complete' && (
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-32 h-32 rounded-full gradient-success mb-6">
              <i data-lucide="check" className="w-16 h-16"></i>
            </div>
            <h3 className="text-2xl font-bold mb-2">Scan Complete!</h3>
            <p className="text-slate-400">Processing your results...</p>
          </div>
        )}

        {status === 'error' && (
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-32 h-32 rounded-full gradient-danger mb-6">
              <i data-lucide="x-circle" className="w-16 h-16"></i>
            </div>
            <h3 className="text-2xl font-bold mb-2">Scan Failed</h3>
            <p className="text-slate-400 mb-6">{message}</p>
            <div className="flex gap-4 justify-center">
              <button
                onClick={onBack}
                className="bg-slate-700 px-6 py-3 rounded-lg font-semibold hover:bg-slate-600"
              >
                Back
              </button>
              <button
                onClick={() => { setStatus('idle'); setProgress(0); }}
                className="gradient-bg px-6 py-3 rounded-lg font-semibold hover:opacity-90"
              >
                Try Again
              </button>
            </div>
          </div>
        )}
      </div>

      {status === 'idle' && (
        <div className="mt-6 text-center">
          <button
            onClick={onBack}
            className="text-slate-400 hover:text-white inline-flex items-center gap-2"
          >
            <i data-lucide="arrow-left" className="w-4 h-4"></i>
            Back to Information
          </button>
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
