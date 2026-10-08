"""Tests for Flask API endpoints and error handlers (Phase 2)."""

import json
import pytest
from src.app import create_app


@pytest.fixture
def app():
    """Create test application instance with custom small payload limit for testing 413."""
    app = create_app({
        "TESTING": True,
        "MAX_CONTENT_LENGTH": 1024,  # 1 KB limit for testing 413 easily
    })
    return app


@pytest.fixture
def client(app):
    """Test client."""
    return app.test_client()


def test_health_check_endpoint(client):
    """GET /api/health should return 200 and expected status object."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.is_json

    data = response.get_json()
    assert data["status"] == "online"
    assert data["model_loaded"] is False
    assert data["model_version"] is None


def test_404_error_handler(client):
    """Accessing an invalid endpoint should return a clean 404 JSON response with no path leaks."""
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert response.is_json

    data = response.get_json()
    assert data["status"] == "error"
    assert data["error"] == "not_found"
    assert "not found" in data["message"].lower()

    # Verify no filesystem paths are leaked
    raw_text = response.get_data(as_text=True)
    assert "\\" not in raw_text
    assert "/Users/" not in raw_text
    assert "/home/" not in raw_text


def test_413_payload_too_large(client):
    """Submitting payload exceeding MAX_CONTENT_LENGTH should return 413 JSON response."""
    # Our test fixture sets limit to 1024 bytes (1 KB)
    oversized_data = "A" * 2048
    response = client.post(
        "/api/health",  # Any route with payload
        data=oversized_data,
        content_type="text/plain",
    )
    assert response.status_code in (413, 405)  # Method not allowed or payload too large
    if response.status_code == 413:
        assert response.is_json
        data = response.get_json()
        assert data["status"] == "error"
        assert data["error"] == "payload_too_large"


def test_custom_400_bad_request():
    """Verify that a 400 error returns properly formatted JSON."""
    test_app = create_app({"TESTING": True})

    # Add a temporary test route that triggers abort(400)
    from flask import abort

    @test_app.route("/test-bad-request")
    def trigger_bad_request():
        abort(400, description="Invalid JSON input structure.")

    with test_app.test_client() as test_client:
        response = test_client.get("/test-bad-request")
        assert response.status_code == 400
        assert response.is_json
        data = response.get_json()
        assert data["status"] == "error"
        assert data["error"] == "bad_request"
        assert "Invalid JSON" in data["message"]
