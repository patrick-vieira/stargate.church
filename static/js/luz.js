/* luz.js — STAR-51, onda 6: a luz e a névoa. Candidato a static/js/luz.js. Vanilla, sem dependências, sem rede.
   - UM listener pointermove por documento (passive), agrupado num requestAnimationFrame; mais um pointerdown (toque: a luz
     fica no último toque). Escreve --luz-x/--luz-y/--luz-nx/--luz-ny/--luz-i SÓ nos [data-luz] visíveis (IntersectionObserver).
   - Foco: o campo [data-luz=campo] ganha .luz--foco (a borda acende; o anel de foco AA vem do CSS, sem a luz).
   - Erro / sucesso: eventos luz:erro, luz:sucesso e luz:reset (ou Luz.erro(el), Luz.sucesso(el), Luz.reset(el)). A classe vai para
     o [data-luz=nevoa] mais próximo: .luz--erro + .luz--tremor (400 ms) / .luz--dissipa (600 ms). Tudo por classes.
   - Home: [data-luz=ceu] recebe data-fase (madrugada 0-5, manha 6-11, tarde 12-16, crepusculo 17-19, noite 20-23), pela hora do
     leitor ou por ?hora=HH.
   - reduced-motion: não segue o cursor (a luz fica nos padrões do CSS); as classes de erro/sucesso aplicam-se, sem animação. */
(function () {
  'use strict';
  var doc = document;
  var mq = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : { matches: false };
  var TREMOR_MS = 400, QUEDA = 240;
  var visiveis = new Set(), px = 0, py = 0, temPonto = false, raf = 0;

  function limita(v, a, b) { return v < a ? a : v > b ? b : v; }

  var io = 'IntersectionObserver' in window ? new IntersectionObserver(function (es) {
    es.forEach(function (e) { if (e.isIntersecting) visiveis.add(e.target); else visiveis.delete(e.target); });
    if (temPonto && !raf) raf = requestAnimationFrame(quadro);
  }, { rootMargin: '120px' }) : null;

  function liga(el) {
    if (el.__luz) return;
    el.__luz = 1;
    if (io) io.observe(el); else visiveis.add(el);
  }

  function quadro() {
    raf = 0;
    if (mq.matches) return;
    var lidos = [];
    visiveis.forEach(function (el) { lidos.push([el, el.getBoundingClientRect()]); });   // primeiro lê tudo...
    lidos.forEach(function (p) {                                                           // ...depois escreve tudo
      var el = p[0], r = p[1], w = Math.max(r.width, 1), h = Math.max(r.height, 1);
      var x = px - r.left, y = py - r.top;
      var dx = Math.max(0, Math.abs(x - w / 2) - w / 2), dy = Math.max(0, Math.abs(y - h / 2) - h / 2);
      var i = limita(1 - Math.hypot(dx, dy) / QUEDA, 0, 1);
      if (i === 0 && el.__i === 0) return;                 // longe e já apagado: nada a escrever
      el.__i = i;
      var s = el.style;
      s.setProperty('--luz-x', x.toFixed(1) + 'px');
      s.setProperty('--luz-y', y.toFixed(1) + 'px');
      s.setProperty('--luz-nx', limita((x - w / 2) / (w / 2), -1, 1).toFixed(3));
      s.setProperty('--luz-ny', limita((y - h / 2) / (h / 2), -1, 1).toFixed(3));
      s.setProperty('--luz-i', i.toFixed(3));
    });
  }

  function mover(e) {
    if (mq.matches) return;
    px = e.clientX; py = e.clientY; temPonto = true;
    if (!raf) raf = requestAnimationFrame(quadro);
  }
  doc.addEventListener('pointermove', mover, { passive: true });
  doc.addEventListener('pointerdown', mover, { passive: true });
  window.addEventListener('scroll', function () { if (temPonto && !raf) raf = requestAnimationFrame(quadro); }, { passive: true });

  function soltaTudo() {
    visiveis.forEach(function (el) {
      ['--luz-x', '--luz-y', '--luz-nx', '--luz-ny', '--luz-i'].forEach(function (k) { el.style.removeProperty(k); });
      el.__i = undefined;
    });
  }
  if (mq.addEventListener) mq.addEventListener('change', function () { if (mq.matches) soltaTudo(); });

  /* foco */
  function foco(e) {
    var c = e.target.closest && e.target.closest('[data-luz=campo]');
    if (!c) return;
    if (e.type === 'focusin') { if (e.target.matches(':focus-visible')) c.classList.add('luz--foco'); }
    else c.classList.remove('luz--foco');
  }
  doc.addEventListener('focusin', foco);
  doc.addEventListener('focusout', foco);

  /* erro / sucesso / reset */
  function nevoaDe(el) {
    return (el.closest && el.closest('[data-luz=nevoa]')) || (el.querySelector && el.querySelector('[data-luz=nevoa]')) || el;
  }
  doc.addEventListener('luz:erro', function (e) {
    var n = nevoaDe(e.target);
    n.classList.remove('luz--dissipa', 'luz--tremor');
    n.classList.add('luz--erro');
    void n.offsetWidth;                                       // reinicia a animação se já tremia
    n.classList.add('luz--tremor');
    clearTimeout(n.__tremor);
    n.__tremor = setTimeout(function () { n.classList.remove('luz--tremor'); }, TREMOR_MS + 80);
  });
  doc.addEventListener('luz:sucesso', function (e) {
    var n = nevoaDe(e.target);
    clearTimeout(n.__tremor);
    n.classList.remove('luz--erro', 'luz--tremor');
    n.classList.add('luz--dissipa');
  });
  doc.addEventListener('luz:reset', function (e) {
    var n = nevoaDe(e.target);
    n.classList.remove('luz--erro', 'luz--tremor', 'luz--dissipa');
  });
  function emite(nome) { return function (el) { el.dispatchEvent(new CustomEvent(nome, { bubbles: true })); }; }

  /* a home por hora do dia */
  var FASES = [['madrugada', 0, 5], ['manha', 6, 11], ['tarde', 12, 16], ['crepusculo', 17, 19], ['noite', 20, 23]];
  function horaAgora() {
    var m = /[?&]hora=(\d{1,2})(?:&|$)/.exec(window.location.search);
    if (m && +m[1] >= 0 && +m[1] <= 23) return { h: +m[1], fixa: true };
    return { h: new Date().getHours(), fixa: false };
  }
  function faseDe(h) { for (var k = 0; k < FASES.length; k++) if (h >= FASES[k][1] && h <= FASES[k][2]) return FASES[k][0]; return 'tarde'; }
  function ceu(el) {
    var t = horaAgora();
    el.setAttribute('data-fase', faseDe(t.h));
    if (!t.fixa) setInterval(function () { el.setAttribute('data-fase', faseDe(new Date().getHours())); }, 60000);
  }

  function inicia() {
    doc.querySelectorAll('[data-luz]').forEach(liga);
    doc.querySelectorAll('[data-luz=ceu]').forEach(ceu);
  }
  if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', inicia); else inicia();

  window.Luz = { liga: liga, erro: emite('luz:erro'), sucesso: emite('luz:sucesso'), reset: emite('luz:reset'), faseDe: faseDe };
})();
