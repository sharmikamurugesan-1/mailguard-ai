"""Generate a publication-grade PDF report for MailGuard AI using Playwright."""

import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

def generate_report():
    base_dir = Path(__file__).resolve().parent.parent
    reports_dir = base_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    pdf_output_path = reports_dir / "MailGuard_AI_Project_Report.pdf"
    
    # Artifact directory for Antigravity UI presentation
    artifact_dir = Path(r"C:\Users\LENOVO\.gemini\antigravity\brain\e0672e4d-78de-4925-b93d-6706ff3329c8")
    artifact_pdf_path = artifact_dir / "MailGuard_AI_Project_Report.pdf"

    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>MailGuard AI — THREAT_RADAR Project Report</title>
<style>
  @page {
    size: A4;
    margin: 18mm 16mm 20mm 16mm;
    @bottom-right {
      content: "Page " counter(page);
      font-size: 9pt;
      color: #8c8c99;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    @bottom-left {
      content: "MailGuard AI — THREAT_RADAR | Project Report";
      font-size: 9pt;
      color: #8c8c99;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
  }

  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: #1f2024;
    line-height: 1.55;
    font-size: 10pt;
    margin: 0;
    padding: 0;
    background: #ffffff;
  }

  /* Header & Banner */
  .header-card {
    background: linear-gradient(135deg, #2b0d18 0%, #4a1528 50%, #7a1027 100%);
    color: #fcf4ec;
    padding: 24px 28px;
    border-radius: 10px;
    margin-bottom: 24px;
    box-shadow: 0 4px 14px rgba(43, 13, 24, 0.15);
  }

  .header-card h1 {
    font-size: 22pt;
    margin: 0 0 6px 0;
    font-weight: 800;
    letter-spacing: -0.5px;
    color: #ffffff;
  }

  .header-card .subtitle {
    font-size: 12pt;
    color: #f06b88;
    margin: 0 0 16px 0;
    font-weight: 500;
  }

  .meta-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 8px 16px;
    font-size: 9pt;
    border-top: 1px solid rgba(240, 107, 136, 0.3);
    padding-top: 12px;
  }

  .meta-item strong {
    color: #f5c056;
  }

  .meta-item a {
    color: #fcf4ec;
    text-decoration: underline;
  }

  /* Typography */
  h2 {
    font-size: 14pt;
    color: #7a1027;
    border-bottom: 2px solid #f06b88;
    padding-bottom: 4px;
    margin-top: 24px;
    margin-bottom: 12px;
    font-weight: 700;
    page-break-after: avoid;
  }

  h3 {
    font-size: 11.5pt;
    color: #2b0d18;
    margin-top: 16px;
    margin-bottom: 8px;
    font-weight: 600;
    page-break-after: avoid;
  }

  p {
    margin: 0 0 10px 0;
    text-align: justify;
  }

  ul, ol {
    margin: 0 0 12px 0;
    padding-left: 20px;
  }

  li {
    margin-bottom: 4px;
  }

  /* Tables */
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0 16px 0;
    font-size: 8.5pt;
    page-break-inside: avoid;
  }

  th, td {
    padding: 7px 10px;
    text-align: left;
    border: 1px solid #e2d3d8;
  }

  th {
    background: #361120;
    color: #ffffff;
    font-weight: 600;
  }

  tr:nth-child(even) {
    background: #faf4f6;
  }

  .badge-pass {
    background: #e6f4ea;
    color: #137333;
    padding: 2px 6px;
    border-radius: 4px;
    font-weight: 600;
    font-size: 7.5pt;
  }

  .badge-winner {
    background: #fef3c7;
    color: #92400e;
    padding: 2px 6px;
    border-radius: 4px;
    font-weight: 700;
    font-size: 7.5pt;
  }

  /* Callout boxes */
  .callout {
    background: #fdf2f4;
    border-left: 4px solid #7a1027;
    padding: 10px 14px;
    margin: 12px 0;
    border-radius: 0 6px 6px 0;
    font-size: 9pt;
    page-break-inside: avoid;
  }

  /* Code block */
  pre {
    background: #19050d;
    color: #fcf4ec;
    padding: 12px 14px;
    border-radius: 6px;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 8pt;
    line-height: 1.45;
    overflow-x: auto;
    margin: 10px 0 14px 0;
    border: 1px solid #4d192c;
    page-break-inside: avoid;
  }

  code {
    font-family: "Consolas", "Courier New", monospace;
    font-size: 8.5pt;
    color: #8b1e3f;
    background: #f8eaee;
    padding: 1px 4px;
    border-radius: 3px;
  }

  pre code {
    color: inherit;
    background: transparent;
    padding: 0;
  }

  /* Diagrams */
  .diagram-container {
    background: #faf7f8;
    border: 1px solid #e0c8d0;
    border-radius: 8px;
    padding: 14px;
    margin: 14px 0;
    text-align: center;
    page-break-inside: avoid;
  }

  .diagram-container svg {
    max-width: 100%;
    height: auto;
  }

  .diagram-caption {
    font-size: 8pt;
    color: #63434c;
    margin-top: 6px;
    font-style: italic;
  }

  .avoid-break {
    page-break-inside: avoid;
  }

  .page-break {
    page-break-before: always;
  }
</style>
</head>
<body>

<!-- Header Banner -->
<div class="header-card">
  <h1>MailGuard AI — THREAT_RADAR</h1>
  <div class="subtitle">Client-Side Privacy-First Email Forensics & Multi-Model Threat Intelligence</div>
  <div class="meta-grid">
    <div class="meta-item"><strong>Lead Engineer:</strong> Sharmika Murugesan</div>
    <div class="meta-item"><strong>Live Web App:</strong> <a href="https://mailguard-ai-6ljt.onrender.com">https://mailguard-ai-6ljt.onrender.com</a></div>
    <div class="meta-item"><strong>GitHub Repository:</strong> <a href="https://github.com/sharmikamurugesan-1/mailguard-ai">sharmikamurugesan-1/mailguard-ai</a></div>
    <div class="meta-item"><strong>Release Version:</strong> v2.0.0 Production Hardened</div>
  </div>
</div>

<!-- Section 1 -->
<h2>1. Executive Summary & Problem Statement</h2>
<p>
  Email continues to be the dominant attack vector in over <strong>91% of modern cyber incidents</strong>. Attackers employ deceptive social engineering, invoice impersonation, and fraudulent QR codes (<strong>Quishing</strong>) that easily bypass legacy keyword filters and static header checks.
</p>
<p>
  Concurrently, conventional enterprise email scanning solutions present a severe data confidentiality liability: they mandate that corporate communications, proprietary intellectual property, and attachment images be uploaded to remote cloud infrastructure for inspection.
</p>
<div class="callout">
  <strong>Core Mission:</strong> MailGuard AI resolves this dilemma through a <strong>Zero-Storage, Client-Side Visual Sandbox</strong> coupled with a high-precision <strong>Multi-Model Consensus Engine</strong>. It guarantees that email contents and image files are never stored or logged on any server, delivering transparent explainable AI telemetry with <strong>98.83% precision</strong> and <strong>99.07% recall</strong>.
</div>

<!-- Section 2 -->
<h2>2. End-to-End System Architecture</h2>
<p>
  The MailGuard AI architecture isolates visual data processing within the user's browser via WebAssembly, dispatching only sanitized text structures to a stateless, containerized Python Flask backend.
</p>

<div class="diagram-container">
  <svg viewBox="0 0 720 220" width="100%" height="220" xmlns="http://www.w3.org/2000/svg">
    <!-- Client Box -->
    <rect x="10" y="20" width="240" height="180" rx="8" fill="#fdf2f4" stroke="#7a1027" stroke-width="2"/>
    <text x="130" y="45" text-anchor="middle" font-size="12" font-weight="bold" fill="#7a1027">Client-Side Browser (WASM Sandbox)</text>
    <rect x="25" y="65" width="210" height="35" rx="5" fill="#ffffff" stroke="#c48a99"/>
    <text x="130" y="87" text-anchor="middle" font-size="10" fill="#2b0d18">Zero-Upload OCR (Tesseract.js WASM)</text>
    <rect x="25" y="110" width="210" height="35" rx="5" fill="#ffffff" stroke="#c48a99"/>
    <text x="130" y="132" text-anchor="middle" font-size="10" fill="#2b0d18">In-Browser QR Decoder (jsQR)</text>
    <rect x="25" y="155" width="210" height="30" rx="5" fill="#ffffff" stroke="#c48a99"/>
    <text x="130" y="175" text-anchor="middle" font-size="10" fill="#2b0d18">Local Audit Log (IndexedDB)</text>

    <!-- Arrow 1 -->
    <path d="M 250 110 L 295 110" stroke="#7a1027" stroke-width="2" marker-end="url(#arrow)"/>
    <text x="272" y="100" text-anchor="middle" font-size="8" fill="#7a1027">POST JSON</text>

    <!-- Backend Box -->
    <rect x="300" y="20" width="230" height="180" rx="8" fill="#f5f0f2" stroke="#361120" stroke-width="2"/>
    <text x="415" y="45" text-anchor="middle" font-size="12" font-weight="bold" fill="#361120">Flask Backend Engine (Render)</text>
    <rect x="315" y="65" width="200" height="35" rx="5" fill="#ffffff" stroke="#99707e"/>
    <text x="415" y="87" text-anchor="middle" font-size="10" fill="#2b0d18">SHA-256 Model Integrity Guard</text>
    <rect x="315" y="110" width="200" height="35" rx="5" fill="#ffffff" stroke="#99707e"/>
    <text x="415" y="132" text-anchor="middle" font-size="10" fill="#2b0d18">15,000 TF-IDF (1,2) N-Gram Extractor</text>
    <rect x="315" y="155" width="200" height="30" rx="5" fill="#ffffff" stroke="#99707e"/>
    <text x="415" y="175" text-anchor="middle" font-size="10" fill="#2b0d18">URL & SPF/DKIM Heuristics</text>

    <!-- Arrow 2 -->
    <path d="M 530 110 L 575 110" stroke="#7a1027" stroke-width="2"/>

    <!-- Consensus & Radar Box -->
    <rect x="580" y="20" width="130" height="180" rx="8" fill="#fdf8f0" stroke="#b45309" stroke-width="2"/>
    <text x="645" y="45" text-anchor="middle" font-size="11" font-weight="bold" fill="#b45309">THREAT_RADAR</text>
    <rect x="590" y="65" width="110" height="28" rx="4" fill="#ffffff" stroke="#d97706"/>
    <text x="645" y="83" text-anchor="middle" font-size="9" fill="#2b0d18">Linear SVM</text>
    <rect x="590" y="100" width="110" height="28" rx="4" fill="#ffffff" stroke="#d97706"/>
    <text x="645" y="118" text-anchor="middle" font-size="9" fill="#2b0d18">Logistic Reg</text>
    <rect x="590" y="135" width="110" height="28" rx="4" fill="#ffffff" stroke="#d97706"/>
    <text x="645" y="153" text-anchor="middle" font-size="9" fill="#2b0d18">Naive Bayes</text>
    <text x="645" y="185" text-anchor="middle" font-size="9" font-weight="bold" fill="#7a1027">6D Risk Map</text>
  </svg>
  <div class="diagram-caption">Figure 1: Full-stack system architecture and zero-upload processing flow.</div>
</div>

<!-- Section 3 -->
<h2>3. Machine Learning & Multi-Model Consensus Engine</h2>
<p>
  MailGuard AI integrates three distinct classification algorithms trained and cross-validated on the <strong>Enron Spam dataset ($N = 30,462$)</strong>. To eliminate single-model bias, the system provides both unified single-model predictions and side-by-side consensus arbitration via <code>/api/compare</code>.
</p>

<h3>3.1 Mathematical Formulation</h3>
<ul>
  <li>
    <strong>Calibrated Linear SVM (Primary Production Model):</strong> Optimized with Platt Scaling to convert unbounded margin distances into well-calibrated posterior probabilities:
    <div style="text-align: center; margin: 6px 0; font-family: 'Times New Roman', serif;">
      <em>P(Spam | x) = 1 / (1 + exp(A &middot; f(x) + B))</em>
    </div>
  </li>
  <li>
    <strong>Logistic Regression:</strong> Minimizes cross-entropy with L2 weight decay, providing smooth log-odds interpretation.
  </li>
  <li>
    <strong>Multinomial Naive Bayes:</strong> Employs Laplace smoothing (&alpha; = 1.0) over word frequencies, delivering ultra-low latency inference for high-throughput operational requirements.
  </li>
</ul>

<h3>3.2 Fail-Closed Model Cryptographic Verification</h3>
<p>
  At startup, the application verifies the cryptographic SHA-256 hash of serialized pipelines to prevent supply-chain tampering:
</p>
<pre><code># Location: src/predictor.py
def compute_file_sha256(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

class SpamPredictor:
    def __init__(self, model_path: Path, expected_hash: str):
        actual_hash = compute_file_sha256(model_path)
        if actual_hash != expected_hash:
            raise ValueError(f"FATAL: Model hash mismatch! Expected {expected_hash}, got {actual_hash}")
        self.pipeline = joblib.load(model_path)</code></pre>

<!-- Page Break for Clean Layout -->
<div class="page-break"></div>

<!-- Section 4 -->
<h2>4. Visual Threat Intelligence: Client-Side OCR & QR Extraction</h2>
<p>
  To counter image-embedded spam and Quishing, MailGuard AI performs computer vision processing client-side. The image never leaves the user's browser, eliminating external server liability.
</p>

<div class="diagram-container">
  <svg viewBox="0 0 700 130" width="100%" height="130" xmlns="http://www.w3.org/2000/svg">
    <rect x="10" y="20" width="150" height="90" rx="6" fill="#fdf2f4" stroke="#7a1027"/>
    <text x="85" y="45" text-anchor="middle" font-size="10" font-weight="bold" fill="#7a1027">1. Image Input</text>
    <text x="85" y="65" text-anchor="middle" font-size="8.5" fill="#444">User selects .png/.jpg</text>
    <text x="85" y="80" text-anchor="middle" font-size="8.5" fill="#444">Canvas element created</text>

    <path d="M 160 65 L 195 65" stroke="#7a1027" stroke-width="2"/>

    <rect x="200" y="20" width="170" height="90" rx="6" fill="#f5f0f2" stroke="#361120"/>
    <text x="285" y="45" text-anchor="middle" font-size="10" font-weight="bold" fill="#361120">2. In-Browser WASM Worker</text>
    <text x="285" y="65" text-anchor="middle" font-size="8.5" fill="#444">Tesseract-core-lstm.wasm</text>
    <text x="285" y="80" text-anchor="middle" font-size="8.5" fill="#444">jsQR Bitmatrix Scan</text>

    <path d="M 370 65 L 405 65" stroke="#7a1027" stroke-width="2"/>

    <rect x="410" y="20" width="140" height="90" rx="6" fill="#eff6ff" stroke="#2563eb"/>
    <text x="480" y="45" text-anchor="middle" font-size="10" font-weight="bold" fill="#2563eb">3. Local Artifacts</text>
    <text x="480" y="65" text-anchor="middle" font-size="8.5" fill="#444">Raw Text extracted</text>
    <text x="480" y="80" text-anchor="middle" font-size="8.5" fill="#444">QR URLs decoded</text>

    <path d="M 550 65 L 585 65" stroke="#7a1027" stroke-width="2"/>

    <rect x="590" y="20" width="100" height="90" rx="6" fill="#ecfdf5" stroke="#059669"/>
    <text x="640" y="45" text-anchor="middle" font-size="10" font-weight="bold" fill="#059669">4. API Dispatch</text>
    <text x="640" y="65" text-anchor="middle" font-size="8.5" fill="#444">POST /api/analyze</text>
    <text x="640" y="80" text-anchor="middle" font-size="8" fill="#059669">Zero image sent</text>
  </svg>
  <div class="diagram-caption">Figure 2: In-browser WebAssembly OCR & QR visual pipeline.</div>
</div>

<h3>4.1 Client-Side Execution Code</h3>
<pre><code>// Location: static/js/app.js
function analyzeImageClientSide(file) {
  return new Promise((resolve, reject) => {
    const worker = new Worker('/vendor/tesseract/worker.min.js');
    const img = new Image();
    img.src = URL.createObjectURL(file);
    img.onload = () => {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      canvas.width = img.width; canvas.height = img.height;
      ctx.drawImage(img, 0, 0);
      
      const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const qrCode = jsQR(imgData.data, canvas.width, canvas.height);
      
      Tesseract.recognize(canvas, 'eng').then(({ data: { text } }) => {
        resolve({ extractedText: text, qrUrl: qrCode ? qrCode.data : null });
      }).catch(reject);
    };
  });
}</code></pre>

<!-- Section 5 -->
<h2>5. Forensic Signals & THREAT_RADAR Telemetry</h2>
<p>
  MailGuard AI extracts structured heuristics from text, URLs, and headers to construct a multi-vector threat profile:
</p>

<div class="avoid-break">
  <table>
    <thead>
      <tr>
        <th>Radar Dimension</th>
        <th>Target Risk Vector</th>
        <th>Underlying Heuristic / Method</th>
        <th>Weight</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>Linguistic Signals</strong></td>
        <td>Urgency, coercion, financial extortion</td>
        <td>TF-IDF positive token weights &times; keyword density</td>
        <td>25%</td>
      </tr>
      <tr>
        <td><strong>URL Reputation</strong></td>
        <td>Phishing links, credential harvesters</td>
        <td>IP hostnames, Punycode homographs, suspicious TLDs</td>
        <td>20%</td>
      </tr>
      <tr>
        <td><strong>Header Auth</strong></td>
        <td>Domain spoofing & impersonation</td>
        <td>SPF, DKIM, and DMARC alignment status</td>
        <td>20%</td>
      </tr>
      <tr>
        <td><strong>Formatting Anomalies</strong></td>
        <td>Spam formatting tricks</td>
        <td>Capital letter density (&gt;25%), repeated punctuation</td>
        <td>10%</td>
      </tr>
      <tr>
        <td><strong>Vocabulary Entropy</strong></td>
        <td>Random character / dictionary padding</td>
        <td>Shannon entropy over word tokens</td>
        <td>10%</td>
      </tr>
      <tr>
        <td><strong>Model Confidence</strong></td>
        <td>Empirical model certainty</td>
        <td>Calibrated posterior probability: max(P(spam), 1-P(spam))</td>
        <td>15%</td>
      </tr>
    </tbody>
  </table>
</div>

<h3>5.1 Forensic Inspection Code</h3>
<pre><code># Location: src/signals.py
def evaluate_url_reputation(url: str) -> dict:
    parsed = urllib.parse.urlparse(url)
    hostname = parsed.hostname or ""
    flags = []
    if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", hostname):
        flags.append("ip_hostname_phishing")
    if hostname.startswith("xn--"):
        flags.append("punycode_homograph_spoof")
    high_risk_tlds = {".xyz", ".top", ".work", ".click", ".kim", ".ru"}
    if any(hostname.endswith(tld) for tld in high_risk_tlds):
        flags.append("suspicious_tld")
    return {"url": url, "hostname": hostname, "flags": flags}</code></pre>

<!-- Page Break for Clean Layout -->
<div class="page-break"></div>

<!-- Section 6 -->
<h2>6. Empirical Results & Data Leakage Audit</h2>

<h3>6.1 5-Fold Stratified Cross-Validation (Training Split: N = 24,369)</h3>
<table>
  <thead>
    <tr>
      <th>Model Candidate</th>
      <th>CV Precision (Spam)</th>
      <th>CV Recall (Spam)</th>
      <th>CV F1 Score</th>
      <th>CV Accuracy</th>
      <th>Decision Status</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Calibrated Linear SVM</strong></td>
      <td><strong>98.72%</strong> (&plusmn;0.0022)</td>
      <td><strong>99.29%</strong> (&plusmn;0.0027)</td>
      <td><strong>99.00%</strong> (&plusmn;0.0010)</td>
      <td><strong>99.04%</strong> (&plusmn;0.0010)</td>
      <td><span class="badge-winner">WINNER (Primary)</span></td>
    </tr>
    <tr>
      <td>Multinomial Naive Bayes</td>
      <td>98.24% (&plusmn;0.0028)</td>
      <td>98.52% (&plusmn;0.0011)</td>
      <td>98.38% (&plusmn;0.0009)</td>
      <td>98.45% (&plusmn;0.0009)</td>
      <td><span class="badge-pass">Qualified Candidate</span></td>
    </tr>
    <tr>
      <td>Logistic Regression</td>
      <td>97.65% (&plusmn;0.0025)</td>
      <td>99.41% (&plusmn;0.0021)</td>
      <td>98.52% (&plusmn;0.0010)</td>
      <td>98.57% (&plusmn;0.0010)</td>
      <td>Disqualified (Prec &lt; 98%)</td>
    </tr>
  </tbody>
</table>

<h3>6.2 Held-Out Test Set Performance (N = 6,093)</h3>
<div class="diagram-container">
  <svg viewBox="0 0 520 120" width="100%" height="120" xmlns="http://www.w3.org/2000/svg">
    <rect x="100" y="10" width="180" height="45" fill="#f0fdf4" stroke="#16a34a"/>
    <text x="190" y="30" text-anchor="middle" font-size="10" font-weight="bold" fill="#15803d">True Negatives (TN): 3,148</text>
    <text x="190" y="45" text-anchor="middle" font-size="8.5" fill="#555">Clean Ham Preserved</text>

    <rect x="300" y="10" width="180" height="45" fill="#fef2f2" stroke="#dc2626"/>
    <text x="390" y="30" text-anchor="middle" font-size="10" font-weight="bold" fill="#b91c1c">False Positives (FP): 34</text>
    <text x="390" y="45" text-anchor="middle" font-size="8.5" fill="#555">False Alarms (0.55%)</text>

    <rect x="100" y="65" width="180" height="45" fill="#fffbeb" stroke="#d97706"/>
    <text x="190" y="85" text-anchor="middle" font-size="10" font-weight="bold" fill="#b45309">False Negatives (FN): 27</text>
    <text x="190" y="100" text-anchor="middle" font-size="8.5" fill="#555">Missed Threats (0.44%)</text>

    <rect x="300" y="65" width="180" height="45" fill="#eff6ff" stroke="#2563eb"/>
    <text x="390" y="85" text-anchor="middle" font-size="10" font-weight="bold" fill="#1d4ed8">True Positives (TP): 2,884</text>
    <text x="390" y="100" text-anchor="middle" font-size="8.5" fill="#555">Threats Intercepted</text>
  </svg>
  <div class="diagram-caption">Figure 3: Held-out test set confusion matrix (Accuracy: 99.00%, Precision: 98.83%, Recall: 99.07%).</div>
</div>

<h3>6.3 Data Leakage & Near-Duplicate Analysis</h3>
<p>
  Pairwise TF-IDF cosine similarity was computed between all 6,093 test samples and training data:
</p>
<ul>
  <li>Identified <strong>1,208 near-duplicates</strong> (19.83% of test set) sharing corporate signature templates.</li>
  <li>Evaluating on the strictly de-duplicated subset (<strong>N = 4,885</strong>) yielded <strong>98.75% accuracy</strong> and <strong>98.52% precision</strong>.</li>
  <li>Both false positives (34) and false negatives (27) remained identical, proving that performance is driven by true pattern generalization rather than memorized boilerplate.</li>
</ul>

<!-- Section 7 -->
<h2>7. Quality Assurance, Security & Accessibility</h2>

<div class="avoid-break">
  <table>
    <thead>
      <tr>
        <th>Verification Area</th>
        <th>Audit Command / Tool</th>
        <th>Result</th>
        <th>Standard / Requirement</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>Automated Unit Tests</strong></td>
        <td><code>pytest -v -rs</code></td>
        <td><span class="badge-pass">176 / 176 PASSED</span></td>
        <td>Full test suite execution in 15.6s</td>
      </tr>
      <tr>
        <td><strong>Color Contrast Audit</strong></td>
        <td><code>scripts/check_contrast.py</code></td>
        <td><span class="badge-pass">26 / 26 PASSED</span></td>
        <td>WCAG 2.1 AA (all pairs &ge; 4.5:1 up to 17.75:1)</td>
      </tr>
      <tr>
        <td><strong>Route Accessibility</strong></td>
        <td>Playwright + Axe-core</td>
        <td><span class="badge-pass">0 VIOLATIONS</span></td>
        <td>Zero critical/serious issues across 11 routes</td>
      </tr>
      <tr>
        <td><strong>Static Security Code Scan</strong></td>
        <td><code>bandit -r src/</code></td>
        <td><span class="badge-pass">0 ISSUES</span></td>
        <td>Clean static security analysis</td>
      </tr>
      <tr>
        <td><strong>Dependency Vulnerabilities</strong></td>
        <td><code>pip-audit -r requirements.txt</code></td>
        <td><span class="badge-pass">0 VULNERABILITIES</span></td>
        <td>Zero known CVEs in runtime dependencies</td>
      </tr>
      <tr>
        <td><strong>High-Concurrency Capacity</strong></td>
        <td><code>scripts/test_1000_concurrency.py</code></td>
        <td><span class="badge-pass">0 DROPPED REQS</span></td>
        <td>Bounded queue execution with graceful handling</td>
      </tr>
    </tbody>
  </table>
</div>

<!-- Section 8 -->
<h2>8. Deployment Architecture & Verification</h2>
<p>
  MailGuard AI is deployed in a unified production configuration:
</p>
<ul>
  <li>
    <strong>Production Web Application:</strong> <a href="https://mailguard-ai-6ljt.onrender.com">https://mailguard-ai-6ljt.onrender.com</a>  
    <em>Hosts the unified frontend UI, static assets, and Flask 3.1.3 ML backend on the same origin, eliminating cross-origin latency and CORS issues.</em>
  </li>
  <li>
    <strong>GitHub Repository:</strong> <a href="https://github.com/sharmikamurugesan-1/mailguard-ai">https://github.com/sharmikamurugesan-1/mailguard-ai</a>  
    <em>Complete source code, reproducible training scripts, model pipelines, and comprehensive documentation.</em>
  </li>
</ul>

<!-- Section 9 -->
<h2>9. Conclusion</h2>
<p>
  MailGuard AI demonstrates that enterprise-grade email security and rigorous user data privacy can coexist. By executing visual threat extraction client-side via WebAssembly and coupling it with a multi-model consensus engine, the platform achieves <strong>98.83% precision</strong> while maintaining zero server retention of private communications.
</p>

</body>
</html>
"""

    temp_html_path = reports_dir / "report_temp.html"
    temp_html_path.write_text(html_content, encoding="utf-8")
    
    print(f"Generated HTML source at {temp_html_path}")
    print("Launching Chromium via Playwright to generate PDF...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(temp_html_path.as_uri())
        
        # Render high-resolution PDF
        page.pdf(
            path=str(pdf_output_path),
            format="A4",
            print_background=True,
            margin={"top": "18mm", "bottom": "20mm", "left": "16mm", "right": "16mm"}
        )
        browser.close()

    # Also copy to artifact directory
    if artifact_dir.exists():
        import shutil
        shutil.copy2(pdf_output_path, artifact_pdf_path)
        print(f"Copied PDF artifact to {artifact_pdf_path}")

    # Remove temp HTML
    if temp_html_path.exists():
        temp_html_path.unlink()

    print("=" * 60)
    print(f"SUCCESS: Publication-grade PDF generated successfully!")
    print(f"Location: {pdf_output_path}")
    print(f"Size: {pdf_output_path.stat().st_size:,} bytes")
    print("=" * 60)

if __name__ == "__main__":
    generate_report()
