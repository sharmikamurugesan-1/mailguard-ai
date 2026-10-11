# AGENTS.md - MailGuard AI Agent Guidelines & Operating Boundaries

## 1. Mission & System Overview
MailGuard AI is a production-grade, privacy-first email threat detection system featuring:
* **Backend:** Python 3.12 + Flask + Gunicorn on Render, serving a calibrated Linear SVM ML model with heuristic email/URL analysis and rate limiting.
* **Frontend:** Static ES6+ Vanilla JavaScript on Vercel (`frontend/`), communicating with Render cross-origin via strict CORS allowlisting.
* **Privacy Contract:** Zero email text, subject lines, or image attachments are ever stored or logged on the server. Scan history is preserved strictly client-side in browser IndexedDB. Image OCR (Tesseract.js) and QR scanning (jsQR) run 100% in-browser via Web Workers.

---

## 2. Operating Rules for AI Agents

### Prohibited Actions (Never Permitted without Explicit User Confirmation)
1. **Never guess, invent, or hardcode production URLs.**
   - All production URLs must be provided explicitly by the user from their cloud dashboards.
   - Never report a service as "deployed" without a real HTTP 200 response from the actual live URL.
2. **Never push to git remotes or merge to `master`.**
   - The user executes git push and branch merges. Agents operate on branch `v2/redesign` locally.
3. **Never modify billing plans or trigger paid changes.**
4. **Never send load against production before GATE 3.**
   - Never send automated load against Vercel or third-party infrastructure.
5. **Never log or persist user email content.**

### Permitted Actions (Autonomous)
1. Local code fixes for verified bugs and blockers.
2. Adding and executing tests in `tests/` and `scripts/`.
3. Updating documentation, model cards, benchmarks, and reports.
4. Committing changes locally on branch `v2/redesign`.

---

## 3. Evidence & Reporting Standards
1. **Raw Evidence Only:** Always paste real, unedited terminal output or verbatim excerpts from `reports/verify_latest.md`.
2. **Measurement Tagging:** Every latency, throughput, memory, or capacity number must be explicitly tagged:
   - `[LOCAL]` - Measured on the local development machine.
   - `[LOCAL-0.1CPU-EMULATED]` - Measured in a CPU/memory throttled container emulating Render Free tier.
   - `[LIVE]` - Measured directly against the live deployed URL.
   Never blend or cross-cite these environments.
3. **State Tracking:** Maintain `reports/launch_state.md` updated after every stage and gate.

---

## 4. Launch Stages & Gate Architecture
* **STAGE A: PRE-DEPLOY (Local):** Run `verify_all.py --full`, review Gunicorn configuration for 512 MB, execute adversarial robustness tests, configure dynamic rate limits, and construct the capacity model.
* **GATE 1:** User pushes, deploys Render backend, and provides live Render URL.
* **STAGE B: BACKEND LIVE [LIVE]:** Run live smoke tests, HTTPS verification, CORS preflight checks, configure frontend origin via `scripts/set_api_origin.py`.
* **GATE 2:** User deploys Vercel frontend, sets Render CORS origin, and provides live Vercel URL.
* **STAGE C: LIVE WEBSITE CHECK [LIVE]:** Full Playwright regression and Axe accessibility audit on the live Vercel site.
* **GATE 3:** User approves targeted live load test cap (e.g. 3 rps, 60s, <= 200 reqs).
* **STAGE D: LIVE CAPACITY VALIDATION [LIVE]:** Execute approved load test against live backend, compare with capacity model.
