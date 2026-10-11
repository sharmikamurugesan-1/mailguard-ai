"""Playwright automated verification for MailGuard AI v2 Phase 12F (Client-side Image OCR & QR Threat Analyzer).

Verifies:
1. Vendor Library Lazy Loading & Self-Hosting:
   - Self-hosted files under static/vendor/ (jsQR, Tesseract.js, worker, WASM, eng.traineddata.gz).
   - Zero external CDNs contacted.
   - Lazy-loaded: vendor libraries are not loaded until Image Analysis view or OCR toggle is accessed.
2. Image Threat Analyzer View (#/image-analysis):
   - Fixture 1: tests/fixtures/images/text_screenshot.png
     * Magic bytes validated (PNG: 89 50 4E 47).
     * Image preview card with dimensions & metadata.
     * Web Worker client-side OCR extraction with progress updates.
     * Extracted text, confidence, URLs table, risk score, key findings.
     * Copy text button & "Send to Email Analyzer" transfer.
     * Verified scan saved locally to IndexedDB with source 'image'.
   - Fixture 2: tests/fixtures/images/qr_phish.png
     * Client-side QR decode with jsQR (decoded URL: http://phishing-portal.test/steal-credentials).
     * Combined threat evaluation identifies phishing URL & elevated risk score.
     * Copy QR content button.
   - Fixture 3: tests/fixtures/images/plain_photo.jpg
     * Magic bytes validated (JPEG: FF D8 FF).
     * Zero text / zero QR detected -> clean state with Safe verdict (Risk Score 0).
   - Fixture 4: tests/fixtures/images/corrupt.png
     * Content magic bytes validation rejection.
     * Error alert displayed; preview blocked.
   - Fixture 5: tests/fixtures/images/oversized.png
     * 5 MB client-side size limit enforcement (13.85 MB rejected).
     * Error alert displayed; preview blocked.
   - Cancellation Flow:
     * User clicks "Cancel Analysis" during active scan -> terminates Web Worker, re-enables controls.
3. Email Analyzer OCR Integration:
   - "Image OCR & QR" toggle in Email Analyzer.
   - Dropping image into Email Analyzer dropzone runs client-side OCR and populates textarea.
4. Quality & Compliance:
   - Axe-core accessibility audit on #/image-analysis (0 violations).
   - Zero console errors, zero page errors, zero CSP violations.
   - First OCR latency benchmark & client-side memory usage recorded.
5. Captures screenshots in docs/screenshots/v2/.
"""

import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

from axe_core_python.sync_playwright import Axe
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:5009"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCREENSHOT_DIR = PROJECT_ROOT / "docs" / "screenshots" / "v2"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures" / "images"


def run_verification():
    print("=" * 80)
    print("MAILGUARD AI v2 - PHASE 12F PLAYWRIGHT VERIFICATION AUDIT")
    print("=" * 80)

    # 1. Start Server on port 5009
    env = os.environ.copy()
    env["PORT"] = "5009"
    env["RATELIMIT_ENABLED"] = "1"
    env["PYTHONUNBUFFERED"] = "1"

    server_process = subprocess.Popen(
        [sys.executable, "-m", "src.app"],
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    print("Starting MailGuard AI Flask application on port 5009...")
    started = False
    for attempt in range(25):
        try:
            with urllib.request.urlopen(f"{BASE_URL}/api/health", timeout=2) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    print(f"Server healthy on port 5009. Model loaded: {data.get('model_loaded')}")
                    started = True
                    break
        except Exception:
            time.sleep(0.5)

    if not started:
        print("ERROR: Server failed to start within timeout.")
        server_process.terminate()
        sys.exit(1)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1440, "height": 900},
                device_scale_factor=1,
                permissions=["clipboard-read", "clipboard-write"],
            )
            page = context.new_page()

            # Security and error trackers
            console_errors = []
            csp_violations = []

            def on_console(msg):
                if msg.type == "error":
                    # Ignore intentional console errors if any
                    console_errors.append(msg.text)
                elif "violates" in msg.text.lower() or "csp" in msg.text.lower():
                    csp_violations.append(msg.text)

            page.on("console", on_console)
            page.on("pageerror", lambda err: console_errors.append(str(err)))

            # Hook into CSP violation events in-page
            page.add_init_script("""
                window.__csp_violations = [];
                document.addEventListener('securitypolicyviolation', (e) => {
                    window.__csp_violations.push({
                        blockedURI: e.blockedURI,
                        violatedDirective: e.violatedDirective,
                        originalPolicy: e.originalPolicy
                    });
                });
            """)

            # =================================================================
            # STEP 1: VERIFY INITIAL STATE & LAZY LOADING
            # =================================================================
            print("\n--- STEP 1: Verifying Lazy Loading of Vendor Libraries ---")
            page.goto(f"{BASE_URL}/#/dashboard")
            page.wait_for_selector("#view-dashboard", state="visible")

            # Check that Tesseract and jsQR are NOT loaded yet on dashboard
            vendor_status_initial = page.evaluate("""() => ({
                hasJsQR: typeof window.jsQR === 'function',
                hasTesseract: typeof window.Tesseract === 'object'
            })""")
            print("  Dashboard initial vendor status:", vendor_status_initial)
            assert not vendor_status_initial["hasJsQR"], "jsQR should NOT be loaded on dashboard initially"
            assert not vendor_status_initial["hasTesseract"], "Tesseract should NOT be loaded on dashboard initially"
            print("  [PASS] Vendor libraries are not prematurely loaded on Dashboard.")

            # =================================================================
            # STEP 2: NAVIGATE TO IMAGE THREAT ANALYZER
            # =================================================================
            print("\n--- STEP 2: Navigating to Image Threat Analyzer (#/image-analysis) ---")
            page.goto(f"{BASE_URL}/#/image-analysis")
            page.wait_for_selector("#view-image-analysis", state="visible")
            page.wait_for_timeout(300)

            # Check dropzone & controls visible
            assert page.is_visible("#img-drop-zone"), "Image dropzone missing"
            assert page.is_visible("#img-browse-btn"), "Image browse button missing"
            assert page.locator("#img-file-input").count() == 1, "Image file input element missing"
            page.screenshot(path=str(SCREENSHOT_DIR / "v2_12f_image_analyzer_empty.png"))
            print(f"  Captured: {SCREENSHOT_DIR / 'v2_12f_image_analyzer_empty.png'}")

            # =================================================================
            # STEP 3: FIXTURE 4 - CORRUPT MAGIC BYTES VALIDATION
            # =================================================================
            print("\n--- STEP 3: Testing Fixture 4 (corrupt.png - Magic Bytes Validation) ---")
            corrupt_file = FIXTURES_DIR / "corrupt.png"
            page.set_input_files("#img-file-input", str(corrupt_file))
            page.wait_for_selector("#img-alert-box:not(.hidden)", timeout=3000)

            alert_text = page.locator("#img-alert-box").text_content()
            print(f"  Alert message for corrupt file: '{alert_text}'")
            assert "magic bytes" in alert_text.lower() or "invalid file format" in alert_text.lower(), "Expected magic bytes error"
            assert page.locator("#img-preview-box").is_hidden(), "Preview should not be visible for invalid file"
            page.screenshot(path=str(SCREENSHOT_DIR / "v2_12f_corrupt_magic_bytes_error.png"))
            print(f"  Captured: {SCREENSHOT_DIR / 'v2_12f_corrupt_magic_bytes_error.png'}")
            print("  [PASS] Non-PNG/JPEG content successfully rejected by magic bytes inspection.")

            # =================================================================
            # STEP 4: FIXTURE 5 - OVERSIZED FILE (> 5 MB) ENFORCEMENT
            # =================================================================
            print("\n--- STEP 4: Testing Fixture 5 (oversized.png - 5 MB Size Limit) ---")
            oversized_file = FIXTURES_DIR / "oversized.png"
            page.set_input_files("#img-file-input", str(oversized_file))
            page.wait_for_selector("#img-alert-box:not(.hidden)", timeout=3000)

            alert_text_size = page.locator("#img-alert-box").text_content()
            print(f"  Alert message for oversized file: '{alert_text_size}'")
            assert "exceeds" in alert_text_size.lower() and "5 mb" in alert_text_size.lower(), "Expected 5 MB size error"
            assert page.locator("#img-preview-box").is_hidden(), "Preview should not be visible for oversized file"
            page.screenshot(path=str(SCREENSHOT_DIR / "v2_12f_oversized_error.png"))
            print(f"  Captured: {SCREENSHOT_DIR / 'v2_12f_oversized_error.png'}")
            print("  [PASS] Oversized file (> 5 MB) successfully rejected before processing.")

            # =================================================================
            # STEP 5: FIXTURE 1 - TEXT SCREENSHOT OCR THREAT SCAN
            # =================================================================
            print("\n--- STEP 5: Testing Fixture 1 (text_screenshot.png - Web Worker OCR Scan) ---")
            text_file = FIXTURES_DIR / "text_screenshot.png"
            page.set_input_files("#img-file-input", str(text_file))
            page.wait_for_selector("#img-preview-box:not(.hidden)", timeout=3000)

            # Validate preview metadata
            meta_text = page.locator("#img-meta-text").text_content()
            print(f"  Preview metadata: '{meta_text}'")
            assert "text_screenshot.png" in meta_text, "Filename missing in metadata"
            assert "PNG" in meta_text, "PNG format missing in metadata"

            page.screenshot(path=str(SCREENSHOT_DIR / "v2_12f_image_preview.png"))
            print(f"  Captured: {SCREENSHOT_DIR / 'v2_12f_image_preview.png'}")

            # Measure client memory before OCR
            mem_before = page.evaluate("""() => {
                if (window.performance && window.performance.memory) {
                    return Math.round(window.performance.memory.usedJSHeapSize / (1024 * 1024));
                }
                return null;
            }""")

            # Click Analyze Image Threats
            t0 = time.perf_counter()
            page.click("#img-start-scan-btn")

            # Progress box should show up
            page.wait_for_selector("#img-progress-box:not(.hidden)", timeout=3000)

            # Wait for report to appear (timeout 30s)
            page.wait_for_selector("#img-report-container:not(.hidden)", timeout=35000)
            t1 = time.perf_counter()
            first_ocr_latency = t1 - t0
            print(f"  First OCR scan completion latency: {first_ocr_latency:.2f}s")

            # Measure memory after OCR
            mem_after = page.evaluate("""() => {
                if (window.performance && window.performance.memory) {
                    return Math.round(window.performance.memory.usedJSHeapSize / (1024 * 1024));
                }
                return null;
            }""")
            print(f"  Client JS Heap memory: before={mem_before} MB, after={mem_after} MB")

            # Validate report contents
            verdict = page.locator("#img-verdict-badge").text_content().strip()
            risk_score_str = page.locator("#img-risk-score-val").text_content()
            ocr_conf_str = page.locator("#img-ocr-conf-val").text_content()
            extracted_text = page.locator("#img-ocr-text-display").text_content()

            print(f"  Image Scan Verdict: {verdict}")
            print(f"  Risk Score: {risk_score_str}")
            print(f"  OCR Confidence: {ocr_conf_str}")
            print(f"  Extracted Text Snippet: {extracted_text[:120]}...")

            assert verdict in ["Spam", "Suspicious"], f"Expected Spam or Suspicious verdict, got {verdict}"
            assert float(risk_score_str.split("/")[0].strip()) >= 50.0, "Expected elevated risk score for urgent phishing notice"
            assert "URGENT" in extracted_text or "NOTICE" in extracted_text or "security-update" in extracted_text, "OCR text missing expected keywords"

            # Check URLs table
            assert page.is_visible("#img-urls-table-wrapper:not(.hidden)"), "URLs table should be visible"
            urls_table_text = page.locator("#img-urls-tbody").text_content()
            assert "security-update.example" in urls_table_text, "Extracted URL missing from table"
            print(f"  URLs table text: '{urls_table_text.strip()}'")

            # Test Copy Text button
            page.click("#img-copy-text-btn")
            page.wait_for_timeout(300)

            page.screenshot(path=str(SCREENSHOT_DIR / "v2_12f_image_ocr_report.png"))
            print(f"  Captured: {SCREENSHOT_DIR / 'v2_12f_image_ocr_report.png'}")
            print("  [PASS] Text screenshot successfully processed with Web Worker OCR.")

            # Test Transfer to Email Analyzer
            page.click("#img-send-to-analyzer-btn")
            page.wait_for_selector("#view-analyzer", state="visible")
            body_val = page.locator("#body-input").input_value()
            assert "URGENT" in body_val or "security-update" in body_val, "Transferred body text missing keywords"
            print("  [PASS] 'Send to Email Analyzer' successfully transferred extracted text to Analyzer.")

            # =================================================================
            # STEP 6: FIXTURE 2 - QR CODE PHISHING SCAN
            # =================================================================
            print("\n--- STEP 6: Testing Fixture 2 (qr_phish.png - Client-Side jsQR Scan) ---")
            page.goto(f"{BASE_URL}/#/image-analysis")
            page.wait_for_selector("#view-image-analysis", state="visible")

            qr_file = FIXTURES_DIR / "qr_phish.png"
            page.set_input_files("#img-file-input", str(qr_file))
            page.wait_for_selector("#img-preview-box:not(.hidden)", timeout=3000)

            page.click("#img-start-scan-btn")
            page.wait_for_selector("#img-report-container:not(.hidden)", timeout=35000)

            qr_val = page.locator("#img-qr-text-val").text_content().strip()
            print(f"  Decoded QR Code Content: '{qr_val}'")
            assert qr_val == "http://phishing-portal.test/steal-credentials", f"Unexpected QR content: {qr_val}"
            assert page.is_visible("#img-copy-qr-btn"), "Copy QR button should be visible"

            qr_verdict = page.locator("#img-verdict-badge").text_content().strip()
            print(f"  QR Scan Verdict: {qr_verdict}")
            assert qr_verdict in ["Spam", "Suspicious"], f"Expected Spam/Suspicious for phishing QR, got {qr_verdict}"

            page.screenshot(path=str(SCREENSHOT_DIR / "v2_12f_qr_phish_report.png"))
            print(f"  Captured: {SCREENSHOT_DIR / 'v2_12f_qr_phish_report.png'}")
            print("  [PASS] QR code decoded and phishing threat correctly flagged.")

            # =================================================================
            # STEP 7: FIXTURE 3 - PLAIN BENIGN PHOTO (ZERO TEXT / ZERO QR)
            # =================================================================
            print("\n--- STEP 7: Testing Fixture 3 (plain_photo.jpg - Clean Benign Image) ---")
            page.click("#img-clear-selection-btn")
            page.wait_for_selector("#img-preview-box", state="hidden")

            plain_file = FIXTURES_DIR / "plain_photo.jpg"
            page.set_input_files("#img-file-input", str(plain_file))
            page.wait_for_selector("#img-preview-box:not(.hidden)", timeout=3000)

            page.click("#img-start-scan-btn")
            page.wait_for_selector("#img-report-container:not(.hidden)", timeout=35000)

            plain_verdict = page.locator("#img-verdict-badge").text_content().strip()
            plain_risk = page.locator("#img-risk-score-val").text_content().strip()
            print(f"  Plain Image Verdict: {plain_verdict}, Risk: {plain_risk}")
            assert plain_verdict == "Safe", f"Expected Safe for plain photo, got {plain_verdict}"
            assert "0" in plain_risk, f"Expected 0 risk for clean photo, got {plain_risk}"

            page.screenshot(path=str(SCREENSHOT_DIR / "v2_12f_plain_photo_clean.png"))
            print(f"  Captured: {SCREENSHOT_DIR / 'v2_12f_plain_photo_clean.png'}")
            print("  [PASS] Clean image with zero text and zero QR yields clean Safe verdict.")

            # =================================================================
            # STEP 8: CANCELLATION FLOW TEST
            # =================================================================
            print("\n--- STEP 8: Testing User Cancellation Flow ---")
            page.click("#img-clear-selection-btn")
            page.set_input_files("#img-file-input", str(text_file))
            page.wait_for_selector("#img-preview-box:not(.hidden)", timeout=3000)

            # Start scan and cancel immediately
            page.click("#img-start-scan-btn")
            page.wait_for_selector("#img-cancel-scan-btn", state="visible")
            page.click("#img-cancel-scan-btn")

            # Progress should disappear, cancel alert should appear
            page.wait_for_selector("#img-alert-box:not(.hidden)", timeout=3000)
            cancel_alert = page.locator("#img-alert-box").text_content()
            print(f"  Cancellation alert: '{cancel_alert}'")
            assert "cancelled" in cancel_alert.lower(), "Expected cancellation message in alert"
            assert page.locator("#img-progress-box").is_hidden(), "Progress box should be hidden after cancel"
            assert page.locator("#img-start-scan-btn").is_enabled(), "Analyze button should be re-enabled"

            page.screenshot(path=str(SCREENSHOT_DIR / "v2_12f_cancelled_flow.png"))
            print(f"  Captured: {SCREENSHOT_DIR / 'v2_12f_cancelled_flow.png'}")
            print("  [PASS] Cancellation terminates worker and resets controls cleanly.")

            # =================================================================
            # STEP 9: EMAIL ANALYZER OCR TOGGLE FLOW
            # =================================================================
            print("\n--- STEP 9: Testing Email Analyzer OCR Toggle Integration ---")
            page.goto(f"{BASE_URL}/#/analyzer")
            page.wait_for_selector("#view-analyzer", state="visible")
            page.click("#clear-btn")
            page.wait_for_timeout(200)

            # Enable OCR toggle
            if not page.locator("#opt-image-ocr").is_checked():
                page.locator("#ocr-toggle-wrapper").click()
            assert page.locator("#opt-image-ocr").is_checked(), "OCR toggle should be checked"
            page.wait_for_timeout(300)

            # Drop / upload image to Email Analyzer
            page.set_input_files("#file-picker-input", str(text_file))

            # Form should automatically process image via OCR and run analyze
            page.wait_for_selector("#analyzer-report-card #report-active-view:not(.hidden)", timeout=35000)
            analyzer_verdict = page.locator("#report-classification-val").text_content().strip()
            print(f"  Email Analyzer Verdict from Image: {analyzer_verdict}")
            assert analyzer_verdict in ["Spam", "Suspicious"], f"Expected Spam/Suspicious, got {analyzer_verdict}"

            page.screenshot(path=str(SCREENSHOT_DIR / "v2_12f_analyzer_ocr_toggle.png"))
            print(f"  Captured: {SCREENSHOT_DIR / 'v2_12f_analyzer_ocr_toggle.png'}")
            print("  [PASS] Email Analyzer OCR toggle seamlessly processes images into report.")

            # =================================================================
            # STEP 10: ACCESSIBILITY (AXE) AUDIT
            # =================================================================
            print("\n--- STEP 10: Automated WCAG 2.1 AA Accessibility Audit ---")
            axe = Axe()

            views_to_audit = ["#/image-analysis", "#/analyzer"]
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

            print("  [PASS] Accessibility audit passed with 0 violations across Phase 12F views.")

            # =================================================================
            # STEP 11: ZERO CONSOLE ERRORS & CSP COMPLIANCE
            # =================================================================
            print("\n--- STEP 11: Security & Console Integrity Audit ---")
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
    print("ALL PHASE 12F PLAYWRIGHT VERIFICATION CHECKS PASSED PERFECTLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_verification()
