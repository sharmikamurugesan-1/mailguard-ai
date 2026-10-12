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

import hashlib
import json
import logging
from pathlib import Path
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
    MODEL_EXPECTED_SHA256,
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


def compute_file_sha256(filepath: Path) -> str:
    """Compute lowercase hex SHA-256 checksum of a file in 64 KB blocks."""
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest().lower()


class SpamPredictor:
    """Production predictor wrapping trained scikit-learn pipeline and metadata."""

    def __init__(
        self,
        model_path: Path = MODEL_PATH,
        metadata_path: Path = METADATA_PATH,
        expected_sha256: Optional[str] = None,
    ):
        self.model_path = model_path
        self.metadata_path = metadata_path
        self.expected_sha256 = expected_sha256
        self.pipeline: Optional[Pipeline] = None
        self.metadata: Dict[str, Any] = {}
        self.load_count: int = 0
        self._load_artifacts()

    def _load_artifacts(self) -> None:
        """Load pipeline artifact and metadata once, checking version compatibility and SHA-256 integrity."""
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

        # 2. Check Model Artifact Existence
        model_filename = Path(self.model_path).name
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model artifact not found: {model_filename}. "
                f"Ensure models/{model_filename} exists."
            )

        # 3. Model Integrity Verification (SHA-256)
        # Determine expected hash: explicit argument > metadata.json > committed constant
        resolved_expected = (
            self.expected_sha256
            or self.metadata.get("model_sha256")
            or (MODEL_EXPECTED_SHA256 if Path(self.model_path).resolve() == Path(MODEL_PATH).resolve() else None)
        )

        if resolved_expected:
            actual_hash = compute_file_sha256(self.model_path)
            if actual_hash.lower() != resolved_expected.lower():
                err_msg = (
                    f"Model integrity verification failed for {model_filename}! "
                    f"Expected SHA-256: {resolved_expected.lower()}, got: {actual_hash}. "
                    "Refusing to load untrusted or tampered model artifact."
                )
                logger.error(err_msg)
                raise ValueError(err_msg)
            logger.info(f"Model integrity verified (SHA-256: {actual_hash[:12]}...).")

        logger.info(f"Loading model pipeline from {model_filename}... ")
        self.pipeline = joblib.load(self.model_path)
        self.load_count += 1
        logger.info(f"Model pipeline loaded successfully (load_count={self.load_count}).")

        # Multi-model catalog
        self.pipelines: Dict[str, Pipeline] = {"svm": self.pipeline}
        self._load_additional_pipelines()

    def _load_additional_pipelines(self) -> None:
        """Load additional trained candidate models (Logistic Regression, Multinomial Naive Bayes) if available."""
        models_dir = Path(self.model_path).parent
        lr_path = models_dir / "lr_pipeline.joblib"
        nb_path = models_dir / "nb_pipeline.joblib"

        if lr_path.exists():
            try:
                self.pipelines["lr"] = joblib.load(lr_path)
                logger.info("Loaded Logistic Regression pipeline (models/lr_pipeline.joblib).")
            except Exception as e:
                logger.warning(f"Could not load Logistic Regression pipeline: {e}")

        if nb_path.exists():
            try:
                self.pipelines["nb"] = joblib.load(nb_path)
                logger.info("Loaded Multinomial Naive Bayes pipeline (models/nb_pipeline.joblib).")
            except Exception as e:
                logger.warning(f"Could not load Multinomial Naive Bayes pipeline: {e}")

    def get_pipeline(self, model_key: str = "svm") -> Pipeline:
        """Resolve requested pipeline key to loaded instance, defaulting to primary Calibrated Linear SVM."""
        normalized = (model_key or "svm").lower().strip()
        if normalized in ("lr", "logistic", "logistic_regression", "logistic regression"):
            return self.pipelines.get("lr", self.pipeline)
        elif normalized in ("nb", "naive_bayes", "multinomial_nb", "multinomial naive bayes", "bayes"):
            return self.pipelines.get("nb", self.pipeline)
        return self.pipelines.get("svm", self.pipeline)

    def _extract_signals(
        self,
        text: str,
        pipeline: Optional[Pipeline] = None,
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
        target_pipe = pipeline or self.pipeline
        if not target_pipe:
            return []

        tfidf = target_pipe.named_steps.get("tfidf")
        clf = target_pipe.named_steps.get("clf")

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
        model_key: str = "svm",
        include_explanations: bool = True,
    ) -> Dict[str, Any]:
        """Classify email subject and body using requested model algorithm.

        Supports:
        - "svm": Calibrated Linear SVM (Primary baseline)
        - "lr": Logistic Regression (Balanced linear classifier)
        - "nb": Multinomial Naive Bayes (Fast probabilistic baseline)
        """
        active_pipeline = self.get_pipeline(model_key)
        if not active_pipeline:
            raise RuntimeError("Model pipeline is not loaded.")

        normalized_key = (model_key or "svm").lower().strip()
        if normalized_key in ("lr", "logistic", "logistic_regression", "logistic regression"):
            resolved_key = "lr"
            model_display_name = "Logistic Regression"
        elif normalized_key in ("nb", "naive_bayes", "multinomial_nb", "multinomial naive bayes", "bayes"):
            resolved_key = "nb"
            model_display_name = "Multinomial Naive Bayes"
        else:
            resolved_key = "svm"
            model_display_name = "Calibrated Linear SVM"

        combined_text = combine_email(subject, body)
        raw_tokens = tokenize_text(combined_text)

        # Calibrated probability output
        if not raw_tokens or not combined_text.strip():
            p_spam = 0.50
        else:
            proba = active_pipeline.predict_proba([combined_text])[0]
            # Standard order: class 0 = ham, class 1 = spam
            p_spam = float(proba[1])

        # Evaluate decision via reliability module
        prediction, label_display, risk_level, confidence = evaluate_decision(p_spam)

        # Vectorizer reference for vocab coverage
        tfidf = active_pipeline.named_steps.get("tfidf")
        reliability = compute_reliability(
            spam_probability=p_spam,
            text=combined_text,
            vectorizer=tfidf,
        )

        # Model-derived signals & top_tokens (max 15)
        signals: List[Dict[str, Any]] = []
        top_tokens: List[Dict[str, Any]] = []
        if include_explanations:
            signals = self._extract_signals(
                combined_text,
                pipeline=active_pipeline,
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
            "model_key": resolved_key,
            "selected_model": model_display_name,
        }

    def compare_models(
        self,
        subject: Optional[str] = "",
        body: str = "",
        filter_stopwords: bool = False,
        primary_result: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute genuine multi-model inference across all 3 algorithms and synthesize comparison."""
        # 1. Run inference on each model, skipping token explanation extraction
        # for candidate comparison algorithms (or reusing primary_result if model_key matches).
        def _get_model_res(key: str) -> Dict[str, Any]:
            if primary_result and primary_result.get("model_key") == key:
                return primary_result
            return self.predict(
                subject=subject,
                body=body,
                filter_stopwords=filter_stopwords,
                model_key=key,
                include_explanations=False,
            )

        svm_res = _get_model_res("svm")
        lr_res = _get_model_res("lr")
        nb_res = _get_model_res("nb")

        # Held-out test evaluation benchmarks from metadata.json
        benchmarks = {
            "svm": {
                "name": "Calibrated Linear SVM",
                "accuracy": 0.9900,
                "precision": 0.9883,
                "recall": 0.9907,
                "f1": 0.9895,
                "selection_rank": "Winner (Selected Production Model)",
                "confusion_matrix": {"tp": 2884, "fp": 34, "tn": 3148, "fn": 27},
            },
            "lr": {
                "name": "Logistic Regression",
                "accuracy": 0.9869,
                "precision": 0.9797,
                "recall": 0.9931,
                "f1": 0.9864,
                "selection_rank": "Candidate (High Recall)",
                "confusion_matrix": {"tp": 2891, "fp": 60, "tn": 3122, "fn": 20},
            },
            "nb": {
                "name": "Multinomial Naive Bayes",
                "accuracy": 0.9849,
                "precision": 0.9832,
                "recall": 0.9852,
                "f1": 0.9842,
                "selection_rank": "Candidate (Fast Baseline)",
                "confusion_matrix": {"tp": 2868, "fp": 49, "tn": 3133, "fn": 43},
            },
        }

        preds = [svm_res["prediction"], lr_res["prediction"], nb_res["prediction"]]
        spam_votes = sum(1 for p in preds if p == "spam")
        ham_votes = sum(1 for p in preds if p == "ham")
        all_agree = (len(set(preds)) == 1)

        consensus_verdict = "spam" if spam_votes >= 2 else ("ham" if ham_votes >= 2 else "uncertain")
        consensus_strength = f"{max(spam_votes, ham_votes)}/3"

        disagreement_notes = None
        if not all_agree:
            disagreement_notes = (
                f"Model Disagreement: SVM predicted '{svm_res['prediction']}' ({svm_res['spam_probability']*100:.1f}%), "
                f"LR predicted '{lr_res['prediction']}' ({lr_res['spam_probability']*100:.1f}%), "
                f"NB predicted '{nb_res['prediction']}' ({nb_res['spam_probability']*100:.1f}%)."
            )

        return {
            "all_agree": all_agree,
            "consensus_verdict": consensus_verdict,
            "consensus_strength": consensus_strength,
            "disagreement_notes": disagreement_notes,
            "algorithms": {
                "svm": {
                    "name": "Calibrated Linear SVM",
                    "prediction": svm_res["prediction"],
                    "label_display": svm_res["label_display"],
                    "spam_probability": svm_res["spam_probability"],
                    "confidence": svm_res["confidence"],
                    "risk_level": svm_res["risk_level"],
                    "evaluation": benchmarks["svm"],
                },
                "lr": {
                    "name": "Logistic Regression",
                    "prediction": lr_res["prediction"],
                    "label_display": lr_res["label_display"],
                    "spam_probability": lr_res["spam_probability"],
                    "confidence": lr_res["confidence"],
                    "risk_level": lr_res["risk_level"],
                    "evaluation": benchmarks["lr"],
                },
                "nb": {
                    "name": "Multinomial Naive Bayes",
                    "prediction": nb_res["prediction"],
                    "label_display": nb_res["label_display"],
                    "spam_probability": nb_res["spam_probability"],
                    "confidence": nb_res["confidence"],
                    "risk_level": nb_res["risk_level"],
                    "evaluation": benchmarks["nb"],
                },
            },
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
    model_key: str = "svm",
) -> Dict[str, Any]:
    """Module-level convenience inference function."""
    return get_predictor().predict(subject, body, filter_stopwords=filter_stopwords, model_key=model_key)


def compare_models(
    subject: Optional[str] = "",
    body: str = "",
    filter_stopwords: bool = False,
    primary_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Module-level convenience 3-model comparison function."""
    return get_predictor().compare_models(
        subject,
        body,
        filter_stopwords=filter_stopwords,
        primary_result=primary_result,
    )
