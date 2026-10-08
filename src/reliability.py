"""Pure reliability analysis and decision boundaries for MailGuard AI.

Phase 6: Pure functions, zero Flask imports, fully unit-testable.
Evaluates prediction uncertainty, reliability levels, and warning signals.

Reliability Level Rule:
- 'high': Input has adequate token context, normal vocabulary coverage, English text,
          and a decisive prediction (only the persistent 'dataset_age_notice' is present).
- 'medium': Exactly one data-specific warning is triggered (e.g., 'near_decision_boundary'
            OR 'short_input').
- 'low': Two or more data-specific warnings are triggered (e.g., 'short_input' AND
         'low_vocab_coverage', or 'non_english_suspected'), indicating significantly reduced confidence.

No label ever contains 'safe' or '100%'.
"""

import os
import re
from typing import Any, Dict, List, Optional, Set, Tuple

# Environment Variable Configurations with Defaults from Validation Tuning
def get_uncertain_low() -> float:
    return float(os.getenv("UNCERTAIN_LOW", "0.40"))


def get_uncertain_high() -> float:
    return float(os.getenv("UNCERTAIN_HIGH", "0.60"))


def get_short_input_min_tokens() -> int:
    return int(os.getenv("SHORT_INPUT_MIN_TOKENS", "10"))


def get_vocab_coverage_min() -> float:
    return float(os.getenv("VOCAB_COVERAGE_MIN", "0.50"))


def get_non_ascii_threshold() -> float:
    return float(os.getenv("NON_ASCII_THRESHOLD", "0.25"))


def tokenize_clean_tokens(text: str) -> List[str]:
    """Extract lowercased word tokens from text."""
    if not text:
        return []
    return re.findall(r"\b[a-zA-Z0-9']{2,}\b", text.lower())


def calculate_vocabulary_coverage(tokens: List[str], vectorizer: Any) -> float:
    """Calculate the percentage of tokens present in the vectorizer vocabulary."""
    if not tokens:
        return 0.0

    if vectorizer is None:
        return 1.0

    vocab = getattr(vectorizer, "vocabulary_", None)
    if not vocab:
        return 1.0

    known = sum(1 for t in tokens if t in vocab)
    return float(known) / float(len(tokens))


def check_non_english(text: str, threshold: Optional[float] = None) -> bool:
    """Check if text has an excessive share of non-ASCII characters."""
    if not text or len(text.strip()) < 15:
        return False

    limit = threshold if threshold is not None else get_non_ascii_threshold()
    total_chars = len(text)
    ascii_chars = sum(1 for c in text if ord(c) < 128)
    non_ascii_share = (total_chars - ascii_chars) / total_chars

    return non_ascii_share > limit


def evaluate_decision(spam_probability: float) -> Tuple[str, str, str, float]:
    """Map calibrated spam probability to prediction category, user-facing label, and risk level.

    Returns:
        (prediction, label_display, risk_level, confidence)
    """
    unc_low = get_uncertain_low()
    unc_high = get_uncertain_high()

    p_spam = float(spam_probability)
    p_ham = 1.0 - p_spam

    if unc_low <= p_spam <= unc_high:
        prediction = "uncertain"
        label_display = "Needs review"
        risk_level = "medium"
        confidence = round(max(p_spam, p_ham), 4)
    elif p_spam > unc_high:
        prediction = "spam"
        label_display = "Likely spam"
        risk_level = "high"
        confidence = round(p_spam, 4)
    else:
        prediction = "ham"
        label_display = "Likely legitimate"
        risk_level = "low"
        confidence = round(p_ham, 4)

    return prediction, label_display, risk_level, confidence


def compute_reliability(
    spam_probability: float,
    text: str,
    vectorizer: Any = None,
) -> Dict[str, Any]:
    """Compute reliability assessment, warnings list, and reliability level.

    Warning codes:
    - near_decision_boundary: probability in [0.35, 0.65]
    - short_input: fewer than SHORT_INPUT_MIN_TOKENS (10)
    - low_vocab_coverage: less than VOCAB_COVERAGE_MIN (50%) of tokens known
    - non_english_suspected: share of non-ASCII characters exceeds threshold
    - dataset_age_notice: persistent notice regarding Enron-era training data
    """
    warnings: List[str] = []
    tokens = tokenize_clean_tokens(text)
    n_tokens = len(tokens)

    # 1. Near decision boundary check
    if 0.35 <= spam_probability <= 0.65:
        warnings.append("near_decision_boundary")

    # 2. Short input check
    min_tokens = get_short_input_min_tokens()
    if n_tokens < min_tokens:
        warnings.append("short_input")

    # 3. Low vocab coverage check
    cov_min = get_vocab_coverage_min()
    vocab_coverage = calculate_vocabulary_coverage(tokens, vectorizer)
    if n_tokens >= min_tokens and vocab_coverage < cov_min:
        warnings.append("low_vocab_coverage")

    # 4. Non-English suspected check
    if check_non_english(text):
        warnings.append("non_english_suspected")

    # 5. Dataset age notice (always present for this Enron-trained model)
    warnings.append("dataset_age_notice")

    # Compute reliability level based on count of data-specific warnings
    # (excluding the permanent baseline dataset_age_notice)
    data_warnings_count = len(warnings) - 1

    if data_warnings_count == 0:
        level = "high"
    elif data_warnings_count == 1:
        level = "medium"
    else:
        level = "low"

    return {
        "level": level,
        "warnings": warnings,
        "token_count": n_tokens,
        "vocab_coverage": round(vocab_coverage, 4),
    }
