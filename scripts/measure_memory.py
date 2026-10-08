"""Measure process Resident Set Size (RSS) memory consumption on model load and inference."""

import os
import sys
import psutil
from typing import Dict, Any

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def measure_memory_profile() -> Dict[str, Any]:
    process = psutil.Process(os.getpid())
    
    # Baseline before loading app or heavy ML libraries
    baseline_rss_mb = process.memory_info().rss / (1024 * 1024)
    
    # 1. Load app and scikit-learn model
    from app import app
    client = app.test_client()
    after_load_rss_mb = process.memory_info().rss / (1024 * 1024)
    
    # 2. Send 20 varied prediction requests
    samples = [
        {"subject": f"Project Update {i}", "body": f"Meeting notes regarding Q3 milestones and deliverables number {i}."}
        if i % 2 == 0 else
        {"subject": f"URGENT CLAIM PRIZE {i}", "body": f"Click now for free cash rewards and pharmaceuticals at http://prize-{i}.example.com!"}
        for i in range(20)
    ]
    
    for payload in samples:
        resp = client.post("/api/predict", json=payload)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    
    after_20_preds_rss_mb = process.memory_info().rss / (1024 * 1024)
    
    # Render Free tier limits
    RENDER_FREE_LIMIT_MB = 512.0
    
    print("=" * 65)
    print("MAILGUARD AI - PROCESS MEMORY (RSS) PROFILE")
    print("=" * 65)
    print(f"Baseline Python Runtime RSS:        {baseline_rss_mb:.2f} MB")
    print(f"After App & Model Load RSS:         {after_load_rss_mb:.2f} MB")
    print(f"After 20 Inferences RSS:            {after_20_preds_rss_mb:.2f} MB")
    print(f"Net Model & Runtime Footprint:      {after_20_preds_rss_mb - baseline_rss_mb:.2f} MB")
    print("-" * 65)
    print(f"Render Free Plan RAM Allocation:    {RENDER_FREE_LIMIT_MB:.1f} MB (0.1 CPU)")
    print(f"Single Worker RAM Consumption:      {after_20_preds_rss_mb:.2f} MB ({after_20_preds_rss_mb / RENDER_FREE_LIMIT_MB * 100:.1f}% of limit)")
    print(f"Single Worker Remaining Headroom:   {RENDER_FREE_LIMIT_MB - after_20_preds_rss_mb:.2f} MB")
    print("-" * 65)
    
    two_workers_est = after_20_preds_rss_mb * 2
    print(f"Two Separate Worker Processes Est:  {two_workers_est:.2f} MB ({two_workers_est / RENDER_FREE_LIMIT_MB * 100:.1f}% of limit)")
    print("=" * 65)
    
    return {
        "baseline_rss_mb": baseline_rss_mb,
        "after_load_rss_mb": after_load_rss_mb,
        "after_20_preds_rss_mb": after_20_preds_rss_mb,
        "render_limit_mb": RENDER_FREE_LIMIT_MB,
        "pct_of_limit": after_20_preds_rss_mb / RENDER_FREE_LIMIT_MB * 100
    }

if __name__ == "__main__":
    measure_memory_profile()
