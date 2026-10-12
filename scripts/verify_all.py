#!/usr/bin/env python3
"""Unified verification orchestrator for MailGuard AI.

Usage:
    python scripts/verify_all.py --quick
    python scripts/verify_all.py --full

Features:
- --quick: Fast sanity checks (model hash integrity, static frontend export, API origin safety & core API tests).
- --full: Comprehensive regression (model integrity, static export, full pytest suite, split architecture Playwright verification, Axe accessibility audit on all routes).
- Emits raw summary report to reports/verify_latest.md.
"""

import argparse
import hashlib
from pathlib import Path
import subprocess
import sys
import time

BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
REPORT_FILE = REPORTS_DIR / "verify_latest.md"


def check_model_integrity() -> bool:
    """Validate SHA-256 hash of models/spam_pipeline.joblib against committed hash."""
    model_path = BASE_DIR / "models" / "spam_pipeline.joblib"
    hash_path = BASE_DIR / "models" / "model_hash.sha256"

    if not model_path.exists():
        print(f"ERROR: Model file not found at {model_path}")
        return False
    if not hash_path.exists():
        print(f"ERROR: Model hash file not found at {hash_path}")
        return False

    expected_hash = hash_path.read_text(encoding="utf-8").strip()
    actual_hash = hashlib.sha256(model_path.read_bytes()).hexdigest()

    if actual_hash != expected_hash:
        print(f"ERROR: Model hash mismatch! Expected {expected_hash}, got {actual_hash}")
        return False

    print(f"  [PASS] Model SHA-256 integrity verified: {actual_hash[:16]}...")
    return True


def run_command(cmd, desc: str) -> tuple[int, str]:
    """Execute command and return returncode and output."""
    print(f"\n--- {desc} ---")
    t0 = time.time()
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=str(BASE_DIR))
    dur = time.time() - t0
    status = "PASS" if proc.returncode == 0 else "FAIL"
    print(f"  [{status}] {desc} ({dur:.2f}s, exit code {proc.returncode})")
    return proc.returncode, proc.stdout


def verify_quick() -> int:
    print("=" * 70)
    print("MAILGUARD AI: QUICK VERIFICATION SUITE")
    print("=" * 70)

    log_sections = []
    all_passed = True

    # 1. Model integrity
    if not check_model_integrity():
        all_passed = False
        log_sections.append("### 1. Model Integrity Check: FAILED")
    else:
        log_sections.append("### 1. Model Integrity Check: PASSED")

    # 2. Static frontend export
    rc, out = run_command([sys.executable, "scripts/build_frontend.py"], "Static Frontend Export")
    if rc != 0:
        all_passed = False
    log_sections.append(f"### 2. Static Frontend Export\n```\n{out}\n```")

    # 3. Targeted fast pytest suite
    test_files = [
        "tests/test_api_origin_safety.py",
        "tests/test_api.py",
        "tests/test_cors.py",
    ]
    rc_pytest, out_pytest = run_command([sys.executable, "-m", "pytest", "-v"] + test_files, "Targeted API & CORS Pytest")
    if rc_pytest != 0:
        all_passed = False
    log_sections.append(f"### 3. API & Security Tests\n```\n{out_pytest}\n```")

    # Write report
    report_content = f"# MailGuard AI Verification Report (Quick)\n\n"
    report_content += f"- **Mode:** `--quick`\n"
    report_content += f"- **Timestamp:** {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n"
    report_content += f"- **Overall Result:** {'PASSED' if all_passed else 'FAILED'}\n\n"
    report_content += "\n\n".join(log_sections) + "\n"
    REPORT_FILE.write_text(report_content, encoding="utf-8")
    print(f"\nReport written to: {REPORT_FILE}")

    return 0 if all_passed else 1


def verify_full() -> int:
    print("=" * 70)
    print("MAILGUARD AI: FULL REGRESSION VERIFICATION SUITE")
    print("=" * 70)

    log_sections = []
    all_passed = True

    # 1. Model integrity
    if not check_model_integrity():
        all_passed = False
        log_sections.append("### 1. Model Integrity Check: FAILED")
    else:
        log_sections.append("### 1. Model Integrity Check: PASSED")

    # 2. Static frontend export
    rc, out = run_command([sys.executable, "scripts/build_frontend.py"], "Static Frontend Export")
    if rc != 0:
        all_passed = False
    log_sections.append(f"### 2. Static Frontend Export\n```\n{out}\n```")

    # 3. Full pytest suite
    rc_pytest, out_pytest = run_command([sys.executable, "-m", "pytest", "-v"], "Full Pytest Suite (163 Tests)")
    if rc_pytest != 0:
        all_passed = False
    log_sections.append(f"### 3. Full Pytest Suite\n```\n{out_pytest}\n```")

    # 4. Split architecture verification (Vercel emulator, OCR, cold-start, Axe)
    rc_split, out_split = run_command([sys.executable, "scripts/verify_split_architecture.py"], "Split Architecture Playwright Verification")
    if rc_split != 0:
        all_passed = False
    log_sections.append(f"### 4. Split Architecture Verification\n```\n{out_split}\n```")

    # Write report
    report_content = f"# MailGuard AI Verification Report (Full)\n\n"
    report_content += f"- **Mode:** `--full`\n"
    report_content += f"- **Timestamp:** {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n"
    report_content += f"- **Overall Result:** {'PASSED' if all_passed else 'FAILED'}\n\n"
    report_content += "\n\n".join(log_sections) + "\n"
    REPORT_FILE.write_text(report_content, encoding="utf-8")
    print(f"\nReport written to: {REPORT_FILE}")

    return 0 if all_passed else 1


def main():
    parser = argparse.ArgumentParser(description="MailGuard AI verification suite.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--quick", action="store_true", help="Run fast targeted sanity checks")
    group.add_argument("--full", action="store_true", help="Run full comprehensive regression and E2E checks")
    args = parser.parse_args()

    if args.full:
        sys.exit(verify_full())
    else:
        sys.exit(verify_quick())


if __name__ == "__main__":
    main()
