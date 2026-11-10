// mapa.js: desenha o mapa (SVG). Dois desenhos:
//  - 'hub': as séries como raios a partir do cruzamento (ou átrio), com a porta fechada;
//  - 'serie': o grafo de uma série. Eixos: para a direita = seguir; para baixo = aprofundar; para cima/direita = lado otimista,
//    para baixo/esquerda = lado sombrio. Mostra o bloco atual (anel), os visitados (cheios) e os por visitar (vazios).
// Pequeno (grande:false): estático e decorativo (o botão que o envolve abre o grande). Grande: cada nó é um botão para saltar.
// c = { modo, grande, mapaHub, layout, atualId, visitados:Set, aoNo(id), aoSerie(id), aoHub() }

const NS = 'http://www.w3.org/2000/svg';
function s(nome, atrs, filhos) {
  const e = document.createElementNS(NS, nome);
  for (const k in atrs) e.setAttribute(k, atrs[k]);
  if (filhos) filhos.forEach((f) => e.appendChild(f));
  return e;
}
function botao(rotulo, aoAtivar, filhos) {
  const g = s('g', { role: 'button', tabindex: '0', 'aria-label': rotulo, class: 'm-bt' }, filhos);
  g.addEventListener('click', (e) => { e.stopPropagation(); aoAtivar(); });
  g.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); e.stopPropagation(); aoAtivar(); } });
  return g;
}
const texto = (x, y, t, ancora, cls) => { const e = s('text', { x, y, class: cls, 'text-anchor': ancora }); e.textContent = t; return e; };
const CORES = { seguir: 'm-e-seguir', aprofundar: 'm-e-prof', subir: 'm-e-prof', otimista: 'm-e-otim', catastrofico: 'm-e-cata', museu: 'm-e-seguir' };

export function desenharMapa(svg, c) {
  svg.replaceChildren();
  if (c.modo === 'serie' && c.layout && c.layout.nos.length) desenhaSerie(svg, c); else desenhaHub(svg, c);
}

function desenhaSerie(svg, c) {
  const G = !!c.grande, L = c.layout;
  const W = G ? 420 : 200, H = G ? 320 : 200, P = G ? 36 : 16;
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  const DX = 60, DY = 62, PX = 20, PY = 20;
  const bruto = (n) => [n.col * DX + n.polo * PX, n.nivel * DY - n.polo * PY];
  const pts = L.nos.map(bruto);
  const x0 = Math.min(...pts.map((p) => p[0])), x1 = Math.max(...pts.map((p) => p[0]));
  const y0 = Math.min(...pts.map((p) => p[1])), y1 = Math.max(...pts.map((p) => p[1]));
  const esc = Math.min((W - 2 * P) / Math.max(1, x1 - x0), (H - 2 * P - (G ? 18 : 0)) / Math.max(1, y1 - y0), G ? 1.6 : 1.2);
  const ox = (W - (x1 - x0) * esc) / 2 - x0 * esc, oy = (H - (G ? 18 : 0) - (y1 - y0) * esc) / 2 - y0 * esc;
  const pos = new Map(L.nos.map((n) => { const b = bruto(n); return [n.id, [ox + b[0] * esc, oy + b[1] * esc]]; }));
  for (const a of L.arestas) {
    const [xa, ya] = pos.get(a.de), [xb, yb] = pos.get(a.para);
    svg.appendChild(s('line', { x1: xa, y1: ya, x2: xb, y2: yb, class: 'm-aresta ' + CORES[a.tipo] }));
  }
  const r = G ? 9 : 4.6;
  for (const n of L.nos) {
    const [x, y] = pos.get(n.id);
    const visto = c.visitados && c.visitados.has(n.id), aqui = n.id === c.atualId;
    const cls = 'm-no' + (visto ? ' m-visto' : '') + (n.polo > 0 ? ' m-pol-o' : n.polo < 0 ? ' m-pol-c' : '') + (aqui ? ' m-aqui' : '');
    const filhos = [s('circle', { cx: x, cy: y, r: aqui ? r * 1.35 : r, class: cls })];
    if (G) filhos.push(texto(x, y + 3.5, n.num, 'middle', 'm-num'));
    if (aqui) filhos.push(s('circle', { cx: x, cy: y, r: r * 1.35 + 4, class: 'm-voce', 'aria-hidden': 'true' }));
    if (G) {
      const t = s('title', {}); t.textContent = n.titulo; filhos.push(t, s('circle', { cx: x, cy: y, r: 14, class: 'm-toque' }));
      svg.appendChild(botao(`Bloco ${n.num}: ${n.titulo}${aqui ? ' (você está aqui)' : visto ? ' (já visitado)' : ''}`, () => c.aoNo(n.id), filhos));
    } else filhos.forEach((f) => svg.appendChild(f));
  }
  // eixos
  const ax = G ? 14 : 8, ay = H - (G ? 12 : 8);
  svg.appendChild(s('line', { x1: ax, y1: ay, x2: ax + (G ? 44 : 24), y2: ay, class: 'm-eixo' }));
  svg.appendChild(s('line', { x1: ax, y1: ay, x2: ax, y2: ay - (G ? 0 : 0), class: 'm-eixo' }));
  if (G) {
    svg.appendChild(texto(ax + 50, ay + 4, 'seguir', 'start', 'm-leg'));
    svg.appendChild(texto(W - 10, ay - 2, 'baixo: aprofundar · cima/direita: otimista · baixo/esquerda: sombrio', 'end', 'm-leg m-leg-p'));
  }
}

function desenhaHub(svg, c) {
  const G = !!c.grande, M = c.mapaHub;
  const L = G ? 400 : 200, C = L / 2, R0 = G ? 24 : 13, R1 = G ? 124 : 76;
  svg.setAttribute('viewBox', `0 0 ${L} ${L}`);
  const seno = (a) => Math.sin((a * Math.PI) / 180);
  const ponto = (ang, r) => [C + seno(ang) * r, C - Math.cos((ang * Math.PI) / 180) * r];
  for (const n of M.nos) {
    const atual = M.atual === n.id;
    const [x0, y0] = ponto(n.angulo, R0), [x1, y1] = ponto(n.angulo, n.fechada ? R0 + (R1 - R0) * 0.4 : R1);
    const cls = 'm-raio' + (atual ? ' m-atual' : '') + (n.fechada ? ' m-fechada' : '') + (n.mock ? ' m-mock' : '');
    svg.appendChild(s('line', { x1: x0, y1: y0, x2: x1, y2: y1, class: cls }));
    if (n.fechada) {
      svg.appendChild(s('rect', { x: x1 - 4, y: y1 - 4, width: 8, height: 8, class: 'm-cadeado' }));
      if (G) svg.appendChild(texto(x1 + (seno(n.angulo) >= 0 ? 10 : -10), y1 + 4, 'em breve', seno(n.angulo) >= 0 ? 'start' : 'end', 'm-rot'));
      continue;
    }
    if (!G) continue;
    const [tx, ty] = ponto(n.angulo, R1 + 16), dx = seno(n.angulo);
    const nome = n.titulo.length > 24 ? n.titulo.slice(0, 23) + '…' : n.titulo;
    svg.appendChild(texto(tx, ty + 4, nome, dx > 0.3 ? 'start' : dx < -0.3 ? 'end' : 'middle', 'm-rot' + (atual ? ' m-rot-atual' : '')));
    const [ex, ey] = ponto(n.angulo, R1 * 0.7);
    svg.appendChild(botao(`Corredor ${n.titulo}: entrar`, () => c.aoSerie(n.id), [s('circle', { cx: ex, cy: ey, r: 7, class: 'm-no m-visto' }), s('circle', { cx: ex, cy: ey, r: 16, class: 'm-toque' })]));
  }
  const hub = s('rect', { x: C - R0 * 0.62, y: C - R0 * 0.62, width: R0 * 1.24, height: R0 * 1.24, rx: 3, class: 'm-hub' + (M.atual ? '' : ' m-aqui') });
  if (G) svg.appendChild(botao(`${M.tipoHub === 'atrio' ? 'Átrio' : 'Cruzamento'}: ir ao centro`, () => c.aoHub(), [hub, s('circle', { cx: C, cy: C, r: R0 + 2, class: 'm-toque' })]));
  else svg.appendChild(hub);
}
