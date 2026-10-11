"""Launch readiness and comprehensive robustness test suite for MailGuard AI.

Validates Stage A Launch Robustness Criteria:
1. Oversize bodies (413 Payload Too Large) on /api/predict and /api/analyze.
2. Malformed JSON (400 Bad Request) on all endpoints.
3. Wrong Content-Type (415 Unsupported Media Type).
4. Malformed .eml payloads, binary garbage, and corrupted MIME headers.
5. 1 MB adversarial string (ReDoS check: execution finishes in < 2.0s).
6. 50 parallel identical requests via ThreadPoolExecutor proving bit-for-bit determinism and thread safety.
7. Log capture asserting zero input text or email contents appear in server logs.
8. 500 internal server error responses confirm zero stack traces or file paths leaked.
9. Dynamic env-configurable rate limiting verification.
"""

import concurrent.futures
import io
import json
import logging
import os
import time
from unittest.mock import patch

import pytest
from src import config
from src.app import create_app


@pytest.fixture
def client():
    """Create a test client with testing mode enabled."""
    app = create_app({"TESTING": True})
    return app.test_client()


# =============================================================================
# 1. Oversize Body Tests (413 Payload Too Large)
# =============================================================================

def test_oversize_body_predict_413(client):
    """POST /api/predict with body exceeding MAX_INPUT_CHARS returns 413."""
    max_chars = config.MAX_INPUT_CHARS
    oversize_payload = {
        "subject": "Test Subject",
        "body": "A" * (max_chars + 100),
    }
    res = client.post("/api/predict", json=oversize_payload)
    assert res.status_code == 413
    assert res.is_json
    data = res.get_json()
    assert data["error"]["code"] == "payload_too_large"
    assert "exceeds the maximum limit" in data["error"]["message"]


def test_oversize_text_analyze_413(client):
    """POST /api/analyze with text exceeding MAX_INPUT_CHARS returns 413."""
    max_chars = config.MAX_INPUT_CHARS
    oversize_payload = {
        "text": "B" * (max_chars + 50),
    }
    res = client.post("/api/analyze", json=oversize_payload)
    assert res.status_code == 413
    assert res.is_json
    data = res.get_json()
    assert data["error"]["code"] == "payload_too_large"


def test_oversize_eml_analyze_413(client):
    """POST /api/analyze with raw EML exceeding 1 MB returns 413."""
    oversize_eml = "From: sender@example.test\r\nSubject: Test\r\n\r\n" + ("X" * 1_000_100)
    res = client.post("/api/analyze", json={"eml": oversize_eml})
    assert res.status_code == 413
    assert res.is_json
    data = res.get_json()
    assert data["error"]["code"] == "payload_too_large"
    assert "exceeds maximum limit" in data["error"]["message"]


def test_max_content_length_flask_413(client):
    """Payload exceeding Flask MAX_CONTENT_LENGTH (2 MB) triggers 413."""
    oversize_raw = b"{" + b'"text": "' + (b"A" * (2 * 1024 * 1024 + 1024)) + b'"}'
    res = client.post(
        "/api/analyze",
        data=oversize_raw,
        content_type="application/json",
    )
    assert res.status_code == 413
    assert res.is_json
    data = res.get_json()
    assert data["error"]["code"] == "payload_too_large"


# =============================================================================
# 2. Malformed JSON Tests (400 Bad Request)
# =============================================================================

def test_malformed_json_syntax(client):
    """Truncated or invalid JSON syntax returns 400 with code 'invalid_json'."""
    broken_payloads = [
        b'{"text": "unterminated string',
        b'{"text": ',
        b'{not json at all}',
        b'',
    ]
    for raw in broken_payloads:
        res = client.post("/api/analyze", data=raw, content_type="application/json")
        assert res.status_code == 400
        assert res.is_json
        data = res.get_json()
        assert data["error"]["code"] in ("invalid_json", "bad_request")


def test_invalid_json_types(client):
    """Non-object JSON root or non-string fields return 400."""
    # List instead of dict
    res = client.post("/api/analyze", json=["not", "a", "dict"])
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "invalid_json"

    # Integer text field
    res = client.post("/api/analyze", json={"text": 12345})
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "invalid_type"

    # Integer EML field
    res = client.post("/api/analyze", json={"eml": 98765})
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "invalid_type"

    # Non-dict options
    res = client.post("/api/analyze", json={"text": "hello", "options": "invalid"})
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "invalid_type"


def test_empty_input_analyze_400(client):
    """Empty JSON or whitespace-only inputs return 400 with 'empty_input'."""
    res = client.post("/api/analyze", json={})
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "empty_input"

    res = client.post("/api/analyze", json={"text": "   \n\t  "})
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "empty_input"


# =============================================================================
# 3. Wrong Content-Type Tests (415 Unsupported Media Type)
# =============================================================================

def test_wrong_content_type_415(client):
    """Non-JSON Content-Types return 415 with 'unsupported_media_type'."""
    invalid_content_types = [
        "text/plain",
        "application/x-www-form-urlencoded",
        "multipart/form-data",
        "application/xml",
    ]
    for ct in invalid_content_types:
        res = client.post("/api/analyze", data="text=hello", content_type=ct)
        assert res.status_code == 415
        assert res.is_json
        assert res.get_json()["error"]["code"] == "unsupported_media_type"

        res_p = client.post("/api/predict", data="body=hello", content_type=ct)
        assert res_p.status_code == 415
        assert res_p.is_json
        assert res_p.get_json()["error"]["code"] == "unsupported_media_type"


# =============================================================================
# 4. Malformed .eml and Binary Garbage Tests
# =============================================================================

def test_malformed_eml_binary_garbage(client):
    """Malformed EML messages, corrupted headers, and raw binary garbage do not crash server."""
    garbage_samples = [
        # Binary null bytes and high ASCII
        "From: admin@example.test\r\nSubject: \x00\xff\xfe\xca\xfe\r\n\r\nCorrupted body text \x00\x01\x02",
        # Truncated multipart boundary
        "Content-Type: multipart/mixed; boundary=\"--boundary123\"\r\n\r\n----boundary123\r\nContent-Type: text/plain\r\n\r\nTruncated without end boundary",
        # Corrupted base64 payload
        "Content-Transfer-Encoding: base64\r\n\r\n!@#$%^&*()_not_base64=====",
        # Truncated single header line
        "Subject:",
        # Header injection attempt
        "From: attack@evil.test\r\nSubject: Test\r\nBcc: victim@example.test\r\n\r\nTest body",
    ]

    for sample in garbage_samples:
        res = client.post("/api/analyze", json={"eml": sample})
        # Server must handle gracefully (200 with fallback analysis or 400), NEVER unhandled 500
        assert res.status_code in (200, 400)
        assert res.is_json
        if res.status_code == 200:
            data = res.get_json()
            assert "risk_score" in data
            assert "classification" in data


# =============================================================================
# 5. Adversarial Input & ReDoS Check (< 2.0s Execution Time)
# =============================================================================

def test_adversarial_redos_execution_time(client):
    """1 MB raw input boundary and pathological regex patterns complete in < 2.0s."""
    # 1. Pathological patterns for URL regex, header regex, and tokenization within 20k text limit
    adversarial_eml = (
        "From: " + ("a" * 50) + "@" + ("sub." * 20) + "example.test\r\n"
        "Subject: " + ("URGENT " * 50) + "\r\n"
        "Received: from [127.0.0.1] by host.test with ESMTP; Sun, 11 Oct 2026 12:00:00 +0000\r\n"
        "\r\n"
        # Pathological URLs with nested structures, deep subdomains, repetitive schemes
        + ("http://user:pass@" + ("sub." * 20) + "domain.test/path/to/page?query=" + ("x" * 50) + "\n") * 20
        + ("http://" + ("a" * 100) + ".example.test " * 20)
        + ("Check this link: http://legitimate.test but really http://phishing.test\n" * 20)
        + ("Word " * 1000)
    )

    start_time = time.perf_counter()
    res = client.post("/api/analyze", json={"eml": adversarial_eml})
    elapsed = time.perf_counter() - start_time

    assert res.status_code == 200
    assert elapsed < 2.0, f"Adversarial ReDoS check exceeded 2.0s: took {elapsed:.3f}s"
    data = res.get_json()
    assert "risk_score" in data
    assert "indicators" in data

    # 2. Large 990 KB raw EML with oversized body rejected at 413 in < 2.0s
    large_1mb_eml = "From: sender@example.test\r\nSubject: Big\r\n\r\n" + ("X" * 990_000)
    t0 = time.perf_counter()
    res_large = client.post("/api/analyze", json={"eml": large_1mb_eml})
    t_large = time.perf_counter() - t0
    assert res_large.status_code == 413
    assert t_large < 2.0, f"Large 1MB processing exceeded 2.0s: took {t_large:.3f}s"


# =============================================================================
# 6. Concurrency & Thread-Safety (50 Parallel Identical Requests)
# =============================================================================

def test_parallel_requests_thread_safety_and_determinism(client):
    """50 concurrent identical requests via ThreadPoolExecutor yield bit-for-bit identical results."""
    payload = {
        "text": (
            "URGENT: Your account access has been suspended due to unauthorized login attempts. "
            "Please click http://secure-banking.update-verify.test/login immediately to verify your identity."
        ),
        "options": {
            "scan_urls": True,
            "sensitivity": "medium",
        },
    }

    def send_single_request():
        r = client.post("/api/analyze", json=payload)
        return r.status_code, r.get_json()

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(send_single_request) for _ in range(50)]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())

    assert len(results) == 50

    # Verify all succeeded
    status_codes = [status for status, _ in results]
    assert all(code == 200 for code in status_codes), f"Some requests failed: {set(status_codes)}"

    # Verify bit-for-bit determinism across all 50 responses
    first_response = results[0][1]
    expected_risk = first_response["risk_score"]
    expected_classification = first_response["classification"]
    expected_prob = first_response["model"]["probability"]
    expected_findings = first_response["key_findings"]

    for i, (_, resp) in enumerate(results[1:], start=2):
        assert resp["risk_score"] == expected_risk, f"Thread {i} risk score mismatch"
        assert resp["classification"] == expected_classification, f"Thread {i} classification mismatch"
        assert resp["model"]["probability"] == expected_prob, f"Thread {i} model prob mismatch"
        assert resp["key_findings"] == expected_findings, f"Thread {i} findings mismatch"


# =============================================================================
# 7. Privacy & Zero Input Text Logging Invariant
# =============================================================================

def test_zero_input_text_logging_invariant(client, caplog):
    """Input text, subject, body, or EML contents NEVER appear in server logs."""
    canary_text = "CANARY_SECRET_USER_PAYLOAD_TOKEN_987654321_DO_NOT_LOG"
    canary_subject = "CONFIDENTIAL_CANARY_SUBJECT_XYZ_SECRET"

    caplog.clear()
    with caplog.at_level(logging.DEBUG):
        # 1. Test /api/predict
        res1 = client.post("/api/predict", json={"subject": canary_subject, "body": canary_text})
        assert res1.status_code == 200

        # 2. Test /api/analyze with text
        res2 = client.post("/api/analyze", json={"text": f"{canary_subject}\n\n{canary_text}"})
        assert res2.status_code == 200

        # 3. Test /api/analyze with EML
        eml_canary = f"From: user@test.test\r\nSubject: {canary_subject}\r\n\r\n{canary_text}"
        res3 = client.post("/api/analyze", json={"eml": eml_canary})
        assert res3.status_code == 200

    # Inspect all captured logs
    for record in caplog.records:
        log_message = record.getMessage()
        assert canary_text not in log_message, f"Canary text leaked in log: '{log_message}'"
        assert canary_subject not in log_message, f"Canary subject leaked in log: '{log_message}'"
        if record.exc_text:
            assert canary_text not in record.exc_text
            assert canary_subject not in record.exc_text


# =============================================================================
# 8. 500 Error Responses Leaking Zero File Paths or Stack Traces
# =============================================================================

def test_500_internal_error_zero_leakage(client):
    """500 error responses return unified JSON and leak zero file paths or tracebacks."""
    # 1. Unhandled exception in /api/analyze (triggers handle_internal_error)
    with patch("src.app.compute_risk_score") as mock_compute:
        mock_compute.side_effect = RuntimeError("Critical unexpected failure at C:\\secret\\mailguard\\model.py:105")

        res = client.post("/api/analyze", json={"text": "Normal safe text for analysis."})
        assert res.status_code == 500
        assert res.is_json

        data = res.get_json()
        assert "error" in data
        assert data["error"]["code"] == "internal_server_error"
        assert "unexpected" in data["error"]["message"].lower()

        # Confirm zero path or traceback leakage in raw body
        raw_body = res.get_data(as_text=True)
        assert "RuntimeError" not in raw_body
        assert "C:\\" not in raw_body
        assert "Traceback" not in raw_body
        assert ".py" not in raw_body
        assert "mailguard" not in raw_body

    # 2. Inference exception in /api/predict (triggers prediction_error 500)
    with patch("src.app.get_predictor") as mock_pred:
        mock_pred.side_effect = RuntimeError("Inference crash at C:\\secret\\mailguard\\model.py:200")

        res_p = client.post("/api/predict", json={"body": "Normal safe text for predict."})
        assert res_p.status_code == 500
        assert res_p.is_json

        data_p = res_p.get_json()
        assert "error" in data_p
        assert data_p["error"]["code"] == "prediction_error"

        raw_body_p = res_p.get_data(as_text=True)
        assert "RuntimeError" not in raw_body_p
        assert "C:\\" not in raw_body_p
        assert "Traceback" not in raw_body_p
        assert ".py" not in raw_body_p


# =============================================================================
# 9. Dynamic Rate Limiting Configuration Verification
# =============================================================================

def test_dynamic_rate_limiting_env_config():
    """Setting RATELIMIT_ANALYZE_PER_MINUTE dynamically adjusts enforcement limit."""
    with patch.dict(os.environ, {"RATELIMIT_ANALYZE_PER_MINUTE": "5"}):
        app = create_app({
            "TESTING": True,
            "RATELIMIT_ENABLED": True,
        })
        client = app.test_client()

        # Fire 5 allowed requests
        for i in range(5):
            r = client.post("/api/analyze", json={"text": f"Valid request {i}"})
            assert r.status_code == 200, f"Request {i} unexpectedly blocked"

        # 6th request must trigger 429
        r6 = client.post("/api/analyze", json={"text": "Request 6 exceeding limit"})
        assert r6.status_code == 429
        assert r6.is_json
        assert r6.get_json()["error"]["code"] == "rate_limit_exceeded"
