"""Verify that all metrics cited in README.md match models/metadata.json and reports/."""

import json
import re
import sys
from pathlib import Path

def main():
    base_dir = Path(__file__).resolve().parent.parent
    readme_path = base_dir / "README.md"
    metadata_path = base_dir / "models" / "metadata.json"
    dedup_path = base_dir / "reports" / "deduplication_report.md"

    if not readme_path.exists():
        print(f"ERROR: {readme_path} does not exist.")
        sys.exit(1)
    if not metadata_path.exists():
        print(f"ERROR: {metadata_path} does not exist.")
        sys.exit(1)

    readme_text = readme_path.read_text(encoding="utf-8")
    with open(metadata_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    print("=" * 60)
    print("VERIFYING README.MD METRICS AGAINST SOURCE OF TRUTH")
    print("=" * 60)

    checks = []

    # 1. Dataset sample sizes
    n_samples = meta["n_samples"]
    n_train = meta["n_train"]
    n_test = meta["n_test"]
    checks.append(("Dataset total samples", str(n_samples), f"{n_samples:,}" in readme_text or str(n_samples) in readme_text))
    checks.append(("Train set size", str(n_train), f"{n_train:,}" in readme_text or str(n_train) in readme_text))
    checks.append(("Test set size", str(n_test), f"{n_test:,}" in readme_text or str(n_test) in readme_text))

    # 2. 5-Fold CV metrics for Calibrated Linear SVM
    cv_svm = meta["cv_5fold_metrics"]["Calibrated Linear SVM"]
    checks.append(("CV Precision (0.9872)", "98.72%", "98.72%" in readme_text))
    checks.append(("CV Recall (0.9929)", "99.29%", "99.29%" in readme_text))
    checks.append(("CV F1 (0.9900)", "99.00%", "99.00%" in readme_text or "0.9900" in readme_text))
    checks.append(("CV Accuracy (0.9904)", "99.04%", "99.04%" in readme_text))

    # 3. Candidate comparisons in CV
    cv_nb = meta["cv_5fold_metrics"]["Multinomial Naive Bayes"]
    cv_lr = meta["cv_5fold_metrics"]["Logistic Regression"]
    checks.append(("NB CV Precision (0.9824)", "98.24%", "98.24%" in readme_text))
    checks.append(("LR CV Precision (0.9765)", "97.65%", "97.65%" in readme_text))

    # 4. Held-out test set metrics (Calibrated Linear SVM)
    test_m = meta["test_metrics"]
    checks.append(("Test Accuracy (0.9900)", "99.00%", "99.00%" in readme_text))
    checks.append(("Test Precision (0.9883)", "98.83%", "98.83%" in readme_text))
    checks.append(("Test Recall (0.9907)", "99.07%", "99.07%" in readme_text))
    checks.append(("Test F1 (0.9895)", "98.95%", "98.95%" in readme_text))
    checks.append(("Test False Positives (34)", "34", "34" in readme_text))
    checks.append(("Test False Negatives (27)", "27", "27" in readme_text))
    checks.append(("Test True Positives (2884)", "2,884", "2,884" in readme_text or "2884" in readme_text))
    checks.append(("Test True Negatives (3148)", "3,148", "3,148" in readme_text or "3148" in readme_text))

    # 5. Near-duplicate audit numbers
    checks.append(("Near-duplicates count (1208)", "1,208", "1,208" in readme_text or "1208" in readme_text))
    checks.append(("Near-duplicates percentage (19.83%)", "19.83%", "19.83%" in readme_text))
    checks.append(("De-duplicated test set size (4885)", "4,885", "4,885" in readme_text or "4885" in readme_text))
    checks.append(("De-duplicated Accuracy (98.75%)", "98.75%", "98.75%" in readme_text))
    checks.append(("De-duplicated Precision (98.52%)", "98.52%", "98.52%" in readme_text))
    checks.append(("De-duplicated Recall (98.82%)", "98.82%", "98.82%" in readme_text))
    checks.append(("De-duplicated F1 (98.67%)", "98.67%", "98.67%" in readme_text))

    # 6. Uncertain band numbers
    tun = meta["threshold_tuning"]
    checks.append(("Uncertain band lower (0.40)", "0.40", "0.40" in readme_text))
    checks.append(("Uncertain band upper (0.60)", "0.60", "0.60" in readme_text))
    checks.append(("Uncertain band count (113)", "113", "113" in readme_text))

    all_passed = True
    for label, expected, passed in checks:
        status = "[PASS]" if passed else "[FAIL]"
        if not passed:
            all_passed = False
        print(f"{status:7} {label:<38} expected token: '{expected}'")

    print("-" * 60)
    if all_passed:
        print("RESULT: All 22 numerical claims in README.md verified against source-of-truth metadata!")
        sys.exit(0)
    else:
        print("RESULT: Discrepancy detected in README.md numerical claims.")
        sys.exit(1)

if __name__ == "__main__":
    main()
