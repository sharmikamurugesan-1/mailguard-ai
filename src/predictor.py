"""Model inference engine, calibration mapping, and explanation generator.

Phase 6: Predictor Implementation
- Singleton cached model loading (loads ONCE).
- Scikit-learn version verification against metadata.json with explicit warning on mismatch.
- Exposes predict(subject: str, body: str) -> Dict[str, Any].
- Calibrated probability output labeled "confidence".
- Signal explanations computed via model weights x TF-IDF feature values for tokens present in input.
- Leverages src.reliability for uncertain band and warning codes.
- Safe terminology: "Likely legitimate" for ham (never "safe" or "100%").
"""

import json
import logging
from pathlib import Path
import pickle
from typing import Any, Dict, List, Optional
import warnings

import joblib
import numpy as np
import sklearn
try:
    from sklearn.calibration import CalibratedClassifierCV
except Exception:
    CalibratedClassifierCV = None

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

try:
    from sklearn.linear_model import LogisticRegression
except Exception:
    LogisticRegression = None

try:
    from sklearn.naive_bayes import MultinomialNB
except Exception:
    MultinomialNB = None

from sklearn.pipeline import Pipeline

try:
    from sklearn.svm import LinearSVC
except Exception:
    LinearSVC = None


from src.config import (
    METADATA_PATH,
    MODEL_PATH,
)
from src.preprocessing import clean_text_for_nlp, combine_email, tokenize_text
from src.reliability import (
    compute_reliability,
    evaluate_decision,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MailGuard-Predictor")


def is_stopword_term(term: str) -> bool:
    """Determine whether a token or n-gram consists entirely of standard English stopwords."""
    t = term.lower().strip()
    if t in ENGLISH_STOP_WORDS:
        return True
    parts = t.split()
    if parts and all(p in ENGLISH_STOP_WORDS for p in parts):
        return True
    return False


class SpamPredictor:
    """Production predictor wrapping trained scikit-learn pipeline and metadata."""

    def __init__(
        self,
        model_path: Path = MODEL_PATH,
        metadata_path: Path = METADATA_PATH,
    ):
        self.model_path = model_path
        self.metadata_path = metadata_path
        self.pipeline: Optional[Pipeline] = None
        self.metadata: Dict[str, Any] = {}
        self.load_count: int = 0
        self._load_artifacts()

    def _load_artifacts(self) -> None:
        """Load pipeline artifact and metadata once, checking version compatibility."""
        # 1. Load Metadata
        metadata_filename = Path(self.metadata_path).name
        if self.metadata_path.exists():
            try:
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load metadata from {metadata_filename}: {e}")
                self.metadata = {}
        else:
            logger.warning(f"Metadata file not found at {metadata_filename}")
            self.metadata = {}

        # Check scikit-learn version mismatch
        trained_sklearn_version = self.metadata.get("sklearn_version")
        current_sklearn_version = sklearn.__version__

        if trained_sklearn_version and trained_sklearn_version != current_sklearn_version:
            warn_msg = (
                f"Scikit-learn version mismatch detected! Model was trained with {trained_sklearn_version}, "
                f"but runtime is {current_sklearn_version}. Potential deserialization or behavioral discrepancies."
            )
            warnings.warn(warn_msg, RuntimeWarning)
            logger.warning(warn_msg)

        # 2. Load Pipeline Artifact
        model_filename = Path(self.model_path).name
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model artifact not found: {model_filename}. "
                f"Ensure models/{model_filename} exists."
            )

        logger.info(f"Loading model pipeline from {model_filename}... ")
        self.pipeline = joblib.load(self.model_path)
        self.load_count += 1
        logger.info(f"Model pipeline loaded successfully (load_count={self.load_count}).")

    def _extract_signals(
        self,
        text: str,
        top_k: int = 15,
        filter_stopwords: bool = False,
    ) -> List[Dict[str, Any]]:
        """Extract model-derived contribution signals for tokens present in this email.

        Signals are computed as:
            contribution = (TF-IDF value of token in email) * (model weight for token)
        where model weight is the average calibrated hyperplane normal vector coefficient
        across CalibratedClassifierCV folds.

        Note: These are statistical correlations indicating terms that pushed the decision
        toward spam or ham; they should never be interpreted as 'the causal reason'.
        """
        if not self.pipeline:
            return []

        tfidf = self.pipeline.named_steps.get("tfidf")
        clf = self.pipeline.named_steps.get("clf")

        if not tfidf or not clf:
            return []

        vocab = getattr(tfidf, "vocabulary_", {})
        if not vocab:
            return []

        # Extract weights from classifier
        weights = None
        clf_name = type(clf).__name__
        if clf_name == "CalibratedClassifierCV" or (CalibratedClassifierCV is not None and isinstance(clf, CalibratedClassifierCV)):
            base_weights = []
            for cal_clf in getattr(clf, "calibrated_classifiers_", []):
                est = getattr(cal_clf, "estimator", None)
                if est and hasattr(est, "coef_"):
                    base_weights.append(est.coef_[0])
            if base_weights:
                weights = np.mean(base_weights, axis=0)
        elif clf_name == "LogisticRegression" or (LogisticRegression is not None and isinstance(clf, LogisticRegression)):
            weights = clf.coef_[0]
        elif clf_name == "MultinomialNB" or (MultinomialNB is not None and isinstance(clf, MultinomialNB)):
            weights = clf.feature_log_prob_[1] - clf.feature_log_prob_[0]


        if weights is None:
            return []

        # Transform email using tfidf to get sparse values
        cleaned = clean_text_for_nlp(text)
        tfidf_matrix = tfidf.transform([cleaned])
        coo = tfidf_matrix.tocoo()

        feature_names = tfidf.get_feature_names_out()

        signals: List[Dict[str, Any]] = []
        for col_idx, tfidf_val in zip(coo.col, coo.data):
            term = str(feature_names[col_idx])
            weight = float(weights[col_idx])
            score = float(tfidf_val * weight)
            is_stop = is_stopword_term(term)

            if filter_stopwords and is_stop:
                continue

            signals.append({
                "term": term,
                "contribution": round(score, 4),
                "direction": "spam" if weight > 0 else "ham",
                "is_stopword": is_stop,
                "note": "top contributing term",
            })

        # Sort by absolute contribution magnitude
        signals.sort(key=lambda s: abs(s["contribution"]), reverse=True)
        return signals[:top_k]

    def predict(
        self,
        subject: Optional[str] = "",
        body: str = "",
        filter_stopwords: bool = False,
    ) -> Dict[str, Any]:
        """Classify email subject and body, returning decision, calibrated confidence, signals, and reliability."""
        if not self.pipeline:
            raise RuntimeError("Model pipeline is not loaded.")

        combined_text = combine_email(subject, body)
        raw_tokens = tokenize_text(combined_text)

        # Calibrated probability output
        if not raw_tokens or not combined_text.strip():
            p_spam = 0.50
        else:
            proba = self.pipeline.predict_proba([combined_text])[0]
            # Standard order: class 0 = ham, class 1 = spam
            p_spam = float(proba[1])

        # Evaluate decision via reliability module
        prediction, label_display, risk_level, confidence = evaluate_decision(p_spam)

        # Vectorizer reference for vocab coverage
        tfidf = self.pipeline.named_steps.get("tfidf")
        reliability = compute_reliability(
            spam_probability=p_spam,
            text=combined_text,
            vectorizer=tfidf,
        )

        # Model-derived signals & top_tokens (max 15)
        signals = self._extract_signals(
            combined_text,
            top_k=15,
            filter_stopwords=filter_stopwords,
        )

        top_tokens = [
            {
                "token": s["term"],
                "weight": s["contribution"],
                "direction": s["direction"],
                "is_stopword": s["is_stopword"],
            }
            for s in signals[:15]
        ]

        # Model version from metadata or default
        model_version = self.metadata.get("trained_at", "1.0.0")

        return {
            "prediction": prediction,
            "label": label_display,
            "label_display": label_display,
            "confidence": confidence,
            "model_confidence": confidence,
            "spam_probability": round(p_spam, 4),
            "risk_level": risk_level,
            "is_uncertain": (prediction == "uncertain"),
            "signals": signals,
            "top_contributing_terms": signals,
            "top_tokens": top_tokens,
            "reliability": {
                "level": reliability["level"],
                "warnings": reliability["warnings"],
            },
            "model_version": model_version,
            "dataset_type": "email",
        }


# Global singleton predictor instance
_PREDICTOR_INSTANCE: Optional[SpamPredictor] = None


def get_predictor() -> SpamPredictor:
    """Retrieve or initialize singleton SpamPredictor."""
    global _PREDICTOR_INSTANCE
    if _PREDICTOR_INSTANCE is None:
        _PREDICTOR_INSTANCE = SpamPredictor()
    return _PREDICTOR_INSTANCE


def predict(
    subject: Optional[str] = "",
    body: str = "",
    filter_stopwords: bool = False,
) -> Dict[str, Any]:
    """Module-level convenience inference function."""
    return get_predictor().predict(subject, body, filter_stopwords=filter_stopwords)
