#!/usr/bin/env python3
"""Local HTTP server emulating Vercel's static runtime and vercel.json configuration.

Phase 12J: Split-deploy hardening.
Reads vercel.json directly to apply:
1. outputDirectory resolution (frontend/)
2. Custom headers matching source patterns (CSP, X-Frame-Options, Referrer-Policy, etc.)
3. cleanUrls: .html resolution for extensionless paths
4. Filesystem priority: static files are NEVER swallowed by SPA rewrites
5. SPA rewrites: fallback non-existent paths to /index.html
"""

import http.server
import json
import mimetypes
import os
from pathlib import Path
import re
import socketserver
import sys
import threading
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent
VERCEL_JSON_PATH = BASE_DIR / "vercel.json"

MIME_OVERRIDES = {
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".html": "text/html; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".wasm": "application/wasm",
    ".svg": "image/svg+xml",
    ".woff2": "font/woff2",
    ".gz": "application/gzip",
}


def load_vercel_config():
    if not VERCEL_JSON_PATH.exists():
        raise FileNotFoundError(f"vercel.json not found at {VERCEL_JSON_PATH}")
    return json.loads(VERCEL_JSON_PATH.read_text(encoding="utf-8"))


class VercelStaticHandler(http.server.BaseHTTPRequestHandler):
    """HTTP request handler emulating Vercel deployment behaviour."""

    def __init__(self, *args, vercel_config=None, output_dir=None, **kwargs):
        self._explicit_config = vercel_config
        self.output_dir = output_dir or (BASE_DIR / (vercel_config or load_vercel_config()).get("outputDirectory", "frontend"))
        super().__init__(*args, **kwargs)

    @property
    def vercel_config(self):
        if self._explicit_config is not None:
            return self._explicit_config
        return load_vercel_config()

    def log_message(self, format, *args):
        # Quiet logger unless error
        if args and str(args[1]).startswith(("4", "5")):
            sys.stderr.write(f"[VercelServer] {self.address_string()} - {format % args}\n")

    def _get_configured_headers(self, path: str):
        """Find and collect headers defined in vercel.json that match path."""
        headers = []
        for rule in self.vercel_config.get("headers", []):
            source_pat = rule.get("source", "")
            # Convert Vercel source pattern to regex
            regex_pat = "^" + source_pat.replace("/(.*)", "/.*") + "$"
            if re.match(regex_pat, path):
                for h in rule.get("headers", []):
                    headers.append((h["key"], h["value"]))
        return headers

    def do_HEAD(self):
        self._serve_path(send_body=False)

    def do_GET(self):
        self._serve_path(send_body=True)

    def _serve_path(self, send_body: bool = True):
        parsed = urlparse(self.path)
        rel_path = parsed.path.lstrip("/")

        # 1. Clean URLs check
        clean_urls = self.vercel_config.get("cleanUrls", False)

        # Candidate filesystem path
        target_file = None
        if not rel_path or rel_path == "/":
            target_file = self.output_dir / "index.html"
        else:
            candidate = self.output_dir / rel_path
            if candidate.is_file():
                target_file = candidate
            elif clean_urls and (self.output_dir / f"{rel_path}.html").is_file():
                target_file = self.output_dir / f"{rel_path}.html"

        # 2. SPA Rewrites fallback
        if target_file is None or not target_file.is_file():
            # Check rewrites in vercel.json
            for rw in self.vercel_config.get("rewrites", []):
                src_pat = rw.get("source", "")
                dest = rw.get("destination", "/index.html")
                regex_pat = "^" + src_pat.replace("/(.*)", "/.*") + "$"
                if re.match(regex_pat, parsed.path):
                    target_file = self.output_dir / dest.lstrip("/")
                    break

        if target_file is None or not target_file.is_file():
            # 404 fallback
            not_found_file = self.output_dir / "404.html"
            content = not_found_file.read_bytes() if not_found_file.is_file() else b"Not Found"
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self._apply_vercel_headers(parsed.path)
            self.end_headers()
            if send_body:
                self.wfile.write(content)
            return

        # 3. Serve the resolved file
        content = target_file.read_bytes()
        ext = target_file.suffix.lower()
        content_type = MIME_OVERRIDES.get(ext) or mimetypes.guess_type(target_file.name)[0] or "application/octet-stream"

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))

        # Handle gzip compressed vendor files
        if target_file.name.endswith(".traineddata.gz"):
            self.send_header("Content-Encoding", "gzip")

        self._apply_vercel_headers(parsed.path)
        self.end_headers()

        if send_body:
            self.wfile.write(content)

    def _apply_vercel_headers(self, path: str):
        for key, val in self._get_configured_headers(path):
            self.send_header(key, val)


class ReusableThreadingServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


def create_vercel_server(port: int = 3000):
    def handler_factory(*args, **kwargs):
        return VercelStaticHandler(*args, **kwargs)

    httpd = ReusableThreadingServer(("127.0.0.1", port), handler_factory)
    return httpd


def run_standalone(port: int = 3000):
    server = create_vercel_server(port)
    print(f"Vercel static emulator running at http://127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    run_standalone(port)
