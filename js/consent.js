/* ==========================================================================
   WM Trading — consent.js
   Banner de consentimento LGPD + Google Consent Mode v2 + carregador do GTM.
   Centraliza TODO o tracking do site:
   - Nenhuma tag carrega antes do aceite (GTM bloqueado — GA4, pixels e webchat).
   - "Aceitar" => consent granted (Consent Mode v2) + GTM carrega.
   - "Recusar" => nada carrega; escolha lembrada; site funciona normalmente.
   - Escolha persistida por 180 dias (localStorage). Link no rodapé
     [data-wm-consent-prefs] reabre o banner para trocar a decisão.
   - Trava de domínio: GTM só carrega em wmtrading.com.br / www.wmtrading.com.br
     (homologação vercel.app não suja métricas; teste manual via localStorage
     wm_gtm_test=1). O banner aparece em qualquer domínio para validar a UX.
   Este arquivo substitui o antigo snippet inline do GTM no <head>.
   ========================================================================== */

(function () {
  'use strict';

  var GTM_ID = 'GTM-K58GFND';
  var KEY = 'wm_consent';
  var MAX_AGE_DAYS = 180;

  // Versão vigente das políticas (meta emitida pelo gerador). Quando ela muda,
  // quem aceitou a versão anterior volta a ver o aviso e decide de novo.
  function politicaVersao() {
    var m = document.querySelector('meta[name="wm-politica-versao"]');
    return (m && m.getAttribute('content')) || '';
  }

  var VERSAO = politicaVersao();

  // Texto exato do aviso — guardado junto com a escolha como registro do aceite.
  var TEXTO_AVISO = 'Usamos cookies para medir o desempenho do site, entender como você ' +
    'chegou até nós e melhorar sua experiência. Você pode aceitar ou recusar os cookies de ' +
    'análise e publicidade — os essenciais ao funcionamento permanecem ativos.';

  // ---- Consent Mode v2: default SEMPRE negado, antes de qualquer tag ----
  window.dataLayer = window.dataLayer || [];
  function gtag() { window.dataLayer.push(arguments); }
  gtag('consent', 'default', {
    ad_storage: 'denied',
    ad_user_data: 'denied',
    ad_personalization: 'denied',
    analytics_storage: 'denied',
    functionality_storage: 'granted', // essenciais ao funcionamento
    security_storage: 'granted',
    wait_for_update: 500
  });

  function readChoice() {
    try {
      var c = JSON.parse(localStorage.getItem(KEY));
      if (!c || !c.status || !c.em) return null;
      var ageDays = (Date.now() - new Date(c.em).getTime()) / 86400000;
      if (ageDays > MAX_AGE_DAYS) { localStorage.removeItem(KEY); return null; }
      // Política mudou desde o aceite: a escolha antiga não vale para o texto novo.
      if (VERSAO && c.versao !== VERSAO) { localStorage.removeItem(KEY); return null; }
      return c.status; // 'granted' | 'denied'
    } catch (e) { return null; }
  }

  function saveChoice(status) {
    var registro = {
      v: 2,
      status: status,
      em: new Date().toISOString(),
      versao: VERSAO,
      texto: TEXTO_AVISO
    };
    try {
      localStorage.setItem(KEY, JSON.stringify(registro));
    } catch (e) { /* modo privado */ }
    // Log da decisão para o GA4/GTM (auditoria da taxa de aceite e da revogação)
    window.dataLayer.push({
      event: 'consent_decision',
      consent_status: status,
      consent_versao: VERSAO,
      page: window.location.pathname
    });
  }

  function trackingAllowedHere() {
    var h = window.location.hostname;
    var test = null;
    try { test = localStorage.getItem('wm_gtm_test'); } catch (e) {}
    return h === 'www.wmtrading.com.br' || h === 'wmtrading.com.br' || !!test;
  }

  var gtmLoaded = false;
  function loadGtm() {
    if (gtmLoaded || !trackingAllowedHere()) return;
    gtmLoaded = true;
    (function (w, d, s, l, i) {
      w[l] = w[l] || [];
      w[l].push({ 'gtm.start': new Date().getTime(), event: 'gtm.js' });
      var f = d.getElementsByTagName(s)[0], j = d.createElement(s),
        dl = l !== 'dataLayer' ? '&l=' + l : '';
      j.async = true;
      j.src = 'https://www.googletagmanager.com/gtm.js?id=' + i + dl;
      f.parentNode.insertBefore(j, f);
    })(window, document, 'script', 'dataLayer', GTM_ID);
  }

  function grantConsent() {
    gtag('consent', 'update', {
      ad_storage: 'granted',
      ad_user_data: 'granted',
      ad_personalization: 'granted',
      analytics_storage: 'granted'
    });
    // Atribuição de origem passa a valer entre visitas (ver js/utm-tracking.js)
    if (window.wmTracking && window.wmTracking.persistir) window.wmTracking.persistir();
    loadGtm();
  }

  function denyConsent() {
    // Recusou: nenhuma tag carrega e a origem deixa de ser guardada entre visitas.
    if (window.wmTracking && window.wmTracking.esquecer) window.wmTracking.esquecer();
  }

  // ---------------------------- Banner ----------------------------

  var CSS = [
    '.wm-consent{position:fixed;left:0;right:0;bottom:0;z-index:9990;background:#1A1A1A;color:#fff;',
    'padding:18px 20px;box-shadow:0 -6px 24px rgba(0,0,0,.3);display:none;',
    'font-family:"Poppins",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;}',
    '.wm-consent.is-open{display:block;}',
    '.wm-consent__inner{max-width:1140px;margin:0 auto;display:flex;align-items:center;gap:24px;flex-wrap:wrap;}',
    '.wm-consent__text{flex:1 1 420px;font-size:13px;line-height:1.6;color:rgba(255,255,255,.85);margin:0;}',
    '.wm-consent__text a{color:#FC5000;text-decoration:underline;}',
    '.wm-consent__actions{display:flex;gap:12px;flex-wrap:wrap;}',
    '.wm-consent__btn{font:inherit;font-size:14px;font-weight:600;border-radius:8px;padding:12px 22px;',
    'cursor:pointer;transition:background .2s ease,color .2s ease;white-space:nowrap;}',
    '.wm-consent__btn--accept{background:#FC5000;border:1.5px solid #FC5000;color:#fff;}',
    '.wm-consent__btn--accept:hover{background:#E04700;border-color:#E04700;}',
    '.wm-consent__btn--reject{background:transparent;border:1.5px solid rgba(255,255,255,.45);color:#fff;}',
    '.wm-consent__btn--reject:hover{border-color:#fff;}',
    '@media(max-width:600px){.wm-consent{padding:16px;}.wm-consent__inner{gap:14px;}',
    '.wm-consent__actions{width:100%;}.wm-consent__btn{flex:1;text-align:center;padding:12px 10px;}}',
    '@media print{.wm-consent{display:none!important;}}'
  ].join('');

  var banner = null;

  function buildBanner() {
    if (banner) { banner.classList.add('is-open'); return; }
    var style = document.createElement('style');
    style.textContent = CSS;
    document.head.appendChild(style);

    banner = document.createElement('div');
    banner.className = 'wm-consent is-open';
    banner.setAttribute('role', 'dialog');
    banner.setAttribute('aria-label', 'Preferências de cookies');
    banner.innerHTML =
      '<div class="wm-consent__inner">' +
        '<p class="wm-consent__text">' + TEXTO_AVISO + ' ' +
        'Saiba mais na <a href="/politica-de-cookies.html">Política de Cookies</a> e na ' +
        '<a href="/politica-de-privacidade.html">Política de Privacidade</a>.</p>' +
        '<div class="wm-consent__actions">' +
          '<button type="button" class="wm-consent__btn wm-consent__btn--reject">Recusar não essenciais</button>' +
          '<button type="button" class="wm-consent__btn wm-consent__btn--accept">Aceitar todos</button>' +
        '</div>' +
      '</div>';
    document.body.appendChild(banner);

    banner.querySelector('.wm-consent__btn--accept').addEventListener('click', function () {
      saveChoice('granted');
      banner.classList.remove('is-open');
      grantConsent();
    });
    banner.querySelector('.wm-consent__btn--reject').addEventListener('click', function () {
      saveChoice('denied');
      banner.classList.remove('is-open');
      denyConsent();
    });
  }

  function openBanner() {
    if (document.body) { buildBanner(); }
    else { document.addEventListener('DOMContentLoaded', buildBanner); }
  }

  // Link "Preferências de cookies" (rodapé) reabre o banner
  document.addEventListener('click', function (e) {
    var link = e.target.closest && e.target.closest('[data-wm-consent-prefs]');
    if (!link) return;
    e.preventDefault();
    openBanner();
  });

  // ---------------------------- Fluxo ----------------------------

  var choice = readChoice();
  if (choice === 'granted') {
    grantConsent(); // GTM carrega já com consentimento concedido
  } else if (choice === null) {
    openBanner(); // primeira visita (ou política nova): nada carrega até decidir
  }
  // choice === 'denied': nada a fazer — nenhuma tag carrega

  window.wmConsent = {
    open: openBanner,
    reset: function () { try { localStorage.removeItem(KEY); } catch (e) {} openBanner(); },
    status: function () { return readChoice(); },
    versao: function () { return VERSAO; },
    // Registro do aceite, para consulta/depuração e atendimento a titulares
    registro: function () {
      try { return JSON.parse(localStorage.getItem(KEY)); } catch (e) { return null; }
    }
  };
})();
