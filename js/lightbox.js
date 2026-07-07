/* WM Trading — Lightbox de imagens do blog
   Abre imagens do corpo do post (.prose-wm img) em popup ampliado,
   com navegação entre imagens, fechamento por X / Esc / clique no fundo.
   Vanilla JS, sem dependências. */
(function () {
  "use strict";

  function init() {
    var thumbs = Array.prototype.slice.call(
      document.querySelectorAll(".prose-wm img")
    );
    if (!thumbs.length) return;

    // ----- Overlay (criado uma vez) -----
    var overlay = document.createElement("div");
    overlay.className = "wm-lightbox";
    overlay.setAttribute("role", "dialog");
    overlay.setAttribute("aria-modal", "true");
    overlay.setAttribute("aria-label", "Imagem ampliada");
    overlay.innerHTML =
      '<button class="wm-lightbox__btn wm-lightbox__close" aria-label="Fechar">&times;</button>' +
      '<button class="wm-lightbox__btn wm-lightbox__prev" aria-label="Imagem anterior">&#8249;</button>' +
      '<img class="wm-lightbox__img" alt="" />' +
      '<button class="wm-lightbox__btn wm-lightbox__next" aria-label="Próxima imagem">&#8250;</button>' +
      '<div class="wm-lightbox__caption"></div>';
    document.body.appendChild(overlay);

    var imgEl = overlay.querySelector(".wm-lightbox__img");
    var captionEl = overlay.querySelector(".wm-lightbox__caption");
    var btnClose = overlay.querySelector(".wm-lightbox__close");
    var btnPrev = overlay.querySelector(".wm-lightbox__prev");
    var btnNext = overlay.querySelector(".wm-lightbox__next");
    var current = 0;

    if (thumbs.length < 2) {
      btnPrev.style.display = "none";
      btnNext.style.display = "none";
    }

    function show(index) {
      current = (index + thumbs.length) % thumbs.length;
      var thumb = thumbs[current];
      // Miniaturas do WordPress têm sufixo -LARGURAxALTURA; tenta a original
      // em alta resolução e, se não existir, volta para a miniatura.
      var fullSrc = thumb.src.replace(/-\d+x\d+(\.\w+)(\?.*)?$/, "$1$2");
      imgEl.onerror = function () {
        imgEl.onerror = null;
        imgEl.src = thumb.src;
      };
      imgEl.src = fullSrc;
      imgEl.alt = thumb.alt || "";
      captionEl.textContent = thumb.alt || "";
    }

    function open(index) {
      show(index);
      overlay.classList.add("is-open");
      document.body.style.overflow = "hidden";
      btnClose.focus();
    }

    function close() {
      overlay.classList.remove("is-open");
      document.body.style.overflow = "";
    }

    thumbs.forEach(function (thumb, i) {
      thumb.addEventListener("click", function () {
        open(i);
      });
    });

    btnClose.addEventListener("click", close);
    btnPrev.addEventListener("click", function (e) {
      e.stopPropagation();
      show(current - 1);
    });
    btnNext.addEventListener("click", function (e) {
      e.stopPropagation();
      show(current + 1);
    });
    overlay.addEventListener("click", function (e) {
      if (e.target === overlay) close();
    });
    document.addEventListener("keydown", function (e) {
      if (!overlay.classList.contains("is-open")) return;
      if (e.key === "Escape") close();
      else if (e.key === "ArrowLeft" && thumbs.length > 1) show(current - 1);
      else if (e.key === "ArrowRight" && thumbs.length > 1) show(current + 1);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
