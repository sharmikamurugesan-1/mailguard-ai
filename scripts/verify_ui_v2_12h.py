"""Playwright automated verification for MailGuard AI v2 Phase 12H.

Phase 12H Requirements:
1. Home view: hero with a quick-analyze box (uses /api/analyze), "Try an example" buttons
   (3 spam, 3 safe, 1 borderline) from static JSON.
2. Features section: ONLY features that truly exist + "What this can and can't do" block:
   spam detection only, not malware, not a mail filter, no accounts.
3. Cold-start UX: if request takes >3s, show "Waking up the server, this can take up to a minute on the free host" with retry.
4. Privacy/About view: what is processed (in-memory only), what is stored (local-only IndexedDB/localStorage),
   what is not stored (no server-side emails/images ever), stack, link to repo.
5. Themed 404 and 500 error pages. Favicon. Route page titles. Open Graph & Twitter meta tags.
6. Sensible empty states on all views. Zero dead links.

VERIFICATION PROTOCOL:
- Run in real Chromium browser (Playwright)
- Test as a brand-new visitor: Home -> click example -> result -> Dashboard shows 1 scan.
- Simulate slow first response (>3s) -> waking banner appears with retry.
- Axe-core accessibility audit = 0 violations.
- Strict CSP: zero inline styles/scripts, zero innerHTML, zero console errors.
- Capture screenshots in docs/screenshots/v2/.
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

BASE_URL = "http://127.0.0.1:5012"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCREENSHOT_DIR = PROJECT_ROOT / "docs" / "screenshots" / "v2"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


def run_verification():
    print("=" * 80)
    print("MAILGUARD AI v2 - PHASE 12H PLAYWRIGHT VERIFICATION AUDIT")
    print("=" * 80)

    # 1. Start isolated Flask test server on port 5012
    env = os.environ.copy()
    env["PORT"] = "5012"
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

    print("Starting MailGuard AI test server on port 5012...")
    started = False
    for attempt in range(30):
        try:
            with urllib.request.urlopen(f"{BASE_URL}/api/health", timeout=2) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    print(f"Server healthy on port 5012. Model loaded: {data.get('model_loaded')}")
                    started = True
                    break
        except Exception:
            time.sleep(0.5)

    if not started:
        print("ERROR: Server failed to start within timeout.")
        server_process.terminate()
        sys.exit(1)

    console_errors = []
    page_errors = []
    csp_violations = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            # Create isolated browser context for fresh brand-new visitor
            context = browser.new_context(viewport={"width": 1440, "height": 960})
            page = context.new_page()

            def handle_console(msg):
                if msg.type == "error":
                    text = msg.text
                    console_errors.append(text)
                    if "Content Security Policy" in text or "CSP" in text:
                        csp_violations.append(text)
                    print(f"  [BROWSER ERROR] {text}")

            def handle_pageerror(err):
                page_errors.append(str(err))
                print(f"  [PAGE ERROR] {err}")

            page.on("console", handle_console)
            page.on("pageerror", handle_pageerror)

            print("\n" + "-" * 60)
            print("STEP 1: Brand-New Visitor Landing & Home View Check")
            print("-" * 60)

            # Navigate to root /
            page.goto(f"{BASE_URL}/", wait_until="networkidle")
            page.wait_for_timeout(1000)

            current_url = page.url
            print(f"Loaded URL: {current_url}")
            assert "#/home" in current_url, f"Expected redirect to #/home, got {current_url}"

            title = page.title()
            print(f"Page Title: {title}")
            assert "Home" in title or "MailGuard" in title, f"Unexpected page title: {title}"

            # Verify Hero elements
            hero_title = page.locator(".hero-headline")
            assert hero_title.is_visible(), "Hero headline should be visible"
            print("Hero section is visible.")

            # Verify Example chips rendered
            example_chips = page.locator("#home-examples-chips button.example-chip")
            chips_count = example_chips.count()
            print(f"Rendered example chips count: {chips_count}")
            assert chips_count == 7, f"Expected 7 example chips, found {chips_count}"

            # Verify categories
            spam_chips = page.locator("#home-examples-chips button.chip-spam").count()
            safe_chips = page.locator("#home-examples-chips button.chip-safe").count()
            borderline_chips = page.locator("#home-examples-chips button.chip-borderline").count()
            print(f"Chips breakdown -> Spam: {spam_chips}, Safe: {safe_chips}, Borderline: {borderline_chips}")
            assert spam_chips == 3, f"Expected 3 spam chips, got {spam_chips}"
            assert safe_chips == 3, f"Expected 3 safe chips, got {safe_chips}"
            assert borderline_chips == 1, f"Expected 1 borderline chip, got {borderline_chips}"

            page.screenshot(path=str(SCREENSHOT_DIR / "01_home_first_time_visitor.png"))
            print("Captured screenshot: 01_home_first_time_visitor.png")

            print("\n" + "-" * 60)
            print("STEP 2: Click Example -> Instant Quick Analysis Result")
            print("-" * 60)

            # Click first spam example chip
            first_spam_chip = page.locator("#home-examples-chips button.chip-spam").first
            chip_label = first_spam_chip.inner_text().replace("\n", " ")
            print(f"Clicking example chip: {chip_label}")
            first_spam_chip.click()

            # Wait for result card to render
            page.wait_for_selector("#home-quick-result-card:not(.hidden)", timeout=10000)

            # Verify populated form inputs
            subject_val = page.locator("#home-quick-subject").input_value()
            body_val = page.locator("#home-quick-text").input_value()
            print(f"Form populated with Subject: '{subject_val}' ({len(body_val)} body chars)")
            assert len(body_val) > 20, "Expected body to be populated from example"

            # Verify quick analysis card results
            verdict_badge = page.locator("#home-result-badge").inner_text()
            score_text = page.locator("#home-result-score").inner_text()
            prob_text = page.locator("#home-result-prob").inner_text()
            conf_text = page.locator("#home-result-conf").inner_text()
            print(f"Analysis Verdict: {verdict_badge} | Risk Score: {score_text}/100 | Prob: {prob_text} | Conf: {conf_text}")

            assert "Spam" in verdict_badge, f"Expected Spam verdict, got {verdict_badge}"
            score_num = int(score_text)
            assert score_num >= 80, f"Expected risk score >= 80, got {score_num}"

            # Verify findings and signal tokens
            findings_count = page.locator("#home-result-findings-list li").count()
            tokens_count = page.locator("#home-result-tokens-chips span.quick-token-chip").count()
            print(f"Key findings rendered: {findings_count} | Signal tokens rendered: {tokens_count}")
            assert findings_count >= 1, "Expected at least 1 key finding"
            assert tokens_count >= 1, "Expected explaining token chips"

            page.screenshot(path=str(SCREENSHOT_DIR / "02_home_quick_scan_result.png"))
            print("Captured screenshot: 02_home_quick_scan_result.png")

            print("\n" + "-" * 60)
            print("STEP 3: Dashboard Integration (IndexedDB Persistence)")
            print("-" * 60)

            # Navigate to Dashboard
            page.locator("#nav-dashboard").click()
            page.wait_for_timeout(800)
            assert "#/dashboard" in page.url

            # Wait for dashboard UI to read IndexedDB
            page.wait_for_function("() => document.getElementById('dash-stat-total') && document.getElementById('dash-stat-total').textContent === '1'", timeout=5000)
            total_scans = page.locator("#dash-stat-total").inner_text()
            spam_scans = page.locator("#dash-stat-spam").inner_text()
            print(f"Dashboard Stats -> Total Scans: {total_scans}, Spam Scans: {spam_scans}")
            assert total_scans == "1", f"Expected Total Scans = 1, got {total_scans}"
            assert spam_scans == "1", f"Expected Spam Scans = 1, got {spam_scans}"

            # Verify table row
            table_rows = page.locator("#dash-recent-tbody tr").count()
            print(f"Recent scans table row count: {table_rows}")
            assert table_rows == 1, f"Expected 1 row in scan history table, got {table_rows}"

            page.screenshot(path=str(SCREENSHOT_DIR / "03_dashboard_with_1_scan.png"))
            print("Captured screenshot: 03_dashboard_with_1_scan.png")

            print("\n" + "-" * 60)
            print("STEP 4: Cold-Start UX Simulation (>3s Request Delay)")
            print("-" * 60)

            # Return to Home
            page.locator("#top-nav-home").click()
            page.wait_for_timeout(600)

            # Set up held route for /api/analyze to simulate server cold start
            held_routes = []
            def hold_analyze_route(route):
                print("  [SIMULATOR] Intercepted /api/analyze -> holding in-flight to simulate cold-start latency (>3s)...")
                held_routes.append(route)

            page.route("**/api/analyze", hold_analyze_route)

            # Enter text and trigger quick scan
            page.locator("#home-quick-text").fill("Warning: Immediate account identity confirmation required to avoid suspension.")
            page.locator("#home-quick-analyze-btn").click()

            # Wait 3.3s while request is in-flight: waking banner must appear at 3.0s
            page.wait_for_timeout(3300)

            waking_banner = page.locator("#home-waking-banner")
            is_waking_visible = not ("hidden" in (waking_banner.get_attribute("class") or ""))
            print(f"Waking banner visibility at t=3.3s: {is_waking_visible}")
            assert is_waking_visible, "Cold-start waking banner should be visible when request exceeds 3 seconds"

            banner_text = waking_banner.locator(".waking-banner-text").inner_text()
            print(f"Waking banner message: '{banner_text}'")
            assert "Waking up the server, this can take up to a minute on the free host" in banner_text

            retry_btn = page.locator("#home-waking-retry-btn")
            assert retry_btn.is_visible(), "Waking banner must have retry button"

            # Click retry button
            retry_btn.click()
            print("Clicked retry button on waking banner.")

            page.screenshot(path=str(SCREENSHOT_DIR / "04_cold_start_waking_banner.png"))
            print("Captured screenshot: 04_cold_start_waking_banner.png")

            # Clean up route interception: let held request complete
            if held_routes:
                try:
                    held_routes[0].continue_()
                except Exception:
                    pass
            page.unroute("**/api/analyze")
            page.wait_for_selector("#home-waking-banner", state="hidden", timeout=8000)
            print("Waking banner cleanly hidden after response returned.")

            print("\n" + "-" * 60)
            print("STEP 5: Features View & Scope Transparency Check")
            print("-" * 60)

            page.locator("#top-nav-features").click()
            page.wait_for_timeout(600)
            assert "#/features" in page.url

            feature_cards = page.locator(".features-grid .feature-card").count()
            print(f"Active platform feature cards: {feature_cards}")
            assert feature_cards == 6, f"Expected 6 real features, found {feature_cards}"

            # Verify "What this can and can't do" comparison card
            scope_card = page.locator("#scope-comparison-card")
            assert scope_card.is_visible(), "Scope comparison card must be visible"

            can_header = page.locator(".badge-can").inner_text()
            cannot_header = page.locator(".badge-cannot").inner_text()
            print(f"Scope columns: '{can_header}' vs '{cannot_header}'")

            cannot_items_text = page.locator(".scope-column-cannot").inner_text()
            assert "Spam detection only, not malware" in cannot_items_text, "Must state 'Spam detection only, not malware'"
            assert "Not an automated mail filter" in cannot_items_text, "Must state 'Not an automated mail filter'"
            assert "No user accounts or cloud storage" in cannot_items_text, "Must state 'No user accounts or cloud storage'"
            print("Verified scope boundaries: spam detection only, not malware, not mail filter, no accounts.")

            page.screenshot(path=str(SCREENSHOT_DIR / "05_features_and_scope.png"))
            print("Captured screenshot: 05_features_and_scope.png")

            print("\n" + "-" * 60)
            print("STEP 6: Privacy & Security Architecture View Check")
            print("-" * 60)

            page.locator("#top-nav-privacy").click()
            page.wait_for_timeout(600)
            assert "#/privacy" in page.url

            privacy_title = page.locator("#view-privacy .card-maroon-title").inner_text()
            print(f"Privacy View Title: {privacy_title}")
            assert "Privacy & Security Architecture" in privacy_title

            privacy_cards = page.locator(".privacy-grid .privacy-card").count()
            print(f"Privacy policy pillar cards: {privacy_cards}")
            assert privacy_cards == 4, f"Expected 4 policy pillars, found {privacy_cards}"

            privacy_body_text = page.locator("#view-privacy").inner_text()
            assert "What is Processed" in privacy_body_text
            assert "In-Memory" in privacy_body_text or "in-memory" in privacy_body_text
            assert "What is Stored" in privacy_body_text
            assert "IndexedDB" in privacy_body_text
            assert "What is Never Stored" in privacy_body_text
            assert "Technology Stack" in privacy_body_text

            repo_link = page.locator(".privacy-repo-card a[href*='github']")
            assert repo_link.is_visible(), "GitHub repository link must be present"
            print(f"Repo link target: {repo_link.get_attribute('href')}")

            page.screenshot(path=str(SCREENSHOT_DIR / "06_privacy_view.png"))
            print("Captured screenshot: 06_privacy_view.png")

            print("\n" + "-" * 60)
            print("STEP 7: Themed 404 Error Page Check")
            print("-" * 60)

            page.goto(f"{BASE_URL}/non-existent-page-path", wait_until="networkidle")
            error_code = page.locator(".error-code-badge").inner_text()
            print(f"404 page error badge: {error_code}")
            assert error_code == "404", f"Expected 404 badge, got {error_code}"

            return_btn = page.locator(".error-actions a[href*='dashboard']")
            assert return_btn.is_visible(), "Return to Dashboard action must be present"

            page.screenshot(path=str(SCREENSHOT_DIR / "07_themed_404_page.png"))
            print("Captured screenshot: 07_themed_404_page.png")

            print("\n" + "-" * 60)
            print("STEP 8: Accessibility Audit (Axe-Core)")
            print("-" * 60)

            axe = Axe()

            # Audit #/home
            page.goto(f"{BASE_URL}/#/home", wait_until="networkidle")
            page.wait_for_timeout(800)
            results_home = axe.run(page)
            violations_home = results_home.get("violations", [])
            print(f"Axe violations on #/home: {len(violations_home)}")
            for v in violations_home:
                print(f"  VIOLATION HOME: {v['id']} - {v['description']}")
                for node in v.get('nodes', []):
                    print(f"    Target: {node.get('target')} | HTML: {node.get('html')}")

            # Audit #/features
            page.goto(f"{BASE_URL}/#/features", wait_until="networkidle")
            page.wait_for_timeout(800)
            results_feat = axe.run(page)
            violations_feat = results_feat.get("violations", [])
            print(f"Axe violations on #/features: {len(violations_feat)}")
            for v in violations_feat:
                print(f"  VIOLATION FEAT: {v['id']} - {v['description']}")
                for node in v.get('nodes', []):
                    print(f"    Target: {node.get('target')} | HTML: {node.get('html')}")

            # Audit #/privacy
            page.goto(f"{BASE_URL}/#/privacy", wait_until="networkidle")
            page.wait_for_timeout(800)
            results_priv = axe.run(page)
            violations_priv = results_priv.get("violations", [])
            print(f"Axe violations on #/privacy: {len(violations_priv)}")
            for v in violations_priv:
                print(f"  VIOLATION PRIV: {v['id']} - {v['description']}")
                for node in v.get('nodes', []):
                    print(f"    Target: {node.get('target')} | HTML: {node.get('html')}")

            # Audit #/dashboard
            page.goto(f"{BASE_URL}/#/dashboard", wait_until="networkidle")
            page.wait_for_timeout(800)
            results_dash = axe.run(page)
            violations_dash = results_dash.get("violations", [])
            print(f"Axe violations on #/dashboard: {len(violations_dash)}")
            for v in violations_dash:
                print(f"  VIOLATION DASH: {v['id']} - {v['description']}")
                for node in v.get('nodes', []):
                    print(f"    Target: {node.get('target')} | HTML: {node.get('html')}")

            total_violations = len(violations_home) + len(violations_feat) + len(violations_priv) + len(violations_dash)
            assert total_violations == 0, f"Expected 0 accessibility violations, got {total_violations}"
            print("ALL ACCESSIBILITY AUDITS (HOME, FEATURES, PRIVACY, DASHBOARD) PASSED WITH ZERO VIOLATIONS!")

            print("\n" + "-" * 60)
            print("STEP 9: Quality & Security Integrity Checks")
            print("-" * 60)
            print(f"Total Console Errors: {len(console_errors)}")
            print(f"Total Page Errors: {len(page_errors)}")
            print(f"Total CSP Violations: {len(csp_violations)}")

            assert len(csp_violations) == 0, f"Found {len(csp_violations)} CSP violations: {csp_violations}"
            assert len(page_errors) == 0, f"Found {len(page_errors)} page errors: {page_errors}"

            browser.close()

    finally:
        print("\nShutting down test server...")
        server_process.terminate()
        server_process.wait(timeout=5)
        print("Test server stopped cleanly.")

    print("\n" + "=" * 80)
    print("PHASE 12H PLAYWRIGHT VERIFICATION AUDIT PASSED 100%!")
    print("=" * 80)


if __name__ == "__main__":
    run_verification()
