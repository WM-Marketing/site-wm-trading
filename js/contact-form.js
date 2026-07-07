/* ==========================================================================
   WM Trading — contact-form.js (Vanilla client-side form submissions)
   ========================================================================== */

(function() {
  'use strict';

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

    try {
      const response = await fetch('/api/contato', {
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
        throw new Error(result.error || 'Não foi possível enviar o formulário. Tente novamente.');
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
      errorMsgEl.textContent = err.message || 'Ocorreu um erro. Tente novamente.';
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
        <h3 class="form-success-box__title">Material liberado! ✅</h3>
        <p class="form-success-box__text">O download do e-book <strong>"${formTitle}"</strong> deve começar automaticamente.</p>
        <a href="${pdfUrl}" target="_blank" rel="noopener noreferrer" class="btn mt-4" style="display: inline-flex;">
          Baixar e-book manualmente
        </a>
      `;
      // Open PDF in new tab
      if (pdfUrl) {
        window.open(pdfUrl, '_blank', 'noopener');
      }
    } else {
      successBox.innerHTML = `
        <h3 class="form-success-box__title">Mensagem enviada! ✅</h3>
        <p class="form-success-box__text">Recebemos o seu contato. Um especialista da WM falará com você em breve.</p>
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
