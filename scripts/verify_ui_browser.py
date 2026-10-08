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
    print("MAILGUARD AI - PLAYWRIGHT REAL BROWSER UI VERIFICATION")
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

            # --- 1. Initial Page Load ---
            print("\n[Test 1] Loading initial page at 1280x800...")
            page.goto(BASE_URL)
            page.wait_for_selector("#status-text")
            # Wait for health check to complete
            page.wait_for_function("document.getElementById('status-text').textContent === 'Server Online'")
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
            # Fill with 20,050 characters
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
            # Give short moment for transition
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
            # Unroute
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
            # Reset card states with clear button first
            page.click("#clear-btn")
            held_routes = []

            def hold_predict_route(route):
                # Hold the route without completing it immediately so browser stays in loading state
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

            # Wait 5.2s for the waking banner timer to fire in the browser
            print("  Waiting 5.2s for waking banner to trigger...")
            page.wait_for_selector("#waking-banner:not(.hidden)", timeout=7000)
            banner_text = page.inner_text("#waking-banner")
            assert "waking up" in banner_text, f"Banner text mismatch: {banner_text}"
            page.screenshot(path=str(SCREENSHOT_DIR / "10_waking_banner_5s.png"))
            print(f"  ✓ Waking banner appeared at 5s: '{banner_text.strip()}'. Screenshot saved.")

            # Now release the held route so the request completes
            assert len(held_routes) > 0, "No route was captured"
            held_routes[0].continue_()

            # Wait for request to finish: button becomes re-enabled and result appears
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

            browser.close()
            print("\n" + "=" * 70)
            print("ALL 11 BROWSER UI VERIFICATION TESTS PASSED SUCCESSFULLY!")
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
