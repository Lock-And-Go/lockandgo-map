/* LockAndGo · custom GA4 events
 * Fires on: book_click (affiliate partner outbound), external_outbound_click,
 *           map_open, area_view, spot_view, blog_75_scroll.
 * Loads via <script defer src="/analytics-events.js"></script> right before </body>.
 */
(function () {
  'use strict';

  // Bail if gtag isn't available (e.g. ad-blocker, consent denied)
  if (typeof window.gtag !== 'function') return;

  // ── 1. Outbound link clicks (affiliates + generic outbound) ──────────────
  document.addEventListener(
    'click',
    function (e) {
      var a = e.target.closest && e.target.closest('a[href]');
      if (!a) return;
      var href = a.href;
      if (!href || href.indexOf('http') !== 0) return;

      var host;
      try {
        host = new URL(href).hostname;
      } catch (_) {
        return;
      }
      // Skip internal links
      if (host.indexOf('lockandgo.sk') !== -1) return;

      // Identify affiliate partners
      var partner = null;
      if (/(^|\.)bounce\.com$/.test(host)) partner = 'bounce';
      else if (/(^|\.)radicalstorage\.com$/.test(host)) partner = 'radical';
      else if (/(^|\.)luggagehero\.com$/.test(host)) partner = 'luggagehero';
      else if (/(^|\.)stasher\.com$/.test(host)) partner = 'stasher';

      if (partner) {
        gtag('event', 'book_click', {
          partner: partner,
          link_domain: host,
          link_url: href,
          link_text: (a.innerText || a.textContent || '').trim().slice(0, 80),
          page_path: location.pathname
        });
      } else {
        gtag('event', 'external_outbound_click', {
          link_domain: host,
          link_url: href,
          link_text: (a.innerText || a.textContent || '').trim().slice(0, 80),
          page_path: location.pathname
        });
      }
    },
    { passive: true, capture: true }
  );

  // ── 2. Path-aware page-type events (fires once on load) ──────────────────
  var path = location.pathname || '/';
  var lang = path.indexOf('/en') === 0 ? 'en' : 'sk';

  if (path === '/app' || path === '/en/app') {
    gtag('event', 'map_open', { page_lang: lang });
  } else if (path.indexOf('/area/') !== -1) {
    var areaSlug = path.split('/').filter(Boolean).pop();
    gtag('event', 'area_view', { area_slug: areaSlug, page_lang: lang });
  } else if (path.indexOf('/spot/') === 0) {
    var spotSlug = path.split('/').filter(Boolean).pop();
    gtag('event', 'spot_view', { spot_slug: spotSlug });
  }

  // ── 3. Blog 75% scroll depth ─────────────────────────────────────────────
  if (path.indexOf('/blog/') === 0) {
    var fired = false;
    function onScroll() {
      if (fired) return;
      var doc = document.documentElement;
      var scrollTop = doc.scrollTop || document.body.scrollTop || 0;
      var scrollHeight = Math.max(doc.scrollHeight, document.body.scrollHeight);
      var clientHeight = doc.clientHeight || window.innerHeight;
      if (scrollHeight <= clientHeight) return;
      var pct = (scrollTop + clientHeight) / scrollHeight;
      if (pct >= 0.75) {
        fired = true;
        gtag('event', 'blog_75_scroll', {
          article_slug: path.split('/').filter(Boolean).pop()
        });
        window.removeEventListener('scroll', onScroll);
      }
    }
    window.addEventListener('scroll', onScroll, { passive: true });
  }
})();
