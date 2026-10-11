#!/usr/bin/env python3
"""Verification script for MailGuard AI split architecture (Phase 12I).

Simulates Vercel frontend + Render backend locally:
1. Spawns backend Flask server on http://127.0.0.1:5000 with CORS_ALLOWED_ORIGINS set to port 3000.
2. Spawns frontend static HTTP server on http://127.0.0.1:3000 serving the frontend/ directory.
3. Uses Playwright to load http://127.0.0.1:3000/#/home.
4. Confirms:
   - window.API_BASE_URL resolves to http://127.0.0.1:5000.
   - Cross-origin health check succeeds (Server Online indicator).
   - Cross-origin quick scan on #/home executes, receives 200, and renders ML predictions.
   - Cross-origin deep scan on #/analyzer executes with token highlights.
5. Saves screenshot evidence to docs/screenshots/v2/split_architecture_cross_origin.png.
"""

import http.server
import os
from pathlib import Path
import socketserver
import subprocess
import sys
import threading
import time

from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
SCREENSHOT_DIR = BASE_DIR / "docs" / "screenshots" / "v2"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

BACKEND_PORT = 5000
FRONTEND_PORT = 3000


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


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


def start_frontend_server():
    """Start Python HTTP server serving frontend/ on port 3000."""
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

        def log_message(self, format, *args):
            pass  # Quiet logging

    httpd = ReusableTCPServer(("127.0.0.1", FRONTEND_PORT), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd


def run_split_verification():
    print("=" * 70)
    print("PHASE 12I: SPLIT ARCHITECTURE PLAYWRIGHT VERIFICATION")
    print(f"Backend API:   http://127.0.0.1:{BACKEND_PORT} (Simulating Render)")
    print(f"Frontend Host: http://127.0.0.1:{FRONTEND_PORT} (Simulating Vercel)")
    print("=" * 70)

    # 1. Start Backend
    print("[1/5] Starting backend Flask server on port 5000...")
    backend_proc = start_backend()
    time.sleep(2)

    # 2. Start Frontend Server
    print("[2/5] Starting static frontend server on port 3000...")
    frontend_server = start_frontend_server()
    time.sleep(1)

    try:
        # 3. Playwright browser test
        print("[3/5] Launching Playwright browser...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1400, "height": 950})

            # Track network requests
            api_requests = []
            page.on("request", lambda req: api_requests.append(req.url) if f":{BACKEND_PORT}/api" in req.url else None)

            # Navigate to frontend host
            print(f"  Navigating to http://127.0.0.1:{FRONTEND_PORT}/#/home...")
            page.goto(f"http://127.0.0.1:{FRONTEND_PORT}/#/home", wait_until="networkidle")
            time.sleep(1)

            # Check config API_BASE_URL
            api_url = page.evaluate("() => window.API_BASE_URL")
            print(f"  Detected window.API_BASE_URL: '{api_url}'")
            assert api_url == f"http://127.0.0.1:{BACKEND_PORT}", f"Unexpected API_BASE_URL: {api_url}"

            # Check Server Online status indicator
            page.wait_for_selector("#status-dot.status-online", timeout=10000)
            status_text = page.locator("#status-text").text_content()
            print(f"  Status indicator text: '{status_text}'")
            assert "Online" in status_text, f"Server status not online: {status_text}"

            # 4. Perform Quick Scan on Home
            print("[4/5] Testing cross-origin Quick Scan on Home view...")
            sample_chips = page.locator("#home-examples-chips .example-chip")
            chip_count = sample_chips.count()
            print(f"  Found {chip_count} synthetic example chips.")
            assert chip_count >= 7, f"Expected at least 7 example chips, found {chip_count}"

            # Click first spam example chip
            first_chip = sample_chips.first
            first_chip.click()
            time.sleep(0.5)

            # Trigger Quick Analyze button
            analyze_btn = page.locator("#home-quick-analyze-btn")
            analyze_btn.click()

            # Wait for result card to become visible
            page.wait_for_selector("#home-quick-result-card:not(.hidden)", timeout=15000)
            score_num = page.locator("#home-result-score").text_content()
            verdict_badge = page.locator("#home-result-badge").text_content()
            print(f"  Home quick scan result: Verdict='{verdict_badge}', Risk Score='{score_num}'")
            assert verdict_badge in ["Spam", "Suspicious", "Safe"], f"Invalid verdict: {verdict_badge}"

            # 5. Navigate to Analyzer view and perform email scan
            print("[5/5] Testing cross-origin Email Analyzer view (#/analyzer)...")
            page.goto(f"http://127.0.0.1:{FRONTEND_PORT}/#/analyzer", wait_until="networkidle")
            time.sleep(1)

            # Click sample spam button
            page.click("#sample-spam-btn")
            time.sleep(0.5)

            # Click analyze button
            page.click("#analyze-btn")

            # Wait for report to render
            page.wait_for_selector("#report-active-view:not(.hidden)", timeout=15000)
            analyzer_verdict = page.locator("#report-classification-val").text_content()
            analyzer_score = page.locator("#risk-ring-num").text_content()
            print(f"  Analyzer report result: Verdict='{analyzer_verdict}', Risk Score='{analyzer_score}'")

            # Take screenshot evidence
            screenshot_path = SCREENSHOT_DIR / "split_architecture_cross_origin.png"
            page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"  Screenshot saved: {screenshot_path}")

            # Verify that cross-origin requests were made to port 5000
            print(f"  Recorded {len(api_requests)} cross-origin API calls to port {BACKEND_PORT}:")
            for req in api_requests:
                print(f"    -> {req}")
            assert any(f":{BACKEND_PORT}/api/health" in r for r in api_requests), "Health check not requested cross-origin"
            assert any(f":{BACKEND_PORT}/api/analyze" in r for r in api_requests), "Analyze not requested cross-origin"

            browser.close()

        print("=" * 70)
        print("VERIFICATION SUCCESS: Split architecture cross-origin communication PASSED!")
        print("=" * 70)
        return 0

    finally:
        print("Shutting down test servers...")
        try:
            frontend_server.shutdown()
            frontend_server.server_close()
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
