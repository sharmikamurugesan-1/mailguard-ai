"""Locust load testing scenario for MailGuard AI backend API.

Usage:
    # Interactive Web UI:
    locust -f locustfile.py --host=http://127.0.0.1:5000

    # Headless 1000-user concurrency test:
    locust -f locustfile.py --headless --host=http://127.0.0.1:5000 -u 1000 -r 50 --run-time 1m --csv=reports/locust_1000
"""

import os
import random
from locust import HttpUser, task, between, events

SHORT_PAYLOAD = {
    "text": "Quick sync tomorrow at 10am regarding quarterly budget.",
    "options": {"scan_urls": True, "sensitivity": "medium"}
}

TYPICAL_PAYLOAD = {
    "text": (
        "Subject: Invoice INV-2026-9481\n\n"
        "Please find attached invoice INV-2026-9481 for consulting services rendered in September 2026. "
        "The total balance due is $4,250.00 payable within 14 business days. You can review your account statement "
        "online at https://billing.example.test/portal?id=9481. If you have questions regarding this billing statement, "
        "contact our accounts department directly. Thank you for your prompt payment."
    ),
    "options": {"scan_urls": True, "sensitivity": "medium"}
}

PHISHING_PAYLOAD = {
    "text": (
        "Subject: URGENT: Your PayPal Account Has Been Suspended\n\n"
        "Dear Customer,\n"
        "We detected suspicious sign-in activity on your account. To prevent unauthorized charges, "
        "verify your credentials within 24 hours at http://paypa1-security-verification.servehttp.com/login.\n"
        "Failure to do so will result in permanent account termination.\n\n"
        "PayPal Security Team"
    ),
    "options": {"scan_urls": True, "sensitivity": "high"}
}

LARGE_PAYLOAD = {
    "text": (
        "Subject: Corporate Security Policy Update - Mandatory Review\n\n"
        + ("Please be advised that unauthorized login attempts were detected from external IP 198.51.100.22. "
           "Verify your credentials immediately by visiting https://secure-auth.security-check.example.test/login. "
           "Failure to respond within 24 hours will result in permanent suspension of access.\n\n" * 45)
    )[:18000],
    "options": {"scan_urls": True, "sensitivity": "medium"}
}


class MailGuardUser(HttpUser):
    """Simulates realistic concurrent user behavior across MailGuard AI endpoints."""

    wait_time = between(
        float(os.getenv("LOCUST_WAIT_MIN", "1.0")),
        float(os.getenv("LOCUST_WAIT_MAX", "3.0"))
    )

    def on_start(self):
        """Seed random client IP to simulate distributed user traffic."""
        self.client_ip = f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}"
        self.headers = {
            "Content-Type": "application/json",
            "X-Forwarded-For": self.client_ip,
            "User-Agent": "LocustMailGuardBenchmark/1.0"
        }

    @task(2)
    def check_health(self):
        """Health check endpoint probe."""
        with self.client.get("/api/health", headers=self.headers, catch_response=True) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"Health check failed with HTTP {resp.status_code}")

    @task(1)
    def check_model_info(self):
        """Model info metadata endpoint probe."""
        with self.client.get("/api/model-info", headers=self.headers, catch_response=True) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"Model-info check failed with HTTP {resp.status_code}")

    @task(10)
    def analyze_typical_email(self):
        """Primary traffic path: typical business/personal email payload."""
        with self.client.post("/api/analyze", json=TYPICAL_PAYLOAD, headers=self.headers, catch_response=True) as resp:
            if resp.status_code == 200:
                data = resp.json()
                if "classification" in data and "confidence" in data:
                    resp.success()
                else:
                    resp.failure("Response missing required schema fields")
            elif resp.status_code == 429:
                resp.failure("Rate limited (HTTP 429)")
            else:
                resp.failure(f"HTTP {resp.status_code}: {resp.text[:100]}")

    @task(3)
    def analyze_short_text(self):
        """Short SMS or single-sentence email inspection."""
        with self.client.post("/api/analyze", json=SHORT_PAYLOAD, headers=self.headers, catch_response=True) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"HTTP {resp.status_code}")

    @task(4)
    def analyze_phishing_email(self):
        """Suspicious/phishing email with URL scanning active."""
        with self.client.post("/api/analyze", json=PHISHING_PAYLOAD, headers=self.headers, catch_response=True) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"HTTP {resp.status_code}")

    @task(1)
    def analyze_large_email(self):
        """Stress payload: long newsletter or multi-hop forwarding chain."""
        with self.client.post("/api/analyze", json=LARGE_PAYLOAD, headers=self.headers, catch_response=True) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"HTTP {resp.status_code}")
