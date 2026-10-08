# Train/Test Near-Duplicate Analysis & Correction Report

## 1. Summary of Correction
In the Phase 5/6 preliminary report, the held-out test set de-duplicated metrics were erroneously reported as having $FN = 29$ and $N = 5,026$, whereas the full test set had $FN = 27$.
**Reason for Error**: In the preliminary scratch analysis, an approximate subset calculation or different similarity partition was referenced, inadvertently introducing two spurious false negatives. In reality, subsetting a held-out test set by removing near-duplicates of the training set can **never** increase false negatives or false positives, because all samples in the clean subset are drawn directly from the evaluated test set.

A rigorous re-evaluation using exact TF-IDF cosine similarity ($\ge 0.95$) against the full training set ($N=24,369$) was executed on the held-out test set ($N=6,093$) using the trained production model pipeline (`models/spam_pipeline.joblib`).

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
