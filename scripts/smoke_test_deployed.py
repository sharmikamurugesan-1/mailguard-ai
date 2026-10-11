"""Standalone smoke test script for deployed MailGuard AI service.

Uses ONLY Python standard library (urllib, json, sys, time) so it can run
in any environment (CI, deployment verification, developer machine) without
requiring third-party HTTP client libraries like requests.
"""

import json
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional, Tuple


def make_request(
    url: str,
    method: str = "GET",
    data: Optional[Dict[str, Any]] = None,
    timeout: float = 30.0,
) -> Tuple[int, Dict[str, Any], str]:
    """Execute an HTTP request using urllib.request and return (status, json_data, raw_text)."""
    headers = {"User-Agent": "MailGuard-SmokeTest/1.0"}
    encoded_data = None
    if data is not None:
        headers["Content-Type"] = "application/json"
        encoded_data = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            raw_text = resp.read().decode("utf-8")
            try:
                json_data = json.loads(raw_text)
            except Exception:
                json_data = {}
            return status, json_data, raw_text
    except urllib.error.HTTPError as e:
        status = e.code
        raw_text = e.read().decode("utf-8")
        try:
            json_data = json.loads(raw_text)
        except Exception:
            json_data = {}
        return status, json_data, raw_text
    except Exception as e:
        return 0, {}, str(e)


def run_smoke_tests(base_url: str) -> bool:
    """Run full suite of HTTP smoke tests against target base URL."""
    base_url = base_url.rstrip("/")
    print("=" * 70)
    print(f"MAILGUARD AI - DEPLOYMENT SMOKE TEST: {base_url}")
    print("=" * 70)

    all_passed = True
    start_total = time.time()

    tests = []

    # 1. Health check
    def test_health():
        url = f"{base_url}/api/health"
        status, data, _ = make_request(url)
        passed = (
            status == 200
            and data.get("status") == "healthy"
            and data.get("model_loaded") is True
        )
        return "GET /api/health", status, passed, f"status={data.get('status')}, model_loaded={data.get('model_loaded')}"

    tests.append(test_health)

    # 2. Model info
    def test_model_info():
        url = f"{base_url}/api/model-info"
        status, data, _ = make_request(url)
        model_name = data.get("model_type") or data.get("selected_model")
        passed = (
            status == 200
            and model_name is not None
            and "dataset_type" in data
            and data.get("dataset_type") == "email"
        )
        return "GET /api/model-info", status, passed, f"model={model_name}, type={data.get('dataset_type')}"

    tests.append(test_model_info)

    # 3. HTML Landing page
    def test_index_page():
        url = f"{base_url}/"
        status, _, raw = make_request(url)
        passed = status == 200 and "MailGuard AI" in raw and "<html" in raw.lower()
        return "GET /", status, passed, f"length={len(raw)} bytes, title present"

    tests.append(test_index_page)

    # 4. Predict Ham
    def test_predict_ham():
        url = f"{base_url}/api/predict"
        payload = {
            "subject": "Team meeting tomorrow at 10am",
            "body": "Hi everyone, please review the attached project schedule for our sprint review.",
        }
        status, data, _ = make_request(url, method="POST", data=payload)
        passed = (
            status == 200
            and data.get("prediction") == "ham"
            and data.get("risk_level") == "low"
            and isinstance(data.get("spam_probability"), (int, float))
            and data.get("spam_probability", 1.0) < 0.40
        )
        prob = round(data.get("spam_probability", 0.0), 4)
        return "POST /api/predict (Ham)", status, passed, f"prediction={data.get('prediction')}, P(spam)={prob}"

    tests.append(test_predict_ham)

    # 5. Predict Spam
    def test_predict_spam():
        url = f"{base_url}/api/predict"
        payload = {
            "subject": "FREE VIAGRA ONLINE PHARMACY BONUS",
            "body": "Click here to claim your free cash prize and discount pharmaceuticals right now!",
        }
        status, data, _ = make_request(url, method="POST", data=payload)
        passed = (
            status == 200
            and data.get("prediction") == "spam"
            and data.get("risk_level") == "high"
            and isinstance(data.get("spam_probability"), (int, float))
            and data.get("spam_probability", 0.0) > 0.60
        )
        prob = round(data.get("spam_probability", 0.0), 4)
        return "POST /api/predict (Spam)", status, passed, f"prediction={data.get('prediction')}, P(spam)={prob}"

    tests.append(test_predict_spam)

    # 6. Validation Error (empty input)
    def test_validation_error():
        url = f"{base_url}/api/predict"
        payload = {"subject": "", "body": ""}
        status, data, _ = make_request(url, method="POST", data=payload)
        passed = status == 400 and "error" in data
        return "POST /api/predict (Validation Error)", status, passed, f"status={status}, error='{data.get('error', {}).get('message', '')}'"

    tests.append(test_validation_error)

    # 7. Analyze endpoint (v2 full analysis pipeline)
    def test_analyze():
        url = f"{base_url}/api/analyze"
        payload = {
            "subject": "Quick smoke check",
            "body": "This is a legitimate test message for smoke testing.",
        }
        status, data, _ = make_request(url, method="POST", data=payload)
        passed = (
            status == 200
            and "verdict" in data
            and "risk_score" in data
            and "probabilities" in data
        )
        return "POST /api/analyze (v2 Analyze)", status, passed, f"verdict={data.get('verdict')}, risk={data.get('risk_score')}"

    tests.append(test_analyze)

    # Execute all tests
    for test_fn in tests:
        t0 = time.time()
        name, status_code, passed, details = test_fn()
        elapsed = round((time.time() - t0) * 1000, 1)
        tag = "[PASS]" if passed else "[FAIL]"
        if not passed:
            all_passed = False
        print(f"{tag:7} {name:<35} HTTP {status_code:<4} {elapsed:>6}ms | {details}")

    total_elapsed = round(time.time() - start_total, 2)
    print("-" * 70)
    if all_passed:
        print(f"RESULT: ALL {len(tests)} SMOKE TESTS PASSED ({total_elapsed}s total)")
        print("=" * 70)
        return True
    else:
        print(f"RESULT: ONE OR MORE SMOKE TESTS FAILED ({total_elapsed}s total)")
        print("=" * 70)
        return False


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000"
    success = run_smoke_tests(target)
    sys.exit(0 if success else 1)
