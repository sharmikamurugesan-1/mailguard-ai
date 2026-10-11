"""Download and verify self-hosted vendor libraries for Phase 12F.

Self-hosts:
- jsQR v1.4.0 (client-side QR decoding)
- Tesseract.js v5.1.0 + worker + wasm core + English fast traineddata
"""

from pathlib import Path
import urllib.request
import sys

VENDOR_URLS = {
    "static/vendor/jsqr/jsQR.js": "https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.js",
    "static/vendor/tesseract/tesseract.min.js": "https://cdn.jsdelivr.net/npm/tesseract.js@5.1.0/dist/tesseract.min.js",
    "static/vendor/tesseract/worker.min.js": "https://cdn.jsdelivr.net/npm/tesseract.js@5.1.0/dist/worker.min.js",
    "static/vendor/tesseract/tesseract-core-simd-lstm.wasm.js": "https://cdn.jsdelivr.net/npm/tesseract.js-core@5.1.0/tesseract-core-simd-lstm.wasm.js",
    "static/vendor/tesseract/tesseract-core-simd-lstm.wasm": "https://cdn.jsdelivr.net/npm/tesseract.js-core@5.1.0/tesseract-core-simd-lstm.wasm",
    "static/vendor/tesseract/tesseract-core-lstm.wasm.js": "https://cdn.jsdelivr.net/npm/tesseract.js-core@5.1.0/tesseract-core-lstm.wasm.js",
    "static/vendor/tesseract/tesseract-core-lstm.wasm": "https://cdn.jsdelivr.net/npm/tesseract.js-core@5.1.0/tesseract-core-lstm.wasm",
    "static/vendor/tesseract/eng.traineddata.gz": "https://raw.githubusercontent.com/naptha/tessdata/gh-pages/4.0.0_fast/eng.traineddata.gz",
}


def download_vendor_assets():
    project_root = Path(__file__).resolve().parent.parent
    headers = {"User-Agent": "Mozilla/5.0 (MailGuard-AI/VendorFetcher)"}

    print("Checking and downloading self-hosted vendor libraries...")
    for rel_path, url in VENDOR_URLS.items():
        dest = project_root / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists() and dest.stat().st_size > 0:
            print(f"  [OK] {rel_path} already exists ({dest.stat().st_size:,} bytes)")
            continue

        print(f"  Downloading {url} -> {rel_path}...")
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp, open(dest, "wb") as out:
            out.write(resp.read())
        print(f"  [Saved] {rel_path} ({dest.stat().st_size:,} bytes)")


if __name__ == "__main__":
    download_vendor_assets()
