/* transicao.js — STAR-51, onda 7: o clima de cada transição. Vanilla, sem dependências, sem rede.
   Carrega-se SÍNCRONO no <head> (depois do transicao.css), para correr antes da primeira pintura.
   - pageswap (página que SAI): guarda o clima dela (data-clima do <html>) e a cor do fundo; escreve o type no ViewTransition.
   - pagereveal (página que ENTRA): lê o clima guardado e escreve o MESMO type, para a entrada usar o mesmo clima
     (as animações ::view-transition-* correm no documento novo, por isso é aqui que o type conta).
   - Sem View Transitions (ou ?semvt=1, que fica na sessão; ?semvt=0 limpa): navegação normal + html.vt-fallback (fundido ≤ 250 ms).
   Não intercepta cliques. */
(function () {
  'use strict';
  var H = document.documentElement, S = null;
  try { S = window.sessionStorage; } catch (_) { S = null; }
  function ler(k) { try { return S ? S.getItem(k) : null; } catch (_) { return null; } }
  function esc(k, v) { try { if (S) { if (v === null) S.removeItem(k); else S.setItem(k, v); } } catch (_) { /* sem sessão: segue sem guardar */ } }

  var m = /[?&]semvt=([01])(?:&|$)/.exec(location.search);
  if (m) esc('vt-semvt', m[1] === '1' ? '1' : null);
  var semvt = ler('vt-semvt') === '1';
  if (semvt) {
    var off = document.createElement('style');
    off.textContent = '@view-transition{navigation:none}';          // a última regra vence: esta página não participa
    (document.head || H).appendChild(off);
    H.classList.add('sem-vt');
  }

  var suporta = 'PageRevealEvent' in window && !semvt;
  if (!suporta) H.classList.add('vt-fallback');

  function clima() { if (H.dataset.envelope === 'base' && H.dataset.estilo === '3') return 'estelar'; return H.getAttribute('data-clima') || 'padrao'; }

  window.addEventListener('pageswap', function (e) {
    esc('vt-clima', clima());
    esc('vt-fundo', getComputedStyle(H).getPropertyValue('--vt-fundo').trim() || null);
    if (e.viewTransition) { try { e.viewTransition.types.add(clima()); } catch (_) { /* sem types */ } }
  });

  window.addEventListener('pagereveal', function (e) {
    var vt = e.viewTransition, c = ler('vt-clima') || 'padrao', ant = ler('vt-fundo');
    if (!vt) { H.classList.add('vt-fallback'); return; }
    try { vt.types.add(c); } catch (_) { /* sem types */ }
    if (ant) H.style.setProperty('--vt-fundo-ant', ant);
    function solta() { H.style.removeProperty('--vt-fundo-ant'); }
    vt.finished.then(solta, solta);
  });
}());
