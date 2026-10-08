"""Tests for dataset loading, validation, cleaning, and reporting (Phase 3)."""

from pathlib import Path
import tempfile
import pandas as pd
import pytest

from src.data import (
    clean_and_format_dataset,
    load_raw_dataset,
    validate_columns,
    REQUIRED_COLUMNS,
)


@pytest.fixture
def sample_raw_dataframe():
    """Create a controlled sample DataFrame mimicking raw data."""
    return pd.DataFrame({
        "Message ID": [1, 2, 3, 4, 5, 6],
        "Subject": [
            "Project Update",
            "Urgent: Claim your prize now!",
            None,  # Only body
            "Meeting Reminder",  # Only subject
            None,  # Both null -> should be dropped
            "Project Update",  # Duplicate text with row 1
        ],
        "Message": [
            "Here is the weekly update report.",
            "Click here to win a million dollars today.",
            "Body text without subject.",
            None,
            None,  # Both null
            "Here is the weekly update report.",  # Duplicate text
        ],
        "Spam/Ham": [
            "ham",
            "spam",
            "ham",
            "ham",
            "spam",
            "ham",
        ],
    })


def test_validate_columns_success(sample_raw_dataframe):
    """Validation succeeds when all required columns are present."""
    validate_columns(sample_raw_dataframe)


def test_validate_columns_failure():
    """Validation raises ValueError when a required column is missing."""
    df_missing = pd.DataFrame({"Subject": ["Hi"], "Message": ["Hello"]})
    with pytest.raises(ValueError, match="missing required column"):
        validate_columns(df_missing)


def test_clean_and_format_dataset_handling(sample_raw_dataframe):
    """Verify null handling, deduplication, and combination format."""
    df_clean, stats = clean_and_format_dataset(sample_raw_dataframe)

    # Row 5 (both null) dropped -> initial 6 - 1 = 5
    # Row 6 (duplicate of row 1) dropped -> 5 - 1 = 4
    assert len(df_clean) == 4
    assert stats["both_null_dropped"] == 1
    assert stats["duplicates_removed"] == 1
    assert stats["n_samples"] == 4

    # Verify documented combination format
    row_1 = df_clean.iloc[0]
    assert row_1["text"] == "Subject: Project Update\n\nHere is the weekly update report."
    assert row_1["label"] == "ham"

    # Verify single nulls handled properly
    # Row with only message
    row_no_subj = df_clean[df_clean["Subject"] == ""].iloc[0]
    assert row_no_subj["text"] == "Body text without subject."

    # Row with only subject
    row_no_body = df_clean[df_clean["Message"] == ""].iloc[0]
    assert row_no_body["text"] == "Subject: Meeting Reminder"


def test_invalid_label_rejection():
    """Verify that unexpected target labels raise a ValueError."""
    df_invalid = pd.DataFrame({
        "Subject": ["Test"],
        "Message": ["Hello"],
        "Spam/Ham": ["unknown_class"],
    })
    with pytest.raises(ValueError, match="Encountered unexpected target labels"):
        clean_and_format_dataset(df_invalid)


def test_dataset_report_content_integrity():
    """Verify generated dataset report contains expected keys and honest metadata."""
    from src.config import DATASET_REPORT_JSON

    assert DATASET_REPORT_JSON.exists(), "dataset_report.json must exist"
    import json
    with open(DATASET_REPORT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["dataset_type"] == "email"
    assert data["n_samples"] == 30462
    assert data["class_counts"]["ham"] == 15910
    assert data["class_counts"]["spam"] == 14552
    assert data["duplicates_removed"] == 3203
    assert len(data["sample_rows"]) == 5
