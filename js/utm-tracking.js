/* ==========================================================================
   WM Trading — utm-tracking.js
   Identidade do visitante + atribuicao de origem, para o join CRM x GA4.

   O QUE VAI PARA O FORMULARIO
   ---------------------------
     wm_vid         ID de primeira parte, gerado por nos. SEMPRE existe.
     clientid       client_id do GA4 (nome mantido: o Zap ja mapeia assim).
     ga_session_id  session_id do GA4 — permite join no grao de SESSAO.
     ga_status      por que clientid/session_id faltaram, quando faltarem.
     utm_*, gclid, msclkid, fbclid, referrer_inicial, pagina_entrada.

     paginas_vistas      trilha das ultimas 12 paginas ("/a/ > /b/ > ...").
     total_paginas       pageviews no total (conta tudo, mesmo o que a trilha cortou).
     total_sessoes       sessoes contadas com gap de 30 min, convencao do GA4.
     dias_ate_lead       dias entre a primeira visita e o envio do formulario.
     primeira_visita_em  ISO da primeira visita.

   POR QUE O wm_vid EXISTE
   -----------------------
   O client_id do GA4 e o cookie _ga. Ele falta em varios cenarios reais:
   bloqueador de anuncio, primeira visita antes do GA4 gravar o cookie, e
   consentimento negado (aí ele nao existe mesmo — o GA4 entra em cookieless
   ping, sem identificador persistente). O wm_vid nao depende de nada disso:
   e nosso, no nosso dominio, e serve como chave de join exata — sem truncar
   digito, sem heuristica de formato, sem risco de match falso.
   O wm_vid tambem vai ao dataLayer, para o GTM enviar como user property e
   ele aparecer no GA4 (e em user_properties no export do BigQuery).

   NUNCA GRAVAR "false"
   --------------------
   A tag antiga do GTM fazia `var clientId = {{Ga - clientid 2}}` sem aspas:
   quando o cookie nao existia, escrevia a string "false" no campo do
   formulario. Aqui, ausencia = string vazia + ga_status explicando o motivo.
   Perda silenciosa vira numero mensuravel.

   MOMENTO DA LEITURA
   ------------------
   Os IDs do GA4 sao lidos NO ENVIO do formulario, nao no page view. A tag
   antiga lia em All Pages, quando o cookie _ga ainda nao havia sido gravado
   em visitantes de primeira viagem — origem do "false" nos registros.

   LGPD
   ----
   Guardar identidade e origem ENTRE visitas depende de consentimento. Sem
   consentimento, wm_vid e origem vivem so na sessao (sessionStorage): basta
   para identificar o formulario que a pessoa esta enviando agora, sem criar
   historico persistente. Quem avisa este arquivo e o consent.js, chamando
   persistir() quando o CMP concede e esquecer() quando nega/revoga.
   ========================================================================== */

(function () {
  'use strict';

  var KEY = 'wm_tracking';
  var KEY_VID = 'wm_vid';
  var MEASUREMENT_ID = 'G-2ZYJ222PF0';
  var TIMEOUT_GA_MS = 800;

  var PARAMS = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term',
    'utm_content', 'gclid', 'msclkid', 'fbclid'];

  // Estado de consentimento mantido em memoria. NAO ler de localStorage.wm_consent:
  // essa chave era do banner proprio e o CMP (AdOpt) a substituiu — ficaria sempre
  // falsa e prenderia tudo em sessionStorage. Quem atualiza e persistir()/esquecer(),
  // chamados pelo consent.js ao observar o Consent Mode.
  var consentido = false;
  try {
    // Se ja existe copia persistente de visita anterior, houve consentimento antes.
    consentido = !!(localStorage.getItem(KEY) || localStorage.getItem(KEY_VID));
  } catch (e) { consentido = false; }

  function destino() {
    return consentido ? window.localStorage : window.sessionStorage;
  }

  function lerChave(k) {
    try { return localStorage.getItem(k) || sessionStorage.getItem(k) || null; }
    catch (e) { return null; }
  }

  function read() {
    try { return JSON.parse(lerChave(KEY)) || {}; } catch (e) { return {}; }
  }

  function save(d) {
    try { destino().setItem(KEY, JSON.stringify(d)); } catch (e) { /* modo privado */ }
  }

  // ---- wm_vid ------------------------------------------------------------

  function novoUuid() {
    try {
      if (window.crypto && typeof window.crypto.randomUUID === 'function') {
        return window.crypto.randomUUID();
      }
      if (window.crypto && window.crypto.getRandomValues) {
        var b = new Uint8Array(16);
        window.crypto.getRandomValues(b);
        b[6] = (b[6] & 0x0f) | 0x40;             // versao 4
        b[8] = (b[8] & 0x3f) | 0x80;             // variante
        var h = [];
        for (var i = 0; i < 16; i++) h.push(('0' + b[i].toString(16)).slice(-2));
        return h.slice(0, 4).join('') + '-' + h.slice(4, 6).join('') + '-' +
               h.slice(6, 8).join('') + '-' + h.slice(8, 10).join('') + '-' +
               h.slice(10, 16).join('');
      }
    } catch (e) { /* cai no fallback */ }
    // Fallback sem crypto: menos entropia, mas nunca devolve vazio.
    return 'f-' + Date.now().toString(36) + '-' +
           Math.random().toString(36).slice(2, 10) +
           Math.random().toString(36).slice(2, 10);
  }

  function garantirVid() {
    var v = lerChave(KEY_VID);
    if (v && v.length >= 8) return v;
    v = novoUuid();
    try { destino().setItem(KEY_VID, v); } catch (e) { /* modo privado */ }
    return v;
  }

  var VID = garantirVid();

  // Declara o wm_vid no dataLayer ANTES do GTM subir (este arquivo carrega antes
  // do consent.js). O GTM le como Variavel da Camada de Dados e envia como user
  // property para o GA4 — e assim ele aparece em user_properties no BigQuery.
  window.dataLayer = window.dataLayer || [];
  window.dataLayer.push({ wm_vid: VID });

  // ---- consentimento (chamado pelo consent.js) ---------------------------

  function persistir() {
    consentido = true;
    try {
      var d = read();
      if (Object.keys(d).length) localStorage.setItem(KEY, JSON.stringify(d));
      var v = lerChave(KEY_VID);
      if (v) localStorage.setItem(KEY_VID, v);
      sessionStorage.removeItem(KEY);
      sessionStorage.removeItem(KEY_VID);
    } catch (e) { /* modo privado */ }
  }

  function esquecer() {
    consentido = false;
    try {
      var d = read();
      var v = lerChave(KEY_VID);
      localStorage.removeItem(KEY);
      localStorage.removeItem(KEY_VID);
      // Mantem na sessao: o formulario que a pessoa esta preenchendo agora
      // continua identificavel, mas nada sobrevive ao fechar a aba.
      if (Object.keys(d).length) sessionStorage.setItem(KEY, JSON.stringify(d));
      if (v) sessionStorage.setItem(KEY_VID, v);
    } catch (e) { /* modo privado */ }
  }

  // ---- captura de origem -------------------------------------------------

  function capture() {
    var q;
    try { q = new URLSearchParams(window.location.search); } catch (e) { q = null; }
    var d = read();
    var current = {};
    var hasParam = false;
    if (q) {
      PARAMS.forEach(function (p) {
        var v = q.get(p);
        if (v) { current[p] = v; hasParam = true; }
      });
    }

    if (!d.first) {
      d.first = {
        pagina_entrada: window.location.pathname,
        referrer: document.referrer || '',
        em: new Date().toISOString()
      };
      PARAMS.forEach(function (p) { if (current[p]) d.first[p] = current[p]; });
    }
    if (hasParam) {
      d.last = { em: new Date().toISOString() };
      PARAMS.forEach(function (p) { if (current[p]) d.last[p] = current[p]; });
    }

    registrarJornada(d);
    save(d);
  }

  // ---- jornada -----------------------------------------------------------
  // Trilha de navegacao acumulada no proprio navegador e enviada junto com o
  // lead. Responde "o que este cliente olhou antes de pedir contato" SEM
  // depender de GA4, BigQuery ou join: o dado nasce e chega no mesmo lugar,
  // dentro do negocio no Pipedrive, onde o comercial vai de fato olhar.
  // O GA4 continua necessario para o agregado e para quem NAO converteu.
  var MAX_PAGINAS = 12;        // ultimas N na trilha (contadores seguem somando tudo)
  var MAX_CHARS_TRILHA = 900;  // teto do campo, para nao estourar Pipedrive/Zapier
  var GAP_SESSAO_MS = 30 * 60 * 1000; // 30 min: mesma convencao do GA4

  function registrarJornada(d) {
    var agora = Date.now();
    var j = d.jornada;
    if (!j || typeof j !== 'object') {
      j = d.jornada = { paginas: [], total: 0, sessoes: 0, ultimo_em: 0 };
    }
    if (!Array.isArray(j.paginas)) j.paginas = [];

    // Nova sessao quando passaram mais de 30 min desde o ultimo pageview.
    if (!j.ultimo_em || (agora - j.ultimo_em) > GAP_SESSAO_MS) j.sessoes = (j.sessoes || 0) + 1;
    j.ultimo_em = agora;
    j.total = (j.total || 0) + 1;

    // Nao repete pagina consecutiva: F5 e recarregamento nao poluem a trilha.
    // Revisita nao-consecutiva SIM entra — voltar duas vezes na mesma pagina
    // e justamente o sinal de interesse que o comercial quer ver.
    var p = window.location.pathname || '/';
    if (j.paginas[j.paginas.length - 1] !== p) j.paginas.push(p);
    if (j.paginas.length > MAX_PAGINAS) j.paginas = j.paginas.slice(-MAX_PAGINAS);
  }

  function trilhaLegivel(j) {
    if (!j || !j.paginas || !j.paginas.length) return '';
    var lista = j.paginas.slice();
    var s = lista.join(' > ');
    var truncou = false;
    while (s.length > MAX_CHARS_TRILHA && lista.length > 1) {
      lista.shift();
      truncou = true;
      s = lista.join(' > ');
    }
    // Marca que houve corte, para ninguem ler a trilha como se fosse completa.
    if (truncou || (j.total || 0) > j.paginas.length) s = '... > ' + s;
    return s.slice(0, MAX_CHARS_TRILHA);
  }

  function camposJornada(d) {
    var out = {};
    var j = d.jornada;
    var f = d.first || {};
    if (j) {
      var t = trilhaLegivel(j);
      if (t) out.paginas_vistas = t;
      out.total_paginas = String(j.total || 0);
      out.total_sessoes = String(j.sessoes || 0);
    }
    if (f.em) {
      out.primeira_visita_em = f.em;
      var ms = Date.now() - new Date(f.em).getTime();
      out.dias_ate_lead = String(ms > 0 ? Math.floor(ms / 86400000) : 0);
    }
    return out;
  }

  // ---- IDs do GA4 --------------------------------------------------------

  function gaClientIdDoCookie() {
    var m = document.cookie.match(/_ga=GA\d+\.\d+\.(\d+\.\d+)/);
    return m ? m[1] : '';
  }

  function consentimentoDoCmp() {
    try {
      if (window.wmConsent && typeof window.wmConsent.consentimento === 'function') {
        return window.wmConsent.consentimento(); // 'granted' | 'denied' | null
      }
    } catch (e) {}
    return null;
  }

  var cacheGa = null; // { client_id, session_id, status }

  /* Decide o ga_status por PRIORIDADE de utilidade para o BI, e nao pela ordem
     em que a falha foi detectada:
       1. conseguiu o ID          -> ok | ok_cookie
       2. consentimento negado    -> sem_consentimento  (perda esperada, nao e defeito)
       3. motivo tecnico          -> sem_gtag | timeout | erro_gtag
       4. resto                   -> sem_cookie
     A recusa vem antes do motivo tecnico de proposito: quando o CMP nega, o GA4
     nem chega a existir na pagina, e reportar "sem_gtag" esconderia a causa real. */
  function classificar(temId, viaCookie, motivoTecnico) {
    if (temId) return viaCookie ? 'ok_cookie' : 'ok';
    if (consentimentoDoCmp() === 'denied') return 'sem_consentimento';
    if (motivoTecnico) return motivoTecnico;
    return 'sem_cookie';
  }

  function pedirGa4(timeoutMs) {
    return new Promise(function (resolve) {
      var res = { client_id: '', session_id: '', status: '' };

      function fechar(motivoTecnico) {
        var viaCookie = false;
        if (!res.client_id) {
          // Fallback: o gtag pode nao responder mas o cookie existir.
          var doCookie = gaClientIdDoCookie();
          if (doCookie) { res.client_id = doCookie; viaCookie = true; }
        }
        res.status = classificar(!!res.client_id, viaCookie, motivoTecnico);
        resolve(res);
      }

      if (typeof window.gtag !== 'function') {
        // GA4 nao esta na pagina: bloqueador, ou ambiente sem GTM.
        return fechar('sem_gtag');
      }

      var pendentes = 2, encerrado = false;
      var t = setTimeout(function () {
        if (encerrado) return;
        encerrado = true;
        fechar('timeout');
      }, timeoutMs || TIMEOUT_GA_MS);

      function recebeu() {
        if (encerrado) return;
        if (--pendentes > 0) return;
        encerrado = true;
        clearTimeout(t);
        fechar('');
      }

      try {
        window.gtag('get', MEASUREMENT_ID, 'client_id', function (v) {
          if (v) res.client_id = String(v);
          recebeu();
        });
        window.gtag('get', MEASUREMENT_ID, 'session_id', function (v) {
          if (v) res.session_id = String(v);
          recebeu();
        });
      } catch (e) {
        if (!encerrado) { encerrado = true; clearTimeout(t); fechar('erro_gtag'); }
      }
    });
  }

  // Tenta resolver os IDs cedo e guardar em cache, para o envio do formulario
  // nao pagar a espera. Repete uma vez, porque o GA4 pode subir depois do
  // aceite no CMP e so entao o cookie passa a existir.
  function aquecer() {
    pedirGa4(TIMEOUT_GA_MS).then(function (r) {
      if (r.client_id) cacheGa = r;
    });
  }
  setTimeout(aquecer, 1500);
  setTimeout(aquecer, 6000);

  // ---- saida para os formularios ----------------------------------------

  function camposBase() {
    var d = read();
    var f = d.first || {};
    var l = d.last || {};
    var out = {};
    // ultimo toque com fallback para o primeiro (o Zap mapeia utm_source → Campanha)
    PARAMS.forEach(function (p) {
      var v = l[p] || f[p];
      if (v) out[p] = v;
    });
    if (f.utm_source) out.utm_source_inicial = f.utm_source;
    if (f.utm_campaign) out.utm_campaign_inicial = f.utm_campaign;
    if (f.referrer) out.referrer_inicial = f.referrer;
    if (f.pagina_entrada) out.pagina_entrada = f.pagina_entrada;
    out.wm_vid = VID;
    var jn = camposJornada(d);
    for (var k in jn) { if (Object.prototype.hasOwnProperty.call(jn, k)) out[k] = jn[k]; }
    return out;
  }

  /* Versao sincrona — mantida por compatibilidade. Usa apenas o cookie, entao
     pode devolver clientid vazio em cenarios em que a assincrona acharia.
     Prefira getFieldsAsync() nos formularios. */
  function getFields() {
    var out = camposBase();
    var doCache = cacheGa && cacheGa.client_id;
    var cid = doCache || gaClientIdDoCookie();
    out.clientid = cid || '';
    if (cacheGa && cacheGa.session_id) out.ga_session_id = cacheGa.session_id;
    out.ga_status = doCache ? cacheGa.status
                           : classificar(!!cid, true, typeof window.gtag !== 'function' ? 'sem_gtag' : '');
    return out;
  }

  /* Versao recomendada: pergunta os IDs ao proprio GA4, com timeout curto.
     Resolve SEMPRE — nunca rejeita, para nunca bloquear o envio do lead. */
  function getFieldsAsync(timeoutMs) {
    var out = camposBase();
    if (cacheGa && cacheGa.client_id) {
      out.clientid = cacheGa.client_id;
      if (cacheGa.session_id) out.ga_session_id = cacheGa.session_id;
      out.ga_status = cacheGa.status;
      return Promise.resolve(out);
    }
    return pedirGa4(timeoutMs || TIMEOUT_GA_MS).then(function (r) {
      if (r.client_id) cacheGa = r;
      out.clientid = r.client_id || '';
      if (r.session_id) out.ga_session_id = r.session_id;
      out.ga_status = r.status;
      return out;
    })['catch'](function () {
      out.clientid = '';
      out.ga_status = 'erro';
      return out;
    });
  }

  capture();

  window.wmTracking = {
    getFields: getFields,
    getFieldsAsync: getFieldsAsync,
    persistir: persistir,
    esquecer: esquecer,
    vid: function () { return VID; },
    // Depuracao no console: wmTracking.diagnostico()
    diagnostico: function () {
      return {
        wm_vid: VID,
        consentido: consentido,
        armazenamento: consentido ? 'localStorage' : 'sessionStorage',
        cacheGa: cacheGa,
        jornada: (read().jornada || null),
        cookie_ga: gaClientIdDoCookie() || '(ausente)',
        cmp: consentimentoDoCmp(),
        gtag: typeof window.gtag
      };
    }
  };
})();
