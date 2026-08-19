/* ==========================================================================
   WM Trading — Anos de experiência (atualização automática)
   --------------------------------------------------------------------------
   Mantém o "tempo de casa" sempre correto, sem edição manual todo ano.

   Uso no HTML — o número fica escrito no markup com o valor do ano corrente,
   para quem não roda JS (e para os crawlers) ler o valor certo:

     <span data-wm-anos-desde="2004">22</span> anos

   O script recalcula ano_atual − ano_de_fundação e só reescreve se o valor
   mudou. Vale para qualquer página: basta marcar o número com o atributo.
   ========================================================================== */
(function () {
  'use strict';

  function atualizar() {
    var anoAtual = new Date().getFullYear();
    var alvos = document.querySelectorAll('[data-wm-anos-desde]');

    for (var i = 0; i < alvos.length; i++) {
      var el = alvos[i];
      var fundacao = parseInt(el.getAttribute('data-wm-anos-desde'), 10);
      if (!fundacao) continue;

      var anos = anoAtual - fundacao;
      if (anos < 1) continue;

      if (el.textContent.trim() !== String(anos)) {
        el.textContent = String(anos);
      }
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', atualizar);
  } else {
    atualizar();
  }
})();
