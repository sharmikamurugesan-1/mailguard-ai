# MailGuard AI Verification Report (Quick)

- **Mode:** `--quick`
- **Timestamp:** 2026-10-11T10:36:40Z
- **Overall Result:** PASSED

### 1. Model Integrity Check: PASSED

### 2. Static Frontend Export
```
============================================================
MailGuard AI - Static Frontend Export (Phase 12I)
============================================================
Repository Root: C:\Users\LENOVO\.gemini\antigravity\scratch\mailguard-ai
Templates Directory: C:\Users\LENOVO\.gemini\antigravity\scratch\mailguard-ai\templates
Static Assets Directory: C:\Users\LENOVO\.gemini\antigravity\scratch\mailguard-ai\static
Target Output Directory: C:\Users\LENOVO\.gemini\antigravity\scratch\mailguard-ai\frontend
Cleaning existing output directory: C:\Users\LENOVO\.gemini\antigravity\scratch\mailguard-ai\frontend
  [FILE] static/config.js -> frontend/config.js (3,491 bytes)
  [DIR]  static/css -> frontend/css (1 files, 92,839 bytes)
  [DIR]  static/data -> frontend/data (1 files, 3,268 bytes)
  [FILE] static/favicon.ico -> frontend/favicon.ico (2,121 bytes)
  [FILE] static/favicon.svg -> frontend/favicon.svg (804 bytes)
  [DIR]  static/fonts -> frontend/fonts (3 files, 23,700 bytes)
  [DIR]  static/img -> frontend/img (1 files, 60,698 bytes)
  [DIR]  static/js -> frontend/js (2 files, 164,750 bytes)
  [DIR]  static/vendor -> frontend/vendor (8 files, 16,027,658 bytes)
  [HTML] templates/index.html -> frontend/index.html (128,955 bytes)
  [HTML] templates/404.html -> frontend/404.html (1,558 bytes)
  [HTML] templates/500.html -> frontend/500.html (1,554 bytes)
============================================================
Static frontend export SUCCESSFUL!
Total files in frontend/: 22
Total size: 16,511,396 bytes (15.75 MB)
============================================================

```

### 3. API & Security Tests
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\LENOVO\.gemini\antigravity\scratch\mailguard-ai\.venv\Scripts\python.exe
cachedir: .pytest_cache
hypothesis profile 'default'
rootdir: C:\Users\LENOVO\.gemini\antigravity\scratch\mailguard-ai
configfile: pytest.ini
plugins: hypothesis-6.168.5, platformdirs-4.13.0, cov-7.1.0
collecting ... collected 49 items

tests/test_api_origin_safety.py::test_validate_origin_valid_https PASSED [  2%]
tests/test_api_origin_safety.py::test_validate_origin_valid_localhost PASSED [  4%]
tests/test_api_origin_safety.py::test_validate_origin_rejects_wildcard PASSED [  6%]
tests/test_api_origin_safety.py::test_validate_origin_rejects_non_https_remote PASSED [  8%]
tests/test_api_origin_safety.py::test_validate_origin_rejects_subpath PASSED [ 10%]
tests/test_api_origin_safety.py::test_validate_origin_rejects_empty PASSED [ 12%]
tests/test_api_origin_safety.py::test_set_api_origin_updates_and_resets PASSED [ 14%]
tests/test_api.py::test_index_page_serves_html PASSED                    [ 16%]
tests/test_api.py::test_health_check_endpoint PASSED                     [ 18%]
tests/test_api.py::test_404_error_handler PASSED                         [ 20%]
tests/test_api.py::test_415_unsupported_media_type PASSED                [ 22%]
tests/test_api.py::test_413_payload_too_large_content_length PASSED      [ 24%]
tests/test_api.py::test_413_payload_too_large_character_limit PASSED     [ 26%]
tests/test_api.py::test_400_malformed_json PASSED                        [ 28%]
tests/test_api.py::test_400_missing_body PASSED                          [ 30%]
tests/test_api.py::test_400_empty_body PASSED                            [ 32%]
tests/test_api.py::test_400_invalid_types PASSED                         [ 34%]
tests/test_api.py::test_get_model_info PASSED                            [ 36%]
tests/test_api.py::test_predict_realistic_spam PASSED                    [ 38%]
tests/test_api.py::test_predict_realistic_ham PASSED                     [ 40%]
tests/test_api.py::test_predictor_singleton_load_once PASSED             [ 42%]
tests/test_api.py::test_security_headers_present PASSED                  [ 44%]
tests/test_api.py::test_api_endpoints_cache_control_no_store PASSED      [ 46%]
tests/test_api.py::test_405_method_not_allowed_get_predict PASSED        [ 48%]
tests/test_api.py::test_405_method_not_allowed_post_health PASSED        [ 51%]
tests/test_api.py::test_400_non_dict_payloads[payload0] PASSED           [ 53%]
tests/test_api.py::test_400_non_dict_payloads[payload1] PASSED           [ 55%]
tests/test_api.py::test_400_non_dict_payloads[12345] PASSED              [ 57%]
tests/test_api.py::test_400_non_dict_payloads[just a string] PASSED      [ 59%]
tests/test_api.py::test_400_non_dict_payloads[True] PASSED               [ 61%]
tests/test_api.py::test_exact_boundary_length_20000_vs_20001 PASSED      [ 63%]
tests/test_api.py::test_api_uncertain_prediction_flow PASSED             [ 65%]
tests/test_api.py::test_root_wsgi_app_import PASSED                      [ 67%]
tests/test_api.py::test_500_internal_server_error PASSED                 [ 69%]
tests/test_api.py::test_rate_limiting_enforced PASSED                    [ 71%]
tests/test_api.py::test_rate_limiting_ip_forwarded_for_separation PASSED [ 73%]
tests/test_api.py::test_html_404_error_page PASSED                       [ 75%]
tests/test_api.py::test_favicon_endpoints PASSED                         [ 77%]
tests/test_api.py::test_static_examples_dataset PASSED                   [ 79%]
tests/test_api.py::test_og_preview_image PASSED                          [ 81%]
tests/test_cors.py::test_allowed_origin_get_health PASSED                [ 83%]
tests/test_cors.py::test_allowed_vercel_origin_model_info PASSED         [ 85%]
tests/test_cors.py::test_blocked_origin_does_not_receive_cors PASSED     [ 87%]
tests/test_cors.py::test_preflight_options_allowed_origin PASSED         [ 89%]
tests/test_cors.py::test_preflight_options_blocked_origin PASSED         [ 91%]
tests/test_cors.py::test_bad_input_preserves_cors_headers PASSED         [ 93%]
tests/test_cors.py::test_unsupported_media_type_preserves_cors PASSED    [ 95%]
tests/test_cors.py::test_wildcard_asterisk_strictly_disallowed PASSED    [ 97%]
tests/test_cors.py::test_successful_post_cross_origin PASSED             [100%]

============================= 49 passed in 5.70s ==============================

```
