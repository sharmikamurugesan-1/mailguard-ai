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

  // Phase 11C Elements
  var dropZone = document.getElementById('drop-zone');
  var dropOverlay = document.getElementById('drop-overlay');
  var filePickerInput = document.getElementById('file-picker-input');
  var filePickerBtn = document.getElementById('file-picker-btn');

  var copyResultBtn = document.getElementById('copy-result-btn');
  var copyBtnText = document.getElementById('copy-btn-text');
  var copyBtnIcon = document.getElementById('copy-btn-icon');

  var uncertainBanner = document.getElementById('uncertain-banner');
  var uncertainBannerText = document.getElementById('uncertain-banner-text');

  var highlightSection = document.getElementById('highlight-section');
  var highlightPreviewBox = document.getElementById('highlight-preview-box');
  var stopwordToggleBtn = document.getElementById('stopword-toggle-btn');
  var stopwordToggleText = document.getElementById('stopword-toggle-text');
  var stopwordToggleIcon = document.getElementById('stopword-toggle-icon');
  var stopwordCountBadge = document.getElementById('stopword-count-badge');
  var toastContainer = document.getElementById('toast-container');

  // Application State
  var filterStopwords = true;
  var currentPredictionData = null;
  var currentInputText = { subject: '', body: '' };

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
      subject: 're : no java ?',
      body: 'you are cracking me up . basically you are the only thing keeping me awake today . .'
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
  // Accessible Toast Feedback
  // --------------------------------------------------------------------------

  function showToast(message, type) {
    if (!toastContainer) return;
    var toast = document.createElement('div');
    toast.className = 'toast toast-' + (type || 'info');

    var iconSpan = document.createElement('span');
    iconSpan.setAttribute('aria-hidden', 'true');
    iconSpan.textContent = type === 'success' ? '✓' : type === 'warn' ? '⚠' : type === 'error' ? '✖' : 'ℹ';

    var textSpan = document.createElement('span');
    textSpan.textContent = message;

    toast.appendChild(iconSpan);
    toast.appendChild(textSpan);
    toastContainer.appendChild(toast);

    setTimeout(function () {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
    }, 3500);
  }

  // --------------------------------------------------------------------------
  // EML & Text File Parsing (Client-Side, 1 MB Limit)
  // --------------------------------------------------------------------------

  function parseEml(rawText) {
    if (!rawText) return { subject: '', body: '' };

    // Normalize newlines (\r\r\n -> \n, \r\n -> \n, \r -> \n)
    var normalized = rawText.replace(/\r+\n?/g, '\n');
    var headerEndIndex = normalized.indexOf('\n\n');
    var headers = "";
    var body = normalized;
    if (headerEndIndex !== -1) {
      headers = normalized.substring(0, headerEndIndex);
      body = normalized.substring(headerEndIndex).trim();
    }

    var subject = "";
    var subjectMatch = headers.match(/^Subject:\s*([^\n]+(?:\n[ \t]+[^\n]+)*)/im);
    if (subjectMatch) {
      subject = subjectMatch[1].replace(/\n[ \t]+/g, ' ').trim();
    }

    // If multipart MIME, extract text/plain section
    if (headers.indexOf('multipart') !== -1 || body.indexOf('Content-Type:') !== -1) {
      var plainMatch = body.match(/Content-Type:\s*text\/plain[^;\n]*;?[^\n]*\n(?:\n)([\s\S]*?)(?=\n--|$)/i);
      if (plainMatch) {
        body = plainMatch[1].trim();
      } else {
        // Fallback: strip html tags if html only
        var htmlMatch = body.match(/Content-Type:\s*text\/html[^;\n]*;?[^\n]*\n(?:\n)([\s\S]*?)(?=\n--|$)/i);
        if (htmlMatch) {
          body = htmlMatch[1].replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
        }
      }
    }

    return {
      subject: subject,
      body: body.trim()
    };
  }

  function handleFileSelection(file) {
    if (!file) return;

    // 1 MB limit check
    var MAX_FILE_BYTES = 1024 * 1024;
    if (file.size > MAX_FILE_BYTES) {
      var sizeMb = (file.size / (1024 * 1024)).toFixed(2);
      bodyError.textContent = `File exceeds the 1 MB size limit (${sizeMb} MB).`;
      bodyError.classList.remove('hidden');
      showToast('File too large (limit: 1 MB)', 'error');
      return;
    }

    var nameParts = file.name.split('.');
    var ext = nameParts.length > 1 ? nameParts.pop().toLowerCase() : '';
    if (ext !== 'txt' && ext !== 'eml') {
      bodyError.textContent = `Unsupported file type (.${ext || 'unknown'}). Please choose a .txt or .eml file.`;
      bodyError.classList.remove('hidden');
      showToast('Unsupported file type', 'error');
      return;
    }

    var reader = new FileReader();
    reader.onload = function (e) {
      var raw = e.target.result || '';
      if (ext === 'eml') {
        var parsed = parseEml(raw);
        if (parsed.subject) {
          subjectInput.value = parsed.subject;
        }
        bodyInput.value = parsed.body;
      } else {
        bodyInput.value = raw.trim();
      }

      updateCharCount();
      bodyError.classList.add('hidden');
      bodyError.textContent = '';
      showToast(`Loaded ${file.name} (${bodyInput.value.length.toLocaleString()} chars)`, 'success');
      bodyInput.focus();
    };

    reader.onerror = function () {
      bodyError.textContent = 'Could not read file. Please ensure it is a valid text file.';
      bodyError.classList.remove('hidden');
      showToast('Error reading file', 'error');
    };

    reader.onloadend = function () {
      if (filePickerInput) {
        filePickerInput.value = '';
      }
    };

    reader.readAsText(file, 'utf-8');
  }

  // --------------------------------------------------------------------------
  // Copy Result Summary
  // --------------------------------------------------------------------------

  function fallbackCopyText(text) {
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    try {
      document.execCommand('copy');
      showToast('Analysis summary copied to clipboard', 'success');
    } catch (e) {
      showToast('Could not copy to clipboard', 'error');
    }
    document.body.removeChild(ta);
  }

  function copyResultSummary() {
    if (!currentPredictionData) {
      showToast('No analysis result to copy', 'warn');
      return;
    }

    var data = currentPredictionData;
    var pred = data.prediction || 'uncertain';
    var label = data.label_display || 'Needs review';
    var risk = (data.risk_level || 'medium').toUpperCase();
    var conf = typeof data.confidence === 'number' ? (data.confidence * 100).toFixed(1) + '%' : '--';
    var prob = typeof data.spam_probability === 'number' ? data.spam_probability.toFixed(4) : '--';
    var rel = data.reliability ? (data.reliability.level || 'medium').toUpperCase() : '--';

    var lines = [
      'MailGuard AI - Email Analysis Summary',
      '======================================',
      `Verdict:          ${label} (${pred.toUpperCase()})`,
      `Risk Level:       ${risk}`,
      `Model Confidence: ${conf}`,
      `Calibrated Spam P:${prob}`,
      `Reliability Level:${rel}`,
      '',
      'Top Contributing Tokens:'
    ];

    var tokens = data.top_tokens || data.signals || [];
    if (tokens.length === 0) {
      lines.push('  (No significant feature tokens detected)');
    } else {
      tokens.slice(0, 8).forEach(function (t) {
        var name = formatDisplayTerm(t.token || t.term || '');
        var dir = t.direction === 'spam' ? '+Spam' : '-Legitimate';
        var w = Math.abs(t.weight || t.contribution || 0).toFixed(4);
        lines.push(`  - ${name.padEnd(20)} ${dir.padEnd(12)} (weight: ${w})`);
      });
    }

    lines.push('');
    lines.push('Note: MailGuard AI provides statistical probability estimates, not absolute guarantees.');

    var summaryText = lines.join('\n');

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(summaryText).then(function () {
        if (copyBtnText) copyBtnText.textContent = 'Copied!';
        if (copyBtnIcon) copyBtnIcon.textContent = '✓';
        if (copyResultBtn) copyResultBtn.classList.add('copied');
        showToast('Analysis summary copied to clipboard', 'success');

        setTimeout(function () {
          if (copyBtnText) copyBtnText.textContent = 'Copy Result';
          if (copyBtnIcon) copyBtnIcon.textContent = '📋';
          if (copyResultBtn) copyResultBtn.classList.remove('copied');
        }, 2000);
      }).catch(function () {
        fallbackCopyText(summaryText);
      });
    } else {
      fallbackCopyText(summaryText);
    }
  }

  // --------------------------------------------------------------------------
  // In-Text Token Highlighter (createElement & textContent Only)
  // --------------------------------------------------------------------------

  function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  function renderInTextHighlights(subject, body, tokens, filterActive) {
    if (!highlightPreviewBox) return;

    while (highlightPreviewBox.firstChild) {
      highlightPreviewBox.removeChild(highlightPreviewBox.firstChild);
    }

    var combinedText = (subject ? 'Subject: ' + subject + '\n\n' : '') + (body || '');
    if (!combinedText.trim()) {
      var emptyNotice = document.createElement('span');
      emptyNotice.className = 'token-neutral-sample';
      emptyNotice.textContent = 'No message content available to highlight.';
      highlightPreviewBox.appendChild(emptyNotice);
      return;
    }

    // Determine candidate tokens based on stopword filter
    var activeTokens = [];
    var hiddenStopwordCount = 0;

    (tokens || []).forEach(function (t) {
      if (t.is_stopword) {
        hiddenStopwordCount++;
        if (!filterActive) {
          activeTokens.push(t);
        }
      } else {
        activeTokens.push(t);
      }
    });

    // Update stopword count badge
    if (stopwordCountBadge) {
      if (filterActive) {
        stopwordCountBadge.textContent = hiddenStopwordCount > 0
          ? `${hiddenStopwordCount} common word${hiddenStopwordCount === 1 ? '' : 's'} hidden`
          : '0 common words in text';
      } else {
        stopwordCountBadge.textContent = 'All tokens visible (including common words)';
      }
    }

    if (activeTokens.length === 0) {
      highlightPreviewBox.appendChild(document.createTextNode(combinedText));
      return;
    }

    // Sort tokens by string length descending so multi-word n-grams match first
    activeTokens.sort(function (a, b) {
      var lenA = (a.token || a.term || '').length;
      var lenB = (b.token || b.term || '').length;
      return lenB - lenA;
    });

    // Build regex mapping
    var tokenMap = {};
    var patternParts = [];

    activeTokens.forEach(function (tok) {
      var term = (tok.token || tok.term || '').trim();
      if (!term) return;

      var escaped;
      if (term === '__url__' || term === '<url>') {
        escaped = '(?:https?://|www\\.)\\S+';
      } else if (term === '__number__' || term === '<number>') {
        escaped = '\\b\\d+(?:[.,]\\d+)*\\b';
      } else if (term === '__email__' || term === '<email>') {
        escaped = '\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}\\b';
      } else if (term === '__currency__' || term === '<currency>') {
        escaped = '[$£€¥]\\s*\\d+(?:[.,]\\d+)*|\\d+(?:[.,]\\d+)*\\s*[$£€¥]';
      } else {
        escaped = '\\b' + escapeRegExp(term) + '\\b';
      }

      patternParts.push(escaped);
      tokenMap[term.toLowerCase()] = tok;
    });

    if (patternParts.length === 0) {
      highlightPreviewBox.appendChild(document.createTextNode(combinedText));
      return;
    }

    var regex = new RegExp('(' + patternParts.join('|') + ')', 'gi');
    var chunks = combinedText.split(regex);

    chunks.forEach(function (chunk) {
      if (!chunk) return;

      var lowerChunk = chunk.toLowerCase();
      var matchedTok = tokenMap[lowerChunk];

      // Handle entity fallbacks if regex matched URL, number, etc.
      if (!matchedTok) {
        if (/^https?:\/\/|^www\./i.test(chunk)) {
          matchedTok = tokenMap['__url__'] || tokenMap['<url>'];
        } else if (/^\d+(?:[.,]\d+)*$/.test(chunk)) {
          matchedTok = tokenMap['__number__'] || tokenMap['<number>'];
        } else if (/^[$£€¥]/.test(chunk)) {
          matchedTok = tokenMap['__currency__'] || tokenMap['<currency>'];
        } else if (/@/.test(chunk)) {
          matchedTok = tokenMap['__email__'] || tokenMap['<email>'];
        }
      }

      if (matchedTok) {
        var mark = document.createElement('mark');
        var isSpam = matchedTok.direction === 'spam';
        mark.className = 'token-highlight ' + (isSpam ? 'token-spam' : 'token-ham');

        var sign = isSpam ? '+' : '-';
        var weightVal = Math.abs(matchedTok.weight || matchedTok.contribution || 0).toFixed(4);
        var dirLabel = isSpam ? 'Spam' : 'Legitimate';
        var tokName = matchedTok.token || matchedTok.term || chunk;

        mark.title = `${tokName} (${dirLabel} weight: ${sign}${weightVal})`;
        mark.setAttribute('aria-label', `${chunk}, ${dirLabel} token with weight ${sign}${weightVal}`);

        // Matched text node
        mark.appendChild(document.createTextNode(chunk));

        // Non-color cue badge
        var cue = document.createElement('span');
        cue.className = 'token-cue';
        cue.setAttribute('aria-hidden', 'true');
        cue.textContent = isSpam ? '▲' : '▼';
        mark.appendChild(cue);

        highlightPreviewBox.appendChild(mark);
      } else {
        // Plain text node
        highlightPreviewBox.appendChild(document.createTextNode(chunk));
      }
    });
  }

  // --------------------------------------------------------------------------
  // Signals List Renderer (Top Contributing Terms)
  // --------------------------------------------------------------------------

  function renderSignalsList(signals, filterActive) {
    if (!signalsList) return;

    while (signalsList.firstChild) {
      signalsList.removeChild(signalsList.firstChild);
    }

    var displaySignals = [];
    (signals || []).forEach(function (s) {
      if (s.is_stopword && filterActive) {
        return;
      }
      displaySignals.push(s);
    });

    if (displaySignals.length === 0) {
      var emptyNote = document.createElement('p');
      emptyNote.className = 'footnote';
      emptyNote.textContent = filterActive
        ? 'No non-stopword vocabulary features identified for this text.'
        : 'No significant vocabulary feature contributions identified for this text.';
      signalsList.appendChild(emptyNote);
      return;
    }

    var maxContrib = 0.0001;
    displaySignals.forEach(function (s) {
      var val = Math.abs(s.contribution || s.weight || 0);
      if (val > maxContrib) maxContrib = val;
    });

    displaySignals.forEach(function (item) {
      var row = document.createElement('div');
      row.className = 'signal-row';

      var termSpan = document.createElement('span');
      termSpan.className = 'signal-term';
      var displayTerm = formatDisplayTerm(item.term || item.token || '');
      termSpan.textContent = displayTerm;
      termSpan.title = displayTerm;

      var barTrack = document.createElement('div');
      barTrack.className = 'signal-bar-track';

      var barFill = document.createElement('div');
      var itemVal = Math.abs(item.contribution || item.weight || 0);
      var fillPct = Math.min(100, Math.max(5, (itemVal / maxContrib) * 100));
      barFill.style.width = `${fillPct}%`;

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

    // Set Verdict Styling, Icons & Uncertain Banner
    if (prediction === 'spam') {
      resultCard.classList.add('verdict-spam-border');
      verdictIcon.classList.add('verdict-icon-spam');
      verdictIcon.textContent = '🚨';
      verdictTitle.textContent = labelDisplay;
      if (uncertainBanner) uncertainBanner.classList.add('hidden');
    } else if (prediction === 'ham') {
      resultCard.classList.add('verdict-ham-border');
      verdictIcon.classList.add('verdict-icon-ham');
      verdictIcon.textContent = '✓';
      verdictTitle.textContent = labelDisplay;
      if (uncertainBanner) uncertainBanner.classList.add('hidden');
    } else {
      resultCard.classList.add('verdict-uncertain-border');
      verdictIcon.classList.add('verdict-icon-unc');
      verdictIcon.textContent = '⚖';
      verdictTitle.textContent = labelDisplay;
      if (uncertainBanner) {
        uncertainBanner.classList.remove('hidden');
        if (uncertainBannerText) {
          uncertainBannerText.textContent = `Calibrated spam probability (${spamProb.toFixed(4)}) falls within the [0.40, 0.60] borderline zone. Empirical 5-fold cross-validation on 24,369 training emails showed that 0.46% of messages fall into this band (nearly 50/50 ham vs spam). Automated classification is withheld; human review is recommended.`;
        }
      }
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

    // Interactive In-Text Highlights
    var tokensForHighlight = data.top_tokens || data.signals || [];
    renderInTextHighlights(currentInputText.subject, currentInputText.body, tokensForHighlight, filterStopwords);

    // Signals Rendering with Stopword Filtering
    renderSignalsList(data.signals || [], filterStopwords);

    // Trigger smooth fade-in
    resultCard.classList.add('verdict-fade-in');

    // Update session dashboard counters with real telemetry
    updateSessionStats(prediction);

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

    var subVal = (subjectInput.value || '').trim();
    var bodyVal = (bodyInput.value || '').trim();

    currentInputText.subject = subVal;
    currentInputText.body = bodyVal;

    var payload = {
      subject: subVal,
      body: bodyVal,
      filter_stopwords: filterStopwords
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
      currentPredictionData = resultData;
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

  // Phase 11C Event Listeners: Drag & Drop, File Picker, Copy, Stopword Toggle
  if (dropZone) {
    ['dragenter', 'dragover'].forEach(function (eventName) {
      dropZone.addEventListener(eventName, function (e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.add('drag-over');
        if (dropOverlay) dropOverlay.classList.remove('hidden');
      });
    });

    ['dragleave', 'dragend'].forEach(function (eventName) {
      dropZone.addEventListener(eventName, function (e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove('drag-over');
        if (dropOverlay) dropOverlay.classList.add('hidden');
      });
    });

    dropZone.addEventListener('drop', function (e) {
      e.preventDefault();
      e.stopPropagation();
      dropZone.classList.remove('drag-over');
      if (dropOverlay) dropOverlay.classList.add('hidden');
      if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        handleFileSelection(e.dataTransfer.files[0]);
      }
    });
  }

  if (filePickerBtn && filePickerInput) {
    filePickerBtn.addEventListener('click', function () {
      filePickerInput.click();
    });

    filePickerInput.addEventListener('change', function () {
      if (filePickerInput.files && filePickerInput.files.length > 0) {
        handleFileSelection(filePickerInput.files[0]);
      }
    });
  }

  if (copyResultBtn) {
    copyResultBtn.addEventListener('click', function () {
      copyResultSummary();
    });
  }

  if (stopwordToggleBtn) {
    stopwordToggleBtn.addEventListener('click', function () {
      filterStopwords = !filterStopwords;
      stopwordToggleBtn.setAttribute('aria-pressed', filterStopwords ? 'true' : 'false');
      stopwordToggleBtn.classList.toggle('active', filterStopwords);
      if (stopwordToggleText) {
        stopwordToggleText.textContent = filterStopwords ? 'Filter Common Words (ON)' : 'Filter Common Words (OFF)';
      }
      if (currentPredictionData) {
        renderInTextHighlights(
          currentInputText.subject,
          currentInputText.body,
          currentPredictionData.top_tokens || currentPredictionData.signals || [],
          filterStopwords
        );
        renderSignalsList(currentPredictionData.signals || [], filterStopwords);
      }
      showToast(filterStopwords ? 'Common words hidden' : 'All words visible', 'info');
    });
  }

  // --------------------------------------------------------------------------
  // Session Telemetry & Dashboard Counters (Phase 12A)
  // --------------------------------------------------------------------------

  var sessionStats = {
    total: 0,
    spam: 0,
    uncertain: 0,
    ham: 0
  };

  function updateSessionStats(prediction) {
    sessionStats.total++;
    if (prediction === 'spam') {
      sessionStats.spam++;
    } else if (prediction === 'uncertain') {
      sessionStats.uncertain++;
    } else {
      sessionStats.ham++;
    }

    var elTotal = document.getElementById('dash-stat-total');
    var elSpam = document.getElementById('dash-stat-spam');
    var elUnc = document.getElementById('dash-stat-uncertain');
    var elDonutNum = document.querySelector('.donut-circle .donut-num');

    if (elTotal) elTotal.textContent = String(sessionStats.total);
    if (elSpam) elSpam.textContent = String(sessionStats.spam);
    if (elUnc) elUnc.textContent = String(sessionStats.uncertain);
    if (elDonutNum) elDonutNum.textContent = String(sessionStats.total);
  }

  // --------------------------------------------------------------------------
  // App Shell & Hash-Based Routing (Phase 12A)
  // --------------------------------------------------------------------------

  var ROUTE_MAP = {
    '#/dashboard': { viewId: 'view-dashboard', navId: 'nav-dashboard', topNavId: null },
    '#/analyzer': { viewId: 'view-analyzer', navId: 'nav-analyzer', topNavId: null },
    '#/image-analysis': { viewId: 'view-image-analysis', navId: 'nav-image-analysis', topNavId: null },
    '#/reports': { viewId: 'view-reports', navId: 'nav-reports', topNavId: null },
    '#/settings': { viewId: 'view-settings', navId: 'nav-settings', topNavId: null },
    '#/home': { viewId: 'view-home', navId: null, topNavId: 'top-nav-home' },
    '#/features': { viewId: 'view-features', navId: null, topNavId: 'top-nav-features' },
    '#/model-card': { viewId: 'view-model-card', navId: null, topNavId: 'top-nav-model-card' },
    '#/docs': { viewId: 'view-docs', navId: null, topNavId: 'top-nav-docs' }
  };

  var appSidebar = document.getElementById('app-sidebar');
  var mobileMenuBtn = document.getElementById('mobile-menu-btn');
  var sidebarBackdrop = document.getElementById('sidebar-backdrop');
  var globalSearch = document.getElementById('global-search');
  var userChip = document.getElementById('user-chip');

  function closeMobileDrawer() {
    if (appSidebar) {
      appSidebar.classList.remove('drawer-open', 'open');
    }
    if (sidebarBackdrop) {
      sidebarBackdrop.classList.add('hidden');
    }
    if (mobileMenuBtn) {
      mobileMenuBtn.setAttribute('aria-expanded', 'false');
    }
  }

  function openMobileDrawer() {
    if (appSidebar) {
      appSidebar.classList.add('drawer-open', 'open');
    }
    if (sidebarBackdrop) {
      sidebarBackdrop.classList.remove('hidden');
    }
    if (mobileMenuBtn) {
      mobileMenuBtn.setAttribute('aria-expanded', 'true');
    }
  }

  function toggleMobileDrawer() {
    if (appSidebar && (appSidebar.classList.contains('drawer-open') || appSidebar.classList.contains('open'))) {
      closeMobileDrawer();
    } else {
      openMobileDrawer();
    }
  }

  function handleRoute(hash) {
    var rawHash = hash || window.location.hash || '#/dashboard';
    var routeConfig = ROUTE_MAP[rawHash];

    if (!routeConfig) {
      rawHash = '#/dashboard';
      routeConfig = ROUTE_MAP[rawHash];
    }

    // 1. Hide all view panels
    var viewPanels = document.querySelectorAll('.view-panel');
    viewPanels.forEach(function (panel) {
      panel.classList.add('hidden');
    });

    // 2. Show active view panel
    var activePanel = document.getElementById(routeConfig.viewId);
    if (activePanel) {
      activePanel.classList.remove('hidden');
      activePanel.focus({ preventScroll: true });
    }

    // 3. Update sidebar active links
    var sidebarLinks = document.querySelectorAll('.sidebar-nav-item');
    sidebarLinks.forEach(function (link) {
      link.classList.remove('active');
      link.removeAttribute('aria-current');
    });
    if (routeConfig.navId) {
      var activeSidebarLink = document.getElementById(routeConfig.navId);
      if (activeSidebarLink) {
        activeSidebarLink.classList.add('active');
        activeSidebarLink.setAttribute('aria-current', 'page');
      }
    }

    // 4. Update top-nav active links
    var topNavLinks = document.querySelectorAll('.top-nav-item');
    topNavLinks.forEach(function (link) {
      link.classList.remove('active');
      link.removeAttribute('aria-current');
    });
    if (routeConfig.topNavId) {
      var activeTopLink = document.getElementById(routeConfig.topNavId);
      if (activeTopLink) {
        activeTopLink.classList.add('active');
        activeTopLink.setAttribute('aria-current', 'page');
      }
    }

    // 5. Close mobile drawer on navigation
    closeMobileDrawer();
  }

  function initAppShell() {
    // Hash routing listeners
    window.addEventListener('hashchange', function () {
      handleRoute(window.location.hash);
    });

    // Mobile menu toggle button
    if (mobileMenuBtn) {
      mobileMenuBtn.addEventListener('click', function (e) {
        e.preventDefault();
        toggleMobileDrawer();
      });
    }

    // Mobile backdrop click
    if (sidebarBackdrop) {
      sidebarBackdrop.addEventListener('click', function () {
        closeMobileDrawer();
      });
    }

    // Escape key closes mobile drawer
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && appSidebar && (appSidebar.classList.contains('drawer-open') || appSidebar.classList.contains('open'))) {
        closeMobileDrawer();
        if (mobileMenuBtn) {
          mobileMenuBtn.focus();
        }
      }
    });

    // Global Search box
    if (globalSearch) {
      globalSearch.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
          e.preventDefault();
          var query = (globalSearch.value || '').trim().toLowerCase();
          if (!query) return;

          if (query.includes('anal') || query.includes('scan') || query.includes('spam') || query.includes('email')) {
            window.location.hash = '#/analyzer';
          } else if (query.includes('dash')) {
            window.location.hash = '#/dashboard';
          } else if (query.includes('imag') || query.includes('ocr')) {
            window.location.hash = '#/image-analysis';
          } else if (query.includes('rep') || query.includes('audit')) {
            window.location.hash = '#/reports';
          } else if (query.includes('set') || query.includes('pref')) {
            window.location.hash = '#/settings';
          } else if (query.includes('home') || query.includes('start')) {
            window.location.hash = '#/home';
          } else if (query.includes('feat')) {
            window.location.hash = '#/features';
          } else if (query.includes('model') || query.includes('card') || query.includes('spec') || query.includes('transpar')) {
            window.location.hash = '#/model-card';
          } else if (query.includes('doc') || query.includes('api')) {
            window.location.hash = '#/docs';
          } else {
            showToast('No match for "' + query + '". Try "analyzer", "model", or "docs".', 'warn');
          }
        }
      });
    }

    // User chip interaction
    if (userChip) {
      function handleUserChipActivation() {
        showToast('Logged in as Guest (demo session). All model transparency active.', 'info');
      }

      userChip.addEventListener('click', handleUserChipActivation);
      userChip.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleUserChipActivation();
        }
      });
    }

    // Initial route invocation
    if (!window.location.hash) {
      window.location.hash = '#/dashboard';
    } else {
      handleRoute(window.location.hash);
    }
  }

  // Initial Boot
  initTheme();
  checkServerHealth();
  loadModelInfo();
  updateCharCount();
  initAppShell();

})();
