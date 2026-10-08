"""Tests for Flask API endpoints, reliability features, and error handlers (Phase 6)."""

import json
import pytest
from src import config
from src.app import create_app
from src.predictor import get_predictor


@pytest.fixture
def app():
    """Create test application instance with custom small payload limit for testing 413."""
    app = create_app({
        "TESTING": True,
        "MAX_CONTENT_LENGTH": 1024,  # 1 KB limit for testing 413 HTTP transport
    })
    return app


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


# -------------------------------------------------------------------------
# Health Check Endpoint
# -------------------------------------------------------------------------

def test_health_check_endpoint(client):
    """GET /api/health returns 200, status, model_loaded, and model_version."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.is_json

    data = response.get_json()
    assert "status" in data
    assert data["status"] in ("healthy", "degraded")
    assert data["model_loaded"] is True
    assert isinstance(data["model_version"], str)
    assert len(data["model_version"]) > 0


# -------------------------------------------------------------------------
# Error Handlers & Security (Unified Error Schema & No Path Leaks)
# -------------------------------------------------------------------------

def test_404_error_handler(client):
    """Accessing non-existent endpoint returns 404 with unified error shape and no path leaks."""
    response = client.get("/api/non-existent-endpoint")
    assert response.status_code == 404
    assert response.is_json

    data = response.get_json()
    assert "error" in data
    assert data["error"]["code"] == "not_found"
    assert "not found" in data["error"]["message"].lower()

    # Zero path leak check
    raw_text = response.get_data(as_text=True)
    assert "\\" not in raw_text
    assert "C:" not in raw_text
    assert "/Users/" not in raw_text
    assert "/home/" not in raw_text


def test_415_unsupported_media_type(client):
    """POST /api/predict with non-JSON Content-Type returns 415."""
    response = client.post(
        "/api/predict",
        data="raw string email text",
        content_type="text/plain",
    )
    assert response.status_code == 415
    assert response.is_json

    data = response.get_json()
    assert "error" in data
    assert data["error"]["code"] == "unsupported_media_type"
    assert "Content-Type must be application/json" in data["error"]["message"]


def test_413_payload_too_large_content_length(client):
    """Submitting payload exceeding MAX_CONTENT_LENGTH returns 413 JSON."""
    # Test app has 1 KB limit; send 2 KB
    oversized_data = json.dumps({"body": "X" * 2048})
    response = client.post(
        "/api/predict",
        data=oversized_data,
        content_type="application/json",
    )
    assert response.status_code == 413
    assert response.is_json

    data = response.get_json()
    assert "error" in data
    assert data["error"]["code"] == "payload_too_large"


def test_413_payload_too_large_character_limit():
    """POST /api/predict exceeding MAX_INPUT_CHARS returns 413."""
    custom_app = create_app({
        "TESTING": True,
        "MAX_CONTENT_LENGTH": 100 * 1024,  # High HTTP limit
    })
    with custom_app.test_client() as c:
        # Exceed MAX_INPUT_CHARS (config default is 50,000)
        oversized_body = "A" * (config.MAX_INPUT_CHARS + 100)
        response = c.post(
            "/api/predict",
            json={"subject": "Big", "body": oversized_body},
        )
        assert response.status_code == 413
        assert response.is_json

        data = response.get_json()
        assert "error" in data
        assert data["error"]["code"] == "payload_too_large"
        assert "exceeds the maximum limit" in data["error"]["message"]


def test_400_malformed_json(client):
    """POST /api/predict with invalid raw JSON syntax returns 400 invalid_json."""
    response = client.post(
        "/api/predict",
        data='{"subject": "test", "body": "unclosed json',
        content_type="application/json",
    )
    assert response.status_code == 400
    assert response.is_json

    data = response.get_json()
    assert "error" in data
    assert data["error"]["code"] == "invalid_json"


def test_400_missing_body(client):
    """POST /api/predict without 'body' field returns 400 missing_field."""
    response = client.post(
        "/api/predict",
        json={"subject": "Only a subject"},
    )
    assert response.status_code == 400
    assert response.is_json

    data = response.get_json()
    assert "error" in data
    assert data["error"]["code"] == "missing_field"
    assert "'body' is missing" in data["error"]["message"]


def test_400_empty_body(client):
    """POST /api/predict with empty or whitespace-only 'body' returns 400 empty_input."""
    response = client.post(
        "/api/predict",
        json={"subject": "Test", "body": "   \n\t  "},
    )
    assert response.status_code == 400
    assert response.is_json

    data = response.get_json()
    assert "error" in data
    assert data["error"]["code"] == "empty_input"


def test_400_invalid_types(client):
    """POST /api/predict with non-string fields returns 400 invalid_type."""
    # Body as integer
    res1 = client.post(
        "/api/predict",
        json={"subject": "Test", "body": 12345},
    )
    assert res1.status_code == 400
    assert res1.get_json()["error"]["code"] == "invalid_type"

    # Subject as list
    res2 = client.post(
        "/api/predict",
        json={"subject": ["not", "a", "string"], "body": "Valid body text here"},
    )
    assert res2.status_code == 400
    assert res2.get_json()["error"]["code"] == "invalid_type"


# -------------------------------------------------------------------------
# GET /api/model-info Endpoint
# -------------------------------------------------------------------------

def test_get_model_info(client):
    """GET /api/model-info returns complete provenance, metrics, thresholds, and limitations."""
    response = client.get("/api/model-info")
    assert response.status_code == 200
    assert response.is_json

    data = response.get_json()
    expected_keys = [
        "model_type",
        "vectorizer",
        "version",
        "trained_at",
        "sklearn_version",
        "dataset_name",
        "dataset_source_url",
        "dataset_license",
        "dataset_type",
        "n_samples",
        "class_counts",
        "selection_criterion",
        "test_metrics",
        "thresholds",
        "limitations",
    ]
    for key in expected_keys:
        assert key in data, f"Missing key in /api/model-info: {key}"

    assert data["dataset_type"] == "email"
    assert isinstance(data["test_metrics"], dict)
    assert "precision" in data["test_metrics"]
    assert "recall" in data["test_metrics"]
    assert "f1" in data["test_metrics"]
    assert "fp" in data["test_metrics"]
    assert "fn" in data["test_metrics"]

    assert isinstance(data["limitations"], list)
    assert len(data["limitations"]) >= 3
    # Check that Enron-era limitation is explicitly mentioned
    limitations_text = " ".join(data["limitations"]).lower()
    assert "enron" in limitations_text
    assert "test set" in limitations_text

    # Verify zero path leaks
    raw_text = response.get_data(as_text=True)
    assert "\\" not in raw_text
    assert "C:" not in raw_text
    assert "/Users/" not in raw_text


# -------------------------------------------------------------------------
# POST /api/predict Endpoint
# -------------------------------------------------------------------------

def test_predict_realistic_spam(client):
    """POST /api/predict with realistic spam returns spam classification, confidence, and signals."""
    payload = {
        "subject": "URGENT: Claim your $1000 gift card online now!",
        "body": "Congratulations winner! Click http://claim-prize.biz/free to receive your cash money immediately. Do not remove this email.",
    }
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 200
    assert response.is_json

    data = response.get_json()
    assert data["prediction"] == "spam"
    assert data["label_display"] in ("Likely spam", "Spam", "Suspicious")
    assert data["risk_level"] == "high"
    assert 0.0 <= data["spam_probability"] <= 1.0
    assert 0.0 <= data["confidence"] <= 1.0
    assert data["spam_probability"] >= 0.60

    # Verify signals
    assert "signals" in data
    assert isinstance(data["signals"], list)
    if data["signals"]:
        first_sig = data["signals"][0]
        assert "term" in first_sig
        assert "contribution" in first_sig
        assert "direction" in first_sig
        assert first_sig["note"] == "top contributing term"

    # Verify reliability block
    assert "reliability" in data
    assert data["reliability"]["level"] in ("high", "medium", "low")
    assert isinstance(data["reliability"]["warnings"], list)


def test_predict_realistic_ham(client):
    """POST /api/predict with realistic ham returns 'Likely legitimate' ham classification."""
    payload = {
        "subject": "Quarterly Budget Review Meeting Notes",
        "body": "Hi team, please find attached the spreadsheet for our Q3 financial review. Let me know if you have any questions before Monday's presentation.",
    }
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 200
    assert response.is_json

    data = response.get_json()
    assert data["prediction"] == "ham"
    assert data["label_display"] == "Likely legitimate"
    assert data["risk_level"] == "low"
    assert data["spam_probability"] < 0.40
    assert 0.0 <= data["confidence"] <= 1.0

    # Ensure forbidden words 'safe' and '100%' are not used
    raw_text = response.get_data(as_text=True).lower()
    assert '"safe"' not in raw_text
    assert "100%" not in raw_text


def test_predictor_singleton_load_once(client):
    """Verify that multiple predict calls do not reload the model pipeline from disk."""
    predictor = get_predictor()
    initial_count = predictor.load_count

    # Make multiple predictions
    client.post("/api/predict", json={"subject": "Meeting 1", "body": "Project updates for today."})
    client.post("/api/predict", json={"subject": "Meeting 2", "body": "Next sprint planning session."})
    client.get("/api/health")
    client.get("/api/model-info")

    assert predictor.load_count == initial_count == 1
