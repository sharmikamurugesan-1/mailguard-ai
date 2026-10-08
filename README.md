# MailGuard AI 🛡️

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![scikit-learn 1.9.1](https://img.shields.io/badge/scikit--learn-1.9.1-orange.svg)](https://scikit-learn.org/)
[![Flask 3.1.3](https://img.shields.io/badge/Flask-3.1.3-black.svg)](https://flask.palletsprojects.com/)
[![Tests](https://img.shields.io/badge/tests-71%20passed-brightgreen.svg)](#testing--quality-assurance)
[![License: GPL-3.0](https://img.shields.io/badge/dataset%20license-GPL--3.0-blue.svg)](#dataset--license)

> **Portfolio-Grade Email Spam, Ham, and Ambiguity Classifier**  
> MailGuard AI is an end-to-end machine learning system designed to address the real-world operational challenges of email filtering: strict false-positive aversion, decision calibration, out-of-distribution detection, explainable token attribution, and zero-downtime cold start handling.

---

## 📸 Interface & Visual Walkthrough

| Legitimate Email (Ham) | Phishing / Spam Email | Ambiguous / Uncertain Band |
|:---:|:---:|:---:|
| ![Legitimate Email Result](docs/screenshots/06_ham_result.png) | ![Spam Email Result](docs/screenshots/05_spam_result.png) | ![Uncertain Email Result](docs/screenshots/07_uncertain_result.png) |

| Model Transparency Card | Cold Start Resilience Banner (Render Free Tier) | Mobile Responsive Layout (375px) |
|:---:|:---:|:---:|
| ![Model Metadata Card](docs/screenshots/08_model_data_card.png) | ![Cold Start Awakening Banner](docs/screenshots/10_waking_banner_5s.png) | ![Mobile Viewport View](docs/screenshots/11_mobile_375px.png) |

---

## 🏗️ System Architecture & Engineering Principles

```
  User Email Input (Subject + Body)
                 │
                 ▼
  ┌──────────────────────────────────────────────┐
  │         Normalization & Preprocessing        │
  │  • Lowercase, Whitespace & Control Clean     │
  │  • Regex Tokenization: __url__, __email__,   │
  │    __number__, __currency__                  │
  └──────────────────────┬───────────────────────┘
                         │
                         ▼
  ┌──────────────────────────────────────────────┐
  │         Feature Extraction & Vectorizer      │
  │  • TF-IDF (Unigrams + Bigrams: (1, 2))       │
  │  • Max Features: 15,000 | Sublinear TF: True │
  └──────────────────────┬───────────────────────┘
                         │
                         ▼
  ┌──────────────────────────────────────────────┐
  │        Calibrated Linear SVM Classifier       │
  │  • LinearSVC(class_weight='balanced')        │
  │  • CalibratedClassifierCV (Platt Scaling)    │
  └──────────────────────┬───────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        ▼                                 ▼
┌───────────────────────────────┐ ┌───────────────────────────────┐
│     Three-Tier Decision       │ │    Reliability & Heuristics   │
│ • P(spam) < 0.40  => Ham      │ │ • Short input (< 10 tokens)   │
│ • [0.40, 0.60]    => Uncertain│ │ • Low vocab coverage (< 50%)  │
│ • P(spam) > 0.60  => Spam     │ │ • Non-English language check  │
└───────────────────────────────┘ └───────────────────────────────┘
```

### Key Engineering Decisions
1. **False Positive Aversion**: In corporate communications, misclassifying a legitimate email as spam (False Positive) is far more damaging than letting an occasional spam message reach the inbox. Our model selection protocol enforces a strict constraint: **Spam Precision $\ge 0.98$** before considering recall or F1 score.
2. **Probability Calibration**: Standard Linear SVMs output uncalibrated hinge loss margins. We wrap `LinearSVC` inside `CalibratedClassifierCV` using sigmoid Platt scaling, yielding well-calibrated posterior probabilities.
3. **Explicit Uncertain Band**: Instead of forcing a hard binary decision at 0.50, emails with posterior probabilities in **[0.40, 0.60]** are routed to an `uncertain` status, prompting human review.
4. **Heuristic Guardrails**: When emails contain fewer than 10 tokens, unfamiliar vocabulary (< 50% coverage), or non-English text, structured reliability warnings are attached directly to the prediction.
5. **Cold-Start UX**: Render's free tier spins down idle instances. If an API request exceeds 5 seconds, the UI surfaces an informative countdown banner and automatically executes a clean 1-retry attempt with a 90-second safety window.

---

## 📊 Rigorous Model Evaluation & Selection

The model was selected using **5-Fold Stratified Cross-Validation** on the training split of **24,369** samples (from **30,462** total samples).

### Selection Criterion Hierarchy
- **Priority 1**: Spam Precision $\ge 0.98$ (Hard disqualification threshold).
- **Priority 2**: Highest Recall on Spam (Catch the maximum number of threats among qualifying models).
- **Priority 3**: Highest F1 Score.
- *Rule*: Never select based on accuracy alone.

### 5-Fold Stratified Cross-Validation Results (Train Set: $N = 24,369$)

| Model Candidate | CV Precision (Spam) | CV Recall (Spam) | CV F1 Score | CV Accuracy | Status |
|:---|:---:|:---:|:---:|:---:|:---:|
| **Calibrated Linear SVM** | **98.72%** (±0.0022) | **99.29%** (±0.0027) | **99.00%** (±0.0010) | **99.04%** (±0.0010) | **WINNER (Selected)** |
| Multinomial Naive Bayes | 98.24% (±0.0028) | 98.52% (±0.0011) | 98.38% (±0.0009) | 98.45% (±0.0009) | Qualified, Runner-Up |
| Logistic Regression | 97.65% (±0.0025) | 99.41% (±0.0021) | 98.52% (±0.0010) | 98.57% (±0.0010) | **Disqualified** (Precision < 98%) |

*Decision Rationale*: Logistic Regression was disqualified under Priority 1 because its CV precision was only 97.65%. Between the two qualifying models, Calibrated Linear SVM dominated Multinomial Naive Bayes on both Recall (99.29% vs 98.52%) and F1 (99.00% vs 98.38%).

---

## 🧪 Independent Held-Out Test Set Performance

Evaluated once on the held-out test split of **6,093** emails.

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

## 🔍 Data Hygiene & Near-Duplicate Leakage Audit

To prevent test-set inflation from near-duplicate corporate emails, we computed pairwise TF-IDF cosine similarities between all 6,093 test samples and the 24,369 training samples.

- **Near-Duplicates Identified (Cosine $\ge 0.95$)**: **1,208** emails (**19.83%** of the test set).
- **Strictly Non-Overlapping Test Set**: **4,885** emails.

### Generalization Comparison Table

| Metric | Full Test Set ($N = 6,093$) | De-Duplicated Test Set ($N = 4,885$) | Net Difference |
|:---|:---:|:---:|:---:|
| **Accuracy** | 99.00% | **98.75%** | -0.25% |
| **Precision (Spam)** | 98.83% | **98.52%** | -0.31% |
| **Recall (Spam)** | 99.07% | **98.82%** | -0.25% |
| **F1 Score** | 98.95% | **98.67%** | -0.28% |
| **False Positives (FP)** | 34 | 34 | 0 (Unchanged) |
| **False Negatives (FN)** | 27 | 27 | 0 (Unchanged) |

> **Conclusion**: Stripping all near-duplicates proves that model accuracy remains above 98.7% and spam precision remains above 98.5%. The performance is driven by genuine generalization, not memorization.

---

## 🎯 Uncertain Band Calibration

Tuned exclusively on out-of-fold validation predictions across the 24,369 training samples:
- **Band Window**: $[0.40, 0.60]$
- **Samples in Band**: **113** emails (0.46% of training data)
- **Class Distribution in Band**: 58 Ham vs 55 Spam (~50/50 split confirming true ambiguity)
- **Performance Outside Band**:
  - Accuracy: **99.20%**
  - Precision: **98.90%**
  - Recall: **99.44%**

---

## 🔌 REST API Specification

### 1. `POST /api/predict`
Classifies an email subject and body.

**Request Payload (`application/json`):**
```json
{
  "subject": "Important update on project deliverables",
  "body": "Hi team, please find attached the revised schedule for Q3."
}
```

**Response Payload (`200 OK`):**
```json
{
  "prediction": "ham",
  "label_display": "Legitimate",
  "confidence": 0.9984,
  "spam_probability": 0.0016,
  "risk_level": "low",
  "signals": [
    { "term": "team", "type": "ham", "weight": -0.8421 },
    { "term": "schedule", "type": "ham", "weight": -0.6312 }
  ],
  "reliability": {
    "level": "high",
    "warnings": []
  },
  "dataset_type": "email",
  "model_version": "1.0.0"
}
```

### 2. `GET /api/health`
Health check endpoint used by Render and container orchestrators.
```json
{
  "status": "healthy",
  "model_loaded": true,
  "version": "1.0.0"
}
```

### 3. `GET /api/model-info`
Returns full model metadata, training parameters, and performance metrics.

---

## ⚠️ Transparent Limitations & Dataset Context

1. **Historical Dataset Context**: Trained on the **Enron Spam Dataset** (~2000–2002 corporate communications). Vocabulary reflects energy trading, corporate administration, and early web marketing.
2. **Domain Shift & Modern Threats**: Modern spear-phishing campaigns (QR code quishing, SVG obfuscation, cloud file lures) exhibit different textual patterns. An adversarial drift warning is displayed in the UI.
3. **Language Scope**: The model is optimized for English text. Non-English submissions trigger an automated reliability warning.
4. **Input Length**: Emails under 10 tokens provide minimal TF-IDF context and trigger a `short_input` reliability alert.

---

## 🚀 Quickstart & Local Development

### 1. Prerequisites
- Python 3.12+
- Git

### 2. Setup Virtual Environment
```bash
# Clone the repository
git clone https://github.com/sharmikamurugesan/mailguard-ai.git
cd mailguard-ai

# Create and activate virtual environment
python -m venv .venv

# On Linux/macOS:
source .venv/bin/activate

# On Windows:
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```bash
# Production dependencies
pip install -r requirements.txt

# Development and testing dependencies
pip install -r requirements-dev.txt
```

### 4. Run Development Server
```bash
python -m src.app
# Server starts at http://127.0.0.1:5000
```

### 5. Run Production Server (Gunicorn)
```bash
gunicorn app:app --bind 0.0.0.0:5000 --workers 2 --timeout 120
```

---

## 🧪 Testing & Quality Assurance

```bash
# Run complete test suite (71 passing tests)
pytest -v -rs

# Run test coverage audit
pytest --cov=src --cov-report=term-missing

# Run end-to-end Playwright browser tests (14 UI test cases)
python scripts/verify_ui_browser.py

# Verify README metrics against source-of-truth metadata
python scripts/verify_readme_metrics.py
```

---

## 📦 Deployment to Render

The repository includes a ready-to-use [`render.yaml`](render.yaml) blueprint:
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
- **Health Check Path**: `/api/health`

For complete step-by-step instructions, see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

---

## 📜 Dataset & License

- **Dataset**: [Enron Spam Dataset](https://github.com/MWiechmann/enron_spam_data) (MWiechmann) licensed under the **GNU General Public License v3.0**.
- **Code License**: Subject to user selection (MIT, Apache-2.0, or GPL-3.0). See Phase 9 report for details.
