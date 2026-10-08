"""Compatibility shim re-exporting unified preprocessing from src.preprocessing."""

from src.preprocessing import (
    COMMON_ENGLISH_WORDS,
    EmailCleanerTransformer,
    calculate_vocab_coverage,
    clean_text_for_nlp,
    clean_text_for_nlp as clean_text,
    combine_email,
    detect_non_english,
    evaluate_reliability_warnings,
    tokenize_text,
)

__all__ = [
    "COMMON_ENGLISH_WORDS",
    "EmailCleanerTransformer",
    "calculate_vocab_coverage",
    "clean_text",
    "clean_text_for_nlp",
    "combine_email",
    "detect_non_english",
    "evaluate_reliability_warnings",
    "tokenize_text",
]
