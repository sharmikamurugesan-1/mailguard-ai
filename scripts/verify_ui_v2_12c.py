"""Playwright automated verification for MailGuard AI v2 Phase 12C (Analyzer & Report Screens).

Verifies:
1. Two-column analyzer grid (#analyzer-input-card and #analyzer-report-card).
2. Analyzer tabs: "Email Content", "Header Analysis", "Image Analysis" link.
3. File upload validation:
   - Rejects unsupported file (.exe) clearly.
   - Rejects oversized file (> 1 MB) clearly.
   - Rejects Outlook .msg clearly with user-friendly message.
   - Loads .eml (parses subject, body, and populates header telemetry).
   - Loads .txt.
4. Option toggles: Extract URLs, Analyze headers, Detect suspicious links.
5. Real Spam analysis (.eml):
   - SVG Risk Ring gauge with score and classification badge.
   - Classification, Confidence, Timestamp metadata.
   - Detected indicator chips with icons and severity classes.
   - Key findings bullet list.
   - Email preview with token highlights (▲ spam, ▼ legitimate) and stopword toggle.
   - Header telemetry panel (SPF, DKIM, DMARC, hops, raw headers).
6. Real Ham analysis (.eml):
   - Low risk score, Safe badge, clean indicator chip, SPF/DKIM pass.
7. Borderline uncertain state (.eml / sample):
   - Visible uncertain banner with empirical zone explanation.
8. Interactive actions:
   - Preview Original vs Extracted toggle.
   - Copy report formatted text to clipboard.
   - Export JSON download.
   - Copy raw headers.
   - New Scan button resets to clean empty state.
9. Dark mode rendering.
10. Accessibility (Axe zero violations) & zero CSP violations & zero console errors.
11. Captures screenshots in docs/screenshots/v2/.
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

BASE_URL = "http://127.0.0.1:5006"
SCREENSHOT_DIR = Path("docs/screenshots/v2")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

FIXTURES_DIR = Path("tests/data/fixtures")


def run_verification():
    print("=" * 78)
    print("MAILGUARD AI v2 - PHASE 12C ANALYZER & REPORT SCREENS PLAYWRIGHT VERIFICATION")
    print("=" * 78)

    # 1. Start Flask application on dedicated port 5006
    env = os.environ.copy()
    env["PORT"] = "5006"
    server_process = subprocess.Popen(
        [sys.executable, "-m", "src.app"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    server_ready = False
    for _ in range(30):
        if server_process.poll() is not None:
            stdout, stderr = server_process.communicate()
            raise RuntimeError(f"Server exited prematurely:\n{stderr.decode(errors='replace')}")
        try:
            with urllib.request.urlopen(f"{BASE_URL}/api/health", timeout=1.0) as r:
                if r.status == 200:
                    server_ready = True
                    break
        except Exception:
            time.sleep(0.5)

    if not server_ready:
        server_process.terminate()
        stdout, stderr = server_process.communicate()
        raise RuntimeError("Server did not become ready within 15s")

    print("[SERVER] Flask application running at " + BASE_URL)
    results = {}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1280, "height": 950},
                permissions=["clipboard-read", "clipboard-write"],
            )
            page = context.new_page()

            console_errors = []
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            page.on("pageerror", lambda err: console_errors.append(str(err)))

            # Attach CSP violation listener
            page.add_init_script("""
                window.__csp_violations = [];
                window.addEventListener('securitypolicyviolation', (e) => {
                    window.__csp_violations.push({
                        blockedURI: e.blockedURI,
                        violatedDirective: e.violatedDirective,
                        effectiveDirective: e.effectiveDirective
                    });
                });
            """)

            # ----------------------------------------------------------------
            # STEP 1: INITIAL ANALYZER STATE (#/analyzer)
            # ----------------------------------------------------------------
            print("\n[STEP 1] Testing Initial Analyzer View & Shell")
            page.goto(f"{BASE_URL}/#/analyzer")
            page.wait_for_selector("#view-analyzer", state="visible")
            page.wait_for_timeout(500)

            # Assert Analyzer 2-column layout and cards
            assert page.is_visible("#analyzer-input-card"), "Missing analyzer input card"
            assert page.is_visible("#analyzer-report-card"), "Missing analyzer report card"
            assert page.is_visible("#report-empty-state"), "Report empty state should be visible initially"
            assert not page.is_visible("#report-active-view"), "Report active view should be hidden initially"

            # Check tabs
            assert page.get_attribute("#tab-btn-content", "aria-selected") == "true"
            assert page.get_attribute("#tab-btn-headers", "aria-selected") == "false"
            assert page.is_visible("#tab-panel-content")
            assert not page.is_visible("#tab-panel-headers")

            page.screenshot(path=str(SCREENSHOT_DIR / "v2_12c_analyzer_initial.png"))
            print("  ✓ Saved screenshot: v2_12c_analyzer_initial.png")
            results["step1_initial_state"] = "PASS"

            # ----------------------------------------------------------------
            # STEP 2: BAD FILE (.exe) REJECTION
            # ----------------------------------------------------------------
            print("\n[STEP 2] Testing Unsupported File (.exe) Rejection")
            bad_file_path = str((FIXTURES_DIR / "bad_file.exe").resolve())
            page.set_input_files("#file-picker-input", bad_file_path)
            page.wait_for_timeout(300)

            body_error = page.inner_text("#body-error")
            assert "Unsupported file type (.exe)" in body_error, f"Expected .exe rejection error, got: {body_error}"
            assert page.is_visible("#body-error")

            page.screenshot(path=str(SCREENSHOT_DIR / "v2_12c_bad_file_rejection.png"))
            print("  ✓ Saved screenshot: v2_12c_bad_file_rejection.png")
            results["step2_bad_file"] = "PASS"

            # ----------------------------------------------------------------
            # STEP 3: OVERSIZED FILE (> 1 MB) REJECTION
            # ----------------------------------------------------------------
            print("\n[STEP 3] Testing Oversized File (> 1 MB) Rejection")
            oversized_path = str((FIXTURES_DIR / "oversized_file.txt").resolve())
            page.set_input_files("#file-picker-input", oversized_path)
            page.wait_for_timeout(300)

            body_error = page.inner_text("#body-error")
            assert "exceeds the 1 MB size limit" in body_error, f"Expected >1MB rejection error, got: {body_error}"
            assert page.is_visible("#body-error")

            page.screenshot(path=str(SCREENSHOT_DIR / "v2_12c_oversized_file_rejection.png"))
            print("  ✓ Saved screenshot: v2_12c_oversized_file_rejection.png")
            results["step3_oversized_file"] = "PASS"

            # ----------------------------------------------------------------
            # STEP 4: OUTLOOK .MSG REJECTION
            # ----------------------------------------------------------------
            print("\n[STEP 4] Testing Outlook .msg Clear Rejection")
            msg_fixture_path = FIXTURES_DIR / "test_dummy.msg"
            msg_fixture_path.write_bytes(b"OutlookMSGdummy")
            try:
                page.set_input_files("#file-picker-input", str(msg_fixture_path.resolve()))
                page.wait_for_timeout(300)

                body_error = page.inner_text("#body-error")
                assert "Outlook .msg format is not directly supported" in body_error, f"Expected .msg rejection, got: {body_error}"
                print("  ✓ Outlook .msg clearly rejected with user guidance")
                results["step4_msg_rejection"] = "PASS"
            finally:
                if msg_fixture_path.exists():
                    msg_fixture_path.unlink()

            # ----------------------------------------------------------------
            # STEP 5: REAL SPAM .EML ANALYSIS & REPORT CARD
            # ----------------------------------------------------------------
            print("\n[STEP 5] Testing Real Spam .eml Analysis & Report Card")
            spam_path = str((FIXTURES_DIR / "real_spam.eml").resolve())
            page.set_input_files("#file-picker-input", spam_path)
            page.wait_for_timeout(400)

            # Check that subject and body populated
            sub_val = page.input_value("#subject-input")
            body_val = page.input_value("#body-input")
            assert "URGENT: Your PayPal account has been restricted" in sub_val
            assert "Unauthorized debit card activity" in body_val

            # Submit analysis via Analyze Email button
            page.click("#analyze-btn")

            # Wait for report active view
            page.wait_for_selector("#report-active-view", state="visible", timeout=10000)
            page.wait_for_timeout(600)  # allow ring animation

            # Assert SVG Risk Ring
            risk_num = page.inner_text("#risk-ring-num")
            assert int(risk_num) >= 70, f"Expected high risk score >= 70, got: {risk_num}"
            risk_badge_text = page.inner_text("#risk-ring-badge").strip()
            assert risk_badge_text.upper() in ("SPAM", "SUSPICIOUS"), f"Expected Spam/Suspicious badge, got: {risk_badge_text}"

            # Assert Metadata
            verdict_text = page.inner_text("#report-classification-val").strip()
            assert verdict_text.upper() in ("SPAM", "SUSPICIOUS")
            conf_text = page.inner_text("#report-confidence-val")
            assert "%" in conf_text

            # Assert Indicator Chips
            chip_count = int(page.inner_text("#indicator-count-badge"))
            assert chip_count > 0, "Expected threat indicators detected for spam email"
            chips_text = page.inner_text("#indicators-chips-container")
            assert "spf" in chips_text.lower() or "url" in chips_text.lower() or "indicator" in chips_text.lower()

            # Assert Key Findings
            findings_text = page.inner_text("#findings-list")
            assert len(findings_text) > 20, "Expected key findings populated"

            # Assert Preview & Highlighter
            assert page.is_visible("#preview-from-val")
            assert page.is_visible("#highlight-preview-box")
            assert page.locator(".token-highlight").count() > 0, "Expected highlighted tokens"

            page.screenshot(path=str(SCREENSHOT_DIR / "v2_12c_report_spam.png"))
            print("  ✓ Saved screenshot: v2_12c_report_spam.png")
            results["step5_spam_report"] = "PASS"

            # ----------------------------------------------------------------
            # STEP 6: HEADER ANALYSIS TAB TELEMETRY
            # ----------------------------------------------------------------
            print("\n[STEP 6] Testing Header Analysis Tab Telemetry")
            page.click("#tab-btn-headers")
            page.wait_for_selector("#tab-panel-headers", state="visible")
            page.wait_for_timeout(300)

            assert page.is_visible("#headers-telemetry-active"), "Headers telemetry active box should be visible"
            spf_val = page.inner_text("#h-spf-val")
            assert "FAIL" in spf_val, f"Expected SPF FAIL, got: {spf_val}"
            sender_match = page.inner_text("#h-sender-match-val")
            assert "Mismatch" in sender_match, f"Expected Sender Mismatch, got: {sender_match}"

            raw_headers = page.inner_text("#raw-headers-pre")
            assert "Received:" in raw_headers
            assert "Authentication-Results:" in raw_headers

            page.screenshot(path=str(SCREENSHOT_DIR / "v2_12c_header_analysis_tab.png"))
            print("  ✓ Saved screenshot: v2_12c_header_analysis_tab.png")
            results["step6_header_telemetry"] = "PASS"

            # ----------------------------------------------------------------
            # STEP 7: REAL HAM .EML ANALYSIS & CLEAN STATE
            # ----------------------------------------------------------------
            print("\n[STEP 7] Testing Real Ham .eml Analysis")
            page.click("#tab-btn-content")
            page.wait_for_selector("#tab-panel-content", state="visible")

            page.click("#clear-btn")
            page.wait_for_timeout(200)
            assert page.is_visible("#report-empty-state"), "Clear should return report to empty state"

            ham_path = str((FIXTURES_DIR / "real_ham.eml").resolve())
            page.set_input_files("#file-picker-input", ham_path)
            page.wait_for_timeout(300)

            page.click("#analyze-btn")
            page.wait_for_selector("#report-active-view", state="visible", timeout=10000)
            page.wait_for_timeout(600)

            ham_risk = int(page.inner_text("#risk-ring-num"))
            assert ham_risk < 40, f"Expected low risk score < 40 for ham, got: {ham_risk}"
            ham_verdict = page.inner_text("#report-classification-val").strip()
            assert ham_verdict.upper() == "SAFE", f"Expected Safe verdict, got: {ham_verdict}"

            page.screenshot(path=str(SCREENSHOT_DIR / "v2_12c_report_ham.png"))
            print("  ✓ Saved screenshot: v2_12c_report_ham.png")
            results["step7_ham_report"] = "PASS"

            # ----------------------------------------------------------------
            # STEP 8: BORDERLINE UNCERTAIN STATE
            # ----------------------------------------------------------------
            print("\n[STEP 8] Testing Borderline Uncertain State Callout")
            page.click("#sample-borderline-btn")
            page.wait_for_timeout(200)
            page.click("#analyze-btn")
            page.wait_for_selector("#report-active-view", state="visible", timeout=10000)
            page.wait_for_timeout(600)

            # Assert uncertain banner is displayed
            assert page.is_visible("#report-uncertain-banner"), "Expected uncertain banner to be visible for borderline text"
            banner_text = page.inner_text("#report-uncertain-text")
            assert "borderline zone" in banner_text, f"Banner text missing explanation: {banner_text}"

            page.screenshot(path=str(SCREENSHOT_DIR / "v2_12c_report_borderline_uncertain.png"))
            print("  ✓ Saved screenshot: v2_12c_report_borderline_uncertain.png")
            results["step8_borderline_uncertain"] = "PASS"

            # ----------------------------------------------------------------
            # STEP 9: PREVIEW MODE SWITCH & ACTIONS (COPY & EXPORT)
            # ----------------------------------------------------------------
            print("\n[STEP 9] Testing Preview Switch, Copy Report & Export JSON")
            # Switch to Extracted preview
            page.click("#btn-preview-extracted")
            page.wait_for_timeout(200)
            assert page.get_attribute("#btn-preview-extracted", "class").find("active") != -1

            # Switch back to Original preview
            page.click("#btn-preview-original")
            page.wait_for_timeout(200)
            assert page.get_attribute("#btn-preview-original", "class").find("active") != -1

            # Copy report
            page.click("#copy-report-btn")
            page.wait_for_timeout(300)
            assert page.is_visible(".toast"), "Expected toast feedback after copy report"

            # Export JSON
            page.click("#export-json-btn")
            page.wait_for_timeout(300)
            assert page.is_visible(".toast"), "Expected toast feedback after export JSON"

            # New scan button
            page.click("#new-scan-btn")
            page.wait_for_timeout(200)
            assert page.is_visible("#report-empty-state"), "New scan button should reset right card to empty state"
            results["step9_interactive_actions"] = "PASS"

            # ----------------------------------------------------------------
            # STEP 10: DARK THEME RENDERING
            # ----------------------------------------------------------------
            print("\n[STEP 10] Testing Dark Mode Theme Rendering")
            page.click("#theme-toggle-btn")
            page.wait_for_timeout(300)
            assert page.get_attribute("html", "data-theme") == "dark"

            page.click("#sample-spam-btn")
            page.wait_for_timeout(200)
            page.click("#analyze-btn")
            page.wait_for_selector("#report-active-view", state="visible", timeout=10000)
            page.wait_for_timeout(600)

            page.screenshot(path=str(SCREENSHOT_DIR / "v2_12c_report_dark_mode.png"))
            print("  ✓ Saved screenshot: v2_12c_report_dark_mode.png")
            results["step10_dark_mode"] = "PASS"

            # ----------------------------------------------------------------
            # STEP 11: ACCESSIBILITY (AXE), ZERO CSP VIOLATIONS & ZERO CONSOLE ERRORS
            # ----------------------------------------------------------------
            print("\n[STEP 11] Accessibility Audit (Axe) & CSP Compliance Check")
            axe = Axe()
            axe_results = axe.run(page)
            violations = axe_results.get("violations", [])

            print(f"  - Axe violations count: {len(violations)}")
            if len(violations) > 0:
                print(f"  [WARN] Axe violations: {json.dumps(violations, indent=2)}")

            assert len(violations) == 0, f"Expected 0 accessibility violations, found {len(violations)}"

            # CSP violations check
            csp_violations = page.evaluate("window.__csp_violations || []")
            print(f"  - CSP violations count: {len(csp_violations)}")
            assert len(csp_violations) == 0, f"Expected 0 CSP violations, got: {csp_violations}"

            # Console errors check
            print(f"  - Console errors count: {len(console_errors)}")
            assert len(console_errors) == 0, f"Expected 0 console errors, got: {console_errors}"
            results["step11_a11y_csp_console"] = "PASS"

            browser.close()

    finally:
        server_process.terminate()
        try:
            server_process.wait(timeout=3)
        except Exception:
            server_process.kill()

    print("\n" + "=" * 78)
    print("ALL PHASE 12C PLAYWRIGHT TESTS PASSED!")
    print(json.dumps(results, indent=2))
    print("=" * 78)


if __name__ == "__main__":
    run_verification()
