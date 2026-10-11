# MailGuard AI - Deployment Guide

This guide details how to deploy MailGuard AI across two target architectures:
1. **Split Architecture (Recommended):** Vercel (static frontend) + Render (Flask ML backend API).
2. **Monolith Fallback:** Render-only single-origin deployment (Flask serves both API and static frontend).

---

## 1. Architecture Overview

```
                      +------------------------------------------+
                      |               USER BROWSER               |
                      |  - Vanilla ES6+ UI (Hash routing)        |
                      |  - Client-side IndexedDB history         |
                      |  - Client-side WASM OCR (Tesseract.js)   |
                      +--------------------+---------------------+
                                           |
                 Static Assets & HTML      |     API Requests & Inference
                 (CSS, JS, Fonts, WASM)    |     (/api/health, /api/analyze)
                                           v
                       +-------------------+--------------------+
                       |                                        |
                       v                                        v
        +------------------------------+       +---------------------------------+
        |            VERCEL            |       |             RENDER              |
        |  Static Frontend Host        |       |  Python 3.12 Backend API        |
        |  - outputDirectory: frontend |       |  - Gunicorn + Flask             |
        |  - Strict CSP Headers        |       |  - Calibrated Linear SVM        |
        |  - Zero Secrets / No Build   |       |  - Flask-Limiter Rate Limiting  |
        |  - Production Vercel URL     |       |  - CORS_ALLOWED_ORIGINS filter  |
        +------------------------------+       +---------------------------------+
```

### Privacy Guarantee
* **Email text & images are NEVER stored on the server.** Requests are processed purely in-memory.
* **Scan audit history is stored locally on the user's device** using browser IndexedDB.
* **Image OCR and QR code decoding run 100% in-browser** via Web Workers and WebAssembly.

---

## 2. Environment Variables & Configuration

### Backend (Render Web Service)

| Environment Variable | Recommended Value | Description |
|----------------------|-------------------|-------------|
| `PYTHON_VERSION` | `3.12.10` | Pinned Python runtime version. |
| `FLASK_DEBUG` | `0` | Disables debug mode in production. |
| `MODEL_PATH` | `models/spam_pipeline.joblib` | Path to trained scikit-learn pipeline artifact. |
| `METADATA_PATH` | `models/metadata.json` | Path to dataset and evaluation metadata. |
| `CORS_ALLOWED_ORIGINS` | `https://mailguard-ai.vercel.app` | Comma-separated list of exact allowed origins. **Wildcard `*` is strictly rejected.** |
| `RATELIMIT_ENABLED` | `1` | Enforces rate limits (60 req/min on `/api/analyze`, 120 req/min on `/api/model-info`). |

> [!IMPORTANT]
> The backend automatically validates `models/spam_pipeline.joblib` with SHA-256 integrity verification against `models/model_hash.sha256` at startup. If the hash does not match, the process fails closed immediately.

### Frontend (`frontend/config.js`)

No secrets or environment variables are required on Vercel. `frontend/config.js` configures the API base URL:
* **Local Development (`:3000`):** Resolves automatically to `http://127.0.0.1:5000`.
* **Vercel (`*.vercel.app`):** Resolves automatically to `https://mailguard-ai.onrender.com`.
* **Same-Origin Fallback:** Resolves automatically to `window.location.origin`.

---

## 3. Render Backend Deployment Steps

### Option A: Render Blueprint (Infrastructure as Code)
1. Push your branch to GitHub.
2. In the Render Dashboard, select **New +** > **Blueprint**.
3. Select your repository. Render automatically reads `render.yaml`.
4. Review the plan (Free tier web service) and click **Apply**.

### Option B: Manual Web Service Setup
1. In the Render Dashboard, select **New +** > **Web Service**.
2. Connect your GitHub repository.
3. Configure the following service settings:
   - **Name:** `mailguard-ai`
   - **Region:** Oregon (US West) or closest to your users
   - **Branch:** `v2/redesign` (or `master`)
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120`
   - **Health Check Path:** `/api/health`
4. Under **Environment Variables**, add:
   - `CORS_ALLOWED_ORIGINS` = `https://<your-vercel-app>.vercel.app`
   - `PYTHON_VERSION` = `3.12.10`
   - `FLASK_DEBUG` = `0`
   - `MODEL_PATH` = `models/spam_pipeline.joblib`
   - `METADATA_PATH` = `models/metadata.json`
5. Click **Create Web Service**.
6. Note your Render URL: `https://<your-app>.onrender.com`.

---

## 4. Vercel Frontend Deployment Steps

The `frontend/` directory is pre-built with static HTML, CSS, JavaScript, fonts, and WASM cores.

1. In the Vercel Dashboard, select **Add New...** > **Project**.
2. Import your Git repository.
3. Configure the project:
   - **Framework Preset:** `Other`
   - **Root Directory:** `./`
   - **Build Command:** *(Leave empty; static assets are committed in `frontend/`)*
   - **Output Directory:** `frontend` *(Overridden automatically by root `vercel.json`)*
4. Under **Environment Variables**, leave empty (zero secrets required).
5. Click **Deploy**.
6. Once deployed, copy your production Vercel URL (e.g. `https://mailguard-ai.vercel.app`).
7. Update `CORS_ALLOWED_ORIGINS` on Render to include your exact Vercel URL.

---

## 5. Local Split-Architecture Testing

You can test the split architecture locally before pushing to production:

```powershell
# 1. Export static frontend (if you made changes to templates or static)
python scripts/build_frontend.py

# 2. Start the Flask backend on port 5000 with CORS allowed for port 3000
$env:CORS_ALLOWED_ORIGINS="http://127.0.0.1:3000,http://localhost:3000"
python app.py

# 3. In a separate terminal, serve the frontend on port 3000
python -m http.server 3000 --directory frontend

# 4. Open in browser
# Navigate to: http://127.0.0.1:3000/#/home
```

### Automated Playwright Verification
Run the end-to-end split architecture test:
```powershell
python scripts/verify_split_architecture.py
```
This script launches both servers, simulates cross-origin requests, validates API base resolution, checks server health indicators, tests both home and analyzer views, and saves a screenshot to `docs/screenshots/v2/split_architecture_cross_origin.png`.

---

## 6. Monolith Fallback (Render Only)

If you prefer deploying a single service:
* Flask serves `templates/index.html` at `/` and static assets from `static/`.
* No Vercel deployment needed.
* Simply deploy the repository to Render; the frontend works seamlessly on `https://mailguard-ai.onrender.com` in single-origin mode.

---

## 7. Troubleshooting & Operational Runbook

### Cold Start Delay (Free Tier)
* **Symptom:** The first request after 15 minutes of inactivity takes 30–60 seconds.
* **Behavior:** The frontend displays an informative banner:
  > *"Waking up the server, this can take up to a minute on the free host"*
* **Resolution:** Wait for the spin-up to complete; subsequent requests take <100ms.

### CORS Errors
* **Symptom:** Browser console shows `Access to fetch at '...' has been blocked by CORS policy`.
* **Cause:** The Vercel URL is not in `CORS_ALLOWED_ORIGINS` on Render.
* **Resolution:** Ensure the origin on Render matches the browser URL exactly (e.g. `https://mailguard-ai.vercel.app` with `https://`, no trailing slash).

### Rate Limit (HTTP 429)
* **Symptom:** `429 Too Many Requests` error returned.
* **Limits:** 60 requests/minute for `/api/analyze` and `/api/predict`.
* **Behavior:** Rate limits are stored in-memory per worker process and reset on worker restart.

### Integrity Failure (HTTP 500 on startup)
* **Symptom:** Container fails to start with `ValueError: Model artifact integrity verification failed`.
* **Cause:** The model artifact `models/spam_pipeline.joblib` was corrupted or does not match `models/model_hash.sha256`.
* **Resolution:** Re-run `python scripts/measure_performance.py` or re-generate `models/model_hash.sha256`.
