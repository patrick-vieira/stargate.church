/* STAR-76: os eventos nativos preservam links, histórico e navegação sem JS. */
(function () {
  'use strict';
  var html = document.documentElement;
  var movimento = window.matchMedia('(prefers-reduced-motion: reduce)');
  function ativa() {
    return html.dataset.envelope === 'base' && html.dataset.estilo === '3' &&
      !movimento.matches && !html.classList.contains('sem-vt');
  }
  if (!('PageSwapEvent' in window) || !('PageRevealEvent' in window)) return;

  function preparar() {
    if (!ativa() || document.querySelector('.sg-viagem-estrelas')) return;
    var estrelas = document.createElement('div');
    estrelas.className = 'sg-viagem-estrelas';
    estrelas.setAttribute('aria-hidden', 'true');
    // Distribuição determinística: as duas páginas fotografam o mesmo céu.
    for (var i = 0; i < 48; i++) {
      var estrela = document.createElement('i');
      var angulo = i * 137.508;
      var raio = 12 + (i * 17 % 60);
      estrela.style.setProperty('--angulo', angulo + 'deg');
      estrela.style.setProperty('--raio', raio + 'vmax');
      estrelas.appendChild(estrela);
    }
    document.body.appendChild(estrelas);
  }
  document.addEventListener('DOMContentLoaded', preparar);
  window.addEventListener('pageswap', function (evento) {
    if (!ativa() || !evento.viewTransition) return;
    // Sem types, fica a transição padrão já existente.
    if (evento.viewTransition.types) evento.viewTransition.types.add('viagem-estrelas');
  });
  window.addEventListener('pagereveal', function (evento) {
    if (!ativa() || !evento.viewTransition) return;
    preparar();
    if (evento.viewTransition.types) evento.viewTransition.types.add('viagem-estrelas');
  });
}());
