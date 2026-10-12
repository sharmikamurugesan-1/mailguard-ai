"""Unit tests for Multi-Model Intelligence (Requirement 1 & 10).

Verifies:
1. All three candidate models (SVM, LR, NB) load properly in SpamPredictor.
2. Each model performs genuine inference and outputs calibrated probabilities.
3. GET /api/models exposes algorithm catalog with held-out metrics.
4. POST /api/predict supports model selection ('svm', 'lr', 'nb').
5. POST /api/compare returns simultaneous 3-model outputs with consensus calculation.
6. POST /api/analyze integrates multi-model comparison data and honors model selection.
"""

import pytest
from src.app import create_app
from src.predictor import SpamPredictor


@pytest.fixture
def client():
    app = create_app({"TESTING": True, "RATELIMIT_ENABLED": False})
    return app.test_client()


@pytest.fixture
def predictor():
    return SpamPredictor()


def test_predictor_loads_all_three_models(predictor):
    """SpamPredictor must have svm, lr, and nb pipelines loaded."""
    assert "svm" in predictor.pipelines
    assert "lr" in predictor.pipelines
    assert "nb" in predictor.pipelines
    assert predictor.pipelines["svm"] is not None
    assert predictor.pipelines["lr"] is not None
    assert predictor.pipelines["nb"] is not None


def test_individual_model_predictions(predictor):
    """Each model must return genuine prediction for clear spam and clear ham."""
    spam_sample = "URGENT WINNER: Claim your $5,000,000 cash prize instantly at claim-now.test!"
    ham_sample = "Hi team, please find attached the weekly sprint retrospective notes and agenda."

    for model_key in ["svm", "lr", "nb"]:
        res_spam = predictor.predict(subject="Urgent Notice", body=spam_sample, model_key=model_key)
        assert res_spam["prediction"] in ["spam", "uncertain"]
        assert res_spam["model_key"] == model_key
        assert 0.0 <= res_spam["spam_probability"] <= 1.0

        res_ham = predictor.predict(subject="Meeting Notes", body=ham_sample, model_key=model_key)
        assert res_ham["prediction"] in ["ham", "uncertain"]
        assert res_ham["model_key"] == model_key
        assert 0.0 <= res_ham["spam_probability"] <= 1.0


def test_compare_models_consensus(predictor):
    """compare_models returns per-model outputs, consensus verdict, and held-out benchmarks."""
    spam_sample = "Exclusive lottery jackpot winner! Call now to verify your bank account details."
    comp = predictor.compare_models(subject="Winning Claim", body=spam_sample)

    assert "algorithms" in comp
    assert "svm" in comp["algorithms"]
    assert "lr" in comp["algorithms"]
    assert "nb" in comp["algorithms"]

    assert comp["consensus_verdict"] in ["spam", "ham", "uncertain"]
    assert comp["consensus_strength"] in ["3/3", "2/3", "1/3"]
    assert "all_agree" in comp

    # Check benchmarks present
    for m in ["svm", "lr", "nb"]:
        algo = comp["algorithms"][m]
        assert "evaluation" in algo
        assert algo["evaluation"]["accuracy"] > 0.98
        assert algo["evaluation"]["f1"] > 0.98


def test_api_models_endpoint(client):
    """GET /api/models returns 200 with the 3 algorithm definitions and metrics."""
    res = client.get("/api/models")
    assert res.status_code == 200
    data = res.get_json()
    assert "models" in data
    assert len(data["models"]) == 3
    keys = [m["key"] for m in data["models"]]
    assert "svm" in keys
    assert "lr" in keys
    assert "nb" in keys


def test_api_predict_model_selection(client):
    """POST /api/predict accepts model parameter and reflects model_key in response."""
    payload = {
        "subject": "Test",
        "body": "Congratulations, you won a free vacation! Click here immediately.",
        "model": "lr"
    }
    res = client.post("/api/predict", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["model_key"] == "lr"


def test_api_compare_endpoint(client):
    """POST /api/compare executes multi-model comparison across all 3 models."""
    payload = {
        "subject": "Security Alert",
        "body": "Please review your account credentials at http://verify-identity.test"
    }
    res = client.post("/api/compare", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert "algorithms" in data
    assert "svm" in data["algorithms"]
    assert "lr" in data["algorithms"]
    assert "nb" in data["algorithms"]
    assert data["consensus_strength"] in ["3/3", "2/3", "1/3"]


def test_api_analyze_contains_models_comparison(client):
    """POST /api/analyze includes models_comparison and honors model option."""
    payload = {
        "text": "Subject: Invoice Alert\n\nYour account has been charged $450. Call 1-800-555-0199.",
        "model": "nb",
        "options": {
            "model": "nb"
        }
    }
    res = client.post("/api/analyze", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert "models_comparison" in data
    assert data["models_comparison"] is not None
    assert data["model"]["key"] == "nb"


def test_predict_without_explanations_and_primary_result_reuse(predictor):
    """Verify include_explanations=False omits signals/top_tokens and compare_models reuses primary_result."""
    text = "Urgent: Click http://verify.test to claim your refund."
    
    # 1. With explanations (default)
    res_full = predictor.predict(subject="Alert", body=text, model_key="svm", include_explanations=True)
    assert len(res_full["top_tokens"]) > 0
    assert len(res_full["signals"]) > 0

    # 2. Without explanations
    res_fast = predictor.predict(subject="Alert", body=text, model_key="svm", include_explanations=False)
    assert len(res_fast["top_tokens"]) == 0
    assert len(res_fast["signals"]) == 0
    assert res_fast["prediction"] == res_full["prediction"]
    assert res_fast["spam_probability"] == res_full["spam_probability"]

    # 3. compare_models with primary_result reuse
    comp = predictor.compare_models(subject="Alert", body=text, primary_result=res_full)
    assert comp["algorithms"]["svm"]["spam_probability"] == res_full["spam_probability"]
    assert "lr" in comp["algorithms"]
    assert "nb" in comp["algorithms"]
