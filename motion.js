// LockAndGo — scroll-reveal + number counters (vanilla, no deps).
// Inspired by Watermelon UI / Skiper UI scroll-into-view effects.
(function(){
  if (typeof window === 'undefined') return;
  var reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ── Scroll reveal ─────────────────────────────────────────────────────────
  var reveals = document.querySelectorAll('.reveal');
  if (reveals.length) {
    if (reduced || !('IntersectionObserver' in window)) {
      reveals.forEach(function(el){ el.classList.add('is-visible'); });
    } else {
      var revealObs = new IntersectionObserver(function(entries){
        entries.forEach(function(entry){
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            revealObs.unobserve(entry.target);
          }
        });
      }, { threshold: 0.12, rootMargin: '0px 0px -60px 0px' });
      reveals.forEach(function(el){ revealObs.observe(el); });
    }
  }

  // ── Number counters ───────────────────────────────────────────────────────
  function format(n, locale) {
    try { return n.toLocaleString(locale || 'sk-SK'); }
    catch (e) { return String(n); }
  }

  function animateCount(el) {
    var target = parseFloat(el.getAttribute('data-target'));
    if (isNaN(target)) return;
    var duration = parseInt(el.getAttribute('data-duration') || '1500', 10);
    var decimals = parseInt(el.getAttribute('data-decimals') || '0', 10);
    var locale = el.getAttribute('data-locale') || document.documentElement.lang || 'sk-SK';
    var startTime = performance.now();
    function tick(now) {
      var t = Math.min((now - startTime) / duration, 1);
      var eased = 1 - Math.pow(1 - t, 3); // ease-out cubic
      var value = target * eased;
      if (decimals > 0) {
        el.textContent = format(value, locale).split(/[.,]/)[0] +
          (locale.indexOf('sk') === 0 ? ',' : '.') +
          value.toFixed(decimals).split('.')[1];
      } else {
        el.textContent = format(Math.round(value), locale);
      }
      if (t < 1) requestAnimationFrame(tick);
      else el.textContent = decimals > 0
        ? target.toFixed(decimals).replace('.', locale.indexOf('sk') === 0 ? ',' : '.')
        : format(target, locale);
    }
    requestAnimationFrame(tick);
  }

  var counters = document.querySelectorAll('[data-target]');
  if (counters.length) {
    if (reduced || !('IntersectionObserver' in window)) {
      counters.forEach(function(el){
        var t = parseFloat(el.getAttribute('data-target'));
        var d = parseInt(el.getAttribute('data-decimals') || '0', 10);
        var loc = el.getAttribute('data-locale') || document.documentElement.lang || 'sk-SK';
        el.textContent = d > 0 ? t.toFixed(d).replace('.', loc.indexOf('sk') === 0 ? ',' : '.') : format(t, loc);
      });
    } else {
      var counterObs = new IntersectionObserver(function(entries){
        entries.forEach(function(entry){
          if (entry.isIntersecting && !entry.target.dataset.counted) {
            entry.target.dataset.counted = '1';
            animateCount(entry.target);
            counterObs.unobserve(entry.target);
          }
        });
      }, { threshold: 0.35 });
      counters.forEach(function(el){ counterObs.observe(el); });
    }
  }
})();
