# VitalSense AI — Frontend

**Professional, production-ready web UI for the rPPG Vital Signs Estimation System.**

Built with React 18, Tailwind CSS, and Lucide Icons — zero build step required.

---

## ✨ Features

### 🎯 3-Step User Journey
1. **User Information** — Age, gender, height, weight with real-time validation
2. **Face Scanning** — Live progress tracking with visual feedback (0–100%)
3. **Results Dashboard** — Beautiful cards showing HR, HRV, BP, and Stress

### 🎨 UI/UX Highlights
- **Responsive design** — Works on mobile, tablet, desktop
- **Real-time progress** — Updates every 500ms during scan
- **Animated feedback** — Pulsing scan ring, smooth transitions
- **Clear instructions** — Step-by-step guidance with icons
- **Error handling** — Graceful fallbacks if scan fails or face not detected
- **Industry-standard design** — Gradient cards, professional typography, accessibility-friendly

### 🔒 Safety & Validation
- **Form validation** — Age (10–120), height (100–250 cm), weight (20–300 kg)
- **API error handling** — Clear error messages if backend is down
- **Disclaimers** — Prominent warnings that this is NOT a medical device

---

## 🚀 Quick Start

### 1. Make sure your backend is running

```bash
cd ../   # Go back to rppg_vitals root
python main.py
```

Backend should be running on `http://localhost:8000`.

### 2. Serve the frontend

**Option A — Python (simplest)**

```bash
cd frontend
python -m http.server 3000
```

Then open: **http://localhost:3000**

**Option B — Node.js (if you have it)**

```bash
npx serve -s . -p 3000
```

**Option C — VS Code Live Server**

Right-click `index.html` → "Open with Live Server"

---

## 📁 File Structure

```
frontend/
├── index.html      # HTML shell with CDN links (React, Tailwind, Lucide)
├── app.jsx         # Main React app (3 steps + API client)
└── README.md       # This file
```

**Why no build step?**  
We're using CDN-hosted React (via UMD) and Babel Standalone for JSX transpilation. This is perfect for quick prototyping and demos. For production deployment with millions of users, you'd migrate to Vite/Next.js.

---

## 🎨 Customization

### Change Colors

Edit the gradient classes in `index.html` `<style>` block:

```css
.gradient-bg {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  /* ↑ Change these hex codes */
}
```

### Change Scan Duration

In `app.jsx`, find this line in `Step2_Scanning`:

```javascript
const [scanDuration] = useState(45);  // ← Change to 30, 60, etc.
```

### Change API URL

At the top of `app.jsx`:

```javascript
const API_BASE = 'http://localhost:8000';  // ← Change if backend is on a different port/domain
```

---

## 🌐 Deployment

### Deploy to Vercel / Netlify (Free)

1. Create a `netlify.toml` or `vercel.json`:

```toml
# netlify.toml
[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

2. Push to GitHub

3. Connect repo to Vercel/Netlify — it auto-deploys

4. **Important:** Update `API_BASE` in `app.jsx` to your deployed backend URL

### Deploy Backend to Cloud

**Option 1 — Render.com (free tier)**

1. Push your `rppg_vitals` repo to GitHub
2. Create a new Web Service on Render
3. Build command: `pip install -r requirements.txt`
4. Start command: `python main.py`
5. Copy the deployed URL (e.g., `https://your-app.onrender.com`)
6. Update `API_BASE` in frontend

**Option 2 — Railway / Fly.io / AWS / GCP**

Similar process — most have 1-click FastAPI deploy.

---

## 🔧 Troubleshooting

| Issue | Fix |
|-------|-----|
| **"This site can't be reached"** | Make sure you're serving the frontend (`python -m http.server 3000`) and visiting `localhost:3000`, not just opening `index.html` directly in the browser (React needs to be served via HTTP). |
| **"Failed to fetch" errors** | Backend isn't running. Start `python main.py` in the root directory. |
| **CORS errors** | The backend already has CORS enabled for `*`. If you still see errors, restart the backend. |
| **Icons not showing** | Lucide icons are loaded via CDN. Check your internet connection, or download Lucide locally. |
| **Scan stuck at 0%** | See the main README troubleshooting — likely a face detection issue. Run `test_camera.py`. |

---

## 📱 Mobile Support

The UI is fully responsive and works on phones. However:

- **Camera access** requires HTTPS in production (localhost works without HTTPS in dev)
- Face detection quality depends on phone camera resolution and lighting
- For best results, use a tablet or laptop

---

## 🎯 Roadmap / Future Enhancements

- [ ] Export results as PDF report
- [ ] Historical tracking (save scans to localStorage or backend database)
- [ ] Comparison charts (show trends over time)
- [ ] Multi-language support (i18n)
- [ ] Dark/light mode toggle
- [ ] Integration with health apps (Apple Health, Google Fit)

---

## 📄 License

Same as the main project — provided as-is for educational, research, and prototyping purposes.

**Remember:** This is a wellness estimation tool, NOT a medical device.
