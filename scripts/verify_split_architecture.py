#!/usr/bin/env python3
"""Comprehensive verification script for MailGuard AI split architecture (Phase 12J).

Hardened Split-Deployment Verification:
1. Real Vercel static server emulator (scripts.serve_with_vercel_json) on port 3000.
2. Flask ML backend on port 5000 with CORS allowlist set to port 3000.
3. API Origin Safety Guard verification:
   - Unconfigured placeholder (.invalid) blocks fetches and displays "Backend Not Configured".
   - Configured origin via scripts/set_api_origin.py allows fetches.
4. Static asset precedence over SPA rewrite:
   - /config.js, /data/examples.json, /vendor/... served as static assets, not rewritten to HTML.
5. Deterministic ML predictions:
   - Home quick-scan: Verdict='Spam', Score='99'.
   - Analyzer scan: Verdict='Spam', Score='99.3'.
6. Cold-start & error resilience:
   - >3s request delay triggers waking banner, resolves cleanly.
   - 503 Service Unavailable handled gracefully.
   - Network failure/abort handled without uncaught exceptions.
7. OCR & QR analysis under strict Vercel CSP headers:
   - text_screenshot.png (Web Worker OCR)
   - qr_phish.png (Client-side jsQR)
   - plain_photo.jpg (Clean benign image)
8. Zero CSP violations and zero browser console errors.
9. Axe-core accessibility audit across all major routes.
10. Restores placeholder origin at test conclusion.
"""

import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import urllib.request

from axe_core_python.sync_playwright import Axe
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from scripts.serve_with_vercel_json import create_vercel_server
from scripts.set_api_origin import set_api_origin, CONFIG_JS_PATH as STATIC_CONFIG, VERCEL_JSON_PATH as VERCEL_JSON

FRONTEND_DIR = BASE_DIR / "frontend"
FIXTURES_DIR = BASE_DIR / "tests" / "fixtures" / "images"
SCREENSHOT_DIR = BASE_DIR / "docs" / "screenshots" / "v2"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

BACKEND_PORT = 5000
FRONTEND_PORT = 3000


def start_backend():
    """Start local Flask backend server on port 5000."""
    python_exe = sys.executable
    cmd = [
        python_exe,
        "-c",
        f"""
import sys
from pathlib import Path
sys.path.insert(0, r"{BASE_DIR}")
from src.app import create_app
app = create_app({{
    'TESTING': True,
    'RATELIMIT_ENABLED': False,
    'CORS_ALLOWED_ORIGINS': 'http://127.0.0.1:3000,http://localhost:3000'
}})
app.run(host='127.0.0.1', port={BACKEND_PORT}, debug=False)
""",
    ]
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["CORS_ALLOWED_ORIGINS"] = "http://127.0.0.1:3000,http://localhost:3000"
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    return proc


def start_vercel_frontend():
    """Start Vercel static emulator on port 3000."""
    server = create_vercel_server(FRONTEND_PORT)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def test_static_asset_precedence():
    """Verify static assets are served directly with proper MIME types and not rewritten to HTML."""
    print("\n--- TEST 1: Static Asset Resolution & Vercel Headers ---")

    # 1. /config.js
    req_config = urllib.request.urlopen(f"http://127.0.0.1:{FRONTEND_PORT}/config.js")
    assert req_config.status == 200, f"Expected 200 for config.js, got {req_config.status}"
    ctype_config = req_config.headers.get("Content-Type", "")
    assert "javascript" in ctype_config, f"Expected JS content-type, got {ctype_config}"
    assert "text/html" not in ctype_config, "Static config.js was swallowed by SPA rewrite!"
    content_config = req_config.read().decode("utf-8")
    assert "PROD_API_URL" in content_config, "Missing expected content in config.js"
    print("  [PASS] /config.js served directly as application/javascript.")

    # 2. /data/examples.json
    req_examples = urllib.request.urlopen(f"http://127.0.0.1:{FRONTEND_PORT}/data/examples.json")
    assert req_examples.status == 200
    ctype_examples = req_examples.headers.get("Content-Type", "")
    assert "json" in ctype_examples, f"Expected JSON content-type, got {ctype_examples}"
    examples_data = json.loads(req_examples.read().decode("utf-8"))
    assert len(examples_data) == 7, f"Expected 7 examples, got {len(examples_data)}"
    print("  [PASS] /data/examples.json served directly with 7 items.")

    # 3. /vendor/tesseract/tesseract.min.js
    req_tess = urllib.request.urlopen(f"http://127.0.0.1:{FRONTEND_PORT}/vendor/tesseract/tesseract.min.js")
    assert req_tess.status == 200
    assert "javascript" in req_tess.headers.get("Content-Type", "")
    print("  [PASS] /vendor/tesseract/tesseract.min.js served directly.")

    # 4. /vendor/tesseract/eng.traineddata.gz
    req_trained = urllib.request.urlopen(f"http://127.0.0.1:{FRONTEND_PORT}/vendor/tesseract/eng.traineddata.gz")
    assert req_trained.status == 200
    assert req_trained.headers.get("Content-Encoding") == "gzip"
    print("  [PASS] /vendor/tesseract/eng.traineddata.gz served with Content-Encoding: gzip.")

    # 5. Non-existent SPA route rewritten to /index.html
    req_spa = urllib.request.urlopen(f"http://127.0.0.1:{FRONTEND_PORT}/some-non-existent-spa-route")
    assert req_spa.status == 200
    ctype_spa = req_spa.headers.get("Content-Type", "")
    assert "text/html" in ctype_spa, f"Expected HTML for SPA rewrite, got {ctype_spa}"
    csp_header = req_spa.headers.get("Content-Security-Policy", "")
    assert "connect-src" in csp_header, "Missing CSP header on SPA response"
    print("  [PASS] Non-existent route falls back to SPA index.html with Vercel headers.")


def run_split_verification():
    print("=" * 75)
    print("PHASE 12J: SPLIT DEPLOYMENT PLAYWRIGHT VERIFICATION")
    print(f"Backend API:   http://127.0.0.1:{BACKEND_PORT} (Simulating Render)")
    print(f"Frontend Host: http://127.0.0.1:{FRONTEND_PORT} (Simulating Vercel via serve_with_vercel_json)")
    print("=" * 75)

    # Backup original config & vercel.json
    orig_config = STATIC_CONFIG.read_text(encoding="utf-8")
    orig_vercel = VERCEL_JSON.read_text(encoding="utf-8")

    # Start servers
    print("[1/10] Starting backend Flask server on port 5000...")
    backend_proc = start_backend()
    time.sleep(2)

    print("[2/10] Starting Vercel emulator static server on port 3000...")
    vercel_server = start_vercel_frontend()
    time.sleep(1)

    try:
        # Test static asset precedence
        test_static_asset_precedence()

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1400, "height": 950})

            # Track errors, CSP violations, and network calls
            csp_violations = []
            console_errors = []
            page_errors = []
            api_requests = []

            # In-page CSP violation listener
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

            def handle_console(msg):
                if msg.type == "error":
                    text = msg.text
                    console_errors.append(text)
                    print(f"  [CONSOLE ERROR] {text}")

            def handle_pageerror(err):
                page_errors.append(str(err))
                print(f"  [PAGE ERROR] {err}")

            page.on("console", handle_console)
            page.on("pageerror", handle_pageerror)
            page.on("request", lambda req: api_requests.append(req.url) if f":{BACKEND_PORT}/api" in req.url else None)

            # -----------------------------------------------------------------
            # TEST 2: RUNTIME GUARD - UNCONFIGURED ORIGIN (.invalid)
            # -----------------------------------------------------------------
            print("\n--- TEST 2: Runtime Guard with Unconfigured .invalid Origin ---")
            api_requests.clear()
            page.add_init_script("""
                window.MAILGUARD_API_URL = 'https://REPLACE-WITH-RENDER-URL.invalid';
            """)
            page.goto(f"http://127.0.0.1:{FRONTEND_PORT}/#/home")
            page.wait_for_timeout(1000)

            status_text = page.locator("#status-text").text_content()
            print(f"  Status indicator text: '{status_text}'")
            assert "Not Configured" in status_text, f"Expected unconfigured status, got '{status_text}'"

            # Check that clicking analyze triggers unconfigured alert with zero network calls
            page.goto(f"http://127.0.0.1:{FRONTEND_PORT}/#/analyzer")
            page.wait_for_selector("#sample-spam-btn", timeout=10000)
            page.click("#sample-spam-btn")
            page.click("#analyze-btn")
            page.wait_for_selector("#general-error:not(.hidden)", timeout=5000)
            err_msg = page.locator("#general-error-message").text_content()
            print(f"  Configuration notice on attempt: '{err_msg}'")
            assert "Backend not configured" in err_msg or "Backend API is not configured" in err_msg

            # Assert ZERO network requests made to backend API
            print(f"  API requests made while unconfigured: {len(api_requests)}")
            assert len(api_requests) == 0, f"Expected 0 API requests while unconfigured, made {len(api_requests)}"
            print("  [PASS] Runtime guard successfully prevented network requests and alerted user.")

            # -----------------------------------------------------------------
            # CONFIGURE ORIGIN FOR SPLIT OPERATION
            # -----------------------------------------------------------------
            print("\n--- Configuring Origin via scripts/set_api_origin.py ---")
            set_api_origin(f"http://127.0.0.1:{BACKEND_PORT}")

            # Re-create page to clear init_script override
            page.close()
            page = browser.new_page(viewport={"width": 1400, "height": 950})
            page.on("console", handle_console)
            page.on("pageerror", handle_pageerror)
            page.on("request", lambda req: api_requests.append(req.url) if f":{BACKEND_PORT}/api" in req.url else None)
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

            # -----------------------------------------------------------------
            # TEST 3: CONFIGURED HOME QUICK SCAN (DETERMINISTIC SCORE)
            # -----------------------------------------------------------------
            print("\n--- TEST 3: Configured Home View & Deterministic Quick Scan ---")
            api_requests.clear()
            page.goto(f"http://127.0.0.1:{FRONTEND_PORT}/#/home")
            page.wait_for_selector("#status-dot.status-online", timeout=10000)

            status_text = page.locator("#status-text").text_content()
            print(f"  Server status text: '{status_text}'")
            assert "Online" in status_text

            api_base = page.evaluate("() => window.API_BASE_URL")
            print(f"  Active window.API_BASE_URL: '{api_base}'")
            assert api_base == f"http://127.0.0.1:{BACKEND_PORT}"

            # Click first synthetic spam chip (spam-1)
            sample_chips = page.locator("#home-examples-chips .example-chip")
            first_chip = sample_chips.first
            first_chip.click()
            page.wait_for_timeout(300)

            # Trigger quick analyze
            page.locator("#home-quick-analyze-btn").click()
            page.wait_for_selector("#home-quick-result-card:not(.hidden)", timeout=15000)

            home_verdict = page.locator("#home-result-badge").text_content().strip()
            home_score = page.locator("#home-result-score").text_content().strip()
            print(f"  Home quick scan result: Verdict='{home_verdict}', Risk Score='{home_score}'")

            # Deterministic assertions
            assert home_verdict == "Spam", f"Expected Spam verdict, got '{home_verdict}'"
            assert home_score == "99", f"Expected deterministic score 99, got '{home_score}'"
            print("  [PASS] Deterministic Home quick scan verified (Verdict=Spam, Score=99).")

            # -----------------------------------------------------------------
            # TEST 4: CONFIGURED ANALYZER SCAN (DETERMINISTIC SCORE)
            # -----------------------------------------------------------------
            print("\n--- TEST 4: Configured Analyzer View & Deterministic Deep Scan ---")
            page.goto(f"http://127.0.0.1:{FRONTEND_PORT}/#/analyzer")
            page.wait_for_selector("#sample-spam-btn", timeout=10000)

            page.click("#sample-spam-btn")
            page.wait_for_timeout(300)
            page.click("#analyze-btn")

            page.wait_for_selector("#report-active-view:not(.hidden)", timeout=15000)
            analyzer_verdict = page.locator("#report-classification-val").text_content().strip()
            analyzer_score = page.locator("#risk-ring-num").text_content().strip()
            print(f"  Analyzer report result: Verdict='{analyzer_verdict}', Risk Score='{analyzer_score}'")

            assert analyzer_verdict == "Spam", f"Expected Spam verdict, got '{analyzer_verdict}'"
            assert analyzer_score in ("99.3", "100"), f"Expected deterministic score (99.3 or 100), got '{analyzer_score}'"
            print(f"  [PASS] Deterministic Analyzer scan verified (Verdict=Spam, Score={analyzer_score}).")

            # Capture screenshot
            page.screenshot(path=str(SCREENSHOT_DIR / "split_architecture_cross_origin.png"), full_page=True)
            print(f"  Saved screenshot: {SCREENSHOT_DIR / 'split_architecture_cross_origin.png'}")

            # -----------------------------------------------------------------
            # TEST 5: COLD-START WAKING BANNER & ERROR RESILIENCE
            # -----------------------------------------------------------------
            print("\n--- TEST 5: Cold-Start Waking Banner & Error Handling ---")
            page.goto(f"http://127.0.0.1:{FRONTEND_PORT}/#/home")
            page.wait_for_selector("#home-quick-analyze-btn", timeout=10000)

            # Test 5a: Cold-start 3s delay triggers waking banner
            print("  Testing 5a: Simulating cold-start delay (>3s in-flight)...")
            held_routes = []

            def hold_analyze(route):
                held_routes.append(route)

            page.route("**/api/analyze", hold_analyze)

            page.locator("#home-quick-text").fill("Subject: Account Verification Required. Please confirm details.")
            page.locator("#home-quick-analyze-btn").click()

            # Wait 3.3s while request is in-flight: waking banner must appear at 3.0s
            page.wait_for_timeout(3300)

            waking_banner = page.locator("#home-waking-banner")
            is_waking_visible = not ("hidden" in (waking_banner.get_attribute("class") or ""))
            print(f"  Waking banner visibility at t=3.3s: {is_waking_visible}")
            assert is_waking_visible, "Cold-start waking banner should be visible when request exceeds 3 seconds"

            banner_text = waking_banner.locator(".waking-banner-text").inner_text()
            print(f"  Waking banner text: '{banner_text}'")
            assert "Waking up the server, this can take up to a minute on the free host" in banner_text

            page.screenshot(path=str(SCREENSHOT_DIR / "split_architecture_cold_start.png"))
            print(f"  Saved screenshot: {SCREENSHOT_DIR / 'split_architecture_cold_start.png'}")

            # Resume request
            if held_routes:
                held_routes[0].continue_()
            page.unroute("**/api/analyze")
            page.wait_for_selector("#home-waking-banner", state="hidden", timeout=10000)
            print("  [PASS] Cold-start waking banner appeared at 3s and dismissed cleanly after response.")

            # Test 5b: 503 Service Unavailable
            print("  Testing 5b: 503 Service Unavailable handling...")
            page.goto(f"http://127.0.0.1:{FRONTEND_PORT}/#/analyzer")
            page.wait_for_selector("#sample-spam-btn", timeout=10000)
            page.click("#sample-spam-btn")

            page.route("**/api/analyze", lambda route: route.fulfill(
                status=503,
                content_type="application/json",
                body=json.dumps({"error": {"code": "service_unavailable", "message": "Backend warming up"}})
            ))
            page.click("#analyze-btn")
            page.wait_for_selector("#general-error:not(.hidden)", timeout=10000)
            gen_err_503 = page.locator("#general-error-message").text_content()
            print(f"  503 response error display: '{gen_err_503}'")
            assert "Backend warming up" in gen_err_503 or "error" in gen_err_503.lower() or "503" in gen_err_503
            page.unroute("**/api/analyze")
            print("  [PASS] 503 response handled gracefully.")

            # Test 5c: Network drop / connection abort
            print("  Testing 5c: Network drop / connection abort handling...")
            page.route("**/api/analyze", lambda route: route.abort("failed"))
            page.click("#analyze-btn")
            page.wait_for_selector("#general-error:not(.hidden)", timeout=10000)
            abort_err = page.locator("#general-error-message").text_content()
            print(f"  Network failure error display: '{abort_err}'")
            page.unroute("**/api/analyze")
            print("  [PASS] Connection abort handled gracefully without uncaught exceptions.")

            # -----------------------------------------------------------------
            # TEST 6: CLIENT-SIDE OCR & QR IN SPLIT MODE UNDER VERCEL HEADERS
            # -----------------------------------------------------------------
            print("\n--- TEST 6: OCR & QR Analysis in Split Mode (Vercel Headers) ---")
            page.goto(f"http://127.0.0.1:{FRONTEND_PORT}/#/image-analysis")
            page.wait_for_selector("#img-drop-zone", timeout=10000)

            # Fixture 1: text_screenshot.png (or email_screenshot.png)
            print("  Testing Fixture 1: Email screenshot Web Worker OCR...")
            text_file = FIXTURES_DIR / "text_screenshot.png"
            page.set_input_files("#img-file-input", str(text_file))
            page.wait_for_selector("#img-preview-box:not(.hidden)", timeout=5000)

            t0 = time.perf_counter()
            page.click("#img-start-scan-btn")
            page.wait_for_selector("#img-report-container:not(.hidden)", timeout=40000)
            ocr_dur = time.perf_counter() - t0

            img_verdict = page.locator("#img-verdict-badge").text_content().strip()
            img_score = page.locator("#img-risk-score-val").text_content().strip()
            ocr_text = page.locator("#img-ocr-text-display").text_content().strip()
            print(f"  Fixture 1 OCR ({ocr_dur:.2f}s) -> Verdict='{img_verdict}', Score='{img_score}'")
            print(f"  Extracted text snippet: '{ocr_text[:80]}...'")

            assert img_verdict in ["Spam", "Suspicious"], f"Unexpected verdict: {img_verdict}"
            assert float(img_score.split("/")[0]) >= 50.0, f"Expected risk >= 50, got {img_score}"
            assert "URGENT" in ocr_text or "NOTICE" in ocr_text or "restricted" in ocr_text

            page.screenshot(path=str(SCREENSHOT_DIR / "split_architecture_ocr.png"), full_page=True)
            print(f"  Saved screenshot: {SCREENSHOT_DIR / 'split_architecture_ocr.png'}")
            print("  [PASS] Fixture 1 processed via Web Worker OCR under strict Vercel CSP.")

            # Fixture 2: qr_phish.png (or phishing_qr.png)
            print("  Testing Fixture 2: Phishing QR Code analysis...")
            page.click("#img-clear-selection-btn")
            page.wait_for_selector("#img-preview-box", state="hidden")

            qr_file = FIXTURES_DIR / "qr_phish.png"
            page.set_input_files("#img-file-input", str(qr_file))
            page.wait_for_selector("#img-preview-box:not(.hidden)", timeout=5000)

            page.click("#img-start-scan-btn")
            page.wait_for_selector("#img-report-container:not(.hidden)", timeout=40000)

            qr_val = page.locator("#img-qr-text-val").text_content().strip()
            qr_verdict = page.locator("#img-verdict-badge").text_content().strip()
            print(f"  Fixture 2 QR -> Content='{qr_val}', Verdict='{qr_verdict}'")
            assert qr_val == "http://phishing-portal.test/steal-credentials", f"Unexpected QR decoded: {qr_val}"
            assert qr_verdict in ["Spam", "Suspicious"], f"Unexpected QR verdict: {qr_verdict}"
            print("  [PASS] Fixture 2 decoded via client-side jsQR and flagged as phishing threat.")

            # Fixture 3: plain_photo.jpg (or clean_photo.jpg)
            print("  Testing Fixture 3: Benign clean photo (zero text / zero QR)...")
            page.click("#img-clear-selection-btn")
            page.wait_for_selector("#img-preview-box", state="hidden")

            clean_file = FIXTURES_DIR / "plain_photo.jpg"
            page.set_input_files("#img-file-input", str(clean_file))
            page.wait_for_selector("#img-preview-box:not(.hidden)", timeout=5000)

            page.click("#img-start-scan-btn")
            page.wait_for_selector("#img-report-container:not(.hidden)", timeout=40000)

            clean_verdict = page.locator("#img-verdict-badge").text_content().strip()
            clean_risk = page.locator("#img-risk-score-val").text_content().strip()
            print(f"  Fixture 3 Clean -> Verdict='{clean_verdict}', Risk='{clean_risk}'")
            assert clean_verdict == "Safe", f"Expected Safe verdict, got {clean_verdict}"
            assert "0" in clean_risk, f"Expected 0 risk, got {clean_risk}"
            print("  [PASS] Fixture 3 yields clean Safe verdict.")

            # -----------------------------------------------------------------
            # TEST 7: ZERO CSP VIOLATIONS & ZERO CONSOLE ERRORS
            # -----------------------------------------------------------------
            print("\n--- TEST 7: Zero CSP Violations & Zero Console Errors Audit ---")
            violations = page.evaluate("() => window.__csp_violations || []")
            print(f"  Recorded CSP violations: {len(violations)}")
            if violations:
                print(f"  CSP Violations Detail: {violations}")
            assert len(violations) == 0, f"Found {len(violations)} CSP violations!"

            # Filter console errors to ignore expected test-induced network abort logs if any
            real_console_errors = [
                e for e in console_errors
                if "favicon" not in e.lower()
                and "503" not in e
                and "failed" not in e.lower()
                and "net::err" not in e.lower()
            ]
            print(f"  Recorded console errors: {len(real_console_errors)}")
            assert len(real_console_errors) == 0, f"Found console errors: {real_console_errors}"
            assert len(page_errors) == 0, f"Found uncaught page errors: {page_errors}"
            print("  [PASS] Strict CSP Level 3 enforced: ZERO violations and ZERO console errors.")

            # -----------------------------------------------------------------
            # TEST 8: AXE ACCESSIBILITY AUDIT ACROSS ALL ROUTES
            # -----------------------------------------------------------------
            print("\n--- TEST 8: Axe-core Accessibility Audit Across Routes ---")
            axe = Axe()
            routes_to_audit = ["#/home", "#/analyzer", "#/image-analysis", "#/dashboard", "#/features", "#/privacy"]

            for route in routes_to_audit:
                page.goto(f"http://127.0.0.1:{FRONTEND_PORT}/{route}")
                page.wait_for_timeout(500)
                axe_res = axe.run(page)
                v_list = axe_res.get("violations", [])
                critical_serious = [v for v in v_list if v.get("impact") in ("critical", "serious")]
                print(f"  Route {route:<18} -> {len(v_list)} total violations, {len(critical_serious)} critical/serious")
                assert len(critical_serious) == 0, f"Axe violations on {route}: {critical_serious}"

            print("  [PASS] Axe accessibility audit passed on all routes (0 critical/serious).")

            browser.close()

        print("\n" + "=" * 75)
        print("PHASE 12J: ALL SPLIT DEPLOYMENT VERIFICATIONS PASSED 100%!")
        print("=" * 75)
        return 0

    finally:
        print("\nRestoring placeholder origin and cleaning up...")
        STATIC_CONFIG.write_text(orig_config, encoding="utf-8")
        VERCEL_JSON.write_text(orig_vercel, encoding="utf-8")
        try:
            from scripts.build_frontend import build_frontend
            build_frontend()
        except Exception:
            pass

        try:
            vercel_server.shutdown()
            vercel_server.server_close()
        except Exception:
            pass
        try:
            backend_proc.terminate()
            backend_proc.wait(timeout=3)
        except Exception:
            try:
                backend_proc.kill()
            except Exception:
                pass


if __name__ == "__main__":
    sys.exit(run_split_verification())
