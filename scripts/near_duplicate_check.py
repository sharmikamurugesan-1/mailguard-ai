"""Reproducible near-duplicate evaluation between train and held-out test splits.

Phase 8 / Step 0c:
Calculates exact TF-IDF cosine similarity between held-out test samples (N=6,093)
and training set samples (N=24,369) using the production pipeline vectorizer
(15,000 features, 1-2 n-grams, sublinear TF) and cleaner transformer.

Documents both:
1. Production Pipeline Vectorizer (1-2 ngrams): 1,208 near-duplicates (19.83%)
2. Unigram Baseline Vectorizer (1-1 ngrams): 1,067 - 1,072 near-duplicates (~17.51%)
"""

import argparse
import sys
from pathlib import Path

# Ensure project root in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split

from src.config import MODEL_PATH, RAW_DATA_PATH
from src.train import load_and_clean_data


def run_check(threshold: float = 0.95):
    print("=" * 70)
    print("MAILGUARD AI - TRAIN/TEST NEAR-DUPLICATE AUDIT")
    print(f"Cosine Similarity Threshold: >= {threshold}")
    print("=" * 70)

    # 1. Load cleaned data and split with random_state=42
    X, y, profile = load_and_clean_data(RAW_DATA_PATH)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    # 2. Load model pipeline
    pipeline = joblib.load(MODEL_PATH)
    cleaner = pipeline.named_steps["preprocess"]
    tfidf = pipeline.named_steps["tfidf"]

    print(f"\nTransforming data with pipeline preprocessor & TF-IDF ({tfidf.ngram_range} n-grams)...")
    X_train_clean = cleaner.transform(X_train)
    X_test_clean = cleaner.transform(X_test)

    vec_train = tfidf.transform(X_train_clean)
    vec_test = tfidf.transform(X_test_clean)

    # 3. Batch cosine similarity using Production Pipeline Vectorizer (1-2 ngrams)
    n_test = vec_test.shape[0]
    batch_size = 500
    is_near_dup = np.zeros(n_test, dtype=bool)

    for i in range(0, n_test, batch_size):
        batch = vec_test[i : i + batch_size]
        sim = cosine_similarity(batch, vec_train)
        is_near_dup[i : i + batch_size] = (sim.max(axis=1) >= threshold)

    n_dups_prod = int(is_near_dup.sum())
    dup_pct_prod = (n_dups_prod / n_test) * 100
    print(f"\n[1] Production Vectorizer (ngram_range=(1, 2), max_features=15000):")
    print(f"    Near-duplicates (>= {threshold}): {n_dups_prod:,} / {n_test:,} ({dup_pct_prod:.2f}%)")

    # 3b. Comparison with Unigram Vectorizer (1-1 ngrams)
    unigram_vec = TfidfVectorizer(max_features=15000, ngram_range=(1, 1), sublinear_tf=True)
    unigram_vec.fit(X_train_clean)
    vec_train_uni = unigram_vec.transform(X_train_clean)
    vec_test_uni = unigram_vec.transform(X_test_clean)

    is_near_dup_uni = np.zeros(n_test, dtype=bool)
    for i in range(0, n_test, batch_size):
        batch_u = vec_test_uni[i : i + batch_size]
        sim_u = cosine_similarity(batch_u, vec_train_uni)
        is_near_dup_uni[i : i + batch_size] = (sim_u.max(axis=1) >= threshold)

    n_dups_uni = int(is_near_dup_uni.sum())
    dup_pct_uni = (n_dups_uni / n_test) * 100
    print(f"\n[2] Unigram Vectorizer (ngram_range=(1, 1), max_features=15000):")
    print(f"    Near-duplicates (>= {threshold}): {n_dups_uni:,} / {n_test:,} ({dup_pct_uni:.2f}%)")

    # 4. Compute metrics before and after
    y_pred = pipeline.predict(X_test)
    cm_full = confusion_matrix(y_test, y_pred)
    tn_f, fp_f, fn_f, tp_f = cm_full.ravel()

    print("\n--- FULL HELD-OUT TEST SET (N = 6,093) ---")
    print(f"TP={tp_f}, FP={fp_f}, TN={tn_f}, FN={fn_f}")
    print(f"Accuracy:  {accuracy_score(y_test, y_pred):.6f}")
    print(f"Precision: {precision_score(y_test, y_pred):.6f}")
    print(f"Recall:    {recall_score(y_test, y_pred):.6f}")
    print(f"F1 Score:  {f1_score(y_test, y_pred):.6f}")

    # Clean subset
    mask_clean = ~is_near_dup
    y_test_clean = np.array(y_test)[mask_clean]
    y_pred_clean = y_pred[mask_clean]

    cm_clean = confusion_matrix(y_test_clean, y_pred_clean)
    tn_c, fp_c, fn_c, tp_c = cm_clean.ravel()

    print(f"\n--- DE-DUPLICATED TEST SET (N = {len(y_test_clean):,}) ---")
    print(f"TP={tp_c}, FP={fp_c}, TN={tn_c}, FN={fn_c}")
    print(f"Accuracy:  {accuracy_score(y_test_clean, y_pred_clean):.6f}")
    print(f"Precision: {precision_score(y_test_clean, y_pred_clean):.6f}")
    print(f"Recall:    {recall_score(y_test_clean, y_pred_clean):.6f}")
    print(f"F1 Score:  {f1_score(y_test_clean, y_pred_clean):.6f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=float, default=0.95)
    args = parser.parse_args()
    run_check(args.threshold)
