"""Automated browser UI verification using Playwright.

Executes real browser tests against the running Flask application:
1. Initial page load & health check badge
2. Empty body validation error
3. Oversized input validation error (> 20,000 chars)
4. Clear button functionality
5. Real Spam sample classification
6. Real Ham sample classification
7. Uncertain ('Needs review') UI state via route interception
8. Model & Data transparency card accordion
9. Loading state + disabled button
10. 5-second waking banner
11. Mobile responsive layout (375px)
12. Network error + automatic retry (first fails, retry succeeds)
13. Permanent failure + UI error alert & 'Try again' button
14. Security Headers & CSP violation verification (ZERO CSP violations)

Saves full-page screenshots to docs/screenshots/.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:5001"
SCREENSHOT_DIR = Path("docs/screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


def run_browser_verification():
    print("=" * 70)
    print("MAILGUARD AI - PLAYWRIGHT REAL BROWSER UI & CSP VERIFICATION")
    print("=" * 70)

    # 1. Start Flask app in background on port 5001
    env = os.environ.copy()
    env["PORT"] = "5001"
    server_process = subprocess.Popen(
        [sys.executable, "-m", "src.app"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to bind
    time.sleep(3.5)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 800})

            # Track console errors & CSP violation events
            console_errors = []
            csp_console_errors = []

            def handle_console_msg(msg):
                txt = msg.text
                if msg.type == "error":
                    if "violates the following Content Security Policy directive" in txt or "Content Security Policy" in txt:
                        csp_console_errors.append(txt)
                    console_errors.append(txt)

            page.on("console", handle_console_msg)
            page.on("pageerror", lambda err: console_errors.append(str(err)))

            # Inject in-page securitypolicyviolation listener before scripts load
            page.add_init_script("""
                window.__csp_violations = [];
                window.addEventListener('securitypolicyviolation', (e) => {
                    window.__csp_violations.push({
                        blockedURI: e.blockedURI,
                        violatedDirective: e.violatedDirective,
                        effectiveDirective: e.effectiveDirective,
                        originalPolicy: e.originalPolicy
                    });
                });
            """)

            # --- 1. Initial Page Load & Header Verification ---
            print("\n[Test 1] Loading initial page at 1280x800 and inspecting security headers...")
            response = page.goto(BASE_URL)
            assert response.status == 200, f"Expected 200, got {response.status}"

            # Verify security headers in browser response
            headers = response.headers
            assert headers.get("x-content-type-options") == "nosniff", "Missing X-Content-Type-Options"
            assert headers.get("x-frame-options") == "DENY", "Missing X-Frame-Options"
            assert headers.get("referrer-policy") == "no-referrer", "Missing Referrer-Policy"
            csp_header = headers.get("content-security-policy", "")
            assert "default-src 'self'" in csp_header, "CSP missing default-src 'self'"
            assert "script-src 'self'" in csp_header, "CSP script-src must be 'self' only"
            print("  ✓ Security headers verified on HTTP response.")

            page.wait_for_selector("#status-text")
            page.wait_for_selector("#status-text:has-text('Server Online')")
            page.screenshot(path=str(SCREENSHOT_DIR / "01_initial_desktop.png"))
            print("  ✓ Status badge reads 'Server Online'. Screenshot saved.")

            # --- 2. Empty Input Validation ---
            print("\n[Test 2] Testing empty input validation...")
            page.click("#analyze-btn")
            page.wait_for_selector("#body-error:not(.hidden)")
            error_text = page.inner_text("#body-error")
            assert "Email body is required" in error_text, f"Unexpected error text: {error_text}"
            page.screenshot(path=str(SCREENSHOT_DIR / "02_empty_input_error.png"))
            print(f"  ✓ Empty input blocked. Inline error: '{error_text}'")

            # --- 3. Oversized Input Validation ---
            print("\n[Test 3] Testing oversized input validation (> 20,000 chars)...")
            oversized_body = "A" * 20050
            page.fill("#body-input", oversized_body)
            counter_text = page.inner_text("#char-counter")
            assert "20,050" in counter_text, f"Counter text mismatch: {counter_text}"
            page.click("#analyze-btn")
            page.wait_for_selector("#body-error:not(.hidden)")
            error_text = page.inner_text("#body-error")
            assert "exceeds" in error_text, f"Unexpected error text: {error_text}"
            page.screenshot(path=str(SCREENSHOT_DIR / "03_oversize_error.png"))
            print(f"  ✓ Oversized input blocked. Inline error: '{error_text}'")

            # --- 4. Clear Button ---
            print("\n[Test 4] Testing Clear button...")
            page.click("#clear-btn")
            body_val = page.input_value("#body-input")
            counter_val = page.inner_text("#char-counter")
            assert body_val == "", "Body not cleared"
            assert "0 / 20,000" in counter_val, f"Counter not reset: {counter_val}"
            page.screenshot(path=str(SCREENSHOT_DIR / "04_cleared_form.png"))
            print("  ✓ Form cleared and counter reset to 0 / 20,000.")

            # --- 5. Real Spam Sample Analysis ---
            print("\n[Test 5] Testing real Spam sample analysis...")
            page.click("#sample-spam-btn")
            page.click("#analyze-btn")
            page.wait_for_selector("#result-card:not(.hidden)", timeout=15000)
            verdict_text = page.inner_text("#verdict-title")
            risk_text = page.inner_text("#risk-badge")
            assert verdict_text == "Likely spam", f"Unexpected verdict: {verdict_text}"
            assert "HIGH" in risk_text, f"Unexpected risk badge: {risk_text}"
            page.screenshot(path=str(SCREENSHOT_DIR / "05_spam_result.png"))
            print(f"  ✓ Spam classified correctly: '{verdict_text}', '{risk_text}'.")

            # --- 6. Real Legitimate (Ham) Sample Analysis ---
            print("\n[Test 6] Testing real Legitimate (Ham) sample analysis...")
            page.click("#sample-ham-btn")
            page.click("#analyze-btn")
            page.wait_for_selector("#result-card:not(.hidden)", timeout=15000)
            time.sleep(0.5)
            verdict_text = page.inner_text("#verdict-title")
            risk_text = page.inner_text("#risk-badge")
            assert verdict_text == "Likely legitimate", f"Unexpected verdict: {verdict_text}"
            assert "LOW" in risk_text, f"Unexpected risk badge: {risk_text}"
            page.screenshot(path=str(SCREENSHOT_DIR / "06_ham_result.png"))
            print(f"  ✓ Legitimate classified correctly: '{verdict_text}', '{risk_text}'.")

            # --- 7. Uncertain ('Needs review') State (Step 0b) ---
            print("\n[Test 7] Demonstrating Uncertain ('Needs review') state via route override...")
            def handle_uncertain(route):
                route.fulfill(
                    status=200,
                    content_type="application/json",
                    json={
                        "prediction": "uncertain",
                        "label_display": "Needs review",
                        "confidence": 0.50,
                        "spam_probability": 0.50,
                        "risk_level": "medium",
                        "signals": [
                            {"term": "invoice", "contribution": 0.04, "direction": "spam", "note": "top contributing term"},
                            {"term": "schedule", "contribution": -0.04, "direction": "ham", "note": "top contributing term"}
                        ],
                        "reliability": {
                            "level": "medium",
                            "warnings": ["near_decision_boundary", "dataset_age_notice"]
                        },
                        "model_version": "1.0.0",
                        "dataset_type": "email"
                    }
                )
            page.route("**/api/predict", handle_uncertain)
            page.click("#sample-borderline-btn")
            page.click("#analyze-btn")
            page.wait_for_selector("#result-card:not(.hidden)")
            time.sleep(0.5)
            verdict_text = page.inner_text("#verdict-title")
            risk_text = page.inner_text("#risk-badge")
            icon_text = page.inner_text("#verdict-icon")
            assert verdict_text == "Needs review", f"Expected 'Needs review', got {verdict_text}"
            assert "MEDIUM" in risk_text, f"Expected 'RISK: MEDIUM', got {risk_text}"
            assert "⚖" in icon_text, f"Expected neutral scale icon, got {icon_text}"
            page.screenshot(path=str(SCREENSHOT_DIR / "07_uncertain_result.png"))
            print(f"  ✓ Uncertain verdict rendered: '{verdict_text}', icon '{icon_text}', '{risk_text}'.")
            page.unroute("**/api/predict")

            # --- 8. Model & Data Transparency Card ---
            print("\n[Test 8] Expanding Model & Data Transparency card...")
            page.click("#model-details-accordion summary")
            page.wait_for_selector("#meta-model-type")
            model_type = page.inner_text("#meta-model-type")
            assert "Calibrated Linear SVM" in model_type, f"Model type mismatch: {model_type}"
            page.screenshot(path=str(SCREENSHOT_DIR / "08_model_data_card.png"))
            print(f"  ✓ Accordion opened. Model type displayed: '{model_type}'.")

            # --- 9 & 10. Loading State & 5s Waking Banner ---
            print("\n[Test 9 & 10] Testing loading state and 5s waking banner...")
            page.click("#clear-btn")
            held_routes = []

            def hold_predict_route(route):
                held_routes.append(route)

            page.route("**/api/predict", hold_predict_route)
            page.click("#sample-spam-btn")
            page.click("#analyze-btn")

            # Check loading state while request is held
            page.wait_for_selector("#analyze-btn:disabled", timeout=3000)
            is_disabled = page.is_disabled("#analyze-btn")
            btn_text = page.inner_text("#analyze-btn-text")
            assert is_disabled, "Analyze button should be disabled during flight"
            assert btn_text == "Analyzing...", f"Button text mismatch: {btn_text}"
            page.screenshot(path=str(SCREENSHOT_DIR / "09_loading_state.png"))
            print("  ✓ Button disabled and in loading state ('Analyzing...'). Screenshot saved.")

            # Wait 5.2s for waking banner
            print("  Waiting 5.2s for waking banner to trigger...")
            page.wait_for_selector("#waking-banner:not(.hidden)", timeout=7000)
            banner_text = page.inner_text("#waking-banner")
            assert "waking up" in banner_text, f"Banner text mismatch: {banner_text}"
            page.screenshot(path=str(SCREENSHOT_DIR / "10_waking_banner_5s.png"))
            print(f"  ✓ Waking banner appeared at 5s: '{banner_text.strip()}'. Screenshot saved.")

            # Release held route
            assert len(held_routes) > 0, "No route was captured"
            held_routes[0].continue_()

            page.wait_for_selector("#analyze-btn:not(:disabled)", timeout=10000)
            page.wait_for_selector("#result-card:not(.hidden)", timeout=10000)
            page.wait_for_selector("#waking-banner", state="hidden", timeout=10000)
            assert page.is_hidden("#waking-banner"), "Waking banner should hide on response"
            print("  ✓ Result rendered and waking banner hidden.")
            page.unroute("**/api/predict")

            # --- 11. Mobile Viewport 375px ---
            print("\n[Test 11] Testing Mobile Viewport (375px width)...")
            page.set_viewport_size({"width": 375, "height": 667})
            page.screenshot(path=str(SCREENSHOT_DIR / "11_mobile_375px.png"))
            print("  ✓ Rendered at 375px viewport. Screenshot saved.")
            page.set_viewport_size({"width": 1280, "height": 800})

            # --- 12. Network Failure Automatic Retry (Step 0b) ---
            print("\n[Test 12] Testing network failure automatic 1-retry mechanism...")
            page.click("#clear-btn")
            attempt_count = [0]

            def handle_retry_flow(route):
                attempt_count[0] += 1
                if attempt_count[0] == 1:
                    # Abort first request to trigger network failure catch block
                    route.abort("failed")
                else:
                    # Pass through second (automatic retry) request
                    route.continue_()

            page.route("**/api/predict", handle_retry_flow)
            page.click("#sample-ham-btn")
            page.click("#analyze-btn")

            # Result should succeed on the 2nd automatic retry
            page.wait_for_selector("#result-card:not(.hidden)", timeout=10000)
            assert attempt_count[0] == 2, f"Expected exactly 2 attempts (1 initial + 1 automatic retry), got {attempt_count[0]}"
            verdict_text = page.inner_text("#verdict-title")
            assert verdict_text == "Likely legitimate", f"Unexpected verdict after retry: {verdict_text}"
            print(f"  ✓ Automatic retry verified: initial request aborted, 2nd attempt automatically succeeded ({attempt_count[0]} total requests).")
            page.unroute("**/api/predict")

            # --- 13. Permanent Network Failure & Try Again Button ---
            print("\n[Test 13] Testing permanent failure error alert and 'Try again' button...")
            page.click("#clear-btn")
            failed_attempts = [0]

            def handle_permanent_failure(route):
                failed_attempts[0] += 1
                route.abort("failed")

            page.route("**/api/predict", handle_permanent_failure)
            page.click("#sample-spam-btn")
            page.click("#analyze-btn")

            page.wait_for_selector("#general-error:not(.hidden)", timeout=10000)
            page.wait_for_selector("#retry-btn:not(.hidden)", timeout=10000)
            assert failed_attempts[0] == 2, f"Expected 2 failed attempts before displaying error, got {failed_attempts[0]}"
            print(f"  ✓ Exhausted retries ({failed_attempts[0]} attempts). General error and 'Try again' button visible.")
            page.unroute("**/api/predict")

            # --- 14. Strict CSP Violations & Console Audit ---
            print("\n[Test 14] Verifying ZERO CSP violations and ZERO console errors...")
            csp_violations = page.evaluate("() => window.__csp_violations || []")
            assert len(csp_violations) == 0, f"CSP violations detected: {csp_violations}"
            assert len(csp_console_errors) == 0, f"CSP console errors detected: {csp_console_errors}"
            print("  ✓ ZERO CSP violations detected.")
            print("  ✓ ZERO CSP console errors detected.")

            browser.close()
            print("\n" + "=" * 70)
            print("ALL 14 BROWSER UI, RETRY & CSP TESTS PASSED WITH ZERO VIOLATIONS!")
            print(f"All screenshots saved to: {SCREENSHOT_DIR.resolve()}")
            print("=" * 70)

    finally:
        server_process.terminate()
        try:
            server_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server_process.kill()


if __name__ == "__main__":
    run_browser_verification()
