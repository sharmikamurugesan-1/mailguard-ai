"""Measures CPU process time and wall-clock latency per /api/analyze request.

Runs 200 iterations for each payload tier:
- Short (~50 Bytes)
- Typical (~500 Bytes)
- Large (~18 KB text near MAX_INPUT_CHARS limit)

Measures:
- time.process_time() (CPU seconds consumed on CPU)
- time.perf_counter() (Wall-clock seconds elapsed)
- Calculates p50, p95, p99, and theoretical max RPS for 0.1, 0.5, and 1.0 vCPU.
"""

import json
import statistics
import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.app import create_app

SHORT_PAYLOAD = {
    "text": "Quick sync tomorrow at 10am regarding project.",
    "options": {"scan_urls": True, "sensitivity": "medium"}
}

TYPICAL_PAYLOAD = {
    "text": (
        "Subject: Invoice INV-2026-9481\n\n"
        "Please find attached invoice INV-2026-9481 for consulting services rendered in September 2026. "
        "The total balance due is $4,250.00 payable within 14 business days. You can review your account statement "
        "online at https://billing.example.test/portal?id=9481. If you have questions regarding this billing statement, "
        "contact our accounts department directly. Thank you for your continued partnership and prompt payment."
    ),
    "options": {"scan_urls": True, "sensitivity": "medium"}
}

# Construct ~18 KB text (under 20k char limit)
LARGE_TEXT = (
    "Subject: Comprehensive Quarterly Security Audit and Vulnerability Assessment Report\n\n"
    + ("During the recent security review, multiple endpoints were tested against adversarial vectors. "
       "Security officers noticed repeated attempts to harvest credentials via https://verify-login.example.test/auth. "
       "All employees are reminded to verify SSL certificates and never approve unexpected MFA push notifications.\n\n" * 55)
)

LARGE_PAYLOAD = {
    "text": LARGE_TEXT[:18000],
    "options": {"scan_urls": True, "sensitivity": "medium"}
}


def benchmark_tier(client, payload: dict, name: str, n: int = 200):
    cpu_times = []
    wall_times = []

    # Warmup 5 runs
    for _ in range(5):
        client.post("/api/analyze", json=payload)

    for _ in range(n):
        c_start = time.process_time()
        w_start = time.perf_counter()

        res = client.post("/api/analyze", json=payload)
        assert res.status_code == 200

        w_elapsed = time.perf_counter() - w_start
        c_elapsed = time.process_time() - c_start

        cpu_times.append(c_elapsed)
        wall_times.append(w_elapsed)

    cpu_times.sort()
    wall_times.sort()

    p50_cpu = statistics.median(cpu_times)
    p95_cpu = cpu_times[int(0.95 * n)]
    p99_cpu = cpu_times[int(0.99 * n)]

    p50_wall = statistics.median(wall_times)
    p95_wall = wall_times[int(0.95 * n)]
    p99_wall = wall_times[int(0.99 * n)]

    # Theoretical RPS = CPU_share / cpu_seconds
    rps_01 = 0.1 / p50_cpu if p50_cpu > 0 else 0
    rps_05 = 0.5 / p50_cpu if p50_cpu > 0 else 0
    rps_10 = 1.0 / p50_cpu if p50_cpu > 0 else 0

    return {
        "name": name,
        "payload_bytes": len(json.dumps(payload)),
        "n": n,
        "cpu_seconds": {
            "p50": round(p50_cpu, 6),
            "p95": round(p95_cpu, 6),
            "p99": round(p99_cpu, 6),
        },
        "wall_seconds": {
            "p50": round(p50_wall, 6),
            "p95": round(p95_wall, 6),
            "p99": round(p99_wall, 6),
        },
        "theoretical_rps": {
            "0.1_cpu": round(rps_01, 1),
            "0.5_cpu": round(rps_05, 1),
            "1.0_cpu": round(rps_10, 1),
        }
    }


def main():
    print("Initializing Flask test client...")
    app = create_app({"TESTING": True})
    client = app.test_client()

    print("\nRunning CPU Process Time Benchmark (200 requests per tier)...")
    results = {}
    for name, payload in [("Short (50B)", SHORT_PAYLOAD), ("Typical (500B)", TYPICAL_PAYLOAD), ("Large (18KB)", LARGE_PAYLOAD)]:
        print(f"  Benchmarking {name}...")
        res = benchmark_tier(client, payload, name, n=200)
        results[name] = res

    # Blended weighted average (70% typical, 20% short, 10% large)
    blended_cpu_p50 = (
        0.20 * results["Short (50B)"]["cpu_seconds"]["p50"] +
        0.70 * results["Typical (500B)"]["cpu_seconds"]["p50"] +
        0.10 * results["Large (18KB)"]["cpu_seconds"]["p50"]
    )
    blended_cpu_p95 = (
        0.20 * results["Short (50B)"]["cpu_seconds"]["p95"] +
        0.70 * results["Typical (500B)"]["cpu_seconds"]["p95"] +
        0.10 * results["Large (18KB)"]["cpu_seconds"]["p95"]
    )

    blended = {
        "cpu_seconds_p50": round(blended_cpu_p50, 6),
        "cpu_seconds_p95": round(blended_cpu_p95, 6),
        "theoretical_rps": {
            "0.1_cpu": round(0.1 / blended_cpu_p50, 1) if blended_cpu_p50 > 0 else 0,
            "0.5_cpu": round(0.5 / blended_cpu_p50, 1) if blended_cpu_p50 > 0 else 0,
            "1.0_cpu": round(1.0 / blended_cpu_p50, 1) if blended_cpu_p50 > 0 else 0,
        }
    }
    results["Blended (70/20/10)"] = blended

    output_path = Path("reports/cpu_benchmark.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\nBenchmark Results Summary:")
    print(json.dumps(results, indent=2))
    print(f"\nSaved results to {output_path}")


if __name__ == "__main__":
    main()
