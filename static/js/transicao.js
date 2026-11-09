/* transicao.js — STAR-51, onda 7: o clima de cada transição. Vanilla, sem dependências, sem rede.
   Carrega-se SÍNCRONO no <head> (depois do transicao.css), para correr antes da primeira pintura.
   - pageswap (página que SAI): guarda o clima dela (data-clima do <html>) e a cor do fundo; escreve o type no ViewTransition.
   - pagereveal (página que ENTRA): lê o clima guardado e escreve o MESMO type, para a entrada usar o mesmo clima
     (as animações ::view-transition-* correm no documento novo, por isso é aqui que o type conta).
   - Sem View Transitions (ou ?semvt=1, que fica na sessão; ?semvt=0 limpa): navegação normal + html.vt-fallback (fundido ≤ 250 ms).
   - Registo para a prova: sessionStorage['vt-registro'] = [{u, vt, tipos, clima, anims, fim}]. Não intercepta cliques.
   - Só para a prova: sessionStorage['vt-k'] multiplica as durações (câmera lenta). */
(function () {
  'use strict';
  var H = document.documentElement, S = null;
  try { S = window.sessionStorage; } catch (_) { S = null; }
  function ler(k) { try { return S ? S.getItem(k) : null; } catch (_) { return null; } }
  function esc(k, v) { try { if (S) { if (v === null) S.removeItem(k); else S.setItem(k, v); } } catch (_) { /* sem sessão: segue sem registo */ } }

  var m = /[?&]semvt=([01])(?:&|$)/.exec(location.search);
  if (m) esc('vt-semvt', m[1] === '1' ? '1' : null);
  var semvt = ler('vt-semvt') === '1';
  if (semvt) {
    var off = document.createElement('style');
    off.textContent = '@view-transition{navigation:none}';          // a última regra vence: esta página não participa
    (document.head || H).appendChild(off);
    H.classList.add('sem-vt');
  }
  var k = parseFloat(ler('vt-k'));
  if (k > 0 && k !== 1) H.style.setProperty('--vt-k', String(k));

  var suporta = 'PageRevealEvent' in window && !semvt;
  if (!suporta) H.classList.add('vt-fallback');

  function clima() { return H.getAttribute('data-clima') || 'padrao'; }

  window.addEventListener('pageswap', function (e) {
    esc('vt-clima', clima());
    esc('vt-fundo', getComputedStyle(H).getPropertyValue('--vt-fundo').trim() || null);
    if (e.viewTransition) { try { e.viewTransition.types.add(clima()); } catch (_) { /* sem types */ } }
  });

  window.addEventListener('pagereveal', function (e) {
    var vt = e.viewTransition, c = ler('vt-clima') || 'padrao', ant = ler('vt-fundo');
    var reg = [], ent = { u: location.pathname + location.search, vt: !!vt, tipos: [], clima: c, anims: null, fim: null };
    try { reg = JSON.parse(ler('vt-registro') || '[]'); } catch (_) { reg = []; }
    reg.push(ent);
    if (!vt) {
      H.classList.add('vt-fallback');
      esc('vt-registro', JSON.stringify(reg));
      return;
    }
    try { vt.types.add(c); } catch (_) { /* sem types */ }
    if (ant) H.style.setProperty('--vt-fundo-ant', ant);
    ent.tipos = Array.from(vt.types);
    esc('vt-registro', JSON.stringify(reg));
    vt.ready.then(function () {
      var as = document.getAnimations(), fim = 0, n = 0;
      as.forEach(function (a) {
        var pe = a.effect && a.effect.pseudoElement ? String(a.effect.pseudoElement) : '';
        var t = pe.indexOf('::view-transition') === 0 && a.effect.getComputedTiming ? a.effect.getComputedTiming() : null;   // só as da transição
        if (t && t.duration > 0) { n++; if (t.endTime > fim) fim = t.endTime; }
      });
      ent.anims = n; ent.fim = Math.round(fim / (parseFloat(H.style.getPropertyValue('--vt-k')) || 1));
      ent.nome = getComputedStyle(H, '::view-transition-new(root)').animationName;
      esc('vt-registro', JSON.stringify(reg));
    }).catch(function () { ent.anims = -1; ent.fim = -1; esc('vt-registro', JSON.stringify(reg)); });
    vt.finished.then(function () { H.style.removeProperty('--vt-fundo-ant'); }, function () { H.style.removeProperty('--vt-fundo-ant'); });
  });
}());
