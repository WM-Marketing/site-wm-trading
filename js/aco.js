/**
 * aco.js
 * Clonado de js/aeronaves.js (só a parte do hero).
 * Carregado apenas por /segmentos/aco/.
 *
 * Define --aco-scale no .aco-hero com base na largura real do mosaico,
 * garantindo que textos e CTAs acompanhem o zoom do browser.
 */
(function () {
  const DESIGN_W  = 1440;   /* viewport de referência do design */
  const SCALE_MIN = 0.55;
  const SCALE_MAX = 1;

  function updateScale() {
    const hero    = document.querySelector('.aco-hero');
    const mosaico = document.querySelector('.aco-hero__mosaico--desktop');
    if (!hero) return;

    /* Usa a largura renderizada da composição se disponível,
       caso contrário cai para window.innerWidth */
    const refW  = mosaico ? mosaico.offsetWidth : window.innerWidth;
    const scale = Math.min(SCALE_MAX, Math.max(SCALE_MIN, refW / DESIGN_W));

    hero.style.setProperty('--aco-scale', scale.toFixed(4));
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
  document.documentElement.classList.add('aco-anim');
})();


/* ─────────────────────────────────────
   MODAL — Vídeo YouTube (clone de aeronaves.js)
   Abre com autoplay ao clicar no play, fecha ao clicar fora, no X ou ESC.
───────────────────────────────────── */
(function () {
  /* Video do SEGMENTO DE MAQUINAS. O clone da pagina fotovoltaica veio com o
     video dela (IqGdtPnWhyY) e ficou assim no ar de 27/08/2026 ate ser
     corrigido no mesmo dia. A fonte da verdade e o SEGMENT_MEDIA["aco"]
     do build_pages.py, que ja trazia https://youtu.be/LUHSCxojw9A e alimentava
     a versao gerada da pagina antes do layout novo. */
  const VIDEO_ID = 'yutUI3a5GsA';   /* WM CAST #17 — Importacao de Aco e Fertilizantes */
  const VIDEO_T  = 0;               /* start time em segundos */

  const modal    = document.getElementById('aco-video-modal');
  const frame    = document.getElementById('aco-video-frame');
  const backdrop = modal?.querySelector('.aco-video-modal__backdrop');
  const closeBtn = modal?.querySelector('.aco-video-modal__close');
  const playBtn  = document.querySelector('.aco-intro__play');

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

  /* S2 — faixa full-width */
  stagger(document.querySelectorAll('.aco-faixa'), 0, 0);

  /* S3 — intro (os elementos já vêm com .reveal no HTML; aqui só o atraso) */
  stagger(document.querySelectorAll('.aco-intro__col'), 0.05, 0);
  stagger(document.querySelectorAll('.aco-intro__video-wrap'), 0.15, 0);

  /* S4 — benefícios (os itens ficam de fora: a sanfona controla o estado) */
  stagger(document.querySelectorAll('.aco-benef__header'), 0.05, 0);

  /* S5 — gestão. Os cards usam reveal-fade (só opacidade): com o .reveal
     normal, o transform:translateY(0) do estado revelado tem a mesma
     especificidade do :hover e vence por vir depois no CSS — o scale do
     efeito nunca aplicaria. */
  stagger(document.querySelectorAll('.aco-gestao__card'), 0.1, 0.08, 'reveal-fade');

  /* S9 — CTA + formulário */
  stagger(document.querySelectorAll('.aco-cta__icon, .aco-cta__title, .aco-cta__text, .aco-cta__label, .aco-cta__actions'), 0.1, 0.1);
  stagger(document.querySelectorAll('.aco-cta__form'), 0.25, 0);

  /* S8 — nossos resultados */
  stagger(document.querySelectorAll('.aco-result__header'), 0.05, 0);
  stagger(document.querySelectorAll('.aco-result__banner'), 0.15, 0);
  stagger(document.querySelectorAll('.aco-result__footer'), 0.25, 0);

  /* S7 — diferenciais (cards com reveal-fade: têm transform próprio no arco) */
  stagger(document.querySelectorAll('.aco-diff__title'), 0.1, 0);
  stagger(document.querySelectorAll('.aco-diff__card'), 0.2, 0.1, 'reveal-fade');
  stagger(document.querySelectorAll('.aco-diff__footer'), 0.2, 0);

  /* S6 — conteúdos do blog */
  stagger(document.querySelectorAll('.aco-blog__header'), 0.05, 0);

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
  const itens = Array.from(document.querySelectorAll('.aco-benef__item'));
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
      if (e.target.closest('.aco-benef__btn')) return;   /* deixa o link navegar */
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


/* ══════════════════════════════════════
   S6 — VITRINE DO BLOG, SEMPRE ATUAL
   O HTML já chega com os 3 posts do último build. Aqui a lista é relida de
   /blog/posts-aco.json — publicado pelo build_pages.py — e reescrita,
   para o caso de um post ter entrado depois de esta página ser gerada.
   Se o fetch falhar (offline, 404, JSON quebrado) nada acontece e o visitante
   continua vendo os cards do HTML: nunca trocamos conteúdo bom por vazio.
══════════════════════════════════════ */
(function () {
  const grade = document.querySelector('[data-aco-blog-feed]');
  if (!grade || !('fetch' in window)) return;

  const QUANTOS = 3;
  const SETA = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" ' +
    'aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>';

  /* O título e a categoria vêm do frontmatter dos posts. Escapar aqui evita
     que um '&' ou um '<' num título quebre a marcação da vitrine. */
  const esc = (t) => String(t == null ? '' : t).replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[c]);

  function card(post) {
    const capa = post.cover || '/images/aco/benef-01.jpg';
    return '<a class="aco-blog__card" href="' + esc(post.url) + '">' +
      '<div class="aco-blog__media">' +
        '<img src="' + esc(capa) + '" alt="" width="640" height="420" ' +
             'loading="lazy" decoding="async">' +
      '</div>' +
      '<div class="aco-blog__body">' +
        '<span class="aco-blog__meta">' +
          '<span class="aco-blog__cat">' + esc(post.category) + '</span>' +
          '<time datetime="' + esc(String(post.date).slice(0, 10)) + '">' +
            esc(post.displayDate) + '</time>' +
        '</span>' +
        '<h3 class="aco-blog__card-title">' + esc(post.title) + '</h3>' +
        '<span class="aco-blog__more">Ler artigo' + SETA + '</span>' +
      '</div>' +
    '</a>';
  }

  fetch('/blog/posts-aco.json', { cache: 'no-cache' })
    .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
    .then((posts) => {
      if (!Array.isArray(posts) || !posts.length) return;
      grade.innerHTML = posts.slice(0, QUANTOS).map(card).join('');
    })
    .catch(() => { /* fica o HTML do build */ });
})();
