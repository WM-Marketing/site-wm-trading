/**
 * fotovoltaico.js
 * Clonado de js/aeronaves.js (só a parte do hero).
 * Carregado apenas por /segmentos/equipamentos-fotovoltaicos/.
 *
 * Define --fv-scale no .fv-hero com base na largura real do mosaico,
 * garantindo que textos e CTAs acompanhem o zoom do browser.
 */
(function () {
  const DESIGN_W  = 1440;   /* viewport de referência do design */
  const SCALE_MIN = 0.55;
  const SCALE_MAX = 1;

  function updateScale() {
    const hero    = document.querySelector('.fv-hero');
    const mosaico = document.querySelector('.fv-hero__mosaico--desktop');
    if (!hero) return;

    /* Usa a largura renderizada da composição se disponível,
       caso contrário cai para window.innerWidth */
    const refW  = mosaico ? mosaico.offsetWidth : window.innerWidth;
    const scale = Math.min(SCALE_MAX, Math.max(SCALE_MIN, refW / DESIGN_W));

    hero.style.setProperty('--fv-scale', scale.toFixed(4));
  }

  updateScale();
  window.addEventListener('resize', updateScale);
  /* Recalcula depois do load, caso a fonte mude a métrica do texto */
  window.addEventListener('load', updateScale);
})();

/* ─────────────────────────────────────
   ENTRADA DO HERO
   Quem adiciona body.loaded é o js/main.js, junto com o loader — aqui só
   marcamos que o JS está ativo, que é o gatilho do estado inicial no CSS.
───────────────────────────────────── */
(function () {
  /* Marca que o JS está ativo: só então o CSS esconde o texto para animá-lo. */
  document.documentElement.classList.add('fv-anim');
})();


/* ─────────────────────────────────────
   MODAL — Vídeo YouTube (clone de aeronaves.js)
   Abre com autoplay ao clicar no play, fecha ao clicar fora, no X ou ESC.
───────────────────────────────────── */
(function () {
  const VIDEO_ID = 'IqGdtPnWhyY';
  const VIDEO_T  = 1;               /* start time em segundos */

  const modal    = document.getElementById('fv-video-modal');
  const frame    = document.getElementById('fv-video-frame');
  const backdrop = modal?.querySelector('.fv-video-modal__backdrop');
  const closeBtn = modal?.querySelector('.fv-video-modal__close');
  const playBtn  = document.querySelector('.fv-intro__play');

  if (!modal || !playBtn) return;

  function openModal() {
    modal.hidden = false;
    document.body.style.overflow = 'hidden';
    frame.innerHTML = `<iframe
      src="https://www.youtube.com/embed/${VIDEO_ID}?autoplay=1&rel=0&start=${VIDEO_T}&modestbranding=1"
      allow="autoplay; encrypted-media; fullscreen"
      allowfullscreen
    ></iframe>`;
  }

  function closeModal() {
    modal.hidden = true;
    document.body.style.overflow = '';
    frame.innerHTML = '';   /* para o vídeo imediatamente */
  }

  playBtn.addEventListener('click', openModal);
  backdrop?.addEventListener('click', closeModal);
  closeBtn?.addEventListener('click', closeModal);
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && !modal.hidden) closeModal(); });
})();
/* ─────────────────────────────────────
   SCROLL REVEAL — seções
   Mesmo mecanismo do aeronaves.js: marca os elementos e revela quando entram
   na viewport. As classes .reveal/.reveal-fade estão no fim do CSS.
───────────────────────────────────── */
(function () {
  const stagger = (els, baseDelay = 0, step = 0.1, cls = 'reveal') => {
    els.forEach((el, i) => {
      el.style.setProperty('--reveal-delay', `${baseDelay + i * step}s`);
      el.classList.add(cls);
    });
  };

  /* S2 — faixa da usina */
  stagger(document.querySelectorAll('.fv-usina'), 0, 0);

  /* S3 — intro (os elementos já vêm com .reveal no HTML; aqui só o atraso) */
  stagger(document.querySelectorAll('.fv-intro__header'), 0.05, 0);
  stagger(document.querySelectorAll('.fv-intro__video-wrap'), 0.1, 0);
  stagger(document.querySelectorAll('.fv-intro__caption'), 0.15, 0);

  /* S4 — benefícios (os itens ficam de fora: a sanfona controla o estado) */
  stagger(document.querySelectorAll('.fv-benef__header'), 0.05, 0);

  /* S5 — gestão. Os cards usam reveal-fade (só opacidade): com o .reveal
     normal, o transform:translateY(0) do estado revelado tem a mesma
     especificidade do :hover e vence por vir depois no CSS — o scale do
     efeito nunca aplicaria. */
  stagger(document.querySelectorAll('.fv-gestao__card'), 0.1, 0.08, 'reveal-fade');

  /* S9 — CTA + formulário */
  stagger(document.querySelectorAll('.fv-cta__icon, .fv-cta__title, .fv-cta__text, .fv-cta__label, .fv-cta__actions'), 0.1, 0.1);
  stagger(document.querySelectorAll('.fv-cta__form'), 0.25, 0);

  /* S8 — cases */
  stagger(document.querySelectorAll('.fv-cases__aside'), 0.05, 0);
  stagger(document.querySelectorAll('.fv-cases__card'), 0.15, 0.12, 'reveal-fade');

  /* S7 — diferenciais (cards com reveal-fade: têm transform próprio no arco) */
  stagger(document.querySelectorAll('.fv-diff__title'), 0.1, 0);
  stagger(document.querySelectorAll('.fv-diff__card'), 0.2, 0.1, 'reveal-fade');
  stagger(document.querySelectorAll('.fv-diff__footer'), 0.2, 0);

  /* S6 — e-book */
  stagger(document.querySelectorAll('.fv-ebook__label, .fv-ebook__title, .fv-ebook__btn'), 0.15, 0.1);

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('revealed');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.reveal, .reveal-fade').forEach(el => observer.observe(el));
})();


/* ─────────────────────────────────────
   BENEFÍCIOS (S4) — lista expansível
   Um único item aberto por vez. Desktop abre no mouse, toque abre no clique,
   teclado abre no foco.
───────────────────────────────────── */
(function () {
  const itens = Array.from(document.querySelectorAll('.fv-benef__item'));
  if (!itens.length) return;

  const abrir = (alvo) => itens.forEach(i => i.classList.toggle('is-open', i === alvo));

  /* Estado inicial: o primeiro benefício, mesmo depois de recarregar */
  abrir(itens[0]);

  itens.forEach(item => {
    item.addEventListener('mouseenter', () => {
      if (window.matchMedia('(hover: hover)').matches) abrir(item);
    });

    item.addEventListener('focus', () => abrir(item));

    item.addEventListener('click', e => {
      if (e.target.closest('.fv-benef__btn')) return;   /* deixa o link navegar */
      abrir(item);
    });

    item.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        abrir(item);
      }
    });
  });
})();
