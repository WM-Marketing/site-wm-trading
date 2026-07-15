// WM Trading 2.0 — Main JS

// Page Loader — Lottie cargo ship
(function () {
  const loader = document.getElementById('page-loader');
  const container = document.getElementById('loader-lottie');
  if (!loader || !container) return;

  const init = () => {
    if (typeof lottie === 'undefined') return;
    lottie.loadAnimation({
      container,
      renderer: 'svg',
      loop: true,
      autoplay: true,
      path: 'images/assets/cargo-ship.json'
    });
  };

  // Init when lottie is ready
  if (typeof lottie !== 'undefined') {
    init();
  } else {
    document.querySelector('script[src*="lottie"]')?.addEventListener('load', init);
  }

  // Hide loader + trigger hero entrance
  window.addEventListener('load', () => {
    setTimeout(() => {
      loader.classList.add('hidden');
      document.body.classList.add('loaded');
    }, 300);
  });
})();

// Counter animation — Section 4
(function () {
  const counters = document.querySelectorAll('.numero-value[data-count]');
  if (!counters.length) return;

  const animate = (el) => {
    const target = +el.dataset.count;
    const suffix = el.dataset.suffix || '';
    const duration = 1600;
    const start = performance.now();

    const step = (now) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = Math.floor(eased * target) + suffix;
      if (progress < 1) requestAnimationFrame(step);
      else el.textContent = target + suffix;
    };
    requestAnimationFrame(step);
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        animate(entry.target);
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.3 });

  counters.forEach(el => observer.observe(el));
})();

// Nav Dropdown — keyboard + mobile tap support
(function () {
  document.querySelectorAll('.nav-dropdown').forEach(dropdown => {
    const trigger = dropdown.querySelector('.nav-dropdown__trigger');
    const menu    = dropdown.querySelector('.nav-dropdown__menu');
    if (!trigger || !menu) return;

    function openDropdown() {
      trigger.classList.add('open');
      menu.classList.add('open');
      trigger.setAttribute('aria-expanded', 'true');
    }
    function closeDropdown() {
      trigger.classList.remove('open');
      menu.classList.remove('open');
      trigger.setAttribute('aria-expanded', 'false');
    }

    // Toggle on click (for touch/mobile)
    trigger.addEventListener('click', e => {
      e.stopPropagation();
      // Trigger que também é link (ex.: Segmentos → /segmentos/):
      // desktop (hover abre o submenu) o clique navega; no touch o 1º toque
      // abre o submenu e o 2º toque navega
      if (trigger.tagName === 'A') {
        if (window.matchMedia('(hover: hover)').matches) return;
        if (!menu.classList.contains('open')) {
          e.preventDefault();
          openDropdown();
        }
        return;
      }
      menu.classList.contains('open') ? closeDropdown() : openDropdown();
    });

    // Close when clicking outside
    document.addEventListener('click', () => closeDropdown());

    // Keyboard: Escape closes
    trigger.addEventListener('keydown', e => {
      if (e.key === 'Escape') closeDropdown();
    });
  });
})();

// Segmentos carousel — setas avançam 1 card; snap do CSS alinha o trilho
(function () {
  const track = document.querySelector('.segmentos-carousel .segmentos-grid');
  const prev  = document.querySelector('.segmentos-nav--prev');
  const next  = document.querySelector('.segmentos-nav--next');
  if (!track || !prev || !next) return;

  function step() {
    const card = track.querySelector('.segmento-card');
    if (!card) return 0;
    const gap = parseFloat(getComputedStyle(track).columnGap) || 20;
    return card.getBoundingClientRect().width + gap;
  }

  function update() {
    const max = track.scrollWidth - track.clientWidth - 1;
    prev.disabled = track.scrollLeft <= 0;
    next.disabled = track.scrollLeft >= max;
  }

  prev.addEventListener('click', () => track.scrollBy({ left: -step(), behavior: 'smooth' }));
  next.addEventListener('click', () => track.scrollBy({ left: step(), behavior: 'smooth' }));
  track.addEventListener('scroll', update, { passive: true });
  window.addEventListener('resize', update);
  update();
})();

// Hamburger menu toggle
(function () {
  const toggle = document.getElementById('menu-toggle');
  const nav    = document.querySelector('.header-nav');
  if (!toggle || !nav) return;
  toggle.addEventListener('click', () => {
    const open = nav.classList.toggle('open');
    toggle.classList.toggle('open', open);
    toggle.setAttribute('aria-expanded', open);
  });
  // Fecha ao clicar num link
  nav.querySelectorAll('a').forEach(a => {
    a.addEventListener('click', () => {
      nav.classList.remove('open');
      toggle.classList.remove('open');
      toggle.setAttribute('aria-expanded', false);
    });
  });
})();

// Header shadow on scroll
window.addEventListener('scroll', () => {
  document.querySelector('.header')?.classList.toggle('scrolled', window.scrollY > 10);
});
document.head.insertAdjacentHTML('beforeend', '<style>.header.scrolled{box-shadow:0 2px 16px rgba(0,0,0,0.08)}</style>');

// Scroll blur reveal — Sections 3–9
(function () {
  const stagger = (els, baseDelay = 0, step = 0.1) => {
    els.forEach((el, i) => {
      el.style.setProperty('--reveal-delay', `${baseDelay + i * step}s`);
      el.classList.add('reveal');
    });
  };

  // Section 3 — motivo
  stagger(document.querySelectorAll('.motivo-title, .motivo-subtitle, .motivo-divider'), 0.25, 0.1);
  stagger(document.querySelectorAll('.motivo-grid-top .motivo-card'), 0.25, 0.12);
  stagger(document.querySelectorAll('.motivo-grid-bottom .motivo-card'), 0.25, 0.12);

  // Section 4 — números
  stagger(document.querySelectorAll('.numero-item'), 0.25, 0.12);

  // Section 5 — benefícios
  stagger(document.querySelectorAll('.beneficios-title-row, .beneficios-text, .beneficios-map'), 0.25, 0.12);

  // Section 6 — experiência
  stagger(document.querySelectorAll('.experiencia-media, .experiencia-content'), 0.25, 0.15);

  // Section 7 — segmentos
  stagger(document.querySelectorAll('.segmentos-header'), 0.25, 0);
  stagger(document.querySelectorAll('.segmento-card'), 0.25, 0.12);
  stagger(document.querySelectorAll('.segmentos-ver-todos'), 0.6, 0);

  // Section 8 — modalidades
  stagger(document.querySelectorAll('.modalidade-header, .tabs, .tab-panels'), 0.25, 0.12);

  // Section 9 — CTA
  stagger(document.querySelectorAll('.cta-title, .cta-text, .section-cta .btn'), 0.25, 0.12);

  // Observer
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('revealed');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15 });

  document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
})();

// Magic card effect — Section 3
document.querySelectorAll('.motivo-card').forEach(card => {
  card.addEventListener('mousemove', (e) => {
    const rect = card.getBoundingClientRect();
    card.style.setProperty('--mouse-x', `${e.clientX - rect.left}px`);
    card.style.setProperty('--mouse-y', `${e.clientY - rect.top}px`);
  });
});

// VER TODOS bar — match height to card image (Section 7)
(function () {
  const syncBar = () => {
    const img = document.querySelector('.segmento-card-img');
    const bar = document.querySelector('.segmentos-ver-todos');
    if (!img || !bar) return;
    bar.style.height = img.offsetHeight + 'px';
  };
  syncBar();
  window.addEventListener('resize', syncBar);
})();

// Tabs — Section 8
document.querySelectorAll('.tab-radio input[type="radio"]').forEach(input => {
  input.addEventListener('change', () => {
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.getElementById('tab-' + input.value)?.classList.add('active');
  });
});
