"""Model Card Artifact & Visual Asset Builder for MailGuard AI v2.

Computes exact evaluation metrics on the held-out test set:
- Confusion Matrix (TP, FP, TN, FN)
- Precision, Recall, F1, Accuracy with 1,000-sample bootstrap 95% Confidence Intervals
- Precision-Recall Curve points and PR-AUC
- Calibration Curve (reliability diagram) via Platt scaling vs perfect diagonal
- De-duplication summary and provenance statistics

Outputs:
- reports/model_card_data.json (structured metrics, CIs, and SVG XML strings)
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple
import json
import math
import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import RAW_DATA_PATH, REPORTS_DIR
from src.train import load_and_clean_data


def generate_confusion_matrix_svg(tn: int, fp: int, fn: int, tp: int) -> str:
    """Generate inline SVG for the 2x2 confusion matrix."""
    total_ham = tn + fp
    total_spam = fn + tp
    tn_pct = (tn / total_ham) * 100
    fp_pct = (fp / total_ham) * 100
    fn_pct = (fn / total_spam) * 100
    tp_pct = (tp / total_spam) * 100

    return f'''<svg class="model-card-chart-svg" viewBox="0 0 420 300" width="100%" role="img" aria-label="Holdout Test Set Confusion Matrix">
  <!-- Title / Headers -->
  <text x="250" y="22" class="cm-title">Predicted Verdict</text>
  <text x="180" y="44" class="cm-axis">Pred Safe (Ham)</text>
  <text x="320" y="44" class="cm-axis">Pred Spam</text>

  <!-- Y-Axis Label (Rotated) -->
  <text x="-165" y="24" transform="rotate(-90)" class="cm-title">Actual Class (Ground Truth)</text>
  <text x="75" y="115" class="cm-axis">True Safe</text>
  <text x="75" y="130" class="cm-axis cm-sub-count">({total_ham:,})</text>
  <text x="75" y="205" class="cm-axis">True Spam</text>
  <text x="75" y="220" class="cm-axis cm-sub-count">({total_spam:,})</text>

  <!-- Cell 1: True Negative (Top-Left) -->
  <g transform="translate(115, 60)">
    <rect width="130" height="90" class="cm-cell-bg" fill="#15803d" fill-opacity="0.22" stroke="#15803d" stroke-width="1.5" rx="6" ry="6"/>
    <text x="65" y="42" class="cm-val" fill="#15803d">{tn:,}</text>
    <text x="65" y="62" class="cm-sub" fill="#15803d">True Negative ({tn_pct:.1f}%)</text>
    <text x="65" y="78" class="cm-desc">Correct Ham</text>
  </g>

  <!-- Cell 2: False Positive (Top-Right) -->
  <g transform="translate(255, 60)">
    <rect width="130" height="90" class="cm-cell-bg" fill="#b45309" fill-opacity="0.18" stroke="#b45309" stroke-width="1.5" rx="6" ry="6"/>
    <text x="65" y="42" class="cm-val" fill="#b45309">{fp:,}</text>
    <text x="65" y="62" class="cm-sub" fill="#b45309">False Positive ({fp_pct:.1f}%)</text>
    <text x="65" y="78" class="cm-desc">Ham flagged as Spam</text>
  </g>

  <!-- Cell 3: False Negative (Bottom-Left) -->
  <g transform="translate(115, 160)">
    <rect width="130" height="90" class="cm-cell-bg" fill="#b91c1c" fill-opacity="0.18" stroke="#b91c1c" stroke-width="1.5" rx="6" ry="6"/>
    <text x="65" y="42" class="cm-val" fill="#b91c1c">{fn:,}</text>
    <text x="65" y="62" class="cm-sub" fill="#b91c1c">False Negative ({fn_pct:.1f}%)</text>
    <text x="65" y="78" class="cm-desc">Spam missed as Ham</text>
  </g>

  <!-- Cell 4: True Positive (Bottom-Right) -->
  <g transform="translate(255, 160)">
    <rect width="130" height="90" class="cm-cell-bg" fill="#8b1e3f" fill-opacity="0.22" stroke="#8b1e3f" stroke-width="1.5" rx="6" ry="6"/>
    <text x="65" y="42" class="cm-val" fill="#8b1e3f">{tp:,}</text>
    <text x="65" y="62" class="cm-sub" fill="#8b1e3f">True Positive ({tp_pct:.1f}%)</text>
    <text x="65" y="78" class="cm-desc">Spam detected</text>
  </g>

  <!-- Bottom Legend / Note -->
  <text x="210" y="280" class="cm-note">
    Total Held-Out Test Samples: {tn + fp + fn + tp:,} | Accuracy: {(tn + tp) / (tn + fp + fn + tp) * 100:.2f}%
  </text>
</svg>'''


def generate_pr_curve_svg(precisions: np.ndarray, recalls: np.ndarray, pr_auc: float, baseline_rate: float) -> str:
    """Generate inline SVG for the Precision-Recall curve."""
    ox, oy = 55, 30
    w, h = 330, 185

    # Sample points along curve for a smooth SVG path
    n_points = 50
    indices = np.linspace(0, len(recalls) - 1, n_points, dtype=int)
    path_cmds = []

    for idx in indices:
        r = float(recalls[idx])
        p = float(precisions[idx])
        px = ox + (r * w)
        py = oy + ((1.0 - p) * h)
        if not path_cmds:
            path_cmds.append(f"M {px:.1f} {py:.1f}")
        else:
            path_cmds.append(f"L {px:.1f} {py:.1f}")

    path_data = " ".join(path_cmds)
    baseline_y = oy + ((1.0 - baseline_rate) * h)

    return f'''<svg class="model-card-chart-svg" viewBox="0 0 420 280" width="100%" role="img" aria-label="Precision-Recall Curve">
  <!-- Horizontal gridlines -->
  <line x1="{ox}" y1="{oy}" x2="{ox + w}" y2="{oy}" class="pr-grid"/>
  <text x="{ox - 8}" y="{oy + 4}" class="pr-axis" text-anchor="end">1.0</text>

  <line x1="{ox}" y1="{oy + h * 0.25}" x2="{ox + w}" y2="{oy + h * 0.25}" class="pr-grid"/>
  <text x="{ox - 8}" y="{oy + h * 0.25 + 4}" class="pr-axis" text-anchor="end">0.75</text>

  <line x1="{ox}" y1="{oy + h * 0.5}" x2="{ox + w}" y2="{oy + h * 0.5}" class="pr-grid"/>
  <text x="{ox - 8}" y="{oy + h * 0.5 + 4}" class="pr-axis" text-anchor="end">0.50</text>

  <line x1="{ox}" y1="{oy + h * 0.75}" x2="{ox + w}" y2="{oy + h * 0.75}" class="pr-grid"/>
  <text x="{ox - 8}" y="{oy + h * 0.75 + 4}" class="pr-axis" text-anchor="end">0.25</text>

  <line x1="{ox}" y1="{oy + h}" x2="{ox + w}" y2="{oy + h}" class="pr-grid"/>
  <text x="{ox - 8}" y="{oy + h + 4}" class="pr-axis" text-anchor="end">0.0</text>

  <!-- Vertical gridlines -->
  <line x1="{ox}" y1="{oy}" x2="{ox}" y2="{oy + h}" class="pr-grid"/>
  <text x="{ox}" y="{oy + h + 16}" class="pr-axis" text-anchor="middle">0.0</text>

  <line x1="{ox + w * 0.25}" y1="{oy}" x2="{ox + w * 0.25}" y2="{oy + h}" class="pr-grid"/>
  <text x="{ox + w * 0.25}" y="{oy + h + 16}" class="pr-axis" text-anchor="middle">0.25</text>

  <line x1="{ox + w * 0.5}" y1="{oy}" x2="{ox + w * 0.5}" y2="{oy + h}" class="pr-grid"/>
  <text x="{ox + w * 0.5}" y="{oy + h + 16}" class="pr-axis" text-anchor="middle">0.50</text>

  <line x1="{ox + w * 0.75}" y1="{oy}" x2="{ox + w * 0.75}" y2="{oy + h}" class="pr-grid"/>
  <text x="{ox + w * 0.75}" y="{oy + h + 16}" class="pr-axis" text-anchor="middle">0.75</text>

  <line x1="{ox + w}" y1="{oy}" x2="{ox + w}" y2="{oy + h}" class="pr-grid"/>
  <text x="{ox + w}" y="{oy + h + 16}" class="pr-axis" text-anchor="middle">1.0</text>

  <!-- Baseline (Random Guess / Class Balance) -->
  <line x1="{ox}" y1="{baseline_y:.1f}" x2="{ox + w}" y2="{baseline_y:.1f}" class="pr-baseline"/>

  <!-- PR Curve Path -->
  <path d="{path_data}" class="pr-line"/>

  <!-- Area under curve shading -->
  <path d="{path_data} L {ox + w} {oy + h} L {ox} {oy + h} Z" class="pr-area"/>

  <!-- Axis Titles -->
  <text x="{ox + w / 2}" y="{oy + h + 34}" class="pr-title" text-anchor="middle">Recall (Sensitivity)</text>
  <text x="-{(oy + h / 2):.1f}" y="16" transform="rotate(-90)" class="pr-title" text-anchor="middle">Precision (Positive Predictive Value)</text>

  <!-- Metrics Callout Badge -->
  <g transform="translate({ox + 15}, {oy + h - 55})">
    <rect width="155" height="42" class="pr-badge-box" rx="4" ry="4"/>
    <text x="10" y="18" class="pr-badge-title">PR-AUC: {pr_auc:.4f}</text>
    <text x="10" y="32" class="pr-badge-sub">Baseline (Spam prev): {baseline_rate * 100:.1f}%</text>
  </g>
</svg>'''


def generate_calibration_curve_svg(prob_pred: List[float], prob_true: List[float]) -> str:
    """Generate inline SVG for the Platt Scaling Calibration Reliability curve."""
    ox, oy = 55, 30
    w, h = 330, 185

    # Compute plotted points
    points_svg = []
    path_cmds = []

    for pp, pt in zip(prob_pred, prob_true):
        px = ox + (pp * w)
        py = oy + ((1.0 - pt) * h)
        path_cmds.append(f"{'M' if not path_cmds else 'L'} {px:.1f} {py:.1f}")
        points_svg.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4" class="cal-dot"/>')

    line_path = " ".join(path_cmds)
    points_markup = "\n  ".join(points_svg)

    return f'''<svg class="model-card-chart-svg" viewBox="0 0 420 280" width="100%" role="img" aria-label="Platt Calibration Reliability Diagram">
  <!-- Horizontal gridlines -->
  <line x1="{ox}" y1="{oy}" x2="{ox + w}" y2="{oy}" class="cal-grid"/>
  <text x="{ox - 8}" y="{oy + 4}" class="cal-axis" text-anchor="end">1.0</text>

  <line x1="{ox}" y1="{oy + h * 0.25}" x2="{ox + w}" y2="{oy + h * 0.25}" class="cal-grid"/>
  <text x="{ox - 8}" y="{oy + h * 0.25 + 4}" class="cal-axis" text-anchor="end">0.75</text>

  <line x1="{ox}" y1="{oy + h * 0.5}" x2="{ox + w}" y2="{oy + h * 0.5}" class="cal-grid"/>
  <text x="{ox - 8}" y="{oy + h * 0.5 + 4}" class="cal-axis" text-anchor="end">0.50</text>

  <line x1="{ox}" y1="{oy + h * 0.75}" x2="{ox + w}" y2="{oy + h * 0.75}" class="cal-grid"/>
  <text x="{ox - 8}" y="{oy + h * 0.75 + 4}" class="cal-axis" text-anchor="end">0.25</text>

  <line x1="{ox}" y1="{oy + h}" x2="{ox + w}" y2="{oy + h}" class="cal-grid"/>
  <text x="{ox - 8}" y="{oy + h + 4}" class="cal-axis" text-anchor="end">0.0</text>

  <!-- Vertical gridlines -->
  <line x1="{ox}" y1="{oy}" x2="{ox}" y2="{oy + h}" class="cal-grid"/>
  <text x="{ox}" y="{oy + h + 16}" class="cal-axis" text-anchor="middle">0.0</text>

  <line x1="{ox + w * 0.25}" y1="{oy}" x2="{ox + w * 0.25}" y2="{oy + h}" class="cal-grid"/>
  <text x="{ox + w * 0.25}" y="{oy + h + 16}" class="cal-axis" text-anchor="middle">0.25</text>

  <line x1="{ox + w * 0.5}" y1="{oy}" x2="{ox + w * 0.5}" y2="{oy + h}" class="cal-grid"/>
  <text x="{ox + w * 0.5}" y="{oy + h + 16}" class="cal-axis" text-anchor="middle">0.50</text>

  <line x1="{ox + w * 0.75}" y1="{oy}" x2="{ox + w * 0.75}" y2="{oy + h}" class="cal-grid"/>
  <text x="{ox + w * 0.75}" y="{oy + h + 16}" class="cal-axis" text-anchor="middle">0.75</text>

  <line x1="{ox + w}" y1="{oy}" x2="{ox + w}" y2="{oy + h}" class="cal-grid"/>
  <text x="{ox + w}" y="{oy + h + 16}" class="cal-axis" text-anchor="middle">1.0</text>

  <!-- Perfect Calibration Reference (Diagonal Line y = x) -->
  <line x1="{ox}" y1="{oy + h}" x2="{ox + w}" y2="{oy}" class="cal-ideal"/>

  <!-- Model Calibration Line & Points -->
  <path d="{line_path}" class="cal-line"/>
  {points_markup}

  <!-- Axis Titles -->
  <text x="{ox + w / 2}" y="{oy + h + 34}" class="cal-title" text-anchor="middle">Mean Predicted Spam Probability</text>
  <text x="-{(oy + h / 2):.1f}" y="16" transform="rotate(-90)" class="cal-title" text-anchor="middle">Observed Fraction of Spam (Positives)</text>

  <!-- Legend -->
  <g transform="translate({ox + 15}, {oy + 12})">
    <rect width="165" height="38" class="cal-badge" rx="4" ry="4"/>
    <text x="8" y="16" class="cal-badge-title">Calibrated Linear SVM</text>
    <text x="8" y="29" class="cal-badge-sub">--- Ideal Calibration (y = x)</text>
  </g>
</svg>'''


def build_model_card_assets():
    """Compute metrics from real held-out test set and export SVGs & metadata."""
    print("=" * 80)
    print("BUILDING MODEL CARD ASSETS & EVALUATION METRICS (TEST SET)")
    print("=" * 80)

    # 1. Load data
    X, y, profile = load_and_clean_data(RAW_DATA_PATH)
    total_raw = profile.get("raw_count", 33665)
    total_cleaned = profile.get("cleaned_count", 30462)
    dedup_dropped = profile.get("dropped_duplicate_count", 3203)

    # 2. Stratified split (80/20, seed=42)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    # 3. Load model artifact
    model_path = Path("models/spam_pipeline.joblib")
    if not model_path.exists():
        raise FileNotFoundError(f"Missing model artifact: {model_path}")

    pipeline = joblib.load(model_path)
    y_proba = pipeline.predict_proba(X_test)[:, 1]
    y_pred = (y_proba >= 0.50).astype(int)

    # 4. Compute Test Metrics
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()

    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred, zero_division=0))
    rec = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))

    pr_auc = float(average_precision_score(y_test, y_proba))
    precisions, recalls, _ = precision_recall_curve(y_test, y_proba)
    baseline_rate = float(np.sum(y_test) / len(y_test))

    # Calibration Curve (10 bins)
    prob_true, prob_pred = calibration_curve(y_test, y_proba, n_bins=10, strategy="uniform")
    prob_true_list = [float(round(x, 4)) for x in prob_true]
    prob_pred_list = [float(round(x, 4)) for x in prob_pred]

    # 5. Bootstrap 95% Confidence Intervals (1000 resamples)
    print("Computing 1,000 bootstrap resamples for 95% confidence intervals...")
    rng = np.random.default_rng(42)
    n_boot = 1000
    boot_acc, boot_prec, boot_rec, boot_f1 = [], [], [], []
    n_samples = len(y_test)
    y_test_arr = np.array(y_test)

    for _ in range(n_boot):
        idx = rng.choice(n_samples, size=n_samples, replace=True)
        b_true = y_test_arr[idx]
        b_pred = y_pred[idx]
        boot_acc.append(accuracy_score(b_true, b_pred))
        boot_prec.append(precision_score(b_true, b_pred, zero_division=0))
        boot_rec.append(recall_score(b_true, b_pred, zero_division=0))
        boot_f1.append(f1_score(b_true, b_pred, zero_division=0))

    ci_acc = [float(round(np.percentile(boot_acc, 2.5), 4)), float(round(np.percentile(boot_acc, 97.5), 4))]
    ci_prec = [float(round(np.percentile(boot_prec, 2.5), 4)), float(round(np.percentile(boot_prec, 97.5), 4))]
    ci_rec = [float(round(np.percentile(boot_rec, 2.5), 4)), float(round(np.percentile(boot_rec, 97.5), 4))]
    ci_f1 = [float(round(np.percentile(boot_f1, 2.5), 4)), float(round(np.percentile(boot_f1, 97.5), 4))]

    # 6. Generate SVGs
    cm_svg = generate_confusion_matrix_svg(int(tn), int(fp), int(fn), int(tp))
    pr_svg = generate_pr_curve_svg(precisions, recalls, pr_auc, baseline_rate)
    cal_svg = generate_calibration_curve_svg(prob_pred_list, prob_true_list)

    # 7. Compile Model Card Data Structure
    model_card_data = {
        "metadata": {
            "model_name": "MailGuard AI - Calibrated Linear SVM",
            "model_architecture": "LinearSVC + CalibratedClassifierCV (Platt Scaling, 5-Fold)",
            "vectorizer": "TF-IDF (15,000 features, 1-2 n-grams, sublinear TF scaling)",
            "dataset_name": "Enron Spam Dataset",
            "dataset_provenance": "https://github.com/MWiechmann/enron_spam_data",
            "code_license": "MIT License",
            "dataset_license": "GNU General Public License v3.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "dataset_deduplication": {
            "raw_total_samples": total_raw,
            "deduplicated_removed": dedup_dropped,
            "cleaned_total_samples": total_cleaned,
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "class_distribution_overall": {
                "ham": int(np.sum(y == 0)),
                "spam": int(np.sum(y == 1)),
            },
            "class_distribution_test": {
                "ham": int(np.sum(y_test == 0)),
                "spam": int(np.sum(y_test == 1)),
            },
        },
        "evaluation_metrics": {
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "pr_auc": round(pr_auc, 4),
            "confusion_matrix": {
                "tn": int(tn),
                "fp": int(fp),
                "fn": int(fn),
                "tp": int(tp),
            },
        },
        "bootstrap_95_ci": {
            "accuracy": ci_acc,
            "precision": ci_prec,
            "recall": ci_rec,
            "f1": ci_f1,
            "resamples": n_boot,
        },
        "calibration": {
            "mean_predicted_probabilities": prob_pred_list,
            "observed_positive_fractions": prob_true_list,
        },
        "disclaimer_scope": (
            "MailGuard AI is an NLP statistical classifier designed exclusively to identify unsolicited "
            "spam and email fraud patterns. It DOES NOT detect malicious software, executable zero-days, "
            "ransomware binaries, or operating system-level malware."
        ),
        "known_failure_modes": [
            "Historical lexical bias: Enron corpus reflects early-2000s corporate language; novel modern fraud terminology may have lower vocabulary coverage.",
            "English text orientation: Accent-stripping NFKD normalization decomposes Latin diacritics; non-English scripts are flagged for human review.",
            "Short message ambiguity: Ultra-short inputs (< 10 words) provide sparse n-gram statistics and trigger borderline uncertainty.",
            "Adversarial obfuscation: Deliberate spaced typos ('c a s h') or zero-width character insertions may evade TF-IDF tokenization unless pre-cleaned.",
        ],
        "svgs": {
            "confusion_matrix": cm_svg,
            "pr_curve": pr_svg,
            "calibration_curve": cal_svg,
        },
    }

    output_path = REPORTS_DIR / "model_card_data.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(model_card_data, f, indent=2)

    print(f"Model Card data and SVGs saved to: {output_path}")
    print(f"  Accuracy:  {acc * 100:.2f}% (95% CI: [{ci_acc[0] * 100:.2f}%, {ci_acc[1] * 100:.2f}%])")
    print(f"  Precision: {prec * 100:.2f}% (95% CI: [{ci_prec[0] * 100:.2f}%, {ci_prec[1] * 100:.2f}%])")
    print(f"  Recall:    {rec * 100:.2f}% (95% CI: [{ci_rec[0] * 100:.2f}%, {ci_rec[1] * 100:.2f}%])")
    print(f"  F1 Score:  {f1 * 100:.2f}% (95% CI: [{ci_f1[0] * 100:.2f}%, {ci_f1[1] * 100:.2f}%])")
    print(f"  PR-AUC:    {pr_auc:.4f}")
    print(f"  Confusion Matrix: TN={tn}, FP={fp}, FN={fn}, TP={tp}")
    return model_card_data


if __name__ == "__main__":
    build_model_card_assets()
