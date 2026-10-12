"""Unit tests and Hypothesis property-based fuzz tests for src/signals.py (Phase 12B).

Covers:
1. URL inspection: shorteners, IP hosts, punycode, suspicious TLDs, anchor text mismatch.
2. EML header parsing: SPF, DKIM, DMARC, From/Reply-To mismatch, hop counting.
3. Edge cases: empty text, huge text, malformed EML, unicode strings, emoji.
4. Risk score formula: capping, invariant guards (confident results never flip).
5. Sensitivity profiles: low/medium/high thresholds.
6. Hypothesis fuzz tests for robustness.
7. Zero user text logged verification.
"""

import email
import logging
from typing import Any, Dict, List
from hypothesis import given, settings, strategies as st
import pytest

from src.signals import (
    SHORTENER_DOMAINS,
    SUSPICIOUS_TLDS,
    compute_risk_score,
    extract_and_check_urls,
    extract_html_links,
    generate_key_findings,
    parse_eml_message,
)


# =============================================================================
# 1. URL Checks: Shorteners, IP Hosts, Punycode, TLDs, Mismatches
# =============================================================================

def test_url_shortener_detection():
    text = "Please review your document here: https://bit.ly/3xSample and https://tinyurl.com/secure123"
    urls, indicators = extract_and_check_urls(text)
    assert len(urls) >= 2
    shorteners = [u for u in urls if "shortener" in u["flags"]]
    assert len(shorteners) == 2
    shortener_indicators = [i for i in indicators if "Shortened link" in i["detail"]]
    assert len(shortener_indicators) >= 2


def test_url_ip_host_detection():
    text = "Urgent server update: http://192.168.1.100/admin and http://10.0.0.1:8080/portal"
    urls, indicators = extract_and_check_urls(text)
    ip_urls = [u for u in urls if "ip_host" in u["flags"]]
    assert len(ip_urls) == 2
    assert any(i["severity"] == "high" for i in indicators)


def test_url_punycode_detection():
    text = "Login to your account: https://xn--pypal-4ve.com/account"
    urls, indicators = extract_and_check_urls(text)
    puny_urls = [u for u in urls if "punycode" in u["flags"]]
    assert len(puny_urls) == 1
    assert any("Punycode" in i["detail"] for i in indicators)


def test_url_suspicious_tld_detection():
    text = "Win money today: http://claim-prize.top/win and http://lottery-winner.xyz"
    urls, indicators = extract_and_check_urls(text)
    tld_urls = [u for u in urls if "suspicious_tld" in u["flags"]]
    assert len(tld_urls) == 2


def test_link_text_vs_href_mismatch():
    html = """
    <p>Please log in to your account at:
    <a href="https://evil-phish.xyz/login">https://paypal.com/security</a>
    </p>
    """
    urls, indicators = extract_and_check_urls(text="", html_text=html)
    mismatches = [u for u in urls if "link_text_mismatch" in u["flags"]]
    assert len(mismatches) == 1
    assert any(i["severity"] == "critical" and "Phishing camouflage" in i["detail"] for i in indicators)


def test_clean_benign_urls():
    text = "Check our documentation at https://mailguard.ai/docs or https://python.org"
    urls, indicators = extract_and_check_urls(text)
    assert len(urls) == 2
    # Benign domains should have empty flags
    for u in urls:
        assert len(u["flags"]) == 0
    assert len(indicators) == 0


# =============================================================================
# 2. EML Header Parsing & Security Checks
# =============================================================================

def test_parse_clean_eml():
    eml = (
        "From: Alice <alice@example.com>\n"
        "To: Bob <bob@example.com>\n"
        "Subject: Project Kickoff Meeting\n"
        "Received: from mail.example.com by mx.example.com; Fri, 10 Oct 2026 10:00:00 +0000\n"
        "Received: from client.example.com by mail.example.com; Fri, 10 Oct 2026 09:59:00 +0000\n"
        "Authentication-Results: mx.example.com; spf=pass; dkim=pass; dmarc=pass\n"
        "Content-Type: text/plain; charset=utf-8\n"
        "\n"
        "Hi Bob, looking forward to our kickoff discussion tomorrow."
    )
    res = parse_eml_message(eml)
    assert res["subject"] == "Project Kickoff Meeting"
    assert "kickoff discussion" in res["body"]
    assert res["headers"] is not None
    assert res["headers"]["spf"] == "pass"
    assert res["headers"]["dkim"] == "pass"
    assert res["headers"]["dmarc"] == "pass"
    assert res["headers"]["from_reply_mismatch"] is False
    assert res["headers"]["hops"] == 2
    assert len(res["indicators"]) == 0


def test_parse_spoofed_eml_with_mismatch_and_spf_fail():
    eml = (
        "From: Security Team <security@bankofamerica.com>\n"
        "Reply-To: Collector <dropzone@hacker-server.net>\n"
        "Subject: Urgent: Verify Your Password\n"
        "Authentication-Results: mx.target.com; spf=fail; dkim=fail; dmarc=fail\n"
        "Content-Type: text/plain; charset=utf-8\n"
        "\n"
        "Your account is compromised. Click to update credentials."
    )
    res = parse_eml_message(eml)
    headers = res["headers"]
    assert headers["from_reply_mismatch"] is True
    assert headers["spf"] == "fail"
    assert headers["dmarc"] == "fail"
    # Should flag indicators
    indicators = res["indicators"]
    assert any("mismatch" in i["detail"] for i in indicators)
    assert any("SPF" in i["detail"] for i in indicators)
    assert any("DMARC" in i["detail"] for i in indicators)


def test_parse_multipart_eml():
    eml = (
        "From: News <news@tech.org>\n"
        "Subject: Tech Newsletter\n"
        "MIME-Version: 1.0\n"
        "Content-Type: multipart/alternative; boundary=\"boundary123\"\n"
        "\n"
        "--boundary123\n"
        "Content-Type: text/plain; charset=utf-8\n"
        "\n"
        "Plain text newsletter content.\n"
        "--boundary123\n"
        "Content-Type: text/html; charset=utf-8\n"
        "\n"
        "<p>HTML newsletter with <a href=\"https://tech.org\">link</a></p>\n"
        "--boundary123--"
    )
    res = parse_eml_message(eml)
    assert res["subject"] == "Tech Newsletter"
    assert "Plain text newsletter content" in res["body"]
    assert "<p>" in res["html_body"]


# =============================================================================
# 3. Edge Cases: Empty, Huge, Malformed EML, Unicode
# =============================================================================

def test_empty_and_whitespace_inputs():
    urls, inds = extract_and_check_urls("")
    assert urls == [] and inds == []

    urls, inds = extract_and_check_urls("   \n\t   ")
    assert urls == [] and inds == []

    eml_res = parse_eml_message("")
    assert eml_res["subject"] == ""
    assert eml_res["body"] == ""
    assert eml_res["headers"] is None


def test_huge_input_handling():
    huge_text = "Check this link: https://legit-site.com/item " * 2000
    urls, inds = extract_and_check_urls(huge_text)
    assert len(urls) == 1
    assert urls[0]["url"] == "https://legit-site.com/item"


def test_malformed_eml_does_not_crash():
    malformed = "This is not a valid email header line without colons.\r\n--unclosed_boundary\r\n\x00\x01\x02"
    res = parse_eml_message(malformed)
    assert isinstance(res, dict)
    assert "subject" in res
    assert "body" in res


def test_unicode_and_encoded_words_eml():
    eml = (
        "From: =?UTF-8?B?5bGx55Sw5aSq6YOO?= <yamada@example.jp>\n"
        "Subject: =?UTF-8?Q?=E7=B7=8A=E6=80=A5=E3=81=AE=E3=81=8A=E7=9F=A5=E3=82=89=E3=81=9B?=\n"
        "Content-Type: text/plain; charset=utf-8\n"
        "\n"
        "こんにちは世界 🚨 Important notice with emoji."
    )
    res = parse_eml_message(eml)
    assert "yamada@example.jp" in str(res)
    assert "こんにちは世界" in res["body"]


# =============================================================================
# 4. Risk Score Formula & Invariant Rules
# =============================================================================

def test_risk_score_base_calculation():
    # Model probability 0.85 -> base 85.0
    score, classification = compute_risk_score(0.85, [], sensitivity="medium")
    assert score == 85.0
    assert classification == "Spam"


def test_heuristic_bump_and_capping():
    # Model probability 0.50 -> base 50.0
    # Add indicators exceeding 15 points
    indicators = [
        {"type": "heuristic", "severity": "critical"},  # +8
        {"type": "heuristic", "severity": "critical"},  # +8 -> sum 16
        {"type": "heuristic", "severity": "high"},      # +5 -> sum 21
    ]
    score, classification = compute_risk_score(0.50, indicators, sensitivity="medium")
    # Capped at +15.0 -> 50.0 + 15.0 = 65.0
    assert score == 65.0
    assert classification == "Spam"  # > 60 in medium


def test_invariant_signals_never_flip_confident_ham():
    """Signals NEVER flip a confident model result alone.
    If probability < 0.20, maximum score is clamped to 35.0 (Safe), never Spam!
    """
    indicators = [
        {"type": "heuristic", "severity": "critical"},
        {"type": "heuristic", "severity": "critical"},
        {"type": "heuristic", "severity": "critical"},
    ]
    # Model is confident ham (0.05 probability)
    score, classification = compute_risk_score(0.05, indicators, sensitivity="medium")
    assert score <= 35.0
    assert classification == "Safe"


def test_invariant_signals_never_flip_confident_spam():
    """Confident spam (p > 0.80) never drops below 80.0."""
    score, classification = compute_risk_score(0.95, [], sensitivity="medium")
    assert score >= 80.0
    assert classification == "Spam"


def test_sensitivity_profiles():
    # Risk score 55.0
    # In low sensitivity: Safe < 50, Suspicious 50-70, Spam > 70 -> Suspicious
    # In medium sensitivity: Safe < 40, Suspicious 40-60, Spam > 60 -> Suspicious
    # In high sensitivity: Safe < 30, Suspicious 30-45, Spam > 45 -> Spam
    _, class_low = compute_risk_score(0.55, [], sensitivity="low")
    _, class_med = compute_risk_score(0.55, [], sensitivity="medium")
    _, class_high = compute_risk_score(0.55, [], sensitivity="high")

    assert class_low == "Suspicious"
    assert class_med == "Suspicious"
    assert class_high == "Spam"


# =============================================================================
# 5. Key Findings Synthesis
# =============================================================================

def test_key_findings_generation():
    findings = generate_key_findings(
        probability=0.02,
        classification="Safe",
        indicators=[],
        headers={"spf": "pass", "dkim": "pass", "hops": 2, "from_reply_mismatch": False},
        urls=[{"url": "https://example.com", "flags": []}],
    )
    assert len(findings) >= 2
    assert any("legitimate" in f.lower() for f in findings)
    assert any("zero suspicious domains" in f.lower() for f in findings)


# =============================================================================
# 6. Hypothesis Property-Based Fuzz Tests
# =============================================================================

@settings(max_examples=50, deadline=None)
@given(st.text())
def test_hypothesis_fuzz_extract_urls(text: str):
    urls, indicators = extract_and_check_urls(text)
    assert isinstance(urls, list)
    assert isinstance(indicators, list)


@settings(max_examples=50, deadline=None)
@given(st.text())
def test_hypothesis_fuzz_parse_eml(text: str):
    res = parse_eml_message(text)
    assert isinstance(res, dict)
    assert "subject" in res
    assert "body" in res


@settings(max_examples=50, deadline=None)
@given(
    prob=st.floats(allow_nan=True, allow_infinity=True),
    sensitivity=st.sampled_from(["low", "medium", "high", "invalid", ""]),
)
def test_hypothesis_fuzz_compute_risk_score(prob: float, sensitivity: str):
    score, classification = compute_risk_score(prob, [], sensitivity=sensitivity)
    assert 0.0 <= score <= 100.0
    assert classification in ("Safe", "Spam", "Suspicious")


# =============================================================================
# 7. Privacy: Zero User Input Logging Verification
# =============================================================================

def test_zero_user_text_logging(caplog):
    secret_marker = "SUPER_SECRET_PAYPAL_CREDENTIALS_987654"
    secret_url = f"https://bit.ly/{secret_marker}"

    with caplog.at_level(logging.DEBUG):
        urls, indicators = extract_and_check_urls(f"Check {secret_url}")
        parse_eml_message(f"From: me@test.com\nSubject: {secret_marker}\n\nSecret body")
        compute_risk_score(0.5, indicators)

    captured_logs = caplog.text
    assert secret_marker not in captured_logs
