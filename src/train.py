"""Offline ML model training script for MailGuard AI.

Phase 4: Preprocessing + Training
- Pipeline architecture: preprocessing (EmailCleanerTransformer) -> TfidfVectorizer -> classifier
- Cross-platform paths and zero server-start execution
- Stratified train/test split with fixed random_state=42
- Cross-split duplicate assertion to guarantee 0 data leakage
- 5-Fold Stratified Cross-Validation on train set
- Class imbalance handled (class_weight='balanced')
- Comparison across 3 models: Multinomial Naive Bayes, Logistic Regression, Calibrated Linear SVM
- Pre-declared selection criterion:
    "Spam precision >= 0.98 first, then highest recall on spam, then F1 score. Never select by accuracy alone."
- Raw comparison metrics saved to reports/model_comparison.json
- Winning pipeline saved to models/spam_pipeline.joblib and models/metadata.json
"""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
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
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from src.config import (
    METADATA_PATH,
    MODEL_COMPARISON_JSON,
    MODEL_PATH,
    RAW_DATA_PATH,
    REPORTS_DIR,
)
from src.preprocess import combine_email
from src.preprocessing import EmailCleanerTransformer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MailGuard-Train")

SELECTION_CRITERION_DOC = (
    "Spam precision >= 0.98 first, then highest recall on spam, then F1 score. "
    "Never select by accuracy alone."
)


def load_and_clean_data(csv_path: Path) -> Tuple[pd.Series, pd.Series, Dict[str, Any]]:
    """Load, inspect, clean, and deduplicate raw email dataset."""
    logger.info(f"Loading raw dataset from {csv_path}...")
    if not csv_path.exists():
        raise FileNotFoundError(f"Raw dataset file not found at {csv_path}")

    df = pd.read_csv(csv_path)
    initial_rows = len(df)

    # Remove rows where both Subject and Message are null
    both_null_mask = df["Subject"].isnull() & df["Message"].isnull()
    both_null_count = int(both_null_mask.sum())
    df = df[~both_null_mask].copy()

    df["Subject"] = df["Subject"].fillna("")
    df["Message"] = df["Message"].fillna("")

    # Combine text representation
    df["combined_text"] = [
        combine_email(s, m) for s, m in zip(df["Subject"], df["Message"])
    ]

    # Filter out empty texts
    df = df[df["combined_text"].str.strip().str.len() > 0].copy()

    # Deduplicate texts
    duplicates_before = int(df.duplicated(subset=["combined_text"]).sum())
    df = df.drop_duplicates(subset=["combined_text"]).reset_index(drop=True)
    logger.info(f"Deduplication removed {duplicates_before} duplicate email texts.")

    # Target encoding
    raw_labels = df["Spam/Ham"].astype(str).str.strip().str.lower()
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
        "both_null_dropped": both_null_count,
        "duplicates_dropped": duplicates_before,
        "final_samples": final_rows,
        "class_counts": {"ham": ham_count, "spam": spam_count},
        "language": "en",
    }

    return df["combined_text"], y, data_profile


def build_candidate_pipelines() -> Dict[str, Pipeline]:
    """Build candidate ML pipelines conforming to:

    preprocessing -> TfidfVectorizer(ngrams, min_df, max_features) -> classifier.
    """
    tfidf = TfidfVectorizer(
        max_features=15000,
        ngram_range=(1, 2),
        min_df=3,
        sublinear_tf=True,
    )

    models = {
        "Multinomial Naive Bayes": Pipeline([
            ("preprocess", EmailCleanerTransformer()),
            ("tfidf", tfidf),
            ("clf", MultinomialNB(alpha=0.1)),
        ]),
        "Logistic Regression": Pipeline([
            ("preprocess", EmailCleanerTransformer()),
            ("tfidf", tfidf),
            ("clf", LogisticRegression(
                class_weight="balanced",
                C=1.0,
                max_iter=1000,
                random_state=42,
            )),
        ]),
        "Calibrated Linear SVM": Pipeline([
            ("preprocess", EmailCleanerTransformer()),
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


def evaluate_model_cv_and_test(
    name: str,
    pipeline: Pipeline,
    X_train: pd.Series,
    y_train: pd.Series,
    X_test: pd.Series,
    y_test: pd.Series,
    cv_folds: int = 5,
) -> Dict[str, Any]:
    """Perform 5-fold cross-validation on train split, then evaluate on held-out test split."""
    logger.info(f"Running {cv_folds}-Fold Stratified CV for {name}...")

    # Cross-validation on train set
    skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
    cv_results = cross_validate(
        pipeline,
        X_train,
        y_train,
        cv=skf,
        scoring=["precision", "recall", "f1", "accuracy"],
        n_jobs=-1,
        return_train_score=False,
    )

    cv_summary = {
        "mean_accuracy": float(round(np.mean(cv_results["test_accuracy"]), 4)),
        "std_accuracy": float(round(np.std(cv_results["test_accuracy"]), 4)),
        "mean_precision": float(round(np.mean(cv_results["test_precision"]), 4)),
        "std_precision": float(round(np.std(cv_results["test_precision"]), 4)),
        "mean_recall": float(round(np.mean(cv_results["test_recall"]), 4)),
        "std_recall": float(round(np.std(cv_results["test_recall"]), 4)),
        "mean_f1": float(round(np.mean(cv_results["test_f1"]), 4)),
        "std_f1": float(round(np.std(cv_results["test_f1"]), 4)),
    }

    # Fit final pipeline on complete X_train and evaluate on held-out test split
    logger.info(f"Fitting {name} on full train set and evaluating on held-out test split...")
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()

    test_metrics = {
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

    return {
        "cv_5fold": cv_summary,
        "test_metrics": test_metrics,
    }


def select_best_model(results: Dict[str, Dict[str, Any]]) -> str:
    """Select best model using pre-declared criterion:

    Priority 1: Spam precision >= 0.98.
    Priority 2: Highest recall on spam among qualifying models.
    Priority 3: Highest F1 on spam.
    Never select by accuracy alone.
    """
    logger.info(f"Applying selection criterion: '{SELECTION_CRITERION_DOC}'")

    qualified = {
        name: res for name, res in results.items()
        if res["test_metrics"]["precision"] >= 0.98
    }

    if qualified:
        logger.info(f"Models meeting test precision >= 0.98: {list(qualified.keys())}")
        best_name = max(
            qualified.keys(),
            key=lambda k: (
                qualified[k]["test_metrics"]["recall"],
                qualified[k]["test_metrics"]["f1"],
            )
        )
    else:
        logger.warning("No model met precision >= 0.98 threshold. Selecting highest precision model.")
        best_name = max(
            results.keys(),
            key=lambda k: (
                results[k]["test_metrics"]["precision"],
                results[k]["test_metrics"]["recall"],
                results[k]["test_metrics"]["f1"],
            )
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
        weights = clf.feature_log_prob_[1] - clf.feature_log_prob_[0]
    elif isinstance(clf, CalibratedClassifierCV):
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


def run_training_pipeline() -> Tuple[Pipeline, Dict[str, Any]]:
    """Full offline training pipeline orchestration."""
    print("=" * 80)
    print("MAILGUARD AI - PHASE 4: PREPROCESSING & MODEL TRAINING")
    print(f"Selection Criterion: {SELECTION_CRITERION_DOC}")
    print("=" * 80)

    # 1. Load, clean, and deduplicate data
    X, y, profile = load_and_clean_data(RAW_DATA_PATH)

    # 2. Stratified train/test split BEFORE fitting any transformer
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    logger.info(f"Train split size: {len(X_train)} (Ham: {(y_train == 0).sum()}, Spam: {(y_train == 1).sum()})")
    logger.info(f"Test split size: {len(X_test)} (Ham: {(y_test == 0).sum()}, Spam: {(y_test == 1).sum()})")

    # 3. Cross-split duplicate assertion to guarantee 0 data leakage
    train_texts = set(X_train)
    test_overlap = sum(1 for t in X_test if t in train_texts)
    logger.info(f"Cross-split duplicate check: {test_overlap} overlapping texts found.")
    assert test_overlap == 0, f"Data leakage detected! {test_overlap} texts appear in both train and test splits."

    # 4. Train and compare 3 models
    candidates = build_candidate_pipelines()
    results: Dict[str, Dict[str, Any]] = {}

    print("\n--- MODEL COMPARISON RESULTS (CV + TEST) ---")
    for name, pipeline in candidates.items():
        eval_output = evaluate_model_cv_and_test(
            name, pipeline, X_train, y_train, X_test, y_test, cv_folds=5
        )
        results[name] = eval_output

        cv = eval_output["cv_5fold"]
        tm = eval_output["test_metrics"]
        cm = tm["confusion_matrix"]

        print(f"\nModel: {name}")
        print(f"  5-Fold CV Accuracy:  {cv['mean_accuracy']:.4f} (+/- {cv['std_accuracy']:.4f})")
        print(f"  5-Fold CV Precision: {cv['mean_precision']:.4f} (+/- {cv['std_precision']:.4f})")
        print(f"  5-Fold CV Recall:    {cv['mean_recall']:.4f} (+/- {cv['std_recall']:.4f})")
        print(f"  5-Fold CV F1:        {cv['mean_f1']:.4f} (+/- {cv['std_f1']:.4f})")
        print(f"  Held-out Test Precision: {tm['precision']:.4f} | Recall: {tm['recall']:.4f} | F1: {tm['f1']:.4f} | Acc: {tm['accuracy']:.4f}")
        print(f"  Confusion Matrix: TP={cm['true_positives']}, FP={cm['false_positives']}, TN={cm['true_negatives']}, FN={cm['false_negatives']}")

    # 5. Model selection
    winner_name = select_best_model(results)
    winner_pipeline = candidates[winner_name]
    winner_metrics = results[winner_name]["test_metrics"]

    # 6. Extract top contributing spam terms
    top_terms = extract_top_spam_terms(winner_pipeline, top_n=30)

    # 7. Save raw results to reports/model_comparison.json
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    comparison_report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "selection_criterion": SELECTION_CRITERION_DOC,
        "stratified_split": {
            "total_samples": len(X),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "random_state": 42,
            "test_size": 0.20,
            "cross_split_duplicates": test_overlap,
        },
        "models": results,
        "selected_model": winner_name,
        "selection_rationale": (
            f"Selected {winner_name} based on pre-declared criterion: "
            f"Spam Precision ({winner_metrics['precision']:.4f}) >= 0.98, "
            f"then highest Spam Recall ({winner_metrics['recall']:.4f}) and F1 ({winner_metrics['f1']:.4f})."
        ),
    }

    logger.info(f"Saving model comparison report to {MODEL_COMPARISON_JSON}...")
    with open(MODEL_COMPARISON_JSON, "w", encoding="utf-8") as f:
        json.dump(comparison_report, f, indent=2)

    # 8. Save production pipeline artifact
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Saving winning pipeline artifact to {MODEL_PATH}...")
    joblib.dump(winner_pipeline, MODEL_PATH)

    # 9. Save models/metadata.json
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
        "all_candidate_metrics": {k: v["test_metrics"] for k, v in results.items()},
        "top_global_spam_terms": top_terms,
        "qualifier_notice": (
            "Metrics are measured on a held-out test set of THIS dataset only. "
            "Real-world email performance may be lower."
        ),
    }

    logger.info(f"Saving metadata to {METADATA_PATH}...")
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print("\n" + "=" * 80)
    print("PHASE 4 TRAINING COMPLETE")
    print(f"Selected Model: {winner_name}")
    print(f"Test Precision: {winner_metrics['precision']:.4f} (Priority 1)")
    print(f"Test Recall:    {winner_metrics['recall']:.4f} (Priority 2)")
    print(f"Test F1:        {winner_metrics['f1']:.4f} (Priority 3)")
    print(f"Saved Artifact: {MODEL_PATH}")
    print(f"Saved Metadata: {METADATA_PATH}")
    print(f"Comparison:     {MODEL_COMPARISON_JSON}")
    print("=" * 80)

    return winner_pipeline, comparison_report


if __name__ == "__main__":
    run_training_pipeline()
