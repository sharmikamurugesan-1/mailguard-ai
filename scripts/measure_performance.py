"""Benchmark MailGuard AI performance: Cold start, API latency (p50/p95), and gzipped asset sizes."""

import gzip
import json
from pathlib import Path
import statistics
import subprocess
import sys
import time

base_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(base_dir))


def measure_cold_start() -> float:
    """Measure cold start time in a fresh, isolated Python subprocess."""
    code = """
import time
t0 = time.perf_counter()
from app import app
with app.test_client() as client:
    resp = client.get('/api/health')
    assert resp.status_code == 200
t1 = time.perf_counter()
print(f"COLD_START_SEC:{t1 - t0:.4f}")
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(base_dir),
        capture_output=True,
        text=True,
        check=True,
    )
    for line in result.stdout.splitlines():
        if line.startswith("COLD_START_SEC:"):
            return float(line.split(":")[1])
    return 0.0


def benchmark_api_latencies(n_runs: int = 100):
    from app import app
    app.config["RATELIMIT_ENABLED"] = False
    if hasattr(app, "limiter"):
        app.limiter.enabled = False
    client = app.test_client()

    payloads = [
        {
            "text": "Subject: Q3 Project Review & Sprint Deliverables\n\nHi team, please find attached the reviewed roadmap items and schedule for tomorrow's standup meeting.",
            "headers": "From: manager@company.test\nTo: team@company.test\nSubject: Sprint Review",
        },
        {
            "text": "Subject: URGENT: Verify your account immediately\n\nYour bank account has been suspended! Click http://secure-auth.test/verify now or lose all funds.",
            "headers": "From: security@fakebank.test\nTo: victim@example.test\nSubject: URGENT",
        },
        {
            "text": "Subject: Borderline notification alert\n\nYour subscription will renew soon. View details at http://service.test/billing.",
            "headers": "",
        },
    ]

    # Warmup
    for _ in range(5):
        client.post("/api/analyze", json=payloads[0])

    latencies_ms = []
    for i in range(n_runs):
        p = payloads[i % len(payloads)]
        t0 = time.perf_counter()
        resp = client.post("/api/analyze", json=p)
        t1 = time.perf_counter()
        if resp.status_code != 200:
            print(f"FAILED on run {i}: status={resp.status_code}, body={resp.get_json()}")
        assert resp.status_code == 200
        latencies_ms.append((t1 - t0) * 1000.0)

    p50 = statistics.median(latencies_ms)
    sorted_lats = sorted(latencies_ms)
    p95_idx = int(0.95 * len(sorted_lats))
    p95 = sorted_lats[p95_idx]
    p99_idx = int(0.99 * len(sorted_lats))
    p99 = sorted_lats[p99_idx]
    mean_lat = statistics.mean(latencies_ms)

    return {
        "runs": n_runs,
        "mean_ms": round(mean_lat, 2),
        "p50_ms": round(p50, 2),
        "p95_ms": round(p95, 2),
        "p99_ms": round(p99, 2),
        "min_ms": round(min(latencies_ms), 2),
        "max_ms": round(max(latencies_ms), 2),
    }


def measure_asset_sizes():
    static_dir = base_dir / "static"
    templates_dir = base_dir / "templates"

    assets = [
        templates_dir / "index.html",
        static_dir / "css" / "style.css",
        static_dir / "js" / "app.js",
        static_dir / "data" / "examples.json",
        static_dir / "vendor" / "tesseract" / "tesseract.min.js",
        static_dir / "vendor" / "tesseract" / "tesseract-worker.min.js",
        static_dir / "vendor" / "tesseract" / "tesseract-core.wasm.js",
        static_dir / "vendor" / "jsqr" / "jsQR.js",
    ]

    report = []
    total_raw = 0
    total_gzip = 0

    for path in assets:
        if not path.exists():
            continue
        raw_bytes = path.read_bytes()
        gz_bytes = gzip.compress(raw_bytes, compresslevel=9)
        raw_len = len(raw_bytes)
        gz_len = len(gz_bytes)
        total_raw += raw_len
        total_gzip += gz_len
        rel = path.relative_to(base_dir).as_posix()
        report.append({
            "asset": rel,
            "raw_kb": round(raw_len / 1024.0, 2),
            "gzip_kb": round(gz_len / 1024.0, 2),
            "compression_ratio": round(raw_len / max(gz_len, 1), 2),
        })

    return report, round(total_raw / 1024.0, 2), round(total_gzip / 1024.0, 2)


def main():
    print("=" * 70)
    print("MAILGUARD AI - PERFORMANCE BENCHMARK")
    print("=" * 70)

    # 1. Cold start
    cold_start_sec = measure_cold_start()
    print(f"Cold Start (Process + Model + Health check): {cold_start_sec:.3f} s")

    # 2. Latencies
    print("\nBenchmarking /api/analyze over 100 requests...")
    latency_stats = benchmark_api_latencies(100)
    print(f"Mean Latency: {latency_stats['mean_ms']} ms")
    print(f"p50  Latency: {latency_stats['p50_ms']} ms")
    print(f"p95  Latency: {latency_stats['p95_ms']} ms")
    print(f"p99  Latency: {latency_stats['p99_ms']} ms")

    # 3. Assets
    print("\nMeasuring Gzipped Asset Sizes...")
    assets, total_raw_kb, total_gzip_kb = measure_asset_sizes()
    for a in assets:
        print(f"  {a['asset']:<45} {a['raw_kb']:>7} KB raw | {a['gzip_kb']:>6} KB gzip")
    print("-" * 70)
    print(f"Total Static Assets: {total_raw_kb} KB raw | {total_gzip_kb} KB gzip")
    print("=" * 70)

    perf_report = {
        "cold_start_sec": cold_start_sec,
        "latency_stats": latency_stats,
        "assets": assets,
        "total_raw_kb": total_raw_kb,
        "total_gzip_kb": total_gzip_kb,
    }

    out_file = base_dir / "reports" / "performance_benchmark.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(perf_report, f, indent=2)
    print(f"Saved report to {out_file.relative_to(base_dir)}")


if __name__ == "__main__":
    main()
