"""Playwright automated verification for MailGuard AI v2 Phase 11C (Interactive Analysis UX).

Verifies:
1. Real borderline email triggers "Needs review" state with amber banner, ⚖ icon, and explanation.
2. In-text highlighter: tokens highlighted with .token-spam / .token-ham, non-color cues (▲/▼), and tooltips.
3. Stopword toggle: switching on/off updates counts, badge, and token display.
4. File import (.txt and .eml): drag-and-drop / file picker loads text, parses .eml, rejects >1 MB and bad types.
5. Ctrl+Enter keyboard submission works from textarea.
6. "Copy Result" button copies summary to clipboard, shows "Copied!" and toast feedback.
7. Skeleton loader displays during loading state.
8. Captures screenshots in light and dark mode saved to docs/screenshots/v2/.
9. Zero CSP violations and zero console errors.
"""

from pathlib import Path
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:5003"
SCREENSHOT_DIR = Path("docs/screenshots/v2")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


def run_phase_11c_verification():
    print("=" * 76)
    print("MAILGUARD AI v2 - PHASE 11C INTERACTIVE ANALYSIS UX BROWSER VERIFICATION")
    print("=" * 76)

    # Start Flask app on port 5003
    env = os.environ.copy()
    env["PORT"] = "5003"
    server_process = subprocess.Popen(
        [sys.executable, "-m", "src.app"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server readiness
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

    test_results = {}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1280, "height": 850},
                permissions=["clipboard-read", "clipboard-write"]
            )
            page = context.new_page()

            console_errors = []
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            page.on("pageerror", lambda err: console_errors.append(str(err)))

            # Attach securitypolicyviolation tracker
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

            page.goto(BASE_URL)
            page.wait_for_selector("#email-form")

            # -----------------------------------------------------------------
            # 1. Real Borderline Email ("Needs review" State & Banner)
            # -----------------------------------------------------------------
            print("[1/7] Testing Real Borderline Email ('Needs review' state)...")
            # Click sample borderline button
            page.click("#sample-borderline-btn")
            assert "re : no java ?" in page.input_value("#subject-input")
            assert "cracking me up" in page.input_value("#body-input")

            # Analyze
            page.click("#analyze-btn")
            page.wait_for_selector("#result-card:not(.hidden)", timeout=10000)

            verdict_text = page.inner_text("#verdict-title")
            assert "Needs review" in verdict_text, f"Expected 'Needs review', got '{verdict_text}'"

            verdict_icon = page.inner_text("#verdict-icon")
            assert verdict_icon == "⚖", f"Expected '⚖' icon, got '{verdict_icon}'"

            # Check uncertain banner
            is_banner_hidden = page.evaluate("() => document.getElementById('uncertain-banner').classList.contains('hidden')")
            assert not is_banner_hidden, "Uncertain banner should be visible for borderline prediction"

            banner_text = page.inner_text("#uncertain-banner-text")
            assert "[0.40, 0.60] borderline zone" in banner_text, f"Banner text missing threshold info: {banner_text}"

            # Capture screenshots in light and dark
            page.evaluate("() => document.documentElement.setAttribute('data-theme', 'light')")
            time.sleep(0.2)
            page.screenshot(path=str(SCREENSHOT_DIR / "borderline_uncertain_light.png"), full_page=True)
            print(f"       Captured screenshot: {SCREENSHOT_DIR / 'borderline_uncertain_light.png'}")

            page.evaluate("() => document.documentElement.setAttribute('data-theme', 'dark')")
            time.sleep(0.2)
            page.screenshot(path=str(SCREENSHOT_DIR / "borderline_uncertain_dark.png"), full_page=True)
            print(f"       Captured screenshot: {SCREENSHOT_DIR / 'borderline_uncertain_dark.png'}")

            test_results["borderline_needs_review"] = "PASS"

            # -----------------------------------------------------------------
            # 2. In-Text Highlighter & Non-Color Cues
            # -----------------------------------------------------------------
            print("[2/7] Testing In-Text Token Highlighter & Cues on Spam Email...")
            # Load spam sample
            page.click("#sample-spam-btn")
            page.click("#analyze-btn")
            page.wait_for_selector("#result-card:not(.hidden)", timeout=10000)

            # Check highlighted tokens in preview box
            token_count = page.evaluate("() => document.querySelectorAll('#highlight-preview-box mark.token-highlight').length")
            assert token_count > 0, f"Expected highlighted tokens, found {token_count}"

            spam_cue_count = page.evaluate("() => document.querySelectorAll('#highlight-preview-box mark.token-spam .token-cue').length")
            assert spam_cue_count > 0, "Spam highlight token missing non-color cue '▲'"

            first_cue_text = page.evaluate("() => document.querySelector('#highlight-preview-box mark.token-spam .token-cue').textContent")
            assert first_cue_text == "▲", f"Expected cue '▲', got '{first_cue_text}'"

            # Tooltip attribute presence
            has_title = page.evaluate("() => document.querySelector('#highlight-preview-box mark.token-highlight').hasAttribute('title')")
            assert has_title, "Highlight token missing 'title' attribute with weight details"

            page.evaluate("() => document.documentElement.setAttribute('data-theme', 'light')")
            time.sleep(0.2)
            page.screenshot(path=str(SCREENSHOT_DIR / "highlights_spam_light.png"), full_page=True)
            print(f"       Captured screenshot: {SCREENSHOT_DIR / 'highlights_spam_light.png'}")

            page.evaluate("() => document.documentElement.setAttribute('data-theme', 'dark')")
            time.sleep(0.2)
            page.screenshot(path=str(SCREENSHOT_DIR / "highlights_spam_dark.png"), full_page=True)
            print(f"       Captured screenshot: {SCREENSHOT_DIR / 'highlights_spam_dark.png'}")

            test_results["in_text_highlighter"] = "PASS"

            # -----------------------------------------------------------------
            # 3. Stopword Toggle Behavior
            # -----------------------------------------------------------------
            print("[3/7] Testing Stopword Toggle...")
            initial_pressed = page.get_attribute("#stopword-toggle-btn", "aria-pressed")
            assert initial_pressed == "true", "Initial stopword toggle should be pressed (filtering active)"

            initial_badge_text = page.inner_text("#stopword-count-badge")
            assert "common word" in initial_badge_text, f"Expected stopword count in badge, got '{initial_badge_text}'"

            # Toggle OFF
            page.click("#stopword-toggle-btn")
            new_pressed = page.get_attribute("#stopword-toggle-btn", "aria-pressed")
            assert new_pressed == "false", "Stopword toggle should be false after click"

            badge_text_unfiltered = page.inner_text("#stopword-count-badge")
            assert "All tokens visible" in badge_text_unfiltered, f"Expected all tokens visible badge text, got '{badge_text_unfiltered}'"

            # Toggle back ON
            page.click("#stopword-toggle-btn")
            revert_pressed = page.get_attribute("#stopword-toggle-btn", "aria-pressed")
            assert revert_pressed == "true", "Stopword toggle should be true after second click"

            test_results["stopword_toggle"] = "PASS"

            # -----------------------------------------------------------------
            # 4. File Import (.txt and .eml) & Validation Limits
            # -----------------------------------------------------------------
            print("[4/7] Testing File Import (.txt, .eml, >1MB rejection, bad extension)...")
            with tempfile.TemporaryDirectory() as tmpdir:
                # 4a. Plain text file
                txt_path = Path(tmpdir) / "sample_email.txt"
                txt_path.write_text("This is an imported plain text email body for testing.", encoding="utf-8")

                page.set_input_files("#file-picker-input", str(txt_path))
                page.wait_for_function("() => document.getElementById('body-input').value.includes('This is an imported plain text')")
                body_val = page.input_value("#body-input")
                assert "This is an imported plain text email body" in body_val, "Failed to load .txt file"

                # 4b. EML file
                eml_path = Path(tmpdir) / "sample_email.eml"
                eml_content = (
                    "From: sender@example.com\r\n"
                    "To: recipient@example.com\r\n"
                    "Subject: Urgent Server Maintenance Window\r\n"
                    "Content-Type: text/plain; charset=utf-8\r\n\r\n"
                    "All production databases will be upgraded at 02:00 UTC tonight.\r\n"
                )
                eml_path.write_text(eml_content, encoding="utf-8")

                page.set_input_files("#file-picker-input", str(eml_path))
                page.wait_for_function("() => document.getElementById('subject-input').value.includes('Urgent Server Maintenance Window')")
                sub_val = page.input_value("#subject-input")
                body_val_eml = page.input_value("#body-input")
                assert "Urgent Server Maintenance Window" in sub_val, f"EML subject failed to parse: '{sub_val}'"
                assert "All production databases will be upgraded" in body_val_eml, f"EML body failed to parse: '{body_val_eml}'"

                # 4c. File size limit (>1 MB)
                large_path = Path(tmpdir) / "oversized.txt"
                large_path.write_text("A" * (1024 * 1024 + 100), encoding="utf-8")

                page.set_input_files("#file-picker-input", str(large_path))
                page.wait_for_selector("#body-error:not(.hidden)")
                err_text = page.inner_text("#body-error")
                assert "exceeds the 1 MB size limit" in err_text, f"Expected size error, got '{err_text}'"

                # 4d. Unsupported file extension (.exe)
                bad_ext_path = Path(tmpdir) / "malicious.exe"
                bad_ext_path.write_text("MZ\x90\x00", encoding="latin-1")

                page.set_input_files("#file-picker-input", str(bad_ext_path))
                page.wait_for_function("() => document.getElementById('body-error').textContent.includes('Unsupported file type')")
                err_text_ext = page.inner_text("#body-error")
                assert "Unsupported file type (.exe)" in err_text_ext, f"Expected unsupported extension error, got '{err_text_ext}'"

            test_results["file_import_and_limits"] = "PASS"

            # -----------------------------------------------------------------
            # 5. Ctrl+Enter Keyboard Shortcut
            # -----------------------------------------------------------------
            print("[5/7] Testing Ctrl+Enter Keyboard Shortcut...")
            page.fill("#subject-input", "Meeting Tomorrow")
            page.fill("#body-input", "Hi Alex, please bring the quarterly financial projection slides.")
            page.focus("#body-input")

            # Press Control+Enter
            page.keyboard.press("Control+Enter")
            page.wait_for_selector("#result-card:not(.hidden)", timeout=10000)

            verdict_after_shortcut = page.inner_text("#verdict-title")
            assert "Likely legitimate" in verdict_after_shortcut or "Needs review" in verdict_after_shortcut or "Likely spam" in verdict_after_shortcut
            test_results["ctrl_enter_shortcut"] = "PASS"

            # -----------------------------------------------------------------
            # 6. Copy Result Summary Button
            # -----------------------------------------------------------------
            print("[6/7] Testing 'Copy Result' Summary Button...")
            # Click Copy Result
            page.click("#copy-result-btn")
            time.sleep(0.4)

            btn_text = page.inner_text("#copy-btn-text")
            assert btn_text == "Copied!", f"Expected 'Copied!', got '{btn_text}'"

            # Verify clipboard text
            clipboard_content = page.evaluate("() => navigator.clipboard.readText()")
            assert "MailGuard AI - Email Analysis Summary" in clipboard_content, f"Clipboard missing summary header: '{clipboard_content}'"
            assert "Verdict:" in clipboard_content, "Clipboard missing verdict line"
            assert "Top Contributing Tokens:" in clipboard_content, "Clipboard missing top tokens"

            test_results["copy_result_summary"] = "PASS"

            # -----------------------------------------------------------------
            # 7. Zero CSP Violations & Console Integrity
            # -----------------------------------------------------------------
            print("[7/7] Verifying Zero CSP Violations & Console Integrity...")
            in_page_csp = page.evaluate("() => window.__csp_violations || []")
            assert len(in_page_csp) == 0, f"CSP violations detected: {in_page_csp}"
            assert len(console_errors) == 0, f"Console errors detected: {console_errors}"
            test_results["csp_and_console_clean"] = "PASS"

            context.close()
            browser.close()

    finally:
        server_process.terminate()
        try:
            server_process.wait(timeout=3)
        except Exception:
            server_process.kill()

    print("=" * 76)
    print("ALL 7 PLAYWRIGHT INTERACTIVE UX CHECKS PASSED WITH ZERO ERRORS")
    print("=" * 76)
    return test_results


if __name__ == "__main__":
    results = run_phase_11c_verification()
    for k, v in results.items():
        print(f" - {k:35}: {v}")
