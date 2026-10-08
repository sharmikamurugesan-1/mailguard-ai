"""Email text preprocessing and normalization transformer.

Phase 4: Shared Preprocessing & Pipeline Construction
- Single shared cleaning function: clean_text_for_nlp(text)
  - Lowercase
  - URL normalization: __url__
  - Email normalization: __email__
  - Currency normalization: __currency__
  - Number normalization: __number__
  - HTML tag removal
  - Unicode normalization (NFKD)
  - Punctuation & whitespace normalization
- Scikit-learn compatible EmailCleanerTransformer for inclusion in Pipeline:
  preprocessing -> TfidfVectorizer -> classifier
- Used identically in both training and inference.
"""

import html
import re
import unicodedata
from typing import Any, Iterable, List, Optional, Union

import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

# Precompiled regex patterns for performance
URL_PATTERN = re.compile(
    r"(?:https?://|ftp://|www\.)[^\s/$.?#].[^\s]*",
    re.IGNORECASE
)
EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
)
CURRENCY_PATTERN = re.compile(
    r"[\$\£\€\¥]\s*\d+(?:[.,]\d+)*|\d+(?:[.,]\d+)*\s*[\$\£\€\¥]|(?:usd|eur|gbp)\s*\d+",
    re.IGNORECASE
)
NUMBER_PATTERN = re.compile(
    r"\b\d+(?:[.,]\d+)*\b"
)
HREF_PATTERN = re.compile(
    r"""<a\s+[^>]*href=["']([^"']+)["'][^>]*>""",
    re.IGNORECASE
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


def clean_text_for_nlp(text: Optional[Union[str, float]]) -> str:
    """Single shared NLP normalization function for email subject and body.

    Used identically during offline training and real-time inference.

    Handles:
    - None / NaN / non-string inputs
    - Unicode accents and compatibility characters
    - HTML entities and markup (extracts href URLs before stripping tags)
    - URLs -> __url__
    - Emails -> __email__
    - Monetary amounts -> __currency__
    - Numbers -> __number__
    - Excess punctuation and spacing
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

    # 4. Unicode normalization (NFKD + strip combining diacritic marks)
    text = "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))

    # 5. Lowercase
    text = text.lower()


    # 5. Normalization tokens for high-signal patterns
    text = URL_PATTERN.sub(" __url__ ", text)
    text = EMAIL_PATTERN.sub(" __email__ ", text)
    text = CURRENCY_PATTERN.sub(" __currency__ ", text)
    text = NUMBER_PATTERN.sub(" __number__ ", text)

    # 6. Normalize punctuation repetition (e.g. "!!!" -> "! ", "???" -> "? ")
    text = EXCESS_PUNCT_PATTERN.sub(r" \1 ", text)

    # 7. Strip non-printable / control characters while retaining valid words and tokens
    text = re.sub(r"[^\w\s_!?.,@$-]", " ", text)

    # 8. Normalize whitespace
    text = WHITESPACE_PATTERN.sub(" ", text).strip()

    return text


class EmailCleanerTransformer(BaseEstimator, TransformerMixin):
    """Scikit-learn compatible transformer that applies clean_text_for_nlp."""

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
