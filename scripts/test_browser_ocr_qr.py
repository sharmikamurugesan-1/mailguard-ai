"""Test self-hosted Tesseract.js and jsQR in headless Chromium via Playwright."""

import sys
import time
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.app import create_app


def run_test():
    # Start app on test port
    app = create_app({"TESTING": True})
    
    from werkzeug.serving import make_server
    server = make_server("127.0.0.1", 5005, app)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    print("Flask server running on http://127.0.0.1:5005")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            console_messages = []
            page.on("console", lambda msg: console_messages.append(f"[{msg.type}] {msg.text}"))
            page.on("pageerror", lambda err: console_messages.append(f"[ERROR] {err}"))

            page.goto("http://127.0.0.1:5005/")
            print("Page loaded:", page.title())

            # 1. Test lazy-loading scripts
            result = page.evaluate("""async () => {
                const loadScript = (src) => new Promise((resolve, reject) => {
                    const s = document.createElement('script');
                    s.src = src;
                    s.onload = resolve;
                    s.onerror = reject;
                    document.head.appendChild(s);
                });
                await loadScript('/vendor/jsqr/jsQR.js');
                await loadScript('/vendor/tesseract/tesseract.min.js');
                return {
                    hasJsQR: typeof window.jsQR === 'function',
                    hasTesseract: typeof window.Tesseract === 'object' && typeof window.Tesseract.createWorker === 'function'
                };
            }""")
            print("Vendor library load status:", result)
            assert result["hasJsQR"], "jsQR failed to load"
            assert result["hasTesseract"], "Tesseract failed to load"

            # 2. Test jsQR decoding on qr_phish.png
            qr_fixture = PROJECT_ROOT / "tests" / "fixtures" / "images" / "qr_phish.png"
            with open(qr_fixture, "rb") as f:
                qr_bytes = list(f.read())

            qr_result = page.evaluate("""async (bytes) => {
                const blob = new Blob([new Uint8Array(bytes)], { type: 'image/png' });
                const img = new Image();
                const url = URL.createObjectURL(blob);
                await new Promise((res, rej) => {
                    img.onload = res;
                    img.onerror = rej;
                    img.src = url;
                });
                const canvas = document.createElement('canvas');
                canvas.width = img.width;
                canvas.height = img.height;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0);
                const imgData = ctx.getImageData(0, 0, img.width, img.height);
                const code = window.jsQR(imgData.data, img.width, img.height);
                URL.revokeObjectURL(url);
                return code ? code.data : null;
            }""", qr_bytes)
            print("QR Code decode result:", qr_result)
            assert qr_result == "http://phishing-portal.test/steal-credentials", f"Unexpected QR: {qr_result}"

            # 3. Test Tesseract OCR on text_screenshot.png
            text_fixture = PROJECT_ROOT / "tests" / "fixtures" / "images" / "text_screenshot.png"
            with open(text_fixture, "rb") as f:
                text_bytes = list(f.read())

            t0 = time.perf_counter()
            ocr_result = page.evaluate("""async (bytes) => {
                const blob = new Blob([new Uint8Array(bytes)], { type: 'image/png' });
                const img = new Image();
                const url = URL.createObjectURL(blob);
                await new Promise((res, rej) => {
                    img.onload = res;
                    img.onerror = rej;
                    img.src = url;
                });
                const canvas = document.createElement('canvas');
                canvas.width = img.width;
                canvas.height = img.height;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0);

                const worker = await window.Tesseract.createWorker(['eng'], 1, {
                    workerPath: '/vendor/tesseract/worker.min.js',
                    corePath: '/vendor/tesseract/tesseract-core-simd-lstm.wasm.js',
                    langPath: '/vendor/tesseract',
                    gzip: true
                });
                const res = await worker.recognize(canvas);
                await worker.terminate();
                URL.revokeObjectURL(url);
                return {
                    text: res.data.text,
                    confidence: res.data.confidence
                };
            }""", text_bytes)
            t1 = time.perf_counter()
            ocr_latency = t1 - t0
            print(f"OCR recognition latency: {ocr_latency:.2f}s")
            print(f"OCR Confidence: {ocr_result['confidence']:.2f}%")
            print(f"OCR Extracted snippet: {ocr_result['text'][:120]}...")

            assert "URGENT NOTICE" in ocr_result["text"] or "restricted" in ocr_result["text"].lower() or "security-update" in ocr_result["text"].lower()

            browser.close()
            print("\nALL IN-BROWSER OCR AND QR CHECKS PASSED PERFECTLY!")

    finally:
        server.shutdown()


if __name__ == "__main__":
    run_test()
