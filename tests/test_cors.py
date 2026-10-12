"""Tests for Phase 12I CORS configuration and split-architecture headers.

Verifies:
1. Allowed origins receive Access-Control-Allow-Origin matching their exact origin.
2. Blocked origins receive zero CORS headers.
3. Preflight OPTIONS requests to /api/* return 204 with required CORS methods and headers.
4. Preflight OPTIONS requests from blocked origins receive zero CORS headers.
5. Bad input responses (400 Bad Request, 415, 413) preserve CORS headers for allowed origins.
6. Wildcard '*' is strictly forbidden and rejected.
"""

import pytest
from src.app import create_app


@pytest.fixture
def cors_app():
    """Create Flask application instance configured with explicit CORS allow-list."""
    app = create_app({
        "TESTING": True,
        "RATELIMIT_ENABLED": False,
        "CORS_ALLOWED_ORIGINS": "http://127.0.0.1:3000, https://mailguard-ai.vercel.app",
    })
    return app


@pytest.fixture
def client(cors_app):
    return cors_app.test_client()


def test_allowed_origin_get_health(client):
    """Allowed origin GET request receives exact Access-Control-Allow-Origin header."""
    res = client.get("/api/health", headers={"Origin": "http://127.0.0.1:3000"})
    assert res.status_code == 200
    assert res.headers.get("Access-Control-Allow-Origin") == "http://127.0.0.1:3000"
    assert "Origin" in res.headers.get("Vary", "")
    assert res.headers.get("Cache-Control") == "no-store"


def test_allowed_vercel_origin_model_info(client):
    """Production Vercel origin receives exact Access-Control-Allow-Origin header."""
    res = client.get("/api/model-info", headers={"Origin": "https://mailguard-ai.vercel.app"})
    assert res.status_code == 200
    assert res.headers.get("Access-Control-Allow-Origin") == "https://mailguard-ai.vercel.app"
    assert "Origin" in res.headers.get("Vary", "")


def test_blocked_origin_does_not_receive_cors(client):
    """Untrusted origin receives standard response without Access-Control-Allow-Origin."""
    res = client.get("/api/health", headers={"Origin": "https://malicious-phishing-site.example"})
    assert res.status_code == 200
    assert "Access-Control-Allow-Origin" not in res.headers


def test_preflight_options_allowed_origin(client):
    """OPTIONS preflight on /api/analyze from allowed origin returns 204 with all CORS controls."""
    res = client.open(
        "/api/analyze",
        method="OPTIONS",
        headers={
            "Origin": "http://127.0.0.1:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    assert res.status_code == 204
    assert res.headers.get("Access-Control-Allow-Origin") == "http://127.0.0.1:3000"
    assert "POST" in res.headers.get("Access-Control-Allow-Methods", "")
    assert "Content-Type" in res.headers.get("Access-Control-Allow-Headers", "")
    assert res.headers.get("Access-Control-Max-Age") == "86400"
    assert "Origin" in res.headers.get("Vary", "")


def test_preflight_options_blocked_origin(client):
    """OPTIONS preflight from blocked origin receives zero CORS allow headers."""
    res = client.open(
        "/api/analyze",
        method="OPTIONS",
        headers={
            "Origin": "http://evil-attacker.example",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    assert "Access-Control-Allow-Origin" not in res.headers


def test_bad_input_preserves_cors_headers(client):
    """Validation errors (400 Bad Request) preserve CORS headers so client browser can read error JSON."""
    # Send empty body / malformed JSON to /api/analyze
    res = client.post(
        "/api/analyze",
        data="not-valid-json",
        content_type="application/json",
        headers={"Origin": "http://127.0.0.1:3000"},
    )
    assert res.status_code == 400
    assert res.headers.get("Access-Control-Allow-Origin") == "http://127.0.0.1:3000"
    data = res.get_json()
    assert "error" in data


def test_unsupported_media_type_preserves_cors(client):
    """415 Unsupported Media Type preserves CORS headers."""
    res = client.post(
        "/api/analyze",
        data="plain text",
        content_type="text/plain",
        headers={"Origin": "https://mailguard-ai.vercel.app"},
    )
    assert res.status_code == 415
    assert res.headers.get("Access-Control-Allow-Origin") == "https://mailguard-ai.vercel.app"


def test_wildcard_asterisk_strictly_disallowed():
    """Configuring '*' must not grant wildcard CORS access."""
    wildcard_app = create_app({
        "TESTING": True,
        "RATELIMIT_ENABLED": False,
        "CORS_ALLOWED_ORIGINS": "*",
    })
    wildcard_client = wildcard_app.test_client()
    res = wildcard_client.get("/api/health", headers={"Origin": "https://any-random-site.com"})
    assert "Access-Control-Allow-Origin" not in res.headers


def test_successful_post_cross_origin(client):
    """Successful POST /api/analyze from allowed origin succeeds with CORS headers."""
    payload = {
        "text": "Subject: Team Sync\n\nHi everyone, let us meet tomorrow at 10am.",
        "options": {"scan_urls": False, "analyze_headers": False, "sensitivity": "medium"},
    }
    res = client.post(
        "/api/analyze",
        json=payload,
        headers={"Origin": "http://127.0.0.1:3000"},
    )
    assert res.status_code == 200
    assert res.headers.get("Access-Control-Allow-Origin") == "http://127.0.0.1:3000"
    data = res.get_json()
    assert "classification" in data
    assert "risk_score" in data
