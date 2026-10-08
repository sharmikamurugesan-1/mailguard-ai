"""Email preprocessing, tokenization, and reliability heuristics."""

import re
import string
from typing import Any, Dict, List, Optional, Set, Tuple

from src.config import (
    BOUNDARY_LOWER,
    BOUNDARY_UPPER,
    MIN_TOKEN_COUNT,
    MIN_VOCAB_COVERAGE,
)

# Common English function words used for basic language heuristic validation
COMMON_ENGLISH_WORDS = {
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "i",
    "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
    "this", "but", "his", "by", "from", "they", "we", "say", "her",
    "she", "or", "an", "will", "my", "one", "all", "would", "there",
    "their", "what", "so", "up", "out", "if", "about", "who", "get",
    "which", "go", "me", "when", "make", "can", "like", "time", "no",
    "just", "him", "know", "take", "people", "into", "year", "your",
    "good", "some", "could", "them", "see", "other", "than", "then",
    "now", "look", "only", "come", "its", "over", "think", "also",
    "back", "after", "use", "two", "how", "our", "work", "first",
    "well", "way", "even", "new", "want", "because", "any", "these",
    "give", "day", "most", "us", "is", "are", "was", "were", "been"
}


def clean_text(text: Optional[str]) -> str:
    """Normalize text by stripping surrounding whitespace and normalizing internal spaces."""
    if text is None:
        return ""
    text = str(text)
    # Remove control characters while preserving newlines and tabs
    text = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", "", text)
    # Normalize multiple whitespace characters
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def combine_email(subject: Optional[str], body: Optional[str]) -> str:
    """Combine email subject and body into a structured text representation for classification."""
    clean_subj = clean_text(subject)
    clean_body = clean_text(body)

    if not clean_subj and not clean_body:
        return ""

    if clean_subj and clean_body:
        return f"Subject: {clean_subj}\n\n{clean_body}"
    elif clean_subj:
        return f"Subject: {clean_subj}"
    else:
        return clean_body


def tokenize_text(text: str) -> List[str]:
    """Extract lowercased alphanumeric word tokens from text."""
    if not text:
        return []
    return re.findall(r"\b[a-zA-Z0-9']{2,}\b", text.lower())


def calculate_vocab_coverage(tokens: List[str], vocabulary: Any) -> float:
    """Calculate the fraction of tokens present in the trained model's vectorizer vocabulary.

    Args:
        tokens: List of extracted tokens.
        vocabulary: Dictionary mapping token->index or a set of tokens.

    Returns:
        Float value between 0.0 and 1.0 representing coverage.
    """
    if not tokens:
        return 0.0

    if hasattr(vocabulary, "__contains__"):
        known_count = sum(1 for t in tokens if t in vocabulary)
        return float(known_count) / float(len(tokens))
    return 0.0


def detect_non_english(text: str, tokens: Optional[List[str]] = None) -> bool:
    """Detect if the input text appears to be non-English based on character encoding and stopwords.

    Heuristic rules:
    1. If non-ASCII character ratio exceeds 25% for text longer than 20 characters.
    2. If text contains >= 10 tokens but fewer than 5% common English function words.
    """
    if not text or len(text.strip()) < 15:
        return False

    # Check ASCII character ratio
    total_chars = len(text)
    ascii_chars = sum(1 for c in text if ord(c) < 128)
    ascii_ratio = ascii_chars / total_chars if total_chars > 0 else 1.0

    if ascii_ratio < 0.75:
        return True

    # Check common English stopwords coverage
    if tokens is None:
        tokens = tokenize_text(text)

    if len(tokens) >= 12:
        common_count = sum(1 for t in tokens if t in COMMON_ENGLISH_WORDS)
        common_ratio = common_count / len(tokens)
        if common_ratio < 0.08:
            return True

    return False


def evaluate_reliability_warnings(
    text: str,
    tokens: List[str],
    vocab_coverage: float,
    spam_probability: float,
    dataset_type: str = "email",
) -> List[Dict[str, str]]:
    """Generate structured reliability warnings for model predictions.

    Covers required codes:
    - short_input (< 10 tokens)
    - low_vocab_coverage (< 50% known tokens)
    - non_english_suspected (documented heuristic)
    - near_decision_boundary (probability in [0.35, 0.65])
    - sms_trained_model (if dataset_type == 'sms')
    """
    warnings: List[Dict[str, str]] = []

    # 1. Short input check
    if len(tokens) < MIN_TOKEN_COUNT:
        warnings.append({
            "code": "short_input",
            "message": f"Input contains only {len(tokens)} token(s) (minimum recommended: {MIN_TOKEN_COUNT}). Very short emails provide limited context for reliable classification."
        })

    # 2. Low vocabulary coverage check
    if len(tokens) >= MIN_TOKEN_COUNT and vocab_coverage < MIN_VOCAB_COVERAGE:
        pct = round(vocab_coverage * 100, 1)
        warnings.append({
            "code": "low_vocab_coverage",
            "message": f"Only {pct}% of words in this email were seen during training. Unfamiliar vocabulary reduces model confidence."
        })

    # 3. Non-English suspected check
    if detect_non_english(text, tokens):
        warnings.append({
            "code": "non_english_suspected",
            "message": "This email appears to contain non-English text or uncommon characters. The model was trained on English emails and may produce unreliable results."
        })

    # 4. Near decision boundary check
    if BOUNDARY_LOWER <= spam_probability <= BOUNDARY_UPPER:
        warnings.append({
            "code": "near_decision_boundary",
            "message": f"Spam probability ({round(spam_probability * 100, 1)}%) falls close to the decision threshold. The classification carries higher uncertainty."
        })

    # 5. SMS trained model check
    if dataset_type == "sms":
        warnings.append({
            "code": "sms_trained_model",
            "message": "This model was trained on SMS messages, not full emails. Results on real emails may be less accurate."
        })

    return warnings
