/* carregando.js — STAR-51, onda 7: liga o esqueleto aos posts pesados. Vanilla, sem rede além do módulo local.
   Marcação: <div data-carrega="three|rive" [data-modulo="caminho/do/modulo.js"] [data-simula="MS"] [data-frase="…"] [data-frase-erro="…"] aria-busy="true">
   - Enquanto carrega: aria-busy=true e o esqueleto (.car-esq, criado aqui se faltar) cobre o contentor, que tem altura reservada.
   - Quando o módulo entra: dispara «carrega:pronto» no contentor (detail.modulo = o módulo; a página monta a cena, de forma síncrona,
     e se falhar põe detail.falhou = true). Depois: aria-busy sai e o esqueleto sai com um fundido (.car--pronto).
   - Se o import ou a montagem falhar: fica o esqueleto PARADO com uma frase (.car--erro), aria-busy sai. Nunca um buraco.
   - ?lento=MS atrasa o import em MS (para a prova); ?falha=1 força a falha (para a prova).
   - data-simula="MS" (sem data-modulo) simula um carregamento de MS.
   - Sem data-modulo nem data-simula: modo manual (o do repo); quem monta a cena chama Carregando.pronto(el) ou Carregando.erro(el). */
(function () {
  'use strict';
  var q = new URLSearchParams(window.location.search);
  var lento = Math.max(0, parseInt(q.get('lento'), 10) || 0);
  var falha = q.get('falha') === '1';

  function espera(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }

  function esqueleto(el) {
    var e = el.querySelector('.car-esq');
    if (e) return e;
    e = document.createElement('div');
    e.className = 'car-esq';
    e.setAttribute('role', 'status');
    e.innerHTML = '<i class="car-esq__forma"></i><i class="car-esq__forma"></i><i class="car-esq__forma"></i><p class="car-esq__txt"></p>';
    el.appendChild(e);
    return e;
  }

  function frase(el, texto) {
    var t = esqueleto(el).querySelector('.car-esq__txt');
    if (t) t.textContent = texto;
  }

  function pronto(el) {
    if (!el || el.classList.contains('car--erro')) return;
    el.removeAttribute('aria-busy');
    el.classList.add('car--pronto');
    el.dataset.carregaEstado = 'pronto';
  }

  function erro(el) {
    if (!el) return;
    el.removeAttribute('aria-busy');
    el.classList.add('car--erro');
    el.dataset.carregaEstado = 'erro';
    frase(el, el.getAttribute('data-frase-erro') || 'Não foi possível montar a cena agora. O texto continua aqui.');
  }

  function prepara(el) {
    el.setAttribute('aria-busy', 'true');
    frase(el, el.getAttribute('data-frase') || 'A cena está chegando…');
  }

  async function carrega(el) {
    prepara(el);
    if (!el.hasAttribute('data-modulo') && !el.hasAttribute('data-simula')) return;   // modo manual: quem monta chama Carregando.pronto/erro
    try {
      var modulo = null;
      if (lento) await espera(lento);
      if (el.getAttribute('data-modulo')) {
        var alvo = el.getAttribute('data-modulo');
        if (falha) alvo = alvo.replace(/[^/]*$/, 'nao-existe.js');
        modulo = await import(new URL(alvo, window.location.href).href);
      } else {
        await espera(parseInt(el.getAttribute('data-simula'), 10) || 0);
        if (falha) throw new Error('falha simulada');
      }
      var det = { modulo: modulo, tipo: el.getAttribute('data-carrega'), falhou: false };
      el.dispatchEvent(new CustomEvent('carrega:pronto', { bubbles: true, detail: det }));
      if (det.falhou) throw new Error('montagem');
      pronto(el);
    } catch (_) {
      erro(el);
    }
  }

  // Modo manual (o motor imersivo do repo carrega o three/Rive por conta própria): sem data-modulo nem data-simula este script só
  // mostra o esqueleto e deixa o efeito chamar Carregando.pronto(el) quando a cena estiver montada, ou Carregando.erro(el).
  // ?falha=1 também força a falha no modo manual (para a prova): o esqueleto fica parado com a frase de erro.
  window.Carregando = { pronto: pronto, erro: erro, lento: lento, falha: falha };

  function inicia() {
    Array.prototype.forEach.call(document.querySelectorAll('[data-carrega]'), function (el) {
      carrega(el);
      if (falha && !el.hasAttribute('data-modulo') && !el.hasAttribute('data-simula')) erro(el);
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', inicia); else inicia();
}());
