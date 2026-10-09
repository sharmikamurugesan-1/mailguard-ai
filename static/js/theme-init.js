/**
 * MailGuard AI - Theme Initialization Script
 * Runs synchronously in <head> before first render to prevent theme flashing (FOUT/FOUC).
 * Strictly zero inline scripts, CSP compliant (script-src 'self').
 */
(function () {
  'use strict';
  try {
    var stored = localStorage.getItem('mailguard_theme');
    if (stored === 'dark' || stored === 'light') {
      document.documentElement.setAttribute('data-theme', stored);
      return;
    }
  } catch (e) {
    // localStorage may be inaccessible in certain sandboxed frames
  }

  try {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      document.documentElement.setAttribute('data-theme', 'dark');
      return;
    }
  } catch (e) {
    // matchMedia unavailable
  }

  document.documentElement.setAttribute('data-theme', 'light');
})();
