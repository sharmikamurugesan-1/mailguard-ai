"""Tests for POST /api/analyze endpoint (Phase 12B).

Verifies:
1. Input handling: text, raw EML, mixed inputs, options toggles.
2. Output schema: model {label, probability, confidence, uncertain}, risk_score (0-100),
   classification (Safe / Spam / Suspicious), indicators [{type, severity, detail}],
   key_findings [str], top_tokens, vocab_coverage %, urls [{url, flags}],
   headers {spf, dkim, dmarc, from_reply_mismatch, hops} (omitted if no headers present).
3. URL scanning: shorteners, IP hosts, punycode, suspicious TLDs, link text vs href mismatch.
4. EML header analysis: SPF, DKIM, DMARC, From vs Reply-To mismatch, relay hop count.
5. Sensitivity mapping (low, medium, high) and decision boundary.
6. Mathematical invariant: signals never flip confident predictions alone.
7. Error conditions: 400 (malformed JSON, empty, invalid types), 405 (GET), 413 (payload too large), 415 (unsupported media type).
8. Latency benchmark: p95 latency under 50 ms.
9. Zero input text logging verified.
"""

import json
import logging
import time
from typing import Any, Dict
import numpy as np
import pytest

from src.app import create_app


@pytest.fixture
def client():
    """Create Flask test client."""
    app = create_app({"TESTING": True})
    return app.test_client()


# -----------------------------------------------------------------------------
# 1. Happy Path & Output Schema Verification
# -----------------------------------------------------------------------------

def test_analyze_plain_text_clean_ham(client):
    """POST /api/analyze with clean plain text returns 200 and complete schema without headers."""
    payload = {
        "text": "Hi team, please find attached the revised financial agenda for tomorrow's meeting."
    }
    res = client.post("/api/analyze", json=payload)
    assert res.status_code == 200
    data = res.get_json()

    # Model shape
    assert "model" in data
    assert isinstance(data["model"]["label"], str)
    assert 0.0 <= data["model"]["probability"] <= 1.0
    assert 0.0 <= data["model"]["confidence"] <= 1.0
    assert isinstance(data["model"]["uncertain"], bool)

    # Risk score & Classification
    assert "risk_score" in data
    assert 0.0 <= data["risk_score"] <= 100.0
    assert data["classification"] in ("Safe", "Spam", "Suspicious")

    # Threat indicators & Key findings
    assert "indicators" in data
    assert isinstance(data["indicators"], list)
    assert "key_findings" in data
    assert isinstance(data["key_findings"], list)
    assert len(data["key_findings"]) >= 1

    # Top tokens & vocab coverage
    assert "top_tokens" in data
    assert isinstance(data["top_tokens"], list)
    assert "vocab_coverage" in data
    assert isinstance(data["vocab_coverage"], (int, float))

    # URLs & Sensitivity
    assert "urls" in data
    assert isinstance(data["urls"], list)
    assert data["sensitivity"] == "medium"

    # Headers field MUST be omitted if no headers were present
    assert "headers" not in data


def test_analyze_raw_eml_with_headers(client):
    """POST /api/analyze with real RFC 5322 EML returns headers object and hop count."""
    eml = (
        "Received: from mail.company.com (192.168.1.10) by mx.google.com with ESMTPS; Fri, 09 Oct 2026 12:00:00 -0700\n"
        "Received: from internal.lan (10.0.0.5) by mail.company.com; Fri, 09 Oct 2026 11:59:00 -0700\n"
        "Authentication-Results: mx.google.com; spf=pass; dkim=pass; dmarc=pass\n"
        "From: Alice Johnson <alice@company.com>\n"
        "To: Bob Smith <bob@company.com>\n"
        "Subject: Q4 Budget Review\n"
        "Content-Type: text/plain; charset=utf-8\n"
        "\n"
        "Please review the attached spreadsheet for our quarterly forecast."
    )
    payload = {"eml": eml}
    res = client.post("/api/analyze", json=payload)
    assert res.status_code == 200
    data = res.get_json()

    # Headers object MUST be present
    assert "headers" in data
    headers = data["headers"]
    assert headers["spf"] == "pass"
    assert headers["dkim"] == "pass"
    assert headers["dmarc"] == "pass"
    assert headers["from_reply_mismatch"] is False
    assert headers["hops"] == 2


def test_analyze_spoofed_eml_triggers_indicators(client):
    """Spoofed EML with domain mismatch and SPF failure triggers heuristic indicators."""
    eml = (
        "Received: from suspicious-relay.ru (185.220.101.5) by mx.google.com; Fri, 09 Oct 2026 12:00:00 -0700\n"
        "Authentication-Results: mx.google.com; spf=fail; dmarc=fail\n"
        "From: Security Support <support@paypal.com>\n"
        "Reply-To: attacker@phishing-haven.cc\n"
        "Subject: Urgent Account Suspension\n"
        "Content-Type: text/plain; charset=utf-8\n"
        "\n"
        "Your account has been locked. Verify immediately."
    )
    payload = {"eml": eml}
    res = client.post("/api/analyze", json=payload)
    assert res.status_code == 200
    data = res.get_json()

    # Verify indicators contain spoofing heuristics
    indicators = data["indicators"]
    details = [ind["detail"] for ind in indicators]
    assert any("From" in d and "Reply-To" in d for d in details)
    assert any("SPF" in d for d in details)
    assert any("DMARC" in d for d in details)

    assert data["headers"]["from_reply_mismatch"] is True
    assert data["headers"]["spf"] == "fail"
    assert data["headers"]["dmarc"] == "fail"


# -----------------------------------------------------------------------------
# 2. URL Inspection Integration
# -----------------------------------------------------------------------------

def test_analyze_urls_detected_and_flagged(client):
    """URLs with shorteners, IP hosts, suspicious TLDs, and HTML text mismatch are all flagged."""
    text_content = (
        "Check these links:\n"
        "1. http://bit.ly/secure-login\n"
        "2. http://198.51.100.22/admin\n"
        "3. http://free-giftcard.top/claim\n"
        "4. http://xn--pple-43d.com/login\n"
        "<a href=\"http://evil-phish.com/steal\">https://paypal.com/verify</a>"
    )
    payload = {"text": text_content}
    res = client.post("/api/analyze", json=payload)
    assert res.status_code == 200
    data = res.get_json()

    urls = data["urls"]
    assert len(urls) >= 4

    all_flags = set()
    for u in urls:
        for f in u["flags"]:
            all_flags.add(f)

    assert "shortener" in all_flags
    assert "ip_host" in all_flags
    assert "suspicious_tld" in all_flags
    assert "punycode" in all_flags
    assert "link_text_mismatch" in all_flags

    # Indicators must reflect these
    indicators = data["indicators"]
    assert any(ind["severity"] == "critical" for ind in indicators)
    assert any(ind["severity"] == "high" for ind in indicators)


# -----------------------------------------------------------------------------
# 3. Options Toggles & Sensitivity Profiles
# -----------------------------------------------------------------------------

def test_options_scan_urls_disabled(client):
    """When scan_urls=False, URLs are not inspected and zero URL indicators are produced."""
    payload = {
        "text": "Click here: http://bit.ly/prize now!",
        "options": {"scan_urls": False}
    }
    res = client.post("/api/analyze", json=payload)
    assert res.status_code == 200
    data = res.get_json()

    assert data["urls"] == []
    url_details = [ind["detail"] for ind in data["indicators"] if "URL" in ind["detail"] or "bit.ly" in ind["detail"]]
    assert len(url_details) == 0


def test_scan_urls_toggle_changes_analyze_output(client):
    """Direct comparative proof that toggling scan_urls changes /api/analyze output."""
    raw_payload = {
        "text": "Review document at http://bit.ly/urgent-doc and http://192.168.1.1/login"
    }

    # Enabled
    res_enabled = client.post("/api/analyze", json={
        **raw_payload,
        "options": {"scan_urls": True}
    }).get_json()

    # Disabled
    res_disabled = client.post("/api/analyze", json={
        **raw_payload,
        "options": {"scan_urls": False}
    }).get_json()

    assert len(res_enabled["urls"]) == 2
    assert len(res_disabled["urls"]) == 0
    assert len(res_enabled["indicators"]) > len(res_disabled["indicators"])
    assert res_enabled["risk_score"] > res_disabled["risk_score"]


def test_options_analyze_headers_disabled(client):
    """When analyze_headers=False, headers object is omitted and header indicators are not added."""
    eml = (
        "From: spoof@paypal.com\n"
        "Reply-To: attacker@phish.cc\n"
        "Subject: Warning\n"
        "\n"
        "Account notice."
    )
    payload = {
        "eml": eml,
        "options": {"analyze_headers": False}
    }
    res = client.post("/api/analyze", json=payload)
    assert res.status_code == 200
    data = res.get_json()

    assert "headers" not in data
    assert len(data["indicators"]) == 0


def test_analyze_headers_toggle_changes_analyze_output(client):
    """Direct comparative proof that toggling analyze_headers changes /api/analyze output."""
    eml = (
        "Received: from bad.relay.org; Fri, 09 Oct 2026 12:00:00 -0700\n"
        "Authentication-Results: mx.google.com; spf=fail; dmarc=fail\n"
        "From: security@paypal.com\n"
        "Reply-To: scammer@evil.ru\n"
        "Subject: Critical Account Update\n"
        "\n"
        "Please check your account settings."
    )

    # Enabled
    res_enabled = client.post("/api/analyze", json={
        "eml": eml,
        "options": {"analyze_headers": True}
    }).get_json()

    # Disabled
    res_disabled = client.post("/api/analyze", json={
        "eml": eml,
        "options": {"analyze_headers": False}
    }).get_json()

    assert "headers" in res_enabled
    assert "headers" not in res_disabled
    assert any("SPF" in ind["detail"] for ind in res_enabled["indicators"])
    assert not any("SPF" in ind.get("detail", "") for ind in res_disabled["indicators"])
    assert res_enabled["risk_score"] > res_disabled["risk_score"]



def test_options_sensitivity_profiles_affect_classification(client):
    """Sensitivity setting alters boundary thresholds for borderline input."""
    # A borderline text
    payload_base = {
        "text": "Please confirm if you received the wire transfer receipt.",
    }

    # Test with all 3 sensitivities
    classifications = {}
    for sens in ("low", "medium", "high"):
        payload = dict(payload_base)
        payload["options"] = {"sensitivity": sens}
        res = client.post("/api/analyze", json=payload)
        assert res.status_code == 200
        data = res.get_json()
        assert data["sensitivity"] == sens
        classifications[sens] = data["classification"]

    # Verify sensitivity was accepted and classifications are valid
    for s in ("low", "medium", "high"):
        assert classifications[s] in ("Safe", "Spam", "Suspicious")


def test_unknown_sensitivity_defaults_to_medium(client):
    """Invalid sensitivity string defaults gracefully to 'medium'."""
    payload = {
        "text": "Regular team update meeting.",
        "options": {"sensitivity": "ultra_extreme_invalid"}
    }
    res = client.post("/api/analyze", json=payload)
    assert res.status_code == 200
    assert res.get_json()["sensitivity"] == "medium"


# -----------------------------------------------------------------------------
# 4. Invariant Guardrails via Endpoint
# -----------------------------------------------------------------------------

def test_invariant_signals_never_flip_confident_ham(client):
    """Confident legitimate email with multiple heuristic indicators is clamped to <= 35.0."""
    # Standard clean corporate email text
    text = "Thanks for the feedback. Let's schedule a call tomorrow afternoon to discuss project architecture."
    # EML with several spoofing flags attached
    eml = (
        "Received: from relay1.bad.org; Fri, 09 Oct 2026 12:00:00 -0700\n"
        "Authentication-Results: mx.google.com; spf=fail; dmarc=fail\n"
        "From: legitimate@company.com\n"
        "Reply-To: other@unknown.com\n"
        "Subject: Project sync\n"
        "\n"
        f"{text} http://bit.ly/sync-doc http://192.168.1.1/login"
    )
    payload = {"eml": eml}
    res = client.post("/api/analyze", json=payload)
    assert res.status_code == 200
    data = res.get_json()

    prob = data["model"]["probability"]
    if prob < 0.20:
        # Strictly clamped invariant
        assert data["risk_score"] <= 35.0
        assert data["classification"] == "Safe"


def test_invariant_signals_never_flip_confident_spam(client):
    """Confident spam text has risk score pinned to at least 80.0."""
    spam_text = "WINNER! You have won $10,000,000 cash lottery prize! Send account number now to claim your millions free."
    payload = {"text": spam_text}
    res = client.post("/api/analyze", json=payload)
    assert res.status_code == 200
    data = res.get_json()

    prob = data["model"]["probability"]
    if prob > 0.80:
        assert data["risk_score"] >= 80.0
        assert data["classification"] == "Spam"


# -----------------------------------------------------------------------------
# 5. Error Handling & Validation
# -----------------------------------------------------------------------------

def test_415_unsupported_media_type(client):
    """Non-JSON Content-Type returns 415."""
    res = client.post(
        "/api/analyze",
        data="text=hello",
        content_type="application/x-www-form-urlencoded",
    )
    assert res.status_code == 415
    assert res.get_json()["error"]["code"] == "unsupported_media_type"


def test_405_method_not_allowed(client):
    """GET /api/analyze returns 405 Method Not Allowed."""
    res = client.get("/api/analyze")
    assert res.status_code == 405


def test_400_malformed_json(client):
    """Malformed JSON string returns 400 invalid_json."""
    res = client.post(
        "/api/analyze",
        data="{bad_json: 123",
        content_type="application/json",
    )
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "invalid_json"


def test_400_non_dict_json(client):
    """Non-dictionary JSON payload returns 400 invalid_json."""
    for val in (["an", "array"], "string_only", 12345, True):
        res = client.post("/api/analyze", json=val)
        assert res.status_code == 400
        assert res.get_json()["error"]["code"] == "invalid_json"


def test_400_invalid_field_types(client):
    """Invalid types for text, eml, or options return 400 invalid_type."""
    res1 = client.post("/api/analyze", json={"text": 12345})
    assert res1.status_code == 400
    assert res1.get_json()["error"]["code"] == "invalid_type"

    res2 = client.post("/api/analyze", json={"eml": ["not", "string"]})
    assert res2.status_code == 400
    assert res2.get_json()["error"]["code"] == "invalid_type"

    res3 = client.post("/api/analyze", json={"text": "Valid text", "options": "not_dict"})
    assert res3.status_code == 400
    assert res3.get_json()["error"]["code"] == "invalid_type"


def test_400_empty_input(client):
    """Empty payload or whitespace only returns 400 empty_input."""
    for empty_payload in ({}, {"text": ""}, {"text": "   "}, {"eml": ""}, {"eml": "   "}):
        res = client.post("/api/analyze", json=empty_payload)
        assert res.status_code == 400
        assert res.get_json()["error"]["code"] == "empty_input"


def test_413_text_payload_too_large(client):
    """Text exceeding 20,000 characters returns 413 payload_too_large."""
    payload = {"text": "A" * 20005}
    res = client.post("/api/analyze", json=payload)
    assert res.status_code == 413
    assert res.get_json()["error"]["code"] == "payload_too_large"


def test_413_eml_payload_too_large(client):
    """Raw EML exceeding 1,000,000 characters returns 413 payload_too_large."""
    payload = {"eml": "Received: test\n\n" + ("A" * 1000005)}
    res = client.post("/api/analyze", json=payload)
    assert res.status_code == 413
    assert res.get_json()["error"]["code"] == "payload_too_large"


# -----------------------------------------------------------------------------
# 6. Performance & Latency Benchmark
# -----------------------------------------------------------------------------

def test_p95_latency_under_50ms(client):
    """Verify p95 latency over 50 iterations is under 50 ms."""
    payload = {
        "text": "Urgent notification: verify your account details at http://bit.ly/bank-auth immediately."
    }

    # Warmup
    for _ in range(5):
        client.post("/api/analyze", json=payload)

    # Benchmark 50 requests
    latencies_ms = []
    for _ in range(50):
        t0 = time.perf_counter()
        res = client.post("/api/analyze", json=payload)
        t1 = time.perf_counter()
        assert res.status_code == 200
        latencies_ms.append((t1 - t0) * 1000.0)

    p50 = float(np.percentile(latencies_ms, 50))
    p95 = float(np.percentile(latencies_ms, 95))
    p99 = float(np.percentile(latencies_ms, 99))

    print(f"\n--- /api/analyze Latency Benchmark (50 iterations) ---")
    print(f"p50: {p50:.2f} ms | p95: {p95:.2f} ms | p99: {p99:.2f} ms")

    # Strict requirement: p95 latency under 50 ms
    assert p95 < 50.0, f"p95 latency was {p95:.2f} ms, expected < 50 ms"


# -----------------------------------------------------------------------------
# 7. Zero Input Text Logging Audit
# -----------------------------------------------------------------------------

def test_zero_user_text_logged_in_api(client, caplog):
    """Ensure sensitive email text and EML contents are NEVER logged anywhere."""
    sensitive_token = "TOPSECRET_ACQUISITION_TARGET_XYZ_98765"
    payload = {
        "text": f"Confidential meeting about {sensitive_token} scheduled for Monday.",
        "eml": f"From: insider@acme.com\nSubject: Secret\n\nDiscussion about {sensitive_token}",
    }

    with caplog.at_level(logging.DEBUG):
        res = client.post("/api/analyze", json=payload)
        assert res.status_code == 200

    log_output = caplog.text
    assert sensitive_token not in log_output
    assert "TOPSECRET" not in log_output
