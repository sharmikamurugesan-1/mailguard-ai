# Train/Test Near-Duplicate Analysis & Correction Report

## 1. Summary of Correction
In the Phase 5 report, near-duplicates were reported as **1,067** (17.51%), whereas in Phase 6/7 they were measured as **1,208** (19.83%), both with `random_state=42`.

### Root-Cause Analysis for the Discrepancy:
- **Phase 5 Calculation (1,067 / 17.51%)**:
  The preliminary scratch check evaluated cosine similarity using a unigram TF-IDF vectorizer (`ngram_range=(1, 1)`, 15,000 features). Without bigram pairings, distinct phrases have lower pairwise overlap, identifying 1,067 near-duplicates.
- **Production Pipeline Calculation (1,208 / 19.83%)**:
  The production model pipeline uses `ngram_range=(1, 2)` (unigrams + bigrams, 15,000 features) in its `TfidfVectorizer` step. In this richer feature space, repeated boilerplate structures and common bigrams yield higher pairwise cosine similarity, correctly identifying **1,208** near-duplicates.
- **False Negative Invariance**:
  Removing near-duplicates reduces true positives from 2,884 to 2,256 and true negatives from 3,148 to 2,568. False negatives remain **strictly 27** and false positives remain **strictly 34**. Subsetting can never create new errors.

### Reproducible Audit Command:
```powershell
.\.venv\Scripts\python.exe scripts/near_duplicate_check.py --threshold 0.95
```

---

## 2. Confusion Matrices (Both Sets)

### Set A: Full Held-Out Test Set ($N = 6,093$)
- **True Positives (TP)**: 2,884
- **False Positives (FP)**: 34
- **True Negatives (TN)**: 3,148
- **False Negatives (FN)**: 27

```
                     Predicted Legitimate (Ham)    Predicted Spam
Actual Ham (0)       TN = 3,148                    FP = 34
Actual Spam (1)      FN = 27                       TP = 2,884
```

- **Accuracy**: 0.989989 (99.00%)
- **Precision**: 0.988348 (98.83%)
- **Recall**: 0.990725 (99.07%)
- **F1 Score**: 0.989535 (98.95%)

---

### Set B: Near-Duplicates Removed ($N = 1,208$ samples with cosine $\ge 0.95$)
- **Near-Duplicates Removed**: 1,208 emails (19.83% of test set)
  - True Ham: 580 (all predicted Ham by model)
  - True Spam: 628 (all predicted Spam by model)
- Note: Zero classification errors existed among the 1,208 near-duplicates.

---

### Set C: Corrected De-Duplicated Test Set ($N = 4,885$)
When removing all 1,208 near-duplicates from the test set:
- **True Positives (TP)**: $2,884 - 628 = 2,256$
- **False Positives (FP)**: $34 - 0 = 34$
- **True Negatives (TN)**: $3,148 - 580 = 2,568$
- **False Negatives (FN)**: $27 - 0 = 27$

```
                     Predicted Legitimate (Ham)    Predicted Spam
Actual Ham (0)       TN = 2,568                    FP = 34
Actual Spam (1)      FN = 27                       TP = 2,256
```

- **Accuracy**: $4,824 / 4,885 = 0.987513$ (98.75%)
- **Precision**: $2,256 / 2,290 = 0.985153$ (98.52%)
- **Recall**: $2,256 / 2,283 = 0.988173$ (98.82%)
- **F1 Score**: $0.986661$ (98.67%)

---

## 3. Generalization Conclusion
Even after completely stripping every single sample with $\ge 95\%$ cosine similarity to any training email, the model retains:
- **Precision**: 98.52% (exceeding the 0.98 requirement)
- **Recall**: 98.82%
- **Accuracy**: 98.75%
This demonstrates that high test accuracy is driven by genuine generalization across vocabulary patterns, not mere memorization of near-duplicate emails.
