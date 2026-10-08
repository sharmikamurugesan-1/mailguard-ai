# Deployment Guide: MailGuard AI on Render 🚀

This guide provides step-by-step instructions for deploying MailGuard AI to **Render** using either the automated Blueprint specification or manual Web Service configuration.

---

## 📋 Prerequisites
1. **GitHub Repository**: Push your local MailGuard AI repository to GitHub (e.g. `https://github.com/<your-username>/mailguard-ai`).
2. **Render Account**: Sign up or log in at [render.com](https://render.com).

---

## ⚡ Method 1: Blueprint Deployment (Recommended)

Render Blueprints allow infrastructure-as-code deployment driven by the included [`render.yaml`](../render.yaml).

1. Log in to the [Render Dashboard](https://dashboard.render.com).
2. Click **New +** in the top navigation bar and select **Blueprint**.
3. Connect your GitHub account and select your `mailguard-ai` repository.
4. Render automatically parses `render.yaml` and displays the proposed service configuration:
   - **Service Name**: `mailguard-ai`
   - **Runtime**: `Python`
   - **Plan**: `Free`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120`
   - **Health Check Path**: `/api/health`
5. Click **Apply**.
6. Render will automatically trigger the build pipeline, install dependencies, load model artifacts, and start Gunicorn.

---

## 🛠️ Method 2: Manual Web Service Setup

If you prefer configuring the service manually through Render's UI:

1. In Render Dashboard, click **New +** and select **Web Service**.
2. Connect your GitHub repository `mailguard-ai`.
3. Configure the settings:
   - **Name**: `mailguard-ai`
   - **Region**: `Oregon (US West)` (or closest to your users)
   - **Branch**: `master` (or your default branch)
   - **Root Directory**: *(leave blank — defaults to repository root)*
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120`
   - **Instance Type**: `Free`
4. Expand **Advanced Settings**:
   - **Health Check Path**: `/api/health`
   - **Auto-Deploy**: `Yes`
5. Add the following **Environment Variables**:
   | Key | Value | Description |
   |:---|:---|:---|
   | `PYTHON_VERSION` | `3.12.10` | Enforces exact Python runtime |
   | `FLASK_DEBUG` | `0` | Ensures production mode |
   | `MODEL_PATH` | `models/spam_pipeline.joblib` | Model artifact path |
   | `METADATA_PATH` | `models/metadata.json` | Metadata path |
6. Click **Create Web Service**.

---

## 🔍 Verification & Health Checking

Once the deployment completes and logs state `==> Your service is live 🎉`, test the endpoints:

### 1. Automated Smoke Test Script
We provide a standalone validation script that uses only Python's standard library (`urllib`):
```bash
python scripts/smoke_test_deployed.py https://<your-service-name>.onrender.com
```

### 2. Manual CLI Verification
```bash
# Verify health check
curl -i https://<your-service-name>.onrender.com/api/health

# Verify model metadata
curl -s https://<your-service-name>.onrender.com/api/model-info | jq .

# Verify live prediction
curl -X POST https://<your-service-name>.onrender.com/api/predict \
  -H "Content-Type: application/json" \
  -d '{"subject": "Quarterly Budget Review", "body": "Attached is the spreadsheet for next weeks financial meeting."}'
```

---

## ❄️ Cold-Start Characteristics & UX Handling

On Render's Free tier:
- **Spin Down**: Free web services spin down after **15 minutes** of inactivity to conserve resources.
- **Spin Up Time**: The first incoming request wakes the instance, which takes **30–50 seconds** (container initialization + loading scikit-learn model into memory).
- **Built-in Resilience**: MailGuard AI's frontend is specifically designed for free-tier hosting:
  - If a classification request takes longer than **5 seconds**, an informative warning banner automatically displays: *"Server is waking up on free hosting... please allow up to 45s."* with a live progress countdown.
  - The request timeout is set to **90 seconds** (well above typical spin-up latency).
  - If a network error or cold-start timeout occurs, the frontend automatically executes a clean **1-retry attempt** before surfacing an error modal with a manual "Try Again" button.
