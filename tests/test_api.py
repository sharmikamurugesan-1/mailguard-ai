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
# Index Frontend Endpoint
# -------------------------------------------------------------------------

def test_index_page_serves_html(client):
    """GET / returns 200 HTML with application title."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.content_type
    html_text = response.get_data(as_text=True)
    assert "MailGuard AI" in html_text
    assert "AI-Powered Email Spam Detection" in html_text


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


# -------------------------------------------------------------------------
# Phase 8 Hardening & Security Tests
# -------------------------------------------------------------------------

def test_security_headers_present(client):
    """Assert strict security headers are injected into HTTP responses."""
    response = client.get("/")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("Referrer-Policy") == "no-referrer"
    csp = response.headers.get("Content-Security-Policy", "")
    assert "default-src 'self'" in csp
    assert "style-src 'self'" in csp
    assert "'unsafe-inline'" not in csp
    assert "'unsafe-eval'" not in csp.replace("'wasm-unsafe-eval'", "")
    assert "'wasm-unsafe-eval'" in csp
    assert "worker-src 'self' blob:" in csp
    assert "connect-src 'self' blob:" in csp
    assert "img-src 'self' data: blob:" in csp
    assert "frame-ancestors 'none'" in csp


def test_405_method_not_allowed_get_predict(client):
    """GET /api/predict returns 405 Method Not Allowed in unified JSON shape."""
    response = client.get("/api/predict")
    assert response.status_code == 405
    assert response.is_json
    data = response.get_json()
    assert "error" in data
    assert data["error"]["code"] == "method_not_allowed"
    assert "not allowed" in data["error"]["message"].lower()


def test_405_method_not_allowed_post_health(client):
    """POST /api/health returns 405 Method Not Allowed in unified JSON shape."""
    response = client.post("/api/health", json={"data": "test"})
    assert response.status_code == 405
    assert response.is_json
    data = response.get_json()
    assert "error" in data
    assert data["error"]["code"] == "method_not_allowed"


@pytest.mark.parametrize("payload", [
    [],
    [{"subject": "test", "body": "test"}],
    12345,
    "just a string",
    True,
])
def test_400_non_dict_payloads(client, payload):
    """POST /api/predict with non-dict JSON bodies returns 400 invalid_json."""
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 400
    assert response.is_json
    data = response.get_json()
    assert data["error"]["code"] == "invalid_json"


def test_exact_boundary_length_20000_vs_20001():
    """Verify exact character boundary: 20,000 accepted (200), 20,001 rejected (413)."""
    app = create_app({
        "TESTING": True,
        "MAX_CONTENT_LENGTH": 2 * 1024 * 1024,  # High HTTP transport limit
    })
    with app.test_client() as c:
        # Exactly 20,000 characters total (subject: 10, body: 19,990)
        subject_10 = "S" * 10
        body_19990 = "B" * 19990
        assert len(subject_10) + len(body_19990) == 20000

        res_ok = c.post("/api/predict", json={"subject": subject_10, "body": body_19990})
        assert res_ok.status_code == 200, f"Expected 200, got {res_ok.status_code}: {res_ok.get_data(as_text=True)}"
        assert res_ok.is_json

        # Exactly 20,001 characters total (subject: 10, body: 19,991)
        body_19991 = "B" * 19991
        assert len(subject_10) + len(body_19991) == 20001

        res_too_large = c.post("/api/predict", json={"subject": subject_10, "body": body_19991})
        assert res_too_large.status_code == 413
        assert res_too_large.is_json
        data_large = res_too_large.get_json()
        assert data_large["error"]["code"] == "payload_too_large"
        assert "20001" in data_large["error"]["message"]


def test_api_uncertain_prediction_flow(client, monkeypatch):
    """POST /api/predict returns 'uncertain', 'Needs review', and 'medium' risk when prob is 0.50."""
    predictor = get_predictor()

    # Monkeypatch predict to simulate a borderline case (p=0.50)
    original_predict = predictor.predict

    def fake_predict(subject, body):
        res = original_predict(subject, body)
        res["spam_probability"] = 0.50
        res["confidence"] = 0.50
        res["prediction"] = "uncertain"
        res["label_display"] = "Needs review"
        res["risk_level"] = "medium"
        return res

    monkeypatch.setattr(predictor, "predict", fake_predict)

    response = client.post("/api/predict", json={"subject": "Inquiry", "body": "Please review invoice INV-402"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["prediction"] == "uncertain"
    assert data["label_display"] == "Needs review"
    assert data["risk_level"] == "medium"
    assert data["spam_probability"] == 0.50


def test_root_wsgi_app_import():
    """Verify root app.py exposes the Flask WSGI instance for Gunicorn."""
    import app as wsgi_module
    assert hasattr(wsgi_module, "app")
    assert wsgi_module.app is not None


def test_500_internal_server_error(client, monkeypatch):
    """Ensure unexpected exceptions return 500 with unified JSON error schema and no path leaks."""
    def crash_predictor():
        raise RuntimeError("Simulated internal catastrophic failure")

    monkeypatch.setattr("src.app.get_predictor", crash_predictor)

    response = client.post("/api/predict", json={"subject": "Test", "body": "Crash test body"})
    assert response.status_code == 500
    assert response.is_json
    data = response.get_json()
    assert data["error"]["code"] in ("prediction_error", "internal_server_error")

    raw_text = response.get_data(as_text=True)
    assert "\\" not in raw_text
    assert "C:" not in raw_text
    assert "Traceback" not in raw_text


def test_rate_limiting_enforced():
    """Verify rate limiter returns 429 JSON when enabled and threshold is reached."""
    rate_app = create_app({
        "TESTING": True,
        "RATELIMIT_ENABLED": True,
    })
    rate_client = rate_app.test_client()

    # Health check is exempt
    for _ in range(10):
        res = rate_client.get("/api/health")
        assert res.status_code == 200

    # Exhaust /api/predict (60 req/min limit)
    hit_429 = False
    for i in range(70):
        res = rate_client.post("/api/predict", json={"body": f"Rate test body {i}"})
        if res.status_code == 429:
            hit_429 = True
            assert res.is_json
            data = res.get_json()
            assert data["error"]["code"] == "rate_limit_exceeded"
            assert "Rate limit exceeded" in data["error"]["message"] or "60 per" in data["error"]["message"]
            break
    assert hit_429, "Expected 429 RateLimitExceeded after 60 requests"


def test_rate_limiting_ip_forwarded_for_separation():
    """Verify that Werkzeug ProxyFix allows Flask-Limiter to track separate IPs via X-Forwarded-For."""
    rate_app = create_app({
        "TESTING": True,
        "RATELIMIT_ENABLED": True,
    })
    rate_client = rate_app.test_client()

    ip_a = "203.0.113.195"
    ip_b = "198.51.100.42"

    # Exhaust limit for IP A (60 per minute on /api/predict)
    hit_429 = False
    for i in range(70):
        res = rate_client.post(
            "/api/predict",
            json={"body": f"IP A body {i}"},
            headers={"X-Forwarded-For": ip_a},
        )
        if res.status_code == 429:
            hit_429 = True
            break
    assert hit_429, "Expected IP A to hit 429 rate limit"

    # Verify IP A is indeed rate-limited
    res_a_again = rate_client.post(
        "/api/predict",
        json={"body": "IP A follow-up"},
        headers={"X-Forwarded-For": ip_a},
    )
    assert res_a_again.status_code == 429

    # Verify IP B with distinct X-Forwarded-For is NOT rate-limited (gets 200 OK)
    res_b = rate_client.post(
        "/api/predict",
        json={"body": "IP B fresh request"},
        headers={"X-Forwarded-For": ip_b},
    )
    assert res_b.status_code == 200, f"Expected IP B to succeed (200), got {res_b.status_code}"


def test_html_404_error_page(client):
    """Browser request to non-existent route returns themed 404 HTML page."""
    res = client.get("/non-existent-web-page", headers={"Accept": "text/html,application/xhtml+xml"})
    assert res.status_code == 404
    assert not res.is_json
    html = res.get_data(as_text=True)
    assert "404" in html
    assert "Page Not Found" in html
    assert "MailGuard AI" in html
    assert "Return to Dashboard" in html


def test_favicon_endpoints(client):
    """Favicon ICO and SVG endpoints are served with proper content types."""
    res_ico = client.get("/favicon.ico")
    assert res_ico.status_code == 200
    assert "image/vnd.microsoft.icon" in res_ico.content_type

    res_svg = client.get("/favicon.svg")
    assert res_svg.status_code == 200
    assert "image/svg+xml" in res_svg.content_type


def test_static_examples_dataset(client):
    """GET /data/examples.json serves 7 validated examples with test domains."""
    res = client.get("/data/examples.json")
    assert res.status_code == 200
    assert res.is_json
    data = res.get_json()
    assert isinstance(data, list)
    assert len(data) == 7

    categories = [ex["category"] for ex in data]
    assert categories.count("spam") == 3
    assert categories.count("safe") == 3
    assert categories.count("borderline") == 1

    for ex in data:
        assert "id" in ex
        assert "label" in ex
        assert "subject" in ex
        assert "body" in ex
        # Ensure domains are strictly example.test to avoid real/defamatory targets
        if "http" in ex["body"] or "@" in ex["body"]:
            assert "example.test" in ex["body"]


def test_og_preview_image(client):
    """GET /img/og-preview.png serves valid PNG preview image."""
    res = client.get("/img/og-preview.png")
    assert res.status_code == 200
    assert "image/png" in res.content_type
    assert len(res.data) > 1000

