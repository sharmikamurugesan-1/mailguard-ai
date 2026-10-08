/**
 * MailGuard AI - Client Application Logic
 * Vanilla JavaScript, zero frameworks, zero external dependencies.
 * STRICT SECURITY: DOM manipulation via textContent and createElement only.
 * NO innerHTML usage with user or API data.
 */

(function () {
  'use strict';

  // Constants
  const MAX_INPUT_CHARS = 20000;
  const REQUEST_TIMEOUT_MS = 90000; // 90 seconds
  const WAKING_BANNER_DELAY_MS = 5000; // 5 seconds

  // DOM Elements
  const statusDot = document.getElementById('status-dot');
  const statusText = document.getElementById('status-text');

  const emailForm = document.getElementById('email-form');
  const subjectInput = document.getElementById('subject-input');
  const bodyInput = document.getElementById('body-input');
  const charCounter = document.getElementById('char-counter');
  const bodyError = document.getElementById('body-error');
  const generalError = document.getElementById('general-error');
  const generalErrorMessage = document.getElementById('general-error-message');
  const retryBtn = document.getElementById('retry-btn');
  const wakingBanner = document.getElementById('waking-banner');

  const analyzeBtn = document.getElementById('analyze-btn');
  const analyzeBtnText = document.getElementById('analyze-btn-text');
  const analyzeBtnSpinner = document.getElementById('analyze-btn-spinner');
  const clearBtn = document.getElementById('clear-btn');

  const sampleSpamBtn = document.getElementById('sample-spam-btn');
  const sampleHamBtn = document.getElementById('sample-ham-btn');
  const sampleBorderlineBtn = document.getElementById('sample-borderline-btn');

  // Result Elements
  const resultCard = document.getElementById('result-card');
  const verdictBanner = document.getElementById('verdict-banner');
  const verdictIcon = document.getElementById('verdict-icon');
  const verdictTitle = document.getElementById('verdict-title');
  const riskBadge = document.getElementById('risk-badge');
  const confidenceValue = document.getElementById('confidence-value');
  const confidenceBar = document.getElementById('confidence-bar');
  const probabilitySubtext = document.getElementById('probability-subtext');
  const reliabilityLevelPill = document.getElementById('reliability-level-pill');
  const warningsList = document.getElementById('warnings-list');
  const signalsList = document.getElementById('signals-list');

  // Model Info Elements
  const metaModelType = document.getElementById('meta-model-type');
  const metaVectorizer = document.getElementById('meta-vectorizer');
  const metaDatasetName = document.getElementById('meta-dataset-name');
  const metaDatasetLicense = document.getElementById('meta-dataset-license');
  const metaDatasetSamples = document.getElementById('meta-dataset-samples');
  const metaSelectionCriterion = document.getElementById('meta-selection-criterion');
  const metaAcc = document.getElementById('meta-acc');
  const metaPrec = document.getElementById('meta-prec');
  const metaRec = document.getElementById('meta-rec');
  const metaF1 = document.getElementById('meta-f1');
  const metaFp = document.getElementById('meta-fp');
  const metaFn = document.getElementById('meta-fn');
  const metaLimitationsList = document.getElementById('meta-limitations-list');

  // Sample Data Definitions (pre-packaged client side)
  const SAMPLES = {
    spam: {
      subject: 'URGENT: Your PayPal account has been restricted',
      body: 'Dear customer, unauthorized transactions were flagged on your debit card. Please click http://paypal-security-verification.com/login immediately to confirm your credentials and restore full account access. Failure to respond within 24 hours will lead to permanent suspension.'
    },
    ham: {
      subject: 'Engineering team weekly sync - Agenda & Notes',
      body: 'Hi team, please find attached the agenda for tomorrow\'s sprint planning and engineering review. We will review our quarterly API milestones and the upcoming deployment checklist. Let me know if you would like to add any items before 10 AM.'
    },
    borderline: {
      subject: 'Overdue invoice INV-9042 - legal services',
      body: 'Please review the attached invoice INV-9042 for legal advisory services rendered last month. Send the wire payment to account #4492048 by end of business today.'
    }
  };

  // Warning Code to Human Readable Map
  const WARNING_MESSAGES = {
    near_decision_boundary: 'Classification score is close to the decision boundary (0.35–0.65).',
    short_input: 'Input message is very short (< 10 tokens), which may reduce statistical confidence.',
    low_vocab_coverage: 'Low vocabulary coverage: over half of these words were not observed in training data.',
    non_english_suspected: 'Input appears to contain non-English or non-Latin characters. Preprocessing is English-oriented.',
    dataset_age_notice: 'Trained on 2000s-era Enron corporate emails; modern phrasing or synthetic scams may differ.'
  };

  // --------------------------------------------------------------------------
  // Server Health & Metadata Loading
  // --------------------------------------------------------------------------

  async function checkServerHealth() {
    try {
      const res = await fetch('/api/health');
      if (!res.ok) throw new Error('Health check non-200');
      const data = await res.json();

      statusDot.className = 'status-indicator';
      if (data.status === 'healthy' && data.model_loaded) {
        statusDot.classList.add('status-online');
        statusText.textContent = 'Server Online';
      } else {
        statusDot.classList.add('status-waking');
        statusText.textContent = 'Degraded';
      }
    } catch {
      statusDot.className = 'status-indicator status-offline';
      statusText.textContent = 'Server Offline';
    }
  }

  async function loadModelInfo() {
    try {
      const res = await fetch('/api/model-info');
      if (!res.ok) throw new Error('Failed to load model info');
      const data = await res.json();

      metaModelType.textContent = data.model_type || 'Calibrated Linear SVM';
      metaVectorizer.textContent = data.vectorizer || 'TF-IDF';
      metaDatasetName.textContent = data.dataset_name || 'Enron Spam Dataset';
      metaDatasetLicense.textContent = data.dataset_license || 'GNU General Public License v3.0';

      const nSamples = (data.n_samples || 30462).toLocaleString();
      const nHam = data.class_counts ? data.class_counts.ham.toLocaleString() : '15,910';
      const nSpam = data.class_counts ? data.class_counts.spam.toLocaleString() : '14,552';
      metaDatasetSamples.textContent = `${nSamples} total (${nHam} ham / ${nSpam} spam)`;

      metaSelectionCriterion.textContent = data.selection_criterion || 'Spam Precision >= 0.98 first';

      if (data.test_metrics) {
        metaAcc.textContent = (data.test_metrics.accuracy * 100).toFixed(2) + '%';
        metaPrec.textContent = (data.test_metrics.precision * 100).toFixed(2) + '%';
        metaRec.textContent = (data.test_metrics.recall * 100).toFixed(2) + '%';
        metaF1.textContent = (data.test_metrics.f1 * 100).toFixed(2) + '%';
        metaFp.textContent = String(data.test_metrics.fp ?? 34);
        metaFn.textContent = String(data.test_metrics.fn ?? 27);
      }

      // Limitations
      while (metaLimitationsList.firstChild) {
        metaLimitationsList.removeChild(metaLimitationsList.firstChild);
      }

      const limitations = data.limitations || [];
      limitations.forEach(function (limText) {
        const li = document.createElement('li');
        li.textContent = limText;
        metaLimitationsList.appendChild(li);
      });
    } catch (e) {
      metaModelType.textContent = 'Unavailable (Could not load metadata)';
    }
  }

  // --------------------------------------------------------------------------
  // Character Counter & Validation
  // --------------------------------------------------------------------------

  function updateCharCount() {
    const subLen = (subjectInput.value || '').length;
    const bodyLen = (bodyInput.value || '').length;
    const total = subLen + bodyLen;

    charCounter.textContent = `${total.toLocaleString()} / ${MAX_INPUT_CHARS.toLocaleString()}`;
    if (total > MAX_INPUT_CHARS) {
      charCounter.classList.add('counter-exceeded');
    } else {
      charCounter.classList.remove('counter-exceeded');
    }
  }

  function validateInput() {
    const rawBody = bodyInput.value || '';
    const trimmedBody = rawBody.trim();
    const totalLen = (subjectInput.value || '').length + rawBody.length;

    // Reset error states
    bodyError.textContent = '';
    bodyError.classList.add('hidden');
    generalError.classList.add('hidden');
    generalErrorMessage.textContent = '';
    retryBtn.classList.add('hidden');

    if (!trimmedBody) {
      bodyError.textContent = 'Email body is required to perform spam classification.';
      bodyError.classList.remove('hidden');
      bodyInput.focus();
      return false;
    }

    if (totalLen > MAX_INPUT_CHARS) {
      bodyError.textContent = `Input length (${totalLen.toLocaleString()} chars) exceeds the maximum allowed limit of ${MAX_INPUT_CHARS.toLocaleString()} characters.`;
      bodyError.classList.remove('hidden');
      bodyInput.focus();
      return false;
    }

    return true;
  }

  // --------------------------------------------------------------------------
  // API Prediction Fetch with Timeout & 1 Automatic Retry
  // --------------------------------------------------------------------------

  async function callPredictApi(payload, isRetry) {
    const controller = new AbortController();
    const timeoutId = setTimeout(function () {
      controller.abort();
    }, REQUEST_TIMEOUT_MS);

    try {
      const response = await fetch('/api/predict', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload),
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      const data = await response.json().catch(function () {
        return null;
      });

      if (!response.ok) {
        const errorMsg = data && data.error && data.error.message
          ? data.error.message
          : `Server returned error (${response.status})`;
        throw new Error(errorMsg);
      }

      return data;
    } catch (err) {
      clearTimeout(timeoutId);

      // Handle abort / timeout
      const isTimeout = err.name === 'AbortError';
      const isNetwork = !navigator.onLine || err.message.includes('Failed to fetch') || isTimeout;

      // Execute 1 automatic retry on timeout or network failure
      if (!isRetry && isNetwork) {
        return await callPredictApi(payload, true);
      }

      throw err;
    }
  }

  // --------------------------------------------------------------------------
  // Render Result Card
  // --------------------------------------------------------------------------

  function renderPredictionResult(data) {
    const prediction = data.prediction || 'uncertain';
    const labelDisplay = data.label_display || 'Needs review';
    const riskLevel = (data.risk_level || 'medium').toLowerCase();
    const conf = typeof data.confidence === 'number' ? data.confidence : 0.5;
    const spamProb = typeof data.spam_probability === 'number' ? data.spam_probability : 0.5;

    // Reset card classes
    resultCard.classList.remove('hidden', 'verdict-spam-border', 'verdict-ham-border', 'verdict-uncertain-border');
    verdictIcon.className = 'verdict-icon';
    riskBadge.className = 'risk-badge';

    // Set Verdict Styling & Icons (distinct colors + icons)
    if (prediction === 'spam') {
      resultCard.classList.add('verdict-spam-border');
      verdictIcon.classList.add('verdict-icon-spam');
      verdictIcon.textContent = '🚨';
      verdictTitle.textContent = labelDisplay;
    } else if (prediction === 'ham') {
      resultCard.classList.add('verdict-ham-border');
      verdictIcon.classList.add('verdict-icon-ham');
      verdictIcon.textContent = '✓';
      verdictTitle.textContent = labelDisplay;
    } else {
      // Uncertain / Needs review (strictly neutral amber, never red or green)
      resultCard.classList.add('verdict-uncertain-border');
      verdictIcon.classList.add('verdict-icon-unc');
      verdictIcon.textContent = '⚖';
      verdictTitle.textContent = labelDisplay;
    }

    // Risk Badge
    if (riskLevel === 'high') {
      riskBadge.classList.add('risk-badge-high');
      riskBadge.textContent = 'RISK: HIGH';
    } else if (riskLevel === 'low') {
      riskBadge.classList.add('risk-badge-low');
      riskBadge.textContent = 'RISK: LOW';
    } else {
      riskBadge.classList.add('risk-badge-medium');
      riskBadge.textContent = 'RISK: MEDIUM';
    }

    // Confidence Display
    const confPct = Math.min(100, Math.max(0, conf * 100)).toFixed(1);
    confidenceValue.textContent = `${confPct}%`;
    confidenceBar.style.width = `${confPct}%`;
    probabilitySubtext.textContent = `Calibrated spam probability: ${spamProb.toFixed(4)}`;

    // Reliability & Warnings
    const rel = data.reliability || { level: 'medium', warnings: [] };
    reliabilityLevelPill.textContent = `LEVEL: ${rel.level.toUpperCase()}`;

    while (warningsList.firstChild) {
      warningsList.removeChild(warningsList.firstChild);
    }

    const warnings = rel.warnings || [];
    if (warnings.length === 0) {
      const li = document.createElement('li');
      li.className = 'warning-item';
      li.textContent = 'No data heuristics triggered; standard input length and vocabulary coverage.';
      warningsList.appendChild(li);
    } else {
      warnings.forEach(function (code) {
        const li = document.createElement('li');
        li.className = 'warning-item';
        if (code !== 'dataset_age_notice') {
          li.classList.add('warning-item-warn');
        }
        const text = WARNING_MESSAGES[code] || `Notice: ${code}`;
        li.textContent = text;
        warningsList.appendChild(li);
      });
    }

    // Signals Rendering
    while (signalsList.firstChild) {
      signalsList.removeChild(signalsList.firstChild);
    }

    const signals = data.signals || [];
    if (signals.length === 0) {
      const emptyNote = document.createElement('p');
      emptyNote.className = 'footnote';
      emptyNote.textContent = 'No significant vocabulary feature contributions identified for this text.';
      signalsList.appendChild(emptyNote);
    } else {
      // Find max contribution magnitude for proportional scaling
      let maxContrib = 0.0001;
      signals.forEach(function (s) {
        const val = Math.abs(s.contribution || 0);
        if (val > maxContrib) maxContrib = val;
      });

      signals.forEach(function (item) {
        const row = document.createElement('div');
        row.className = 'signal-row';

        // Term name
        const termSpan = document.createElement('span');
        termSpan.className = 'signal-term';
        // Format tokens cleanly
        let cleanTerm = (item.term || '')
          .replace(/__number__/g, '<number>')
          .replace(/__url__/g, '<url>')
          .replace(/__email__/g, '<email>');
        termSpan.textContent = cleanTerm;
        termSpan.title = cleanTerm;

        // Visual bar track
        const barTrack = document.createElement('div');
        barTrack.className = 'signal-bar-track';

        const barFill = document.createElement('div');
        const fillPct = Math.min(100, Math.max(5, (Math.abs(item.contribution || 0) / maxContrib) * 100));
        barFill.style.width = `${fillPct}%`;

        // Direction indicator
        const dirBadge = document.createElement('span');
        dirBadge.className = 'signal-direction-badge';

        if (item.direction === 'spam') {
          barFill.className = 'signal-bar-fill-spam';
          dirBadge.classList.add('direction-spam');
          dirBadge.textContent = '+ Spam';
        } else {
          barFill.className = 'signal-bar-fill-ham';
          dirBadge.classList.add('direction-ham');
          dirBadge.textContent = '- Legitimate';
        }

        barTrack.appendChild(barFill);
        row.appendChild(termSpan);
        row.appendChild(barTrack);
        row.appendChild(dirBadge);

        signalsList.appendChild(row);
      });
    }

    // Smooth scroll to result
    resultCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  // --------------------------------------------------------------------------
  // Form Submission Handler
  // --------------------------------------------------------------------------

  async function handleFormSubmit(e) {
    if (e) e.preventDefault();

    if (!validateInput()) {
      return;
    }

    const payload = {
      subject: (subjectInput.value || '').trim(),
      body: (bodyInput.value || '').trim()
    };

    // UI Loading state
    analyzeBtn.disabled = true;
    analyzeBtnText.textContent = 'Analyzing...';
    analyzeBtnSpinner.classList.remove('hidden');
    clearBtn.disabled = true;
    sampleSpamBtn.disabled = true;
    sampleHamBtn.disabled = true;
    sampleBorderlineBtn.disabled = true;

    // Timer for waking banner
    let wakingBannerTimer = setTimeout(function () {
      wakingBanner.classList.remove('hidden');
    }, WAKING_BANNER_DELAY_MS);

    try {
      const resultData = await callPredictApi(payload, false);
      clearTimeout(wakingBannerTimer);
      wakingBanner.classList.add('hidden');
      renderPredictionResult(resultData);
    } catch (err) {
      clearTimeout(wakingBannerTimer);
      wakingBanner.classList.add('hidden');

      generalErrorMessage.textContent = err.message || 'An unexpected error occurred while communicating with the server.';
      generalError.classList.remove('hidden');
      retryBtn.classList.remove('hidden');
    } finally {
      analyzeBtn.disabled = false;
      analyzeBtnText.textContent = 'Analyze Email';
      analyzeBtnSpinner.classList.add('hidden');
      clearBtn.disabled = false;
      sampleSpamBtn.disabled = false;
      sampleHamBtn.disabled = false;
      sampleBorderlineBtn.disabled = false;
    }
  }

  // --------------------------------------------------------------------------
  // Event Listeners
  // --------------------------------------------------------------------------

  emailForm.addEventListener('submit', handleFormSubmit);

  bodyInput.addEventListener('input', function () {
    updateCharCount();
    if (!bodyError.classList.contains('hidden')) {
      bodyError.classList.add('hidden');
      bodyError.textContent = '';
    }
  });

  subjectInput.addEventListener('input', updateCharCount);

  clearBtn.addEventListener('click', function () {
    subjectInput.value = '';
    bodyInput.value = '';
    updateCharCount();
    bodyError.classList.add('hidden');
    bodyError.textContent = '';
    generalError.classList.add('hidden');
    generalErrorMessage.textContent = '';
    wakingBanner.classList.add('hidden');
    resultCard.classList.add('hidden');
    subjectInput.focus();
  });

  retryBtn.addEventListener('click', function () {
    handleFormSubmit();
  });

  // Sample Loaders
  sampleSpamBtn.addEventListener('click', function () {
    subjectInput.value = SAMPLES.spam.subject;
    bodyInput.value = SAMPLES.spam.body;
    updateCharCount();
    bodyError.classList.add('hidden');
    generalError.classList.add('hidden');
    bodyInput.focus();
  });

  sampleHamBtn.addEventListener('click', function () {
    subjectInput.value = SAMPLES.ham.subject;
    bodyInput.value = SAMPLES.ham.body;
    updateCharCount();
    bodyError.classList.add('hidden');
    generalError.classList.add('hidden');
    bodyInput.focus();
  });

  sampleBorderlineBtn.addEventListener('click', function () {
    subjectInput.value = SAMPLES.borderline.subject;
    bodyInput.value = SAMPLES.borderline.body;
    updateCharCount();
    bodyError.classList.add('hidden');
    generalError.classList.add('hidden');
    bodyInput.focus();
  });

  // Initial Boot
  checkServerHealth();
  loadModelInfo();
  updateCharCount();

})();
