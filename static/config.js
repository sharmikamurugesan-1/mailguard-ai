/**
 * MailGuard AI - Runtime Configuration
 *
 * Configures the backend API base URL for both:
 * 1. Monolith / Single-origin deployment (Flask serving frontend on Render)
 * 2. Split architecture (Vercel static frontend + Render backend API)
 *
 * Development default: http://127.0.0.1:5000 (when serving static from another port)
 * Production placeholder: https://mailguard-ai.onrender.com
 * No secrets are stored here.
 */
(function () {
  'use strict';

  // Allow explicit override via window.MAILGUARD_API_URL if injected by tests
  if (window.MAILGUARD_API_URL) {
    window.API_BASE_URL = window.MAILGUARD_API_URL;
    window.APP_CONFIG = { API_BASE_URL: window.MAILGUARD_API_URL };
    return;
  }

  // Development backend endpoint for local cross-origin testing
  var DEV_API_URL = 'http://127.0.0.1:5000';

  // Production Render backend endpoint placeholder
  var PROD_API_URL = 'https://mailguard-ai.onrender.com';

  var hostname = window.location.hostname;
  var isLocalhost = Boolean(
    hostname === 'localhost' ||
    hostname === '127.0.0.1' ||
    hostname === '[::1]'
  );

  var apiUrl;
  if (isLocalhost && window.location.port !== '5000' && window.location.port !== '') {
    // Local static server on another port (e.g. http://localhost:3000) talking to local Flask
    apiUrl = DEV_API_URL;
  } else if (!isLocalhost && (hostname.endsWith('.vercel.app') || hostname.includes('vercel'))) {
    // Vercel deployment talking to Render backend
    apiUrl = PROD_API_URL;
  } else if (window.location.origin && window.location.origin !== 'null') {
    // Same-origin monolith fallback (Render or local Flask port 5000)
    apiUrl = window.location.origin;
  } else {
    apiUrl = DEV_API_URL;
  }

  window.API_BASE_URL = apiUrl;
  window.APP_CONFIG = {
    API_BASE_URL: apiUrl,
    VERSION: '2.0.0'
  };
})();
