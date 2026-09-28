# Loader do navio animado — desativado em 28/09/2026

## Por que saiu

PageSpeed de 28/09/2026 (home): desempenho 55 no celular e 61 no computador. Os dados
reais do Chrome davam LCP de 5,9 s no celular e 4,7 s no computador, reprovado nas Core
Web Vitals.

O loader cobria a página inteira e só saía no `window.load`, ou seja, depois de baixar
**tudo**: chat Botmaker (com um PNG de 920 KB), GTM, AdOpt etc. A foto principal
chegava em cerca de 0,2 s e ficava escondida atrás dele (atraso de renderização de
2,2 s). A animação de entrada do hero (`body.loaded`) também esperava esse evento.

Hoje o `body.loaded` é disparado no `DOMContentLoaded` e a animação de entrada do hero
continua funcionando.

## O que foi mantido

- `images/assets/cargo-ship.json`: a animação em si, que continua no repositório.

## Para reativar (4 passos)

### 1. `<head>` de cada página: carregar a biblioteca Lottie

```html
  <script src="https://cdnjs.cloudflare.com/ajax/libs/lottie-web/5.12.2/lottie.min.js" defer></script>
```

Ficava logo antes de `<script src="/js/whatsapp-popup.js" defer></script>`.

### 2. Início do `<body>` de cada página: o bloco do loader

```html
<!-- ══════════════════════════════════════
     PAGE LOADER
══════════════════════════════════════ -->
<div id="page-loader" aria-hidden="true">
  <div id="loader-lottie"></div>
</div>
```

Ficava logo depois de `<body>`, antes do comentário `HEADER`. No `index.html` ele fica
dentro do trecho que o `scripts/build_pages.py` copia como cabeçalho (entre o comentário
`HEADER` e `</header>`), então as páginas geradas herdam o loader sozinhas no próximo build.

### 3. `css/main.css`: o estilo do loader

```css
/* =============================================
   PAGE LOADER
   ============================================= */
#page-loader {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: opacity 0.5s ease, visibility 0.5s ease;
}
#page-loader.hidden {
  opacity: 0;
  visibility: hidden;
  pointer-events: none;
}
#loader-lottie {
  width: 220px;
  height: 220px;
}
```

Ficava antes da seção `SCROLL REVEAL`.

### 4. `js/main.js`: trocar o bloco "Hero entrance" pelo original

```js
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
      // caminho ABSOLUTO: relativo resolve contra a pasta da pagina, entao em
      // /en/about/ virava /en/about/images/... e dava 404 em 291 das 292 paginas.
      path: '/images/assets/cargo-ship.json'
    });
  };

  if (typeof lottie !== 'undefined') {
    init();
  } else {
    document.querySelector('script[src*="lottie"]')?.addEventListener('load', init);
  }

  window.addEventListener('load', () => {
    setTimeout(() => {
      loader.classList.add('hidden');
      document.body.classList.add('loaded');
    }, 300);
  });
})();
```

**Recomendação para reativar sem perder a velocidade:** esconder o loader no
`DOMContentLoaded`, e não no `load`. Assim o navio aparece só por um instante e não fica
esperando o chat nem as tags de terceiros.

A versão completa anterior está no git: commit anterior ao "Remove loader do navio
animado" (`git log --oneline -- js/main.js`).
