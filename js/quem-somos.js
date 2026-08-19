/* ==========================================================================
   WM Trading — Quem somos (/about/)
   --------------------------------------------------------------------------
   1) Entrada suave dos blocos ao rolar, no mesmo padrão da home.
   2) Animação dos gráficos do índice de satisfação.

   Em nenhum dos dois o HTML já vem no estado escondido: as classes são
   aplicadas por JS. Se o script não rodar, a página aparece completa e os
   gráficos aparecem cheios — nunca vazios.
   ========================================================================== */
(function () {
  'use strict';

  var semAnimacao = window.matchMedia &&
                    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------------------------------------------------------------- REVEAL */
  var GRUPOS = [
    { sel: '.qs-brands__list img',                        delay: 0.15, passo: 0.08 },
    { sel: '.qs-bento__cell--texto, .qs-bento__cell--foto', delay: 0.20, passo: 0.10 },
    { sel: '.qs-kpi',                                     delay: 0.20, passo: 0.10 },
    { sel: '.qs-commitment__head',                        delay: 0.20, passo: 0    },
    { sel: '.qs-atuacoes__title, .qs-atuacoes__sub',      delay: 0.20, passo: 0.10 },
    { sel: '.qs-atuacao',                                 delay: 0.20, passo: 0.12 },
    { sel: '.qs-quality .qs-split > *',                   delay: 0.20, passo: 0.15 },
    { sel: '.qs-satisfacao .qs-split > *',                delay: 0.20, passo: 0.15 },
    { sel: '.qs-carreiras__grid > *',                     delay: 0.20, passo: 0.15 }
  ];

  function prepararReveal() {
    var alvos = [];

    GRUPOS.forEach(function (grupo) {
      var els = document.querySelectorAll(grupo.sel);
      Array.prototype.forEach.call(els, function (el, i) {
        el.style.setProperty('--reveal-delay', (grupo.delay + i * grupo.passo) + 's');
        el.classList.add('reveal');
        alvos.push(el);
      });
    });

    return alvos;
  }

  /* ------------------------------------------------------------- GRÁFICOS */
  /* O traço é desenhado por stroke-dashoffset: --qs-vazio é o estado sem
     preenchimento e --qs-cheio o valor final. O CSS faz a transição; aqui
     só entra a classe .is-cheio quando o gráfico aparece na tela. */
  function prepararGraficos() {
    return Array.prototype.map.call(
      document.querySelectorAll('.qs-gauge'),
      function (gauge) {
        gauge.classList.add('is-animado');
        return gauge;
      }
    );
  }

  function contar(el, alvo, duracao) {
    if (semAnimacao) { el.textContent = alvo + '%'; return; }

    var inicio = null;
    function passo(agora) {
      if (inicio === null) inicio = agora;
      var t = Math.min((agora - inicio) / duracao, 1);
      /* Desaceleração equivalente à do traço (cubic-bezier .25,1,.35,1), para o
         número e o anel andarem juntos em vez de o anel chegar primeiro. */
      var suave = 1 - Math.pow(1 - t, 4);
      el.textContent = Math.round(alvo * suave) + '%';
      if (t < 1) requestAnimationFrame(passo);
    }
    requestAnimationFrame(passo);
  }

  function encher(gauge) {
    gauge.classList.add('is-cheio');

    var num = gauge.querySelector('[data-qs-num]');
    var pct = parseInt(gauge.getAttribute('data-qs-pct'), 10);
    if (num && pct) {
      var duracao = gauge.classList.contains('qs-gauge-main') ? 1600 : 1400;
      contar(num, pct, duracao);
    }
  }

  /* ---------------------------------------------------------------- INÍCIO */
  function iniciar() {
    var reveals = prepararReveal();
    var gauges = prepararGraficos();
    var alvos = reveals.concat(gauges);

    if (!alvos.length) return;

    /* Navegador antigo, ou sem observer: mostra tudo já resolvido. */
    if (!('IntersectionObserver' in window)) {
      reveals.forEach(function (el) { el.classList.add('revealed'); });
      gauges.forEach(encher);
      return;
    }

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var el = entry.target;

        if (el.classList.contains('qs-gauge')) encher(el);
        else el.classList.add('revealed');

        observer.unobserve(el);
      });
    }, { threshold: 0.15 });

    alvos.forEach(function (el) { observer.observe(el); });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', iniciar);
  } else {
    iniciar();
  }
})();
