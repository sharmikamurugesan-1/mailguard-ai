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

## 3. Step-by-Step Split Deployment Sequence (Solving Chicken-and-Egg)

Deploying a split architecture involves a chicken-and-egg dependency:
* Vercel needs the Render URL in `frontend/config.js` and `vercel.json` CSP `connect-src`.
* Render needs the Vercel URL in `CORS_ALLOWED_ORIGINS` to accept cross-origin requests.

Follow this exact six-step sequence (a through f) to deploy reliably without guess-work:

### Step (a): Provision Render Backend
1. In the Render Dashboard, create your Web Service (`mailguard-ai`) pointing to your repository branch.
2. Set initial environment variables (`PYTHON_VERSION=3.12.10`, `FLASK_DEBUG=0`, `RATELIMIT_ENABLED=1`).
3. Set `CORS_ALLOWED_ORIGINS` to a temporary placeholder (or leave blank for now).
4. Deploy the service.

### Step (b): Obtain Assigned Render URL
1. Once Render provisions the service, copy the assigned backend URL from the dashboard:
   `https://<your-service-name>.onrender.com`
2. Test that the backend is alive by visiting `https://<your-service-name>.onrender.com/api/health`.

### Step (c): Configure API Origin Locally & Rebuild Frontend
Run the single-source-of-truth configuration tool locally:
```bash
python scripts/set_api_origin.py --origin https://<your-service-name>.onrender.com
```
This automated command:
- Validates strict HTTPS and rejects wildcards (`*`, `?`).
- Updates `PROD_API_URL` in `static/config.js`.
- Updates the CSP `connect-src` directive in `vercel.json`.
- Regenerates all assets in `frontend/` via `scripts/build_frontend.py`.

Commit and push these updated files to your repository:
```bash
git add static/config.js vercel.json frontend/
git commit -m "chore(deploy): set production render api origin"
git push
```

### Step (d): Deploy Vercel Static Frontend
1. In the Vercel Dashboard, import the repository.
2. Select **Framework Preset:** `Other`, **Root Directory:** `./`.
3. Vercel automatically detects `vercel.json` and serves `frontend/`.
4. Deploy the project.

### Step (e): Obtain Assigned Vercel URL
1. Copy your assigned production Vercel URL (e.g. `https://mailguard-ai.vercel.app`).
2. Verify in your browser that the site loads and `config.js` points to your Render backend.

### Step (f): Update Render CORS Allow-List & Verify
1. In the Render Dashboard under **Environment Variables**, set:
   ```env
   CORS_ALLOWED_ORIGINS=https://mailguard-ai.vercel.app
   ```
2. Render automatically restarts the service with the new CORS origin.
3. Verify live operation with the automated smoke test script:
   ```bash
   python scripts/smoke_test_deployed.py --api-url https://<your-service-name>.onrender.com --frontend-url https://mailguard-ai.vercel.app
   ```

---

## 4. Vercel Preview Deployments Policy & CORS Handling

### Strict Exact Origins Policy
* The Flask backend **strictly rejects** wildcard origins (`*`) and wildcard domain patterns (such as `*.vercel.app`).
* Every allowed origin must be an exact HTTPS URL.
* **By design, dynamic Vercel preview branch deployments are blocked from communicating with the production backend.** This prevents arbitrary preview builds or PR forks from accessing production rate-limit quotas or backend resources.

### Temporary Preview URL Testing Procedure
If you need to test a specific Vercel preview deployment against the Render backend:
1. Copy the exact preview URL generated by Vercel (e.g. `https://mailguard-ai-git-feature-preview.vercel.app`).
2. In the Render Dashboard under **Environment Variables**, temporarily append the preview URL to `CORS_ALLOWED_ORIGINS` (comma-separated):
   ```env
   CORS_ALLOWED_ORIGINS=https://mailguard-ai.vercel.app,https://mailguard-ai-git-feature-preview.vercel.app
   ```
3. Test your preview deployment.
4. Once verification is complete, remove the preview URL and restore only the production URL.

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
