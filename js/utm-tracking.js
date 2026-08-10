/* ==========================================================================
   WM Trading — utm-tracking.js
   Persistência de origem de tráfego (UTMs, gclid/msclkid/fbclid, referrer,
   página de entrada e GA4 client id) para atribuição campanha → lead.
   - Primeiro toque: gravado uma única vez, nunca sobrescrito.
   - Último toque: atualizado sempre que a visita chega com UTM/click id.
   - window.wmTracking.getFields() devolve os campos prontos para anexar ao
     payload dos formulários (contact-form.js e whatsapp-popup.js).

   LGPD: guardar a origem ENTRE visitas depende do aceite de cookies. Sem aceite,
   a origem vive só na sessão (sessionStorage) — o suficiente para identificar de
   onde veio um formulário que a própria pessoa está enviando agora, sem criar
   histórico persistente. Ao aceitar, consent.js chama persistir(); ao recusar ou
   revogar, chama esquecer(). O estado do consentimento é lido direto do
   localStorage porque este script roda antes de consent.js definir window.wmConsent.
   ========================================================================== */

(function () {
  'use strict';

  var KEY = 'wm_tracking';
  var CONSENT_KEY = 'wm_consent';
  var PARAMS = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term',
    'utm_content', 'gclid', 'msclkid', 'fbclid'];

  function consentimentoConcedido() {
    try {
      var c = JSON.parse(localStorage.getItem(CONSENT_KEY));
      return !!(c && c.status === 'granted');
    } catch (e) { return false; }
  }

  function destino() {
    return consentimentoConcedido() ? window.localStorage : window.sessionStorage;
  }

  function read() {
    try {
      var raw = localStorage.getItem(KEY) || sessionStorage.getItem(KEY);
      return JSON.parse(raw) || {};
    } catch (e) { return {}; }
  }

  function save(d) {
    try { destino().setItem(KEY, JSON.stringify(d)); } catch (e) { /* modo privado */ }
  }

  function persistir() {
    try {
      var d = read();
      if (Object.keys(d).length) localStorage.setItem(KEY, JSON.stringify(d));
      sessionStorage.removeItem(KEY);
    } catch (e) { /* modo privado */ }
  }

  function esquecer() {
    try {
      var d = read();
      localStorage.removeItem(KEY);
      if (Object.keys(d).length) sessionStorage.setItem(KEY, JSON.stringify(d));
    } catch (e) { /* modo privado */ }
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
  window.wmTracking = { getFields: getFields, persistir: persistir, esquecer: esquecer };
})();
