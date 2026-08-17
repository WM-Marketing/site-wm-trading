/* ==========================================================================
   WM Trading — consent.js  (pos-migracao para o CMP AdOpt)

   O BANNER PROPRIO FOI APOSENTADO. Quem gerencia consentimento agora e o
   AdOpt: banner, painel granular ("Minhas opcoes"), Opt-out, registro de
   aceite e os sinais de Google Consent Mode v2.

   Sobrou para este arquivo o que o CMP nao faz:
     1. Classificar o ambiente e declarar `wm_ambiente` no dataLayer, antes
        de o GTM subir (routeamento de GA4 e bloqueio de pixel por ambiente).
     2. Carregar o GTM.
     3. Fazer a ponte com js/utm-tracking.js: a atribuicao de origem so pode
        ser guardada ENTRE visitas se houver consentimento (LGPD).
     4. Reemitir `consent_decision` no dataLayer, para nao perder a auditoria
        de taxa de aceite que o container ja consumia.

   POR QUE NAO USAMOS A API DO ADOPT
   ---------------------------------
   A ponte com o utm-tracking observa o **Google Consent Mode** no dataLayer,
   nao a API proprietaria do AdOpt. Consent Mode e contrato documentado do
   Google e qualquer CMP compativel emite `gtag('consent','update',...)`.
   Resultado: se um dia o CMP mudar (AdOpt -> Cookiebot -> outro), este
   arquivo continua funcionando sem uma linha alterada.

   ORDEM DE CARGA NO <head> — IMPORTA
   ----------------------------------
       <script src="/js/utm-tracking.js"></script>
       <script src="/js/consent.js"></script>          <-- 1o: default DENIED
       <script src="https://tag.adopt.com.br/....js"></script>  <-- 2o: o CMP

   Este arquivo declara `consent default: denied` ANTES de o AdOpt entrar.
   Isso e deliberado e e a diferenca entre falhar aberto e falhar fechado:
   se o AdOpt for bloqueado por adblock ou cair, o estado permanece negado e
   nenhuma tag de analytics/publicidade se considera autorizada. Chamar
   `default` duas vezes e inofensivo — o segundo nao afrouxa o primeiro, e os
   `update` do AdOpt continuam valendo normalmente.
   ========================================================================== */

(function () {
  'use strict';

  // Container EXCLUSIVO do site novo (conta GTM 6076388443, container 104495218).
  // O GTM-K58GFND ficou com o WordPress: ele serve os dois sites, e por isso
  // qualquer publicacao nele altera o site que esta no ar. Separar foi decisao
  // de 17/08/2026 — ver CLAUDE.md.
  var GTM_ID = 'GTM-52WHRQN';

  // ---- Ambiente ---------------------------------------------------------
  // Classifica onde a pagina esta rodando. Vai para o dataLayer ANTES do GTM
  // subir, entao ja esta disponivel como Variavel da Camada de Dados na
  // inicializacao do container — da para rotear GA4 por ambiente e barrar
  // pixels fora de producao sem tocar neste arquivo de novo.
  var PRODUCAO = ['www.wmtrading.com.br', 'wmtrading.com.br'];

  function detectarAmbiente() {
    var h = String(window.location.hostname || '').toLowerCase();
    if (PRODUCAO.indexOf(h) !== -1) return 'producao';
    if (h === 'localhost' || h === '127.0.0.1' || h === '::1' || h === '[::1]' ||
        /\.local$/.test(h) || /^192\.168\./.test(h) || /^10\./.test(h) ||
        /^172\.(1[6-9]|2\d|3[01])\./.test(h)) return 'local';
    if (/(^|\.)vercel\.app$/.test(h)) return 'homologacao';
    return 'desconhecido';
  }

  var AMBIENTE = detectarAmbiente();

  // Ambientes em que o GTM NAO deve carregar. Vazio = carrega em todos.
  // Ex.: para voltar a excluir homologacao, use ['homologacao'].
  var AMBIENTES_BLOQUEADOS = [];

  window.dataLayer = window.dataLayer || [];
  window.dataLayer.push({ wm_ambiente: AMBIENTE });

  // Residuos das versoes anteriores (banner proprio + flag de teste do GTM).
  // Limpar evita que um navegador antigo carregue estado que nao existe mais.
  try {
    localStorage.removeItem('wm_gtm_test');
    localStorage.removeItem('wm_consent');
  } catch (e) {}

  // ---- Consent Mode v2: fail-closed antes do CMP ------------------------
  function gtag() { window.dataLayer.push(arguments); }
  gtag('consent', 'default', {
    ad_storage: 'denied',
    ad_user_data: 'denied',
    ad_personalization: 'denied',
    analytics_storage: 'denied',
    functionality_storage: 'granted', // essenciais ao funcionamento
    security_storage: 'granted',
    wait_for_update: 2000            // margem para o CMP de terceiro responder
  });

  // ---- Ponte com o utm-tracking.js --------------------------------------
  // Guardar a origem ENTRE visitas depende de consentimento. Sem ele, o
  // utm-tracking mantem a origem apenas na sessao (sessionStorage), o que
  // basta para identificar de onde veio o formulario que a pessoa esta
  // enviando agora, sem criar historico persistente.
  var ultimoEstado = null;

  function aplicarConsentimento(sinais) {
    var analytics = sinais.analytics_storage;
    if (analytics !== 'granted' && analytics !== 'denied') return;
    if (analytics === ultimoEstado) return;   // ignora update repetido
    ultimoEstado = analytics;

    if (analytics === 'granted') {
      if (window.wmTracking && window.wmTracking.persistir) window.wmTracking.persistir();
    } else {
      if (window.wmTracking && window.wmTracking.esquecer) window.wmTracking.esquecer();
    }

    // Auditoria da taxa de aceite/revogacao — o container ja consumia este
    // evento quando o banner era proprio; segue existindo com o CMP.
    window.dataLayer.push({
      event: 'consent_decision',
      consent_status: analytics,
      consent_cmp: 'adopt',
      page: window.location.pathname
    });
  }

  // Observa os comandos de Consent Mode que passarem pelo dataLayer. Instalado
  // ANTES do GTM: quando o GTM embrulhar o push por cima, este wrapper continua
  // na cadeia e segue recebendo os updates do CMP.
  (function observarConsentMode() {
    var pushOriginal = window.dataLayer.push;
    window.dataLayer.push = function () {
      var retorno = pushOriginal.apply(window.dataLayer, arguments);
      try {
        for (var i = 0; i < arguments.length; i++) {
          var a = arguments[i];
          if (a && a[0] === 'consent' && a[1] === 'update' && a[2]) {
            aplicarConsentimento(a[2]);
          }
        }
      } catch (e) { /* nunca deixar a observacao quebrar o dataLayer */ }
      return retorno;
    };
  })();

  // ---- GTM --------------------------------------------------------------
  var gtmLoaded = false;

  function trackingAllowedHere() {
    return AMBIENTES_BLOQUEADOS.indexOf(AMBIENTE) === -1;
  }

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

  // O GTM sobe sempre. O bloqueio de tag antes do aceite passou a ser
  // responsabilidade do CMP + Consent Settings de cada tag no container.
  loadGtm();

  // ---- Link "Preferencias de cookies" no rodape -------------------------
  // O rodape tem [data-wm-consent-prefs] (unico href="#" legitimo do site,
  // conforme scripts/verificar.py). Antes ele reabria o banner proprio; agora
  // precisa reabrir o painel do AdOpt.
  //
  // >>> AJUSTAR AO CONFIRMAR A DOCUMENTACAO DO ADOPT <<<
  // O AdOpt aciona o painel por funcao global ou por classe/atributo no
  // elemento. As tentativas abaixo cobrem os padroes usuais; se nenhuma
  // existir, o link nao da clique morto — leva para a Politica de Cookies.
  function abrirPreferenciasCMP() {
    var candidatos = [
      function () { return window.adoptOpenPreferences; },
      function () { return window.adopt && window.adopt.openPreferences; },
      function () { return window.AdOpt && window.AdOpt.openPreferences; }
    ];
    for (var i = 0; i < candidatos.length; i++) {
      var fn;
      try { fn = candidatos[i](); } catch (e) { fn = null; }
      if (typeof fn === 'function') { fn(); return true; }
    }
    return false;
  }

  document.addEventListener('click', function (e) {
    var link = e.target.closest && e.target.closest('[data-wm-consent-prefs]');
    if (!link) return;
    e.preventDefault();
    if (!abrirPreferenciasCMP()) {
      window.location.href = '/politica-de-cookies/';
    }
  });

  // ---- API de depuracao -------------------------------------------------
  window.wmConsent = {
    ambiente: function () { return AMBIENTE; },
    gtmLiberado: function () { return trackingAllowedHere(); },
    gtmCarregado: function () { return gtmLoaded; },
    // Ultimo estado de analytics_storage visto vindo do CMP:
    // 'granted' | 'denied' | null (CMP ainda nao respondeu)
    consentimento: function () { return ultimoEstado; },
    abrirPreferencias: abrirPreferenciasCMP,
    cmp: 'adopt'
  };
})();
