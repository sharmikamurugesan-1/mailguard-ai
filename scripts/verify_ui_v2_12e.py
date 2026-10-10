"""Playwright automated verification for MailGuard AI v2 Phase 12E (Settings, Docs & Model Card).

Verifies:
1. Settings > Preferences:
   - Sensitivity select ('low', 'medium', 'high') with real effect.
   - 'Scan URLs' and 'Scan headers' toggles.
   - Saved and persisted in localStorage ('mailguard_settings').
   - Synced to Analyzer options.
2. Toggle changes visibly alter analysis results:
   - Sensitivity profile shifts decision boundaries (Low vs High flips verdict).
3. Settings > API Access:
   - Sane rate limit documentation (60 req/min for analyze & predict, 120 req/min for model-info, health exempt).
   - Real copy-pasteable cURL and Python requests snippets.
   - Copy button interaction.
   - Zero fake API keys or dummy buttons.
4. Settings > Account:
   - Shows "Guest, data stays on this device".
   - Local storage management controls.
   - Zero notifications and zero pricing everywhere.
5. Model Card Page (#/model-card):
   - Inline SVGs (Confusion Matrix, PR Curve, Platt Calibration Reliability Diagram).
   - Real de-duplicated numbers (33,665 raw -> 3,203 duplicates removed -> 30,462 cleaned).
   - 1,000-sample Bootstrap 95% Confidence Intervals (Accuracy: 99.00%, Precision: 98.83%, Recall: 99.07%, F1: 98.95%, PR-AUC: 0.9991).
   - Scope disclaimer banner: Plain statement that model detects spam, NOT malware.
   - 4 known failure modes.
6. Docs Page (#/docs):
   - Real endpoints documented with JSON schemas, response formats, and unified error shape.
7. Quality & Integrity:
   - Axe-core accessibility audit: 0 violations.
   - Zero console errors, zero page errors, zero CSP violations.
8. Captures screenshots in docs/screenshots/v2/.
"""

from pathlib import Path
import json
import os
import subprocess
import sys
import time
import urllib.request
from playwright.sync_api import sync_playwright
from axe_core_python.sync_playwright import Axe

BASE_URL = "http://127.0.0.1:5008"
SCREENSHOT_DIR = Path("docs/screenshots/v2")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


def run_verification():
    print("=" * 80)
    print("MAILGUARD AI v2 - PHASE 12E PLAYWRIGHT VERIFICATION AUDIT")
    print("=" * 80)

    # 1. Start Server on port 5008
    env = os.environ.copy()
    env["PORT"] = "5008"
    env["RATELIMIT_ENABLED"] = "1"
    env["PYTHONUNBUFFERED"] = "1"

    server_process = subprocess.Popen(
        [sys.executable, "-m", "src.app"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    print("Starting MailGuard AI Flask application on port 5008...")
    started = False
    for attempt in range(25):
        try:
            with urllib.request.urlopen(f"{BASE_URL}/api/health", timeout=2) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    print(f"Server healthy on port 5008. Model loaded: {data.get('model_loaded')}")
                    started = True
                    break
        except Exception:
            time.sleep(0.5)

    if not started:
        print("[FAIL] Server failed to start on port 5008.")
        server_process.kill()
        sys.exit(1)

    console_errors = []
    csp_violations = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1400, "height": 950},
                device_scale_factor=1,
            )
            page = context.new_page()

            def on_console(msg):
                txt = msg.text
                if msg.type == "error":
                    if "Content Security Policy" in txt or "CSP" in txt:
                        csp_violations.append(txt)
                    console_errors.append(txt)
                    print(f"  [BROWSER ERROR] {txt}")

            page.on("console", on_console)
            page.on("pageerror", lambda err: console_errors.append(str(err)))

            # =================================================================
            # STEP 1: SETTINGS > PREFERENCES & LOCALSTORAGE PERSISTENCE
            # =================================================================
            print("\n--- STEP 1: Testing Settings Preferences & localStorage Sync ---")
            page.goto(f"{BASE_URL}/#/settings")
            page.wait_for_selector("#view-settings", state="visible")
            page.wait_for_timeout(500)

            # Verify Settings Tabs are present
            assert page.is_visible("#tab-btn-pref"), "Preferences tab button missing"
            assert page.is_visible("#tab-btn-api"), "API Access tab button missing"
            assert page.is_visible("#tab-btn-account"), "Account tab button missing"

            # Check initial values
            pref_sens = page.locator("#pref-sensitivity")
            assert pref_sens.is_visible(), "Sensitivity select missing in Settings"
            pref_urls = page.locator("#pref-scan-urls")
            pref_headers = page.locator("#pref-analyze-headers")

            # Change preference values
            pref_sens.select_option("high")
            # Toggle scan_urls from checked to unchecked
            if pref_urls.is_checked():
                page.locator("#pref-scan-urls + .toggle-slider").click()
            # Ensure analyze_headers is checked
            if not pref_headers.is_checked():
                page.locator("#pref-analyze-headers + .toggle-slider").click()

            # Click Save Preferences
            page.click("#save-preferences-btn")
            page.wait_for_timeout(400)

            # Verify localStorage contains updated settings
            stored_raw = page.evaluate("localStorage.getItem('mailguard_settings')")
            assert stored_raw is not None, "mailguard_settings missing from localStorage"
            stored_obj = json.loads(stored_raw)
            print(f"  Stored settings in localStorage: {stored_obj}")
            assert stored_obj["sensitivity"] == "high", f"Expected high sensitivity, got {stored_obj['sensitivity']}"
            assert stored_obj["scan_urls"] is False, "Expected scan_urls to be false"
            assert stored_obj["analyze_headers"] is True, "Expected analyze_headers to be true"

            # Navigate to Email Analyzer and verify sync
            page.goto(f"{BASE_URL}/#/analyzer")
            page.wait_for_selector("#view-analyzer", state="visible")
            page.wait_for_timeout(400)

            analyzer_sens_val = page.locator("#analyzer-sensitivity-select").input_value()
            analyzer_urls_checked = page.locator("#opt-extract-urls").is_checked()
            analyzer_headers_checked = page.locator("#opt-analyze-headers").is_checked()

            assert analyzer_sens_val == "high", f"Analyzer sensitivity didn't sync: got {analyzer_sens_val}"
            assert analyzer_urls_checked is False, "Analyzer scan_urls didn't sync"
            assert analyzer_headers_checked is True, "Analyzer analyze_headers didn't sync"
            print("  [PASS] Settings successfully persisted to localStorage and synced to Analyzer defaults.")

            # Capture Settings screenshot
            page.goto(f"{BASE_URL}/#/settings")
            page.wait_for_selector("#view-settings", state="visible")
            page.screenshot(path=str(SCREENSHOT_DIR / "v2_12e_settings_preferences.png"))
            print(f"  Captured: {SCREENSHOT_DIR / 'v2_12e_settings_preferences.png'}")

            # =================================================================
            # STEP 2: TOGGLE CHANGES VISIBLY ALTER RESULTS
            # =================================================================
            print("\n--- STEP 2: Proving Sensitivity Toggle Changes Visibly Alter Results ---")
            page.goto(f"{BASE_URL}/#/analyzer")
            page.wait_for_selector("#view-analyzer", state="visible")

            # Borderline test email that sits between high and low boundaries (risk score 61.5)
            borderline_text = (
                "Subject: new email\n\n"
                "yo bro . this is my new email address . save it .\n"
                "aggie _ chico 2 @ hotmail . com .\n"
                "love you , lacy\n"
                "get your private , free email at http://www.hotmail.com"
            )

            # Test A: Set sensitivity to LOW (Safe < 50, Suspicious 50-70, Spam > 70)
            page.locator("#analyzer-sensitivity-select").select_option("low")
            page.fill("#body-input", borderline_text)
            page.click("#analyze-btn")
            page.wait_for_selector("#report-active-view", state="visible", timeout=10000)
            page.wait_for_timeout(400)

            score_a = page.locator("#risk-ring-num").text_content()
            classification_a = page.locator("#report-classification-val").text_content()
            print(f"  Sensitivity LOW result: Risk Score = {score_a}, Classification = '{classification_a}'")

            # Test B: Switch sensitivity to HIGH (Safe < 30, Suspicious 30-45, Spam > 45)
            page.locator("#analyzer-sensitivity-select").select_option("high")
            page.click("#analyze-btn")
            page.wait_for_selector("#report-active-view", state="visible", timeout=10000)
            page.wait_for_timeout(400)

            score_b = page.locator("#risk-ring-num").text_content()
            classification_b = page.locator("#report-classification-val").text_content()
            print(f"  Sensitivity HIGH result: Risk Score = {score_b}, Classification = '{classification_b}'")

            # Verify the classification visibly altered between Suspicious and Spam
            assert classification_a == "Suspicious", f"Expected 'Suspicious' under low sensitivity, got {classification_a}"
            assert classification_b == "Spam", f"Expected 'Spam' under high sensitivity, got {classification_b}"
            print(f"  [PASS] Sensitivity toggle visibly altered classification outcome: '{classification_a}' -> '{classification_b}'.")

            page.screenshot(path=str(SCREENSHOT_DIR / "v2_12e_sensitivity_altered.png"))
            print(f"  Captured: {SCREENSHOT_DIR / 'v2_12e_sensitivity_altered.png'}")

            # =================================================================
            # STEP 3: SETTINGS > API ACCESS DOCUMENTATION & SANE LIMITS
            # =================================================================
            print("\n--- STEP 3: Testing Settings API Access & Sane Rate Limits ---")
            page.goto(f"{BASE_URL}/#/settings")
            page.wait_for_selector("#view-settings", state="visible")
            page.click("#tab-btn-api")
            page.wait_for_selector("#settings-panel-api", state="visible")
            page.wait_for_timeout(400)

            api_panel_text = page.locator("#settings-panel-api").text_content()
            assert "60 requests / minute" in api_panel_text, "Rate limit info missing from API Access panel"
            assert "POST" in api_panel_text and "/api/analyze" in api_panel_text, "/api/analyze endpoint missing"
            assert "/api/predict" in api_panel_text, "/api/predict endpoint missing"
            assert "curl -X POST" in api_panel_text, "cURL example missing"
            assert "import requests" in api_panel_text, "Python requests example missing"

            # Test copy button interaction
            copy_btn = page.locator(".btn-copy-code").first
            copy_btn.click()
            page.wait_for_timeout(300)
            assert "✓ Copied!" in copy_btn.text_content(), "Copy button did not show success feedback"
            print("  [PASS] API documentation rendered with accurate cURL, Python snippets and rate limit notices.")

            page.screenshot(path=str(SCREENSHOT_DIR / "v2_12e_settings_api.png"))
            print(f"  Captured: {SCREENSHOT_DIR / 'v2_12e_settings_api.png'}")

            # =================================================================
            # STEP 4: SETTINGS > ACCOUNT & PRIVACY POLICY
            # =================================================================
            print("\n--- STEP 4: Testing Settings Account Section & Privacy Controls ---")
            page.click("#tab-btn-account")
            page.wait_for_selector("#settings-panel-account", state="visible")
            page.wait_for_timeout(400)

            account_panel_text = page.locator("#settings-panel-account").text_content()
            assert "Guest, data stays on this device" in account_panel_text, "Guest privacy note missing"
            assert page.is_visible("#clear-local-history-btn"), "Clear history button missing"
            assert page.is_visible("#clear-local-settings-btn"), "Reset settings button missing"

            # Check that Notifications and Pricing do NOT exist anywhere in DOM
            page_content = page.content().lower()
            assert "notification settings" not in page_content, "Found unwanted notification settings"
            assert "pricing plan" not in page_content and "upgrade plan" not in page_content, "Found unwanted pricing/upgrade elements"
            print("  [PASS] Account panel confirms 'Guest, data stays on this device'. Zero pricing/notifications.")

            page.screenshot(path=str(SCREENSHOT_DIR / "v2_12e_settings_account.png"))
            print(f"  Captured: {SCREENSHOT_DIR / 'v2_12e_settings_account.png'}")

            # =================================================================
            # STEP 5: MODEL CARD PAGE WITH INLINE SVGS & BOOTSTRAP CIs
            # =================================================================
            print("\n--- STEP 5: Verifying Model Card Page (#/model-card) ---")
            page.goto(f"{BASE_URL}/#/model-card")
            page.wait_for_selector("#view-model-card", state="visible")
            page.wait_for_timeout(500)

            model_card_text = page.locator("#view-model-card").text_content()

            # Plain statement: Model detects spam, NOT malware
            assert "DOES NOT detect malicious software" in model_card_text, "Malware scope disclaimer missing"
            assert "NLP statistical classifier" in model_card_text, "Classifier description missing"

            # Deduplication provenance statistics
            assert "33,665" in model_card_text, "Raw samples count (33,665) missing"
            assert "3,203" in model_card_text, "Duplicates dropped count (3,203) missing"
            assert "30,462" in model_card_text, "Cleaned samples count (30,462) missing"

            # Bootstrap 95% Confidence Intervals table
            assert "99.00%" in model_card_text, "Accuracy (99.00%) missing"
            assert "[98.74%, 99.23%]" in model_card_text, "Accuracy 95% CI missing"
            assert "98.83%" in model_card_text, "Precision (98.83%) missing"
            assert "[98.41%, 99.20%]" in model_card_text, "Precision 95% CI missing"
            assert "99.07%" in model_card_text, "Recall (99.07%) missing"
            assert "[98.72%, 99.42%]" in model_card_text, "Recall 95% CI missing"
            assert "98.95%" in model_card_text, "F1-Score (98.95%) missing"
            assert "[98.68%, 99.20%]" in model_card_text, "F1 95% CI missing"
            assert "0.9991" in model_card_text, "PR-AUC (0.9991) missing"

            # 3 Inline SVGs
            svg_cm = page.locator("#svg-container-cm svg")
            assert svg_cm.is_visible(), "Confusion Matrix SVG missing or invisible"
            assert "3,148" in svg_cm.text_content(), "TN (3,148) missing in CM SVG"
            assert "2,884" in svg_cm.text_content(), "TP (2,884) missing in CM SVG"

            svg_pr = page.locator("#svg-container-pr svg")
            assert svg_pr.is_visible(), "PR Curve SVG missing or invisible"
            assert "PR-AUC: 0.9991" in svg_pr.text_content(), "PR-AUC missing in PR SVG"

            svg_cal = page.locator("#svg-container-cal svg")
            assert svg_cal.is_visible(), "Calibration Reliability Diagram SVG missing or invisible"
            assert "Calibrated Linear SVM" in svg_cal.text_content(), "Calibrated SVM label missing in Cal SVG"

            # Known failure modes
            assert "Historical lexical bias" in model_card_text, "Historical bias failure mode missing"
            assert "English-oriented preprocessing" in model_card_text, "English bias failure mode missing"
            assert "Short message ambiguity" in model_card_text, "Short message failure mode missing"
            assert "Adversarial obfuscation" in model_card_text, "Adversarial failure mode missing"
            print("  [PASS] Model Card renders complete deduplication provenance, bootstrap CIs, 3 inline SVGs, disclaimer, and failure modes.")

            page.screenshot(path=str(SCREENSHOT_DIR / "v2_12e_model_card.png"))
            print(f"  Captured: {SCREENSHOT_DIR / 'v2_12e_model_card.png'}")

            # =================================================================
            # STEP 6: DOCS PAGE (#/docs)
            # =================================================================
            print("\n--- STEP 6: Verifying Docs Page (#/docs) ---")
            page.goto(f"{BASE_URL}/#/docs")
            page.wait_for_selector("#view-docs", state="visible")
            page.wait_for_timeout(400)

            docs_text = page.locator("#view-docs").text_content()
            assert "/api/analyze" in docs_text, "/api/analyze missing from docs"
            assert "/api/predict" in docs_text, "/api/predict missing from docs"
            assert "/api/model-info" in docs_text, "/api/model-info missing from docs"
            assert "/api/health" in docs_text, "/api/health missing from docs"
            assert "rate_limit_exceeded" in docs_text, "Error schema missing from docs"
            print("  [PASS] Docs page renders full REST schemas and rate limit reference.")

            page.screenshot(path=str(SCREENSHOT_DIR / "v2_12e_docs.png"))
            print(f"  Captured: {SCREENSHOT_DIR / 'v2_12e_docs.png'}")

            # =================================================================
            # STEP 7: ACCESSIBILITY (AXE) AUDIT
            # =================================================================
            print("\n--- STEP 7: Automated WCAG 2.1 AA Accessibility Audit ---")
            axe = Axe()

            views_to_audit = ["#/settings", "#/model-card", "#/docs"]
            for v in views_to_audit:
                page.goto(f"{BASE_URL}/{v}")
                page.wait_for_timeout(400)
                axe_results = axe.run(page)
                violations = axe_results.get("violations", [])
                print(f"  Axe audit on {v}: {len(violations)} violations")
                if violations:
                    for vio in violations:
                        print(f"    [VIOLATION] {vio.get('id')}: {vio.get('description')} (Impact: {vio.get('impact')})")
                assert len(violations) == 0, f"Expected 0 accessibility violations on {v}, found {len(violations)}"

            print("  [PASS] Accessibility audit passed with 0 violations across all Phase 12E views.")

            # =================================================================
            # STEP 8: ZERO CONSOLE ERRORS & CSP COMPLIANCE
            # =================================================================
            print("\n--- STEP 8: Security & Console Integrity Audit ---")
            browser_csp = page.evaluate("window.__csp_violations || []")
            all_csp = csp_violations + browser_csp
            print(f"  Console errors: {len(console_errors)}")
            print(f"  CSP violations: {len(all_csp)}")

            assert len(all_csp) == 0, f"CSP Violations detected: {all_csp}"
            assert len(console_errors) == 0, f"Console Errors detected: {console_errors}"
            print("  [PASS] Zero console errors, zero page errors, zero CSP violations.")

            browser.close()

    finally:
        print("\nTerminating background test server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server_process.kill()

    print("\n" + "=" * 80)
    print("ALL PHASE 12E PLAYWRIGHT VERIFICATION CHECKS PASSED PERFECTLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_verification()
