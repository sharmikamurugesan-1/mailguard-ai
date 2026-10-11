# MailGuard AI Verification Report (Full)

- **Mode:** `--full`
- **Timestamp:** 2026-10-11T11:03:09Z
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

### 3. Full Pytest Suite
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\LENOVO\.gemini\antigravity\scratch\mailguard-ai\.venv\Scripts\python.exe
cachedir: .pytest_cache
hypothesis profile 'default'
rootdir: C:\Users\LENOVO\.gemini\antigravity\scratch\mailguard-ai
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.15.1, hypothesis-6.168.5, platformdirs-4.13.0, cov-7.1.0
collecting ... collected 163 items

tests/test_analyze_api.py::test_analyze_plain_text_clean_ham PASSED      [  0%]
tests/test_analyze_api.py::test_analyze_raw_eml_with_headers PASSED      [  1%]
tests/test_analyze_api.py::test_analyze_spoofed_eml_triggers_indicators PASSED [  1%]
tests/test_analyze_api.py::test_analyze_urls_detected_and_flagged PASSED [  2%]
tests/test_analyze_api.py::test_options_scan_urls_disabled PASSED        [  3%]
tests/test_analyze_api.py::test_scan_urls_toggle_changes_analyze_output PASSED [  3%]
tests/test_analyze_api.py::test_options_analyze_headers_disabled PASSED  [  4%]
tests/test_analyze_api.py::test_analyze_headers_toggle_changes_analyze_output PASSED [  4%]
tests/test_analyze_api.py::test_options_sensitivity_profiles_affect_classification PASSED [  5%]
tests/test_analyze_api.py::test_unknown_sensitivity_defaults_to_medium PASSED [  6%]
tests/test_analyze_api.py::test_invariant_signals_never_flip_confident_ham PASSED [  6%]
tests/test_analyze_api.py::test_invariant_signals_never_flip_confident_spam PASSED [  7%]
tests/test_analyze_api.py::test_415_unsupported_media_type PASSED        [  7%]
tests/test_analyze_api.py::test_405_method_not_allowed PASSED            [  8%]
tests/test_analyze_api.py::test_400_malformed_json PASSED                [  9%]
tests/test_analyze_api.py::test_400_non_dict_json PASSED                 [  9%]
tests/test_analyze_api.py::test_400_invalid_field_types PASSED           [ 10%]
tests/test_analyze_api.py::test_400_empty_input PASSED                   [ 11%]
tests/test_analyze_api.py::test_413_text_payload_too_large PASSED        [ 11%]
tests/test_analyze_api.py::test_413_eml_payload_too_large PASSED         [ 12%]
tests/test_analyze_api.py::test_p95_latency_under_50ms PASSED            [ 12%]
tests/test_analyze_api.py::test_zero_user_text_logged_in_api PASSED      [ 13%]
tests/test_api.py::test_index_page_serves_html PASSED                    [ 14%]
tests/test_api.py::test_health_check_endpoint PASSED                     [ 14%]
tests/test_api.py::test_404_error_handler PASSED                         [ 15%]
tests/test_api.py::test_415_unsupported_media_type PASSED                [ 15%]
tests/test_api.py::test_413_payload_too_large_content_length PASSED      [ 16%]
tests/test_api.py::test_413_payload_too_large_character_limit PASSED     [ 17%]
tests/test_api.py::test_400_malformed_json PASSED                        [ 17%]
tests/test_api.py::test_400_missing_body PASSED                          [ 18%]
tests/test_api.py::test_400_empty_body PASSED                            [ 19%]
tests/test_api.py::test_400_invalid_types PASSED                         [ 19%]
tests/test_api.py::test_get_model_info PASSED                            [ 20%]
tests/test_api.py::test_predict_realistic_spam PASSED                    [ 20%]
tests/test_api.py::test_predict_realistic_ham PASSED                     [ 21%]
tests/test_api.py::test_predictor_singleton_load_once PASSED             [ 22%]
tests/test_api.py::test_security_headers_present PASSED                  [ 22%]
tests/test_api.py::test_api_endpoints_cache_control_no_store PASSED      [ 23%]
tests/test_api.py::test_405_method_not_allowed_get_predict PASSED        [ 23%]
tests/test_api.py::test_405_method_not_allowed_post_health PASSED        [ 24%]
tests/test_api.py::test_400_non_dict_payloads[payload0] PASSED           [ 25%]
tests/test_api.py::test_400_non_dict_payloads[payload1] PASSED           [ 25%]
tests/test_api.py::test_400_non_dict_payloads[12345] PASSED              [ 26%]
tests/test_api.py::test_400_non_dict_payloads[just a string] PASSED      [ 26%]
tests/test_api.py::test_400_non_dict_payloads[True] PASSED               [ 27%]
tests/test_api.py::test_exact_boundary_length_20000_vs_20001 PASSED      [ 28%]
tests/test_api.py::test_api_uncertain_prediction_flow PASSED             [ 28%]
tests/test_api.py::test_root_wsgi_app_import PASSED                      [ 29%]
tests/test_api.py::test_500_internal_server_error PASSED                 [ 30%]
tests/test_api.py::test_rate_limiting_enforced PASSED                    [ 30%]
tests/test_api.py::test_rate_limiting_ip_forwarded_for_separation PASSED [ 31%]
tests/test_api.py::test_html_404_error_page PASSED                       [ 31%]
tests/test_api.py::test_favicon_endpoints PASSED                         [ 32%]
tests/test_api.py::test_static_examples_dataset PASSED                   [ 33%]
tests/test_api.py::test_og_preview_image PASSED                          [ 33%]
tests/test_api_origin_safety.py::test_validate_origin_valid_https PASSED [ 34%]
tests/test_api_origin_safety.py::test_validate_origin_valid_localhost PASSED [ 34%]
tests/test_api_origin_safety.py::test_validate_origin_rejects_wildcard PASSED [ 35%]
tests/test_api_origin_safety.py::test_validate_origin_rejects_non_https_remote PASSED [ 36%]
tests/test_api_origin_safety.py::test_validate_origin_rejects_subpath PASSED [ 36%]
tests/test_api_origin_safety.py::test_validate_origin_rejects_empty PASSED [ 37%]
tests/test_api_origin_safety.py::test_set_api_origin_updates_and_resets PASSED [ 38%]
tests/test_cors.py::test_allowed_origin_get_health PASSED                [ 38%]
tests/test_cors.py::test_allowed_vercel_origin_model_info PASSED         [ 39%]
tests/test_cors.py::test_blocked_origin_does_not_receive_cors PASSED     [ 39%]
tests/test_cors.py::test_preflight_options_allowed_origin PASSED         [ 40%]
tests/test_cors.py::test_preflight_options_blocked_origin PASSED         [ 41%]
tests/test_cors.py::test_bad_input_preserves_cors_headers PASSED         [ 41%]
tests/test_cors.py::test_unsupported_media_type_preserves_cors PASSED    [ 42%]
tests/test_cors.py::test_wildcard_asterisk_strictly_disallowed PASSED    [ 42%]
tests/test_cors.py::test_successful_post_cross_origin PASSED             [ 43%]
tests/test_data.py::test_validate_columns_success PASSED                 [ 44%]
tests/test_data.py::test_validate_columns_failure PASSED                 [ 44%]
tests/test_data.py::test_clean_and_format_dataset_handling PASSED        [ 45%]
tests/test_data.py::test_invalid_label_rejection PASSED                  [ 46%]
tests/test_data.py::test_dataset_report_content_integrity PASSED         [ 46%]
tests/test_launch_robustness.py::test_oversize_body_predict_413 PASSED   [ 47%]
tests/test_launch_robustness.py::test_oversize_text_analyze_413 PASSED   [ 47%]
tests/test_launch_robustness.py::test_oversize_eml_analyze_413 PASSED    [ 48%]
tests/test_launch_robustness.py::test_max_content_length_flask_413 PASSED [ 49%]
tests/test_launch_robustness.py::test_malformed_json_syntax PASSED       [ 49%]
tests/test_launch_robustness.py::test_invalid_json_types PASSED          [ 50%]
tests/test_launch_robustness.py::test_empty_input_analyze_400 PASSED     [ 50%]
tests/test_launch_robustness.py::test_wrong_content_type_415 PASSED      [ 51%]
tests/test_launch_robustness.py::test_malformed_eml_binary_garbage PASSED [ 52%]
tests/test_launch_robustness.py::test_adversarial_redos_execution_time PASSED [ 52%]
tests/test_launch_robustness.py::test_parallel_requests_thread_safety_and_determinism PASSED [ 53%]
tests/test_launch_robustness.py::test_zero_input_text_logging_invariant PASSED [ 53%]
tests/test_launch_robustness.py::test_500_internal_error_zero_leakage PASSED [ 54%]
tests/test_launch_robustness.py::test_dynamic_rate_limiting_env_config PASSED [ 55%]
tests/test_model.py::test_model_artifact_exists_and_loads PASSED         [ 55%]
tests/test_model.py::test_realistic_spam_prediction PASSED               [ 56%]
tests/test_model.py::test_realistic_ham_prediction PASSED                [ 57%]
tests/test_model.py::test_fresh_process_load_works PASSED                [ 57%]
tests/test_model.py::test_metadata_l2_compliance PASSED                  [ 58%]
tests/test_model.py::test_version_mismatch_warning PASSED                [ 58%]
tests/test_model.py::test_sanity_samples_exact_behavior PASSED           [ 59%]
tests/test_model.py::test_missing_model_raises_clear_filenotfounderror PASSED [ 60%]
tests/test_model.py::test_model_sha256_integrity_success PASSED          [ 60%]
tests/test_model.py::test_model_sha256_integrity_tampering_fails_closed PASSED [ 61%]
tests/test_preprocessing.py::test_empty_and_null_inputs PASSED           [ 61%]
tests/test_preprocessing.py::test_unicode_normalization PASSED           [ 62%]
tests/test_preprocessing.py::test_html_like_text PASSED                  [ 63%]
tests/test_preprocessing.py::test_very_long_text PASSED                  [ 63%]
tests/test_preprocessing.py::test_token_normalizations PASSED            [ 64%]
tests/test_preprocessing.py::test_email_cleaner_transformer PASSED       [ 65%]
tests/test_reliability.py::test_injected_probabilities_uncertain_band PASSED [ 65%]
tests/test_reliability.py::test_injected_probabilities_outside_band PASSED [ 66%]
tests/test_reliability.py::test_no_unsafe_terminology PASSED             [ 66%]
tests/test_reliability.py::test_warning_code_near_decision_boundary PASSED [ 67%]
tests/test_reliability.py::test_warning_code_short_input PASSED          [ 68%]
tests/test_reliability.py::test_warning_code_low_vocab_coverage PASSED   [ 68%]
tests/test_reliability.py::test_warning_code_non_english PASSED          [ 69%]
tests/test_reliability.py::test_dataset_age_notice_is_persistent PASSED  [ 69%]
tests/test_reliability.py::test_reliability_levels PASSED                [ 70%]
tests/test_reliability.py::test_thresholds_change_with_env_vars PASSED   [ 71%]
tests/test_robustness.py::test_adversarial_and_unusual_inputs[<script>alert('xss')</script>-<img src=x onerror=alert(1)> Click here for free money] PASSED [ 71%]
tests/test_robustness.py::test_adversarial_and_unusual_inputs[SELECT * FROM emails WHERE 1=1;-DROP TABLE users; -- malicious payload injection test] PASSED [ 72%]
tests/test_robustness.py::test_adversarial_and_unusual_inputs[Null byte test\x00injection-Testing embedded \x00 null bytes in message text] PASSED [ 73%]
tests/test_robustness.py::test_adversarial_and_unusual_inputs[Unicode & CJK: \u3053\u3093\u306b\u3061\u306f-\u8fd9\u662f\u5305\u542b\u4e2d\u6587\u5b57\u7b26\u7684\u6d4b\u8bd5\u90ae\u4ef6\u3002Please review this document.] PASSED [ 73%]
tests/test_robustness.py::test_adversarial_and_unusual_inputs[Emojis: \U0001f680\U0001f525\U0001f4b0 Claim now!-Congratulations \U0001f389 You won 1,000,000 USD! \U0001f381 Claim immediately \U0001f4b8] PASSED [ 74%]
tests/test_robustness.py::test_adversarial_and_unusual_inputs[VeryLongContinuousWord-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA please review] PASSED [ 74%]
tests/test_robustness.py::test_adversarial_and_unusual_inputs[Whitespace only subject-   Valid body with meaningful words about quarterly budget   ] PASSED [ 75%]
tests/test_robustness.py::test_adversarial_and_unusual_inputs[-Body only without subject line provided] PASSED [ 76%]
tests/test_robustness.py::test_prediction_determinism PASSED             [ 76%]
tests/test_robustness.py::test_prediction_schema_and_types PASSED        [ 77%]
tests/test_robustness.py::test_zero_path_and_stack_trace_leaks PASSED    [ 77%]
tests/test_robustness.py::test_startup_no_raw_data_read_or_training PASSED [ 78%]
tests/test_robustness.py::test_privacy_zero_user_text_logged PASSED      [ 79%]
tests/test_robustness.py::test_frontend_static_security_and_integrity PASSED [ 79%]
tests/test_robustness.py::test_concurrency_smoke_test PASSED             [ 80%]
tests/test_robustness.py::test_prediction_latency_benchmark PASSED       [ 80%]
tests/test_signals.py::test_url_shortener_detection PASSED               [ 81%]
tests/test_signals.py::test_url_ip_host_detection PASSED                 [ 82%]
tests/test_signals.py::test_url_punycode_detection PASSED                [ 82%]
tests/test_signals.py::test_url_suspicious_tld_detection PASSED          [ 83%]
tests/test_signals.py::test_link_text_vs_href_mismatch PASSED            [ 84%]
tests/test_signals.py::test_clean_benign_urls PASSED                     [ 84%]
tests/test_signals.py::test_parse_clean_eml PASSED                       [ 85%]
tests/test_signals.py::test_parse_spoofed_eml_with_mismatch_and_spf_fail PASSED [ 85%]
tests/test_signals.py::test_parse_multipart_eml PASSED                   [ 86%]
tests/test_signals.py::test_empty_and_whitespace_inputs PASSED           [ 87%]
tests/test_signals.py::test_huge_input_handling PASSED                   [ 87%]
tests/test_signals.py::test_malformed_eml_does_not_crash PASSED          [ 88%]
tests/test_signals.py::test_unicode_and_encoded_words_eml PASSED         [ 88%]
tests/test_signals.py::test_risk_score_base_calculation PASSED           [ 89%]
tests/test_signals.py::test_heuristic_bump_and_capping PASSED            [ 90%]
tests/test_signals.py::test_invariant_signals_never_flip_confident_ham PASSED [ 90%]
tests/test_signals.py::test_invariant_signals_never_flip_confident_spam PASSED [ 91%]
tests/test_signals.py::test_sensitivity_profiles PASSED                  [ 92%]
tests/test_signals.py::test_key_findings_generation PASSED               [ 92%]
tests/test_signals.py::test_hypothesis_fuzz_extract_urls PASSED          [ 93%]
tests/test_signals.py::test_hypothesis_fuzz_parse_eml PASSED             [ 93%]
tests/test_signals.py::test_hypothesis_fuzz_compute_risk_score PASSED    [ 94%]
tests/test_signals.py::test_zero_user_text_logging PASSED                [ 95%]
tests/test_v2_phase11b.py::test_model_info_v2_fields_and_backward_compatibility PASSED [ 95%]
tests/test_v2_phase11b.py::test_wcag_contrast_real_css PASSED            [ 96%]
tests/test_v2_phase11b.py::test_static_security_templates_and_scripts PASSED [ 96%]
tests/test_v2_phase11b.py::test_character_counter_behavior_simulation PASSED [ 97%]
tests/test_v2_phase11c.py::test_is_stopword_term_helper PASSED           [ 98%]
tests/test_v2_phase11c.py::test_top_tokens_schema_and_types PASSED       [ 98%]
tests/test_v2_phase11c.py::test_filter_stopwords_toggle_behavior PASSED  [ 99%]
tests/test_v2_phase11c.py::test_genuine_borderline_email_classification PASSED [100%]

============================ 163 passed in 13.68s =============================

```

### 4. Split Architecture Verification
```
===========================================================================
PHASE 12J: SPLIT DEPLOYMENT PLAYWRIGHT VERIFICATION
Backend API:   http://127.0.0.1:5000 (Simulating Render)
Frontend Host: http://127.0.0.1:3000 (Simulating Vercel via serve_with_vercel_json)
===========================================================================
[1/10] Starting backend Flask server on port 5000...
[2/10] Starting Vercel emulator static server on port 3000...

--- TEST 1: Static Asset Resolution & Vercel Headers ---
  [PASS] /config.js served directly as application/javascript.
  [PASS] /data/examples.json served directly with 7 items.
  [PASS] /vendor/tesseract/tesseract.min.js served directly.
  [PASS] /vendor/tesseract/eng.traineddata.gz served with Content-Encoding: gzip.
  [PASS] Non-existent route falls back to SPA index.html with Vercel headers.

--- TEST 2: Runtime Guard with Unconfigured .invalid Origin ---
  Status indicator text: 'Backend Not Configured'
  Configuration notice on attempt: 'Backend not configured: Production API origin has not been set (REPLACE-WITH-RENDER-URL.invalid). Run scripts/set_api_origin.py --origin https://<your-render-url>'
  API requests made while unconfigured: 0
  [PASS] Runtime guard successfully prevented network requests and alerted user.

--- Configuring Origin via scripts/set_api_origin.py ---
=================================================================
MailGuard AI - Configure API Origin (Phase 12J)
=================================================================
Target Origin: http://127.0.0.1:5000
  [OK] Updated static/config.js PROD_API_URL -> http://127.0.0.1:5000
  [OK] Updated vercel.json CSP connect-src -> http://127.0.0.1:5000

Regenerating standalone static frontend export...
============================================================
MailGuard AI - Static Frontend Export (Phase 12I)
============================================================
Repository Root: C:\Users\LENOVO\.gemini\antigravity\scratch\mailguard-ai
Templates Directory: C:\Users\LENOVO\.gemini\antigravity\scratch\mailguard-ai\templates
Static Assets Directory: C:\Users\LENOVO\.gemini\antigravity\scratch\mailguard-ai\static
Target Output Directory: C:\Users\LENOVO\.gemini\antigravity\scratch\mailguard-ai\frontend
Cleaning existing output directory: C:\Users\LENOVO\.gemini\antigravity\scratch\mailguard-ai\frontend
  [FILE] static/config.js -> frontend/config.js (3,473 bytes)
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
Total size: 16,511,378 bytes (15.75 MB)
============================================================
=================================================================
API Origin successfully configured across static/config.js,
vercel.json, and frontend/!
=================================================================

--- TEST 3: Configured Home View & Deterministic Quick Scan ---
  Server status text: 'Server Online'
  Active window.API_BASE_URL: 'http://127.0.0.1:5000'
  Home quick scan result: Verdict='Spam', Risk Score='99'
  [PASS] Deterministic Home quick scan verified (Verdict=Spam, Score=99).

--- TEST 4: Configured Analyzer View & Deterministic Deep Scan ---
  Analyzer report result: Verdict='Spam', Risk Score='99.3'
  [PASS] Deterministic Analyzer scan verified (Verdict=Spam, Score=99.3).
  Saved screenshot: C:\Users\LENOVO\.gemini\antigravity\scratch\mailguard-ai\docs\screenshots\v2\split_architecture_cross_origin.png

--- TEST 5: Cold-Start Waking Banner & Error Handling ---
  Testing 5a: Simulating cold-start delay (>3s in-flight)...
  Waking banner visibility at t=3.3s: True
  Waking banner text: 'Waking up the server, this can take up to a minute on the free host'
  Saved screenshot: C:\Users\LENOVO\.gemini\antigravity\scratch\mailguard-ai\docs\screenshots\v2\split_architecture_cold_start.png
  [PASS] Cold-start waking banner appeared at 3s and dismissed cleanly after response.
  Testing 5b: 503 Service Unavailable handling...
  [CONSOLE ERROR] Failed to load resource: the server responded with a status of 503 (Service Unavailable)
  503 response error display: 'Server temporarily unavailable (503). The backend may be booting up or unreachable. Please retry in a moment.'
  [PASS] 503 response handled gracefully.
  Testing 5c: Network drop / connection abort handling...
  [CONSOLE ERROR] Failed to load resource: net::ERR_FAILED
  [CONSOLE ERROR] Failed to load resource: net::ERR_FAILED
  Network failure error display: 'Network error: Unable to reach the backend API. The server may be asleep or unreachable. Please click retry.'
  [PASS] Connection abort handled gracefully without uncaught exceptions.

--- TEST 6: OCR & QR Analysis in Split Mode (Vercel Headers) ---
  Testing Fixture 1: Email screenshot Web Worker OCR...
  Fixture 1 OCR (1.69s) -> Verdict='Spam', Score='99.6 / 100'
  Extracted text snippet: 'Security Alert - Action Required

URGENT NOTICE: Your account access has been re...'
  Saved screenshot: C:\Users\LENOVO\.gemini\antigravity\scratch\mailguard-ai\docs\screenshots\v2\split_architecture_ocr.png
  [PASS] Fixture 1 processed via Web Worker OCR under strict Vercel CSP.
  Testing Fixture 2: Phishing QR Code analysis...
  Fixture 2 QR -> Content='http://phishing-portal.test/steal-credentials', Verdict='Spam'
  [PASS] Fixture 2 decoded via client-side jsQR and flagged as phishing threat.
  Testing Fixture 3: Benign clean photo (zero text / zero QR)...
  Fixture 3 Clean -> Verdict='Safe', Risk='0.0 / 100'
  [PASS] Fixture 3 yields clean Safe verdict.

--- TEST 7: Zero CSP Violations & Zero Console Errors Audit ---
  Recorded CSP violations: 0
  Recorded console errors: 0
  [PASS] Strict CSP Level 3 enforced: ZERO violations and ZERO console errors.

--- TEST 8: Axe-core Accessibility Audit Across Routes ---
  Route #/home             -> 1 total violations, 0 critical/serious
  Route #/analyzer         -> 0 total violations, 0 critical/serious
  Route #/image-analysis   -> 1 total violations, 0 critical/serious
  Route #/dashboard        -> 0 total violations, 0 critical/serious
  Route #/features         -> 0 total violations, 0 critical/serious
  Route #/privacy          -> 0 total violations, 0 critical/serious
  [PASS] Axe accessibility audit passed on all routes (0 critical/serious).

===========================================================================
PHASE 12J: ALL SPLIT DEPLOYMENT VERIFICATIONS PASSED 100%!
===========================================================================

Restoring placeholder origin and cleaning up...
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
