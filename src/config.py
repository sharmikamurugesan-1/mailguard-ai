"""Configuration settings for MailGuard AI.

Follows locked decisions:
- Cross-platform paths only (pathlib.Path).
- Config via environment variables.
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_PATH = Path(os.getenv("RAW_DATA_PATH", str(DATA_DIR / "raw" / "enron_spam_data.csv")))
PROCESSED_DATA_PATH = Path(os.getenv("PROCESSED_DATA_PATH", str(DATA_DIR / "processed" / "cleaned_emails.csv")))
MODELS_DIR = BASE_DIR / "models"
MODEL_PATH = Path(os.getenv("MODEL_PATH", str(MODELS_DIR / "spam_pipeline.joblib")))
METADATA_PATH = Path(os.getenv("METADATA_PATH", str(MODELS_DIR / "metadata.json")))
REPORTS_DIR = BASE_DIR / "reports"
DATASET_REPORT_JSON = REPORTS_DIR / "dataset_report.json"
DATASET_REPORT_MD = REPORTS_DIR / "dataset_report.md"
MODEL_COMPARISON_JSON = REPORTS_DIR / "model_comparison.json"
MODEL_COMPARISON_MD = REPORTS_DIR / "model_comparison.md"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"


# Classification & Uncertain Band Thresholds
# If P(spam) in [UNCERTAIN_LOWER, UNCERTAIN_UPPER], classify as "uncertain"
UNCERTAIN_LOWER = float(os.getenv("UNCERTAIN_LOWER", "0.40"))
UNCERTAIN_UPPER = float(os.getenv("UNCERTAIN_UPPER", "0.60"))

# Decision Boundary Warning Range
BOUNDARY_LOWER = float(os.getenv("BOUNDARY_LOWER", "0.35"))
BOUNDARY_UPPER = float(os.getenv("BOUNDARY_UPPER", "0.65"))

# Reliability Heuristic Thresholds
MIN_TOKEN_COUNT = int(os.getenv("MIN_TOKEN_COUNT", "10"))
MIN_VOCAB_COVERAGE = float(os.getenv("MIN_VOCAB_COVERAGE", "0.50"))

# Server & Security Settings
HOST = os.getenv("HOST", "0.0.0.0")  # nosec B104
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")
MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(2 * 1024 * 1024)))  # 2 MB payload limit
MAX_INPUT_CHARS = int(os.getenv("MAX_INPUT_CHARS", "20000"))  # 20k characters text limit

# Model Integrity (SHA-256)
MODEL_EXPECTED_SHA256 = os.getenv(
    "MODEL_EXPECTED_SHA256",
    "453414c9bb3889c1cc2402ee26473e6d74bf7e7a78cef26eac24da2d8ddfc9f8",
)


