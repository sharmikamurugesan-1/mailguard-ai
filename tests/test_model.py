"""Tests for ML model loading, predictions, metadata, and subprocess isolation (Phase 5)."""

import json
from pathlib import Path
import subprocess
import sys
import pytest
import sklearn

from src.config import METADATA_PATH, MODEL_EXPECTED_SHA256, MODEL_PATH
from src.predictor import SpamPredictor, compute_file_sha256, get_predictor, predict


def test_model_artifact_exists_and_loads():
    """Verify that model artifact exists and can be loaded via SpamPredictor."""
    predictor = SpamPredictor()
    assert predictor.pipeline is not None
    assert "preprocess" in predictor.pipeline.named_steps
    assert "tfidf" in predictor.pipeline.named_steps
    assert "clf" in predictor.pipeline.named_steps


def test_realistic_spam_prediction():
    """Realistic spam email should be classified as spam with high confidence."""
    subject = "URGENT: Your PayPal account has been restricted"
    body = (
        "Dear valued customer, unauthorized activity was detected on your account. "
        "Please click http://paypal-security-verification.com/login immediately to verify your identity and restore access."
    )
    res = predict(subject, body)
    assert res["prediction"] == "spam"
    assert res["label"] in ("Likely spam", "Likely Spam")
    assert res["spam_probability"] >= 0.80
    assert res["risk_level"] == "high"
    assert not res["is_uncertain"]


def test_realistic_ham_prediction():
    """Realistic ham email should be classified as ham with 'Likely legitimate' label (never 'safe')."""
    subject = "Engineering team weekly sync - Agenda & Notes"
    body = (
        "Hi team, attached is the agenda for tomorrow's standup meeting. "
        "We will review the Q3 roadmap, API refactor milestones, and the upcoming staging release. Please update your tickets before 10 AM."
    )
    res = predict(subject, body)
    assert res["prediction"] == "ham"
    assert res["label"] == "Likely legitimate"
    assert res["spam_probability"] <= 0.40
    assert res["risk_level"] == "low"
    assert "safe" not in res["label"].lower()  # Rule L3: Never say safe!


def test_fresh_process_load_works():
    """Verify that model loading and inference succeed in a completely fresh, isolated Python process."""
    code = """
import sys
from src.predictor import predict

res = predict("Meeting tomorrow", "Let's meet at 2pm in conference room B.")
assert res["prediction"] in ("ham", "spam", "uncertain")
assert "model_confidence" in res
print("FRESH_PROCESS_OK")
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "FRESH_PROCESS_OK" in result.stdout


def test_metadata_l2_compliance():
    """Verify models/metadata.json contains all L2 required transparency fields."""
    assert METADATA_PATH.exists(), "metadata.json must exist"
    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)

    # Required L2 fields
    required_fields = [
        "dataset_name",
        "dataset_source_url",
        "dataset_license",
        "dataset_type",
        "n_samples",
        "class_counts",
        "language",
        "trained_at",
        "sklearn_version",
        "selection_criterion",
        "test_metrics",
    ]
    for field in required_fields:
        assert field in meta, f"Metadata missing required L2 field: {field}"

    # Verify metrics fields
    tm = meta["test_metrics"]
    for m in ["precision", "recall", "f1", "accuracy", "false_positives", "false_negatives"]:
        assert m in tm, f"Test metrics missing {m}"

    # Verify qualifier notice
    assert "qualifier_notice" in meta
    assert meta["dataset_type"] == "email"


def test_version_mismatch_warning(tmp_path):
    """Verify that a RuntimeWarning is issued when metadata sklearn_version does not match."""
    fake_meta = tmp_path / "metadata.json"
    fake_meta.write_text(json.dumps({"sklearn_version": "0.24.2"}), encoding="utf-8")
    with pytest.warns(RuntimeWarning, match="Scikit-learn version mismatch"):
        SpamPredictor(metadata_path=fake_meta)


def test_sanity_samples_exact_behavior():
    """Verify that the 10 hand-written sanity samples reproduce exact observed outcomes."""
    sanity_file = Path(__file__).parent / "data" / "sanity_samples.json"
    assert sanity_file.exists(), "sanity_samples.json must exist"
    with open(sanity_file, "r", encoding="utf-8") as f:
        samples = json.load(f)

    assert len(samples) == 10
    spam_count = sum(1 for s in samples if s["true_class"] == "spam")
    ham_count = sum(1 for s in samples if s["true_class"] == "ham")
    assert spam_count == 5
    assert ham_count == 5

    for item in samples:
        res = predict(item["subject"], item["body"])
        assert res["prediction"] == item["expected_prediction"]
        assert res["label_display"] == item["expected_label"]
        if item["is_known_miss"]:
            assert item["true_class"] == "spam"
            assert res["prediction"] == "ham"


def test_missing_model_raises_clear_filenotfounderror(tmp_path):
    """Verify that a missing model artifact raises a clear, descriptive FileNotFoundError."""
    missing_path = tmp_path / "non_existent_model.joblib"
    with pytest.raises(FileNotFoundError, match="Model artifact not found"):
        SpamPredictor(model_path=missing_path)


def test_model_sha256_integrity_success():
    """Verify that models/spam_pipeline.joblib matches the committed SHA-256 hash."""
    assert MODEL_PATH.exists()
    calculated_hash = compute_file_sha256(MODEL_PATH)
    assert calculated_hash == MODEL_EXPECTED_SHA256.lower()

    # Loading the predictor succeeds without integrity exception
    predictor = SpamPredictor()
    assert predictor.pipeline is not None


def test_model_sha256_integrity_tampering_fails_closed(tmp_path):
    """Verify that tampered model artifact fails closed with ValueError."""
    fake_model = tmp_path / "tampered_pipeline.joblib"
    fake_model.write_bytes(b"MALICIOUS_OR_CORRUPT_MODEL_PAYLOAD")

    # Mismatched expected hash should fail closed immediately
    with pytest.raises(ValueError, match="Model integrity verification failed"):
        SpamPredictor(
            model_path=fake_model,
            expected_sha256=MODEL_EXPECTED_SHA256,
        )


