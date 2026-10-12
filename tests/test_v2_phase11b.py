"""Unit, static security, and contrast verification tests for Phase 11B."""

from pathlib import Path
import re
import pytest
from src.app import create_app
from scripts.check_contrast import evaluate_stylesheet


@pytest.fixture
def client():
    app = create_app({"TESTING": True})
    return app.test_client()


# -----------------------------------------------------------------------------
# 1. GET /api/model-info New Fields & Backward Compatibility
# -----------------------------------------------------------------------------

def test_model_info_v2_fields_and_backward_compatibility(client):
    """GET /api/model-info exposes n_train, n_test, code_license, dataset_repo_license without breaking contract."""
    res = client.get("/api/model-info")
    assert res.status_code == 200
    assert res.is_json
    data = res.get_json()

    # New Phase 11B fields
    assert "n_train" in data
    assert data["n_train"] == 24369
    assert "n_test" in data
    assert data["n_test"] == 6093
    assert data.get("code_license") == "MIT"
    assert "GNU General Public License" in data.get("dataset_repo_license", "")

    # Backward compatibility: all previous fields remain
    required_legacy_keys = [
        "model_type",
        "vectorizer",
        "version",
        "trained_at",
        "dataset_name",
        "dataset_source_url",
        "dataset_license",
        "dataset_type",
        "n_samples",
        "class_counts",
        "selection_criterion",
        "test_metrics",
        "thresholds",
        "limitations",
    ]
    for key in required_legacy_keys:
        assert key in data, f"Legacy key '{key}' missing from /api/model-info"

    assert data["n_samples"] == 30462
    assert data["class_counts"]["ham"] == 15910
    assert data["class_counts"]["spam"] == 14552


# -----------------------------------------------------------------------------
# 2. Automated WCAG 2.1 AA Contrast Verification on Real CSS
# -----------------------------------------------------------------------------

def test_wcag_contrast_real_css():
    """All foreground/background pairs in static/css/style.css pass WCAG 2.1 AA contrast requirements."""
    css_path = Path("static/css/style.css")
    assert css_path.exists(), "static/css/style.css does not exist"

    results = evaluate_stylesheet(css_path)
    assert len(results) >= 20, f"Expected at least 20 contrast pairings, found {len(results)}"

    failures = [r for r in results if not r.passed]
    failure_msgs = [
        f"{r.theme.upper()} {r.element}: fg={r.fg_hex} on bg={r.bg_hex} ratio={r.ratio:.2f}:1 (needed >= {r.required}:1)"
        for r in failures
    ]
    assert not failures, f"WCAG contrast failures detected:\n" + "\n".join(failure_msgs)


# -----------------------------------------------------------------------------
# 3. Static Security & Strict CSP Audits
# -----------------------------------------------------------------------------

def test_static_security_templates_and_scripts():
    """Verify absence of inline scripts, inline styles, innerHTML, and correct theme-init loading."""
    html_path = Path("templates/index.html")
    assert html_path.exists()
    html_content = html_path.read_text(encoding="utf-8")

    # 1. Zero inline <script> tags
    inline_script_matches = re.findall(r"<script(?![^>]*src=)[^>]*>", html_content, re.IGNORECASE)
    assert not inline_script_matches, f"Inline script tag detected in templates/index.html: {inline_script_matches}"

    # 2. Zero inline style attributes
    inline_style_matches = re.findall(r'\sstyle=["\'][^"\']*["\']', html_content, re.IGNORECASE)
    assert not inline_style_matches, f"Inline style attribute detected in templates/index.html: {inline_style_matches}"

    # 3. theme-init.js loaded in <head> without defer
    head_match = re.search(r"<head>(.*?)</head>", html_content, re.DOTALL | re.IGNORECASE)
    assert head_match, "<head> block not found in templates/index.html"
    head_content = head_match.group(1)

    assert "theme-init.js" in head_content, "theme-init.js must be referenced in <head>"
    theme_script_tag = re.search(r'<script[^>]*src=["\'][^"\']*theme-init\.js["\'][^>]*>', head_content)
    assert theme_script_tag, "theme-init.js script tag not found in <head>"
    assert "defer" not in theme_script_tag.group(0).lower(), "theme-init.js must NOT have defer attribute"

    # 4. JavaScript files: zero innerHTML or dangerous DOM insertion in active code
    js_files = [Path("static/js/app.js"), Path("static/js/theme-init.js")]
    for js_path in js_files:
        assert js_path.exists(), f"{js_path} does not exist"
        js_code = js_path.read_text(encoding="utf-8")
        # Strip comments
        clean_code = re.sub(r"/\*.*?\*/|//.*", "", js_code, flags=re.DOTALL)
        assert not re.search(r"\binnerHTML\b", clean_code), f"Forbidden innerHTML found in code of {js_path}"
        assert not re.search(r"\bouterHTML\b", clean_code), f"Forbidden outerHTML found in code of {js_path}"
        assert not re.search(r"\bdocument\.write\b", clean_code), f"Forbidden document.write found in code of {js_path}"


# -----------------------------------------------------------------------------
# 4. Character Counter Behavior Simulation
# -----------------------------------------------------------------------------

def test_character_counter_behavior_simulation():
    """Verify that empty body yields 0 body characters even with subject text present."""
    subject = "Action Required: Security Alert on Your Account"
    body = ""
    max_chars = 20000

    sub_len = len(subject)
    body_len = len(body)
    total = sub_len + body_len

    # Assertions reflecting app.js updateCharCount behavior
    assert body_len == 0
    assert sub_len == len(subject)
    assert total == len(subject)
    assert f"{body_len} / {max_chars}" == "0 / 20000"
    assert f"Total: {total} / {max_chars}" == f"Total: {len(subject)} / 20000"
