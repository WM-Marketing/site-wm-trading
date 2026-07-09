/* ==========================================================================
   WM Trading — utm-tracking.js
   Persistência de origem de tráfego (UTMs, gclid/msclkid/fbclid, referrer,
   página de entrada e GA4 client id) para atribuição campanha → lead.
   - Primeiro toque: gravado uma única vez (localStorage), nunca sobrescrito.
   - Último toque: atualizado sempre que a visita chega com UTM/click id.
   - window.wmTracking.getFields() devolve os campos prontos para anexar ao
     payload dos formulários (contact-form.js e whatsapp-popup.js).
   ========================================================================== */

(function () {
  'use strict';

  var KEY = 'wm_tracking';
  var PARAMS = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term',
    'utm_content', 'gclid', 'msclkid', 'fbclid'];

  function read() {
    try { return JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) { return {}; }
  }

  function save(d) {
    try { localStorage.setItem(KEY, JSON.stringify(d)); } catch (e) { /* modo privado */ }
  }

  function capture() {
    var q;
    try { q = new URLSearchParams(window.location.search); } catch (e) { return; }
    var d = read();
    var current = {};
    var hasParam = false;
    PARAMS.forEach(function (p) {
      var v = q.get(p);
      if (v) { current[p] = v; hasParam = true; }
    });

    if (!d.first) {
      d.first = {
        pagina_entrada: window.location.pathname,
        referrer: document.referrer || '',
        em: new Date().toISOString()
      };
      PARAMS.forEach(function (p) { if (current[p]) d.first[p] = current[p]; });
      save(d);
    }
    if (hasParam) {
      d.last = { em: new Date().toISOString() };
      PARAMS.forEach(function (p) { if (current[p]) d.last[p] = current[p]; });
      save(d);
    }
  }

  function gaClientId() {
    var m = document.cookie.match(/_ga=GA\d+\.\d+\.(\d+\.\d+)/);
    return m ? m[1] : '';
  }

  function getFields() {
    var d = read();
    var f = d.first || {};
    var l = d.last || {};
    var out = {};
    // último toque com fallback para o primeiro (o Zap mapeia utm_source → Campanha)
    PARAMS.forEach(function (p) {
      var v = l[p] || f[p];
      if (v) out[p] = v;
    });
    if (f.utm_source) out.utm_source_inicial = f.utm_source;
    if (f.utm_campaign) out.utm_campaign_inicial = f.utm_campaign;
    if (f.referrer) out.referrer_inicial = f.referrer;
    if (f.pagina_entrada) out.pagina_entrada = f.pagina_entrada;
    var cid = gaClientId();
    if (cid) out.clientid = cid;
    return out;
  }

  capture();
  window.wmTracking = { getFields: getFields };
})();
