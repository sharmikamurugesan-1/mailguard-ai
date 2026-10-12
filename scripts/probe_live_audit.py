"""Audit probe for live MailGuard AI deployments (Render backend and Vercel frontends)."""

import json
import urllib.request
import urllib.error
import ssl

ctx = ssl.create_default_context()

def check_render_backend():
    base_url = "https://mailguard-ai-6ljt.onrender.com"
    results = {}
    
    # 1. Health
    try:
        req = urllib.request.Request(f"{base_url}/api/health", headers={"User-Agent": "MailGuardAuditor/1.0"})
        with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
            body = json.loads(r.read().decode())
            results["health"] = {"status": r.status, "body": body}
    except Exception as e:
        results["health"] = {"error": str(e)}

    # 2. Model Info
    try:
        req = urllib.request.Request(f"{base_url}/api/model-info", headers={"User-Agent": "MailGuardAuditor/1.0"})
        with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
            body = json.loads(r.read().decode())
            results["model_info"] = {"status": r.status, "body": body}
    except Exception as e:
        results["model_info"] = {"error": str(e)}

    # 3. CORS Preflight
    try:
        req = urllib.request.Request(
            f"{base_url}/api/analyze",
            headers={
                "Origin": "https://mailguard-aafw79uqj-sharmikamurugesan-1.vercel.app",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
                "User-Agent": "MailGuardAuditor/1.0"
            },
            method="OPTIONS"
        )
        with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
            results["cors_preflight"] = {
                "status": r.status,
                "allow_origin": r.headers.get("Access-Control-Allow-Origin"),
                "allow_methods": r.headers.get("Access-Control-Allow-Methods"),
                "allow_headers": r.headers.get("Access-Control-Allow-Headers")
            }
    except Exception as e:
        results["cors_preflight"] = {"error": str(e)}

    # 4. Safe POST /api/analyze
    try:
        payload = json.dumps({"text": "Hello, this is a routine project status update.", "options": {"scan_urls": False}}).encode()
        req = urllib.request.Request(
            f"{base_url}/api/analyze",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Origin": "https://mailguard-aafw79uqj-sharmikamurugesan-1.vercel.app",
                "User-Agent": "MailGuardAuditor/1.0"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
            body = json.loads(r.read().decode())
            results["analyze_post"] = {
                "status": r.status,
                "classification": body.get("classification"),
                "risk_score": body.get("risk_score"),
                "confidence": body.get("confidence")
            }
    except Exception as e:
        results["analyze_post"] = {"error": str(e)}

    return results


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Prevent following redirect


def check_vercel_frontend():
    opener = urllib.request.build_opener(NoRedirectHandler)
    results = {}
    
    # 1. Preview Deployment
    url1 = "https://mailguard-aafw79uqj-sharmikamurugesan-1.vercel.app/#/home"
    try:
        req = urllib.request.Request(url1, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        resp = opener.open(req, timeout=15)
        results["preview_deployment"] = {"status": resp.status, "headers": dict(resp.headers)}
    except urllib.error.HTTPError as e:
        results["preview_deployment"] = {
            "status": e.code,
            "location": e.headers.get("Location"),
            "x_vercel_id": e.headers.get("x-vercel-id"),
            "server": e.headers.get("server")
        }
    except Exception as e:
        results["preview_deployment"] = {"error": str(e)}

    # 2. Production Domain
    url2 = "https://mailguard-ai.vercel.app"
    try:
        req = urllib.request.Request(url2, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        resp = opener.open(req, timeout=15)
        results["production_domain"] = {"status": resp.status, "headers": dict(resp.headers)}
    except urllib.error.HTTPError as e:
        results["production_domain"] = {
            "status": e.code,
            "location": e.headers.get("Location"),
            "x_vercel_id": e.headers.get("x-vercel-id"),
            "server": e.headers.get("server")
        }
    except Exception as e:
        results["production_domain"] = {"error": str(e)}

    return results


if __name__ == "__main__":
    report = {
        "backend": check_render_backend(),
        "frontend": check_vercel_frontend()
    }
    print(json.dumps(report, indent=2))
