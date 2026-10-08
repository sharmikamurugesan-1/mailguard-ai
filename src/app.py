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

import json
import logging
import os
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import (
    BadRequest,
    HTTPException,
    MethodNotAllowed,
    NotFound,
    RequestEntityTooLarge,
    UnsupportedMediaType,
)

from src import config
from src.predictor import get_predictor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MailGuard-API")


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

    # Security Headers Hook
    @app.after_request
    def set_security_headers(response):
        """Inject strict security and privacy headers into every response."""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "frame-ancestors 'none';"
        )
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
        return jsonify({
            "error": {
                "code": "not_found",
                "message": "The requested API endpoint was not found.",
            }
        }), 404

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

    @app.errorhandler(500)
    def handle_internal_error(e: Exception):
        logger.error(f"Internal server error: {e}", exc_info=True)
        return jsonify({
            "error": {
                "code": "internal_server_error",
                "message": "An unexpected error occurred while processing your request.",
            }
        }), 500

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

    @app.route("/api/health", methods=["GET"])
    def health_check():
        """Liveness and readiness check endpoint."""
        try:
            predictor = get_predictor()
            is_loaded = predictor.pipeline is not None
            version = predictor.metadata.get("trained_at", "1.0.0")
            status_text = "healthy" if is_loaded else "degraded"
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
    def model_info():
        """Retrieve model provenance, evaluation metrics, and operational limitations."""
        predictor = get_predictor()
        meta = predictor.metadata or {}

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
            "dataset_license": meta.get("dataset_license", "GNU General Public License v3.0"),
            "dataset_type": meta.get("dataset_type", "email"),
            "n_samples": meta.get("n_samples", 0),
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
        assert "\\" not in raw_str and "C:" not in raw_str and "/Users/" not in raw_str, "Path leak in model-info"

        return jsonify(info), 200

    @app.route("/api/predict", methods=["GET", "POST"])
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
        try:
            predictor = get_predictor()
            result = predictor.predict(subject=subject or "", body=body)
            return jsonify(result), 200
        except Exception as e:
            logger.error(f"Inference execution failure: {e}", exc_info=True)
            return jsonify({
                "error": {
                    "code": "prediction_error",
                    "message": "An unexpected error occurred during email classification.",
                }
            }), 500

    return app


# Root app instance for WSGI servers (Gunicorn)
app = create_app()

if __name__ == "__main__":
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
