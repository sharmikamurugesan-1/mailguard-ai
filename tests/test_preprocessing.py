"""Tests for text preprocessing, normalization, and transformer (Phase 4)."""

import pandas as pd
import pytest

from src.preprocessing import EmailCleanerTransformer, clean_text_for_nlp


def test_empty_and_null_inputs():
    """Verify that empty, None, and whitespace-only inputs return empty string."""
    assert clean_text_for_nlp(None) == ""
    assert clean_text_for_nlp("") == ""
    assert clean_text_for_nlp("   \n\t  ") == ""


def test_unicode_normalization():
    """Verify that unicode characters and accents are normalized properly."""
    input_text = "Café résumé naïve Über Groß"
    cleaned = clean_text_for_nlp(input_text)
    # NFKD decomposes accents and lowercases
    assert "cafe" in cleaned
    assert "resume" in cleaned
    assert "naive" in cleaned


def test_html_like_text():
    """Verify that HTML entities and tags are stripped and unescaped."""
    html_text = "<p>Congratulations! You &amp; your team won! Click <a href='http://win.example.com/gift'>HERE</a>!</p>"
    cleaned = clean_text_for_nlp(html_text)

    # HTML tags should be removed
    assert "<p>" not in cleaned
    assert "</a>" not in cleaned
    # Entity &amp; unescaped to &
    assert "&" in cleaned or "and" in cleaned or "team" in cleaned
    # URL normalized
    assert "__url__" in cleaned


def test_very_long_text():
    """Verify that very long inputs are handled safely without errors or timeouts."""
    repeated_paragraph = "Urgent: Security verification required for account update. Please verify at http://auth.bank.com. "
    long_text = repeated_paragraph * 2000  # ~200,000 characters
    cleaned = clean_text_for_nlp(long_text)

    assert len(cleaned) > 0
    assert "__url__" in cleaned
    assert "urgent" in cleaned
    assert "security verification" in cleaned


def test_token_normalizations():
    """Verify normalization of URLs, emails, currencies, and numbers."""
    text = (
        "Contact support@company.org or visit https://portal.example.com/login "
        "to claim your $5,000 prize or 250 USD reward within 48 hours."
    )
    cleaned = clean_text_for_nlp(text)

    assert "__email__" in cleaned
    assert "__url__" in cleaned
    assert "__currency__" in cleaned
    assert "__number__" in cleaned
    assert "support@company.org" not in cleaned
    assert "https://portal.example.com" not in cleaned


def test_email_cleaner_transformer():
    """Verify that EmailCleanerTransformer conforms to the scikit-learn transformer API."""
    transformer = EmailCleanerTransformer()
    # Fit returns self
    assert transformer.fit(["sample"]) is transformer

    # Transform list of strings
    raw_texts = [
        "Email 1 with http://test.com",
        "Email 2 with $100 price",
    ]
    transformed = transformer.transform(raw_texts)
    assert len(transformed) == 2
    assert "__url__" in transformed[0]
    assert "__currency__" in transformed[1]

    # Transform Pandas Series
    series = pd.Series(raw_texts)
    transformed_series = transformer.transform(series)
    assert len(transformed_series) == 2
    assert "__url__" in transformed_series[0]
