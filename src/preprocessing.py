"""Unified email text preprocessing, normalization, tokenization, and reliability heuristics.

Shared across offline training and real-time inference.
NOTE (Language Orientation):
Preprocessing is English-oriented. Stripping combining diacritic marks decomposes accents
in Latin scripts (e.g., 'café' -> 'cafe', 'résumé' -> 'resume'), but will alter or distort
scripts that rely fundamentally on combining characters (e.g., Arabic, Devanagari, Hebrew).
Such inputs are flagged by the non_english_suspected reliability heuristic.
"""

import html
import re
from typing import Any, Dict, Iterable, List, Optional, Set, Union
import unicodedata

import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

from src.config import (
    BOUNDARY_LOWER,
    BOUNDARY_UPPER,
    MIN_TOKEN_COUNT,
    MIN_VOCAB_COVERAGE,
)

# Precompiled regex patterns for performance
URL_PATTERN = re.compile(
    r"(?:https?://|ftp://|www\.)[^\s/$.?#].[^\s]*",
    re.IGNORECASE,
)
EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
)
CURRENCY_PATTERN = re.compile(
    r"[\$\£\€\¥]\s*\d+(?:[.,]\d+)*|\d+(?:[.,]\d+)*\s*[\$\£\€\¥]|(?:usd|eur|gbp)\s*\d+",
    re.IGNORECASE,
)
NUMBER_PATTERN = re.compile(
    r"\b\d+(?:[.,]\d+)*\b"
)
HREF_PATTERN = re.compile(
    r"""<a\s+[^>]*href=["']([^"']+)["'][^>]*>""",
    re.IGNORECASE,
)
HTML_TAG_PATTERN = re.compile(
    r"<[^>]+>"
)
EXCESS_PUNCT_PATTERN = re.compile(
    r"([!?,.:;])\1+"
)
WHITESPACE_PATTERN = re.compile(
    r"\s+"
)

# Common English function words used for basic language heuristic validation
COMMON_ENGLISH_WORDS: Set[str] = {
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


def clean_text_for_nlp(text: Optional[Union[str, float]]) -> str:
    """Single shared NLP normalization function for email subject and body.

    Handles:
    - None / NaN / non-string inputs
    - Unicode accents and compatibility characters (NFKD decomposition + combining mark stripping)
    - HTML entities and markup (extracts href URLs before stripping tags)
    - URLs -> __url__
    - Emails -> __email__
    - Monetary amounts -> __currency__
    - Numbers -> __number__
    - Excess punctuation and whitespace normalization
    """
    if text is None:
        return ""

    if not isinstance(text, str):
        text = str(text)

    if not text.strip():
        return ""

    # 1. Unescape HTML entities (e.g., &amp;, &lt;, &gt;)
    text = html.unescape(text)

    # 2. Extract link URLs from HTML anchor tags before stripping other tags
    text = HREF_PATTERN.sub(r" \1 ", text)

    # 3. Strip remaining HTML tags
    text = HTML_TAG_PATTERN.sub(" ", text)

    # 4. Unicode normalization: NFKD decomposition + strip combining diacritic marks.
    # NOTE: This is English/Latin oriented. Accented Latin characters (café -> cafe)
    # are normalized, while non-Latin scripts using combining marks will be flagged
    # by the non-English heuristic.
    text = "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))

    # 5. Lowercase
    text = text.lower()

    # 6. Normalization tokens for high-signal patterns
    text = URL_PATTERN.sub(" __url__ ", text)
    text = EMAIL_PATTERN.sub(" __email__ ", text)
    text = CURRENCY_PATTERN.sub(" __currency__ ", text)
    text = NUMBER_PATTERN.sub(" __number__ ", text)

    # 7. Normalize punctuation repetition (e.g. "!!!" -> "! ", "???" -> "? ")
    text = EXCESS_PUNCT_PATTERN.sub(r" \1 ", text)

    # 8. Strip non-printable / control characters while retaining valid words and tokens
    text = re.sub(r"[^\w\s_!?.,@$-]", " ", text)

    # 9. Normalize whitespace
    text = WHITESPACE_PATTERN.sub(" ", text).strip()

    return text


def combine_email(subject: Optional[str], body: Optional[str]) -> str:
    """Combine email subject and body into a structured text representation for classification."""
    subj_str = str(subject).strip() if subject is not None else ""
    body_str = str(body).strip() if body is not None else ""

    if not subj_str and not body_str:
        return ""

    if subj_str and body_str:
        return f"Subject: {subj_str}\n\n{body_str}"
    elif subj_str:
        return f"Subject: {subj_str}"
    else:
        return body_str


def tokenize_text(text: str) -> List[str]:
    """Extract lowercased alphanumeric word tokens from text."""
    if not text:
        return []
    return re.findall(r"\b[a-zA-Z0-9']{2,}\b", text.lower())


def calculate_vocab_coverage(tokens: List[str], vocabulary: Any) -> float:
    """Calculate the fraction of tokens present in the trained model's vectorizer vocabulary."""
    if not tokens:
        return 0.0

    if hasattr(vocabulary, "__contains__"):
        known_count = sum(1 for t in tokens if t in vocabulary)
        return float(known_count) / float(len(tokens))
    return 0.0


def detect_non_english(text: str, tokens: Optional[List[str]] = None) -> bool:
    """Detect if the input text appears to be non-English based on character encoding and stopwords.

    Heuristics:
    1. If non-ASCII character ratio exceeds 25% for text longer than 15 characters.
    2. If text contains >= 12 tokens but fewer than 8% common English function words.
    """
    if not text or len(text.strip()) < 15:
        return False

    total_chars = len(text)
    ascii_chars = sum(1 for c in text if ord(c) < 128)
    ascii_ratio = ascii_chars / total_chars if total_chars > 0 else 1.0

    if ascii_ratio < 0.75:
        return True

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
    """Generate structured reliability warnings for model predictions."""
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


class EmailCleanerTransformer(BaseEstimator, TransformerMixin):
    """Scikit-learn compatible transformer applying clean_text_for_nlp."""

    def __init__(self):
        pass

    def fit(self, X: Any, y: Optional[Any] = None) -> "EmailCleanerTransformer":
        """No-op fit for stateless text normalization."""
        return self

    def transform(self, X: Iterable[Any]) -> List[str]:
        """Apply clean_text_for_nlp across input collection."""
        if isinstance(X, (pd.Series, pd.Index)):
            return [clean_text_for_nlp(val) for val in X]
        if isinstance(X, str):
            return [clean_text_for_nlp(X)]
        return [clean_text_for_nlp(val) for val in X]
