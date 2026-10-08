# MailGuard AI - Manual Test Checklist & QA Protocol

This document outlines the test cases and verification procedures for the MailGuard AI frontend UI, backend API, accessibility, and cold-start resilience.

---

## 1. Test Matrix & Scenarios

| Test Case | Description | Input Data | Expected Result | Verified Status |
| :--- | :--- | :--- | :--- | :---: |
| **TC-01: Page Load & Health** | User visits `/` on browser | `GET http://127.0.0.1:5000/` | HTTP 200 OK, Status badge reads "Server Online" with green dot. Model transparency section populated. | **VERIFIED** |
| **TC-02: Spam Example** | Click "Spam Sample" & Submit | PayPal phishing template | Verdict "Likely spam", red border & icon, High Risk badge, calibrated confidence > 95%, top spam signals shown. | **VERIFIED** |
| **TC-03: Legitimate (Ham) Example** | Click "Legitimate Sample" & Submit | Weekly sync meeting template | Verdict "Likely legitimate", green border & icon, Low Risk badge, confidence > 95%, negative signals shown. Never says "safe". | **VERIFIED** |
| **TC-04: Borderline / Review Example** | Click "Borderline Sample" & Submit | Corporate legal invoice template | Verdict reflects model score; amber warning if near boundary; Enron-era age notice rendered. | **VERIFIED** |
| **TC-05: Empty Body Validation** | Submit form with empty body | Subject: "Test", Body: `""` | Inline client validation: "Email body is required to perform spam classification." Zero API calls made. | **VERIFIED** |
| **TC-06: Whitespace Only Validation** | Submit form with whitespace only | Subject: "Test", Body: `"   \n\t  "` | Inline client validation error displayed. Zero API calls made. | **VERIFIED** |
| **TC-07: Oversized Input Validation** | Exceed 20,000 char limit | Body text $> 20,000$ characters | Char counter turns red; client validation stops submission before HTTP transfer. | **VERIFIED** |
| **TC-08: Clear Button** | Click "Clear" button | Existing subject/body inputs | Clears inputs, resets char counter to 0/20,000, clears errors, hides result card. | **VERIFIED** |
| **TC-09: Model & Data Transparency** | Click details accordion | `GET /api/model-info` | Shows architecture, TF-IDF vectorizer, training corpus, GPL-3.0 license, test metrics, and limitations list. | **VERIFIED** |
| **TC-10: Cold-Start Waking Banner** | Delay `/api/predict` by 8 seconds | Simulated via `scripts/dev_slow_proxy.py --delay 8` | After 5.0s, waking banner appears: *"Server is waking up (free hosting)..."*. Analyze button remains disabled. | **VERIFIED** |
| **TC-11: Timeout & Retry** | Request exceeds timeout | Simulated network timeout / drop | AbortController fires, automatically executes 1 retry. On terminal failure, displays error with "Try again" button. | **VERIFIED** |
| **TC-12: Mobile Responsiveness** | Viewport at 375px width | DevTools mobile device emulation | Grid stacks vertically, buttons wrap cleanly, signal bars and metrics legible without horizontal overflow. | **VERIFIED** |
| **TC-13: Accessibility & Contrast** | Screen reader & keyboard | Tab navigation & ARIA attributes | Form controls have labels; results use `aria-live="polite"`; color contrast $\ge 4.5:1$ (WCAG AA). | **VERIFIED** |
| **TC-14: Security / Zero XSS** | Attempt script injection in body | `<script>alert(1)</script>` | Inserted purely via `textContent` and `createElement`; zero script execution; zero innerHTML. | **VERIFIED** |

---

## 2. Cold-Start Verification Instructions

To reproduce the cold-start and latency simulation locally without modifying production code:

1. **Start Backend Server**:
   ```powershell
   .\.venv\Scripts\python.exe -m src.app
   ```
2. **Start Dev Slow Proxy**:
   ```powershell
   .\.venv\Scripts\python.exe scripts/dev_slow_proxy.py --delay 8 --port 5050
   ```
3. **Open Browser**:
   Navigate to `http://127.0.0.1:5050/`. Click "Spam Sample" and "Analyze Email".
4. **Observe**:
   - The button shows "Analyzing..." with a spinner.
   - At exactly $t = 5.0\text{s}$, the blue alert banner appears: *"Server is waking up (free hosting). First request can take up to ~60s. Please wait..."*.
   - At $t = 8.0\text{s}$, the response arrives, the banner vanishes, and the result card renders cleanly.
