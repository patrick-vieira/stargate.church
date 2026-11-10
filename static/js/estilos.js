/* Preferência em cookie próprio; a navegação por links funciona sem JavaScript. */
(function () {
  'use strict';
  if (document.documentElement.dataset.envelope !== 'base') return;
  var convite = document.querySelector('[data-convite-estilo]');
  var fechar = document.querySelector('[data-fechar-convite]');
  if (convite && fechar) {
    fechar.hidden = false;
    fechar.addEventListener('click', function () {
      document.cookie = 'stargate_convite=fechado; Path=/; Max-Age=31536000; SameSite=Lax' + (location.protocol === 'https:' ? '; Secure' : '');
      convite.hidden = true;
    });
  }
}());
