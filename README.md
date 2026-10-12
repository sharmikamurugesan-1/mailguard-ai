# MailGuard AI — THREAT_RADAR 🛡️

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![scikit-learn 1.9.1](https://img.shields.io/badge/scikit--learn-1.9.1-orange.svg)](https://scikit-learn.org/)
[![Flask 3.1.3](https://img.shields.io/badge/Flask-3.1.3-black.svg)](https://flask.palletsprojects.com/)
[![Tests](https://img.shields.io/badge/tests-176%20passed-brightgreen.svg)](#-testing--quality-assurance)
[![WCAG 2.1 AA](https://img.shields.io/badge/WCAG%202.1%20AA-26%2F26%20contrast%20passed-brightgreen.svg)](#-accessibility--wcag-21-aa-compliance)
[![Axe-core](https://img.shields.io/badge/axe--core-0%20violations-brightgreen.svg)](#-accessibility--wcag-21-aa-compliance)
[![Security: Bandit & pip-audit](https://img.shields.io/badge/security-clean-brightgreen.svg)](#-security--privacy-architecture)
[![Models](https://img.shields.io/badge/models-SVM%20%7C%20LogReg%20%7C%20Naive%20Bayes-blue.svg)](#-threat_radar--multi-model-consensus-engine)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](#1-codebase-license)
[![Dataset Repo: GPL-3.0](https://img.shields.io/badge/dataset%20repo-GPL--3.0-lightgrey.svg)](#2-dataset-attribution)

> **Client-Side Privacy-First Email Threat Intelligence & Multi-Model Forensic Radar**
> MailGuard AI is a production-grade cybersecurity intelligence platform designed to address real-world email threat detection challenges: false-positive minimization, calibrated posterior probabilities, token attribution explainability, multi-signal URL & header forensics, and zero-upload client-side OCR & QR decoding.
> *Notice: MailGuard AI identifies email spam, phishing vectors, and social engineering patterns; it maintains zero server-side storage of emails or images, keeping user data private.*

---

## 🌐 Live Deployments & Environments

| Component | Target URL | Status | Architecture Notes |
|:---|:---|:---:|:---|
| **Production API (Render)** | [https://mailguard-ai-6ljt.onrender.com](https://mailguard-ai-6ljt.onrender.com) | **Live** | Gunicorn + Flask 3.1.3 backend, 3 serialized ML pipelines, fail-closed SHA-256 validation, CORS origin-restricted *(Free tier wakes in ~30s on cold start)* |
| **Frontend Preview (Vercel)** | [https://mailguard-aafw79uqj-sharmikamurugesan-1.vercel.app](https://mailguard-aafw79uqj-sharmikamurugesan-1.vercel.app) | **Live Preview** | Zero-runtime static export (`frontend/`), client-side Web Worker OCR/QR, CSP Level 3, localStorage + IndexedDB audit log |
| **Custom Production Domain** | [https://mailguard-ai.vercel.app](https://mailguard-ai.vercel.app) | Target | Intended production custom domain endpoint |

---

## 📸 Interface & Visual Walkthrough (THREAT_RADAR)

### 1. Home Quick-Scan Sandbox & Visual Threat Analysis
| Home Quick-Scan & Threat Radar (`#/home`) | Client-Side Image OCR & QR Decoding (`#/image-analysis`) |
|:---:|:---:|
| ![Home Threat Radar](docs/screenshots/v2/release_01_home.png) | ![Image OCR & QR Analysis](docs/screenshots/v2/release_02_image_analyzer.png) |

### 2. Multi-Model Card & Split Deployment Hardening
| Multi-Model Consensus Transparency (`#/model-card`) | Split-Deploy Cross-Origin Integration |
|:---:|:---:|
| ![Model Card Transparency](docs/screenshots/v2/release_03_model_card.png) | ![Split Architecture Integration](docs/screenshots/v2/split_architecture_cross_origin.png) |

### 3. Client-Side Web Worker OCR & Cold-Start Resilience
| In-Browser Web Worker OCR (`#/image-analysis`) | Graceful Backend Waking Banner |
|:---:|:---:|
| ![Client-Side OCR](docs/screenshots/v2/split_architecture_ocr.png) | ![Cold Start Waking Banner](docs/screenshots/v2/split_architecture_cold_start.png) |

---

## 🎯 THREAT_RADAR & Multi-Model Consensus Engine

MailGuard AI integrates **three production-grade machine learning pipelines**, providing dynamic single-model inference, automated algorithm comparison, and a 6-vector radar risk profile:

```
                          ┌──────────────────────────┐
                          │   Incoming Email Input   │
                          └────────────┬─────────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    ▼                  ▼                  ▼
           ┌─────────────────┐ ┌───────────────┐ ┌────────────────┐
           │ Calibrated SVM  │ │  Logistic Reg │ │  Naive Bayes   │
           │ (Primary Model) │ │  (Calibrated) │ │ (Probabilistic)│
           └────────┬────────┘ └───────┬───────┘ └────────┬───────┘
                    │                  │                  │
                    └──────────────────┼──────────────────┘
                                       ▼
                     ┌───────────────────────────────────┐
                     │   Consensus & Multi-Model Engine  │
                     │   • Dynamic model selection       │
                     │   • Side-by-side comparison       │
                     │   • Disagreement arbitration      │
                     └─────────────────┬─────────────────┘
                                       ▼
                     ┌───────────────────────────────────┐
                     │     THREAT_RADAR 6D Vector Map    │
                     │  1. Linguistic Spam Signals       │
                     │  2. URL Domain & TLD Reputation   │
                     │  3. Header Auth (SPF/DKIM/DMARC)  │
                     │  4. Formatting Anomalies & Caps   │
                     │  5. Vocabulary Entropy            │
                     │  6. Calibrated Model Confidence   │
                     └───────────────────────────────────┘
```

### 1. Calibrated Linear SVM (`models/spam_pipeline.joblib`)
- **Role**: Primary Winner & Baseline Classifier.
- **Attributes**: TF-IDF `(1, 2)` n-grams (15,000 features) + Platt scaling for calibrated posterior probabilities.
- **Test Performance**: **98.83% Precision**, **99.07% Recall**, **98.95% F1 Score**.

### 2. Logistic Regression (`models/lr_pipeline.joblib`)
- **Role**: Alternative Linear Probabilistic Pipeline.
- **Attributes**: L2 regularization with balanced class weighting; provides smooth log-odds interpretation.

### 3. Multinomial Naive Bayes (`models/nb_pipeline.joblib`)
- **Role**: High-speed probabilistic baseline.
- **Attributes**: Laplace smoothing ($\alpha = 1.0$), rapid inference under high throughput constraints.

---

## 🎨 Luxury Maroon & Deep Burgundy Design System

The THREAT_RADAR interface features a Render-inspired dark theme with a distinct luxury wine/burgundy palette:

- **Dominant Canvas**: `--color-bg: #1c070f;` (Deep burgundy canvas; zero harsh near-black)
- **Sub-Canvas & Framing**: `--color-bg-subtle: #250b14;`
- **Primary Surfaces & Cards**: `--color-surface: #2b0d18;`
- **Elevated Cards & Popovers**: `--color-surface-2: #361120;`
- **Borders & Separators**: `--color-border: #4d192c;`, `--color-border-hover: #6b243e;`
- **Primary Interactive Action**: `--color-primary: #f06b88;` (Dusty rose / muted pink)
- **Secondary Accent**: `--color-maroon-gold: #f5c056;` (Subtle gold badges)
- **High-Contrast Off-White Text**: `--color-text-main: #fcf4ec;` (16.44:1 contrast ratio)
- **Secondary Muted Text**: `--color-text-muted: #e0bec8;` (10.54:1 contrast ratio)
- **Contrast Guarantee**: **26 / 26 color pairs strictly PASS WCAG 2.1 AA** ($\ge 4.5:1$).

---

## 🏗️ System Architecture & Engineering Principles

```
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                         CLIENT-SIDE BROWSER                            │
  │                                                                         │
  │   Direct Text / EML Upload                   Image / Screenshot Upload   │
  │              │                                           │              │
  │              │                                           ▼              │
  │              │                            ┌───────────────────────────┐ │
  │              │                            │ Web Worker OCR & QR Engine│ │
  │              │                            │ • Self-Hosted Tesseract.js│ │
  │              │                            │ • Self-Hosted jsQR        │ │
  │              │                            │ • ZERO image upload       │ │
  │              │                            └─────────────┬─────────────┘ │
  │              │                                          │               │
  │              │         Extracted Text & QR URLs         │               │
  │              └────────────────────┬─────────────────────┘               │
  └───────────────────────────────────┼─────────────────────────────────────┘
                                      │
                         POST /api/analyze (JSON)
                                      │
                                      ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                    FLASK BACKEND (Render Web Service)                   │
  │                                                                         │
  │   ┌─────────────────────────────────────────────────────────────────┐   │
  │   │ Security Middleware & Input Validation                          │   │
  │   │ • ProxyFix (x_for=1 genuine IP extraction)                      │   │
  │   │ • Flask-Limiter (60 req/min per IP)                             │   │
  │   │ • Content Security Policy & Strict Headers                      │   │
  │   │ • Max payload limit (2 MB) & input char limit (20k chars)       │   │
  │   └───────────────────────────────┬─────────────────────────────────┘   │
  │                                   │                                     │
  │                                   ▼                                     │
  │   ┌─────────────────────────────────────────────────────────────────┐   │
  │   │ Multi-Model Inference Engine (src/predictor.py)                 │   │
  │   │ • SHA-256 Model Integrity Verification at load (fail-closed)     │   │
  │   │ • Text normalization (URLs, emails, numbers, currencies)        │   │
  │   │ • Dynamic Model Switcher (SVM, Logistic Regression, Naive Bayes)│   │
  │   │ • Token contribution signals (weights x TF-IDF)                 │   │
  │   └───────────────────────────────┬─────────────────────────────────┘   │
  │                                   │                                     │
  │                                   ▼                                     │
  │   ┌─────────────────────────────────────────────────────────────────┐   │
  │   │ Multi-Signal Threat Heuristics Engine (src/signals.py)          │   │
  │   │ • URL reputation: punycode, IP hostnames, redirectors, TLDs    │   │
  │   │ • Header analysis: SPF, DKIM, DMARC, Return-Path discrepancies │   │
  │   │ • Formatting anomalies: excessive capitals, urgent keywords     │   │
  │   │ • Reliability heuristics: short input, low vocab coverage       │   │
  │   └───────────────────────────────┬─────────────────────────────────┘   │
  │                                   │                                     │
  │                                   ▼                                     │
  │   ┌─────────────────────────────────────────────────────────────────┐   │
  │   │ Composite Scoring & Calibration                                 │   │
  │   │ • Combined Risk Score (0 - 100)                                 │   │
  │   │ • THREAT_RADAR 6-Vector Breakdown                               │   │
  │   │ • Sensitivity Threshold Matrix (Low, Medium, High)              │   │
  │   │ • Zero server logging or storage of analyzed text               │   │
  │   └───────────────────────────────┬─────────────────────────────────┘   │
  └───────────────────────────────────┼─────────────────────────────────────┘
                                      │
                         Structured JSON Response
                                      │
                                      ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                         CLIENT AUDIT PERSISTENCE                        │
  │                                                                         │
  │   • Results rendered via safe textContent / DOM APIs (0 innerHTML)      │
  │   • Telemetry logged exclusively to browser IndexedDB                   │
  │   • Full scan history, search, filtering, and CSV/JSON export           │
  │   • "History stays on this device" guarantee                            │
  └─────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Model Evaluation & Selection Protocol

The machine learning model was selected using **5-Fold Stratified Cross-Validation** on the training split of **24,369** samples (from **30,462** total samples).

### Selection Criterion Hierarchy
- **Priority 1**: Spam Precision $\ge 0.98$ (Disqualifying threshold).
- **Priority 2**: Highest Recall on Spam (Catch maximum threats among qualifying models).
- **Priority 3**: Highest F1 Score.
- *Rule*: Never select based on accuracy alone.

### 5-Fold Stratified Cross-Validation Results (Train Set: $N = 24,369$)

| Model Candidate | CV Precision (Spam) | CV Recall (Spam) | CV F1 Score | CV Accuracy | Status |
|:---|:---:|:---:|:---:|:---:|:---:|
| **Calibrated Linear SVM** | **98.72%** (±0.0022) | **99.29%** (±0.0027) | **99.00%** (±0.0010) | **99.04%** (±0.0010) | **WINNER (Selected)** |
| Multinomial Naive Bayes | 98.24% (±0.0028) | 98.52% (±0.0011) | 98.38% (±0.0009) | 98.45% (±0.0009) | Qualified, Runner-Up |
| Logistic Regression | 97.65% (±0.0025) | 99.41% (±0.0021) | 98.52% (±0.0010) | 98.57% (±0.0010) | Disqualified (Precision < 98%) |

*Decision Rationale*: Logistic Regression was disqualified under Priority 1 because its CV precision was only 97.65%. Between the qualifying models, Calibrated Linear SVM dominated Multinomial Naive Bayes on both Recall (99.29% vs 98.52%) and F1 (99.00% vs 98.38%). Both models are preserved and accessible for live algorithmic comparison in the THREAT_RADAR platform.

---

## 🧪 Independent Held-Out Test Set Performance

Evaluated on the held-out test split of **6,093** emails.

### Set A: Full Held-Out Test Set ($N = 6,093$)
- **Accuracy**: **99.00%**
- **Precision (Spam)**: **98.83%**
- **Recall (Spam)**: **99.07%**
- **F1 Score**: **98.95%**
- **Confusion Matrix**:
  - **True Positives (TP)**: 2,884
  - **True Negatives (TN)**: 3,148
  - **False Positives (FP)**: 34
  - **False Negatives (FN)**: 27

---

## 🔍 Data Leakage & Near-Duplicate Analysis

Pairwise TF-IDF cosine similarity was computed between all 6,093 test emails and the 24,369 training emails.

### Near-Duplicate Findings (17.5% to 19.8% Overlap)
- **Production N-gram Vectorizer `(1, 2)`**: Identifies **1,208** near-duplicates (**19.83%** of the test set).
- **Unigram Vectorizer `(1, 1)`**: Identifies **1,070** near-duplicates (**17.56%** of the test set).
- *Audit Finding*: All 61 held-out errors (34 FP, 27 FN) occurred on strictly non-near-duplicate emails.

### Generalization Comparison Table

| Metric | Full Test Set ($N = 6,093$) | De-Duplicated Test Set ($N = 4,885$) | Net Difference |
|:---|:---:|:---:|:---:|
| **Accuracy** | 99.00% | **98.75%** | -0.25% |
| **Precision (Spam)** | 98.83% | **98.52%** | -0.31% |
| **Recall (Spam)** | 99.07% | **98.82%** | -0.25% |
| **F1 Score** | 98.95% | **98.67%** | -0.28% |
| **False Positives (FP)** | 34 | 34 | 0 (Unchanged) |
| **False Negatives (FN)** | 27 | 27 | 0 (Unchanged) |

> **Deduplication Audit Takeaway**: Removing all 1,208 near-duplicates leaves 4,885 completely distinct test emails. The model maintains 98.75% accuracy and 98.52% precision. Because false positives and false negatives remain identical (34 FP, 27 FN), model performance is driven by true generalization rather than memorized corporate boilerplate.

### 95% Bootstrap Confidence Intervals ($B = 1,000$ iterations)

| Evaluation Metric | Full Test Set ($N = 6,093$) | De-Duplicated Test Set ($N = 4,885$) |
|:---|:---:|:---:|
| **Accuracy** | 99.00% [98.74%, 99.23%] | 98.75% [98.42%, 99.06%] |
| **Precision** | 98.83% [98.41%, 99.20%] | 98.52% [97.98%, 98.98%] |
| **Recall** | 99.07% [98.72%, 99.42%] | 98.82% [98.34%, 99.25%] |
| **F1 Score** | 98.95% [98.63%, 99.25%] | 98.67% [98.32%, 99.00%] |

### Operating Points across Sensitivity Thresholds

Users can configure detection sensitivity in Settings:

| Sensitivity Setting | Decision Threshold | Test Precision | Test Recall | Test F1 Score | Primary Use Case |
|:---|:---:|:---:|:---:|:---:|:---|
| **Low** | 0.65 | 99.13% | 98.39% | 98.76% | Executive inboxes, zero tolerance for False Positives |
| **Medium (Default)** | 0.50 | 98.83% | 99.07% | 98.95% | Balanced operational baseline |
| **High** | 0.35 | 98.37% | 99.45% | 98.91% | Threat hunting, maximum threat capture |

---

## 🎯 Uncertain Band Calibration

Tuned on out-of-fold validation predictions across the 24,369 training samples:
- **Band Window**: $[0.40, 0.60]$
- **Samples in Band**: **113** emails (0.46% of training data)
- **Class Distribution in Band**: 58 Ham vs 55 Spam (~50/50 split confirming genuine ambiguity)
- **Performance Outside Band**:
  - Accuracy: **99.20%**
  - Precision: **98.90%**
  - Recall: **99.44%**

---

## 🔌 REST API Specification

All endpoints are rate-limited via **Flask-Limiter** using genuine client IP addresses extracted via `werkzeug.middleware.proxy_fix.ProxyFix`.

### 1. `POST /api/analyze` (THREAT_RADAR Deep Forensic Pipeline)
Performs combined NLP classification, URL reputation, header validation, and radar vector scoring.
**Rate Limit**: `60 per minute`

**Request Payload (`application/json`):**
```json
{
  "text": "Subject: Security alert: Unusual login\n\nPlease verify your account at http://login-review.example.test",
  "headers": "From: security@fakebank.test\nTo: user@example.test\nSubject: Security alert",
  "model": "svm",
  "options": {
    "scan_urls": true,
    "scan_headers": true,
    "sensitivity": "medium"
  }
}
```

**Response Payload (`200 OK`):**
```json
{
  "verdict": "Spam",
  "risk_score": 92,
  "confidence": 0.9842,
  "probabilities": {
    "spam": 0.9842,
    "ham": 0.0158
  },
  "key_findings": [
    "High-confidence machine learning spam pattern detected (98.4%).",
    "URL links to suspicious domain structure."
  ],
  "signals": {
    "model_tokens": [
      { "token": "security", "weight": 0.842, "type": "spam" }
    ],
    "urls": [
      { "url": "http://login-review.example.test", "flags": ["suspicious_tld"] }
    ],
    "headers": {
      "spf": "neutral",
      "dkim": "none",
      "dmarc": "none",
      "alignment": false
    }
  },
  "radar_vectors": {
    "linguistic": 94,
    "urls": 80,
    "headers": 70,
    "formatting": 40,
    "entropy": 65,
    "confidence": 98
  },
  "reliability": {
    "level": "high",
    "warnings": []
  }
}
```

### 2. `POST /api/compare` (Consensus Multi-Model Engine)
Runs the input email across all 3 trained models simultaneously (`svm`, `lr`, `nb`) and returns side-by-side metrics and consensus agreement.
**Rate Limit**: `30 per minute`

### 3. `GET /api/models`
Returns list of available model architectures, active default model, and training parameters.
**Rate Limit**: `60 per minute`

### 4. `POST /api/predict` (v1 Lightweight Classifier)
Classifies raw email text.
**Rate Limit**: `60 per minute`

### 5. `GET /api/health`
Health probe used for uptime monitoring and waking UX. Returns status and model loading state.
**Rate Limit**: `120 per minute`

### 6. `GET /api/model-info`
Returns model metadata, SHA-256 hash, and operating parameters.

---

## 🔒 Security & Privacy Architecture

- **Fail-Closed Model Integrity**: At application load time, `src.predictor.SpamPredictor` computes the SHA-256 checksum of `models/spam_pipeline.joblib` and validates it against the committed hash (`453414c9bb3889c1cc2402ee26473e6d74bf7e7a78cef26eac24da2d8ddfc9f8`). Any alteration causes immediate initialization termination.
- **Strict Content Security Policy (CSP Level 3)**:
  ```http
  Content-Security-Policy: default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; style-src 'self'; img-src 'self' data: blob:; worker-src 'self' blob:; connect-src 'self' https://mailguard-ai-6ljt.onrender.com; font-src 'self'; frame-ancestors 'none'; form-action 'self';
  ```
  Zero inline scripts, zero inline styles, and zero `innerHTML` across all views.
- **Zero Server-Side Storage**: Emails, uploaded images, and extracted text are processed entirely in-memory and are **never logged or persisted to disk or database**.
- **Sandboxed Client-Side Image OCR**: Uploaded images are processed in the user's browser using self-hosted Tesseract.js and jsQR in a dedicated Web Worker. Images are never transmitted over the network.
- **Vulnerability Audit**:
  - `bandit -r src/`: **0 issues identified** (clean static security analysis).
  - `pip-audit -r requirements.txt`: **0 known vulnerabilities found**.

---

## ⚡ Performance Benchmarks & Capacity Proof

Measured on the production configuration:

- **Resident Set Size (RSS) Memory**:
  - Baseline Python runtime: **18.24 MB**
  - After model and application initialization: **153.09 MB**
  - After 20 consecutive inference requests: **159.76 MB** (**31.2%** of Render Free 512 MB allocation; **352.24 MB** available headroom).
- **Cold-Start Time**: **2.65 seconds** (subprocess spawn, model integrity verification, pipeline deserialization, health check).
- **Inference Latency (`/api/analyze` over 100 requests)**:
  - Mean: **16.74 ms**
  - Median (p50): **16.19 ms**
  - 95th Percentile (p95): **18.33 ms**
  - 99th Percentile (p99): **72.72 ms**
- **1,000-Concurrency Capacity Proof**:
  - Verified under `scripts/test_1000_concurrency.py` and `locustfile.py` with 0 dropped connections under bounded queuing.
- **Optimized Bundle Sizes (Gzipped)**:
  - Core HTML (`templates/index.html`): 125.8 KB raw / **24.6 KB gzip**
  - Stylesheet (`static/css/style.css`): 90.7 KB raw / **13.9 KB gzip**
  - Core JavaScript (`static/js/app.js`): 155.8 KB raw / **33.5 KB gzip**
  - Vendor OCR & QR Libraries: Lazy-loaded only on demand.

---

## ♿ Accessibility (WCAG 2.1 AA Compliance)

Audited programmatically via **Axe-core** integrated with Playwright across all 11 application routes:

| Route | Route Name | Axe-core Violations | Compliance Status |
|:---|:---|:---:|:---:|
| `#/home` | Home & Quick Sandbox | **0** | Pass (WCAG AA/AAA) |
| `#/analyze` | Email Analyzer & Report | **0** | Pass (WCAG AA/AAA) |
| `#/image-analysis` | Client-Side Image OCR/QR | **0** | Pass (WCAG AA/AAA) |
| `#/dashboard` | Local Analytics Dashboard | **0** | Pass (WCAG AA/AAA) |
| `#/history` | Scan History & Audit Log | **0** | Pass (WCAG AA/AAA) |
| `#/reports` | Reports & File Export | **0** | Pass (WCAG AA/AAA) |
| `#/settings` | Settings & Preferences | **0** | Pass (WCAG AA/AAA) |
| `#/docs` | API Documentation | **0** | Pass (WCAG AA/AAA) |
| `#/model-card` | Model Transparency Card | **0** | Pass (WCAG AA/AAA) |
| `#/features` | Platform Capabilities | **0** | Pass (WCAG AA/AAA) |
| `#/privacy` | Privacy & Data Architecture | **0** | Pass (WCAG AA/AAA) |

**Color Contrast Audit (`scripts/check_contrast.py`)**: **26 / 26 color pairs PASS WCAG 2.1 AA** ($\ge 4.5:1$).

---

## 🚀 Quickstart & Local Development

### 1. Prerequisites
- Python 3.12+
- Git

### 2. Setup Virtual Environment
```bash
# Clone repository
git clone https://github.com/sharmikamurugesan-1/mailguard-ai.git
cd mailguard-ai

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Linux / macOS:
source .venv/bin/activate
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```bash
# Production runtime
pip install -r requirements.txt

# Development and testing dependencies
pip install -r requirements-dev.txt
```

### 4. Run Development Server
```bash
python -m src.app
# Application launches at http://127.0.0.1:5000
```

### 5. Run Production Server (Gunicorn)
```bash
gunicorn app:app --bind 0.0.0.0:5000 --workers 1 --threads 4 --timeout 120
```

---

## 🧪 Testing & Quality Assurance

```bash
# 1. Run unit & integration test suite (176 tests)
pytest -v -rs

# 2. Run color contrast verification suite (26 WCAG AA checks)
python scripts/check_contrast.py

# 3. Export standalone static frontend bundle for Vercel
python scripts/build_frontend.py

# 4. Run full Playwright regression & 11-route Axe-core accessibility audit
python scripts/verify_full_regression.py

# 5. Run split-deploy architecture & Web Worker OCR verification
python scripts/verify_split_architecture.py

# 6. Run static security audit
bandit -r src/

# 7. Run dependency vulnerability audit
pip-audit -r requirements.txt

# 8. Verify README numerical claims against models/metadata.json
python scripts/verify_readme_metrics.py
```

---

## 📦 Deployment Configuration

### 1. Backend on Render
The repository includes a ready-to-use [`render.yaml`](render.yaml) blueprint:
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120`
- **Health Check Path**: `/api/health`

### 2. Frontend on Vercel
The static frontend export in `frontend/` is managed via [`vercel.json`](vercel.json):
- **Output Directory**: `frontend`
- **Security Headers**: Strict Level 3 Content Security Policy with connect-src directed to the Render API origin.

---

## ⚠️ Transparent Limitations & Known Failure Modes

1. **Historical Dataset Context**: Trained on the **Enron Spam Dataset** (~2000–2002 corporate communications). Vocabulary reflects energy trading, corporate operations, and early web marketing.
2. **Domain Shift & Modern Threat Failure Case**: Modern attacks (spear-phishing, business email compromise, invoice fraud) use convincing corporate prose.
   - **Known False Negative in Testing**: In our hand-written sanity set, the invoice fraud email (`Subject: Overdue invoice attached - wire transfer instructions`, `Body: Please review the attached invoice INV-9042 for legal advisory services... Send the wire payment to account #4492048`) was classified as **Legitimate (Ham)** with low spam probability. Because terms like `invoice`, `attached`, and `legal advisory services` frequently occur in legitimate corporate records, the n-gram model fails on this pattern.
3. **Probability Calibration vs Guarantee**: Model confidence is an empirical probability estimate, not a mathematical certainty.
4. **Scope Boundaries**:
   - **Spam & Phishing only**: Does not scan binary attachments, macros, or malware executables.
   - **Not an inbox filter**: Operates as an interactive on-demand scanner; does not route, intercept, or modify live mail server feeds.
   - **No user accounts**: Operates completely stateless on the backend; all telemetry resides on the user's local device.
5. **Free-Tier Cold Start**: Hosted on Render Free tier with 512 MB RAM and 0.1 CPU; idle instances spin down after 15 minutes, requiring ~30s to wake up on the next request.

---

## 📜 License & Dataset Attribution

### 1. Codebase License
The source code in this repository is licensed under the terms of the [MIT License](LICENSE). Copyright (c) 2026 Sharmika Murugesan.

### 2. Dataset Attribution
The dataset repository ([MWiechmann/enron_spam_data](https://github.com/MWiechmann/enron_spam_data)) is published under **GPL-3.0**; the underlying Enron email corpus has its own public domain provenance (CALO Project). The raw dataset is not redistributed in this repository (see `data/README.md` for re-download instructions).
