#!/usr/bin/env python3
"""Script to configure the backend API origin for MailGuard AI split deployment.

Phase 12J: Split-deploy hardening.
Updates the production API origin in:
1. static/config.js (PROD_API_URL)
2. vercel.json (CSP connect-src directive)
3. Regenerates frontend/ via scripts/build_frontend.py

Usage:
    python scripts/set_api_origin.py --origin https://mailguard-ai.onrender.com
"""

import argparse
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_JS_PATH = BASE_DIR / "static" / "config.js"
VERCEL_JSON_PATH = BASE_DIR / "vercel.json"


def validate_origin(origin: str) -> str:
    """Validate that the origin is a strict, secure HTTPS URL (or local HTTP) without wildcards."""
    origin = origin.strip().rstrip("/")
    if not origin:
        raise ValueError("Origin cannot be empty.")

    # Strict rejection of wildcards or regex patterns
    if any(char in origin for char in ["*", "?", "[", "]", "{", "}", "^", "$", "<", ">", '"', "'", "`"]):
        raise ValueError(f"Origin '{origin}' contains invalid or wildcard characters. Wildcards are strictly disallowed.")

    parsed = urlparse(origin)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"Origin '{origin}' is not a valid absolute URL (e.g., https://your-app.onrender.com).")

    if parsed.path and parsed.path != "/":
        raise ValueError(f"Origin '{origin}' must be an origin root without subpaths (found path '{parsed.path}').")

    # Enforce HTTPS unless localhost/127.0.0.1
    is_local = parsed.hostname in ("localhost", "127.0.0.1", "::1")
    if not is_local and parsed.scheme != "https":
        raise ValueError(f"Production origin must use HTTPS scheme (found '{parsed.scheme}://').")

    if is_local and parsed.scheme not in ("http", "https"):
        raise ValueError(f"Local origin must use HTTP or HTTPS (found '{parsed.scheme}://').")

    return origin


def update_static_config(origin: str) -> bool:
    """Update PROD_API_URL in static/config.js."""
    if not CONFIG_JS_PATH.exists():
        raise FileNotFoundError(f"Configuration file not found: {CONFIG_JS_PATH}")

    content = CONFIG_JS_PATH.read_text(encoding="utf-8")
    pattern = r"var PROD_API_URL = ['\"][^'\"]+['\"];"
    if not re.search(pattern, content):
        raise ValueError("Could not find 'var PROD_API_URL = ...' in static/config.js")

    new_content = re.sub(pattern, f"var PROD_API_URL = '{origin}';", content)
    CONFIG_JS_PATH.write_text(new_content, encoding="utf-8")
    print(f"  [OK] Updated static/config.js PROD_API_URL -> {origin}")
    return True


def update_vercel_json(origin: str) -> bool:
    """Update connect-src in vercel.json CSP header."""
    if not VERCEL_JSON_PATH.exists():
        raise FileNotFoundError(f"vercel.json not found: {VERCEL_JSON_PATH}")

    data = json.loads(VERCEL_JSON_PATH.read_text(encoding="utf-8"))
    updated = False

    for header_entry in data.get("headers", []):
        for h in header_entry.get("headers", []):
            if h.get("key") == "Content-Security-Policy":
                csp = h.get("value", "")
                # Replace connect-src 'self' blob: <origin>;
                csp_pattern = r"(connect-src\s+'self'\s+blob:)(?:\s+https?://[^\s;]+)?;"
                replacement = f"\\1 {origin};"
                new_csp = re.sub(csp_pattern, replacement, csp)
                if new_csp != csp:
                    h["value"] = new_csp
                    updated = True

    if not updated:
        raise ValueError("Could not locate or update Content-Security-Policy connect-src in vercel.json")

    VERCEL_JSON_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"  [OK] Updated vercel.json CSP connect-src -> {origin}")
    return True


def regenerate_frontend() -> None:
    """Regenerate static frontend export in frontend/."""
    sys.path.insert(0, str(BASE_DIR))
    from scripts.build_frontend import build_frontend
    res = build_frontend()
    if res != 0:
        raise RuntimeError(f"Frontend regeneration failed with exit code {res}")


def set_api_origin(origin: str) -> int:
    print("=" * 65)
    print("MailGuard AI - Configure API Origin (Phase 12J)")
    print("=" * 65)

    try:
        clean_origin = validate_origin(origin)
        print(f"Target Origin: {clean_origin}")

        update_static_config(clean_origin)
        update_vercel_json(clean_origin)

        print("\nRegenerating standalone static frontend export...")
        regenerate_frontend()

        print("=" * 65)
        print("API Origin successfully configured across static/config.js,")
        print("vercel.json, and frontend/!")
        print("=" * 65)
        return 0
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


def main():
    parser = argparse.ArgumentParser(description="Configure production API origin for split deployment.")
    parser.add_argument(
        "--origin",
        required=True,
        help="The full origin of the Render backend (e.g., https://mailguard-ai.onrender.com)",
    )
    args = parser.parse_args()
    sys.exit(set_api_origin(args.origin))


if __name__ == "__main__":
    main()
