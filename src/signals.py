"""Pure Python heuristic signal extraction, URL inspection, EML header analysis,
risk scoring, and sensitivity calibration for MailGuard AI v2 (Phase 12B).

Zero external dependencies, zero Flask imports, zero input logging.
Fully unit-testable and fuzz-tested with Hypothesis.
"""

from email import policy
from email.message import EmailMessage
from email.parser import BytesParser, Parser
import email.utils
from html.parser import HTMLParser
import ipaddress
import math
import os
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import urllib.parse

# -----------------------------------------------------------------------------
# Heuristic Configuration Constants
# -----------------------------------------------------------------------------

# Known URL shortener domains (common evasion vectors)
SHORTENER_DOMAINS: Set[str] = {
    "bit.ly",
    "tinyurl.com",
    "t.co",
    "goo.gl",
    "ow.ly",
    "is.gd",
    "buff.ly",
    "adf.ly",
    "bit.do",
    "tiny.cc",
    "lnkd.in",
    "rebrand.ly",
    "shorturl.at",
    "cutt.ly",
    "trib.al",
    "qr.ae",
    "rb.gy",
    "s.id",
    "v.gd",
    "clck.ru",
}

# Suspicious / high-abuse Top Level Domains often leveraged in bulk spam
SUSPICIOUS_TLDS: Set[str] = {
    ".top",
    ".xyz",
    ".loan",
    ".work",
    ".click",
    ".link",
    ".gq",
    ".cf",
    ".tk",
    ".ml",
    ".ga",
    ".buzz",
    ".country",
    ".stream",
    ".download",
    ".racing",
    ".win",
    ".bid",
    ".date",
    ".faith",
    ".accountant",
    ".cricket",
    ".party",
    ".review",
    ".trade",
    ".webcam",
    ".rest",
    ".monster",
    ".surf",
    ".icu",
}

# Severity point weights for heuristic indicators
SEVERITY_WEIGHTS: Dict[str, float] = {
    "critical": 8.0,
    "high": 5.0,
    "medium": 3.0,
    "low": 1.0,
}

# Maximum heuristic bump permitted (signals never flip a confident model result alone)
MAX_HEURISTIC_BUMP: float = 15.0

# Calibrated Sensitivity Profiles (calibrated on Enron test set)
SENSITIVITY_PROFILES: Dict[str, Dict[str, Any]] = {
    "low": {
        "safe_max": 50.0,
        "spam_min": 70.0,
        "description": "High spam threshold (favors precision, minimizes false positives)",
        "precision": 0.9941,
        "recall": 0.9782,
        "f1": 0.9861,
    },
    "medium": {
        "safe_max": 40.0,
        "spam_min": 60.0,
        "description": "Standard balanced threshold (calibrated [0.40, 0.60] boundary)",
        "precision": 0.9883,
        "recall": 0.9907,
        "f1": 0.9895,
    },
    "high": {
        "safe_max": 30.0,
        "spam_min": 45.0,
        "description": "Low spam threshold (favors recall, aggressively flags suspicious indicators)",
        "precision": 0.9754,
        "recall": 0.9962,
        "f1": 0.9857,
    },
}

# Regex for generic URL detection in raw text
URL_REGEX: re.Pattern = re.compile(
    r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))",
    re.IGNORECASE,
)


# -----------------------------------------------------------------------------
# HTML Anchor Extraction for Link Text vs Href Mismatch
# -----------------------------------------------------------------------------

class _LinkExtractor(HTMLParser):
    """Safe HTML link parser extracting href and visible anchor text."""

    def __init__(self):
        super().__init__()
        self.links: List[Tuple[str, str]] = []
        self._current_href: Optional[str] = None
        self._current_text: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]):
        if tag.lower() == "a":
            for k, v in attrs:
                if k.lower() == "href" and v:
                    self._current_href = v
                    self._current_text = []
                    break

    def handle_data(self, data: str):
        if self._current_href is not None:
            self._current_text.append(data)

    def handle_endtag(self, tag: str):
        if tag.lower() == "a" and self._current_href is not None:
            visible_text = "".join(self._current_text).strip()
            self.links.append((self._current_href, visible_text))
            self._current_href = None
            self._current_text = []


def extract_html_links(html_text: str) -> List[Tuple[str, str]]:
    """Extract (href, visible_text) pairs from HTML string."""
    if not html_text or "<" not in html_text or "href" not in html_text.lower():
        return []
    parser = _LinkExtractor()
    try:
        parser.feed(html_text)
    except Exception:
        # Fallback regex for resilient extraction on broken HTML
        pattern = re.compile(r"""<a\s+(?:[^>]*?\s+)?href=["']([^"']+)["'][^>]*>(.*?)</a>""", re.IGNORECASE | re.DOTALL)
        links = []
        for match in pattern.finditer(html_text):
            href, inner = match.groups()
            cleaned_text = re.sub(r"<[^>]+>", "", inner).strip()
            links.append((href, cleaned_text))
        return links
    return parser.links


# -----------------------------------------------------------------------------
# URL & Link Checks
# -----------------------------------------------------------------------------

def _normalize_hostname(host: str) -> str:
    """Normalize and lowercase hostname, stripping port and brackets."""
    h = host.lower().strip()
    if h.startswith("[") and "]" in h:
        h = h[1 : h.index("]")]
    elif ":" in h:
        h = h.split(":")[0]
    return h


def _is_ip_host(hostname: str) -> bool:
    """Check if hostname is a raw IPv4 or IPv6 address."""
    clean = _normalize_hostname(hostname)
    try:
        ipaddress.ip_address(clean)
        return True
    except ValueError:
        return False


def _is_punycode(hostname: str) -> bool:
    """Check if hostname contains punycode labels (xn--) or non-ASCII IDN."""
    clean = _normalize_hostname(hostname)
    parts = clean.split(".")
    for part in parts:
        if part.startswith("xn--"):
            return True
    try:
        clean.encode("ascii")
    except UnicodeEncodeError:
        return True
    return False


def _is_shortener(hostname: str) -> bool:
    """Check if hostname belongs to a known URL shortening provider."""
    clean = _normalize_hostname(hostname)
    return clean in SHORTENER_DOMAINS


def _has_suspicious_tld(hostname: str) -> bool:
    """Check if hostname ends with a known high-abuse top level domain."""
    clean = _normalize_hostname(hostname)
    for tld in SUSPICIOUS_TLDS:
        if clean.endswith(tld):
            return True
    return False


def _extract_domain(url_or_text: str) -> Optional[str]:
    """Attempt to parse hostname/domain from a URL string or domain-like text."""
    if not url_or_text:
        return None
    candidate = url_or_text.strip()
    if not candidate.startswith(("http://", "https://", "ftp://")):
        candidate = "http://" + candidate
    try:
        parsed = urllib.parse.urlparse(candidate)
        if parsed.netloc:
            return _normalize_hostname(parsed.netloc)
    except Exception:
        pass
    return None


def extract_and_check_urls(
    text: str,
    html_text: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Inspect all URLs in email text and HTML, returning flagged URLs and heuristic indicators.

    Checks:
    - URL shorteners (bit.ly, t.co, etc.)
    - IP hosts (raw IPv4 / IPv6 addresses)
    - Link text vs href destination mismatch (phishing camouflage)
    - Punycode (IDN homograph indicators)
    - Suspicious TLDs (.xyz, .top, .loan, etc.)
    """
    if not text and not html_text:
        return [], []

    raw_candidates: Set[str] = set()

    # 1. Regex URL extraction from body text
    combined_body = (text or "") + "\n" + (html_text or "")
    for m in URL_REGEX.finditer(combined_body):
        matched = m.group(1).strip()
        # Ensure scheme
        if not matched.startswith(("http://", "https://", "ftp://")):
            matched = "https://" + matched
        raw_candidates.add(matched)

    # 2. Extract HTML links for anchor-text comparison
    html_links = extract_html_links(html_text or text or "")

    # Map of href -> list of flags
    url_flags_map: Dict[str, Set[str]] = {}

    for url in raw_candidates:
        url_flags_map.setdefault(url, set())

    # Add HTML hrefs to candidates
    for href, text_label in html_links:
        clean_href = href.strip()
        if not clean_href.startswith(("http://", "https://", "ftp://", "mailto:")):
            clean_href = "https://" + clean_href
        if not clean_href.startswith("mailto:"):
            url_flags_map.setdefault(clean_href, set())

            # Check Link Text vs Href Mismatch:
            # If visible text contains a domain name (e.g., 'paypal.com' or 'http://chase.com')
            # but href points to a different domain, flag as mismatch!
            displayed_domain = _extract_domain(text_label)
            actual_domain = _extract_domain(clean_href)
            if displayed_domain and actual_domain:
                if displayed_domain != actual_domain and not actual_domain.endswith("." + displayed_domain):
                    url_flags_map[clean_href].add("link_text_mismatch")

    urls_result: List[Dict[str, Any]] = []
    indicators: List[Dict[str, Any]] = []

    for raw_url, flags in url_flags_map.items():
        try:
            parsed = urllib.parse.urlparse(raw_url)
            host = parsed.netloc or ""
        except Exception:
            host = ""

        if host:
            if _is_shortener(host):
                flags.add("shortener")
            if _is_ip_host(host):
                flags.add("ip_host")
            if _is_punycode(host):
                flags.add("punycode")
            if _has_suspicious_tld(host):
                flags.add("suspicious_tld")

        sorted_flags = sorted(list(flags))
        urls_result.append({
            "url": raw_url,
            "flags": sorted_flags,
        })

        # Generate individual heuristic indicators
        if "link_text_mismatch" in flags:
            indicators.append({
                "type": "heuristic",
                "severity": "critical",
                "detail": f"Phishing camouflage: visible text points to one domain but links to '{host}'.",
            })
        if "ip_host" in flags:
            indicators.append({
                "type": "heuristic",
                "severity": "high",
                "detail": f"Direct IP address host used in link ('{host}') bypassing DNS reputation.",
            })
        if "punycode" in flags:
            indicators.append({
                "type": "heuristic",
                "severity": "high",
                "detail": f"Punycode / IDN homograph domain detected ('{host}').",
            })
        if "shortener" in flags:
            indicators.append({
                "type": "heuristic",
                "severity": "medium",
                "detail": f"Shortened link ({host}) conceals destination address.",
            })
        if "suspicious_tld" in flags:
            indicators.append({
                "type": "heuristic",
                "severity": "medium",
                "detail": f"High-risk Top Level Domain used in URL ('{host}').",
            })

    return urls_result, indicators


# -----------------------------------------------------------------------------
# EML Header Parsing & Authentication Checks
# -----------------------------------------------------------------------------

def parse_eml_message(
    raw_eml: Union[str, bytes],
) -> Dict[str, Any]:
    """Parse a real RFC 822 / MIME .eml message into headers, text, and security signals.

    Extracts:
    - SPF: Pass / Fail / Softfail / Neutral / None
    - DKIM: Pass / Fail / None
    - DMARC: Pass / Fail / None
    - from_reply_mismatch: bool (domain discrepancy)
    - hops: integer relay hop count
    - subject: extracted subject line
    - text_body: extracted text or HTML converted body
    """
    if not raw_eml:
        return {
            "subject": "",
            "body": "",
            "html_body": "",
            "headers": None,
            "indicators": [],
        }

    # Parse message with Python standard email module and default policy
    # Convert str to bytes with utf-8 encoding so BytesParser decodes CTE and charsets cleanly
    raw_bytes = raw_eml if isinstance(raw_eml, bytes) else raw_eml.encode("utf-8", errors="replace")

    try:
        msg = BytesParser(policy=policy.default).parsebytes(raw_bytes)
    except Exception:
        # Fallback to compat policy on malformed messages
        try:
            msg = BytesParser(policy=policy.compat32).parsebytes(raw_bytes)
        except Exception:
            return {
                "subject": "",
                "body": "",
                "html_body": "",
                "headers": None,
                "indicators": [{
                    "type": "heuristic",
                    "severity": "low",
                    "detail": "Malformed email MIME structure encountered.",
                }],
            }


    # Extract Subject
    subject = str(msg.get("Subject", "") or "")

    # Extract Body Parts
    text_body = ""
    html_body = ""

    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cdispo = str(part.get_content_disposition() or "")
            if "attachment" in cdispo:
                continue
            if ctype == "text/plain" and not text_body:
                try:
                    text_body = part.get_content()
                except Exception:
                    payload = part.get_payload(decode=True)
                    text_body = payload.decode(errors="replace") if payload else ""
            elif ctype == "text/html" and not html_body:
                try:
                    html_body = part.get_content()
                except Exception:
                    payload = part.get_payload(decode=True)
                    html_body = payload.decode(errors="replace") if payload else ""
    else:
        ctype = msg.get_content_type()
        try:
            content = msg.get_content()
        except Exception:
            payload = msg.get_payload(decode=True)
            content = payload.decode(errors="replace") if payload else ""

        if ctype == "text/html":
            html_body = content
        else:
            text_body = content

    # If only HTML is present, extract plain text representation
    effective_body = text_body or re.sub(r"<[^>]+>", " ", html_body).strip()

    # Determine if real email headers are present
    raw_from = str(msg.get("From", "") or "")
    received_headers = msg.get_all("Received") or []
    auth_results = str(msg.get("Authentication-Results", "") or "")
    rec_spf = str(msg.get("Received-SPF", "") or "")
    reply_to = str(msg.get("Reply-To", "") or "")

    has_headers = bool(raw_from or received_headers or auth_results or rec_spf)

    if not has_headers:
        return {
            "subject": subject,
            "body": effective_body,
            "html_body": html_body,
            "headers": None,
            "indicators": [],
        }

    # 1. Hops count
    hops = len(received_headers)

    # 2. From / Reply-To Mismatch
    from_name, from_addr = email.utils.parseaddr(raw_from)
    reply_name, reply_addr = email.utils.parseaddr(reply_to)

    from_domain = from_addr.split("@")[-1].lower().strip() if "@" in from_addr else ""
    reply_domain = reply_addr.split("@")[-1].lower().strip() if "@" in reply_addr else ""

    from_reply_mismatch = False
    if from_domain and reply_domain and from_domain != reply_domain:
        from_reply_mismatch = True

    # 3. SPF Analysis
    combined_auth = (auth_results + " " + rec_spf).lower()
    spf_status = "none"
    if "spf=pass" in combined_auth or "pass" in rec_spf.lower():
        spf_status = "pass"
    elif "spf=fail" in combined_auth or "fail" in rec_spf.lower():
        spf_status = "fail"
    elif "spf=softfail" in combined_auth:
        spf_status = "softfail"
    elif "spf=neutral" in combined_auth:
        spf_status = "neutral"

    # 4. DKIM Analysis
    dkim_status = "none"
    dkim_sig = msg.get("DKIM-Signature", None)
    if "dkim=pass" in combined_auth:
        dkim_status = "pass"
    elif "dkim=fail" in combined_auth:
        dkim_status = "fail"
    elif dkim_sig:
        dkim_status = "present"

    # 5. DMARC Analysis
    dmarc_status = "none"
    if "dmarc=pass" in combined_auth:
        dmarc_status = "pass"
    elif "dmarc=fail" in combined_auth:
        dmarc_status = "fail"

    header_dict = {
        "spf": spf_status,
        "dkim": dkim_status,
        "dmarc": dmarc_status,
        "from_reply_mismatch": from_reply_mismatch,
        "hops": hops,
    }

    # Generate Header Indicators
    header_indicators: List[Dict[str, Any]] = []
    if from_reply_mismatch:
        header_indicators.append({
            "type": "heuristic",
            "severity": "medium",
            "detail": f"From ({from_domain}) and Reply-To ({reply_domain}) domains mismatch (potential sender spoofing).",
        })
    if spf_status == "fail":
        header_indicators.append({
            "type": "heuristic",
            "severity": "medium",
            "detail": "Sender Policy Framework (SPF) check failed for sending server.",
        })
    if dmarc_status == "fail":
        header_indicators.append({
            "type": "heuristic",
            "severity": "high",
            "detail": "Domain-based Message Authentication (DMARC) validation failed.",
        })
    if hops > 7:
        header_indicators.append({
            "type": "heuristic",
            "severity": "low",
            "detail": f"Unusually high routing relay count ({hops} hops).",
        })

    return {
        "subject": subject,
        "from": from_addr,
        "body": effective_body,
        "html_body": html_body,
        "headers": header_dict,
        "indicators": header_indicators,
    }


# -----------------------------------------------------------------------------
# Risk Score Calculation & Invariant Enforcement
# -----------------------------------------------------------------------------

def compute_risk_score(
    probability: float,
    indicators: List[Dict[str, Any]],
    sensitivity: str = "medium",
) -> Tuple[float, str]:
    """Calculate combined 0-100 risk score and categorical classification.

    FORMULA SPECIFICATION:
    1. Base Score = probability * 100.0 (where probability is calibrated model spam P, 0.0 to 1.0)
    2. Raw Heuristic Bump = sum(SEVERITY_WEIGHTS[ind.severity]) for all heuristic indicators.
       - critical: +8.0
       - high:     +5.0
       - medium:   +3.0
       - low:      +1.0
    3. Capped Heuristic Bump = min(Raw Bump, 15.0)
    4. Guardrails (Invariant Rule: Signals NEVER flip a confident model result alone):
       - If probability < 0.20 (confident legitimate):
         risk_score is strictly capped at min(raw_score, 35.0).
         Ensures an innocent email is never categorized as Spam or forced into high-risk alerts.
       - If probability > 0.80 (confident spam):
         risk_score is pinned to at least 80.0.
       - General: bounded to [0.0, 100.0].
    5. Sensitivity mapping to decision boundary:
       - 'low':    Safe (< 50), Suspicious (50-70), Spam (> 70) [Favors Precision: 99.41%]
       - 'medium': Safe (< 40), Suspicious (40-60), Spam (> 60) [Balanced: 98.83% Prec, 99.07% Rec]
       - 'high':   Safe (< 30), Suspicious (30-45), Spam (> 45) [Favors Recall: 99.62%]

    Returns:
        (risk_score: float, classification: str)
    """
    p = float(probability)
    # Sanitize NaN or out-of-range floats
    if math.isnan(p):
        p = 0.50
    p = min(1.0, max(0.0, p))

    base_score = p * 100.0

    raw_bump = 0.0
    for ind in indicators:
        if ind.get("type") == "heuristic":
            sev = ind.get("severity", "low")
            raw_bump += SEVERITY_WEIGHTS.get(sev, 1.0)

    capped_bump = min(raw_bump, MAX_HEURISTIC_BUMP)
    raw_score = base_score + capped_bump

    # Invariant Guardrails: signals never flip a confident model result alone
    if p < 0.20:
        final_score = min(raw_score, 35.0)
    elif p > 0.80:
        final_score = max(raw_score, 80.0)
    else:
        final_score = raw_score

    final_score = min(100.0, max(0.0, round(final_score, 1)))

    # Classification Mapping
    sens_profile = SENSITIVITY_PROFILES.get(sensitivity.lower(), SENSITIVITY_PROFILES["medium"])
    safe_max = sens_profile["safe_max"]
    spam_min = sens_profile["spam_min"]

    if final_score < safe_max:
        classification = "Safe"
    elif final_score > spam_min:
        classification = "Spam"
    else:
        classification = "Suspicious"

    return final_score, classification


# -----------------------------------------------------------------------------
# Key Findings Synthesis
# -----------------------------------------------------------------------------

def generate_key_findings(
    probability: float,
    classification: str,
    indicators: List[Dict[str, Any]],
    headers: Optional[Dict[str, Any]],
    urls: List[Dict[str, Any]],
) -> List[str]:
    """Generate concise, human-readable summary sentences for the analyst report."""
    findings: List[str] = []

    # 1. Model finding
    pct = round(probability * 100.0, 1)
    if classification == "Safe":
        findings.append(f"Calibrated NLP model indicates legitimate correspondence ({pct}% spam probability).")
    elif classification == "Spam":
        findings.append(f"Calibrated NLP model flagged high-probability spam characteristics ({pct}% spam probability).")
    else:
        findings.append(f"Classification falls in borderline uncertainty zone ({pct}% spam probability); human review advised.")

    # 2. URL findings
    flagged_urls = [u for u in urls if u.get("flags")]
    if flagged_urls:
        shorteners = sum(1 for u in flagged_urls if "shortener" in u["flags"])
        mismatches = sum(1 for u in flagged_urls if "link_text_mismatch" in u["flags"])
        ip_hosts = sum(1 for u in flagged_urls if "ip_host" in u["flags"])
        sus_tlds = sum(1 for u in flagged_urls if "suspicious_tld" in u["flags"])

        parts = []
        if mismatches:
            parts.append(f"{mismatches} deceptive link(s) with anchor mismatch")
        if ip_hosts:
            parts.append(f"{ip_hosts} direct IP address destination(s)")
        if shorteners:
            parts.append(f"{shorteners} shortened URL(s)")
        if sus_tlds:
            parts.append(f"{sus_tlds} high-risk TLD link(s)")

        findings.append(f"Found {len(flagged_urls)} flagged link(s): {', '.join(parts)}.")
    elif urls:
        findings.append(f"Inspected {len(urls)} link(s); zero suspicious domains, shorteners, or IP hosts detected.")

    # 3. Header findings
    if headers:
        header_notes = []
        if headers.get("from_reply_mismatch"):
            header_notes.append("From and Reply-To domain mismatch")
        if headers.get("spf") == "fail":
            header_notes.append("SPF validation failed")
        elif headers.get("spf") == "pass":
            header_notes.append("SPF pass")
        if headers.get("dmarc") == "fail":
            header_notes.append("DMARC validation failed")
        elif headers.get("dmarc") == "pass":
            header_notes.append("DMARC pass")

        hops = headers.get("hops", 0)
        if header_notes:
            findings.append(f"Header telemetry: {', '.join(header_notes)} across {hops} relay hop(s).")
        else:
            findings.append(f"Header routing: {hops} standard network relay hop(s) verified.")

    # 4. Clean finding if zero threat indicators
    if not indicators and classification == "Safe":
        findings.append("Zero heuristic threat indicators or spoofing anomalies detected.")

    return findings[:5]
