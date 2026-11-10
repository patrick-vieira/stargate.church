// controlo.js: os gestos, traduzidos em AÇÕES do modelo. Não sabe de renderizador nem de posição.
// acoes: { avancar (seguir), recuar (voltar ao bloco anterior), virar(dir) (lado sombrio/otimista; no hub, escolhe a saída),
//          aprofundar, subir, voltar (Esc), mapa, ativar (Enter fora de um botão) }
// estado: { pausado(): bool, bloqueado(): bool, bordaAtiva(): bool }  (bloqueado = diálogo aberto: os gestos calam-se;
//          a borda da tela só vira no hub, para um passar de mouse nunca trocar de bloco)
// Gestos: roda/scroll, setas (↑ seguir, ↓ voltar, ←/→ lados), PageDown/PageUp (aprofundar/subir), arrastar (mouse ou toque),
// borda da tela (mouse, com espera, só no hub), toque, Enter, M, Esc.

const LIMIAR_RODA = 70;      // px acumulados para um passo
const INTERVALO_RODA = 300;  // ms entre passos (a inércia do trackpad não atropela o labirinto)
const LIMIAR_ARRASTO = 56;   // px
const BORDA = 56;            // px de cada lado
const ESPERA_BORDA = 600;    // ms de permanência para virar; repete a cada REPETE_BORDA
const REPETE_BORDA = 1100;

export function montarControlo(cena, acoes, estado) {
  const ouvintes = [];
  const on = (alvo, tipo, fn, opc) => { alvo.addEventListener(tipo, fn, opc); ouvintes.push(() => alvo.removeEventListener(tipo, fn, opc)); };

  // roda / scroll
  let acum = 0, ultimaRoda = 0, ultimoPasso = 0;
  on(cena, 'wheel', (e) => {
    if (estado.bloqueado() || e.target.closest?.('.hud')) return;
    e.preventDefault();
    const agora = performance.now();
    if (agora - ultimaRoda > 220) acum = 0;
    ultimaRoda = agora;
    acum += e.deltaY * (e.deltaMode === 1 ? 16 : e.deltaMode === 2 ? 400 : 1);
    if (Math.abs(acum) >= LIMIAR_RODA && agora - ultimoPasso >= INTERVALO_RODA) {
      (acum > 0 ? acoes.avancar : acoes.recuar)();
      ultimoPasso = agora; acum = 0;
    }
  }, { passive: false });

  // teclado
  on(document, 'keydown', (e) => {
    if (e.defaultPrevented || e.ctrlKey || e.metaKey || e.altKey) return;
    if (estado.bloqueado()) return;
    const alvo = e.target;
    if (alvo && (alvo.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(alvo.tagName))) return;
    const k = e.key;
    let feito = true;
    if (k === 'ArrowUp') acoes.avancar();
    else if (k === 'ArrowDown') acoes.recuar();
    else if (k === 'PageDown') acoes.aprofundar();
    else if (k === 'PageUp') acoes.subir();
    else if (k === 'ArrowLeft') acoes.virar(-1);
    else if (k === 'ArrowRight') acoes.virar(1);
    else if (k === 'Escape') acoes.voltar();
    else if (k === 'm' || k === 'M') acoes.mapa();
    else if (k === 'Enter' && (alvo === document.body || cena.contains(alvo) && !/^(BUTTON|A)$/.test(alvo.tagName))) acoes.ativar();
    else feito = false;
    if (feito) e.preventDefault();
  });
  // Nota: ArrowUp/ArrowDown na cena seguem/voltam (como a roda); Tab percorre as portas.

  // arrastar (mouse ou toque) e toque
  let p0 = null, arrastou = false;
  on(cena, 'pointerdown', (e) => {
    if (estado.bloqueado() || (e.pointerType === 'mouse' && e.button !== 0)) return;
    p0 = { x: e.clientX, y: e.clientY, id: e.pointerId }; arrastou = false;
    cena.classList.add('arrasta');
  });
  on(cena, 'pointermove', (e) => {
    if (p0 && p0.id === e.pointerId && Math.hypot(e.clientX - p0.x, e.clientY - p0.y) > 10) arrastou = true;
    borda(e);
  });
  const solta = (e) => {
    if (!p0 || p0.id !== e.pointerId) return;
    const dx = e.clientX - p0.x, dy = e.clientY - p0.y;
    p0 = null; cena.classList.remove('arrasta');
    if (estado.bloqueado()) return;
    if (Math.abs(dx) >= LIMIAR_ARRASTO && Math.abs(dx) > Math.abs(dy)) acoes.virar(dx < 0 ? 1 : -1);          // arrastar para a esquerda = olhar para a direita
    else if (Math.abs(dy) >= LIMIAR_ARRASTO && Math.abs(dy) > Math.abs(dx)) (dy < 0 ? acoes.avancar : acoes.recuar)(); // deslizar para cima = avançar
  };
  on(cena, 'pointerup', solta);
  on(cena, 'pointercancel', (e) => { if (p0 && p0.id === e.pointerId) { p0 = null; cena.classList.remove('arrasta'); } });
  // um arrasto não é um clique: engole o clique que se segue
  on(cena, 'click', (e) => { if (arrastou) { e.stopPropagation(); e.preventDefault(); arrastou = false; } }, true);

  // borda da tela (só mouse, só com movimento permitido)
  let lado = 0, desde = 0, ultimoVira = 0, temporizador = 0;
  function borda(e) {
    if (e.pointerType !== 'mouse' || p0 || estado.pausado() || estado.bloqueado() || !estado.bordaAtiva()) { parar(); return; }
    const r = cena.getBoundingClientRect();
    const l = e.clientX - r.left < BORDA ? -1 : r.right - e.clientX < BORDA ? 1 : 0;
    // o centro-baixo é HUD: a borda só conta na faixa do meio da cena
    const alturaOk = e.clientY - r.top > 80 && r.bottom - e.clientY > 160;
    if (!l || !alturaOk) { parar(); return; }
    if (l !== lado) { lado = l; desde = performance.now(); ultimoVira = 0; cena.dataset.borda = String(l); }
    if (!temporizador) temporizador = setInterval(tique, 120);
  }
  function tique() {
    const t = performance.now();
    if (!lado || estado.pausado() || estado.bloqueado() || !estado.bordaAtiva()) return parar();
    if (t - desde >= ESPERA_BORDA && t - ultimoVira >= REPETE_BORDA) { ultimoVira = t; acoes.virar(lado); }
  }
  function parar() { lado = 0; delete cena.dataset.borda; if (temporizador) { clearInterval(temporizador); temporizador = 0; } }
  on(cena, 'pointerleave', parar);

  return function desmontar() { parar(); ouvintes.forEach((f) => f()); ouvintes.length = 0; };
}
