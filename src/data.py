"""Data loading, validation, cleaning, and reporting module for MailGuard AI.

Phase 3: Dataset Discovery + Validation
- Load raw data and validate required columns.
- Handle missing values and drop empty text records.
- Deduplicate email texts to prevent data leakage.
- Map labels to canonical 'spam' and 'ham'.
- Combine subject + body in ONE documented format: 'Subject: {subject}\\n\\n{body}'.
- Save cleaned dataset to data/processed/.
- Generate reports/dataset_report.json and reports/dataset_report.md.
"""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.config import (
    DATASET_REPORT_JSON,
    DATASET_REPORT_MD,
    PROCESSED_DATA_PATH,
    RAW_DATA_PATH,
    REPORTS_DIR,
)
from src.preprocess import combine_email, tokenize_text

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MailGuard-Data")

REQUIRED_COLUMNS = ["Subject", "Message", "Spam/Ham"]
DOCUMENTED_COMBINE_FORMAT = "Subject: {clean_subject}\\n\\n{clean_body}"


def validate_columns(df: pd.DataFrame) -> None:
    """Validate that the dataset contains all required columns."""
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(
            f"Dataset is missing required column(s): {missing}. "
            f"Expected columns: {REQUIRED_COLUMNS}, found: {list(df.columns)}"
        )


def load_raw_dataset(csv_path: Path = RAW_DATA_PATH) -> pd.DataFrame:
    """Load raw dataset from CSV and check existence and structure."""
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Raw dataset file not found at {csv_path}. "
            "Please refer to data/README.md for download instructions."
        )
    df = pd.read_csv(csv_path)
    validate_columns(df)
    return df


def clean_and_format_dataset(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Clean, validate, deduplicate, and format raw email records."""
    validate_columns(df)
    initial_rows = len(df)

    # 1. Null audit
    null_counts = {col: int(df[col].isnull().sum()) for col in df.columns}
    both_null_mask = df["Subject"].isnull() & df["Message"].isnull()
    both_null_count = int(both_null_mask.sum())

    # Drop rows where both Subject and Message are missing
    df_clean = df[~both_null_mask].copy()

    # Fill NA for text fields
    df_clean["Subject"] = df_clean["Subject"].fillna("")
    df_clean["Message"] = df_clean["Message"].fillna("")

    # 2. Map and validate labels
    df_clean["label"] = df_clean["Spam/Ham"].astype(str).str.strip().str.lower()
    invalid_labels = set(df_clean["label"].unique()) - {"spam", "ham"}
    if invalid_labels:
        raise ValueError(f"Encountered unexpected target labels: {invalid_labels}")

    # 3. Combine subject + body in ONE documented format
    df_clean["text"] = [
        combine_email(s, m) for s, m in zip(df_clean["Subject"], df_clean["Message"])
    ]

    # Filter out empty texts
    df_clean = df_clean[df_clean["text"].str.strip().str.len() > 0].copy()

    # 4. Remove exact duplicate texts
    duplicates_count = int(df_clean.duplicated(subset=["text"]).sum())
    df_clean = df_clean.drop_duplicates(subset=["text"]).reset_index(drop=True)

    # 5. Calculate metrics
    ham_count = int((df_clean["label"] == "ham").sum())
    spam_count = int((df_clean["label"] == "spam").sum())
    total_samples = len(df_clean)

    avg_chars = float(round(df_clean["text"].str.len().mean(), 2)) if total_samples > 0 else 0.0
    token_counts = [len(tokenize_text(t)) for t in df_clean["text"]]
    avg_tokens = float(round(sum(token_counts) / len(token_counts), 2)) if token_counts else 0.0

    # 5 short sample rows
    samples: List[Dict[str, Any]] = []
    for i, row in df_clean.head(5).iterrows():
        subj_snip = str(row["Subject"])[:40]
        body_snip = str(row["Message"])[:60].replace("\n", " ").strip()
        samples.append({
            "index": int(i),
            "label": str(row["label"]),
            "subject_snippet": subj_snip,
            "body_snippet": body_snip,
        })

    audit_stats: Dict[str, Any] = {
        "dataset_name": "Enron Spam Dataset",
        "dataset_source_url": "https://github.com/MWiechmann/enron_spam_data",
        "dataset_license": "GPL-3.0 / Public Domain (CALO Enron Corpus)",
        "dataset_type": "email",
        "combination_format": DOCUMENTED_COMBINE_FORMAT,
        "retrieved_date": "2026-10-06",
        "initial_rows": initial_rows,
        "null_counts_raw": null_counts,
        "both_null_dropped": both_null_count,
        "duplicates_removed": duplicates_count,
        "n_samples": total_samples,
        "class_counts": {"ham": ham_count, "spam": spam_count},
        "class_proportions": {
            "ham": round(ham_count / total_samples, 4) if total_samples else 0.0,
            "spam": round(spam_count / total_samples, 4) if total_samples else 0.0,
        },
        "average_text_length_chars": avg_chars,
        "average_tokens_per_sample": avg_tokens,
        "sample_rows": samples,
    }

    # Select clean columns
    columns_to_keep = ["text", "label", "Subject", "Message"]
    if "Date" in df_clean.columns:
        columns_to_keep.append("Date")
    if "Message ID" in df_clean.columns:
        columns_to_keep.append("Message ID")

    df_result = df_clean[columns_to_keep].copy()
    return df_result, audit_stats


def save_processed_dataset(df: pd.DataFrame, output_path: Path = PROCESSED_DATA_PATH) -> None:
    """Save cleaned dataset to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved processed dataset ({len(df)} rows) to {output_path}")


def generate_reports(stats: Dict[str, Any]) -> None:
    """Write dataset validation reports to JSON and Markdown formats."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. JSON Report
    with open(DATASET_REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Saved JSON dataset report to {DATASET_REPORT_JSON}")

    # 2. Markdown Report
    samples_table = "| Index | Label | Subject Snippet | Body Snippet |\n|---|---|---|---|\n"
    for s in stats["sample_rows"]:
        samples_table += f"| {s['index']} | `{s['label']}` | {s['subject_snippet']} | {s['body_snippet']} |\n"

    md_content = f"""# Dataset Discovery & Validation Report

## Overview
- **Dataset Name**: {stats['dataset_name']}
- **Source URL**: [{stats['dataset_source_url']}]({stats['dataset_source_url']})
- **License**: {stats['dataset_license']}
- **Dataset Type**: `{stats['dataset_type']}` (real emails with separate subject and body)
- **Retrieved Date**: {stats['retrieved_date']}
- **Combination Format**: `{stats['combination_format']}`

## Cleaning Audit & Sample Counts
- **Initial Raw Rows**: {stats['initial_rows']:,}
- **Both Null Dropped**: {stats['both_null_dropped']:,}
- **Duplicates Removed**: {stats['duplicates_removed']:,}
- **Cleaned Total Samples (`n_samples`)**: {stats['n_samples']:,}

## Class Distribution
- **Ham (legitimate)**: {stats['class_counts']['ham']:,} ({stats['class_proportions']['ham']*100:.2f}%)
- **Spam**: {stats['class_counts']['spam']:,} ({stats['class_proportions']['spam']*100:.2f}%)

## Text Characteristics
- **Average Character Length**: {stats['average_text_length_chars']} chars
- **Average Token Count**: {stats['average_tokens_per_sample']} tokens

## Sample Records (First 5)
{samples_table}

## Verification Status
- Validated column integrity: `['Subject', 'Message', 'Spam/Ham']` present.
- Label mapping confirmed: only `spam` and `ham` classes exist.
- De-duplication complete: exact duplicate texts removed to avoid leakage.
"""
    with open(DATASET_REPORT_MD, "w", encoding="utf-8") as f:
        f.write(md_content)
    logger.info(f"Saved Markdown dataset report to {DATASET_REPORT_MD}")


def process_and_report_dataset() -> Dict[str, Any]:
    """Execute complete dataset loading, validation, saving, and reporting pipeline."""
    df_raw = load_raw_dataset(RAW_DATA_PATH)
    df_clean, stats = clean_and_format_dataset(df_raw)
    save_processed_dataset(df_clean, PROCESSED_DATA_PATH)
    generate_reports(stats)
    return stats


if __name__ == "__main__":
    stats = process_and_report_dataset()
    print("=" * 80)
    print("DATASET VALIDATION & PROCESSING COMPLETE")
    print(f"Dataset Type: {stats['dataset_type']}")
    print(f"Total Samples (n_samples): {stats['n_samples']}")
    print(f"Class Counts: Ham={stats['class_counts']['ham']}, Spam={stats['class_counts']['spam']}")
    print(f"Duplicates Removed: {stats['duplicates_removed']}")
    print(f"Average Text Length: {stats['average_text_length_chars']} chars ({stats['average_tokens_per_sample']} tokens)")
    print(f"Cleaned CSV: {PROCESSED_DATA_PATH}")
    print(f"Reports: {DATASET_REPORT_JSON} and {DATASET_REPORT_MD}")
    print("=" * 80)
