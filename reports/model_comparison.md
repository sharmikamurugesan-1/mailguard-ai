# Model Comparison and Selection Report

## Executive Summary
- **Selection Basis**: Strictly based on **5-Fold Cross-Validation (out-of-fold) on the training set**.
- **Selection Criterion**: `Spam precision >= 0.98 first, then highest recall on spam, then F1 score. Never select by accuracy alone.`
- **Selected Production Model**: **Calibrated Linear SVM**
- **Evaluation Dataset**: Enron Spam Dataset (`email`)
- **Total Samples**: 30,462 (Train: 24,369, Test: 6,093)

---

## 1. Model Selection Basis: 5-Fold Cross-Validation Metrics (Train Split)

| Model | 5-Fold CV Precision | 5-Fold CV Recall | 5-Fold CV F1 | 5-Fold CV Accuracy | Meets Priority 1 (P >= 0.98)? |
|---|---|---|---|---|---|
| Multinomial Naive Bayes | 0.9824 (±0.0028) | 0.9852 (±0.0011) | 0.9838 (±0.0009) | 0.9845 (±0.0009) | Yes |
| Logistic Regression | 0.9765 (±0.0025) | 0.9941 (±0.0021) | 0.9852 (±0.0010) | 0.9857 (±0.0010) | No (Disqualified) |
| **Calibrated Linear SVM** | 0.9872 (±0.0022) | 0.9929 (±0.0027) | 0.9900 (±0.0010) | 0.9904 (±0.0010) | Yes |


### Selection Decision & Rationale:
Selection based on 5-Fold Cross-Validation metrics on the training set: Qualifying models with CV Precision >= 0.98: ['Multinomial Naive Bayes', 'Calibrated Linear SVM']. Selected 'Calibrated Linear SVM' based on Priority 2 (Highest CV Recall: 0.9929) and Priority 3 (Highest CV F1: 0.9900). Logistic Regression achieved CV Precision 0.9765 and was disqualified under Priority 1.

#### Runner-Up Analysis (CV):
- **Calibrated Linear SVM (Winner)**:
  - 5-Fold CV Precision: `0.9872` (>= 0.98)
  - 5-Fold CV Recall: `0.9929` (Highest among qualifying models)
  - 5-Fold CV F1 Score: `0.9900`
- **Multinomial Naive Bayes (Runner-Up)**:
  - 5-Fold CV Precision: `0.9824` (>= 0.98)
  - 5-Fold CV Recall: `0.9852` (Lower recall, more false negatives than SVM)
  - 5-Fold CV F1 Score: `0.9838`
- **Logistic Regression (Disqualified under Priority 1)**:
  - 5-Fold CV Precision: `0.9765` (< 0.98 threshold, higher false positive rate)

---

## 2. Final Held-Out Test Set Performance

The held-out test set was evaluated strictly for final validation reporting:

| Model | Test Precision | Test Recall | Test F1 | Test Accuracy | False Positives (FP) | False Negatives (FN) |
|---|---|---|---|---|---|---|
| Multinomial Naive Bayes | 0.9832 | 0.9852 | 0.9842 | 0.9849 | 49 | 43 |
| Logistic Regression | 0.9797 | 0.9931 | 0.9864 | 0.9869 | 60 | 20 |
| **Calibrated Linear SVM** | 0.9883 | 0.9907 | 0.9895 | 0.9900 | 34 | 27 |


---

## 3. Confusion Matrices (Held-Out Test Set)


### Confusion Matrix: Multinomial Naive Bayes (Held-out Test Set)

```
                  Predicted Legitimate (Ham)    Predicted Spam
Actual Ham (0)    TN = 3133                    FP = 49            
Actual Spam (1)   FN = 43                      TP = 2868          
```

### Confusion Matrix: Logistic Regression (Held-out Test Set)

```
                  Predicted Legitimate (Ham)    Predicted Spam
Actual Ham (0)    TN = 3122                    FP = 60            
Actual Spam (1)   FN = 20                      TP = 2891          
```

### Confusion Matrix: Calibrated Linear SVM (Held-out Test Set)

```
                  Predicted Legitimate (Ham)    Predicted Spam
Actual Ham (0)    TN = 3148                    FP = 34            
Actual Spam (1)   FN = 27                      TP = 2884          
```


---

## 4. Threshold & Uncertain Band Tuning (Validation Set Only)

Thresholds were tuned **strictly on out-of-fold validation predictions of the training set** (5-Fold Out-of-Fold Cross-Validation on TRAIN set only):

- **Uncertain Lower Bound**: `0.4`
- **Uncertain Upper Bound**: `0.6`
- **Samples in Uncertain Band**: `113` (0.46%)
- **Uncertain Band Class Distribution**: Ham = `58`, Spam = `55`
- **Accuracy Outside Uncertain Band**: `99.20%`
- **Spam Precision Outside Band**: `98.90%`

### Risk Tier Definitions:
1. **Low Risk** (P(spam) < 0.40): Label: *"Likely legitimate"* (never "safe").
2. **Medium Risk / Uncertain** (0.40 <= P(spam) <= 0.60): Label: *"Needs review"*.
3. **High Risk** (0.60 < P(spam) < 0.85): Label: *"Likely Spam"*.
4. **Critical Risk** (P(spam) >= 0.85): Label: *"Likely Spam"* (High-confidence spam signals).

---

## 5. Dataset Provenance & L2 Transparency Qualifications
- **Dataset Name**: Enron Spam Dataset
- **Source URL**: [https://github.com/MWiechmann/enron_spam_data](https://github.com/MWiechmann/enron_spam_data)
- **License**: GPL-3.0 / Public Domain (CALO Enron Corpus)
- **Dataset Type**: `email`
- **Mandatory Caveat**: *Metrics are measured on a held-out test set of THIS dataset only. Real-world email performance may be lower.*
