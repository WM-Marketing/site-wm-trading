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
    ebookBotao:    'Download manually',
    infoTitulo:    'Here is your infographic ✅',
    infoTexto:     '<strong>"{TITULO}"</strong> is right below. Click the image to open it at full size.',
    infoBotao:     'Open at full size'
  } : {
    erroGenerico:  'Ocorreu um erro. Tente novamente.',
    erroEnvio:     'Não foi possível enviar o formulário. Tente novamente.',
    sucessoTitulo: 'Mensagem enviada! ✅',
    sucessoTexto:  'Recebemos o seu contato. Um especialista da WM falará com você em breve.',
    ebookTitulo:   'Material liberado! ✅',
    ebookTexto:    'O download do e-book <strong>"{TITULO}"</strong> deve começar automaticamente.',
    ebookBotao:    'Baixar e-book manualmente',
    infoTitulo:    'Infográfico liberado! ✅',
    infoTexto:     'O <strong>"{TITULO}"</strong> está logo abaixo. Clique na imagem para abrir em tamanho real.',
    infoBotao:     'Abrir em tamanho real'
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

  /* ---- "Como conheceu a WM Trading?" — origem DECLARADA (16/10/2026) --------
     O rastreio (utm, gclid, referenciador) diz por onde o lead ENTROU, nao o que
     o convenceu: quem conheceu a WM numa resposta de IA e depois buscou o nome
     chega como organico ou anuncio de marca. Esta pergunta guarda a versao do
     proprio lead, em campo separado — o api/contato.js nunca a mistura com o
     origem_canal.

     MONTADA AQUI, e nao no HTML: sao 54 formularios em ~50 paginas, varias
     geradas pelo build. Cada um recebe a pergunta copiando o visual do campo
     vizinho DAQUELE formulario (o "Como deseja ser respondido?", ou a Empresa
     no e-book), entao ela herda o estilo de cada layout sem CSS novo. Formulario
     que ja tiver o campo no HTML e respeitado.

     Os CODIGOS sao a lista fechada do api/contato.js (ORIGENS_DECLARADAS) e sao
     os mesmos em PT e EN. O scripts/verificar.py confere que nao divergiram. */
  var ORIGEM = {
    pergunta: EN ? 'How did you hear about WM Trading? *' : 'Como conheceu a WM Trading? *',
    selecione: EN ? 'Select' : 'Selecione',
    outro: EN ? 'Which one? *' : 'Qual? *',
    opcoes: [
      ['google',    'Pesquisa no Google', 'Google search'],
      ['ia',        'Resposta de uma IA (ChatGPT, Gemini, resumo de IA do Google)',
                    'An AI answer (ChatGPT, Gemini, Google AI Overview)'],
      ['linkedin',  'LinkedIn', 'LinkedIn'],
      ['instagram', 'Instagram', 'Instagram'],
      ['indicacao', 'Indicação', 'Referral'],
      ['feira',     'Feira ou evento', 'Trade show or event'],
      ['cliente',   'Já sou cliente', 'I am already a client'],
      ['outro',     'Outro', 'Other']
    ]
  };
  var origemSeq = 0;

  function montarOrigemDeclarada(form) {
    if (form.querySelector('[name="origem_declarada"]')) return;

    var modelo = form.querySelector('select[name="forma_resposta"]') ||
                 form.querySelector('[name="empresa"]') ||
                 form.querySelector('[name="email"]');
    if (!modelo) return;

    /* Layout com rotulo proprio (<div><label/><select/></div>) copia o bloco
       inteiro; layout de placeholder (o campo solto no grid) copia so o campo. */
    var pai = modelo.parentElement;
    var embrulhado = pai && pai !== form && pai.querySelector('label') &&
                     pai.querySelectorAll('input, select, textarea').length === 1;
    var bloco = embrulhado ? pai.cloneNode(true) : null;
    var id = 'wm-origem-' + (++origemSeq);

    var select = document.createElement('select');
    select.name = 'origem_declarada';
    select.required = true;
    select.className = modelo.className;
    select.id = id;

    var vazio = document.createElement('option');
    vazio.value = '';
    vazio.disabled = true;
    vazio.selected = true;
    vazio.textContent = embrulhado ? ORIGEM.selecione : ORIGEM.pergunta;
    select.appendChild(vazio);
    ORIGEM.opcoes.forEach(function (o) {
      var op = document.createElement('option');
      op.value = o[0];
      op.textContent = EN ? o[2] : o[1];
      select.appendChild(op);
    });
    if (!embrulhado) select.setAttribute('aria-label', ORIGEM.pergunta.replace(' *', ''));

    var outro = document.createElement('input');
    outro.type = 'text';
    outro.name = 'origem_declarada_outro';
    outro.maxLength = 120;
    outro.placeholder = ORIGEM.outro;
    outro.setAttribute('aria-label', ORIGEM.outro.replace(' *', ''));
    outro.className = modelo.className;
    // Escondido E desabilitado: fora do "Outro" nao e obrigatorio nem e enviado.
    outro.style.display = 'none';
    outro.disabled = true;
    if (embrulhado) outro.style.marginTop = '8px';

    select.addEventListener('change', function () {
      var ativo = select.value === 'outro';
      outro.style.display = ativo ? '' : 'none';
      outro.disabled = !ativo;
      outro.required = ativo;
      if (ativo) outro.focus();
    });

    var ancora = embrulhado ? pai : modelo;
    if (embrulhado) {
      var campoVelho = bloco.querySelector('input, select, textarea');
      var rotulo = bloco.querySelector('label');
      rotulo.textContent = ORIGEM.pergunta;
      rotulo.setAttribute('for', id);
      campoVelho.parentNode.replaceChild(select, campoVelho);
      select.parentNode.insertBefore(outro, select.nextSibling);
      ancora.parentNode.insertBefore(bloco, ancora.nextSibling);
    } else {
      ancora.parentNode.insertBefore(select, ancora.nextSibling);
      select.parentNode.insertBefore(outro, select.nextSibling);
    }
  }

  function montarTodas() {
    Array.prototype.forEach.call(document.querySelectorAll('form.contact-form-js'), montarOrigemDeclarada);
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', montarTodas);
  } else {
    montarTodas();
  }

  /* CARIMBO DE TEMPO — camada anti-robo (31/08/2026)
     Guarda quando esta pagina ficou pronta. O tempo ate o envio segue no
     payload e o servidor recusa o que for rapido demais para ser humano.
     Vale tambem pela AUSENCIA: robo que posta JSON direto no endpoint, sem
     abrir a pagina, nao tem como produzir este campo. */
  const CARREGADA_EM = Date.now();

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

    // Milissegundos entre a pagina ficar pronta e o visitante enviar.
    payload._ms = Date.now() - CARREGADA_EM;

    // Qual material foi baixado. Ja existia no data-ebook-title e ia para o
    // dataLayer, mas nunca chegava ao CRM — e e a informacao mais util deste
    // lead: diz o assunto que interessa ao contato.
    const tituloEbook = form.getAttribute('data-ebook-title');
    if (tituloEbook) payload.ebook = tituloEbook;

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
        event: 'wm_form_submit',
        form_type: payload.formulario,
        page: window.location.pathname
      });
      if (payload.formulario === 'ebook' || payload.formulario === 'infografico') {
        window.dataLayer.push({
          event: payload.formulario === 'ebook' ? 'ebook_download' : 'infografico_view',
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
    const tipo = form.getAttribute('data-form-type');
    const isEbook = tipo === 'ebook';
    const isInfografico = tipo === 'infografico';
    const pdfUrl = form.getAttribute('data-pdf-url');
    const imagemUrl = form.getAttribute('data-imagem-url');
    const formTitle = form.getAttribute('data-ebook-title') || 'Material';

    // Create success box
    const successBox = document.createElement('div');
    successBox.className = 'form-success-box';

    if (isInfografico && imagemUrl) {
      /* O infografico aparece AQUI, na propria pagina. Nada de window.open:
         este codigo roda depois do fetch, e o bloqueador de pop-up barra
         janela aberta fora do clique. O link abaixo e um clique do visitante,
         entao esse abre normalmente. */
      successBox.classList.add('form-success-box--infografico');
      successBox.innerHTML = `
        <h3 class="form-success-box__title">${T.infoTitulo}</h3>
        <p class="form-success-box__text">${T.infoTexto.replace('{TITULO}', formTitle)}</p>
        <a href="${imagemUrl}" target="_blank" rel="noopener noreferrer" class="info-reveal">
          <img src="${imagemUrl}" alt="${formTitle}" class="info-reveal__img" />
        </a>
        <a href="${imagemUrl}" target="_blank" rel="noopener noreferrer" class="btn mt-4" style="display: inline-flex;">
          ${T.infoBotao}
        </a>
      `;
    } else if (isEbook) {
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
