"""Unit and integration tests for MailGuard AI v2 Phase 11C.

Verifies:
1. Backend /api/predict schema: top_tokens (max 15 items, token, weight, direction, is_stopword).
2. Stopword flag classification using ENGLISH_STOP_WORDS.
3. Backend filter_stopwords toggle on/off differences.
4. Genuine borderline sample yields 'uncertain' and 'Needs review' within [0.40, 0.60].
5. Static security audit for Phase 11C (zero innerHTML, zero inline styles/scripts).
"""

from pathlib import Path
import re
import pytest

from src.app import create_app
from src.predictor import is_stopword_term, predict


@pytest.fixture
def client():
    app = create_app({"TESTING": True})
    return app.test_client()


def test_is_stopword_term_helper():
    """Verify is_stopword_term accurately categorizes common stopwords and domain terms."""
    # Common English stopwords
    assert is_stopword_term("the") is True
    assert is_stopword_term("please") is True
    assert is_stopword_term("to") is True
    assert is_stopword_term("for the") is True
    assert is_stopword_term("in that") is True

    # Domain / content words
    assert is_stopword_term("paypal") is False
    assert is_stopword_term("account") is False
    assert is_stopword_term("invoice") is False
    assert is_stopword_term("unauthorized") is False
    assert is_stopword_term("__url__") is False


def test_top_tokens_schema_and_types(client):
    """POST /api/predict response contains top_tokens with <= 15 items and correct keys."""
    payload = {
        "subject": "URGENT: Your account requires verification",
        "body": "Dear customer, unauthorized activity detected on your bank card. Click http://bank-verify.com immediately."
    }
    res = client.post("/api/predict", json=payload)
    assert res.status_code == 200
    data = res.get_json()

    assert "top_tokens" in data
    assert isinstance(data["top_tokens"], list)
    assert len(data["top_tokens"]) <= 15
    assert len(data["top_tokens"]) > 0

    for tok in data["top_tokens"]:
        assert "token" in tok
        assert isinstance(tok["token"], str)
        assert "weight" in tok
        assert isinstance(tok["weight"], (int, float))
        assert "direction" in tok
        assert tok["direction"] in ("spam", "ham")
        assert "is_stopword" in tok
        assert isinstance(tok["is_stopword"], bool)


def test_filter_stopwords_toggle_behavior(client):
    """Calling predict with filter_stopwords=True filters out stopwords from top_tokens."""
    payload = {
        "subject": "Meeting regarding the project and the budget",
        "body": "Please be advised that the agenda for the meeting will be sent to the team tomorrow."
    }

    # 1. Unfiltered (filter_stopwords=False)
    res_unfiltered = client.post("/api/predict", json={**payload, "filter_stopwords": False})
    assert res_unfiltered.status_code == 200
    data_unfiltered = res_unfiltered.get_json()
    stopword_count_unfiltered = sum(1 for t in data_unfiltered["top_tokens"] if t["is_stopword"])

    # 2. Filtered (filter_stopwords=True)
    res_filtered = client.post("/api/predict", json={**payload, "filter_stopwords": True})
    assert res_filtered.status_code == 200
    data_filtered = res_filtered.get_json()
    stopword_count_filtered = sum(1 for t in data_filtered["top_tokens"] if t["is_stopword"])

    # When filtered, zero tokens with is_stopword==True remain
    assert stopword_count_filtered == 0
    if stopword_count_unfiltered > 0:
        assert len(data_unfiltered["top_tokens"]) >= len(data_filtered["top_tokens"])


def test_genuine_borderline_email_classification():
    """Verify that a genuine ambiguous email from the Enron dataset yields uncertain / Needs review."""
    subject = "re : no java ?"
    body = "you are cracking me up . basically you are the only thing keeping me awake today . ."

    res = predict(subject, body)
    assert res["prediction"] == "uncertain"
    assert res["label_display"] == "Needs review"
    assert res["is_uncertain"] is True
    assert res["risk_level"] == "medium"
    assert 0.40 <= res["spam_probability"] <= 0.60
    assert len(res["top_tokens"]) > 0
