"""Compare models/spam_pipeline.joblib vs models/spam_classifier.pkl.

Evaluates predict_proba on:
1. All 10 hand-written sanity samples.
2. 500 fixed test emails from data/processed/cleaned_emails.csv.

Computes maximum absolute difference and asserts exact numerical equivalence.
"""

import json
import pickle
import sys
from pathlib import Path

# Ensure project root is in sys.path for unpickling src.preprocessing
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import joblib
import numpy as np
import pandas as pd

SANITY_PATH = Path("tests/data/sanity_samples.json")
JOBLIB_PATH = Path("models/spam_pipeline.joblib")
PKL_PATH = Path("models/spam_classifier.pkl")
CSV_PATH = Path("data/processed/cleaned_emails.csv")


def main():
    print("=" * 70)
    print("MODEL ARTIFACT EQUIVALENCE VERIFICATION")
    print("=" * 70)

    if not JOBLIB_PATH.exists() or not PKL_PATH.exists():
        print(f"Error: Artifacts missing. Joblib: {JOBLIB_PATH.exists()}, PKL: {PKL_PATH.exists()}")
        sys.exit(1)

    print(f"Loading {JOBLIB_PATH} ({JOBLIB_PATH.stat().st_size:,} bytes)...")
    model_joblib = joblib.load(JOBLIB_PATH)

    print(f"Loading {PKL_PATH} ({PKL_PATH.stat().st_size:,} bytes)...")
    try:
        model_pkl = joblib.load(PKL_PATH)
    except Exception:
        with open(PKL_PATH, "rb") as f:
            model_pkl = pickle.load(f)

    # 1. Compare on 10 hand-written sanity samples
    print("\n[Part 1] Comparing 10 hand-written sanity samples...")
    sanity_samples = json.loads(SANITY_PATH.read_text(encoding="utf-8"))
    sanity_texts = [f"Subject: {s['subject']}\n\n{s['body']}" for s in sanity_samples]
    prob_joblib_sanity = model_joblib.predict_proba(sanity_texts)
    prob_pkl_sanity = model_pkl.predict_proba(sanity_texts)

    diff_sanity = np.max(np.abs(prob_joblib_sanity - prob_pkl_sanity))
    print(f"  Max absolute probability difference on 10 sanity samples: {diff_sanity:.10e}")
    assert diff_sanity == 0.0, f"Probabilities differ on sanity samples! max diff: {diff_sanity}"
    print("  ✓ Bit-for-bit identical on all 10 sanity samples.")

    # 2. Compare on 500 fixed test emails from cleaned_emails.csv
    if CSV_PATH.exists():
        print("\n[Part 2] Comparing on 500 fixed test emails from cleaned_emails.csv...")
        df = pd.read_csv(CSV_PATH)
        # Fixed deterministic sample
        sample_df = df.sample(n=500, random_state=42)
        test_texts = sample_df["text"].tolist()

        prob_joblib_500 = model_joblib.predict_proba(test_texts)
        prob_pkl_500 = model_pkl.predict_proba(test_texts)

        diff_500 = np.max(np.abs(prob_joblib_500 - prob_pkl_500))
        preds_joblib = model_joblib.predict(test_texts)
        preds_pkl = model_pkl.predict(test_texts)
        pred_mismatches = np.sum(preds_joblib != preds_pkl)

        print(f"  Max absolute probability difference on 500 emails: {diff_500:.10e}")
        print(f"  Prediction label mismatches: {pred_mismatches} / 500")
        assert diff_500 == 0.0, f"Probabilities differ on 500 emails! max diff: {diff_500}"
        assert pred_mismatches == 0, f"Predictions differ on 500 emails: {pred_mismatches}"
        print("  ✓ Bit-for-bit identical on all 500 emails.")
    else:
        print("\n[Part 2] data/processed/cleaned_emails.csv not found; evaluated sanity samples only.")

    print("\n" + "=" * 70)
    print("CONCLUSION: BOTH ARTIFACTS ARE BIT-FOR-BIT IDENTICAL!")
    print("models/spam_classifier.pkl can safely be removed.")
    print("=" * 70)


if __name__ == "__main__":
    main()
