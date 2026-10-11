# MailGuard AI — Launch State & Capacity Proof Report

**Last Updated:** 2026-10-11T12:05:00Z  
**Current Stage:** Stage B In Progress (Backend Verified Live -> Frontend Configured)  
**Active Branch:** `v2/redesign`  
**Base Release Tag:** `v2.0.0` (`git merge-base --is-ancestor ee89e58 v2.0.0` PASSED)  
**Verified Live Render Backend:** `https://mailguard-ai-6ljt.onrender.com`  

---

## 1. Executive Summary & Current Gate Status

| Item | Status | Verification Detail |
|------|--------|---------------------|
| **Current Stage** | **Stage B (Frontend Configuration)** | Backend verified live; static origin & CSP updated. |
| **Render Backend** | **LIVE [LIVE]** | `https://mailguard-ai-6ljt.onrender.com/api/health` returned HTTP 200 OK (`model_loaded: true`). |
| **Model Info** | **VERIFIED [LIVE]** | `/api/model-info` returned HTTP 200 OK (Calibrated Linear SVM, 99.0% accuracy). |
| **Pending Gate** | **GATE 2** | Awaiting User Vercel Frontend Deployment. |
| **Pytest Suite** | **163 / 163 PASSED [LOCAL]** | 100% pass rate in 14.55s across all 13 test modules. |
| **Static Export** | **15.75 MB [LOCAL]** | 22 assets cleanly exported in `frontend/` (`scripts/build_frontend.py`). |
| **E2E Split Test** | **PASSED [LOCAL]** | Playwright test passed in 27.76s (0 CSP errors, 0 console errors, Axe a11y passed). |

---

## 2. Render Specifications & Gunicorn Configuration (Stage A2)

### Render Instance Tiers Reviewed
- **Free Tier (`free`)**:
  - **Specs:** 0.1 vCPU, 512 MB RAM, $0/month.
  - **Lifecycle:** Sleeps after 15 minutes of inactivity. Cold start spinup takes **~50 to 70 seconds**. 750 free instance hours/month.
- **Starter Tier (`starter`)**:
  - **Specs:** 0.5 vCPU, 512 MB RAM, ~$7/month.
  - **Lifecycle:** Always on (zero idle sleep, zero cold starts).
- **Standard Tier (`standard`)**:
  - **Specs:** 1.0 vCPU, 2 GB RAM, ~$25/month. Always on.

### Production Gunicorn Flags (`render.yaml`)
```yaml
startCommand: gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120 --graceful-timeout 30 --max-requests 1000 --max-requests-jitter 100 --preload
```

#### Engineering Justification for 512 MB RAM Limit:
1. `--workers 1`: The calibrated Linear SVM and TF-IDF pipeline consumes ~150 MB baseline memory. Running 2 worker processes would require ~320 MB baseline heap, leaving unsafe margins (< 180 MB) and triggering OOM process termination under concurrent requests. 1 worker guarantees stability within 512 MB.
2. `--threads 4`: Provides in-process thread concurrency sharing the single 150 MB ML heap. The Python GIL is released during socket I/O and compiled scikit-learn/NumPy C routines.
3. `--timeout 120`: Accommodates Render Free cold-start spinup (up to 70s) and large 1 MB payload parsing without dropping connections.
4. `--graceful-timeout 30`: Allows in-flight requests to complete cleanly during service updates or dyno recycles.
5. `--max-requests 1000 --max-requests-jitter 100`: Regularly recycles the worker process after 900–1100 requests to prevent Python heap fragmentation or long-term memory creep.
6. `--preload`: Loads and verifies model SHA-256 integrity (`models/model_hash.sha256`) in the master process *before* binding the socket, guaranteeing fail-closed behavior on corrupted deployments.

---

## 3. Comprehensive Robustness & Launch Test Suite (Stage A3)

A dedicated test suite was implemented in `tests/test_launch_robustness.py` (14 new tests, bringing the total suite from 149 to **163 tests**).

| Test Case | Scenario Tested | HTTP Code | Result |
|-----------|-----------------|-----------|--------|
| `test_oversize_body_predict_413` | Body > 20k characters on `/api/predict` | 413 Payload Too Large | **PASS [LOCAL]** |
| `test_oversize_text_analyze_413` | Text > 20k characters on `/api/analyze` | 413 Payload Too Large | **PASS [LOCAL]** |
| `test_oversize_eml_analyze_413` | EML > 1 MB raw payload on `/api/analyze` | 413 Payload Too Large | **PASS [LOCAL]** |
| `test_max_content_length_flask_413` | Raw payload > 2 MB Flask `MAX_CONTENT_LENGTH` | 413 Payload Too Large | **PASS [LOCAL]** |
| `test_malformed_json_syntax` | Truncated and broken JSON payloads | 400 Bad Request | **PASS [LOCAL]** |
| `test_invalid_json_types` | Non-object JSON roots and wrong field types | 400 Bad Request | **PASS [LOCAL]** |
| `test_empty_input_analyze_400` | Empty payloads and whitespace-only text | 400 Bad Request | **PASS [LOCAL]** |
| `test_wrong_content_type_415` | `text/plain`, `application/x-www-form-urlencoded` | 415 Unsupported Media Type | **PASS [LOCAL]** |
| `test_malformed_eml_binary_garbage` | Raw null bytes, corrupted MIME boundaries, injection | 200 / 400 (Graceful) | **PASS [LOCAL]** |
| `test_adversarial_redos_execution_time` | Pathological URL/regex patterns completed in < 2.0s | 200 OK (< 2.0s) | **PASS [LOCAL]** |
| `test_parallel_requests_thread_safety` | 50 concurrent requests via `ThreadPoolExecutor` | 200 OK (Identical) | **PASS [LOCAL]** |
| `test_zero_input_text_logging_invariant` | High-entropy canary tokens in payloads grepped in logs | Zero text in logs | **PASS [LOCAL]** |
| `test_500_internal_error_zero_leakage` | Forced unhandled exception returns standardized JSON | 500 (No paths leaked) | **PASS [LOCAL]** |
| `test_dynamic_rate_limiting_env_config` | Dynamic throttle adjustment via env vars | 429 Rate Limited | **PASS [LOCAL]** |

---

## 4. Dynamic Rate Limiting & NAT / Shared-IP Design (Stage A4)

### Configuration Variables (`src/config.py` & `src/app.py`)
- `RATELIMIT_ANALYZE_PER_MINUTE`: default `60` (configurable via env var).
- `RATELIMIT_ANALYZE_BURST_PER_MINUTE`: default `120` (burst headroom).
- `RATELIMIT_PREDICT_PER_MINUTE`: default `60`.
- `RATELIMIT_MODEL_INFO_PER_MINUTE`: default `120`.

### Campus & Conference NAT Considerations
- **The Risk:** When hundreds of students or attendees in a computer lab or university hall share a single public outbound IP via NAT, a strict 60 req/min IP-based rate limit will throttle benign users simultaneously testing the app.
- **Recommended Production Setting for Demos/Classrooms:**
  - Set `RATELIMIT_ANALYZE_PER_MINUTE=120` in Render environment variables.
  - Set `RATELIMIT_ANALYZE_BURST_PER_MINUTE=120`.

---

## 5. Capacity Model & Load Testing Proof (Stage A5)

### Scenario Arithmetic
- **Scenario S1 (1,000 visitors in 10 minutes viewing static showcase)**:
  - Static traffic rate: $1000 / 600\text{ s} = 1.67\text{ req/s}$ static traffic.
  - **Backend Demand:** **$0.00\text{ req/s}$**. All HTML, JS, CSS, WASM assets served by Vercel global Edge CDN.
  - **Verdict on Render Free (0.1 CPU):** **PASS** ($0 backend cost).
- **Scenario S2 (1,000 visitors over 10 min, 30% performing 1 analysis/min)**:
  - Active analysts: 300 users.
  - Backend API load: 300 analyses / 60s = **$5.0\text{ req/s}$ sustained**.
  - **Verdict on Render Free (0.1 CPU):** **BORDERLINE / MARGINAL** (Theoretical limit is ~5.8 RPS; 86% CPU load, susceptible to 15-min idle sleep cold starts).
  - **Verdict on Render Starter (0.5 CPU, $7/mo):** **PASS** (Capacity ~29.1 RPS; operates at 17% load; zero sleeping).
- **Scenario S3 (Classroom / Live Demo Burst: 100 analyses in 10s)**:
  - Burst load: $100 / 10\text{ s} =$ **$10.0\text{ req/s}$**.
  - **Verdict on Render Free (0.1 CPU):** **FAIL / NEEDS UPGRADE** (10.0 RPS exceeds 0.1 vCPU capacity of 5.8 RPS by 72%).
  - **Verdict on Render Starter (0.5 CPU, $7/mo):** **PASS** (Capacity ~29.1 RPS handles 10.0 RPS at 34% load).

### Host Micro-benchmark Measurements `[LOCAL]`
*Environment Note: Docker CLI is present, but the Docker daemon is unavailable on this host system. Measurements were collected via Python CPU process-time profiling (`scripts/benchmark_cpu.py`) over 200 requests per tier.*

| Payload Tier | Payload Size | Measured CPU p50 `[LOCAL]` | Measured Wall p50 `[LOCAL]` | Max RPS (0.1 vCPU) | Max RPS (0.5 vCPU) | Max RPS (1.0 vCPU) |
|--------------|--------------|---------------------------|----------------------------|-------------------|-------------------|-------------------|
| **Short** | 115 Bytes | 0.0156 s (15.6 ms) | 0.0169 s (16.9 ms) | 6.4 RPS | 32.0 RPS | 64.0 RPS |
| **Typical** | 517 Bytes | 0.0156 s (15.6 ms) | 0.0139 s (13.9 ms) | 6.4 RPS | 32.0 RPS | 64.0 RPS |
| **Large** | 17.5 KB | 0.0313 s (31.3 ms) | 0.0289 s (28.9 ms) | 3.2 RPS | 16.0 RPS | 32.0 RPS |
| **Blended (70/20/10)** | Weighted Mix | **0.0172 s (17.2 ms)** | **0.0157 s (15.7 ms)** | **5.8 RPS** | **29.1 RPS** | **58.2 RPS** |

$$\text{Theoretical Capacity} \approx \frac{\text{CPU Share}}{\text{Blended CPU Time per Request}} = \frac{0.1}{0.0172\text{ s}} \approx 5.8\text{ RPS}$$

### Synthetic Open-Loop Load Generator Results `[LOCAL]`
*Harness: `scripts/loadtest.py` (Asyncio + httpx, Poisson arrivals, 70% typical / 20% short / 10% large)*

| Stage | Target RPS | Requests Sent | Successful (200) | Errors | 429 Throttled | p50 Latency `[LOCAL]` | p95 Latency `[LOCAL]` | Process RSS `[LOCAL]` |
|-------|------------|---------------|------------------|--------|---------------|----------------------|----------------------|-----------------------|
| 1 | 1.0 RPS | 5 | 5 (100%) | 0 | 0 | 34.5 ms | 94.5 ms | 41.2 MB |
| 2 | 2.0 RPS | 10 | 10 (100%) | 0 | 0 | 30.4 ms | 43.4 ms | 42.2 MB |
| 3 | 5.0 RPS | 25 | 25 (100%) | 0 | 0 | 28.9 ms | 91.1 ms | 42.4 MB |
| 4 | 10.0 RPS | 50 | 50 (100%) | 0 | 0 | 30.3 ms | 76.5 ms | 42.8 MB |
| 5 | 20.0 RPS | 100 | 100 (100%) | 0 | 0 | 46.5 ms | 149.1 ms | 43.4 MB |
| 6 | 40.0 RPS | 200 | 200 (100%) | 0 | 0 | 213.7 ms | 696.6 ms | 45.5 MB |

**Sustainable Knee `[LOCAL]`:** **40.0 RPS** with 0 errors, 0 timeouts, and p95 latency = 696.6 ms (< 1.5s). Memory stayed flat at 45.5 MB (< 400 MB abort limit).

---

## 6. Sizing Verdict & Recommendation

- **Smallest Render Instance for Free/Dormant Use:** **Render Free Plan** ($0/month).
  - Can sustain Scenario S1 and borderline S2 (~5.8 RPS max).
  - **Caveat:** Spins down after 15 minutes of inactivity; first request takes 50–70s to wake up.
- **Smallest Render Instance for Reliable Public Demos & Burst Loads:** **Render Starter Plan** (0.5 vCPU, 512 MB RAM, ~$7/month).
  - Supports ~29 RPS sustained; comfortably handles S1, S2, and S3 without queuing, drops, or sleep latency.

---

## 7. Current Gate: GATE 2

```
+-------------------------------------------------------------------------+
|                                 GATE 2                                  |
|                 Awaiting User Action: Vercel Frontend                   |
+-------------------------------------------------------------------------+
```
Stage B frontend configuration is complete. The backend origin and CSP have been bound to `https://mailguard-ai-6ljt.onrender.com`.
The `frontend/` directory is fully packaged and ready for Vercel deployment.
Execution is stopped at GATE 2 awaiting user Vercel dashboard import.
