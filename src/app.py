"""Flask application factory and REST endpoints for MailGuard AI.

Phase 6: Prediction API & Reliability
- App factory pattern: create_app()
- Single model loading at initialization (load ONCE, zero training on server start).
- Standardized error JSON shape across all errors: {"error": {"code": str, "message": str}}
- Strict input validation on POST /api/predict:
  - 415 Unsupported Media Type for non-JSON headers
  - 400 Bad Request for malformed JSON, missing/empty body, or invalid types
  - 413 Payload Too Large for inputs exceeding MAX_INPUT_CHARS or MAX_CONTENT_LENGTH
  - Zero filesystem path or stack trace leakage
- Endpoints:
  - GET  /api/health
  - GET  /api/model-info
  - POST /api/predict
"""

import hashlib
import json
import logging
import os
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.exceptions import (
    BadRequest,
    HTTPException,
    MethodNotAllowed,
    NotFound,
    RequestEntityTooLarge,
    UnsupportedMediaType,
)
from werkzeug.middleware.proxy_fix import ProxyFix

from src import config
from src.signals import (
    compute_risk_score,
    extract_and_check_urls,
    generate_key_findings,
    parse_eml_message,
)

try:
    from src.predictor import get_predictor
except Exception as _pred_err:
    get_predictor = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

logger = logging.getLogger("MailGuard-API")


def get_allowed_origins(app: Flask) -> set:
    """Extract and normalize allowed CORS origins from config or environment.

    Security: Wildcard '*' is strictly prohibited to ensure only explicit,
    trusted origins receive Access-Control-Allow-Origin headers.
    """
    raw = app.config.get("CORS_ALLOWED_ORIGINS") or os.getenv("CORS_ALLOWED_ORIGINS", "")
    if isinstance(raw, (list, set, tuple)):
        items = raw
    else:
        items = str(raw).split(",")

    allowed = set()
    for item in items:
        cleaned = item.strip().rstrip("/")
        if cleaned and cleaned != "*":
            allowed.add(cleaned)
    return allowed


def get_rate_limit_analyze() -> str:
    """Resolve dynamic rate limit string for /api/analyze."""
    override = os.getenv("RATELIMIT_ANALYZE_LIMIT")
    if override:
        return override
    per_min = os.getenv("RATELIMIT_ANALYZE_PER_MINUTE", str(config.RATELIMIT_ANALYZE_PER_MINUTE))
    return f"{per_min} per minute"


def get_rate_limit_predict() -> str:
    """Resolve dynamic rate limit string for /api/predict."""
    override = os.getenv("RATELIMIT_PREDICT_LIMIT")
    if override:
        return override
    per_min = os.getenv("RATELIMIT_PREDICT_PER_MINUTE", str(config.RATELIMIT_PREDICT_PER_MINUTE))
    return f"{per_min} per minute"


def get_rate_limit_model_info() -> str:
    """Resolve dynamic rate limit string for /api/model-info."""
    override = os.getenv("RATELIMIT_MODEL_INFO_LIMIT")
    if override:
        return override
    per_min = os.getenv("RATELIMIT_MODEL_INFO_PER_MINUTE", str(config.RATELIMIT_MODEL_INFO_PER_MINUTE))
    return f"{per_min} per minute"


def create_app(test_config: Optional[Dict[str, Any]] = None) -> Flask:
    """Create and configure Flask application instance."""
    app = Flask(
        __name__,
        template_folder=str(config.TEMPLATES_DIR),
        static_folder=str(config.STATIC_DIR),
        static_url_path="",
    )

    # Configuration
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH
    app.config["JSON_SORT_KEYS"] = False

    if test_config:
        app.config.update(test_config)

    # Apply Werkzeug ProxyFix to extract genuine client IP behind reverse proxies (Render)
    # x_for=1 trusts one hop of X-Forwarded-For to populate request.remote_addr.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)

    # Rate Limiting (Flask-Limiter)
    # Note: In-memory storage ("memory://") tracks limits per Gunicorn worker process;
    # counters are worker-local and reset on server process restart or dyno cycling.
    is_testing = app.config.get("TESTING", False)
    ratelimit_enabled = app.config.get("RATELIMIT_ENABLED", not is_testing)
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=[],
        enabled=ratelimit_enabled,
        storage_uri="memory://",
    )
    app.limiter = limiter

    # Eagerly preload and verify model integrity at startup during production (Gunicorn --preload)
    if not is_testing and app.config.get("PRELOAD_MODEL", True):
        try:
            if get_predictor is not None:
                get_predictor()
        except Exception as _preload_err:
            logger.critical(f"Fatal: Failed to preload and verify model integrity on startup: {_preload_err}")
            raise

    # CORS Preflight Handler (Intercept OPTIONS on /api/*)
    @app.before_request
    def handle_cors_preflight():
        if request.method == "OPTIONS" and request.path.startswith("/api"):
            origin = request.headers.get("Origin")
            allowed = get_allowed_origins(app)
            res = app.make_response(("", 204))
            if origin and origin.rstrip("/") in allowed:
                res.headers["Access-Control-Allow-Origin"] = origin
                res.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
                res.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
                res.headers["Access-Control-Max-Age"] = "86400"
                res.headers["Vary"] = "Origin"
            return res

    # Security Headers Hook
    @app.after_request
    def set_security_headers(response):
        """Inject strict security and privacy headers into every response.

        CSP Rationale (Phase 12F Image OCR & Threat Analysis):
        - worker-src 'self' blob: allows self-hosted Tesseract worker and Blob-URL worker initialization.
        - script-src 'self' 'wasm-unsafe-eval': W3C CSP Level 3 standard allowing WebAssembly compilation
          while strictly prohibiting JavaScript 'eval' or inline scripts.
        - connect-src 'self' blob: allows fetching self-hosted wasm cores and traineddata.
        - img-src 'self' data: blob: allows previewing dropped image files via URL.createObjectURL.
        - Zero external CDNs allowed; zero 'unsafe-inline' or 'unsafe-eval' permitted.
        """
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "style-src 'self'; "
            "script-src 'self' 'wasm-unsafe-eval'; "
            "worker-src 'self' blob:; "
            "connect-src 'self' blob:; "
            "img-src 'self' data: blob:; "
            "font-src 'self'; "
            "frame-ancestors 'none';"
        )

        # Enforce no-store on all API endpoints to prevent caching of sensitive analysis data
        if request.path.startswith("/api"):
            response.headers["Cache-Control"] = "no-store"

        # CORS Header Injection for allowed origins (Exact matches, never '*')
        origin = request.headers.get("Origin")
        if origin and request.path.startswith("/api"):
            normalized_origin = origin.rstrip("/")
            allowed = get_allowed_origins(app)
            if normalized_origin in allowed:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
                response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
                response.headers["Access-Control-Max-Age"] = "86400"
                existing_vary = response.headers.get("Vary")
                if not existing_vary:
                    response.headers["Vary"] = "Origin"
                elif "Origin" not in existing_vary:
                    response.headers["Vary"] = f"{existing_vary}, Origin"

        return response

    # --- Error Handlers (Unified {"error": {"code": "...", "message": "..."}} shape) ---

    @app.errorhandler(400)
    def handle_bad_request(e: Exception):
        code = "bad_request"
        msg = "Invalid request payload or malformed syntax."
        if isinstance(e, BadRequest) and e.description:
            msg = e.description
            if "JSON" in msg:
                code = "invalid_json"
        return jsonify({"error": {"code": code, "message": msg}}), 400

    @app.errorhandler(404)
    def handle_not_found(e: Exception):
        if request.path.startswith("/api/") or request.headers.get("Accept") == "application/json":
            return jsonify({
                "error": {
                    "code": "not_found",
                    "message": "The requested API endpoint was not found.",
                }
            }), 404
        return render_template("404.html"), 404

    @app.errorhandler(405)
    @app.errorhandler(MethodNotAllowed)
    def handle_method_not_allowed(e: Exception):
        return jsonify({
            "error": {
                "code": "method_not_allowed",
                "message": "The method is not allowed for the requested URL.",
            }
        }), 405

    @app.errorhandler(413)
    @app.errorhandler(RequestEntityTooLarge)
    def handle_payload_too_large(e: Exception):
        msg = "Request payload exceeds the maximum allowed size limit."
        if isinstance(e, RequestEntityTooLarge) and e.description:
            msg = e.description
        return jsonify({
            "error": {
                "code": "payload_too_large",
                "message": msg,
            }
        }), 413

    @app.errorhandler(415)
    @app.errorhandler(UnsupportedMediaType)
    def handle_unsupported_media_type(e: Exception):
        return jsonify({
            "error": {
                "code": "unsupported_media_type",
                "message": "Unsupported Content-Type. Please use application/json.",
            }
        }), 415

    @app.errorhandler(429)
    def handle_rate_limit_exceeded(e: Exception):
        msg = "Too many requests. Sane rate limit is 60 requests per minute."
        if hasattr(e, "description") and e.description:
            msg = f"Rate limit exceeded: {e.description}."
        return jsonify({
            "error": {
                "code": "rate_limit_exceeded",
                "message": msg,
            }
        }), 429

    @app.errorhandler(500)
    def handle_internal_error(e: Exception):
        logger.error(f"Internal server error: {e}", exc_info=True)
        if request.path.startswith("/api/") or request.headers.get("Accept") == "application/json":
            return jsonify({
                "error": {
                    "code": "internal_server_error",
                    "message": "An unexpected error occurred while processing your request.",
                }
            }), 500
        return render_template("500.html"), 500

    @app.errorhandler(Exception)
    def handle_generic_exception(e: Exception):
        if isinstance(e, HTTPException):
            code_str = e.name.lower().replace(" ", "_")
            return jsonify({
                "error": {
                    "code": code_str,
                    "message": e.description,
                }
            }), e.code or 500

        logger.error(f"Unhandled exception: {e}", exc_info=True)
        return jsonify({
            "error": {
                "code": "internal_server_error",
                "message": "An unexpected internal error occurred.",
            }
        }), 500

    # --- Routes ---

    @app.route("/", methods=["GET"])
    def index():
        """Serve single-page application frontend."""
        return render_template("index.html")

    @app.route("/favicon.ico", methods=["GET"])
    def favicon():
        """Serve application favicon icon."""
        return send_from_directory(str(config.STATIC_DIR), "favicon.ico", mimetype="image/vnd.microsoft.icon")

    @app.route("/favicon.svg", methods=["GET"])
    def favicon_svg():
        """Serve vector SVG favicon."""
        return send_from_directory(str(config.STATIC_DIR), "favicon.svg", mimetype="image/svg+xml")

    @app.route("/api/health", methods=["GET"])
    @limiter.exempt
    def health_check():
        """Liveness and readiness check endpoint."""
        try:
            if get_predictor is not None:
                predictor = get_predictor()
                is_loaded = predictor.pipeline is not None
                version = predictor.metadata.get("trained_at", "1.0.0")
                status_text = "healthy" if is_loaded else "degraded"
            else:
                is_loaded = False
                version = "1.0.0"
                status_text = "degraded"
        except Exception as e:
            logger.warning(f"Health check predictor probe failed: {e}")
            is_loaded = False
            version = None
            status_text = "degraded"

        return jsonify({
            "status": status_text,
            "model_loaded": is_loaded,
            "model_version": version,
        }), 200

    @app.route("/api/model-info", methods=["GET"])
    @limiter.limit(get_rate_limit_model_info)
    def model_info():
        """Retrieve model provenance, evaluation metrics, and operational limitations."""
        meta = {}
        if get_predictor is not None:
            try:
                predictor = get_predictor()
                meta = predictor.metadata or {}
            except Exception:
                meta = {}
        if not meta and config.METADATA_PATH.exists():
            try:
                with open(config.METADATA_PATH, "r", encoding="utf-8") as f:
                    meta = json.load(f)
            except Exception as e:
                logger.warning(f"Metadata fallback load failed: {e}")

        test_m = meta.get("test_metrics", {})
        fp = test_m.get("false_positives", test_m.get("confusion_matrix", {}).get("false_positives", 0))
        fn = test_m.get("false_negatives", test_m.get("confusion_matrix", {}).get("false_negatives", 0))

        # Explicit limitations list
        limitations: List[str] = [
            "Metrics are measured on a held-out test set of THIS dataset only. Real-world email performance may be lower.",
            "Estimated model confidence is a probability, not an absolute guarantee, and confident mistakes are possible.",
            "Trained on 2000s-era Enron corporate emails; may underperform on modern phishing, spear phishing, or synthetic scam styles.",
            "English-oriented preprocessing; diacritic mark stripping and stopword heuristics may degrade accuracy on foreign languages.",
        ]

        # Sanitized thresholds
        thresholds_data = meta.get("threshold_tuning", {}).get("risk_thresholds", {
            "low": "< 0.40",
            "medium": "0.40 - 0.60 (Uncertain)",
            "high": "> 0.60",
        })

        info = {
            "model_type": meta.get("selected_model", "Calibrated Linear SVM"),
            "vectorizer": "TF-IDF (15,000 features, 1-2 n-grams, sublinear TF)",
            "version": meta.get("trained_at", "1.0.0"),
            "trained_at": meta.get("trained_at", "unknown"),
            "sklearn_version": meta.get("sklearn_version", "unknown"),
            "dataset_name": meta.get("dataset_name", "Enron Spam Dataset"),
            "dataset_source_url": meta.get("dataset_source_url", "https://github.com/MWiechmann/enron_spam_data"),
            "dataset_repository_license": meta.get("dataset_repository_license", "GNU General Public License v3.0"),
            "dataset_repo_license": meta.get("dataset_repository_license", "GNU General Public License v3.0"),
            "dataset_license": meta.get("dataset_license", "GNU General Public License v3.0"),
            "code_license": meta.get("code_license", "MIT"),
            "dataset_type": meta.get("dataset_type", "email"),
            "n_samples": meta.get("n_samples", 0),
            "n_train": meta.get("n_train", 24369),
            "n_test": meta.get("n_test", 6093),
            "class_counts": meta.get("class_counts", {"ham": 0, "spam": 0}),
            "selection_criterion": meta.get("selection_criterion", "Spam precision >= 0.98 first, then highest recall on spam, then F1 score."),
            "test_metrics": {
                "precision": test_m.get("precision", 0.0),
                "recall": test_m.get("recall", 0.0),
                "f1": test_m.get("f1", 0.0),
                "accuracy": test_m.get("accuracy", 0.0),
                "fp": fp,
                "fn": fn,
            },
            "thresholds": thresholds_data,
            "limitations": limitations,
        }

        # Sanitize to ensure no local paths are leaked
        raw_str = json.dumps(info)
        if "\\" in raw_str or "C:" in raw_str or "/Users/" in raw_str:
            raise RuntimeError("Path leak detected in model-info response")

        return jsonify(info), 200

    @app.route("/api/predict", methods=["GET", "POST"])
    @limiter.limit(get_rate_limit_predict)
    def predict_email():
        """Classify email subject and body as spam, ham, or uncertain."""
        if request.method != "POST":
            raise MethodNotAllowed()

        # 1. Enforce Content-Type application/json
        if not request.is_json:
            return jsonify({
                "error": {
                    "code": "unsupported_media_type",
                    "message": "Content-Type must be application/json.",
                }
            }), 415

        # 2. Parse and validate JSON structure
        try:
            data = request.get_json(silent=False)
        except RequestEntityTooLarge:
            raise
        except BadRequest:
            return jsonify({
                "error": {
                    "code": "invalid_json",
                    "message": "Malformed JSON payload.",
                }
            }), 400
        except HTTPException:
            raise
        except Exception:
            return jsonify({
                "error": {
                    "code": "invalid_json",
                    "message": "Malformed JSON payload.",
                }
            }), 400

        if not isinstance(data, dict):
            return jsonify({
                "error": {
                    "code": "invalid_json",
                    "message": "JSON body must be a valid key-value object.",
                }
            }), 400

        # 3. Validate subject field
        subject = data.get("subject", "")
        if subject is not None and not isinstance(subject, str):
            return jsonify({
                "error": {
                    "code": "invalid_type",
                    "message": "Field 'subject' must be a string if provided.",
                }
            }), 400

        # 4. Validate body field
        if "body" not in data:
            return jsonify({
                "error": {
                    "code": "missing_field",
                    "message": "Required field 'body' is missing from request payload.",
                }
            }), 400

        body = data["body"]
        if not isinstance(body, str):
            return jsonify({
                "error": {
                    "code": "invalid_type",
                    "message": "Field 'body' must be a string.",
                }
            }), 400

        if not body.strip():
            return jsonify({
                "error": {
                    "code": "empty_input",
                    "message": "Field 'body' cannot be empty or whitespace only.",
                }
            }), 400

        # 5. Length limit check
        combined_len = len(subject or "") + len(body)
        max_chars = int(os.getenv("MAX_INPUT_CHARS", str(config.MAX_INPUT_CHARS)))
        if combined_len > max_chars:
            return jsonify({
                "error": {
                    "code": "payload_too_large",
                    "message": f"Combined input length ({combined_len} characters) exceeds the maximum limit of {max_chars} characters.",
                }
            }), 413

        # 6. Run prediction
        predict_kwargs = {}
        if "filter_stopwords" in data:
            predict_kwargs["filter_stopwords"] = bool(data["filter_stopwords"])
        if "model" in data:
            predict_kwargs["model_key"] = str(data["model"])

        try:
            predictor = get_predictor()
            result = predictor.predict(
                subject=subject or "",
                body=body,
                **predict_kwargs,
            )
            return jsonify(result), 200
        except Exception as e:
            logger.error(f"Inference execution failure: {e}", exc_info=True)
            return jsonify({
                "error": {
                    "code": "prediction_error",
                    "message": "An unexpected error occurred during email classification.",
                }
            }), 500

    @app.route("/api/analyze", methods=["GET", "POST"])
    @limiter.limit(get_rate_limit_analyze)
    def analyze_email():
        """Deep email security analysis combining NLP ML model, heuristic signals, URL checks, and header validation."""
        if request.method != "POST":
            raise MethodNotAllowed()

        # 1. Enforce Content-Type application/json
        if not request.is_json:
            return jsonify({
                "error": {
                    "code": "unsupported_media_type",
                    "message": "Content-Type must be application/json.",
                }
            }), 415

        # 2. Parse and validate JSON structure
        try:
            data = request.get_json(silent=False)
        except RequestEntityTooLarge:
            raise
        except BadRequest:
            return jsonify({
                "error": {
                    "code": "invalid_json",
                    "message": "Malformed JSON payload.",
                }
            }), 400
        except HTTPException:
            raise
        except Exception:
            return jsonify({
                "error": {
                    "code": "invalid_json",
                    "message": "Malformed JSON payload.",
                }
            }), 400

        if not isinstance(data, dict):
            return jsonify({
                "error": {
                    "code": "invalid_json",
                    "message": "JSON body must be a valid key-value object.",
                }
            }), 400

        # 3. Validate input field types
        text_input = data.get("text")
        if text_input is None and data.get("body") and isinstance(data.get("body"), str):
            text_input = ((data.get("subject") or "") + "\n\n" + data["body"]).strip()
        if text_input is not None and not isinstance(text_input, str):
            return jsonify({
                "error": {
                    "code": "invalid_type",
                    "message": "Field 'text' must be a string if provided.",
                }
            }), 400

        eml_input = data.get("eml")
        if eml_input is not None and not isinstance(eml_input, str):
            return jsonify({
                "error": {
                    "code": "invalid_type",
                    "message": "Field 'eml' must be a string if provided.",
                }
            }), 400

        options_input = data.get("options")
        if options_input is not None and not isinstance(options_input, dict):
            return jsonify({
                "error": {
                    "code": "invalid_type",
                    "message": "Field 'options' must be a JSON object if provided.",
                }
            }), 400

        # 4. Enforce size limits
        max_chars = int(os.getenv("MAX_INPUT_CHARS", str(config.MAX_INPUT_CHARS)))
        max_eml_chars = 1_000_000  # 1 MB raw payload limit

        if text_input and len(text_input) > max_chars:
            return jsonify({
                "error": {
                    "code": "payload_too_large",
                    "message": f"Text input length ({len(text_input)} characters) exceeds maximum limit of {max_chars} characters.",
                }
            }), 413

        if eml_input and len(eml_input) > max_eml_chars:
            return jsonify({
                "error": {
                    "code": "payload_too_large",
                    "message": f"Raw EML payload length ({len(eml_input)} characters) exceeds maximum limit of {max_eml_chars} characters.",
                }
            }), 413

        # 5. Extract options
        opts = options_input or {}
        scan_urls = bool(opts.get("scan_urls", True))
        analyze_headers = bool(opts.get("analyze_headers", True))
        raw_sensitivity = str(opts.get("sensitivity", "medium")).lower()
        sensitivity = raw_sensitivity if raw_sensitivity in ("low", "medium", "high") else "medium"

        # 6. EML message parsing (if provided)
        eml_body = ""
        eml_html = ""
        eml_subject = ""
        eml_headers = None
        eml_indicators = []
        eml_attachments = []

        if eml_input and eml_input.strip():
            eml_parsed = parse_eml_message(eml_input)
            eml_body = eml_parsed.get("body", "") or ""
            eml_html = eml_parsed.get("html_body", "") or ""
            eml_subject = eml_parsed.get("subject", "") or ""
            eml_headers = eml_parsed.get("headers")
            eml_indicators = eml_parsed.get("indicators", [])
            eml_attachments = eml_parsed.get("attachments", [])

        # 7. Determine effective content to analyze
        if text_input and text_input.strip():
            raw_t = text_input.strip()
            if raw_t.lower().startswith("subject:") and "\n\n" in raw_t:
                parts = raw_t.split("\n\n", 1)
                sub_extracted = parts[0][len("subject:"):].strip()
                effective_subject = eml_subject or data.get("subject", "") or sub_extracted
                effective_body = parts[1].strip()
            else:
                effective_body = raw_t
                effective_subject = eml_subject or data.get("subject", "") or ""
            effective_html = eml_html
        elif eml_body.strip() or eml_html.strip():
            effective_body = eml_body.strip()
            effective_subject = eml_subject
            effective_html = eml_html
        else:
            return jsonify({
                "error": {
                    "code": "empty_input",
                    "message": "Either 'text' or 'eml' must be provided with non-empty content.",
                }
            }), 400

        # Check total combined length of effective subject and body
        combined_text_len = len(effective_subject) + len(effective_body)
        if combined_text_len > max_chars:
            return jsonify({
                "error": {
                    "code": "payload_too_large",
                    "message": f"Combined input length ({combined_text_len} characters) exceeds the maximum limit of {max_chars} characters.",
                }
            }), 413

        # 8. URL Extraction and inspection
        urls_list = []
        url_indicators = []
        if scan_urls:
            urls_list, url_indicators = extract_and_check_urls(effective_body, effective_html)

        # 9. Header telemetry and indicators
        header_data = None
        header_indicators_active = []
        if analyze_headers and eml_headers is not None:
            header_data = eml_headers
            header_indicators_active = eml_indicators

        # Combine heuristic threat indicators
        all_indicators = url_indicators + header_indicators_active

        # 10. Calibrated NLP Model Inference
        p_spam = 0.50
        confidence = 0.50
        uncertain = True
        top_tokens = []
        vocab_coverage = 100.0
        selected_model_key = opts.get("model") or data.get("model") or "svm"
        model_display_name = "Calibrated Linear SVM"
        models_comparison_data = None

        if get_predictor is not None:
            try:
                predictor = get_predictor()
                pred_result = predictor.predict(
                    subject=effective_subject,
                    body=effective_body,
                    model_key=selected_model_key,
                )
                p_spam = float(pred_result.get("spam_probability", 0.50))
                confidence = float(pred_result.get("confidence", 0.50))
                uncertain = bool(pred_result.get("is_uncertain", False))
                top_tokens = pred_result.get("top_tokens", [])
                raw_cov = pred_result.get("reliability", {}).get("vocab_coverage", 1.0)
                vocab_coverage = round(float(raw_cov) * 100.0, 2)
                model_display_name = pred_result.get("selected_model", "Calibrated Linear SVM")

                # Synthesize 3-model comparison
                models_comparison_data = predictor.compare_models(
                    subject=effective_subject,
                    body=effective_body,
                    primary_result=pred_result,
                )
            except Exception as e:
                logger.warning(f"Predictor model execution in /api/analyze failed: {type(e).__name__}")

        # 11. Compute unified Risk Score & Classification with guardrails
        risk_score, classification = compute_risk_score(
            probability=p_spam,
            indicators=all_indicators,
            sensitivity=sensitivity,
        )

        # 12. Synthesize concise Key Findings
        findings = generate_key_findings(
            probability=p_spam,
            classification=classification,
            indicators=all_indicators,
            headers=header_data,
            urls=urls_list,
        )

        # Compute cryptographic tamper-evident digest of analysed payload
        digest_input = ((effective_subject or "") + "\n" + (effective_body or "")).encode("utf-8", errors="replace")
        evidence_sha256 = hashlib.sha256(digest_input).hexdigest()

        # 13. Construct response
        response_payload = {
            "model": {
                "key": selected_model_key,
                "name": model_display_name,
                "label": "spam" if p_spam >= 0.50 else "ham",
                "probability": round(p_spam, 4),
                "confidence": round(confidence, 4),
                "uncertain": uncertain,
            },
            "models_comparison": models_comparison_data,
            "risk_score": risk_score,
            "classification": classification,
            "verdict": classification,
            "probabilities": {
                "spam": round(p_spam, 4),
                "ham": round(1.0 - p_spam, 4),
            },
            "indicators": all_indicators,
            "key_findings": findings,
            "top_tokens": top_tokens,
            "vocab_coverage": vocab_coverage,
            "urls": urls_list,
            "attachments": eml_attachments,
            "evidence_sha256": evidence_sha256,
            "sensitivity": sensitivity,
        }

        # Include headers only if headers were present
        if header_data is not None:
            response_payload["headers"] = header_data

        return jsonify(response_payload), 200

    @app.route("/api/models", methods=["GET"])
    @limiter.exempt
    def get_models_catalog():
        """Retrieve catalog of available ML models with test metrics."""
        return jsonify({
            "default_model": "svm",
            "models": [
                {
                    "key": "svm",
                    "name": "Calibrated Linear SVM",
                    "type": "Support Vector Machine",
                    "status": "production_primary",
                    "accuracy": 0.9900,
                    "precision": 0.9883,
                    "recall": 0.9907,
                    "f1": 0.9895,
                    "description": "Selected production winner with Platt sigmoid probability calibration.",
                },
                {
                    "key": "lr",
                    "name": "Logistic Regression",
                    "type": "Linear Classifier",
                    "status": "candidate",
                    "accuracy": 0.9869,
                    "precision": 0.9797,
                    "recall": 0.9931,
                    "f1": 0.9864,
                    "description": "High-recall linear model capturing stealth patterns.",
                },
                {
                    "key": "nb",
                    "name": "Multinomial Naive Bayes",
                    "type": "Probabilistic",
                    "status": "candidate",
                    "accuracy": 0.9849,
                    "precision": 0.9832,
                    "recall": 0.9852,
                    "f1": 0.9842,
                    "description": "Fast probabilistic baseline classifier.",
                },
            ],
        }), 200

    @app.route("/api/compare", methods=["POST"])
    @limiter.limit(get_rate_limit_analyze)
    def compare_models_endpoint():
        """Compare all 3 ML models on submitted email text."""
        if not request.is_json:
            return jsonify({
                "error": {
                    "code": "unsupported_media_type",
                    "message": "Content-Type must be application/json.",
                }
            }), 415

        data = request.get_json(silent=True) or {}
        subject = data.get("subject", "")
        body = data.get("body", "") or data.get("text", "")
        if not str(body).strip():
            return jsonify({
                "error": {
                    "code": "empty_input",
                    "message": "Email text or body cannot be empty.",
                }
            }), 400

        try:
            predictor = get_predictor()
            res = predictor.compare_models(subject=subject, body=body)
            return jsonify(res), 200
        except Exception as e:
            logger.error(f"Compare models failure: {e}", exc_info=True)
            return jsonify({
                "error": {
                    "code": "comparison_error",
                    "message": "Failed to execute multi-model comparison.",
                }
            }), 500

    return app



# Root app instance for WSGI servers (Gunicorn)
app = create_app()

if __name__ == "__main__":
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
