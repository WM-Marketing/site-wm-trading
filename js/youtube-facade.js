/* Carrega o player somente quando o visitante pede para assistir. */
document.addEventListener('click', function (event) {
  var button = event.target.closest('.wm-youtube-facade__button');
  if (!button) return;

  var container = button.closest('.wm-youtube-facade');
  var videoId = container && container.getAttribute('data-wm-youtube-id');
  if (!videoId) return;

  var iframe = document.createElement('iframe');
  iframe.src = 'https://www.youtube-nocookie.com/embed/' + encodeURIComponent(videoId) + '?autoplay=1&rel=0&playsinline=1';
  iframe.title = button.getAttribute('aria-label') || 'Vídeo do YouTube';
  iframe.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
  iframe.allowFullscreen = true;
  iframe.referrerPolicy = 'strict-origin-when-cross-origin';
  container.replaceChildren(iframe);
});
