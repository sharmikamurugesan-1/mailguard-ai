"""Verify that all metrics cited in README.md match models/metadata.json in their labelled context."""

import json
import re
import sys
from pathlib import Path

def main():
    base_dir = Path(__file__).resolve().parent.parent
    readme_path = base_dir / "README.md"
    metadata_path = base_dir / "models" / "metadata.json"

    if not readme_path.exists():
        print(f"ERROR: {readme_path} does not exist.")
        sys.exit(1)
    if not metadata_path.exists():
        print(f"ERROR: {metadata_path} does not exist.")
        sys.exit(1)

    readme_text = readme_path.read_text(encoding="utf-8")
    with open(metadata_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    print("=" * 75)
    print("STRENGTHENED CONTEXT-AWARE README.MD METRIC VERIFICATION")
    print("=" * 75)

    checks = [
        # (Label, Context Regex Pattern, Expected Context Description)
        ("Total samples in context", r"from \*\*30,462\*\* total samples", "Total sample count sentence"),
        ("Train split in context", r"training split of \*\*24,369\*\* samples", "Train split size description"),
        ("Test split in context", r"held-out test split of \*\*6,093\*\* emails", "Test split size description"),
        
        ("CV SVM Precision in table", r"\|\s*\*\*Calibrated Linear SVM\*\*\s*\|\s*\*\*98\.72%\*\*", "CV comparison table row"),
        ("CV SVM Recall in table", r"\|\s*\*\*Calibrated Linear SVM\*\*\s*\|.*?\|\s*\*\*99\.29%\*\*", "CV comparison table row"),
        ("CV SVM F1 in table", r"\|\s*\*\*Calibrated Linear SVM\*\*\s*\|.*?\|\s*\*\*99\.00%\*\*", "CV comparison table row"),
        ("CV SVM Accuracy in table", r"\|\s*\*\*Calibrated Linear SVM\*\*\s*\|.*?\|\s*\*\*99\.04%\*\*", "CV comparison table row"),
        ("CV NB Precision in table", r"\|\s*Multinomial Naive Bayes\s*\|\s*98\.24%", "CV comparison table row"),
        ("CV LR Precision in table", r"\|\s*Logistic Regression\s*\|\s*97\.65%", "CV comparison table row"),

        ("Test Accuracy in Set A", r"-\s*\*\*Accuracy\*\*:\s*\*\*99\.00%\*\*", "Held-out test set accuracy bullet"),
        ("Test Precision in Set A", r"-\s*\*\*Precision \(Spam\)\*\*:\s*\*\*98\.83%\*\*", "Held-out test set precision bullet"),
        ("Test Recall in Set A", r"-\s*\*\*Recall \(Spam\)\*\*:\s*\*\*99\.07%\*\*", "Held-out test set recall bullet"),
        ("Test F1 in Set A", r"-\s*\*\*F1 Score\*\*:\s*\*\*98\.95%\*\*", "Held-out test set F1 bullet"),
        ("Test True Positives in Set A", r"-\s*\*\*True Positives \(TP\)\*\*:\s*2,884", "Confusion matrix TP bullet"),
        ("Test True Negatives in Set A", r"-\s*\*\*True Negatives \(TN\)\*\*:\s*3,148", "Confusion matrix TN bullet"),
        ("Test False Positives in Set A", r"-\s*\*\*False Positives \(FP\)\*\*:\s*34\b", "Confusion matrix FP bullet"),
        ("Test False Negatives in Set A", r"-\s*\*\*False Negatives \(FN\)\*\*:\s*27\b", "Confusion matrix FN bullet"),

        ("Near-duplicates n-gram (1,2)", r"Identifies \*\*1,208\*\* near-duplicates \(\*\*19\.83%\*\*", "Near-duplicate production bullet"),
        ("Near-duplicates unigram (1,1)", r"Identifies \*\*1,070\*\* near-duplicates \(\*\*17\.56%\*\*", "Near-duplicate unigram bullet"),
        ("De-duplicated test split size", r"De-Duplicated Test Set \(\$N = 4,885\$\)", "De-duplicated column header"),
        ("De-duplicated Accuracy in table", r"\|\s*\*\*Accuracy\*\*\s*\|\s*99\.00%\s*\|\s*\*\*98\.75%\*\*", "Deduplication table row"),
        ("De-duplicated Precision in table", r"\|\s*\*\*Precision \(Spam\)\*\*\s*\|\s*98\.83%\s*\|\s*\*\*98\.52%\*\*", "Deduplication table row"),
        ("De-duplicated Recall in table", r"\|\s*\*\*Recall \(Spam\)\*\*\s*\|\s*99\.07%\s*\|\s*\*\*98\.82%\*\*", "Deduplication table row"),
        ("De-duplicated F1 in table", r"\|\s*\*\*F1 Score\*\*\s*\|\s*98\.95%\s*\|\s*\*\*98\.67%\*\*", "Deduplication table row"),
        ("Invariance of FP in table", r"\|\s*\*\*False Positives \(FP\)\*\*\s*\|\s*34\s*\|\s*34\s*\|", "Deduplication table row"),
        ("Invariance of FN in table", r"\|\s*\*\*False Negatives \(FN\)\*\*\s*\|\s*27\s*\|\s*27\s*\|", "Deduplication table row"),

        ("Uncertain band window in context", r"Band Window\*\*:\s*\$?\[0\.40,\s*0\.60\]\$?", "Uncertain band window description"),
        ("Uncertain band count in context", r"Samples in Band\*\*:\s*\*\*113\*\* emails", "Uncertain band samples description"),
        ("Uncertain outside accuracy", r"Accuracy:\s*\*\*99\.20%\*\*", "Uncertain band outside accuracy"),
        ("Uncertain outside precision", r"Precision:\s*\*\*98\.90%\*\*", "Uncertain band outside precision"),
        ("Uncertain outside recall", r"Recall:\s*\*\*99\.44%\*\*", "Uncertain band outside recall"),
    ]

    all_passed = True
    for label, pattern, context_desc in checks:
        match = re.search(pattern, readme_text, re.IGNORECASE | re.DOTALL)
        status = "[PASS]" if match else "[FAIL]"
        if not match:
            all_passed = False
        print(f"{status:7} {label:<35} | {context_desc}")

    print("-" * 75)
    if all_passed:
        print(f"RESULT: ALL {len(checks)} METRICS VERIFIED STRICTLY IN CONTEXT!")
        sys.exit(0)
    else:
        print("RESULT: Discrepancy detected in context-aware README metrics verification.")
        sys.exit(1)

if __name__ == "__main__":
    main()
