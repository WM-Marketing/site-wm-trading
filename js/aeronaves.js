/**
 * aeronaves.js
 * Define --aero-scale no .aero-hero com base na largura real do SVG,
 * garantindo que textos e CTAs acompanhem o zoom do browser.
 *
 * PARÂMETROS:
 *   SVG_DESIGN_W — largura de referência do SVG no Figma (px)
 *   SCALE_MIN    — escala mínima (evita texto ilegível)
 *   SCALE_MAX    — escala máxima (não ultrapassa o design original)
 */
(function () {
  const SVG_DESIGN_W = 1440;   /* viewport de referência do design */
  const SCALE_MIN    = 0.55;
  const SCALE_MAX    = 1;

  function updateScale() {
    const hero   = document.querySelector('.aero-hero');
    /* Era .aero-hero__bg-img, o SVG de 13 MB. Ele saiu e a composicao virou o
       mosaico HTML — sem trocar este seletor, bgImg ficaria null, a medida
       cairia no innerWidth e a escala do desktop desabaria de 1 para ~0.89,
       encolhendo todo o texto do hero. */
    const bgImg  = document.querySelector('.aero-hero__mosaico--desktop');
    if (!hero) return;

    /* Usa a largura renderizada da composição se disponível,
       caso contrário cai para window.innerWidth */
    const refW = bgImg ? bgImg.offsetWidth : window.innerWidth;
    const raw   = refW / SVG_DESIGN_W;
    const scale = Math.min(SCALE_MAX, Math.max(SCALE_MIN, raw));

    hero.style.setProperty('--aero-scale', scale.toFixed(4));
  }

  /* Executa imediatamente e após cada redimensionamento */
  updateScale();
  window.addEventListener('resize', updateScale);

  /* Antes era o evento load do SVG, que definia a altura do hero ao chegar.
     O mosaico tem aspect-ratio no CSS, então já ocupa o espaço certo antes das
     fotos carregarem — não há reflow para esperar. Mantido só o recálculo pós
     load da página, para o caso de a fonte mudar a métrica do texto. */
  window.addEventListener('load', updateScale);
})();

/* ─────────────────────────────────────
   MODAL — Vídeo YouTube
   Abre com autoplay ao clicar no play,
   fecha ao clicar fora, no X ou ESC.
───────────────────────────────────── */
(function () {
  const VIDEO_ID  = 'FOQEa2Xtqjs';
  const VIDEO_T   = 2;               /* start time em segundos */

  const modal     = document.getElementById('aero-video-modal');
  const frame     = document.getElementById('aero-video-frame');
  const backdrop  = modal?.querySelector('.aero-video-modal__backdrop');
  const closeBtn  = modal?.querySelector('.aero-video-modal__close');
  const playBtn   = document.querySelector('.aero-intro__play');

  if (!modal || !playBtn) return;

  function openModal() {
    modal.hidden = false;
    document.body.style.overflow = 'hidden';
    frame.innerHTML = `<iframe
      src="https://www.youtube.com/embed/${VIDEO_ID}?autoplay=1&rel=0&t=${VIDEO_T}&modestbranding=1"
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
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });
})();

/* ─────────────────────────────────────
   CARROSSEL — 6 Passos para Importar
   3 cards visíveis: prev | active | next
   Navegação circular por botões ou clique nos laterais
───────────────────────────────────── */
(function () {
  const track    = document.getElementById('stepsTrack');
  if (!track) return;

  const cards    = Array.from(track.querySelectorAll('.aero-steps__card'));
  const prevBtn  = document.querySelector('.aero-steps__nav--prev');
  const nextBtn  = document.querySelector('.aero-steps__nav--next');
  const total    = cards.length;               /* 6 */

  let current    = 0;
  let animating  = false;
  const ANIM_MS  = 420;                        /* deve bater com transition duration */

  /* ── Índice circular ── */
  const mod = (n) => ((n % total) + total) % total;

  /* ── Aplica os estados (is-active / is-prev / is-next / is-hidden) ── */
  function render(idx) {
    const prevIdx = mod(idx - 1);
    const nextIdx = mod(idx + 1);

    cards.forEach((card, i) => {
      card.classList.remove('is-active', 'is-prev', 'is-next', 'is-hidden');
      if      (i === idx)      card.classList.add('is-active');
      else if (i === prevIdx)  card.classList.add('is-prev');
      else if (i === nextIdx)  card.classList.add('is-next');
      else                     card.classList.add('is-hidden');
    });
  }

  /* ── Navega para um novo índice ── */
  function goTo(newIdx) {
    if (animating) return;
    animating = true;
    current = mod(newIdx);
    render(current);
    setTimeout(() => { animating = false; }, ANIM_MS);
  }

  /* ── Botões prev / next ── */
  prevBtn?.addEventListener('click', () => goTo(current - 1));
  nextBtn?.addEventListener('click', () => goTo(current + 1));

  /* ── Clique nos cards laterais avança/recua ── */
  cards.forEach((card, i) => {
    card.addEventListener('click', () => {
      if (card.classList.contains('is-prev')) goTo(current - 1);
      else if (card.classList.contains('is-next')) goTo(current + 1);
    });
  });

  /* ── Swipe touch (mobile) ── */
  let touchStartX = 0;
  track.addEventListener('touchstart', (e) => {
    touchStartX = e.touches[0].clientX;
  }, { passive: true });
  track.addEventListener('touchend', (e) => {
    const dx = e.changedTouches[0].clientX - touchStartX;
    if (Math.abs(dx) > 50) {
      goTo(dx < 0 ? current + 1 : current - 1);
    }
  }, { passive: true });

  /* ── Teclado (acessibilidade) ── */
  document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowRight') goTo(current + 1);
    if (e.key === 'ArrowLeft')  goTo(current - 1);
  });

  /* ── Estado inicial ── */
  render(current);
})();


/* ─────────────────────────────────────
   SCROLL REVEAL — todas as seções
───────────────────────────────────── */
(function () {
  const stagger = (els, baseDelay = 0, step = 0.1, cls = 'reveal') => {
    els.forEach((el, i) => {
      el.style.setProperty('--reveal-delay', `${baseDelay + i * step}s`);
      el.classList.add(cls);
    });
  };

  /* S2 — intro jet */
  stagger(document.querySelectorAll('.aero-jet'), 0, 0);

  /* S4 — carrossel de passos (cards excluídos — carrossel controla position/transform próprios) */
  stagger(document.querySelectorAll('.aero-steps__title'), 0.1, 0);

  /* S5 — ebook CTA (capa excluída — usa transform próprio para centralizar) */
  stagger(document.querySelectorAll('.aero-ebook__label, .aero-ebook__title, .aero-ebook__btn'), 0.15, 0.1);

  /* S6 — diferenciais (cards usam reveal-fade — têm translateY próprio para o arco) */
  stagger(document.querySelectorAll('.aero-diff__title'), 0.1, 0);
  stagger(document.querySelectorAll('.aero-diff__card'), 0.2, 0.1, 'reveal-fade');

  /* S7 — bento (conteúdo dos blocos especiais) */
  stagger(document.querySelectorAll('.aero-bento28__inner'), 0.25, 0);
  stagger(document.querySelectorAll('.aero-bento55__inner'), 0.35, 0);

  /* S8 — bento2 conteúdo */
  stagger(document.querySelectorAll('.aero-bento2-4__inner'), 0.15, 0);
  stagger(document.querySelectorAll('.aero-bento2-7__item'), 0.2, 0.15);

  /* S9 — CTA formulário */
  stagger(document.querySelectorAll('.aero-cta__icon, .aero-cta__title, .aero-cta__text, .aero-cta__cta-label, .aero-cta__actions'), 0.1, 0.1);
  stagger(document.querySelectorAll('.aero-cta__form-card'), 0.25, 0);

  /* Observer com threshold baixo para seções largas */
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
