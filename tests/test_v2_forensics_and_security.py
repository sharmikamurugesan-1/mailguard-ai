"""Unit tests for Phase 13-16: Advanced Email Forensics, URL & Attachment Intelligence,
and Cryptographic Evidence Digest.
"""

import json
import pytest

from src.app import create_app
from src.signals import extract_and_check_urls, parse_eml_message


@pytest.fixture
def client():
    app = create_app({"TESTING": True})
    return app.test_client()


def test_attachment_danger_detection_in_eml():
    """Verify that dangerous attachments (.exe, double extension) are flagged with critical severity."""
    raw_eml = (
        "From: billing@vendor.com\n"
        "To: victim@company.com\n"
        "Subject: Unpaid Invoice Notice\n"
        "MIME-Version: 1.0\n"
        "Content-Type: multipart/mixed; boundary=\"BOUNDARY\"\n"
        "\n"
        "--BOUNDARY\n"
        "Content-Type: text/plain\n"
        "\n"
        "Please review the attached overdue invoice immediately.\n"
        "--BOUNDARY\n"
        "Content-Type: application/octet-stream; name=\"invoice_doc.pdf.exe\"\n"
        "Content-Disposition: attachment; filename=\"invoice_doc.pdf.exe\"\n"
        "Content-Transfer-Encoding: base64\n"
        "\n"
        "TVoAAAAEA==\n"
        "--BOUNDARY--"
    )

    parsed = parse_eml_message(raw_eml)
    attachments = parsed.get("attachments", [])
    assert len(attachments) == 1
    att = attachments[0]
    assert att["filename"] == "invoice_doc.pdf.exe"
    assert att["is_suspicious"] is True
    assert "double extension" in att["threat_reason"] or "Executable" in att["threat_reason"]

    # Check indicator
    indicators = parsed.get("indicators", [])
    assert any(i["severity"] == "critical" and "invoice_doc.pdf.exe" in i["detail"] for i in indicators)


def test_display_name_spoofing_detection():
    """Verify display name spoofing (e.g. Name is 'security@paypal.com' but addr is 'bad@phish.net')."""
    raw_eml = (
        "From: \"service@paypal.com\" <bad-actor@attacker-host.net>\n"
        "To: user@target.org\n"
        "Subject: Account Warning\n"
        "\n"
        "Your account needs verification."
    )

    parsed = parse_eml_message(raw_eml)
    indicators = parsed.get("indicators", [])
    assert any(i["severity"] == "critical" and "Display-name spoofing" in i["detail"] for i in indicators)


def test_return_path_mismatch_and_routing_chain():
    """Verify Return-Path mismatch and routing chain extraction."""
    raw_eml = (
        "Received: from relay2.target.org [198.51.100.2] by mx.target.org; Fri, 10 Oct 2026 12:00:00 +0000\n"
        "Received: from relay1.source.org [203.0.113.1] by relay2.target.org; Fri, 10 Oct 2026 11:58:00 +0000\n"
        "From: Alice <alice@corporate.com>\n"
        "Return-Path: <bounce@unrelated-spammer.xyz>\n"
        "To: Bob <bob@target.org>\n"
        "Subject: Quarterly Update\n"
        "\n"
        "Attached is the update."
    )

    parsed = parse_eml_message(raw_eml)
    headers = parsed.get("headers", {})
    assert headers is not None
    assert headers.get("return_path_mismatch") is True
    assert headers.get("hop_count") == 2
    routing = headers.get("routing_chain", [])
    assert len(routing) == 2
    assert routing[0]["ip"] == "198.51.100.2"

    indicators = parsed.get("indicators", [])
    assert any("Return-Path" in i["detail"] for i in indicators)


def test_url_lookalike_and_dangerous_schemes():
    """Verify brand lookalike domains and dangerous schemes."""
    text = (
        "Please visit http://paypa1-security-login.xyz to verify your credentials. "
        "Also see javascript:alert(1) for bonus tokens."
    )
    urls, indicators = extract_and_check_urls(text)
    assert len(urls) >= 1
    flagged = [u for u in urls if "lookalike_domain" in u["flags"] or "suspicious_scheme" in u["flags"]]
    assert len(flagged) >= 1


def test_analyze_api_returns_evidence_sha256_and_attachments(client):
    """Verify POST /api/analyze returns evidence_sha256 and attachments array."""
    res = client.post("/api/analyze", json={"text": "Review agenda for next week."})
    assert res.status_code == 200
    data = res.get_json()
    assert "evidence_sha256" in data
    assert len(data["evidence_sha256"]) == 64  # Hex SHA-256 length
    assert "attachments" in data
    assert isinstance(data["attachments"], list)
