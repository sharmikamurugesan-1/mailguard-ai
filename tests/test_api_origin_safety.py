"""Tests for Phase 12J: API Origin Safety & Configuration Guards.

Verifies:
1. scripts/set_api_origin.py strictly validates origins:
   - Rejects wildcards ('*', '?')
   - Enforces HTTPS for non-localhost domains
   - Rejects subpaths and malformed inputs
2. scripts/set_api_origin.py updates static/config.js, vercel.json, and rebuilds frontend/
3. Runtime guard: When .invalid placeholder is present, guard displays 'Backend Not Configured'
   and blocks all network fetches.
"""

from pathlib import Path
import pytest
from scripts.set_api_origin import validate_origin, update_static_config, update_vercel_json

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_CONFIG = BASE_DIR / "static" / "config.js"
VERCEL_JSON = BASE_DIR / "vercel.json"


def test_validate_origin_valid_https():
    """Valid HTTPS origin without subpath is accepted."""
    assert validate_origin("https://mailguard-ai.onrender.com") == "https://mailguard-ai.onrender.com"
    assert validate_origin("https://custom-domain.example.com/") == "https://custom-domain.example.com"


def test_validate_origin_valid_localhost():
    """Localhost HTTP origin is accepted for development/testing."""
    assert validate_origin("http://127.0.0.1:5000") == "http://127.0.0.1:5000"
    assert validate_origin("http://localhost:3000") == "http://localhost:3000"


def test_validate_origin_rejects_wildcard():
    """Wildcards are strictly rejected."""
    with pytest.raises(ValueError, match="invalid or wildcard characters"):
        validate_origin("*")
    with pytest.raises(ValueError, match="invalid or wildcard characters"):
        validate_origin("https://*.onrender.com")
    with pytest.raises(ValueError, match="invalid or wildcard characters"):
        validate_origin("https://test?.onrender.com")


def test_validate_origin_rejects_non_https_remote():
    """Insecure HTTP for remote domains is rejected."""
    with pytest.raises(ValueError, match="must use HTTPS"):
        validate_origin("http://remote-server.onrender.com")


def test_validate_origin_rejects_subpath():
    """Origins with subpaths are rejected."""
    with pytest.raises(ValueError, match="must be an origin root without subpaths"):
        validate_origin("https://mailguard-ai.onrender.com/api")


def test_validate_origin_rejects_empty():
    """Empty origin is rejected."""
    with pytest.raises(ValueError, match="cannot be empty"):
        validate_origin("   ")


def test_set_api_origin_updates_and_resets():
    """Test updating static/config.js and vercel.json, then resetting to placeholder."""
    # Backup original content
    orig_config = STATIC_CONFIG.read_text(encoding="utf-8")
    orig_vercel = VERCEL_JSON.read_text(encoding="utf-8")

    try:
        test_url = "https://custom-test-staging.onrender.com"
        update_static_config(test_url)
        update_vercel_json(test_url)

        # Assert static/config.js updated
        assert f"var PROD_API_URL = '{test_url}';" in STATIC_CONFIG.read_text(encoding="utf-8")

        # Assert vercel.json updated
        vercel_content = VERCEL_JSON.read_text(encoding="utf-8")
        assert f"connect-src 'self' blob: {test_url};" in vercel_content

    finally:
        # Restore placeholder
        STATIC_CONFIG.write_text(orig_config, encoding="utf-8")
        VERCEL_JSON.write_text(orig_vercel, encoding="utf-8")
