"""Robustness, security, edge-case hardening, and performance tests (Phase 8)."""

import concurrent.futures
import json
import re
import time
from pathlib import Path

import pytest
from src import config
from src.app import create_app
from src.predictor import get_predictor


@pytest.fixture
def client():
    """Test client with standard configuration."""
    app = create_app({"TESTING": True})
    return app.test_client()


# -----------------------------------------------------------------------------
# 1. Adversarial & Edge-Case Inputs (Fuzzing)
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("subject,body", [
    ("<script>alert('xss')</script>", "<img src=x onerror=alert(1)> Click here for free money"),
    ("SELECT * FROM emails WHERE 1=1;", "DROP TABLE users; -- malicious payload injection test"),
    ("Null byte test\x00injection", "Testing embedded \x00 null bytes in message text"),
    ("Unicode & CJK: こんにちは", "这是包含中文字符的测试邮件。Please review this document."),
    ("Emojis: 🚀🔥💰 Claim now!", "Congratulations 🎉 You won 1,000,000 USD! 🎁 Claim immediately 💸"),
    ("VeryLongContinuousWord", "A" * 600 + " please review"),
    ("Whitespace only subject", "   Valid body with meaningful words about quarterly budget   "),
    ("", "Body only without subject line provided"),
])
def test_adversarial_and_unusual_inputs(client, subject, body):
    """API safely handles adversarial, HTML, null byte, unicode, and extreme tokens without crashing."""
    response = client.post("/api/predict", json={"subject": subject, "body": body})
    assert response.status_code == 200
    assert response.is_json

    data = response.get_json()
    assert data["prediction"] in ("spam", "ham", "uncertain")
    assert isinstance(data["spam_probability"], float)
    assert 0.0 <= data["spam_probability"] <= 1.0

    # Ensure dangerous unescaped tags are not mirrored in raw text fields
    raw_response = response.get_data(as_text=True)
    assert "<script>" not in raw_response
    assert "<img" not in raw_response


# -----------------------------------------------------------------------------
# 2. Prediction Determinism
# -----------------------------------------------------------------------------

def test_prediction_determinism(client):
    """Submitting the exact same input 10 times yields bit-for-bit identical results."""
    payload = {
        "subject": "Scheduled Maintenance Notice - IT Department",
        "body": "All internal servers will be upgraded this Saturday at midnight. Please save your work.",
    }

    first_res = client.post("/api/predict", json=payload).get_json()

    for _ in range(9):
        res = client.post("/api/predict", json=payload).get_json()
        assert res["prediction"] == first_res["prediction"]
        assert res["spam_probability"] == first_res["spam_probability"]
        assert res["confidence"] == first_res["confidence"]
        assert res["risk_level"] == first_res["risk_level"]
        assert res["signals"] == first_res["signals"]
        assert res["reliability"] == first_res["reliability"]


# -----------------------------------------------------------------------------
# 3. Complete Schema & Type Validation
# -----------------------------------------------------------------------------

def test_prediction_schema_and_types(client):
    """POST /api/predict response conforms strictly to contract schema."""
    response = client.post(
        "/api/predict",
        json={"subject": "Inquiry", "body": "Could you provide details about the proposal?"},
    )
    assert response.status_code == 200
    data = response.get_json()

    # Required top-level keys
    required_keys = [
        "prediction",
        "label_display",
        "confidence",
        "spam_probability",
        "risk_level",
        "signals",
        "reliability",
        "dataset_type",
        "model_version",
    ]
    for key in required_keys:
        assert key in data, f"Missing key in response: {key}"

    assert data["prediction"] in ("spam", "ham", "uncertain")
    assert isinstance(data["label_display"], str)
    assert isinstance(data["confidence"], (float, int))
    assert isinstance(data["spam_probability"], (float, int))
    assert data["risk_level"] in ("low", "medium", "high")
    assert data["dataset_type"] == "email"
    assert isinstance(data["model_version"], str)

    # Signals structure
    assert isinstance(data["signals"], list)
    for sig in data["signals"]:
        assert isinstance(sig["term"], str)
        assert isinstance(sig["contribution"], (float, int))
        assert sig["direction"] in ("spam", "ham")
        assert sig["note"] == "top contributing term"

    # Reliability structure
    assert isinstance(data["reliability"], dict)
    assert data["reliability"]["level"] in ("low", "medium", "high")
    assert isinstance(data["reliability"]["warnings"], list)


# -----------------------------------------------------------------------------
# 4. Zero Path Leaks, Zero Stack Traces, Zero Overconfident Language
# -----------------------------------------------------------------------------

def test_zero_path_and_stack_trace_leaks(client):
    """Ensure no filesystem paths, stack traces, or misleading overconfidence appear in any response."""
    test_endpoints = [
        ("GET", "/", None),
        ("GET", "/api/health", None),
        ("GET", "/api/model-info", None),
        ("POST", "/api/predict", {"subject": "Test", "body": "Normal body text"}),
        ("POST", "/api/predict", {"subject": "Test"}),  # 400
        ("POST", "/api/predict", "not json"),  # 415 or 400
        ("GET", "/non-existent", None),  # 404
        ("GET", "/api/predict", None),  # 405
    ]

    forbidden_patterns = [
        r"C:\\",
        r"/Users/",
        r"/home/",
        r"/var/",
        r"Traceback \(most recent call last\)",
        r"\b100%\b",
        r"\bguaranteed\b",
        r"\bbulletproof\b",
    ]

    for method, path, payload in test_endpoints:
        if method == "GET":
            res = client.get(path)
        else:
            if isinstance(payload, dict):
                res = client.post(path, json=payload)
            else:
                res = client.post(path, data=payload, content_type="text/plain")

        text = res.get_data(as_text=True)
        for pattern in forbidden_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            assert not match, f"Forbidden pattern '{pattern}' found in {method} {path} response: {text[:200]}"


# -----------------------------------------------------------------------------
# 5. Startup Isolation (No Training or Raw Data Reads at Server Start)
# -----------------------------------------------------------------------------

def test_startup_no_raw_data_read_or_training(monkeypatch):
    """Starting server and loading predictor must never read raw data or invoke training."""
    raw_accessed = []

    # Monitor path access
    orig_open = open

    def tracking_open(file, *args, **kwargs):
        path_str = str(file).replace("\\", "/")
        if "data/raw" in path_str:
            raw_accessed.append(path_str)
        return orig_open(file, *args, **kwargs)

    monkeypatch.setattr("builtins.open", tracking_open)

    # Re-initialize predictor singleton
    predictor = get_predictor()
    assert predictor.pipeline is not None
    assert len(raw_accessed) == 0, f"Raw data was accessed during predictor load: {raw_accessed}"


# -----------------------------------------------------------------------------
# 6. Privacy: Zero User Subject or Body Text Logged
# -----------------------------------------------------------------------------

def test_privacy_zero_user_text_logged(client, caplog):
    """User input text (subject and body) is strictly confidential and never logged."""
    secret_subject = "CONFIDENTIAL_CODE_XYZ_98765"
    secret_body = "HIGHLY_SENSITIVE_PAYROLL_DATA_ACC_99881122"

    with caplog.at_level("INFO"):
        res = client.post(
            "/api/predict",
            json={"subject": secret_subject, "body": secret_body},
        )
        assert res.status_code == 200

    log_output = caplog.text
    assert secret_subject not in log_output, "Sensitive subject was leaked into application logs!"
    assert secret_body not in log_output, "Sensitive body text was leaked into application logs!"


# -----------------------------------------------------------------------------
# 7. Frontend Static Security & Integrity
# -----------------------------------------------------------------------------

def test_frontend_static_security_and_integrity():
    """Verify frontend uses safe DOM methods, no inline event handlers, and no external CDNs."""
    js_path = config.STATIC_DIR / "js" / "app.js"
    html_path = config.TEMPLATES_DIR / "index.html"
    css_path = config.STATIC_DIR / "css" / "style.css"

    js_code = js_path.read_text(encoding="utf-8")
    html_code = html_path.read_text(encoding="utf-8")
    css_code = css_path.read_text(encoding="utf-8")

    # 1. No innerHTML assignments in app.js (strict DOM manipulation via textContent / createElement)
    assert not re.search(r"\.innerHTML\s*=", js_code), "app.js should not assign to innerHTML; use textContent/createElement"

    # 2. No inline on* handlers in HTML
    inline_events = re.findall(r"\son\w+\s*=", html_code, re.IGNORECASE)
    assert len(inline_events) == 0, f"Inline event handlers found in index.html: {inline_events}"

    # 3. No external CDNs or external script/style references (100% self-contained)
    external_links = re.findall(r'(?:href|src)=["\']https?://[^"\']+', html_code)
    # The only external links allowed are informational links (like Github or Kaggle in footer/provenance)
    for link in external_links:
        assert not link.endswith(".js"), f"External script detected: {link}"
        assert not link.endswith(".css"), f"External CSS stylesheet detected: {link}"

    # 4. Zero CSS @import from external origins
    assert "@import" not in css_code or "http" not in css_code, "External @import detected in style.css"


# -----------------------------------------------------------------------------
# 8. Concurrency Smoke Test (20 Parallel Requests)
# -----------------------------------------------------------------------------

def test_concurrency_smoke_test(client):
    """API safely handles 20 concurrent prediction requests without deadlock or race condition."""
    def send_request(idx):
        payload = {
            "subject": f"Concurrent test {idx}",
            "body": f"This is request payload {idx} validating thread-safety and predictor throughput.",
        }
        res = client.post("/api/predict", json=payload)
        return res.status_code, res.get_json()

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(send_request, i) for i in range(20)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    for status_code, data in results:
        assert status_code == 200
        assert data["prediction"] in ("spam", "ham", "uncertain")
        assert 0.0 <= data["spam_probability"] <= 1.0


# -----------------------------------------------------------------------------
# 9. Latency Benchmark (p50 / p95 over 100 requests)
# -----------------------------------------------------------------------------

def test_prediction_latency_benchmark(client):
    """Benchmark prediction response times over 100 requests (p50, p95)."""
    latencies = []
    payload = {
        "subject": "Performance Benchmarking Check",
        "body": "Verifying production latency under standard email payload conditions across 100 sequential inferences.",
    }

    # Warmup
    client.post("/api/predict", json=payload)

    # 100 timed inferences
    for _ in range(100):
        t0 = time.perf_counter()
        res = client.post("/api/predict", json=payload)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        assert res.status_code == 200
        latencies.append(elapsed_ms)

    latencies.sort()
    p50 = latencies[49]
    p95 = latencies[94]
    p99 = latencies[98]

    # Save benchmark metrics to reports
    benchmark_report = {
        "n_requests": 100,
        "p50_ms": round(p50, 2),
        "p95_ms": round(p95, 2),
        "p99_ms": round(p99, 2),
        "min_ms": round(min(latencies), 2),
        "max_ms": round(max(latencies), 2),
    }

    report_path = config.REPORTS_DIR / "latency_benchmark.local.json"
    report_path.write_text(json.dumps(benchmark_report, indent=2), encoding="utf-8")

    # Assert p95 is under 100ms for lightweight local inference
    assert p95 < 100.0, f"p95 latency exceeded 100ms: {p95}ms"
