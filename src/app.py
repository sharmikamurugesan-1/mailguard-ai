"""Flask application factory for MailGuard AI.

Phase 2: Backend Foundation
- App factory pattern: create_app()
- Configuration loaded via environment variables and src.config
- Central JSON error handlers (400, 404, 413, 500) with zero path or traceback leaks
- Request payload limit enforced via MAX_CONTENT_LENGTH
- GET /api/health endpoint returning {status, model_loaded: false, model_version: null}
"""

import logging
from typing import Any, Dict, Optional

from flask import Flask, jsonify, request
from werkzeug.exceptions import BadRequest, HTTPException, NotFound, RequestEntityTooLarge

from src import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MailGuard-API")


def create_app(test_config: Optional[Dict[str, Any]] = None) -> Flask:
    """Create and configure an instance of the Flask application."""
    app = Flask(
        __name__,
        static_folder=str(config.STATIC_DIR),
        static_url_path="",
    )

    # Configuration
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH
    app.config["JSON_SORT_KEYS"] = False

    if test_config:
        app.config.update(test_config)

    # --- Routes ---

    @app.route("/api/health", methods=["GET"])
    def health_check():
        """Health and liveness check endpoint.

        Returns server readiness status and model loading state.
        """
        return jsonify({
            "status": "online",
            "model_loaded": False,
            "model_version": None,
        }), 200

    # --- Error Handlers (JSON with zero path / traceback leaks) ---

    @app.errorhandler(400)
    def handle_bad_request(e: Exception):
        description = "Invalid request payload or malformed syntax."
        if isinstance(e, BadRequest) and e.description:
            description = e.description
        return jsonify({
            "status": "error",
            "error": "bad_request",
            "message": description,
        }), 400

    @app.errorhandler(404)
    def handle_not_found(e: Exception):
        return jsonify({
            "status": "error",
            "error": "not_found",
            "message": "The requested API endpoint was not found.",
        }), 404

    @app.errorhandler(413)
    @app.errorhandler(RequestEntityTooLarge)
    def handle_payload_too_large(e: Exception):
        max_mb = round(app.config["MAX_CONTENT_LENGTH"] / (1024 * 1024), 1)
        return jsonify({
            "status": "error",
            "error": "payload_too_large",
            "message": f"Request payload exceeds the maximum allowed size of {max_mb} MB.",
        }), 413

    @app.errorhandler(500)
    def handle_internal_error(e: Exception):
        logger.error(f"Internal server error: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "error": "internal_server_error",
            "message": "An unexpected error occurred while processing your request.",
        }), 500

    @app.errorhandler(Exception)
    def handle_generic_exception(e: Exception):
        if isinstance(e, HTTPException):
            return jsonify({
                "status": "error",
                "error": e.name.lower().replace(" ", "_"),
                "message": e.description,
            }), e.code or 500

        logger.error(f"Unhandled exception: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "error": "internal_server_error",
            "message": "An unexpected internal error occurred.",
        }), 500

    return app


# Root app instance for WSGI servers (Gunicorn)
app = create_app()

if __name__ == "__main__":
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
