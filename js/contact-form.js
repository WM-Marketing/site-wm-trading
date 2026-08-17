/* ==========================================================================
   WM Trading — contact-form.js (Vanilla client-side form submissions)
   ========================================================================== */

(function() {
  'use strict';

  /* ---- Textos por idioma ----------------------------------------------------
     As paginas em /en/ declaram lang="en" no <html>. Sem isto, um visitante que
     preenche o formulario em ingles recebe "Mensagem enviada!" em portugues.
     O padrao continua sendo o portugues: so muda quando a pagina diz que e EN. */
  var EN = (document.documentElement.getAttribute('lang') || '').toLowerCase().indexOf('en') === 0;

  var T = EN ? {
    erroGenerico:  'Something went wrong. Please try again.',
    erroEnvio:     'We could not submit the form. Please try again.',
    sucessoTitulo: 'Message sent! ✅',
    sucessoTexto:  'We have received your message. A WM Trading specialist will contact you shortly.',
    ebookTitulo:   'Your material is ready! ✅',
    ebookTexto:    'The download of <strong>"{TITULO}"</strong> should start automatically.',
    ebookBotao:    'Download manually'
  } : {
    erroGenerico:  'Ocorreu um erro. Tente novamente.',
    erroEnvio:     'Não foi possível enviar o formulário. Tente novamente.',
    sucessoTitulo: 'Mensagem enviada! ✅',
    sucessoTexto:  'Recebemos o seu contato. Um especialista da WM falará com você em breve.',
    ebookTitulo:   'Material liberado! ✅',
    ebookTexto:    'O download do e-book <strong>"{TITULO}"</strong> deve começar automaticamente.',
    ebookBotao:    'Baixar e-book manualmente'
  };

  /* ---- Registro de aceite (LGPD art. 8º, § 2º — o ônus da prova é do controlador) ----
     Guardamos o QUE foi aceito, QUAL versão da política estava no ar e QUANDO.
     A versão vem da meta wm-politica-versao, emitida pelo gerador (build_pages.py).
     IP e user agent são acrescentados no servidor (api/contato.js). */
  function politicaVersao() {
    var m = document.querySelector('meta[name="wm-politica-versao"]');
    return (m && m.getAttribute('content')) || '';
  }

  function textoDoAceite(form) {
    var el = form.querySelector('[data-wm-aceite]');
    return el ? el.textContent.replace(/\s+/g, ' ').trim() : '';
  }

  function marcado(form, name) {
    return form.querySelector('[name="' + name + '"]:checked') ? 'sim' : 'nao';
  }

  // Intercept all submit events at document level
  document.addEventListener('submit', async function(e) {
    const form = e.target;
    
    // Check if it's a contact or ebook form
    if (!form.classList.contains('contact-form-js')) return;

    e.preventDefault();

    // Honeypot spam prevention check
    const gotcha = form.querySelector('[name="_gotcha"]');
    if (gotcha && gotcha.value) {
      showSuccess(form); // Falsely show success to bots, block actual request
      return;
    }

    const submitBtn = form.querySelector('[type="submit"]');
    const originalBtnText = submitBtn ? submitBtn.innerHTML : 'Enviar';
    
    // Set loading state
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = 'Enviando...';
    }

    // Hide any previous errors
    let errorMsgEl = form.querySelector('.form-error-msg');
    if (errorMsgEl) errorMsgEl.style.display = 'none';

    // Collect data
    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());
    
    // Add additional metadata
    payload.formulario = form.getAttribute('data-form-type') || 'contato';
    payload.url = window.location.href;
    payload.origem = 'site wmtrading.com.br';

    // Prova de consentimento — segue para o Pipedrive junto com o lead
    payload.aceite_privacidade = marcado(form, 'aceite_privacidade');
    payload.aceite_marketing = marcado(form, 'aceite_marketing');
    payload.aceite_texto = textoDoAceite(form);
    payload.politica_versao = politicaVersao();
    payload.aceite_em = new Date().toISOString();

    // Attribution fields (UTMs, gclid, GA client id — see js/utm-tracking.js)
    // Aguarda os IDs do GA4 (client_id/session_id): eles chegam por callback do
    // gtag('get'), nao estao prontos na hora. A versao sincrona getFields()
    // devolvia vazio em visitante novo — o cookie _ga ainda nao existia.
    // getFieldsAsync tem timeout curto e NUNCA rejeita, entao o envio do lead
    // nunca fica preso: se estourar, vai com o campo vazio e ga_status='timeout'.
    if (window.wmTracking) {
      Object.assign(payload, await window.wmTracking.getFieldsAsync());
    }

    try {
      const response = await fetch('/api/contato/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      let result;
      try {
        result = await response.json();
      } catch (err) {
        throw new Error('Erro ao processar resposta do servidor.');
      }

      if (!response.ok || !result.ok) {
        throw new Error(result.error || T.erroEnvio);
      }

      // Conversion events for GTM/GA4 (real lead — fires only after server accepts)
      window.dataLayer = window.dataLayer || [];
      window.dataLayer.push({
        event: 'form_submit',
        form_type: payload.formulario,
        page: window.location.pathname
      });
      if (payload.formulario === 'ebook') {
        window.dataLayer.push({
          event: 'ebook_download',
          ebook: form.getAttribute('data-ebook-title') || '',
          page: window.location.pathname
        });
      }

      // Success behavior
      showSuccess(form);

    } catch (err) {
      // Revert loading state
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalBtnText;
      }

      // Show error message
      if (!errorMsgEl) {
        errorMsgEl = document.createElement('p');
        errorMsgEl.className = 'form-error-msg';
        form.appendChild(errorMsgEl);
      }
      errorMsgEl.textContent = err.message || T.erroGenerico;
      errorMsgEl.style.display = 'block';
    }
  });

  function showSuccess(form) {
    const isEbook = form.getAttribute('data-form-type') === 'ebook';
    const pdfUrl = form.getAttribute('data-pdf-url');
    const formTitle = form.getAttribute('data-ebook-title') || 'Material';

    // Create success box
    const successBox = document.createElement('div');
    successBox.className = 'form-success-box';

    if (isEbook) {
      successBox.innerHTML = `
        <h3 class="form-success-box__title">${T.ebookTitulo}</h3>
        <p class="form-success-box__text">${T.ebookTexto.replace('{TITULO}', formTitle)}</p>
        <a href="${pdfUrl}" target="_blank" rel="noopener noreferrer" class="btn mt-4" style="display: inline-flex;">
          ${T.ebookBotao}
        </a>
      `;
      // Open PDF in new tab
      if (pdfUrl) {
        window.open(pdfUrl, '_blank', 'noopener');
      }
    } else {
      successBox.innerHTML = `
        <h3 class="form-success-box__title">${T.sucessoTitulo}</h3>
        <p class="form-success-box__text">${T.sucessoTexto}</p>
      `;
    }

    // Replace form contents or form itself
    const parent = form.parentNode;
    if (parent) {
      parent.replaceChild(successBox, form);
    } else {
      form.innerHTML = successBox.innerHTML;
    }
  }

})();
