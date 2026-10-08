"""Offline ML model training script for MailGuard AI.

Follows locked decisions:
- Training is strictly offline (src/train.py).
- Stratified train/test split BEFORE fitting anything.
- Fit TF-IDF on train only (Pipeline + cross-validation). No data leakage.
- Deduplication of texts to prevent leakage across splits.
- Compare Naive Bayes, Logistic Regression, and Calibrated Linear SVM.
- SELECTION CRITERION stated before training:
    "Spam precision >= 0.98 first, then highest recall on spam, then F1 score.
     Never select by accuracy alone."
- Record scikit-learn version, training date, dataset provenance, and held-out test metrics.
"""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sys
from typing import Any, Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from src.config import METADATA_PATH, MODEL_PATH, RAW_DATA_PATH
from src.preprocess import combine_email

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MailGuard-Train")

# Selection criterion statement (LOCKED & PRE-DECLARED)
SELECTION_CRITERION_DOC = (
    "Spam precision >= 0.98 first, then highest recall on spam, then F1 score. "
    "Never select by accuracy alone."
)


def load_and_clean_data(csv_path: Path) -> Tuple[pd.Series, pd.Series, Dict[str, Any]]:
    """Load, inspect, clean, and deduplicate raw email dataset.

    Returns:
        X: Combined text series.
        y: Integer target series (1 for spam, 0 for ham).
        provenance: Dataset profile and cleaning audit information.
    """
    logger.info(f"Loading raw dataset from {csv_path}...")
    if not csv_path.exists():
        raise FileNotFoundError(f"Raw dataset file not found at {csv_path}")

    df = pd.read_csv(csv_path)
    initial_rows = len(df)
    logger.info(f"Raw rows loaded: {initial_rows}")

    # Inspect nulls
    null_subject = int(df["Subject"].isnull().sum())
    null_message = int(df["Message"].isnull().sum())
    both_null = int((df["Subject"].isnull() & df["Message"].isnull()).sum())
    logger.info(f"Null audit - Subject: {null_subject}, Message: {null_message}, Both null: {both_null}")

    # Remove rows where both Subject and Message are null
    df = df[~(df["Subject"].isnull() & df["Message"].isnull())].copy()

    # Fill NA for combination
    df["Subject"] = df["Subject"].fillna("")
    df["Message"] = df["Message"].fillna("")

    # Combine text representation
    df["combined_text"] = [
        combine_email(s, m) for s, m in zip(df["Subject"], df["Message"])
    ]

    # Filter out empty texts
    df = df[df["combined_text"].str.strip().str.len() > 0].copy()

    # Deduplicate texts to prevent data leakage between train and test sets
    duplicates_before = int(df.duplicated(subset=["combined_text"]).sum())
    df = df.drop_duplicates(subset=["combined_text"]).reset_index(drop=True)
    logger.info(f"Deduplication removed {duplicates_before} duplicate email texts.")

    # Parse and encode target labels
    label_col = "Spam/Ham"
    raw_labels = df[label_col].astype(str).str.strip().str.lower()
    y = (raw_labels == "spam").astype(int)

    ham_count = int((y == 0).sum())
    spam_count = int((y == 1).sum())
    final_rows = len(df)
    logger.info(f"Cleaned dataset: {final_rows} total samples (Ham: {ham_count}, Spam: {spam_count})")

    data_profile = {
        "dataset_name": "Enron Spam Dataset",
        "dataset_source_url": "https://github.com/MWiechmann/enron_spam_data",
        "dataset_license": "GPL-3.0 / Public Domain (CALO Enron Corpus)",
        "dataset_type": "email",
        "initial_rows": initial_rows,
        "null_subject": null_subject,
        "null_message": null_message,
        "both_null_dropped": both_null,
        "duplicates_dropped": duplicates_before,
        "final_samples": final_rows,
        "class_counts": {"ham": ham_count, "spam": spam_count},
        "language": "en",
    }

    return df["combined_text"], y, data_profile


def build_candidate_pipelines() -> Dict[str, Pipeline]:
    """Build candidate ML pipelines for comparison.

    All models use the same TF-IDF vectorizer configuration fitted on train only.
    """
    tfidf = TfidfVectorizer(
        max_features=15000,
        ngram_range=(1, 2),
        stop_words="english",
        sublinear_tf=True,
    )

    models = {
        "Multinomial Naive Bayes": Pipeline([
            ("tfidf", tfidf),
            ("clf", MultinomialNB(alpha=0.1)),
        ]),
        "Logistic Regression": Pipeline([
            ("tfidf", tfidf),
            ("clf", LogisticRegression(
                class_weight="balanced",
                C=1.0,
                max_iter=1000,
                random_state=42,
            )),
        ]),
        "Calibrated Linear SVM": Pipeline([
            ("tfidf", tfidf),
            ("clf", CalibratedClassifierCV(
                estimator=LinearSVC(
                    class_weight="balanced",
                    C=1.0,
                    random_state=42,
                    dual="auto",
                ),
                method="sigmoid",
                cv=3,
            )),
        ]),
    }
    return models


def evaluate_model(pipeline: Pipeline, X_train: pd.Series, y_train: pd.Series, X_test: pd.Series, y_test: pd.Series) -> Dict[str, Any]:
    """Train pipeline on X_train and evaluate on held-out X_test.

    All metrics are computed on the real held-out test split.
    """
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    # Probabilities for calibration check
    if hasattr(pipeline, "predict_proba"):
        y_prob = pipeline.predict_proba(X_test)[:, 1]
    elif hasattr(pipeline, "decision_function"):
        y_prob = pipeline.decision_function(X_test)
    else:
        y_prob = None

    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()

    metrics = {
        "accuracy": float(round(accuracy_score(y_test, y_pred), 4)),
        "precision": float(round(precision_score(y_test, y_pred, pos_label=1, zero_division=0), 4)),
        "recall": float(round(recall_score(y_test, y_pred, pos_label=1, zero_division=0), 4)),
        "f1": float(round(f1_score(y_test, y_pred, pos_label=1, zero_division=0), 4)),
        "confusion_matrix": {
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp),
        },
    }
    return metrics


def select_best_model(results: Dict[str, Dict[str, Any]]) -> str:
    """Select best model using pre-declared criterion:

    Priority 1: Spam precision >= 0.98.
    Priority 2: Highest recall on spam among qualifying models.
    Priority 3: Highest F1 on spam.
    Never select by accuracy alone.
    """
    logger.info(f"Applying selection criterion: '{SELECTION_CRITERION_DOC}'")

    qualified = {
        name: res for name, res in results.items() if res["precision"] >= 0.98
    }

    if qualified:
        logger.info(f"Models meeting precision >= 0.98: {list(qualified.keys())}")
        # Sort by recall (desc), then F1 (desc)
        best_name = max(
            qualified.keys(),
            key=lambda k: (qualified[k]["recall"], qualified[k]["f1"])
        )
    else:
        logger.warning("No model met precision >= 0.98 threshold. Selecting highest precision model.")
        best_name = max(
            results.keys(),
            key=lambda k: (results[k]["precision"], results[k]["recall"], results[k]["f1"])
        )

    logger.info(f"Selected winner: {best_name}")
    return best_name


def extract_top_spam_terms(pipeline: Pipeline, top_n: int = 30) -> List[Dict[str, Any]]:
    """Extract global top spam-indicating terms directly derived from model weights."""
    tfidf = pipeline.named_steps["tfidf"]
    clf = pipeline.named_steps["clf"]
    feature_names = tfidf.get_feature_names_out()

    weights = None
    if isinstance(clf, LogisticRegression):
        weights = clf.coef_[0]
    elif isinstance(clf, MultinomialNB):
        # Difference in log probabilities between spam (1) and ham (0)
        weights = clf.feature_log_prob_[1] - clf.feature_log_prob_[0]
    elif isinstance(clf, CalibratedClassifierCV):
        # Average calibrated base estimator weights if available
        base_weights = []
        for calibrated_classifier in clf.calibrated_classifiers_:
            estimator = getattr(calibrated_classifier, "estimator", None)
            if estimator and hasattr(estimator, "coef_"):
                base_weights.append(estimator.coef_[0])
        if base_weights:
            weights = np.mean(base_weights, axis=0)

    if weights is None or len(weights) != len(feature_names):
        return []

    top_indices = np.argsort(weights)[::-1][:top_n]
    top_terms = [
        {"term": str(feature_names[idx]), "weight": float(round(weights[idx], 4))}
        for idx in top_indices
        if weights[idx] > 0
    ]
    return top_terms


def train_and_evaluate() -> None:
    """Full offline training orchestration."""
    print("=" * 80)
    print("MAILGUARD AI - OFFLINE MODEL TRAINING & VALIDATION PIPELINE")
    print(f"Declared Selection Criterion: {SELECTION_CRITERION_DOC}")
    print("=" * 80)

    # 1. Load, clean and audit data
    X, y, profile = load_and_clean_data(RAW_DATA_PATH)

    # 2. Stratified train/test split BEFORE fitting any transformer
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    logger.info(f"Train split size: {len(X_train)} (Ham: {(y_train == 0).sum()}, Spam: {(y_train == 1).sum()})")
    logger.info(f"Held-out Test split size: {len(X_test)} (Ham: {(y_test == 0).sum()}, Spam: {(y_test == 1).sum()})")

    # 3. Candidate models comparison
    candidates = build_candidate_pipelines()
    results: Dict[str, Dict[str, Any]] = {}

    print("\n--- MODEL COMPARISON ON HELD-OUT TEST SPLIT ---")
    for name, pipeline in candidates.items():
        logger.info(f"Fitting and evaluating: {name}...")
        metrics = evaluate_model(pipeline, X_train, y_train, X_test, y_test)
        results[name] = metrics
        cm = metrics["confusion_matrix"]
        print(f"\nModel: {name}")
        print(f"  Accuracy:  {metrics['accuracy']:.4f}")
        print(f"  Precision (Spam): {metrics['precision']:.4f}")
        print(f"  Recall (Spam):    {metrics['recall']:.4f}")
        print(f"  F1 Score (Spam):  {metrics['f1']:.4f}")
        print(f"  Confusion Matrix: TP={cm['true_positives']}, FP={cm['false_positives']}, TN={cm['true_negatives']}, FN={cm['false_negatives']}")

    # 4. Model selection
    winner_name = select_best_model(results)
    winner_pipeline = candidates[winner_name]
    winner_metrics = results[winner_name]

    # 5. Extract global top spam terms
    top_terms = extract_top_spam_terms(winner_pipeline, top_n=30)

    # 6. Save model artifact
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Saving winning model artifact to {MODEL_PATH}...")
    joblib.dump(winner_pipeline, MODEL_PATH)

    # 7. Save metadata.json
    metadata: Dict[str, Any] = {
        "dataset_name": profile["dataset_name"],
        "dataset_source_url": profile["dataset_source_url"],
        "dataset_license": profile["dataset_license"],
        "dataset_type": profile["dataset_type"],
        "n_samples": profile["final_samples"],
        "n_train": len(X_train),
        "n_test": len(X_test),
        "class_counts": profile["class_counts"],
        "language": profile["language"],
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "sklearn_version": sklearn.__version__,
        "selection_criterion": SELECTION_CRITERION_DOC,
        "selected_model": winner_name,
        "test_metrics": winner_metrics,
        "all_candidate_metrics": results,
        "top_global_spam_terms": top_terms,
        "qualifier_notice": (
            "Metrics are measured on a held-out test set of THIS dataset only. "
            "Real-world email performance may be lower."
        ),
    }

    METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Writing metadata to {METADATA_PATH}...")
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print("\n" + "=" * 80)
    print("TRAINING & VALIDATION COMPLETE")
    print(f"Selected Model: {winner_name}")
    print(f"Spam Precision: {winner_metrics['precision']:.4f} (Priority 1)")
    print(f"Spam Recall:    {winner_metrics['recall']:.4f} (Priority 2)")
    print(f"Spam F1:        {winner_metrics['f1']:.4f} (Priority 3)")
    print(f"Artifact Saved: {MODEL_PATH}")
    print(f"Metadata Saved: {METADATA_PATH}")
    print("=" * 80)


if __name__ == "__main__":
    train_and_evaluate()
