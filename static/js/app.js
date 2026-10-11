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

  // Phase 12C Tab Elements
  var tabBtnContent = document.getElementById('tab-btn-content');
  var tabBtnHeaders = document.getElementById('tab-btn-headers');
  var tabPanelContent = document.getElementById('tab-panel-content');
  var tabPanelHeaders = document.getElementById('tab-panel-headers');
  var loadEmlSampleBtn = document.getElementById('load-eml-sample-btn');

  // Phase 12C Option Toggles
  var optExtractUrls = document.getElementById('opt-extract-urls');
  var optAnalyzeHeaders = document.getElementById('opt-analyze-headers');
  var optSuspiciousLinks = document.getElementById('opt-suspicious-links');
  var analyzerSensitivitySelect = document.getElementById('analyzer-sensitivity-select');

  // Phase 12E Settings & Options Elements
  var prefSensitivity = document.getElementById('pref-sensitivity');
  var prefScanUrls = document.getElementById('pref-scan-urls');
  var prefAnalyzeHeaders = document.getElementById('pref-analyze-headers');
  var settingsPreferencesForm = document.getElementById('settings-preferences-form');
  var resetPreferencesBtn = document.getElementById('reset-preferences-btn');
  var tabBtnPref = document.getElementById('tab-btn-pref');
  var tabBtnApi = document.getElementById('tab-btn-api');
  var tabBtnAccount = document.getElementById('tab-btn-account');
  var settingsPanelPref = document.getElementById('settings-panel-pref');
  var settingsPanelApi = document.getElementById('settings-panel-api');
  var settingsPanelAccount = document.getElementById('settings-panel-account');
  var clearLocalHistoryBtn = document.getElementById('clear-local-history-btn');
  var clearLocalSettingsBtn = document.getElementById('clear-local-settings-btn');

  // Phase 12C Report Elements
  var reportEmptyState = document.getElementById('report-empty-state');
  var reportSkeleton = document.getElementById('report-skeleton');
  var reportActiveView = document.getElementById('report-active-view');
  var newScanBtn = document.getElementById('new-scan-btn');
  var riskRingFill = document.getElementById('risk-ring-fill');
  var riskRingNum = document.getElementById('risk-ring-num');
  var riskRingBadge = document.getElementById('risk-ring-badge');
  var reportClassificationVal = document.getElementById('report-classification-val');
  var reportConfidenceVal = document.getElementById('report-confidence-val');
  var reportTimestampVal = document.getElementById('report-timestamp-val');
  var reportUncertainBanner = document.getElementById('report-uncertain-banner');
  var reportUncertainText = document.getElementById('report-uncertain-text');
  var indicatorCountBadge = document.getElementById('indicator-count-badge');
  var indicatorsChipsContainer = document.getElementById('indicators-chips-container');
  var findingsList = document.getElementById('findings-list');
  var btnPreviewOriginal = document.getElementById('btn-preview-original');
  var btnPreviewExtracted = document.getElementById('btn-preview-extracted');
  var previewFromVal = document.getElementById('preview-from-val');
  var previewSubjectVal = document.getElementById('preview-subject-val');
  var copyReportBtn = document.getElementById('copy-report-btn');
  var copyReportIcon = document.getElementById('copy-report-icon');
  var copyReportText = document.getElementById('copy-report-text');
  var exportJsonBtn = document.getElementById('export-json-btn');

  // Phase 12C Header Telemetry Elements
  var headersTelemetryEmpty = document.getElementById('headers-telemetry-empty');
  var headersTelemetryActive = document.getElementById('headers-telemetry-active');
  var hSpfVal = document.getElementById('h-spf-val');
  var hDkimVal = document.getElementById('h-dkim-val');
  var hDmarcVal = document.getElementById('h-dmarc-val');
  var hSenderMatchVal = document.getElementById('h-sender-match-val');
  var hHopsVal = document.getElementById('h-hops-val');
  var rawHeadersPre = document.getElementById('raw-headers-pre');
  var copyRawHeadersBtn = document.getElementById('copy-raw-headers-btn');

  // Phase 12D Local Analytics & Reports Elements
  var dashStatTotal = document.getElementById('dash-stat-total');
  var dashStatTotalSub = document.getElementById('dash-stat-total-sub');
  var dashStatSpam = document.getElementById('dash-stat-spam');
  var dashStatSpamSub = document.getElementById('dash-stat-spam-sub');
  var dashStatUncertain = document.getElementById('dash-stat-uncertain');
  var dashStatUncertainSub = document.getElementById('dash-stat-uncertain-sub');
  var dashStatSafe = document.getElementById('dash-stat-safe');
  var dashStatSafeSub = document.getElementById('dash-stat-safe-sub');

  var donutSegHam = document.getElementById('donut-seg-ham');
  var donutSegUnc = document.getElementById('donut-seg-unc');
  var donutSegSpam = document.getElementById('donut-seg-spam');
  var donutNum = document.getElementById('donut-num');
  var donutLegendSpam = document.getElementById('donut-legend-spam');
  var donutLegendUnc = document.getElementById('donut-legend-unc');
  var donutLegendHam = document.getElementById('donut-legend-ham');

  var dashRecentEmpty = document.getElementById('dash-recent-empty');
  var dashRecentActive = document.getElementById('dash-recent-active');
  var dashRecentTbody = document.getElementById('dash-recent-tbody');

  var storageFallbackBanner = document.getElementById('storage-fallback-banner');
  var historySearchInput = document.getElementById('history-search-input');
  var historyFilterVerdict = document.getElementById('history-filter-verdict');
  var historyFilterSource = document.getElementById('history-filter-source');
  var historySortBy = document.getElementById('history-sort-by');
  var historyDateStart = document.getElementById('history-date-start');
  var historyDateEnd = document.getElementById('history-date-end');
  var exportHistoryCsvBtn = document.getElementById('export-history-csv-btn');
  var exportHistoryJsonBtn = document.getElementById('export-history-json-btn');
  var clearHistoryBtn = document.getElementById('clear-history-btn');

  var historyEmptyState = document.getElementById('history-empty-state');
  var historyEmptyTitle = document.getElementById('history-empty-title');
  var historyEmptyDesc = document.getElementById('history-empty-desc');
  var historyTableWrapper = document.getElementById('history-table-wrapper');
  var historyTbody = document.getElementById('history-tbody');

  var historyPaginationBar = document.getElementById('history-pagination-bar');
  var historyPaginationInfo = document.getElementById('history-pagination-info');
  var historyPagePrev = document.getElementById('history-page-prev');
  var historyPageNext = document.getElementById('history-page-next');
  var historyPageCurrent = document.getElementById('history-page-current');

  // Application State
  var filterStopwords = true;
  var currentPredictionData = null;
  var currentAnalysisData = null;
  var currentRawEml = null;
  var currentSourceType = 'paste';
  var reportsCurrentPage = 1;
  var REPORTS_PAGE_SIZE = 5;
  var isPreviewOriginal = true;
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
    },
    emlSample: {
      raw: 'Received: from mail.suspicious-relay.biz (185.220.101.5) by mx.google.com; Fri, 09 Oct 2026 12:00:00 -0700\n' +
           'Authentication-Results: mx.google.com; spf=fail; dmarc=fail\n' +
           'From: Security Alert <service@paypal-notice.com>\n' +
           'Reply-To: phisher@dark-inbox.ru\n' +
           'Subject: URGENT: Your PayPal account has been restricted\n' +
           'Content-Type: text/plain; charset=utf-8\n\n' +
           'Dear valued customer, unauthorized activity was flagged on your debit card. ' +
           'Please verify immediately at http://bit.ly/paypal-verify-alert to prevent permanent suspension.\n\n' +
           'Thank you,\nAccount Protection Team'
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
  // Settings & Analysis Preference State (Phase 12E: localStorage)
  // --------------------------------------------------------------------------

  function getStoredSettings() {
    try {
      var raw = localStorage.getItem('mailguard_settings');
      if (raw) {
        var parsed = JSON.parse(raw);
        return {
          sensitivity: (parsed.sensitivity === 'low' || parsed.sensitivity === 'high') ? parsed.sensitivity : 'medium',
          scan_urls: parsed.scan_urls !== false,
          analyze_headers: parsed.analyze_headers !== false
        };
      }
    } catch (e) {
      console.warn('Failed to parse mailguard_settings from localStorage', e);
    }
    return {
      sensitivity: 'medium',
      scan_urls: true,
      analyze_headers: true
    };
  }

  function saveStoredSettings(settings) {
    try {
      localStorage.setItem('mailguard_settings', JSON.stringify({
        sensitivity: settings.sensitivity || 'medium',
        scan_urls: settings.scan_urls !== false,
        analyze_headers: settings.analyze_headers !== false
      }));
    } catch (e) {
      console.warn('Failed to save mailguard_settings to localStorage', e);
    }
  }

  function syncSettingsToUi(settings) {
    if (prefSensitivity) prefSensitivity.value = settings.sensitivity;
    if (prefScanUrls) prefScanUrls.checked = settings.scan_urls;
    if (prefAnalyzeHeaders) prefAnalyzeHeaders.checked = settings.analyze_headers;

    if (analyzerSensitivitySelect) analyzerSensitivitySelect.value = settings.sensitivity;
    if (optExtractUrls) optExtractUrls.checked = settings.scan_urls;
    if (optAnalyzeHeaders) optAnalyzeHeaders.checked = settings.analyze_headers;
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
  // API Fetch with Timeout & 1 Automatic Retry (/api/analyze & /api/predict)
  // --------------------------------------------------------------------------

  async function callAnalyzeApi(payload, isRetry) {
    var controller = new AbortController();
    var timeoutId = setTimeout(function () {
      controller.abort();
    }, REQUEST_TIMEOUT_MS);

    try {
      var response = await fetch('/api/analyze', {
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
      var isNetwork = !navigator.onLine || (err.message && err.message.includes('Failed to fetch')) || isTimeout;

      if (!isRetry && isNetwork) {
        return await callAnalyzeApi(payload, true);
      }

      throw err;
    }
  }

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

    if (ext === 'msg') {
      bodyError.textContent = 'Outlook .msg format is not directly supported in the browser. Please save/export as .eml or paste the message text.';
      bodyError.classList.remove('hidden');
      showToast('Outlook .msg unsupported', 'error');
      return;
    }

    if (ext === 'png' || ext === 'jpg' || ext === 'jpeg') {
      var optOcr = document.getElementById('opt-image-ocr');
      if (!optOcr || !optOcr.checked) {
        bodyError.textContent = `Image file selected (.${ext}). Enable the "Image OCR & QR" toggle below or switch to the Image Analysis view.`;
        bodyError.classList.remove('hidden');
        showToast('Enable Image OCR toggle to scan images', 'warn');
        return;
      }
      processImageForAnalyzer(file);
      return;
    }

    if (ext !== 'txt' && ext !== 'eml') {
      bodyError.textContent = `Unsupported file type (.${ext || 'unknown'}). Please choose a .txt or .eml file (or .png/.jpg with OCR toggle).`;
      bodyError.classList.remove('hidden');
      showToast('Unsupported file type', 'error');
      return;
    }

    var reader = new FileReader();
    reader.onload = function (e) {
      var raw = e.target.result || '';
      if (ext === 'eml') {
        currentRawEml = raw;
        currentSourceType = 'eml';
        var parsed = parseEml(raw);
        if (parsed.subject) {
          subjectInput.value = parsed.subject;
        }
        bodyInput.value = parsed.body;

        if (rawHeadersPre) {
          var headerEnd = raw.indexOf('\n\n');
          rawHeadersPre.textContent = headerEnd !== -1 ? raw.substring(0, headerEnd).trim() : raw.substring(0, 500);
        }
        if (headersTelemetryEmpty) headersTelemetryEmpty.classList.add('hidden');
        if (headersTelemetryActive) headersTelemetryActive.classList.remove('hidden');
      } else {
        currentRawEml = null;
        currentSourceType = 'txt';
        bodyInput.value = raw.trim();
        if (headersTelemetryEmpty) headersTelemetryEmpty.classList.remove('hidden');
        if (headersTelemetryActive) headersTelemetryActive.classList.add('hidden');
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
  // --------------------------------------------------------------------------
  // Phase 12C: Render Analysis Report Card (SVG Ring, Indicators, Findings)
  // --------------------------------------------------------------------------

  function renderAnalysisReport(data) {
    currentAnalysisData = data;
    var model = data.model || {};
    var riskScore = typeof data.risk_score === 'number' ? data.risk_score : 50;
    var classification = data.classification || 'Suspicious';
    var conf = typeof model.confidence === 'number' ? model.confidence : 0.50;
    var pSpam = typeof model.probability === 'number' ? model.probability : 0.50;
    var uncertain = Boolean(model.uncertain);

    // Switch card states: hide empty state & skeleton, show active view
    if (reportEmptyState) reportEmptyState.classList.add('hidden');
    if (reportSkeleton) reportSkeleton.classList.add('hidden');
    if (reportActiveView) reportActiveView.classList.remove('hidden');
    if (newScanBtn) newScanBtn.classList.remove('hidden');

    // 1. Risk Ring gauge (circle r=54, circumference = 339.292)
    var CIRCUMFERENCE = 339.292;
    var clampedScore = Math.max(0, Math.min(100, riskScore));
    var dashoffset = CIRCUMFERENCE * (1 - clampedScore / 100);

    if (riskRingFill) {
      riskRingFill.style.strokeDasharray = String(CIRCUMFERENCE);
      riskRingFill.style.strokeDashoffset = dashoffset.toFixed(2);
      riskRingFill.classList.remove('stroke-safe', 'stroke-suspicious', 'stroke-spam');

      var strokeClass = 'stroke-safe';
      if (classification === 'Spam' || clampedScore >= 70) {
        strokeClass = 'stroke-spam';
      } else if (classification === 'Suspicious' || clampedScore >= 40) {
        strokeClass = 'stroke-suspicious';
      }
      riskRingFill.classList.add(strokeClass);
    }

    if (riskRingNum) {
      riskRingNum.textContent = String(clampedScore);
    }

    if (riskRingBadge) {
      riskRingBadge.textContent = classification;
      riskRingBadge.className = 'risk-ring-badge';
      if (classification === 'Spam') {
        riskRingBadge.classList.add('badge-spam');
      } else if (classification === 'Suspicious') {
        riskRingBadge.classList.add('badge-suspicious');
      } else {
        riskRingBadge.classList.add('badge-safe');
      }
    }

    // 2. Metadata Grid
    if (reportClassificationVal) {
      reportClassificationVal.textContent = classification;
      reportClassificationVal.className = 'meta-value-verdict verdict-' + classification.toLowerCase();
    }

    if (reportConfidenceVal) {
      reportConfidenceVal.textContent = (conf * 100).toFixed(1) + '%';
    }

    if (reportTimestampVal) {
      var now = new Date();
      reportTimestampVal.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    }

    // 3. Uncertain Callout Banner
    if (reportUncertainBanner) {
      if (uncertain) {
        reportUncertainBanner.classList.remove('hidden');
        if (reportUncertainText) {
          reportUncertainText.textContent = `Calibrated spam probability (${pSpam.toFixed(4)}) falls within the [0.40, 0.60] borderline zone. Empirical cross-validation on 24,369 emails shows near 50/50 balance in this band. Automated decision withheld; human review recommended.`;
        }
      } else {
        reportUncertainBanner.classList.add('hidden');
      }
    }

    // 4. Detected Indicators Chips
    var indicators = data.indicators || [];
    if (indicatorCountBadge) {
      indicatorCountBadge.textContent = String(indicators.length);
    }

    if (indicatorsChipsContainer) {
      while (indicatorsChipsContainer.firstChild) {
        indicatorsChipsContainer.removeChild(indicatorsChipsContainer.firstChild);
      }

      if (indicators.length === 0) {
        var cleanChip = document.createElement('div');
        cleanChip.className = 'indicator-chip chip-clean';
        var cleanIcon = document.createElement('span');
        cleanIcon.setAttribute('aria-hidden', 'true');
        cleanIcon.textContent = '✓';
        var cleanText = document.createElement('span');
        cleanText.textContent = 'No Threat Indicators Detected (Clean)';
        cleanChip.appendChild(cleanIcon);
        cleanChip.appendChild(cleanText);
        indicatorsChipsContainer.appendChild(cleanChip);
      } else {
        indicators.forEach(function (ind) {
          var chip = document.createElement('div');
          var sev = (ind.severity || 'medium').toLowerCase();
          chip.className = 'indicator-chip chip-' + sev;

          var iconSpan = document.createElement('span');
          iconSpan.setAttribute('aria-hidden', 'true');
          iconSpan.textContent = sev === 'critical' ? '🚨' : sev === 'high' ? '⚠️' : sev === 'medium' ? '🔍' : 'ℹ️';

          var textSpan = document.createElement('span');
          var typeLabel = (ind.type || 'Indicator').replace(/_/g, ' ');
          textSpan.textContent = `${typeLabel}: ${ind.detail || ''}`;

          chip.appendChild(iconSpan);
          chip.appendChild(textSpan);
          indicatorsChipsContainer.appendChild(chip);
        });
      }
    }

    // 5. Key Findings Bullet List
    if (findingsList) {
      while (findingsList.firstChild) {
        findingsList.removeChild(findingsList.firstChild);
      }

      var findings = data.key_findings || [];
      if (findings.length === 0) {
        var defaultLi = document.createElement('li');
        defaultLi.className = 'finding-item';
        var defBullet = document.createElement('span');
        defBullet.className = 'finding-bullet';
        defBullet.textContent = '•';
        var defText = document.createElement('span');
        defText.textContent = 'Standard email syntax and content patterns; no specific anomalies identified.';
        defaultLi.appendChild(defBullet);
        defaultLi.appendChild(defText);
        findingsList.appendChild(defaultLi);
      } else {
        findings.forEach(function (f) {
          var li = document.createElement('li');
          li.className = 'finding-item';
          var bullet = document.createElement('span');
          bullet.className = 'finding-bullet';
          bullet.textContent = '•';
          var textNode = document.createElement('span');
          textNode.textContent = f;
          li.appendChild(bullet);
          li.appendChild(textNode);
          findingsList.appendChild(li);
        });
      }
    }

    // 6. Email Preview Header & Highlighter
    if (previewFromVal) {
      previewFromVal.textContent = (data.headers && data.headers.from) ? data.headers.from : (data.headers && data.headers['From']) || 'user@example.com';
    }
    if (previewSubjectVal) {
      previewSubjectVal.textContent = (data.headers && data.headers.subject) || currentInputText.subject || '(No Subject)';
    }

    var tokens = data.top_tokens || [];
    renderInTextHighlights(currentInputText.subject, currentInputText.body, tokens, filterStopwords);

    // 7. Header Telemetry Panel (if headers present in API response)
    if (data.headers) {
      if (headersTelemetryEmpty) headersTelemetryEmpty.classList.add('hidden');
      if (headersTelemetryActive) headersTelemetryActive.classList.remove('hidden');

      if (hSpfVal) {
        var spf = (data.headers.spf || 'none').toLowerCase();
        hSpfVal.textContent = spf.toUpperCase();
        hSpfVal.className = 'h-val ' + (spf === 'pass' ? 'badge-safe' : (spf === 'fail' ? 'badge-spam' : 'badge-neutral'));
      }
      if (hDkimVal) {
        var dkim = (data.headers.dkim || 'none').toLowerCase();
        hDkimVal.textContent = dkim.toUpperCase();
        hDkimVal.className = 'h-val ' + (dkim === 'pass' ? 'badge-safe' : (dkim === 'fail' ? 'badge-spam' : 'badge-neutral'));
      }
      if (hDmarcVal) {
        var dmarc = (data.headers.dmarc || 'none').toLowerCase();
        hDmarcVal.textContent = dmarc.toUpperCase();
        hDmarcVal.className = 'h-val ' + (dmarc === 'pass' ? 'badge-safe' : (dmarc === 'fail' ? 'badge-spam' : 'badge-neutral'));
      }
      if (hSenderMatchVal) {
        var match = data.headers.sender_match;
        hSenderMatchVal.textContent = match === true ? 'Match' : (match === false ? 'Mismatch' : 'N/A');
        hSenderMatchVal.className = 'h-val ' + (match === false ? 'badge-spam' : 'badge-safe');
      }
      if (hHopsVal) {
        hHopsVal.textContent = `${data.headers.hop_count || 0} hops`;
      }
      if (rawHeadersPre && data.headers.raw_headers) {
        rawHeadersPre.textContent = data.headers.raw_headers;
      }
    }

    // 8. Update Session Stats
    updateSessionStats(classification.toLowerCase());

    // 9. Focus management without harsh scroll
    if (reportActiveView) {
      reportActiveView.focus({ preventScroll: true });
    }
  }

  // Legacy result card renderer guarded against null
  function renderPredictionResult(data) {
    if (!resultCard) return;
    var prediction = data.prediction || 'uncertain';
    var labelDisplay = data.label_display || 'Needs review';
    var riskLevel = (data.risk_level || 'medium').toLowerCase();
    var conf = typeof data.confidence === 'number' ? data.confidence : 0.5;
    var spamProb = typeof data.spam_probability === 'number' ? data.spam_probability : 0.5;

    resultCard.classList.remove('hidden', 'verdict-spam-border', 'verdict-ham-border', 'verdict-uncertain-border', 'verdict-fade-in');
    if (verdictIcon) verdictIcon.className = 'verdict-icon';
    if (riskBadge) riskBadge.className = 'risk-badge';

    if (prediction === 'spam') {
      resultCard.classList.add('verdict-spam-border');
      if (verdictIcon) { verdictIcon.classList.add('verdict-icon-spam'); verdictIcon.textContent = '🚨'; }
      if (verdictTitle) verdictTitle.textContent = labelDisplay;
      if (uncertainBanner) uncertainBanner.classList.add('hidden');
    } else if (prediction === 'ham') {
      resultCard.classList.add('verdict-ham-border');
      if (verdictIcon) { verdictIcon.classList.add('verdict-icon-ham'); verdictIcon.textContent = '✓'; }
      if (verdictTitle) verdictTitle.textContent = labelDisplay;
      if (uncertainBanner) uncertainBanner.classList.add('hidden');
    } else {
      resultCard.classList.add('verdict-uncertain-border');
      if (verdictIcon) { verdictIcon.classList.add('verdict-icon-unc'); verdictIcon.textContent = '⚖'; }
      if (verdictTitle) verdictTitle.textContent = labelDisplay;
      if (uncertainBanner) {
        uncertainBanner.classList.remove('hidden');
        if (uncertainBannerText) {
          uncertainBannerText.textContent = `Calibrated spam probability (${spamProb.toFixed(4)}) falls within the [0.40, 0.60] borderline zone. Empirical 5-fold cross-validation on 24,369 training emails showed that 0.46% of messages fall into this band (nearly 50/50 ham vs spam). Automated classification is withheld; human review is recommended.`;
        }
      }
    }

    if (riskBadge) {
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
    }

    if (confidenceValue && confidenceBar) {
      var confPct = Math.min(100, Math.max(0, conf * 100)).toFixed(1);
      confidenceValue.textContent = `${confPct}%`;
      confidenceBar.style.width = `${confPct}%`;
    }
    if (probabilitySubtext) {
      probabilitySubtext.textContent = `Calibrated spam probability: ${spamProb.toFixed(4)}`;
    }

    var tokensForHighlight = data.top_tokens || data.signals || [];
    renderInTextHighlights(currentInputText.subject, currentInputText.body, tokensForHighlight, filterStopwords);
    renderSignalsList(data.signals || [], filterStopwords);
    resultCard.classList.add('verdict-fade-in');
    updateSessionStats(prediction);
  }

  // --------------------------------------------------------------------------
  // Preview Mode Switch: Original vs Extracted
  // --------------------------------------------------------------------------

  function updatePreviewMode(original) {
    isPreviewOriginal = original;
    if (btnPreviewOriginal) btnPreviewOriginal.classList.toggle('active', original);
    if (btnPreviewExtracted) btnPreviewExtracted.classList.toggle('active', !original);

    if (!currentAnalysisData) return;

    if (original) {
      renderInTextHighlights(currentInputText.subject, currentInputText.body, currentAnalysisData.top_tokens || [], filterStopwords);
    } else {
      renderInTextHighlights(currentInputText.subject, currentInputText.body, currentAnalysisData.top_tokens || [], false);
    }
  }

  if (btnPreviewOriginal) {
    btnPreviewOriginal.addEventListener('click', function () {
      updatePreviewMode(true);
    });
  }

  if (btnPreviewExtracted) {
    btnPreviewExtracted.addEventListener('click', function () {
      updatePreviewMode(false);
    });
  }

  // --------------------------------------------------------------------------
  // Copy Report & Export JSON
  // --------------------------------------------------------------------------

  function copyAnalysisReport() {
    if (!currentAnalysisData) {
      showToast('No analysis report to copy', 'warn');
      return;
    }

    var data = currentAnalysisData;
    var model = data.model || {};
    var lines = [
      'MailGuard AI - Email Security Analysis Report',
      '==============================================',
      `Classification:    ${data.classification}`,
      `Risk Score:        ${data.risk_score} / 100`,
      `Model Confidence:  ${(model.confidence * 100).toFixed(1)}%`,
      `Calibrated Spam P: ${(model.probability).toFixed(4)}`,
      `Uncertain State:   ${model.uncertain ? 'YES (Human Review Recommended)' : 'NO'}`,
      `Vocab Coverage:    ${data.vocab_coverage}%`,
      '',
      'Key Findings:'
    ];

    (data.key_findings || []).forEach(function (f) {
      lines.push(`  • ${f}`);
    });

    lines.push('');
    lines.push(`Detected Indicators (${(data.indicators || []).length}):`);
    if ((data.indicators || []).length === 0) {
      lines.push('  • (No threat indicators detected)');
    } else {
      data.indicators.forEach(function (ind) {
        lines.push(`  • [${(ind.severity || 'MEDIUM').toUpperCase()}] ${ind.type}: ${ind.detail}`);
      });
    }

    if (data.headers) {
      lines.push('');
      lines.push('Header Authentication:');
      lines.push(`  • SPF:    ${(data.headers.spf || 'none').toUpperCase()}`);
      lines.push(`  • DKIM:   ${(data.headers.dkim || 'none').toUpperCase()}`);
      lines.push(`  • DMARC:  ${(data.headers.dmarc || 'none').toUpperCase()}`);
      lines.push(`  • Relay:  ${data.headers.hop_count || 0} hops`);
    }

    lines.push('');
    lines.push('Note: MailGuard AI provides statistical probability estimates, not absolute guarantees.');

    var reportText = lines.join('\n');

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(reportText).then(function () {
        if (copyReportText) copyReportText.textContent = 'Copied!';
        if (copyReportIcon) copyReportIcon.textContent = '✓';
        showToast('Analysis report copied to clipboard', 'success');
        setTimeout(function () {
          if (copyReportText) copyReportText.textContent = 'Copy Report';
          if (copyReportIcon) copyReportIcon.textContent = '📋';
        }, 2000);
      }).catch(function () {
        fallbackCopyText(reportText);
      });
    } else {
      fallbackCopyText(reportText);
    }
  }

  function exportAnalysisJson() {
    if (!currentAnalysisData) {
      showToast('No analysis report to export', 'warn');
      return;
    }

    try {
      var exportPayload = {
        meta: {
          app: 'MailGuard AI',
          version: '2.0.0',
          exported_at: new Date().toISOString()
        },
        analysis: currentAnalysisData,
        input_meta: {
          subject_length: (currentInputText.subject || '').length,
          body_length: (currentInputText.body || '').length,
          has_raw_eml: Boolean(currentRawEml)
        }
      };

      var jsonStr = JSON.stringify(exportPayload, null, 2);
      var blob = new Blob([jsonStr], { type: 'application/json' });
      var url = URL.createObjectURL(blob);
      var a = document.createElement('a');
      a.href = url;
      a.download = `mailguard-analysis-${Date.now()}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      showToast('Analysis report exported as JSON', 'success');
    } catch (e) {
      showToast('Failed to export JSON report', 'error');
    }
  }

  function handleNewScan() {
    if (reportActiveView) reportActiveView.classList.add('hidden');
    if (reportSkeleton) reportSkeleton.classList.add('hidden');
    if (reportEmptyState) reportEmptyState.classList.remove('hidden');
    if (newScanBtn) newScanBtn.classList.add('hidden');
    if (subjectInput) subjectInput.value = '';
    if (bodyInput) bodyInput.value = '';
    currentRawEml = null;
    currentAnalysisData = null;
    updateCharCount();
    if (bodyInput) bodyInput.focus();
  }

  if (copyReportBtn) copyReportBtn.addEventListener('click', copyAnalysisReport);
  if (exportJsonBtn) exportJsonBtn.addEventListener('click', exportAnalysisJson);
  if (newScanBtn) newScanBtn.addEventListener('click', handleNewScan);

  if (copyRawHeadersBtn) {
    copyRawHeadersBtn.addEventListener('click', function () {
      if (rawHeadersPre && rawHeadersPre.textContent) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(rawHeadersPre.textContent).then(function () {
            showToast('Headers copied to clipboard', 'success');
          });
        } else {
          fallbackCopyText(rawHeadersPre.textContent);
        }
      } else {
        showToast('No raw headers to copy', 'warn');
      }
    });
  }

  // --------------------------------------------------------------------------
  // Tab Switching (Email Content vs Header Analysis)
  // --------------------------------------------------------------------------

  function switchTab(tabName) {
    if (tabName === 'content') {
      if (tabBtnContent) {
        tabBtnContent.classList.add('active');
        tabBtnContent.setAttribute('aria-selected', 'true');
      }
      if (tabBtnHeaders) {
        tabBtnHeaders.classList.remove('active');
        tabBtnHeaders.setAttribute('aria-selected', 'false');
      }
      if (tabPanelContent) tabPanelContent.classList.remove('hidden');
      if (tabPanelHeaders) tabPanelHeaders.classList.add('hidden');
    } else if (tabName === 'headers') {
      if (tabBtnHeaders) {
        tabBtnHeaders.classList.add('active');
        tabBtnHeaders.setAttribute('aria-selected', 'true');
      }
      if (tabBtnContent) {
        tabBtnContent.classList.remove('active');
        tabBtnContent.setAttribute('aria-selected', 'false');
      }
      if (tabPanelHeaders) tabPanelHeaders.classList.remove('hidden');
      if (tabPanelContent) tabPanelContent.classList.add('hidden');
    }
  }

  if (tabBtnContent) {
    tabBtnContent.addEventListener('click', function () {
      switchTab('content');
    });
  }

  if (tabBtnHeaders) {
    tabBtnHeaders.addEventListener('click', function () {
      switchTab('headers');
    });
  }

  if (loadEmlSampleBtn) {
    loadEmlSampleBtn.addEventListener('click', function () {
      currentRawEml = SAMPLES.emlSample.raw;
      currentSourceType = 'eml';
      var parsed = parseEml(currentRawEml);
      if (subjectInput) subjectInput.value = parsed.subject;
      if (bodyInput) bodyInput.value = parsed.body;
      if (rawHeadersPre) {
        var headerEnd = currentRawEml.indexOf('\n\n');
        rawHeadersPre.textContent = headerEnd !== -1 ? currentRawEml.substring(0, headerEnd).trim() : currentRawEml;
      }
      if (headersTelemetryEmpty) headersTelemetryEmpty.classList.add('hidden');
      if (headersTelemetryActive) headersTelemetryActive.classList.remove('hidden');
      updateCharCount();
      showToast('Loaded sample .eml headers & content', 'success');
      switchTab('content');
    });
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

    var currentSettings = getStoredSettings();
    var effSensitivity = analyzerSensitivitySelect ? analyzerSensitivitySelect.value : (currentSettings.sensitivity || 'medium');
    var effScanUrls = optExtractUrls ? optExtractUrls.checked : (currentSettings.scan_urls !== false);
    var effAnalyzeHeaders = optAnalyzeHeaders ? optAnalyzeHeaders.checked : (currentSettings.analyze_headers !== false);
    var effDetectSuspicious = optSuspiciousLinks ? optSuspiciousLinks.checked : true;

    var analyzePayload = {
      subject: subVal,
      text: subVal ? (`Subject: ${subVal}\n\n${bodyVal}`) : bodyVal,
      eml: currentRawEml || null,
      options: {
        scan_urls: effScanUrls,
        analyze_headers: effAnalyzeHeaders,
        detect_suspicious_links: effDetectSuspicious,
        sensitivity: effSensitivity
      }
    };

    // UI Loading state
    analyzeBtn.disabled = true;
    analyzeBtnText.textContent = 'Analyzing...';
    analyzeBtnSpinner.classList.remove('hidden');
    clearBtn.disabled = true;
    sampleSpamBtn.disabled = true;
    sampleHamBtn.disabled = true;
    sampleBorderlineBtn.disabled = true;

    // Show skeletons, hide existing views to eliminate layout jump
    if (reportSkeleton) reportSkeleton.classList.remove('hidden');
    if (reportEmptyState) reportEmptyState.classList.add('hidden');
    if (reportActiveView) reportActiveView.classList.add('hidden');
    if (resultSkeleton) resultSkeleton.classList.remove('hidden');
    if (resultCard) resultCard.classList.add('hidden');

    var wakingBannerTimer = setTimeout(function () {
      wakingBanner.classList.remove('hidden');
    }, WAKING_BANNER_DELAY_MS);

    try {
      var resultData = await callAnalyzeApi(analyzePayload, false);
      clearTimeout(wakingBannerTimer);
      wakingBanner.classList.add('hidden');
      if (reportSkeleton) reportSkeleton.classList.add('hidden');
      if (resultSkeleton) resultSkeleton.classList.add('hidden');

      currentAnalysisData = resultData;
      currentPredictionData = {
        prediction: resultData.model ? resultData.model.label : 'ham',
        label_display: resultData.classification,
        risk_level: resultData.classification === 'Spam' ? 'high' : (resultData.classification === 'Suspicious' ? 'medium' : 'low'),
        confidence: resultData.model ? resultData.model.confidence : 0.5,
        spam_probability: resultData.model ? resultData.model.probability : 0.5,
        top_tokens: resultData.top_tokens || [],
        signals: resultData.top_tokens || []
      };

      renderAnalysisReport(resultData);

      // Phase 12D: Persist scan record to local IndexedDB (zero server storage)
      var scanRecord = {
        timestamp: new Date().toISOString(),
        created_at: Date.now(),
        subject: subVal || (bodyVal.length > 60 ? bodyVal.substring(0, 60) + '...' : bodyVal) || 'Untitled Email',
        label: resultData.classification || 'Safe',
        risk_score: typeof resultData.risk_score === 'number' ? resultData.risk_score : (resultData.classification === 'Spam' ? 85 : (resultData.classification === 'Suspicious' ? 50 : 15)),
        source_type: currentSourceType || 'paste',
        confidence: resultData.model ? resultData.model.confidence : 0.5,
        indicator_count: (resultData.indicators || []).length
      };

      await saveScanRecord(scanRecord);
      await updateDashboardUI();
    } catch (err) {
      clearTimeout(wakingBannerTimer);
      wakingBanner.classList.add('hidden');
      if (reportSkeleton) reportSkeleton.classList.add('hidden');
      if (resultSkeleton) resultSkeleton.classList.add('hidden');
      if (reportEmptyState) reportEmptyState.classList.remove('hidden');

      generalErrorMessage.textContent = err.message || 'An unexpected error occurred while communicating with the server.';
      generalError.classList.remove('hidden');
      retryBtn.classList.remove('hidden');
    } finally {
      analyzeBtn.disabled = false;
      analyzeBtnText.textContent = 'Analyze Email →';
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
    currentRawEml = null;
    currentAnalysisData = null;
    currentPredictionData = null;
    updateCharCount();
    bodyError.classList.add('hidden');
    bodyError.textContent = '';
    generalError.classList.add('hidden');
    generalErrorMessage.textContent = '';
    wakingBanner.classList.add('hidden');
    if (reportSkeleton) reportSkeleton.classList.add('hidden');
    if (reportActiveView) reportActiveView.classList.add('hidden');
    if (reportEmptyState) reportEmptyState.classList.remove('hidden');
    if (newScanBtn) newScanBtn.classList.add('hidden');
    if (headersTelemetryEmpty) headersTelemetryEmpty.classList.remove('hidden');
    if (headersTelemetryActive) headersTelemetryActive.classList.add('hidden');
    if (rawHeadersPre) rawHeadersPre.textContent = '';
    subjectInput.focus();
  });

  retryBtn.addEventListener('click', function () {
    handleFormSubmit();
  });

  // Sample Loaders
  sampleSpamBtn.addEventListener('click', function () {
    currentRawEml = null;
    currentSourceType = 'paste';
    subjectInput.value = SAMPLES.spam.subject;
    bodyInput.value = SAMPLES.spam.body;
    updateCharCount();
    bodyError.classList.add('hidden');
    generalError.classList.add('hidden');
    if (headersTelemetryEmpty) headersTelemetryEmpty.classList.remove('hidden');
    if (headersTelemetryActive) headersTelemetryActive.classList.add('hidden');
    if (rawHeadersPre) rawHeadersPre.textContent = '';
    bodyInput.focus();
  });

  sampleHamBtn.addEventListener('click', function () {
    currentRawEml = null;
    currentSourceType = 'paste';
    subjectInput.value = SAMPLES.ham.subject;
    bodyInput.value = SAMPLES.ham.body;
    updateCharCount();
    bodyError.classList.add('hidden');
    generalError.classList.add('hidden');
    if (headersTelemetryEmpty) headersTelemetryEmpty.classList.remove('hidden');
    if (headersTelemetryActive) headersTelemetryActive.classList.add('hidden');
    if (rawHeadersPre) rawHeadersPre.textContent = '';
    bodyInput.focus();
  });

  sampleBorderlineBtn.addEventListener('click', function () {
    currentRawEml = null;
    currentSourceType = 'paste';
    subjectInput.value = SAMPLES.borderline.subject;
    bodyInput.value = SAMPLES.borderline.body;
    updateCharCount();
    bodyError.classList.add('hidden');
    generalError.classList.add('hidden');
    if (headersTelemetryEmpty) headersTelemetryEmpty.classList.remove('hidden');
    if (headersTelemetryActive) headersTelemetryActive.classList.add('hidden');
    if (rawHeadersPre) rawHeadersPre.textContent = '';
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
      if (currentAnalysisData) {
        renderInTextHighlights(
          currentInputText.subject,
          currentInputText.body,
          currentAnalysisData.top_tokens || [],
          filterStopwords
        );
      } else if (currentPredictionData) {
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
  // Phase 12D: Client-Side IndexedDB Storage & Local Analytics
  // --------------------------------------------------------------------------

  var DB_NAME = 'MailGuardDB';
  var DB_VERSION = 1;
  var DB_STORE = 'scans';

  var isStorageFallback = false;
  var memoryScanStore = [];
  var dbInstance = null;
  var dbInitPromise = null;

  function initDatabase() {
    if (dbInitPromise) return dbInitPromise;
    dbInitPromise = new Promise(function (resolve) {
      if (!window.indexedDB) {
        console.warn('IndexedDB not supported in this browser. Falling back to in-memory store.');
        isStorageFallback = true;
        if (storageFallbackBanner) storageFallbackBanner.classList.remove('hidden');
        resolve(null);
        return;
      }

      try {
        var req = window.indexedDB.open(DB_NAME, DB_VERSION);
        req.onupgradeneeded = function (e) {
          var db = e.target.result;
          if (!db.objectStoreNames.contains(DB_STORE)) {
            var store = db.createObjectStore(DB_STORE, { keyPath: 'id', autoIncrement: true });
            store.createIndex('created_at', 'created_at', { unique: false });
            store.createIndex('label', 'label', { unique: false });
            store.createIndex('risk_score', 'risk_score', { unique: false });
            store.createIndex('source_type', 'source_type', { unique: false });
          }
        };

        req.onsuccess = function (e) {
          dbInstance = e.target.result;
          resolve(dbInstance);
        };

        req.onerror = function (e) {
          console.warn('IndexedDB access error (e.g. private mode):', e.target.error);
          isStorageFallback = true;
          if (storageFallbackBanner) storageFallbackBanner.classList.remove('hidden');
          resolve(null);
        };
      } catch (err) {
        console.warn('IndexedDB initialization failed:', err);
        isStorageFallback = true;
        if (storageFallbackBanner) storageFallbackBanner.classList.remove('hidden');
        resolve(null);
      }
    });

    return dbInitPromise;
  }

  function saveScanRecord(record) {
    return new Promise(function (resolve) {
      record.created_at = record.created_at || Date.now();
      record.timestamp = record.timestamp || new Date(record.created_at).toISOString();

      if (isStorageFallback || !dbInstance) {
        record.id = Date.now() + Math.floor(Math.random() * 1000);
        memoryScanStore.unshift(record);
        resolve(record);
        return;
      }

      try {
        var tx = dbInstance.transaction([DB_STORE], 'readwrite');
        var store = tx.objectStore(DB_STORE);
        var req = store.add(record);
        req.onsuccess = function (e) {
          record.id = e.target.result;
          resolve(record);
        };
        req.onerror = function () {
          record.id = Date.now();
          memoryScanStore.unshift(record);
          resolve(record);
        };
      } catch (err) {
        record.id = Date.now();
        memoryScanStore.unshift(record);
        resolve(record);
      }
    });
  }

  function getAllScanRecords() {
    return new Promise(function (resolve) {
      if (isStorageFallback || !dbInstance) {
        var memList = memoryScanStore.slice();
        memList.sort(function (a, b) {
          return (b.created_at || 0) - (a.created_at || 0);
        });
        resolve(memList);
        return;
      }

      try {
        var tx = dbInstance.transaction([DB_STORE], 'readonly');
        var store = tx.objectStore(DB_STORE);
        var req = store.getAll();
        req.onsuccess = function (e) {
          var records = e.target.result || [];
          records.sort(function (a, b) {
            return (b.created_at || 0) - (a.created_at || 0);
          });
          resolve(records);
        };
        req.onerror = function () {
          resolve(memoryScanStore.slice());
        };
      } catch (err) {
        resolve(memoryScanStore.slice());
      }
    });
  }

  function deleteScanRecord(id) {
    return new Promise(function (resolve) {
      if (isStorageFallback || !dbInstance) {
        memoryScanStore = memoryScanStore.filter(function (r) {
          return r.id !== id;
        });
        resolve(true);
        return;
      }

      try {
        var tx = dbInstance.transaction([DB_STORE], 'readwrite');
        var store = tx.objectStore(DB_STORE);
        var req = store.delete(id);
        req.onsuccess = function () {
          resolve(true);
        };
        req.onerror = function () {
          resolve(false);
        };
      } catch (err) {
        resolve(false);
      }
    });
  }

  function clearAllScanRecords() {
    return new Promise(function (resolve) {
      memoryScanStore = [];
      if (isStorageFallback || !dbInstance) {
        resolve(true);
        return;
      }

      try {
        var tx = dbInstance.transaction([DB_STORE], 'readwrite');
        var store = tx.objectStore(DB_STORE);
        var req = store.clear();
        req.onsuccess = function () {
          resolve(true);
        };
        req.onerror = function () {
          resolve(false);
        };
      } catch (err) {
        resolve(false);
      }
    });
  }

  function formatDateTime(ts) {
    if (!ts) return '--';
    var d = new Date(ts);
    if (isNaN(d.getTime())) return String(ts);
    var pad = function (n) { return n < 10 ? '0' + n : String(n); };
    var year = d.getFullYear();
    var month = pad(d.getMonth() + 1);
    var day = pad(d.getDate());
    var hours = pad(d.getHours());
    var mins = pad(d.getMinutes());
    return `${year}-${month}-${day} ${hours}:${mins}`;
  }

  function csvEscape(val) {
    if (val === null || val === undefined) return '""';
    var str = String(val);
    if (str.includes(',') || str.includes('"') || str.includes('\n') || str.includes('\r')) {
      return '"' + str.replace(/"/g, '""') + '"';
    }
    return '"' + str + '"';
  }

  // Legacy compatibility stub
  function updateSessionStats() {
    updateDashboardUI();
  }

  // --------------------------------------------------------------------------
  // Dashboard UI Updater (Threat Distribution Donut, Telemetry, Recent Scans)
  // --------------------------------------------------------------------------

  async function updateDashboardUI() {
    var records = await getAllScanRecords();
    var total = records.length;
    var spamCount = 0;
    var uncCount = 0;
    var safeCount = 0;

    var now = Date.now();
    var oneWeekMs = 7 * 24 * 60 * 60 * 1000;
    var curWeekScans = 0;
    var priorWeekScans = 0;

    records.forEach(function (r) {
      if (r.label === 'Spam') spamCount++;
      else if (r.label === 'Suspicious') uncCount++;
      else safeCount++;

      var t = r.created_at || now;
      if (t >= now - oneWeekMs) {
        curWeekScans++;
      } else if (t >= now - (2 * oneWeekMs)) {
        priorWeekScans++;
      }
    });

    // Stat Cards
    if (dashStatTotal) dashStatTotal.textContent = String(total);
    if (dashStatSpam) dashStatSpam.textContent = String(spamCount);
    if (dashStatUncertain) dashStatUncertain.textContent = String(uncCount);
    if (dashStatSafe) dashStatSafe.textContent = String(safeCount);

    if (dashStatTotalSub) {
      if (priorWeekScans > 0) {
        var diff = curWeekScans - priorWeekScans;
        var pct = Math.round((diff / priorWeekScans) * 100);
        var sign = diff >= 0 ? '+' : '';
        dashStatTotalSub.textContent = `${sign}${pct}% vs last week`;
      } else {
        dashStatTotalSub.textContent = '-- vs last week';
      }
    }

    if (dashStatSpamSub) {
      dashStatSpamSub.textContent = total > 0 ? `${Math.round((spamCount / total) * 100)}% of total scans` : '0% of total scans';
    }
    if (dashStatUncertainSub) {
      dashStatUncertainSub.textContent = total > 0 ? `${Math.round((uncCount / total) * 100)}% of total scans` : '0% of total scans';
    }
    if (dashStatSafeSub) {
      dashStatSafeSub.textContent = total > 0 ? `${Math.round((safeCount / total) * 100)}% of total scans` : '0% of total scans';
    }

    // Donut Chart Calculations (Circumference = 2 * PI * 48 = 301.59)
    var C = 301.59289;
    if (donutNum) donutNum.textContent = String(total);

    if (donutLegendSpam) {
      var pctS = total > 0 ? Math.round((spamCount / total) * 100) : 0;
      donutLegendSpam.textContent = `${spamCount} (${pctS}%)`;
    }
    if (donutLegendUnc) {
      var pctU = total > 0 ? Math.round((uncCount / total) * 100) : 0;
      donutLegendUnc.textContent = `${uncCount} (${pctU}%)`;
    }
    if (donutLegendHam) {
      var pctH = total > 0 ? Math.round((safeCount / total) * 100) : 0;
      donutLegendHam.textContent = `${safeCount} (${pctH}%)`;
    }

    if (donutSegSpam && donutSegUnc && donutSegHam) {
      if (total === 0) {
        donutSegSpam.style.strokeDasharray = '0 302';
        donutSegSpam.style.strokeDashoffset = '0';
        donutSegSpam.setAttribute('stroke-dasharray', '0 302');
        donutSegSpam.setAttribute('stroke-dashoffset', '0');

        donutSegUnc.style.strokeDasharray = '0 302';
        donutSegUnc.style.strokeDashoffset = '0';
        donutSegUnc.setAttribute('stroke-dasharray', '0 302');
        donutSegUnc.setAttribute('stroke-dashoffset', '0');

        donutSegHam.style.strokeDasharray = '0 302';
        donutSegHam.style.strokeDashoffset = '0';
        donutSegHam.setAttribute('stroke-dasharray', '0 302');
        donutSegHam.setAttribute('stroke-dashoffset', '0');
      } else {
        var dashS = (spamCount / total) * C;
        var dashU = (uncCount / total) * C;
        var dashH = (safeCount / total) * C;

        donutSegSpam.style.strokeDasharray = `${dashS.toFixed(2)} ${(C - dashS).toFixed(2)}`;
        donutSegSpam.style.strokeDashoffset = '0';
        donutSegSpam.setAttribute('stroke-dasharray', `${dashS.toFixed(2)} ${(C - dashS).toFixed(2)}`);
        donutSegSpam.setAttribute('stroke-dashoffset', '0');

        donutSegUnc.style.strokeDasharray = `${dashU.toFixed(2)} ${(C - dashU).toFixed(2)}`;
        donutSegUnc.style.strokeDashoffset = `${(-dashS).toFixed(2)}`;
        donutSegUnc.setAttribute('stroke-dasharray', `${dashU.toFixed(2)} ${(C - dashU).toFixed(2)}`);
        donutSegUnc.setAttribute('stroke-dashoffset', `${(-dashS).toFixed(2)}`);

        donutSegHam.style.strokeDasharray = `${dashH.toFixed(2)} ${(C - dashH).toFixed(2)}`;
        donutSegHam.style.strokeDashoffset = `${(-(dashS + dashU)).toFixed(2)}`;
        donutSegHam.setAttribute('stroke-dasharray', `${dashH.toFixed(2)} ${(C - dashH).toFixed(2)}`);
        donutSegHam.setAttribute('stroke-dashoffset', `${(-(dashS + dashU)).toFixed(2)}`);
      }
    }

    // Recent Scans Table on Dashboard
    if (dashRecentEmpty && dashRecentActive && dashRecentTbody) {
      if (total === 0) {
        dashRecentEmpty.classList.remove('hidden');
        dashRecentActive.classList.add('hidden');
        while (dashRecentTbody.firstChild) {
          dashRecentTbody.removeChild(dashRecentTbody.firstChild);
        }
      } else {
        dashRecentEmpty.classList.add('hidden');
        dashRecentActive.classList.remove('hidden');
        while (dashRecentTbody.firstChild) {
          dashRecentTbody.removeChild(dashRecentTbody.firstChild);
        }

        var recentList = records.slice(0, 5);
        recentList.forEach(function (scan) {
          var tr = document.createElement('tr');

          var tdDate = document.createElement('td');
          tdDate.textContent = formatDateTime(scan.created_at || scan.timestamp);
          tr.appendChild(tdDate);

          var tdSub = document.createElement('td');
          var strongSub = document.createElement('strong');
          var subTitle = scan.subject || 'Untitled Email';
          if (subTitle.length > 40) subTitle = subTitle.substring(0, 40) + '...';
          strongSub.textContent = subTitle;
          tdSub.appendChild(strongSub);
          tr.appendChild(tdSub);

          var tdSource = document.createElement('td');
          var badgeSource = document.createElement('span');
          badgeSource.className = 'badge-source';
          badgeSource.textContent = scan.source_type || 'paste';
          tdSource.appendChild(badgeSource);
          tr.appendChild(tdSource);

          var tdRisk = document.createElement('td');
          var badgeRisk = document.createElement('span');
          var riskVal = typeof scan.risk_score === 'number' ? scan.risk_score : 0;
          badgeRisk.className = 'badge ' + (riskVal >= 70 ? 'badge-danger' : (riskVal >= 35 ? 'badge-warning' : 'badge-success'));
          badgeRisk.textContent = `${riskVal}/100`;
          tdRisk.appendChild(badgeRisk);
          tr.appendChild(tdRisk);

          var tdVerdict = document.createElement('td');
          var badgeVerdict = document.createElement('span');
          badgeVerdict.className = 'risk-badge ' + (scan.label === 'Spam' ? 'risk-badge-high' : (scan.label === 'Suspicious' ? 'risk-badge-medium' : 'risk-badge-low'));
          badgeVerdict.textContent = scan.label || 'Safe';
          tdVerdict.appendChild(badgeVerdict);
          tr.appendChild(tdVerdict);

          dashRecentTbody.appendChild(tr);
        });
      }
    }
  }

  // --------------------------------------------------------------------------
  // Reports View & Audit History (Filter, Sort, Paginate, Delete, Exports)
  // --------------------------------------------------------------------------

  function getFilteredScans(allRecords) {
    var searchStr = (historySearchInput ? historySearchInput.value : '').trim().toLowerCase();
    var verdictVal = historyFilterVerdict ? historyFilterVerdict.value : 'all';
    var sourceVal = historyFilterSource ? historyFilterSource.value : 'all';
    var sortVal = historySortBy ? historySortBy.value : 'newest';
    var startVal = historyDateStart ? historyDateStart.value : '';
    var endVal = historyDateEnd ? historyDateEnd.value : '';

    var startMs = startVal ? new Date(startVal + 'T00:00:00').getTime() : null;
    var endMs = endVal ? new Date(endVal + 'T23:59:59.999').getTime() : null;

    var filtered = allRecords.filter(function (r) {
      if (searchStr && !(r.subject || '').toLowerCase().includes(searchStr)) {
        return false;
      }
      if (verdictVal !== 'all' && r.label !== verdictVal) {
        return false;
      }
      if (sourceVal !== 'all' && (r.source_type || 'paste') !== sourceVal) {
        return false;
      }
      var t = r.created_at || (r.timestamp ? new Date(r.timestamp).getTime() : 0);
      if (startMs !== null && t < startMs) {
        return false;
      }
      if (endMs !== null && t > endMs) {
        return false;
      }
      return true;
    });

    filtered.sort(function (a, b) {
      if (sortVal === 'oldest') {
        return (a.created_at || 0) - (b.created_at || 0);
      } else if (sortVal === 'risk_desc') {
        return (b.risk_score || 0) - (a.risk_score || 0);
      } else if (sortVal === 'risk_asc') {
        return (a.risk_score || 0) - (b.risk_score || 0);
      }
      return (b.created_at || 0) - (a.created_at || 0);
    });

    return filtered;
  }

  async function renderReportsUI() {
    var allRecords = await getAllScanRecords();
    var filtered = getFilteredScans(allRecords);
    var totalFiltered = filtered.length;

    if (!historyEmptyState || !historyTableWrapper || !historyTbody) {
      return;
    }

    if (allRecords.length === 0) {
      if (historyEmptyTitle) historyEmptyTitle.textContent = 'No Scans Recorded Yet';
      if (historyEmptyDesc) historyEmptyDesc.textContent = 'Your scan history will automatically appear here as you analyze emails.';
      historyEmptyState.classList.remove('hidden');
      historyTableWrapper.classList.add('hidden');
      if (historyPaginationBar) historyPaginationBar.classList.add('hidden');
      return;
    }

    if (totalFiltered === 0) {
      if (historyEmptyTitle) historyEmptyTitle.textContent = 'No Matching Scans Found';
      if (historyEmptyDesc) historyEmptyDesc.textContent = 'Try adjusting your search terms, verdict filter, or date range.';
      historyEmptyState.classList.remove('hidden');
      historyTableWrapper.classList.add('hidden');
      if (historyPaginationBar) historyPaginationBar.classList.add('hidden');
      return;
    }

    historyEmptyState.classList.add('hidden');
    historyTableWrapper.classList.remove('hidden');

    // Pagination calculations
    var totalPages = Math.ceil(totalFiltered / REPORTS_PAGE_SIZE) || 1;
    if (reportsCurrentPage > totalPages) reportsCurrentPage = totalPages;
    if (reportsCurrentPage < 1) reportsCurrentPage = 1;

    var startIndex = (reportsCurrentPage - 1) * REPORTS_PAGE_SIZE;
    var endIndex = Math.min(startIndex + REPORTS_PAGE_SIZE, totalFiltered);
    var pageRecords = filtered.slice(startIndex, endIndex);

    if (historyPaginationBar) historyPaginationBar.classList.remove('hidden');
    if (historyPaginationInfo) {
      historyPaginationInfo.textContent = `Showing ${startIndex + 1} to ${endIndex} of ${totalFiltered} scans`;
    }
    if (historyPageCurrent) {
      historyPageCurrent.textContent = `Page ${reportsCurrentPage} of ${totalPages}`;
    }
    if (historyPagePrev) {
      historyPagePrev.disabled = reportsCurrentPage <= 1;
    }
    if (historyPageNext) {
      historyPageNext.disabled = reportsCurrentPage >= totalPages;
    }

    while (historyTbody.firstChild) {
      historyTbody.removeChild(historyTbody.firstChild);
    }

    pageRecords.forEach(function (scan) {
      var tr = document.createElement('tr');

      var tdDate = document.createElement('td');
      tdDate.textContent = formatDateTime(scan.created_at || scan.timestamp);
      tr.appendChild(tdDate);

      var tdSub = document.createElement('td');
      var strongSub = document.createElement('strong');
      var subTitle = scan.subject || 'Untitled Email';
      if (subTitle.length > 55) subTitle = subTitle.substring(0, 55) + '...';
      strongSub.textContent = subTitle;
      tdSub.appendChild(strongSub);
      tr.appendChild(tdSub);

      var tdSource = document.createElement('td');
      var badgeSource = document.createElement('span');
      badgeSource.className = 'badge-source';
      badgeSource.textContent = scan.source_type || 'paste';
      tdSource.appendChild(badgeSource);
      tr.appendChild(tdSource);

      var tdRisk = document.createElement('td');
      var badgeRisk = document.createElement('span');
      var riskVal = typeof scan.risk_score === 'number' ? scan.risk_score : 0;
      badgeRisk.className = 'badge ' + (riskVal >= 70 ? 'badge-danger' : (riskVal >= 35 ? 'badge-warning' : 'badge-success'));
      badgeRisk.textContent = `${riskVal}/100`;
      tdRisk.appendChild(badgeRisk);
      tr.appendChild(tdRisk);

      var tdVerdict = document.createElement('td');
      var badgeVerdict = document.createElement('span');
      badgeVerdict.className = 'risk-badge ' + (scan.label === 'Spam' ? 'risk-badge-high' : (scan.label === 'Suspicious' ? 'risk-badge-medium' : 'risk-badge-low'));
      badgeVerdict.textContent = scan.label || 'Safe';
      tdVerdict.appendChild(badgeVerdict);
      tr.appendChild(tdVerdict);

      var tdActions = document.createElement('td');
      tdActions.className = 'td-actions';
      var delBtn = document.createElement('button');
      delBtn.type = 'button';
      delBtn.className = 'btn btn-xs btn-outline btn-danger-outline';
      delBtn.textContent = 'Delete';
      delBtn.setAttribute('aria-label', `Delete scan for ${scan.subject}`);
      delBtn.addEventListener('click', async function (e) {
        e.stopPropagation();
        var ok = await deleteScanRecord(scan.id);
        if (ok) {
          showToast('Scan record deleted', 'info');
          await renderReportsUI();
          await updateDashboardUI();
        } else {
          showToast('Failed to delete scan record', 'error');
        }
      });
      tdActions.appendChild(delBtn);
      tr.appendChild(tdActions);

      historyTbody.appendChild(tr);
    });
  }

  async function exportHistoryCsv() {
    var allRecords = await getAllScanRecords();
    var filtered = getFilteredScans(allRecords);

    if (filtered.length === 0) {
      showToast('No scan records to export', 'warn');
      return;
    }

    try {
      var lines = [
        'ID,Timestamp,Subject,Source,Risk Score,Classification,Confidence,Indicator Count'
      ];

      filtered.forEach(function (r) {
        var row = [
          csvEscape(r.id),
          csvEscape(r.timestamp || new Date(r.created_at).toISOString()),
          csvEscape(r.subject || ''),
          csvEscape(r.source_type || 'paste'),
          csvEscape(r.risk_score ?? 0),
          csvEscape(r.label || 'Safe'),
          csvEscape(r.confidence ?? 0),
          csvEscape(r.indicator_count ?? 0)
        ];
        lines.push(row.join(','));
      });

      var csvContent = lines.join('\r\n');
      var blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      var url = URL.createObjectURL(blob);
      var a = document.createElement('a');
      a.href = url;
      a.download = `mailguard-history-${Date.now()}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      showToast(`Exported ${filtered.length} scan records to CSV`, 'success');
    } catch (e) {
      showToast('Failed to export CSV', 'error');
    }
  }

  async function exportHistoryJson() {
    var allRecords = await getAllScanRecords();
    var filtered = getFilteredScans(allRecords);

    if (filtered.length === 0) {
      showToast('No scan records to export', 'warn');
      return;
    }

    try {
      var exportPayload = {
        meta: {
          app: 'MailGuard AI',
          version: '2.0.0',
          exported_at: new Date().toISOString(),
          total_records: filtered.length,
          source: isStorageFallback ? 'client_memory_fallback' : 'client_indexeddb'
        },
        records: filtered
      };

      var jsonStr = JSON.stringify(exportPayload, null, 2);
      var blob = new Blob([jsonStr], { type: 'application/json' });
      var url = URL.createObjectURL(blob);
      var a = document.createElement('a');
      a.href = url;
      a.download = `mailguard-history-${Date.now()}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      showToast(`Exported ${filtered.length} scan records to JSON`, 'success');
    } catch (e) {
      showToast('Failed to export JSON', 'error');
    }
  }

  function initReportsEventListeners() {
    if (historySearchInput) {
      historySearchInput.addEventListener('input', function () {
        reportsCurrentPage = 1;
        renderReportsUI();
      });
    }

    if (historyFilterVerdict) {
      historyFilterVerdict.addEventListener('change', function () {
        reportsCurrentPage = 1;
        renderReportsUI();
      });
    }

    if (historyFilterSource) {
      historyFilterSource.addEventListener('change', function () {
        reportsCurrentPage = 1;
        renderReportsUI();
      });
    }

    if (historySortBy) {
      historySortBy.addEventListener('change', function () {
        renderReportsUI();
      });
    }

    if (historyDateStart) {
      historyDateStart.addEventListener('change', function () {
        reportsCurrentPage = 1;
        renderReportsUI();
      });
    }

    if (historyDateEnd) {
      historyDateEnd.addEventListener('change', function () {
        reportsCurrentPage = 1;
        renderReportsUI();
      });
    }

    if (historyPagePrev) {
      historyPagePrev.addEventListener('click', function () {
        if (reportsCurrentPage > 1) {
          reportsCurrentPage--;
          renderReportsUI();
        }
      });
    }

    if (historyPageNext) {
      historyPageNext.addEventListener('click', function () {
        reportsCurrentPage++;
        renderReportsUI();
      });
    }

    if (exportHistoryCsvBtn) {
      exportHistoryCsvBtn.addEventListener('click', exportHistoryCsv);
    }

    if (exportHistoryJsonBtn) {
      exportHistoryJsonBtn.addEventListener('click', exportHistoryJson);
    }

    if (clearHistoryBtn) {
      clearHistoryBtn.addEventListener('click', function () {
        if (window.confirm('Are you sure you want to clear all scan history from this device? This action cannot be undone.')) {
          clearAllScanRecords().then(function () {
            showToast('All scan history cleared', 'info');
            reportsCurrentPage = 1;
            renderReportsUI();
            updateDashboardUI();
          });
        }
      });
    }
  }

  // --------------------------------------------------------------------------
  // Phase 12F: Image Threat Analysis (Client-Side OCR & QR Engine)
  // --------------------------------------------------------------------------

  var isJsQRLoaded = false;
  var isTesseractLoaded = false;
  var jsQRLoadPromise = null;
  var tesseractLoadPromise = null;
  var currentOcrWorker = null;
  var isAnalysisCancelled = false;
  var selectedImageFile = null;
  var currentImageObjectUrl = null;

  // DOM Elements - Image Analysis View
  var imgDropZone = document.getElementById('img-drop-zone');
  var imgFileInput = document.getElementById('img-file-input');
  var imgBrowseBtn = document.getElementById('img-browse-btn');
  var imgDropOverlay = document.getElementById('img-drop-overlay');
  var imgAlertBox = document.getElementById('img-alert-box');
  var imgPreviewBox = document.getElementById('img-preview-box');
  var imgThumb = document.getElementById('img-thumb');
  var imgMetaText = document.getElementById('img-meta-text');
  var imgStartScanBtn = document.getElementById('img-start-scan-btn');
  var imgClearSelectionBtn = document.getElementById('img-clear-selection-btn');
  var imgProgressBox = document.getElementById('img-progress-box');
  var imgProgressStatusText = document.getElementById('img-progress-status-text');
  var imgProgressPercent = document.getElementById('img-progress-percent');
  var imgProgressFill = document.getElementById('img-progress-fill');
  var imgProgressTimerText = document.getElementById('img-progress-timer-text');
  var imgCancelScanBtn = document.getElementById('img-cancel-scan-btn');
  var imgReportContainer = document.getElementById('img-report-container');
  var imgVerdictBanner = document.getElementById('img-verdict-banner');
  var imgVerdictBadge = document.getElementById('img-verdict-badge');
  var imgRiskScoreVal = document.getElementById('img-risk-score-val');
  var imgOcrConfVal = document.getElementById('img-ocr-conf-val');
  var imgModelConfVal = document.getElementById('img-model-conf-val');
  var imgQrSection = document.getElementById('img-qr-section');
  var imgQrEmpty = document.getElementById('img-qr-empty');
  var imgQrContentBox = document.getElementById('img-qr-content-box');
  var imgQrTextVal = document.getElementById('img-qr-text-val');
  var imgCopyQrBtn = document.getElementById('img-copy-qr-btn');
  var imgOcrEmpty = document.getElementById('img-ocr-empty');
  var imgOcrTextDisplay = document.getElementById('img-ocr-text-display');
  var imgCopyTextBtn = document.getElementById('img-copy-text-btn');
  var imgSendToAnalyzerBtn = document.getElementById('img-send-to-analyzer-btn');
  var imgUrlsEmpty = document.getElementById('img-urls-empty');
  var imgUrlsTableWrapper = document.getElementById('img-urls-table-wrapper');
  var imgUrlsTbody = document.getElementById('img-urls-tbody');
  var imgFindingsList = document.getElementById('img-findings-list');
  var optImageOcr = document.getElementById('opt-image-ocr');

  function loadScriptOnce(src) {
    return new Promise(function (resolve, reject) {
      var existing = document.querySelector('script[src="' + src + '"]');
      if (existing) {
        if (existing.dataset.loaded === 'true') {
          return resolve();
        }
        existing.addEventListener('load', function () { resolve(); });
        existing.addEventListener('error', function (err) { reject(err); });
        return;
      }
      var script = document.createElement('script');
      script.src = src;
      script.async = true;
      script.addEventListener('load', function () {
        script.dataset.loaded = 'true';
        resolve();
      });
      script.addEventListener('error', function () {
        reject(new Error('Failed to load self-hosted library: ' + src));
      });
      document.head.appendChild(script);
    });
  }

  function ensureVendorLibrariesLoaded() {
    var promises = [];
    if (!isJsQRLoaded) {
      if (!jsQRLoadPromise) {
        jsQRLoadPromise = loadScriptOnce('/vendor/jsqr/jsQR.js').then(function () {
          isJsQRLoaded = true;
        });
      }
      promises.push(jsQRLoadPromise);
    }
    if (!isTesseractLoaded) {
      if (!tesseractLoadPromise) {
        tesseractLoadPromise = loadScriptOnce('/vendor/tesseract/tesseract.min.js').then(function () {
          isTesseractLoaded = true;
        });
      }
      promises.push(tesseractLoadPromise);
    }
    return Promise.all(promises);
  }

  function validateImageMagicBytes(file) {
    return new Promise(function (resolve) {
      if (!file) {
        return resolve({ valid: false, error: 'No file provided.' });
      }
      var MAX_SIZE = 5 * 1024 * 1024; // 5 MB
      if (file.size > MAX_SIZE) {
        var sizeMb = (file.size / (1024 * 1024)).toFixed(2);
        return resolve({
          valid: false,
          error: `File size (${sizeMb} MB) exceeds maximum allowed limit of 5 MB.`
        });
      }
      if (file.size < 8) {
        return resolve({ valid: false, error: 'File is too small or corrupted.' });
      }

      var reader = new FileReader();
      reader.onload = function (e) {
        var buffer = e.target.result;
        var bytes = new Uint8Array(buffer);
        // PNG: 89 50 4E 47
        var isPng = bytes[0] === 0x89 && bytes[1] === 0x50 && bytes[2] === 0x4E && bytes[3] === 0x47;
        // JPEG: FF D8 FF
        var isJpg = bytes[0] === 0xFF && bytes[1] === 0xD8 && bytes[2] === 0xFF;

        if (isPng || isJpg) {
          resolve({ valid: true, type: isPng ? 'PNG' : 'JPEG' });
        } else {
          resolve({
            valid: false,
            error: 'Invalid file format: File content does not match PNG or JPEG magic bytes signature.'
          });
        }
      };
      reader.onerror = function () {
        resolve({ valid: false, error: 'Failed to read file contents for magic bytes verification.' });
      };
      reader.readAsArrayBuffer(file.slice(0, 16));
    });
  }

  function loadImageToCanvas(file) {
    return new Promise(function (resolve, reject) {
      var objectUrl = URL.createObjectURL(file);
      var img = new Image();
      img.onload = function () {
        var w = img.naturalWidth || img.width;
        var h = img.naturalHeight || img.height;
        var maxDim = Math.max(w, h);
        var targetW = w;
        var targetH = h;
        // Downscale large images (max 1600px longest dimension) to preserve memory and speed
        if (maxDim > 1600) {
          var scale = 1600 / maxDim;
          targetW = Math.round(w * scale);
          targetH = Math.round(h * scale);
        }

        var canvas = document.createElement('canvas');
        canvas.width = targetW;
        canvas.height = targetH;
        var ctx = canvas.getContext('2d');
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';
        ctx.drawImage(img, 0, 0, targetW, targetH);
        resolve({
          canvas: canvas,
          ctx: ctx,
          width: targetW,
          height: targetH,
          originalWidth: w,
          originalHeight: h,
          objectUrl: objectUrl
        });
      };
      img.onerror = function () {
        URL.revokeObjectURL(objectUrl);
        reject(new Error('Failed to decode image pixels into canvas.'));
      };
      img.src = objectUrl;
    });
  }

  function scanQrCode(canvas, ctx, width, height) {
    try {
      if (typeof window.jsQR !== 'function') {
        return null;
      }
      var imageData = ctx.getImageData(0, 0, width, height);
      var code = window.jsQR(imageData.data, width, height, {
        inversionAttempts: 'attemptBoth'
      });
      return code ? code.data : null;
    } catch (e) {
      return null;
    }
  }

  function runOcrOnCanvas(canvas, onProgress) {
    return new Promise(function (resolve, reject) {
      if (!window.Tesseract) {
        return reject(new Error('Tesseract.js OCR library is not available.'));
      }

      var isTerminated = false;
      var worker = null;

      // 30s timeout
      var timeoutId = setTimeout(function () {
        if (!isTerminated && worker) {
          isTerminated = true;
          worker.terminate().catch(function () {});
          reject(new Error('OCR recognition timed out after 30 seconds.'));
        }
      }, 30000);

      window.Tesseract.createWorker(['eng'], 1, {
        workerPath: '/vendor/tesseract/worker.min.js',
        corePath: '/vendor/tesseract/tesseract-core-simd-lstm.wasm.js',
        langPath: '/vendor/tesseract',
        gzip: true,
        logger: function (m) {
          if (isTerminated) return;
          if (typeof onProgress === 'function') {
            onProgress(m);
          }
        }
      }).then(function (w) {
        if (isTerminated) {
          w.terminate().catch(function () {});
          return;
        }
        worker = w;
        currentOcrWorker = w;
        return worker.recognize(canvas);
      }).then(function (res) {
        clearTimeout(timeoutId);
        currentOcrWorker = null;
        if (isTerminated) return;
        isTerminated = true;
        if (worker) {
          worker.terminate().catch(function () {});
        }
        var text = (res && res.data && res.data.text) ? res.data.text.trim() : '';
        var confidence = (res && res.data && typeof res.data.confidence === 'number') ? res.data.confidence : 0;
        resolve({ text: text, confidence: confidence });
      }).catch(function (err) {
        clearTimeout(timeoutId);
        currentOcrWorker = null;
        if (isTerminated) return;
        isTerminated = true;
        if (worker) {
          worker.terminate().catch(function () {});
        }
        reject(err);
      });
    });
  }

  function showImageAlert(msg, type = 'danger') {
    if (!imgAlertBox) return;
    imgAlertBox.textContent = msg;
    imgAlertBox.className = `alert alert-${type}`;
    imgAlertBox.classList.remove('hidden');
  }

  function hideImageAlert() {
    if (!imgAlertBox) return;
    imgAlertBox.textContent = '';
    imgAlertBox.classList.add('hidden');
  }

  function updateImageProgress(pct, statusText) {
    if (typeof pct === 'number' && imgProgressPercent && imgProgressFill) {
      var clamped = Math.max(0, Math.min(100, pct));
      imgProgressPercent.textContent = `${clamped}%`;
      imgProgressFill.style.width = `${clamped}%`;
    }
    if (statusText && imgProgressStatusText) {
      imgProgressStatusText.textContent = statusText;
    }
  }

  async function handleImageFileSelection(file) {
    if (!file) return;
    hideImageAlert();
    if (imgReportContainer) imgReportContainer.classList.add('hidden');

    var validation = await validateImageMagicBytes(file);
    if (!validation.valid) {
      showImageAlert(validation.error, 'danger');
      if (imgPreviewBox) imgPreviewBox.classList.add('hidden');
      selectedImageFile = null;
      if (imgFileInput) imgFileInput.value = '';
      return;
    }

    selectedImageFile = file;

    if (currentImageObjectUrl) {
      URL.revokeObjectURL(currentImageObjectUrl);
    }
    currentImageObjectUrl = URL.createObjectURL(file);

    if (imgThumb) {
      imgThumb.src = currentImageObjectUrl;
    }

    var sizeKb = (file.size / 1024).toFixed(1);
    var imgTemp = new Image();
    imgTemp.onload = function () {
      if (imgMetaText) {
        imgMetaText.textContent = `${file.name} (${sizeKb} KB) — ${imgTemp.naturalWidth} × ${imgTemp.naturalHeight} px (${validation.type})`;
      }
    };
    imgTemp.src = currentImageObjectUrl;

    if (imgPreviewBox) imgPreviewBox.classList.remove('hidden');
    // Lazy-load vendor libraries in background while user views preview
    ensureVendorLibrariesLoaded().catch(function () {});
  }

  function renderImageAnalysisReport(analysisData, ocrText, ocrConfidence, qrContent) {
    if (!imgReportContainer) return;

    // Verdict
    var classification = analysisData.classification || 'Safe';
    if (imgVerdictBadge) {
      imgVerdictBadge.textContent = classification;
      imgVerdictBadge.className = 'badge verdict-badge verdict-' + classification.toLowerCase();
    }

    if (imgRiskScoreVal) {
      imgRiskScoreVal.textContent = `${analysisData.risk_score.toFixed(1)} / 100`;
    }

    if (imgOcrConfVal) {
      imgOcrConfVal.textContent = `${ocrConfidence.toFixed(1)}%`;
    }

    if (imgModelConfVal) {
      var modelConf = analysisData.model ? (analysisData.model.confidence * 100).toFixed(1) : '0.0';
      imgModelConfVal.textContent = `${modelConf}%`;
    }

    // QR Code
    if (qrContent) {
      if (imgQrEmpty) imgQrEmpty.classList.add('hidden');
      if (imgQrContentBox) imgQrContentBox.classList.remove('hidden');
      if (imgCopyQrBtn) imgCopyQrBtn.classList.remove('hidden');
      if (imgQrTextVal) imgQrTextVal.textContent = qrContent;
    } else {
      if (imgQrEmpty) imgQrEmpty.classList.remove('hidden');
      if (imgQrContentBox) imgQrContentBox.classList.add('hidden');
      if (imgCopyQrBtn) imgCopyQrBtn.classList.add('hidden');
      if (imgQrTextVal) imgQrTextVal.textContent = '';
    }

    // Extracted OCR text
    if (ocrText && ocrText.trim()) {
      if (imgOcrEmpty) imgOcrEmpty.classList.add('hidden');
      if (imgOcrTextDisplay) {
        imgOcrTextDisplay.classList.remove('hidden');
        imgOcrTextDisplay.textContent = ocrText;
      }
    } else {
      if (imgOcrEmpty) imgOcrEmpty.classList.remove('hidden');
      if (imgOcrTextDisplay) {
        imgOcrTextDisplay.classList.add('hidden');
        imgOcrTextDisplay.textContent = '';
      }
    }

    // Extracted URLs
    while (imgUrlsTbody && imgUrlsTbody.firstChild) {
      imgUrlsTbody.removeChild(imgUrlsTbody.firstChild);
    }

    var urls = analysisData.urls || [];
    if (urls.length > 0 && imgUrlsTbody) {
      urls.forEach(function (uObj) {
        var tr = document.createElement('tr');
        var tdUrl = document.createElement('td');
        var codeEl = document.createElement('code');
        codeEl.textContent = uObj.url;
        tdUrl.appendChild(codeEl);

        var tdFlags = document.createElement('td');
        var flags = uObj.flags || [];
        if (flags.length === 0) {
          var cleanBadge = document.createElement('span');
          cleanBadge.className = 'badge badge-safe';
          cleanBadge.textContent = 'benign';
          tdFlags.appendChild(cleanBadge);
        } else {
          flags.forEach(function (f) {
            var fBadge = document.createElement('span');
            fBadge.className = 'badge badge-warn';
            fBadge.textContent = f;
            tdFlags.appendChild(fBadge);
          });
        }

        tr.appendChild(tdUrl);
        tr.appendChild(tdFlags);
        imgUrlsTbody.appendChild(tr);
      });

      if (imgUrlsEmpty) imgUrlsEmpty.classList.add('hidden');
      if (imgUrlsTableWrapper) imgUrlsTableWrapper.classList.remove('hidden');
    } else {
      if (imgUrlsEmpty) imgUrlsEmpty.classList.remove('hidden');
      if (imgUrlsTableWrapper) imgUrlsTableWrapper.classList.add('hidden');
    }

    // Key findings
    while (imgFindingsList && imgFindingsList.firstChild) {
      imgFindingsList.removeChild(imgFindingsList.firstChild);
    }
    var findings = analysisData.key_findings || [];
    if (imgFindingsList) {
      findings.forEach(function (fText) {
        var li = document.createElement('li');
        li.textContent = fText;
        imgFindingsList.appendChild(li);
      });
    }
  }

  async function startImageThreatAnalysis() {
    if (!selectedImageFile) {
      showImageAlert('Please select an image file first.', 'danger');
      return;
    }

    isAnalysisCancelled = false;
    hideImageAlert();
    if (imgReportContainer) imgReportContainer.classList.add('hidden');
    if (imgProgressBox) imgProgressBox.classList.remove('hidden');
    if (imgStartScanBtn) imgStartScanBtn.disabled = true;

    updateImageProgress(5, 'Loading vision engine (WASM & OCR)...');

    var timeoutSeconds = 30;
    if (imgProgressTimerText) imgProgressTimerText.textContent = `Timeout limit: ${timeoutSeconds}s`;

    var timerInterval = setInterval(function () {
      timeoutSeconds--;
      if (imgProgressTimerText) {
        imgProgressTimerText.textContent = `Timeout limit: ${timeoutSeconds}s`;
      }
      if (timeoutSeconds <= 0) {
        clearInterval(timerInterval);
      }
    }, 1000);

    var imgCanvasData = null;

    try {
      // 1. Ensure vendor libraries are loaded
      await ensureVendorLibrariesLoaded();
      if (isAnalysisCancelled) throw new Error('Analysis cancelled by user.');

      updateImageProgress(20, 'Preparing downscaled image canvas...');

      // 2. Load to off-screen canvas & downscale
      imgCanvasData = await loadImageToCanvas(selectedImageFile);
      if (isAnalysisCancelled) throw new Error('Analysis cancelled by user.');

      updateImageProgress(30, 'Scanning for embedded QR codes...');

      // 3. Scan QR code
      var qrContent = scanQrCode(imgCanvasData.canvas, imgCanvasData.ctx, imgCanvasData.width, imgCanvasData.height);
      if (isAnalysisCancelled) throw new Error('Analysis cancelled by user.');

      updateImageProgress(40, 'Executing OCR character recognition...');

      // 4. Run Tesseract OCR with progress updates
      var ocrResult = await runOcrOnCanvas(imgCanvasData.canvas, function (m) {
        if (isAnalysisCancelled) return;
        if (m.status === 'recognizing text' && typeof m.progress === 'number') {
          var mappedPct = 40 + Math.round(m.progress * 45); // 40% to 85%
          updateImageProgress(mappedPct, `Extracting text (${Math.round(m.progress * 100)}%)...`);
        } else if (m.status) {
          updateImageProgress(null, m.status);
        }
      });

      if (isAnalysisCancelled) throw new Error('Analysis cancelled by user.');

      var ocrText = ocrResult.text || '';
      var ocrConfidence = ocrResult.confidence || 0;

      updateImageProgress(90, 'Evaluating threat indicators & NLP signals...');

      // 5. Submit to backend /api/analyze
      var combinedText = ocrText;
      if (qrContent) {
        combinedText += (combinedText ? '\n\n' : '') + '[Decoded QR Code]: ' + qrContent;
      }

      var analysisData = null;
      if (!combinedText.trim()) {
        // Plain benign image with zero text and zero QR code
        analysisData = {
          model: { label: 'ham', probability: 0.0, confidence: 0.99, uncertain: false },
          risk_score: 0.0,
          classification: 'Safe',
          indicators: [],
          key_findings: [
            'Clean image: Zero text, phishing lures, or suspicious QR codes detected.',
            'OCR scan detected no extractable character data.'
          ],
          urls: [],
          top_tokens: [],
          vocab_coverage: 100.0,
          sensitivity: 'medium'
        };
      } else {
        var sensSelect = document.getElementById('analyzer-sensitivity-select');
        var sens = sensSelect ? sensSelect.value : 'medium';
        var resp = await fetch('/api/analyze', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text: combinedText,
            options: {
              scan_urls: true,
              analyze_headers: false,
              sensitivity: sens
            }
          })
        });

        if (!resp.ok) {
          var errJson = await resp.json().catch(function () { return {}; });
          throw new Error(errJson.error && errJson.error.message ? errJson.error.message : `Server returned error ${resp.status}`);
        }
        analysisData = await resp.json();
      }

      if (isAnalysisCancelled) throw new Error('Analysis cancelled by user.');

      updateImageProgress(100, 'Scan complete!');
      clearInterval(timerInterval);

      // 6. Render report and record to IndexedDB
      renderImageAnalysisReport(analysisData, ocrText, ocrConfidence, qrContent);

      if (imgProgressBox) imgProgressBox.classList.add('hidden');
      if (imgReportContainer) imgReportContainer.classList.remove('hidden');

      // Save scan to IndexedDB
      var previewSubject = 'Image: ' + (ocrText.slice(0, 40).replace(/\n/g, ' ') || (qrContent ? qrContent.slice(0, 40) : '') || selectedImageFile.name);
      await saveScanRecord({
        timestamp: Date.now(),
        subject: previewSubject,
        verdict: analysisData.classification,
        riskScore: analysisData.risk_score,
        sourceType: 'image'
      });
      await updateDashboardUI();
      showToast('Image threat analysis complete', 'success');

    } catch (err) {
      clearInterval(timerInterval);
      if (imgProgressBox) imgProgressBox.classList.add('hidden');
      if (isAnalysisCancelled) {
        showImageAlert('Image analysis was cancelled.', 'info');
      } else {
        showImageAlert(err.message || 'Image threat analysis failed.', 'danger');
      }
    } finally {
      if (timerInterval) clearInterval(timerInterval);
      if (imgStartScanBtn) imgStartScanBtn.disabled = false;
      if (imgCanvasData && imgCanvasData.objectUrl) {
        URL.revokeObjectURL(imgCanvasData.objectUrl);
      }
      currentOcrWorker = null;
    }
  }

  async function processImageForAnalyzer(file) {
    if (!file) return;
    try {
      showToast('Processing image with OCR...', 'info');
      var val = await validateImageMagicBytes(file);
      if (!val.valid) {
        bodyError.textContent = val.error;
        bodyError.classList.remove('hidden');
        showToast(val.error, 'error');
        return;
      }
      await ensureVendorLibrariesLoaded();
      var imgData = await loadImageToCanvas(file);
      var qrContent = scanQrCode(imgData.canvas, imgData.ctx, imgData.width, imgData.height);
      var ocrResult = await runOcrOnCanvas(imgData.canvas, function (m) {
        if (m.status === 'recognizing text' && typeof m.progress === 'number') {
          showToast(`OCR extracting: ${Math.round(m.progress * 100)}%`, 'info');
        }
      });
      if (imgData.objectUrl) URL.revokeObjectURL(imgData.objectUrl);

      var ocrText = ocrResult.text || '';
      var combined = ocrText;
      if (qrContent) {
        combined += (combined ? '\n\n' : '') + '[Decoded QR Code]: ' + qrContent;
      }

      if (!combined.trim()) {
        bodyError.textContent = 'No text or QR codes were detected in the image.';
        bodyError.classList.remove('hidden');
        showToast('No text detected in image', 'warn');
        return;
      }

      bodyInput.value = combined;
      updateCharCount();
      bodyError.classList.add('hidden');
      showToast('Image OCR extracted successfully', 'success');
      handleFormSubmit();
    } catch (err) {
      bodyError.textContent = 'Image OCR failed: ' + err.message;
      bodyError.classList.remove('hidden');
      showToast('Image processing failed: ' + err.message, 'error');
    }
  }

  function initImageAnalysisModule() {
    if (imgDropZone) {
      ['dragenter', 'dragover'].forEach(function (ev) {
        imgDropZone.addEventListener(ev, function (e) {
          e.preventDefault();
          e.stopPropagation();
          imgDropZone.classList.add('drag-over');
          if (imgDropOverlay) imgDropOverlay.classList.remove('hidden');
        });
      });

      ['dragleave', 'dragend'].forEach(function (ev) {
        imgDropZone.addEventListener(ev, function (e) {
          e.preventDefault();
          e.stopPropagation();
          imgDropZone.classList.remove('drag-over');
          if (imgDropOverlay) imgDropOverlay.classList.add('hidden');
        });
      });

      imgDropZone.addEventListener('drop', function (e) {
        e.preventDefault();
        e.stopPropagation();
        imgDropZone.classList.remove('drag-over');
        if (imgDropOverlay) imgDropOverlay.classList.add('hidden');
        if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
          handleImageFileSelection(e.dataTransfer.files[0]);
        }
      });
    }

    if (imgBrowseBtn && imgFileInput) {
      imgBrowseBtn.addEventListener('click', function () {
        imgFileInput.click();
      });

      imgFileInput.addEventListener('change', function () {
        if (imgFileInput.files && imgFileInput.files.length > 0) {
          handleImageFileSelection(imgFileInput.files[0]);
        }
      });
    }

    if (imgClearSelectionBtn) {
      imgClearSelectionBtn.addEventListener('click', function () {
        selectedImageFile = null;
        if (currentImageObjectUrl) {
          URL.revokeObjectURL(currentImageObjectUrl);
          currentImageObjectUrl = null;
        }
        if (imgThumb) imgThumb.src = '';
        if (imgPreviewBox) imgPreviewBox.classList.add('hidden');
        if (imgReportContainer) imgReportContainer.classList.add('hidden');
        hideImageAlert();
        if (imgFileInput) imgFileInput.value = '';
      });
    }

    if (imgStartScanBtn) {
      imgStartScanBtn.addEventListener('click', function () {
        startImageThreatAnalysis();
      });
    }

    if (imgCancelScanBtn) {
      imgCancelScanBtn.addEventListener('click', function () {
        isAnalysisCancelled = true;
        if (currentOcrWorker) {
          currentOcrWorker.terminate().catch(function () {});
          currentOcrWorker = null;
        }
        if (imgProgressBox) imgProgressBox.classList.add('hidden');
        if (imgStartScanBtn) imgStartScanBtn.disabled = false;
        showImageAlert('Image analysis was cancelled by user.', 'info');
        showToast('Image scan cancelled', 'info');
      });
    }

    if (imgCopyTextBtn && imgOcrTextDisplay) {
      imgCopyTextBtn.addEventListener('click', function () {
        var t = imgOcrTextDisplay.textContent || '';
        if (!t) return;
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(t).then(function () {
            showToast('OCR text copied to clipboard', 'success');
          }).catch(function () {
            fallbackCopyText(t);
          });
        } else {
          fallbackCopyText(t);
        }
      });
    }

    if (imgCopyQrBtn && imgQrTextVal) {
      imgCopyQrBtn.addEventListener('click', function () {
        var q = imgQrTextVal.textContent || '';
        if (!q) return;
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(q).then(function () {
            showToast('QR code content copied to clipboard', 'success');
          }).catch(function () {
            fallbackCopyText(q);
          });
        } else {
          fallbackCopyText(q);
        }
      });
    }

    if (imgSendToAnalyzerBtn && imgOcrTextDisplay) {
      imgSendToAnalyzerBtn.addEventListener('click', function () {
        var t = imgOcrTextDisplay.textContent || '';
        if (!t) return;
        bodyInput.value = t;
        updateCharCount();
        window.location.hash = '#/analyzer';
        showToast('Transferred OCR text to Email Analyzer', 'info');
      });
    }

    // OCR Toggle in Email Analyzer
    if (optImageOcr) {
      try {
        var savedOcr = localStorage.getItem('mailguard_opt_image_ocr');
        if (savedOcr === 'true') {
          optImageOcr.checked = true;
          if (filePickerInput) {
            filePickerInput.accept = '.eml,.txt,.msg,.png,.jpg,.jpeg';
          }
        }
      } catch (e) {}

      optImageOcr.addEventListener('change', function () {
        try {
          localStorage.setItem('mailguard_opt_image_ocr', optImageOcr.checked ? 'true' : 'false');
        } catch (e) {}
        if (filePickerInput) {
          filePickerInput.accept = optImageOcr.checked ? '.eml,.txt,.msg,.png,.jpg,.jpeg' : '.eml,.txt,.msg';
        }
        if (optImageOcr.checked) {
          ensureVendorLibrariesLoaded().catch(function () {});
          showToast('Image OCR & QR enabled in analyzer', 'info');
        }
      });
    }
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

    // 6. Refresh view data when navigating to dashboard or reports
    if (rawHash === '#/dashboard') {
      updateDashboardUI();
    } else if (rawHash === '#/reports') {
      renderReportsUI();
    } else if (rawHash === '#/image-analysis') {
      ensureVendorLibrariesLoaded().catch(function () {});
    }
  }

  function initAppShell() {
    // Hash routing listeners
    window.addEventListener('hashchange', function () {
      handleRoute(window.location.hash);
    });

    // Initialize reports view event listeners
    initReportsEventListeners();

    // Initialize image threat analysis module
    initImageAnalysisModule();

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

    // ------------------------------------------------------------------------
    // Phase 12E: Settings, Analysis Preferences & REST API Integration
    // ------------------------------------------------------------------------

    // Apply stored settings
    var activeSettings = getStoredSettings();
    syncSettingsToUi(activeSettings);

    // Sync options changed directly in Email Analyzer
    if (analyzerSensitivitySelect) {
      analyzerSensitivitySelect.addEventListener('change', function () {
        var s = getStoredSettings();
        s.sensitivity = analyzerSensitivitySelect.value;
        saveStoredSettings(s);
        if (prefSensitivity) prefSensitivity.value = s.sensitivity;
        showToast('Sensitivity set to ' + s.sensitivity.toUpperCase(), 'info');
      });
    }

    if (optExtractUrls) {
      optExtractUrls.addEventListener('change', function () {
        var s = getStoredSettings();
        s.scan_urls = optExtractUrls.checked;
        saveStoredSettings(s);
        if (prefScanUrls) prefScanUrls.checked = s.scan_urls;
      });
    }

    if (optAnalyzeHeaders) {
      optAnalyzeHeaders.addEventListener('change', function () {
        var s = getStoredSettings();
        s.analyze_headers = optAnalyzeHeaders.checked;
        saveStoredSettings(s);
        if (prefAnalyzeHeaders) prefAnalyzeHeaders.checked = s.analyze_headers;
      });
    }

    // Settings preferences form submit
    if (settingsPreferencesForm) {
      settingsPreferencesForm.addEventListener('submit', function (e) {
        e.preventDefault();
        var newSettings = {
          sensitivity: prefSensitivity ? prefSensitivity.value : 'medium',
          scan_urls: prefScanUrls ? prefScanUrls.checked : true,
          analyze_headers: prefAnalyzeHeaders ? prefAnalyzeHeaders.checked : true
        };
        saveStoredSettings(newSettings);
        syncSettingsToUi(newSettings);
        showToast('Preferences saved successfully.', 'success');
      });
    }

    // Reset preferences to default
    if (resetPreferencesBtn) {
      resetPreferencesBtn.addEventListener('click', function () {
        var defaultSettings = {
          sensitivity: 'medium',
          scan_urls: true,
          analyze_headers: true
        };
        saveStoredSettings(defaultSettings);
        syncSettingsToUi(defaultSettings);
        showToast('Preferences reset to defaults.', 'info');
      });
    }

    // Settings Sub-tab switcher
    function switchSettingsTab(targetTab) {
      var tabs = [
        { name: 'pref', btn: tabBtnPref, panel: settingsPanelPref },
        { name: 'api', btn: tabBtnApi, panel: settingsPanelApi },
        { name: 'account', btn: tabBtnAccount, panel: settingsPanelAccount }
      ];
      tabs.forEach(function (t) {
        if (t.name === targetTab) {
          if (t.btn) {
            t.btn.classList.add('active');
            t.btn.setAttribute('aria-selected', 'true');
          }
          if (t.panel) t.panel.classList.remove('hidden');
        } else {
          if (t.btn) {
            t.btn.classList.remove('active');
            t.btn.setAttribute('aria-selected', 'false');
          }
          if (t.panel) t.panel.classList.add('hidden');
        }
      });
    }

    if (tabBtnPref) tabBtnPref.addEventListener('click', function () { switchSettingsTab('pref'); });
    if (tabBtnApi) tabBtnApi.addEventListener('click', function () { switchSettingsTab('api'); });
    if (tabBtnAccount) tabBtnAccount.addEventListener('click', function () { switchSettingsTab('account'); });

    // Copy Code Snippets
    var copyButtons = document.querySelectorAll('.btn-copy-code');
    copyButtons.forEach(function (btn) {
      btn.addEventListener('click', function () {
        var targetId = btn.getAttribute('data-target');
        var targetEl = document.getElementById(targetId);
        if (!targetEl) return;
        var textToCopy = targetEl.textContent || '';
        function notifyCopied() {
          var originalLabel = btn.textContent;
          btn.textContent = '✓ Copied!';
          showToast('Snippet copied to clipboard.', 'success');
          setTimeout(function () {
            btn.textContent = originalLabel;
          }, 2000);
        }
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(textToCopy).then(notifyCopied).catch(function () {
            copyTextFallback(textToCopy, notifyCopied);
          });
        } else {
          copyTextFallback(textToCopy, notifyCopied);
        }
      });
    });

    function copyTextFallback(text, onSuccess) {
      try {
        var tempArea = document.createElement('textarea');
        tempArea.value = text;
        tempArea.style.position = 'fixed';
        tempArea.style.left = '-9999px';
        document.body.appendChild(tempArea);
        tempArea.focus();
        tempArea.select();
        document.execCommand('copy');
        document.body.removeChild(tempArea);
        if (onSuccess) onSuccess();
      } catch (err) {
        showToast('Clipboard copy failed.', 'error');
      }
    }

    // Account & Storage Controls
    if (clearLocalHistoryBtn) {
      clearLocalHistoryBtn.addEventListener('click', async function () {
        if (window.confirm('Delete all scan history on this device? This action cannot be undone.')) {
          try {
            await clearAllScans();
            showToast('Local scan history cleared.', 'success');
            await refreshHistoryView();
            await updateDashboardUI();
          } catch (err) {
            showToast('Failed to clear history: ' + err.message, 'error');
          }
        }
      });
    }

    if (clearLocalSettingsBtn) {
      clearLocalSettingsBtn.addEventListener('click', function () {
        try {
          localStorage.removeItem('mailguard_settings');
          var def = { sensitivity: 'medium', scan_urls: true, analyze_headers: true };
          syncSettingsToUi(def);
          showToast('Preferences reset to defaults.', 'info');
        } catch (e) {
          console.warn('Failed to clear stored settings', e);
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
  initDatabase().then(function () {
    updateDashboardUI();
    initAppShell();
  });

})();
