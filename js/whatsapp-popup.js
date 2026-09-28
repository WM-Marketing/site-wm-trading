/* ==========================================================================
   WM Trading — whatsapp-popup.js
   Botão flutuante global + popup de captura antes de abrir o WhatsApp
   (réplica do comportamento do popup Elementor do site antigo).
   Autocontido: injeta o próprio CSS e HTML; nenhuma dependência externa.
   Envia o lead para /api/contato (formulario="whatsapp") e só então abre
   a conversa em wa.me. Também intercepta links diretos para wa.me já
   existentes nas páginas, garantindo a captura antes da conversa.
   ========================================================================== */

(function () {
  'use strict';

  /* CARIMBO DE TEMPO — o /api/contato/ recusa envio sem ele desde 31/08/2026.
     Este popup monta o proprio formulario e faz o proprio fetch, entao NAO passa
     pelo js/contact-form.js e precisa carimbar por conta propria. */
  var CARREGADA_EM = Date.now();

  var WA_NUMBER = '5527981610055'; // WhatsApp oficial (confirmado Renato 09/07); o fixo (27) 3022-9700 é só telefone
  var DEFAULT_WA_URL = 'https://wa.me/' + WA_NUMBER;

  /* IDIOMA — pela tag <html lang>. So "en*" troca os textos; qualquer outra
     coisa (pt-BR, vazio) fica exatamente como era antes de 28/09/2026. Quem
     pediu foi a LP /sell-in-brazil/ (QR do cartao da China), mas vale para
     todas as paginas /en/, que tambem declaram lang="en". */
  var LANG = /^en/i.test(document.documentElement.lang || '') ? 'en' : 'pt';

  var TEXTOS = {
    pt: {
      fab: 'Falar com a WM no WhatsApp',
      dialogo: 'Falar com a WM no WhatsApp',
      fechar: 'Fechar',
      titulo: 'Fale com a WM no WhatsApp',
      subtitulo: 'Preencha os dados abaixo e inicie agora a conversa com um dos nossos especialistas.',
      nome: 'Nome *',
      email: 'E-mail *',
      telefone: 'Telefone * — (DDD) 99999-0000',
      telefoneDica: null,
      politica: '/politica-de-privacidade/',
      aceite: 'Li e estou de acordo com a <a href="{politica}" target="_blank" rel="noopener">Pol&iacute;tica de Privacidade</a> e autorizo a WM Trading a tratar meus dados para responder a este contato.',
      aceiteMarketing: 'Tamb&eacute;m quero receber conte&uacute;dos e comunica&ccedil;&otilde;es comerciais da WM Trading (opcional).',
      botao: 'WhatsApp',
      enviando: 'Enviando...',
      tentarDeNovo: 'Tentar novamente',
      erro: 'Não foi possível enviar seus dados. Tente novamente ou <a href="{url}" target="_blank" rel="noopener">abra o WhatsApp diretamente</a>.',
      sucessoTitulo: 'Dados enviados! ✅',
      sucessoTexto: 'Clique no botão abaixo caso a conversa não tenha aberto automaticamente.',
      abrir: 'Abrir WhatsApp',
      mensagem: 'Olá! Sou {nome}. Vim pelo site da WM Trading e gostaria de falar com um especialista.',
      /* Em PT a validacao continua a do navegador — nada muda. */
      validacao: null
    },
    en: {
      fab: 'Talk to WM on WhatsApp',
      dialogo: 'Talk to WM on WhatsApp',
      fechar: 'Close',
      titulo: 'Talk to WM on WhatsApp',
      subtitulo: 'Fill in your details below to start a conversation with one of our specialists.',
      nome: 'Name *',
      email: 'Email *',
      /* O texto aprovado inteiro nao cabe no placeholder (cortava ate no
         desktop): o exemplo vai numa linha propria, logo abaixo do campo. */
      telefone: 'Phone * (with country code)',
      telefoneDica: 'e.g. +1 555 000 0000',
      politica: '/en/privacy-policy/',
      aceite: 'I have read and agree to the <a href="{politica}" target="_blank" rel="noopener">Privacy Policy</a> and authorize WM Trading to process my data to respond to this request.',
      aceiteMarketing: 'I also want to receive content and commercial communications from WM Trading (optional).',
      botao: 'Open WhatsApp',
      enviando: 'Sending...',
      tentarDeNovo: 'Try again',
      erro: 'We couldn’t send your details. Please try again or <a href="{url}" target="_blank" rel="noopener">open WhatsApp directly</a>.',
      sucessoTitulo: 'Details sent! ✅',
      sucessoTexto: 'If the chat didn’t open automatically, click the button below.',
      abrir: 'Open WhatsApp',
      mensagem: 'Hello! I’m {nome}. I found WM Trading’s website and I want to bring my products to the Brazilian market.',
      /* A mensagem nativa do navegador sai no idioma do SISTEMA do visitante
         (chines, no caso do cartao), nao no da pagina. Por isso em EN elas
         sao escritas aqui. */
      validacao: {
        nome: 'Please enter your name.',
        email: 'Please enter a valid email address.',
        telefone: 'Please enter a valid phone number with country code (8 to 15 digits).',
        aceite_privacidade: 'Please accept the Privacy Policy to continue.'
      }
    }
  };
  var T = TEXTOS[LANG];

  var CSS = [
    // bottom deixa espaço para o webchat Botmaker (via GTM), que ocupa o canto inferior direito
    '.wm-wa-fab{position:fixed;bottom:104px;right:24px;width:60px;height:60px;border-radius:50%;',
    'background:#25D366;border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;',
    'box-shadow:0 6px 20px rgba(0,0,0,.25);z-index:990;transition:transform .2s ease,box-shadow .2s ease;padding:0;}',
    '.wm-wa-fab:hover{transform:scale(1.07);box-shadow:0 8px 24px rgba(0,0,0,.3);}',
    '.wm-wa-fab svg{width:32px;height:32px;fill:#fff;display:block;}',
    '.wm-wa-overlay{position:fixed;inset:0;background:rgba(26,26,26,.55);z-index:10000;display:none;',
    'align-items:center;justify-content:center;padding:16px;}',
    '.wm-wa-overlay.is-open{display:flex;}',
    '.wm-wa-modal{background:#fff;border-radius:16px;max-width:400px;width:100%;padding:28px;position:relative;',
    'box-shadow:0 20px 60px rgba(0,0,0,.3);max-height:90vh;overflow-y:auto;',
    'font-family:"Poppins",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;}',
    '.wm-wa-close{position:absolute;top:10px;right:14px;background:none;border:none;font-size:26px;line-height:1;',
    'color:#888;cursor:pointer;padding:4px;}',
    '.wm-wa-close:hover{color:#3A3A3A;}',
    '.wm-wa-title{display:flex;align-items:center;gap:10px;font-size:18px;font-weight:600;color:#1A1A1A;margin:0 0 6px;}',
    '.wm-wa-title svg{width:26px;height:26px;fill:#25D366;flex-shrink:0;}',
    '.wm-wa-subtitle{font-size:13px;color:#888;margin:0 0 18px;line-height:1.5;}',
    '.wm-wa-form input[type=text],.wm-wa-form input[type=email],.wm-wa-form input[type=tel]{width:100%;',
    'padding:12px 14px;border:1px solid #ddd;border-radius:8px;margin-bottom:12px;font:inherit;font-size:14px;',
    'color:#3A3A3A;background:#fff;box-sizing:border-box;}',
    '.wm-wa-form input:focus{outline:none;border-color:var(--color-primary,#FC5000);}',
    '.wm-wa-hint{font-size:12px;color:#888;margin:-8px 0 12px;line-height:1.4;}',
    '.wm-wa-consent{display:flex;align-items:flex-start;gap:8px;font-size:12px;color:#888;margin:2px 0 16px;',
    'line-height:1.5;cursor:pointer;}',
    '.wm-wa-consent input{margin-top:2px;flex-shrink:0;}',
    '.wm-wa-consent a{color:var(--color-primary,#FC5000);text-decoration:underline;}',
    '.wm-wa-submit{width:100%;display:flex;align-items:center;justify-content:center;gap:10px;background:#25D366;',
    'color:#fff;border:none;border-radius:8px;padding:14px;font:inherit;font-size:15px;font-weight:600;',
    'cursor:pointer;transition:background .2s ease;}',
    '.wm-wa-submit:hover{background:#1EBE5D;}',
    '.wm-wa-submit:disabled{opacity:.65;cursor:wait;}',
    '.wm-wa-submit svg{width:20px;height:20px;fill:#fff;}',
    '.wm-wa-error{display:none;font-size:13px;color:#c0392b;margin:10px 0 0;line-height:1.5;}',
    '.wm-wa-error a{color:#c0392b;font-weight:600;}',
    '.wm-wa-success{text-align:center;padding:10px 0;}',
    '.wm-wa-success h3{font-size:17px;font-weight:600;color:#1A1A1A;margin:0 0 8px;}',
    '.wm-wa-success p{font-size:13px;color:#888;margin:0 0 18px;line-height:1.5;}',
    '.wm-wa-success a.wm-wa-open{display:inline-flex;align-items:center;justify-content:center;gap:10px;',
    'background:#25D366;color:#fff;border-radius:8px;padding:14px 24px;font-size:15px;font-weight:600;',
    'text-decoration:none;}',
    '.wm-wa-success a.wm-wa-open:hover{background:#1EBE5D;}',
    '.wm-wa-success a.wm-wa-open svg{width:20px;height:20px;fill:#fff;}',
    '@media(max-width:600px){.wm-wa-fab{bottom:94px;right:16px;width:54px;height:54px;}',
    '.wm-wa-fab svg{width:29px;height:29px;}.wm-wa-modal{padding:22px;}}',
    '@media print{.wm-wa-fab,.wm-wa-overlay{display:none!important;}}'
  ].join('');

  var WA_ICON = '<svg viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><path d="M16.04 3C9.02 3 3.32 8.7 3.32 15.72c0 2.24.59 4.43 1.7 6.36L3.2 29l7.09-1.86a12.66 12.66 0 0 0 5.75 1.39h.01c7.01 0 12.72-5.7 12.72-12.72 0-3.4-1.32-6.6-3.72-9A12.65 12.65 0 0 0 16.04 3zm0 23.38h-.01c-1.9 0-3.76-.51-5.38-1.47l-.39-.23-4.2 1.1 1.12-4.1-.25-.42a10.55 10.55 0 0 1-1.62-5.63c0-5.83 4.75-10.57 10.58-10.57 2.83 0 5.48 1.1 7.48 3.1a10.5 10.5 0 0 1 3.1 7.48c0 5.83-4.75 10.57-10.58 10.57zm5.8-7.92c-.32-.16-1.88-.93-2.17-1.03-.29-.11-.5-.16-.72.16-.21.32-.82 1.03-1 1.24-.19.21-.37.24-.69.08-.32-.16-1.34-.5-2.56-1.58-.95-.84-1.58-1.88-1.77-2.2-.19-.32-.02-.49.14-.65.14-.14.32-.37.48-.56.16-.19.21-.32.32-.53.11-.21.05-.4-.03-.56-.08-.16-.72-1.72-.98-2.36-.26-.62-.52-.53-.72-.54l-.61-.01c-.21 0-.56.08-.85.4-.29.32-1.12 1.09-1.12 2.65 0 1.56 1.14 3.07 1.3 3.28.16.21 2.25 3.44 5.45 4.82.76.33 1.36.53 1.82.67.77.24 1.46.21 2.01.13.61-.09 1.88-.77 2.15-1.51.26-.74.26-1.38.19-1.51-.08-.13-.29-.21-.61-.37z"/></svg>';

  var state = { targetUrl: DEFAULT_WA_URL, lastFocused: null };
  var overlay = null;
  var form = null;

  function injectCss() {
    var style = document.createElement('style');
    style.textContent = CSS;
    document.head.appendChild(style);
  }

  function buildFab() {
    // A LP da carne suína já tem botão flutuante próprio (.lp-whats) —
    // nesse caso só interceptamos o clique, sem duplicar o botão.
    if (document.querySelector('.lp-whats')) return;
    var fab = document.createElement('button');
    fab.type = 'button';
    fab.className = 'wm-wa-fab';
    fab.setAttribute('aria-label', T.fab);
    fab.innerHTML = WA_ICON;
    fab.addEventListener('click', function () { openPopup(DEFAULT_WA_URL); });
    document.body.appendChild(fab);
  }

  function buildOverlay() {
    if (overlay) overlay.remove();

    overlay = document.createElement('div');
    overlay.className = 'wm-wa-overlay';
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.setAttribute('aria-label', T.dialogo);
    overlay.innerHTML =
      '<div class="wm-wa-modal">' +
        '<button type="button" class="wm-wa-close" aria-label="' + T.fechar + '">&times;</button>' +
        '<h3 class="wm-wa-title">' + WA_ICON + T.titulo + '</h3>' +
        '<p class="wm-wa-subtitle">' + T.subtitulo + '</p>' +
        '<form class="wm-wa-form" novalidate>' +
          '<input type="text" name="_gotcha" tabindex="-1" autocomplete="off" aria-hidden="true" style="display:none;" />' +
          '<input type="text" name="nome" required placeholder="' + T.nome + '" autocomplete="name" />' +
          '<input type="email" name="email" required placeholder="' + T.email + '" autocomplete="email" />' +
          '<input type="tel" name="telefone" required placeholder="' + T.telefone + '" autocomplete="tel" maxlength="24" />' +
          (T.telefoneDica ? '<p class="wm-wa-hint">' + T.telefoneDica + '</p>' : '') +
          '<label class="wm-wa-consent">' +
            '<input type="checkbox" name="aceite_privacidade" required value="sim" />' +
            '<span data-wm-aceite>' + T.aceite.replace('{politica}', T.politica) + '</span>' +
          '</label>' +
          '<label class="wm-wa-consent">' +
            '<input type="checkbox" name="aceite_marketing" value="sim" />' +
            '<span>' + T.aceiteMarketing + '</span>' +
          '</label>' +
          '<button type="submit" class="wm-wa-submit">' + WA_ICON + T.botao + '</button>' +
          '<p class="wm-wa-error"></p>' +
        '</form>' +
      '</div>';
    document.body.appendChild(overlay);

    form = overlay.querySelector('.wm-wa-form');
    overlay.querySelector('.wm-wa-close').addEventListener('click', closePopup);
    overlay.addEventListener('click', function (e) { if (e.target === overlay) closePopup(); });
    form.querySelector('[name="telefone"]').addEventListener('input', LANG === 'en' ? cleanPhoneIntl : maskPhone);
    if (T.validacao) {
      // a mensagem propria so vale ate a pessoa mexer no campo de novo
      var limpa = function (e) { if (e.target.setCustomValidity) e.target.setCustomValidity(''); };
      form.addEventListener('input', limpa);
      form.addEventListener('change', limpa);
    }
    form.addEventListener('submit', onSubmit);
  }

  /* Corta no N-esimo digito preservando o que a pessoa digitou entre eles. */
  function cortaEmDigitos(texto, max) {
    var d = 0, out = '', i;
    for (i = 0; i < texto.length; i++) {
      if (/\d/.test(texto[i])) { if (d >= max) break; d++; }
      out += texto[i];
    }
    return out;
  }

  /* Quem comeca com + ou 00 esta informando o DDI, e a mascara brasileira NAO
     se aplica: ela lia o 55 do DDI como DDD e cortava no 11o digito, entao
     "+55 27 99999-0000" virava "(55) 27999-9900" — 11 digitos, formatado, e
     errado. Pior que vir incompleto: ninguem desconfia ao ver no CRM.
     O criterio do que e DDI e o mesmo do normalizaTelefone() no servidor. */
  function maskPhone(e) {
    var bruto = e.target.value;

    var digitos = bruto.replace(/\D/g, '');

    /* O "00" precisa ser detectado pelos DIGITOS: digitado caractere a
       caractere, no primeiro "0" o valor ainda e "0" e a mascara brasileira ja
       o viraria "(0" — dali em diante nada mais comecaria com "00". */
    if (/^00/.test(digitos)) {
      e.target.value = digitos.slice(0, 15);
      return;
    }
    if (/^\s*\+/.test(bruto)) {
      e.target.value = cortaEmDigitos(bruto.replace(/[^\d+\s().-]/g, ''), 15);
      return;
    }

    var d = digitos.slice(0, 11);
    var out = '';
    if (d.length > 0) out = '(' + d.slice(0, 2);
    if (d.length > 2) out += ') ' + (d.length === 11 ? d.slice(2, 7) : d.slice(2, 6));
    if (d.length === 11 && d.length > 7) out += '-' + d.slice(7);
    else if (d.length > 6 && d.length < 11) out += '-' + d.slice(6);
    e.target.value = out;
  }

  /* EN: publico estrangeiro, sem mascara brasileira. So limpa o que nao e
     digito, +, espaco, parenteses, ponto ou hifen e corta no 15o digito
     (teto do E.164) — mesmo tratamento do telefone do formulario da LP. */
  function cleanPhoneIntl(e) {
    e.target.value = cortaEmDigitos(e.target.value.replace(/[^\d+\s().-]/g, ''), 15);
  }

  /* So em EN. Marca cada campo com a mensagem em ingles antes do
     reportValidity(); em PT a funcao nem roda. */
  function applyValidationMessages() {
    var v = T.validacao;
    var nome = form.querySelector('[name="nome"]');
    var email = form.querySelector('[name="email"]');
    var tel = form.querySelector('[name="telefone"]');
    var aceite = form.querySelector('[name="aceite_privacidade"]');
    var digitos = tel.value.replace(/\D/g, '').length;

    nome.setCustomValidity(nome.value.trim() ? '' : v.nome);
    email.setCustomValidity(email.value.trim() && !email.validity.typeMismatch ? '' : v.email);
    tel.setCustomValidity(digitos >= 8 && digitos <= 15 ? '' : v.telefone);
    aceite.setCustomValidity(aceite.checked ? '' : v.aceite_privacidade);
  }

  function openPopup(targetUrl) {
    state.targetUrl = targetUrl || DEFAULT_WA_URL;
    state.lastFocused = document.activeElement;
    overlay.classList.add('is-open');
    document.body.style.overflow = 'hidden';
    var first = form && form.querySelector('[name="nome"]');
    if (first) first.focus();
  }

  function closePopup() {
    var wasSuccess = !overlay.querySelector('.wm-wa-form');
    overlay.classList.remove('is-open');
    document.body.style.overflow = '';
    if (state.lastFocused && state.lastFocused.focus) state.lastFocused.focus();
    if (wasSuccess) buildOverlay(); // próximo clique volta a mostrar o formulário limpo
  }

  function buildWaUrl(nome) {
    var msg = T.mensagem.replace('{nome}', nome);
    // PT: preserva ?text= do link original, se houver; senão usa a mensagem padrão.
    if (LANG !== 'en') {
      if (state.targetUrl.indexOf('text=') !== -1) return state.targetUrl;
      return state.targetUrl + (state.targetUrl.indexOf('?') === -1 ? '?' : '&') + 'text=' + encodeURIComponent(msg);
    }
    // EN: a mensagem com o nome substitui o ?text= do link. Hoje os unicos
    // links wa.me com texto em pagina lang="en" sao os da /sell-in-brazil/,
    // e a mensagem aprovada para eles e esta (28/09/2026).
    return DEFAULT_WA_URL + '?text=' + encodeURIComponent(msg);
  }

  function pushDataLayer(event, extra) {
    window.dataLayer = window.dataLayer || [];
    var data = { event: event, page: window.location.pathname };
    for (var k in extra) data[k] = extra[k];
    window.dataLayer.push(data);
  }

  function onSubmit(e) {
    e.preventDefault();
    if (T.validacao) applyValidationMessages();
    if (!form.reportValidity()) return;

    var gotcha = form.querySelector('[name="_gotcha"]');
    var nome = form.querySelector('[name="nome"]').value.trim();
    var waUrl = buildWaUrl(nome);

    if (gotcha && gotcha.value) { showSuccess(waUrl); return; } // bot: finge sucesso, não envia

    var btn = form.querySelector('.wm-wa-submit');
    var errorEl = form.querySelector('.wm-wa-error');
    btn.disabled = true;
    btn.innerHTML = T.enviando;
    errorEl.style.display = 'none';

    var aceiteEl = form.querySelector('[data-wm-aceite]');
    var versaoEl = document.querySelector('meta[name="wm-politica-versao"]');

    var payload = {
      nome: nome,
      email: form.querySelector('[name="email"]').value.trim(),
      telefone: form.querySelector('[name="telefone"]').value.trim(),
      formulario: 'whatsapp',
      url: window.location.href,
      origem: 'site wmtrading.com.br',
      // Registro de aceite (LGPD art. 8º, § 2º) — IP e user agent entram no servidor
      aceite_privacidade: form.querySelector('[name="aceite_privacidade"]:checked') ? 'sim' : 'nao',
      aceite_marketing: form.querySelector('[name="aceite_marketing"]:checked') ? 'sim' : 'nao',
      aceite_texto: aceiteEl ? aceiteEl.textContent.replace(/\s+/g, ' ').trim() : '',
      politica_versao: versaoEl ? versaoEl.getAttribute('content') : '',
      aceite_em: new Date().toISOString(),
      // Idioma do popup. O api/contato.js ainda NAO repassa este campo ao
      // Zapier (monta o payload com campos fixos): chega e e ignorado.
      idioma: LANG,
      // Milissegundos entre a pagina ficar pronta e o envio. Sem isto o
      // servidor descarta o lead achando que e robo — e responde ok, entao a
      // perda seria silenciosa.
      _ms: Date.now() - CARREGADA_EM
    };

    // Campos de atribuição (UTMs, gclid, GA client id — js/utm-tracking.js)
    // getFieldsAsync pergunta client_id/session_id ao proprio GA4 e espera o
    // callback, com timeout curto. A versao sincrona getFields() devolvia vazio
    // em visitante novo, quando o cookie _ga ainda nao existe — origem da string
    // "false" nos registros historicos. Nunca rejeita: se estourar o tempo, o
    // lead vai igual, com campo vazio e ga_status='timeout'.
    var atribuicao = (window.wmTracking && window.wmTracking.getFieldsAsync)
      ? window.wmTracking.getFieldsAsync()
      : Promise.resolve({});

    atribuicao
      .then(function (campos) {
        Object.assign(payload, campos);
        return fetch('/api/contato/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
      })
      .then(function (res) { return res.json().then(function (j) { return { ok: res.ok && j.ok }; }); })
      .then(function (r) {
        if (!r.ok) throw new Error('fail');
        pushDataLayer('wm_form_submit', { form_type: 'whatsapp' });
        pushDataLayer('whatsapp_click', {});
        window.open(waUrl, '_blank', 'noopener');
        // Mantém o modal com um botão-âncora: se o navegador bloquear o
        // window.open pós-fetch, o clique manual sempre funciona.
        showSuccess(waUrl);
      })
      .catch(function () {
        btn.disabled = false;
        btn.innerHTML = WA_ICON + T.tentarDeNovo;
        errorEl.innerHTML = T.erro.replace('{url}', waUrl);
        errorEl.style.display = 'block';
      });
  }

  function showSuccess(waUrl) {
    var modal = overlay.querySelector('.wm-wa-modal');
    modal.innerHTML =
      '<button type="button" class="wm-wa-close" aria-label="' + T.fechar + '">&times;</button>' +
      '<div class="wm-wa-success">' +
        '<h3>' + T.sucessoTitulo + '</h3>' +
        '<p>' + T.sucessoTexto + '</p>' +
        '<a class="wm-wa-open" href="' + waUrl + '" target="_blank" rel="noopener">' + WA_ICON + T.abrir + '</a>' +
      '</div>';
    form = null;
    modal.querySelector('.wm-wa-close').addEventListener('click', closePopup);
  }

  function interceptWaLinks() {
    document.addEventListener('click', function (e) {
      var link = e.target.closest && e.target.closest('a[href*="wa.me/"], a[href*="api.whatsapp.com/"]');
      if (!link) return;
      if (overlay && overlay.contains(link)) return; // links do próprio popup passam direto
      e.preventDefault();
      openPopup(link.href);
    });
  }

  function init() {
    injectCss();
    buildFab();
    buildOverlay();
    interceptWaLinks();
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && overlay && overlay.classList.contains('is-open')) closePopup();
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
