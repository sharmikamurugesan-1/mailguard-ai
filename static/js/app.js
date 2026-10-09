/**
 * MailGuard AI - Client Application Logic (Cyber Sentinel Design System)
 * Vanilla JavaScript, zero external dependencies, strict CSP compliant.
 * DOM manipulation via textContent and createElement only (zero unsafe HTML injection).
 */

(function () {
  'use strict';

  // Constants
  var MAX_INPUT_CHARS = 20000;
  var REQUEST_TIMEOUT_MS = 90000; // 90 seconds
  var WAKING_BANNER_DELAY_MS = 5000; // 5 seconds

  // Theme Elements
  var themeToggleBtn = document.getElementById('theme-toggle-btn');
  var themeIcon = document.getElementById('theme-icon');
  var themeText = document.getElementById('theme-text');

  // DOM Elements
  var statusDot = document.getElementById('status-dot');
  var statusText = document.getElementById('status-text');

  var emailForm = document.getElementById('email-form');
  var subjectInput = document.getElementById('subject-input');
  var bodyInput = document.getElementById('body-input');
  var bodyCharCounter = document.getElementById('body-char-counter');
  var totalCharCounter = document.getElementById('total-char-counter');
  var bodyError = document.getElementById('body-error');
  var generalError = document.getElementById('general-error');
  var generalErrorMessage = document.getElementById('general-error-message');
  var retryBtn = document.getElementById('retry-btn');
  var wakingBanner = document.getElementById('waking-banner');

  var analyzeBtn = document.getElementById('analyze-btn');
  var analyzeBtnText = document.getElementById('analyze-btn-text');
  var analyzeBtnSpinner = document.getElementById('analyze-btn-spinner');
  var clearBtn = document.getElementById('clear-btn');

  var sampleSpamBtn = document.getElementById('sample-spam-btn');
  var sampleHamBtn = document.getElementById('sample-ham-btn');
  var sampleBorderlineBtn = document.getElementById('sample-borderline-btn');

  // Result Elements
  var resultSkeleton = document.getElementById('result-skeleton');
  var resultCard = document.getElementById('result-card');
  var verdictBanner = document.getElementById('verdict-banner');
  var verdictIcon = document.getElementById('verdict-icon');
  var verdictTitle = document.getElementById('verdict-title');
  var riskBadge = document.getElementById('risk-badge');
  var confidenceValue = document.getElementById('confidence-value');
  var confidenceBar = document.getElementById('confidence-bar');
  var probabilitySubtext = document.getElementById('probability-subtext');
  var reliabilityLevelPill = document.getElementById('reliability-level-pill');
  var warningsList = document.getElementById('warnings-list');
  var signalsList = document.getElementById('signals-list');

  // Model Info Elements
  var metaModelType = document.getElementById('meta-model-type');
  var metaVectorizer = document.getElementById('meta-vectorizer');
  var metaDatasetName = document.getElementById('meta-dataset-name');
  var metaCodeLicense = document.getElementById('meta-code-license');
  var metaDatasetLicense = document.getElementById('meta-dataset-license');
  var metaDatasetSplit = document.getElementById('meta-dataset-split');
  var metaClassBalance = document.getElementById('meta-class-balance');
  var metaSelectionCriterion = document.getElementById('meta-selection-criterion');
  var metaAcc = document.getElementById('meta-acc');
  var metaPrec = document.getElementById('meta-prec');
  var metaRec = document.getElementById('meta-rec');
  var metaF1 = document.getElementById('meta-f1');
  var metaFp = document.getElementById('meta-fp');
  var metaFn = document.getElementById('meta-fn');
  var metaLimitationsList = document.getElementById('meta-limitations-list');

  // Sample Data Definitions
  var SAMPLES = {
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
  var WARNING_MESSAGES = {
    near_decision_boundary: 'Classification score is close to the decision boundary (0.35–0.65).',
    short_input: 'Input message is very short (< 10 tokens), which may reduce statistical confidence.',
    low_vocab_coverage: 'Low vocabulary coverage: over half of these words were not observed in training data.',
    non_english_suspected: 'Input appears to contain non-English or non-Latin characters. Preprocessing is English-oriented.',
    dataset_age_notice: 'Trained on 2000s-era Enron corporate emails; modern phrasing or synthetic scams may differ.'
  };

  // --------------------------------------------------------------------------
  // Theme Management (Cyber Sentinel Light/Dark)
  // --------------------------------------------------------------------------

  function updateThemeButtonUI(theme) {
    if (!themeToggleBtn) return;
    var isDark = theme === 'dark';
    themeToggleBtn.setAttribute('aria-pressed', isDark ? 'true' : 'false');
    if (themeIcon) {
      themeIcon.textContent = isDark ? '☀️' : '🌙';
    }
    if (themeText) {
      themeText.textContent = isDark ? 'Light' : 'Dark';
    }
  }

  function initTheme() {
    var current = document.documentElement.getAttribute('data-theme') || 'light';
    updateThemeButtonUI(current);

    if (themeToggleBtn) {
      themeToggleBtn.addEventListener('click', function () {
        var active = document.documentElement.getAttribute('data-theme') || 'light';
        var next = active === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        updateThemeButtonUI(next);
        try {
          localStorage.setItem('mailguard_theme', next);
        } catch (e) {}
      });
    }
  }

  // --------------------------------------------------------------------------
  // Server Health & Metadata Loading
  // --------------------------------------------------------------------------

  async function checkServerHealth() {
    try {
      var res = await fetch('/api/health');
      if (!res.ok) throw new Error('Health check non-200');
      var data = await res.json();

      statusDot.className = 'status-indicator';
      if (data.status === 'healthy' && data.model_loaded) {
        statusDot.classList.add('status-online');
        statusText.textContent = 'Server Online';
      } else {
        statusDot.classList.add('status-waking');
        statusText.textContent = 'Waking up...';
      }
    } catch (e) {
      statusDot.className = 'status-indicator status-offline';
      statusText.textContent = 'Server Offline';
    }
  }

  // Bounded re-check on tab visibilitychange (only if tab was hidden > 5 minutes)
  var lastHiddenTimestamp = null;
  var isRecheckingHealth = false;

  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'hidden') {
      lastHiddenTimestamp = Date.now();
    } else if (document.visibilityState === 'visible') {
      if (lastHiddenTimestamp && (Date.now() - lastHiddenTimestamp > 5 * 60 * 1000)) {
        lastHiddenTimestamp = null;
        runBoundedHealthRecheck();
      }
    }
  });

  async function runBoundedHealthRecheck() {
    if (isRecheckingHealth) return;
    isRecheckingHealth = true;
    var maxAttempts = 3;
    var delays = [1000, 2000, 4000];

    for (var attempt = 0; attempt < maxAttempts; attempt++) {
      try {
        var res = await fetch('/api/health');
        if (res.ok) {
          var data = await res.json();
          if (data.status === 'healthy' && data.model_loaded) {
            statusDot.className = 'status-indicator status-online';
            statusText.textContent = 'Server Online';
            break;
          } else {
            statusDot.className = 'status-indicator status-waking';
            statusText.textContent = 'Waking up...';
          }
        } else {
          statusDot.className = 'status-indicator status-offline';
          statusText.textContent = 'Server Offline';
        }
      } catch (e) {
        statusDot.className = 'status-indicator status-offline';
        statusText.textContent = 'Server Offline';
      }
      if (attempt < maxAttempts - 1) {
        await new Promise(function (resolve) { setTimeout(resolve, delays[attempt]); });
      }
    }
    isRecheckingHealth = false;
  }

  async function loadModelInfo() {
    try {
      var res = await fetch('/api/model-info');
      if (!res.ok) throw new Error('Failed to load model info');
      var data = await res.json();

      metaModelType.textContent = data.model_type || 'Calibrated Linear SVM';
      metaVectorizer.textContent = data.vectorizer || 'TF-IDF';
      metaDatasetName.textContent = data.dataset_name || 'Enron Spam Dataset';

      if (metaCodeLicense) {
        metaCodeLicense.textContent = data.code_license || 'MIT';
      }
      metaDatasetLicense.textContent = data.dataset_repo_license || data.dataset_repository_license || data.dataset_license || 'GNU General Public License v3.0';

      var nTrain = data.n_train ? data.n_train.toLocaleString() : '24,369';
      var nTest = data.n_test ? data.n_test.toLocaleString() : '6,093';
      if (metaDatasetSplit) {
        metaDatasetSplit.textContent = `${nTrain} / ${nTest} (80/20)`;
      }

      var nHam = data.class_counts ? data.class_counts.ham.toLocaleString() : '15,910';
      var nSpam = data.class_counts ? data.class_counts.spam.toLocaleString() : '14,552';
      if (metaClassBalance) {
        metaClassBalance.textContent = `${nHam} ham / ${nSpam} spam`;
      }

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

      var limitations = data.limitations || [];
      limitations.forEach(function (limText) {
        var li = document.createElement('li');
        // Sanitized wording: replace generic language detection claim with script check
        var safeText = limText.replace(/language detection/gi, 'script check (heuristic)');
        li.textContent = safeText;
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
    var subLen = (subjectInput.value || '').length;
    var bodyLen = (bodyInput.value || '').length;
    var total = subLen + bodyLen;

    // Body counter shows body characters only
    if (bodyCharCounter) {
      bodyCharCounter.textContent = `${bodyLen.toLocaleString()} / ${MAX_INPUT_CHARS.toLocaleString()}`;
      if (total > MAX_INPUT_CHARS) {
        bodyCharCounter.classList.add('counter-exceeded');
      } else {
        bodyCharCounter.classList.remove('counter-exceeded');
      }
    }

    // Total counter shows subject + body combined
    if (totalCharCounter) {
      totalCharCounter.textContent = `Total: ${total.toLocaleString()} / ${MAX_INPUT_CHARS.toLocaleString()}`;
      if (total > MAX_INPUT_CHARS) {
        totalCharCounter.classList.add('counter-exceeded');
      } else {
        totalCharCounter.classList.remove('counter-exceeded');
      }
    }
  }

  function validateInput() {
    var rawBody = bodyInput.value || '';
    var trimmedBody = rawBody.trim();
    var totalLen = (subjectInput.value || '').length + rawBody.length;

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
  // Display Layer Token Formatter
  // --------------------------------------------------------------------------

  function formatDisplayTerm(term) {
    if (!term) return '';
    return term
      .replace(/__number__|<number>/g, '[Number]')
      .replace(/__url__|<url>/g, '[Link]')
      .replace(/__email__|<email>/g, '[Email]')
      .replace(/__currency__|<currency>/g, '[Amount]');
  }

  // --------------------------------------------------------------------------
  // API Prediction Fetch with Timeout & 1 Automatic Retry
  // --------------------------------------------------------------------------

  async function callPredictApi(payload, isRetry) {
    var controller = new AbortController();
    var timeoutId = setTimeout(function () {
      controller.abort();
    }, REQUEST_TIMEOUT_MS);

    try {
      var response = await fetch('/api/predict', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload),
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      var data = await response.json().catch(function () {
        return null;
      });

      if (!response.ok) {
        var errorMsg = data && data.error && data.error.message
          ? data.error.message
          : `Server returned error (${response.status})`;
        throw new Error(errorMsg);
      }

      return data;
    } catch (err) {
      clearTimeout(timeoutId);

      var isTimeout = err.name === 'AbortError';
      var isNetwork = !navigator.onLine || err.message.includes('Failed to fetch') || isTimeout;

      if (!isRetry && isNetwork) {
        return await callPredictApi(payload, true);
      }

      throw err;
    }
  }

  // --------------------------------------------------------------------------
  // Render Result Card with Gentle Focus & Transitions
  // --------------------------------------------------------------------------

  function renderPredictionResult(data) {
    var prediction = data.prediction || 'uncertain';
    var labelDisplay = data.label_display || 'Needs review';
    var riskLevel = (data.risk_level || 'medium').toLowerCase();
    var conf = typeof data.confidence === 'number' ? data.confidence : 0.5;
    var spamProb = typeof data.spam_probability === 'number' ? data.spam_probability : 0.5;

    // Reset card classes
    resultCard.classList.remove('hidden', 'verdict-spam-border', 'verdict-ham-border', 'verdict-uncertain-border', 'verdict-fade-in');
    verdictIcon.className = 'verdict-icon';
    riskBadge.className = 'risk-badge';

    // Set Verdict Styling & Icons
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
    var confPct = Math.min(100, Math.max(0, conf * 100)).toFixed(1);
    confidenceValue.textContent = `${confPct}%`;
    confidenceBar.style.width = `${confPct}%`;
    probabilitySubtext.textContent = `Calibrated spam probability: ${spamProb.toFixed(4)}`;

    // Reliability & Warnings
    var rel = data.reliability || { level: 'medium', warnings: [] };
    reliabilityLevelPill.textContent = `LEVEL: ${rel.level.toUpperCase()}`;

    while (warningsList.firstChild) {
      warningsList.removeChild(warningsList.firstChild);
    }

    var warnings = rel.warnings || [];
    if (warnings.length === 0) {
      var li = document.createElement('li');
      li.className = 'warning-item';
      li.textContent = 'No data heuristics triggered; standard input length and vocabulary coverage.';
      warningsList.appendChild(li);
    } else {
      warnings.forEach(function (code) {
        var wLi = document.createElement('li');
        wLi.className = 'warning-item';
        if (code !== 'dataset_age_notice') {
          wLi.classList.add('warning-item-warn');
        }
        var text = WARNING_MESSAGES[code] || `Notice: ${code}`;
        wLi.textContent = text;
        warningsList.appendChild(wLi);
      });
    }

    // Signals Rendering with Display Mapping
    while (signalsList.firstChild) {
      signalsList.removeChild(signalsList.firstChild);
    }

    var signals = data.signals || [];
    if (signals.length === 0) {
      var emptyNote = document.createElement('p');
      emptyNote.className = 'footnote';
      emptyNote.textContent = 'No significant vocabulary feature contributions identified for this text.';
      signalsList.appendChild(emptyNote);
    } else {
      var maxContrib = 0.0001;
      signals.forEach(function (s) {
        var val = Math.abs(s.contribution || 0);
        if (val > maxContrib) maxContrib = val;
      });

      signals.forEach(function (item) {
        var row = document.createElement('div');
        row.className = 'signal-row';

        // Term name with human label mapping in display layer
        var termSpan = document.createElement('span');
        termSpan.className = 'signal-term';
        var displayTerm = formatDisplayTerm(item.term || '');
        termSpan.textContent = displayTerm;
        termSpan.title = displayTerm;

        // Visual bar track
        var barTrack = document.createElement('div');
        barTrack.className = 'signal-bar-track';

        var barFill = document.createElement('div');
        var fillPct = Math.min(100, Math.max(5, (Math.abs(item.contribution || 0) / maxContrib) * 100));
        barFill.style.width = `${fillPct}%`;

        // Direction indicator
        var dirBadge = document.createElement('span');
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

    // Trigger smooth fade-in
    resultCard.classList.add('verdict-fade-in');

    // Focus without jumping, gentle scroll only if offscreen
    if (verdictTitle) {
      verdictTitle.focus({ preventScroll: true });
    }
    var rect = resultCard.getBoundingClientRect();
    var isOffScreen = rect.top < 0 || rect.bottom > (window.innerHeight || document.documentElement.clientHeight);
    var prefersReducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (isOffScreen && !prefersReducedMotion) {
      resultCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }

  // --------------------------------------------------------------------------
  // Form Submission Handler
  // --------------------------------------------------------------------------

  async function handleFormSubmit(e) {
    if (e) e.preventDefault();

    if (!validateInput()) {
      return;
    }

    var payload = {
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

    // Show skeleton, hide existing result card to eliminate layout jump
    if (resultSkeleton) {
      resultSkeleton.classList.remove('hidden');
    }
    resultCard.classList.add('hidden');

    var wakingBannerTimer = setTimeout(function () {
      wakingBanner.classList.remove('hidden');
    }, WAKING_BANNER_DELAY_MS);

    try {
      var resultData = await callPredictApi(payload, false);
      clearTimeout(wakingBannerTimer);
      wakingBanner.classList.add('hidden');
      if (resultSkeleton) {
        resultSkeleton.classList.add('hidden');
      }
      renderPredictionResult(resultData);
    } catch (err) {
      clearTimeout(wakingBannerTimer);
      wakingBanner.classList.add('hidden');
      if (resultSkeleton) {
        resultSkeleton.classList.add('hidden');
      }

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

  // Keyboard shortcut Ctrl+Enter / Cmd+Enter
  function handleFormKeydown(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      handleFormSubmit();
    }
  }

  bodyInput.addEventListener('keydown', handleFormKeydown);
  subjectInput.addEventListener('keydown', handleFormKeydown);

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
    if (resultSkeleton) {
      resultSkeleton.classList.add('hidden');
    }
    resultCard.classList.add('hidden');
    subjectInput.focus();
  });

  retryBtn.addEventListener('click', function () {
    handleFormSubmit();
  });

  // Sample Loaders (Click 1 fills form, Click 2 analyzes)
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
  initTheme();
  checkServerHealth();
  loadModelInfo();
  updateCharCount();

})();
