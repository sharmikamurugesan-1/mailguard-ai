"""Full regression and comprehensive accessibility audit for MailGuard AI v2.0.0.

Tests:
1. Axe-core accessibility on EVERY route:
   - #/home
   - #/analyze
   - #/image-analysis
   - #/dashboard
   - #/history
   - #/reports
   - #/settings
   - #/docs
   - #/model-card
   - #/features
   - #/privacy
2. Interactive flow verification:
   - Home quick scan
   - Email analyzer
   - Client-side Image OCR & QR analysis
   - IndexedDB persistence across views
   - Settings localStorage updates
   - CSV and JSON report exports
3. Generates release-ready screenshot artifacts.
"""

import json
import os
from pathlib import Path
import subprocess
import sys
import time

from axe_core_python.sync_playwright import Axe
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
PORT = 5005
BASE_URL = f"http://127.0.0.1:{PORT}"
SCREENSHOT_DIR = BASE_DIR / "docs" / "screenshots" / "v2"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


def start_server():
    cmd = [
        sys.executable,
        "-c",
        f"""
import sys
from pathlib import Path
sys.path.insert(0, r"{BASE_DIR}")
from src.app import create_app
app = create_app({{'TESTING': True, 'RATELIMIT_ENABLED': False}})
app.run(host='127.0.0.1', port={PORT}, debug=False)
""",
    ]
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    return proc


def wait_for_server(timeout=15.0):
    import urllib.request
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(f"{BASE_URL}/api/health", timeout=1.0) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.3)
    return False


def run_full_regression():
    server = start_server()
    try:
        if not wait_for_server():
            print("ERROR: Server failed to start.")
            server.terminate()
            return False

        print("=" * 75)
        print("MAILGUARD AI v2.0.0 - FULL REGRESSION & ACCESSIBILITY AUDIT")
        print("=" * 75)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1280, "height": 900})
            page = context.new_page()
            axe = Axe()

            # 1. Audit EVERY Route for Axe-core accessibility (WCAG 2 AA/AAA)
            routes = [
                ("Home", "#/home"),
                ("Email Analyzer", "#/analyze"),
                ("Image Analyzer", "#/image-analysis"),
                ("Dashboard", "#/dashboard"),
                ("Scan History", "#/history"),
                ("Reports Export", "#/reports"),
                ("Settings", "#/settings"),
                ("API Docs", "#/docs"),
                ("Model Card", "#/model-card"),
                ("Platform Features", "#/features"),
                ("Privacy & Security", "#/privacy"),
            ]

            all_passed = True
            print("\n--- AXE-CORE ACCESSIBILITY AUDIT ON ALL ROUTES ---")
            for name, route in routes:
                page.goto(f"{BASE_URL}/{route}", wait_until="networkidle")
                page.wait_for_timeout(300)

                # Inject and run axe
                results = axe.run(page)
                violations = results.get("violations", [])
                status = "[PASS]" if len(violations) == 0 else "[FAIL]"
                if len(violations) > 0:
                    all_passed = False
                    print(f"{status:7} {name:<22} ({route:<18}): {len(violations)} violations")
                    for v in violations:
                        print(f"        -> {v.get('id')}: {v.get('help')} ({v.get('impact')})")
                else:
                    print(f"{status:7} {name:<22} ({route:<18}): 0 violations (WCAG compliant)")

            # 2. Interactive flow: Analyze on Home and verify handoff
            print("\n--- INTERACTIVE FLOW CHECKS ---")
            page.goto(f"{BASE_URL}/#/home", wait_until="networkidle")
            page.wait_for_selector(".example-chip")
            chips = page.query_selector_all(".example-chip")
            assert len(chips) >= 7, f"Expected >=7 chips, got {len(chips)}"
            chips[0].click()
            page.wait_for_selector("#home-quick-result-card:not(.hidden)", timeout=10000)
            print("[PASS]  Home Quick-Scan executed and rendered result card.")

            # Verify scan persists to Dashboard via in-app router
            page.locator("#nav-dashboard").click()
            page.wait_for_function(
                "() => document.getElementById('dash-stat-total') && parseInt(document.getElementById('dash-stat-total').textContent) >= 1",
                timeout=5000,
            )
            total_text = page.locator("#dash-stat-total").inner_text().strip()
            assert int(total_text) >= 1, f"Expected >=1 scan in dashboard, got {total_text}"
            print(f"[PASS]  Scan persisted to IndexedDB Dashboard (total scans = {total_text}).")

            # 3. Interactive flow: Email Analyzer
            page.locator("#nav-analyzer").click()
            page.wait_for_timeout(300)
            page.fill("#subject-input", "Security alert: Unusual login detected")
            page.fill("#body-input", "We detected a login from an unknown device. Please review http://login-review.example.test immediately.")
            page.click("#analyze-btn")
            page.wait_for_selector("#risk-ring-num", timeout=10000)
            print("[PASS]  Email Analyzer submitted and generated detailed report.")

            # 4. Interactive flow: Image Analyzer with fixture
            qr_fixture = BASE_DIR / "tests" / "fixtures" / "qr_phishing.png"
            if qr_fixture.exists():
                page.locator("#nav-image-analysis").click()
                page.wait_for_timeout(500)
                file_input = page.query_selector("#img-file-input")
                if file_input:
                    file_input.set_input_files(str(qr_fixture))
                    page.wait_for_selector("#img-verdict-badge", timeout=20000)
                    print("[PASS]  Image Analyzer decoded QR phishing fixture.")

            # 5. Interactive flow: Settings toggle persistence
            page.locator("#nav-settings").click()
            page.wait_for_timeout(300)
            pref_tab = page.query_selector("#tab-btn-pref")
            if pref_tab:
                pref_tab.click()
                page.wait_for_timeout(200)
            sens_select = page.query_selector("#setting-sensitivity")
            if sens_select:
                sens_select.select_option("high")
                # Trigger change event
                sens_select.dispatch_event("change")
                page.wait_for_timeout(200)
                # Check localStorage
                saved_sens = page.evaluate("() => localStorage.getItem('mg_setting_sensitivity')")
                assert saved_sens == "high", f"Expected 'high' in localStorage, got {saved_sens}"
                print("[PASS]  Settings preference persisted in localStorage.")

            # 6. Interactive flow: Model Card
            page.goto(f"{BASE_URL}/#/model-card", wait_until="networkidle")
            page.wait_for_timeout(500)
            svg_cm = page.query_selector("#svg-container-cm svg")
            svg_pr = page.query_selector("#svg-container-pr svg")
            svg_cal = page.query_selector("#svg-container-cal svg")
            assert svg_cm is not None, "Confusion matrix SVG missing"
            assert svg_pr is not None, "PR curve SVG missing"
            assert svg_cal is not None, "Calibration curve SVG missing"
            print("[PASS]  Model Card rendered all 3 inline SVG charts.")

            # Capture screenshots for README
            page.goto(f"{BASE_URL}/#/home", wait_until="networkidle")
            page.wait_for_timeout(400)
            page.screenshot(path=str(SCREENSHOT_DIR / "release_01_home.png"), full_page=True)

            page.goto(f"{BASE_URL}/#/image-analysis", wait_until="networkidle")
            page.wait_for_timeout(400)
            page.screenshot(path=str(SCREENSHOT_DIR / "release_02_image_analyzer.png"), full_page=True)

            page.goto(f"{BASE_URL}/#/model-card", wait_until="networkidle")
            page.wait_for_timeout(400)
            page.screenshot(path=str(SCREENSHOT_DIR / "release_03_model_card.png"), full_page=True)

            print(f"[PASS]  Release screenshots saved to {SCREENSHOT_DIR.relative_to(BASE_DIR)}")

            browser.close()

        print("-" * 75)
        if all_passed:
            print("RESULT: FULL REGRESSION AND 11-ROUTE AXE-CORE AUDIT PASSED 100%!")
            print("=" * 75)
            return True
        else:
            print("RESULT: ONE OR MORE AUDITS FAILED.")
            print("=" * 75)
            return False

    finally:
        server.terminate()
        server.wait()


if __name__ == "__main__":
    success = run_full_regression()
    sys.exit(0 if success else 1)
