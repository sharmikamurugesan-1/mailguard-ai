"""Developer Slow Proxy for Cold-Start / Latency Simulation (Phase 7).

Usage:
  1. Start backend app: python -m src.app (port 5000)
  2. Start proxy: python scripts/dev_slow_proxy.py --delay 8 (port 5050)
  3. Open http://127.0.0.1:5050/ in browser to test cold-start UI behavior.

This script runs outside of production code and introduces controllable delays
only on /api/predict to verify:
  - 5s waking banner display
  - Button disabled and loading state
  - 90s AbortController timeout + automatic retry + 'Try again' button
"""

import argparse
import http.client
from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import urllib.parse

TARGET_HOST = "127.0.0.1"
TARGET_PORT = 5000
PROXY_PORT = 5050
DELAY_SECONDS = 8.0


class SlowProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._forward_request("GET")

    def do_POST(self):
        # Inject artificial delay specifically on predict endpoint
        if "/api/predict" in self.path:
            print(f"[SlowProxy] Injecting {DELAY_SECONDS}s delay on {self.path}...")
            time.sleep(DELAY_SECONDS)
            print("[SlowProxy] Resuming request forwarding.")
        self._forward_request("POST")

    def _forward_request(self, method):
        # Read body if present
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else None

        # Connect to target server
        conn = http.client.HTTPConnection(TARGET_HOST, TARGET_PORT)
        headers = {k: v for k, v in self.headers.items() if k.lower() != "host"}

        conn.request(method, self.path, body=body, headers=headers)
        response = conn.getresponse()
        resp_data = response.read()

        # Send response back to client
        self.send_response(response.status)
        for h, v in response.getheaders():
            if h.lower() not in ("transfer-encoding", "content-length"):
                self.send_header(h, v)
        self.send_header("Content-Length", str(len(resp_data)))
        self.end_headers()
        self.wfile.write(resp_data)
        conn.close()

    def log_message(self, format, *args):
        print(f"[SlowProxy] {self.address_string()} - {format % args}")


def main():
    global DELAY_SECONDS
    parser = argparse.ArgumentParser(description="Slow proxy for cold-start UX testing")
    parser.add_argument("--delay", type=float, default=8.0, help="Artificial delay in seconds on /api/predict")
    parser.add_argument("--port", type=int, default=5050, help="Proxy listening port")
    args = parser.parse_args()

    DELAY_SECONDS = args.delay
    server = HTTPServer(("127.0.0.1", args.port), SlowProxyHandler)
    print(f"[SlowProxy] Running on http://127.0.0.1:{args.port} -> forwarding to port {TARGET_PORT} with {DELAY_SECONDS}s delay on /api/predict.")
    server.serve_forever()


if __name__ == "__main__":
    main()
