// render2d.js: o renderizador 2D. Canvas 2D com projeção em perspetiva escrita à mão (sem WebGL, sem CSS 3D): o chão, o teto
// e as paredes são polígonos projetados; os objetos são texturas desenhadas uma vez e coladas à parede em faixas (cada faixa com a
// perspetiva certa). Os objetos clicáveis são `button` reais sobrepostos ao canvas, com a forma do objeto (clip-path) e o nome completo.
//
// Interface (a mesma do render3d.js; ver ARQUITETURA.md):
//   montar(contentor, modelo, opc)  opc = { aoAtivar(alvo), aoFocar(alvo), pausado(): bool }
//   mostrar(posicao, {animar})      leva a câmara à posição do modelo ({no, ...}); o movimento (seguir, aprofundar, subir, polos...) vem de modelo.movimento
//   destacar(alvo|null, modo)       realce de uma porta: 'hover' | 'foco' | null
//   desmontar()
// «alvo» é uma escolha do bloco ({tipo, alvo, num, texto, no}, de modelo.escolhas) ou uma saída do hub (a saída tem .fechada).
// Cena de um bloco: um corredor curto. Seguir = a porta do fundo; lado sombrio = porta azul fria na parede esquerda; lado otimista =
// porta âmbar quente na parede direita; aprofundar / subir = arcos de pedra com seta mais adiante, à esquerda / direita. A cor do corredor
// segue o polo do bloco e o nível escurece-o. O texto do bloco vive num cartão HTML (app.js), não no canvas.

const rad = (d) => (d * Math.PI) / 180;
const PASSO = 2.2, LARG = 1.5, ALT = 1.5, Z_INI = -1.8, ALCANCE = 15, PERTO = 0.12;
const Z_POLO = 4.0, Z_NIVEL = 7.0, Z_FIM = 9.5;
const RAIO_HUB = 4.0;
const FOG = [7, 9, 13];
const BASE_PAL = {
  '0': { parede: [92, 68, 42], dado: [62, 44, 27], chao: [52, 39, 26], teto: [30, 37, 52], luz: [255, 214, 130], friso: [240, 170, 40] },     // neutro: madeira quente
  '1': { parede: [132, 94, 34], dado: [92, 63, 22], chao: [70, 50, 24], teto: [64, 46, 20], luz: [255, 204, 104], friso: [255, 196, 60] },    // otimista: âmbar quente
  '-1': { parede: [34, 54, 98], dado: [22, 36, 68], chao: [20, 30, 54], teto: [12, 20, 40], luz: [150, 192, 255], friso: [110, 160, 235] },  // catastrófico: azul frio
};
const paleta = (polo, nivel) => {
  const b = BASE_PAL[String(polo)] || BASE_PAL['0'], k = Math.max(0.5, 1 - 0.17 * nivel), mul = (c) => c.map((v) => v * k);
  return { parede: mul(b.parede), dado: mul(b.dado), chao: mul(b.chao), teto: mul(b.teto), luz: b.luz, friso: b.friso };
};
const PALETA_HUB = BASE_PAL['0'];

const mistura = (c, d, m = 1) => {
  const f = Math.min(1, Math.pow(Math.max(0, d - 1.2) / ALCANCE, 0.85)) * 0.93;
  return `rgb(${(c[0] * m * (1 - f) + FOG[0] * f) | 0},${(c[1] * m * (1 - f) + FOG[1] * f) | 0},${(c[2] * m * (1 - f) + FOG[2] * f) | 0})`;
};
const nevoa = (d) => Math.min(0.9, Math.pow(Math.max(0, d - 1.2) / ALCANCE, 0.85) * 0.93);
const suaviza = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
const dif = (t, c) => ((((t - c + Math.PI) % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI)) - Math.PI;   // caminho mais curto entre ângulos

// ---------- texturas ----------
function rr(ctx, x, y, w, h, r) { ctx.beginPath(); if (ctx.roundRect) ctx.roundRect(x, y, w, h, r); else ctx.rect(x, y, w, h); }
function linhas(ctx, texto, largMax, fonteBase, minimo, maxLinhas) {
  let tam = fonteBase, ls = [];
  for (; tam >= minimo; tam -= 2) {
    ctx.font = fonte(tam);
    ls = []; let atual = '';
    for (const p of texto.split(' ')) {
      const t = atual ? atual + ' ' + p : p;
      if (ctx.measureText(t).width > largMax && atual) { ls.push(atual); atual = p; } else atual = t;
    }
    ls.push(atual);
    if (ls.length <= maxLinhas && ls.every((l) => ctx.measureText(l).width <= largMax)) break;
  }
  return { ls, tam };
}
const fonte = (t) => `700 ${t}px Georgia, "Times New Roman", serif`;
function texto(ctx, t, cx, cy, largMax, base, min, maxL, cor) {
  const { ls, tam } = linhas(ctx, t, largMax, base, min, maxL);
  ctx.fillStyle = cor; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.font = fonte(tam);
  const h = tam * 1.18, y0 = cy - ((ls.length - 1) * h) / 2;
  ls.forEach((l, i) => ctx.fillText(l, cx, y0 + i * h));
}
function mono(ctx, t, x, y, tam, cor, alinh = 'center') {
  ctx.font = `700 ${tam}px ui-monospace, "SFMono-Regular", Menlo, monospace`; ctx.fillStyle = cor; ctx.textAlign = alinh; ctx.textBaseline = 'middle';
  ctx.fillText(t.toUpperCase(), x, y);
}
function tela(w, h) { const c = document.createElement('canvas'); c.width = w; c.height = h; return [c, c.getContext('2d')]; }

function texEscolha(e, larg) {
  const E = 200, dim = [larg, 2.1], w = Math.round(dim[0] * E), h = Math.round(dim[1] * E);
  const [c, x] = tela(w, h);
  const t = e.tipo, ehPolo = t === 'otimista' || t === 'catastrofico', ehNivel = t === 'aprofundar' || t === 'subir';
  const cor = t === 'otimista' ? ['#a8741c', '#e8b13e'] : t === 'catastrofico' ? ['#1b2f5e', '#3a5ea8'] : ehNivel ? ['#3d424d', '#5a606d'] : ['#8c5430', '#b57440'];
  const g = x.createLinearGradient(0, 0, w, 0); g.addColorStop(0, cor[0]); g.addColorStop(0.5, cor[1]); g.addColorStop(1, cor[0]);
  x.fillStyle = g; x.beginPath(); x.moveTo(0, h); x.lineTo(0, 70); x.quadraticCurveTo(0, 0, w / 2, 0); x.quadraticCurveTo(w, 0, w, 70); x.lineTo(w, h); x.fill();
  x.strokeStyle = t === 'catastrofico' ? '#9fc2ff' : '#f5a30c'; x.lineWidth = 6; x.stroke();
  x.fillStyle = '#00000030'; rr(x, 22, 96, w - 44, h - 130, 10); x.fill();
  mono(x, e.rotulo, w / 2, 56, larg > 1.5 ? 18 : 15, t === 'catastrofico' ? '#dbe8ff' : '#ffe9a8');
  x.fillStyle = t === 'catastrofico' ? '#eaf1ff' : '#fff4d0'; x.font = '700 ' + Math.round(w * 0.42) + 'px Georgia, serif'; x.textAlign = 'center'; x.textBaseline = 'middle';
  x.fillText(e.num, w / 2, h * 0.43);
  const sim = ehNivel ? (t === 'aprofundar' ? '↓' : '↑') : ehPolo ? (t === 'otimista' ? '☀' : '☾') : '→';
  x.font = '700 ' + Math.round(w * 0.22) + 'px Georgia, serif'; x.fillText(sim, w / 2, h * 0.64);
  texto(x, e.no.titulo.replace('[MOCK] ', ''), w / 2, h * 0.82, w - 50, 22, 12, 3, t === 'catastrofico' ? '#eaf1ff' : '#fff4d0');
  return { c, w, h, dimMundo: dim };
}
function texPlaca(titulo, kicker, larg, alt, mock) {
  const E = 200, w = Math.round(larg * E), h = Math.round(alt * E);
  const [c, x] = tela(w, h);
  x.fillStyle = '#0b0e13'; x.fillRect(0, 0, w, h);
  x.strokeStyle = '#f5a30c'; x.lineWidth = 4; x.strokeRect(3, 3, w - 6, h - 6);
  mono(x, kicker, w / 2, 20, 14, '#f5a30c');
  texto(x, titulo, w / 2, h * 0.64, w - 30, 38, 16, 2, '#f1e9d2');
  return { c, w, h, dimMundo: [larg, alt] };
}
function texPortaSaida(saida, tema) {
  const E = 200, dim = [1.7, 2.1], w = Math.round(dim[0] * E), h = Math.round(dim[1] * E);
  const [c, x] = tela(w, h);
  const fechada = saida.fechada;
  const base = fechada ? ['#2c3038', '#3a3f49'] : [['#8c5430', '#b57440'], ['#34507a', '#4a6fa5'], ['#7a3a40', '#a8525a']][tema % 3];
  const g = x.createLinearGradient(0, 0, w, 0); g.addColorStop(0, base[0]); g.addColorStop(0.5, base[1]); g.addColorStop(1, base[0]);
  x.fillStyle = g; x.beginPath(); x.moveTo(0, h); x.lineTo(0, 70); x.quadraticCurveTo(0, 0, w / 2, 0); x.quadraticCurveTo(w, 0, w, 70); x.lineTo(w, h); x.fill();
  x.strokeStyle = fechada ? '#8a8f99' : '#f5a30c'; x.lineWidth = 6; x.stroke();
  x.fillStyle = '#00000030'; rr(x, 34, 90, w - 68, h - 130, 10); x.fill();
  if (fechada) {                                    // cadeado
    x.strokeStyle = '#c9ced6'; x.lineWidth = 9; x.beginPath(); x.arc(w / 2, h * 0.5, 30, Math.PI, 0); x.stroke();
    x.fillStyle = '#c9ced6'; rr(x, w / 2 - 44, h * 0.5, 88, 66, 8); x.fill(); x.fillStyle = '#2c3038'; x.beginPath(); x.arc(w / 2, h * 0.5 + 30, 8, 0, 7); x.fill();
  } else {
    x.fillStyle = '#f5a30c'; x.beginPath(); x.arc(w - 50, h * 0.58, 11, 0, 7); x.fill();
    mono(x, saida.tipo === 'noticias' ? 'notícias' : 'série', w / 2, 62, 17, '#ffe9a8');
    mono(x, saida.passos + (saida.tipo === 'noticias' ? ' notícias' : ' episódios'), w / 2, h * 0.5, 16, '#ffe9a8');
    x.fillStyle = '#ffe9a8'; x.font = `700 70px Georgia, serif`; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText('→', w / 2, h * 0.7);
  }
  return { c, w, h, dimMundo: dim };
}

// ---------- o renderizador ----------
export function criarRender2d() {
  let modelo = null, opc = null, host = null, canvas = null, ctx = null, camada = null;
  let W = 0, H = 0, F = 1, R = 1;
  let cenaId = null, cena = null, posAtual = null, olhado = null, dest = null;
  let cam = { yaw: 0, z: 0, d: 0 }, veu = 0, anim = null, raf = 0, pendente = false;
  let cs = 1, sn = 0, cx = 0, cz = 0, cy = 0;
  const botoes = new Map();
  const medidas = [];
  let ouvResize = null;

  const pausado = () => !!(opc && opc.pausado && opc.pausado());

  // ----- projeção -----
  function p3(x, y, z) {                         // -> [sx, sy, zr] (zr = profundidade na câmara)
    const dx = x - cx, dz = z - cz;
    const xr = dx * cs - dz * sn, zr = dx * sn + dz * cs;
    return [W / 2 + (xr / zr) * F, H / 2 + ((y - cy) / zr) * F, zr, xr];
  }
  function cam3(x, y, z) { const dx = x - cx, dz = z - cz; return [dx * cs - dz * sn, y - cy, dx * sn + dz * cs]; }
  function poligono(pts, cor) {                  // pts: [[x,y,z]...] em mundo; recorta no plano próximo
    const c = pts.map((p) => cam3(p[0], p[1], p[2]));
    const o = [];
    for (let i = 0; i < c.length; i++) {
      const a = c[i], b = c[(i + 1) % c.length];
      const ina = a[2] > PERTO, inb = b[2] > PERTO;
      if (ina) o.push(a);
      if (ina !== inb) { const t = (PERTO - a[2]) / (b[2] - a[2]); o.push([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, PERTO]); }
    }
    if (o.length < 3) return false;
    ctx.beginPath();
    for (let i = 0; i < o.length; i++) { const sx = W / 2 + (o[i][0] / o[i][2]) * F, sy = H / 2 + (o[i][1] / o[i][2]) * F; i ? ctx.lineTo(sx, sy) : ctx.moveTo(sx, sy); }
    ctx.fillStyle = cor; ctx.fill();
    return true;
  }
  const dist = (x, z) => Math.hypot(x - cx, z - cz);

  // ----- construção das cenas -----
  function montaHub() {
    const m = modelo, N = Math.round(360 / m.passoAngulo), apot = RAIO_HUB, meia = apot * Math.tan(Math.PI / N);
    const quads = [], paineis = [];
    for (let j = 0; j < N; j++) {
      const f = rad(j * m.passoAngulo), s = Math.sin(f), c = Math.cos(f);
      const centro = [apot * s, apot * c], dir = [c, -s];
      paineis.push({ centro, dir, meia, a: [centro[0] - dir[0] * meia, centro[1] - dir[1] * meia], b: [centro[0] + dir[0] * meia, centro[1] + dir[1] * meia] });
      const saida = m.saidas[j];
      if (!saida) continue;
      const tema = saida.fechada ? 0 : (m.porId.get(saida.id) || {}).tema | 0;
      quads.push({ tipo: 'tex', alvo: saida, tex: texPortaSaida(saida, tema), centro, dir, larg: 1.7, y0: ALT - 2.1, y1: ALT, id: 'porta-' + saida.id });
      const kick = saida.fechada ? 'porta fechada' : saida.tipo === 'noticias' ? 'galeria' : 'corredor';
      quads.push({ tipo: 'tex', tex: texPlaca(saida.titulo, kick, 1.7, 0.5), centro, dir, larg: 1.7, y0: ALT - 2.1 - 0.62, y1: ALT - 2.1 - 0.12, id: 'placa-' + saida.id });
    }
    return { tipo: 'hub', quads, paineis, N };
  }
  function montaNo(pos) {
    const n = modelo.noDe(pos), es = modelo.escolhas(pos), quads = [];
    const E = (t) => es.find((e) => e.tipo === t);
    const porta = (e, centro, dir, larg, z) => quads.push({ tipo: 'tex', alvo: e, tex: texEscolha(e, larg), centro, dir, larg, y0: ALT - 2.1, y1: ALT, id: 'esc-' + e.tipo });
    if (E('seguir')) porta(E('seguir'), [0, Z_FIM], [1, 0], 1.7);
    else {
      const [cv, x] = tela(340, 200); x.fillStyle = '#0b0e13'; x.fillRect(0, 0, 340, 200); x.strokeStyle = '#f5a30c'; x.lineWidth = 3; x.strokeRect(6, 6, 328, 188);
      mono(x, 'sem passagem em frente', 170, 84, 18, '#f5a30c'); mono(x, 'escolha uma porta ou volte', 170, 124, 14, '#f1e9d2');
      quads.push({ tipo: 'tex', tex: { c: cv, w: 340, h: 200, dimMundo: [3, 1.8] }, centro: [0, Z_FIM], dir: [1, 0], larg: 2.4, y0: -0.9, y1: 0.7, id: 'fim' });
    }
    if (E('catastrofico')) porta(E('catastrofico'), [-LARG, Z_POLO], [0, 1], 1.3);
    if (E('otimista')) porta(E('otimista'), [LARG, Z_POLO], [0, -1], 1.3);
    if (E('aprofundar')) porta(E('aprofundar'), [-LARG, Z_NIVEL], [0, 1], 1.3);
    if (E('subir')) porta(E('subir'), [LARG, Z_NIVEL], [0, -1], 1.3);
    const lado = n.polo > 0 ? 'lado otimista' : n.polo < 0 ? 'lado sombrio' : 'bloco';
    quads.push({ tipo: 'tex', tex: texPlaca('Bloco ' + n.num, 'nível ' + n.nivel + ' · ' + lado, 1.5, 0.5), centro: [-LARG, 1.1], dir: [0, 1], larg: 1.5, y0: -0.75, y1: -0.25, id: 'placa' });
    const sala = modelo.grafo?.salas?.find(s => s.id === n.sala);
    const pal = paleta(n.polo,n.nivel);
    if (sala) {
      const rgb = hex => hex.match(/[a-f0-9]{2}/gi).map(x => parseInt(x,16));
      pal.parede = rgb(sala.tema.cor); pal.dado = pal.parede.map(x => x * .6);
      pal.chao = pal.parede.map(x => x * .4); pal.luz = rgb(sala.tema.luz); pal.friso = pal.luz;
    }
    document.documentElement.style.setProperty('--sala-cor',sala?.tema.cor || '#916239');
    return { tipo: 'no', n, quads, pal, sala };
  }
  function definirCena(p) {
    cenaId = p.no;
    cena = p.no === 'hub' ? montaHub() : montaNo(p);
    criarBotoes();
  }

  // ----- botões (os objetos clicáveis, acessíveis) -----
  function criarBotoes() {
    camada.replaceChildren(); botoes.clear();
    for (const q of cena.quads) {
      if (!q.alvo) continue;
      const a = q.alvo, b = document.createElement('button');
      b.type = 'button'; b.className = 'alvo'; b.dataset.id = q.id; if (a.tipo) b.dataset.tipo = a.tipo;
      if (a.alvo !== undefined) b.tabIndex = -1;       // as portas de um bloco têm o equivalente no cartão (botões de escolha): só o cartão é parada do Tab
      if (a.fechada !== undefined) {
        b.setAttribute('aria-label', a.fechada ? 'Porta fechada: em breve, a próxima série' : a.tipo === 'noticias' ? 'Entrar no corredor das notícias' : `Entrar no corredor da série ${a.titulo}`);
        if (a.fechada) b.setAttribute('aria-disabled', 'true');
      } else {
        b.setAttribute('aria-label', `${a.texto}. ${a.no.titulo}`);
      }
      b.addEventListener('click', () => opc.aoAtivar(a));
      b.addEventListener('focus', () => { opc.aoFocar && opc.aoFocar(a); destacar(a, 'foco'); });
      b.addEventListener('blur', () => { if (dest && dest.alvo === a && dest.modo === 'foco') destacar(null); });
      b.addEventListener('pointerenter', () => destacar(a, 'hover'));
      b.addEventListener('pointerleave', () => { if (dest && dest.alvo === a && dest.modo === 'hover') destacar(null); });
      camada.appendChild(b); botoes.set(q, b);
    }
  }
  function posicionaBotoes() {
    for (const [q, b] of botoes) {
      const k = q.cantos;
      let css = 'left:0;top:0;width:1px;height:1px;opacity:0;pointer-events:none;clip-path:none';
      if (k) {
        const xs = k.map((p) => p[0]), ys = k.map((p) => p[1]);
        const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
        if (x1 > 0 && x0 < W && y1 > 0 && y0 < H && x1 - x0 > 8 && y1 - y0 > 8) {
          const poly = k.map((p) => `${(p[0] - x0).toFixed(1)}px ${(p[1] - y0).toFixed(1)}px`).join(',');
          css = `left:${x0.toFixed(1)}px;top:${y0.toFixed(1)}px;width:${(x1 - x0).toFixed(1)}px;height:${(y1 - y0).toFixed(1)}px;clip-path:polygon(${poly})`;
        }
      }
      if (q.css !== css) { q.css = css; b.style.cssText = css; }
    }
  }

  // ----- desenho de um quad com textura (faixas com a perspetiva certa) -----
  function desenhaQuad(q) {
    q.cantos = null;
    const [dx, dz] = q.dir, hw = q.larg / 2, [mx, mz] = q.centro;
    const ax = mx - dx * hw, az = mz - dz * hw, bx = mx + dx * hw, bz = mz + dz * hw;
    const cantos = [p3(ax, q.y0, az), p3(bx, q.y0, bz), p3(bx, q.y1, bz), p3(ax, q.y1, az)];
    if (cantos.some((p) => p[2] <= PERTO)) return;
    q.cantos = cantos;
    const d = dist(mx, mz);
    const larguraPx = Math.max(Math.abs(cantos[1][0] - cantos[0][0]), Math.abs(cantos[2][0] - cantos[3][0]));
    const K = Math.max(3, Math.min(28, Math.ceil(larguraPx / 18)));
    const t = q.tex, sw = t.w / K;
    const topo = [], base = [];
    for (let i = 0; i <= K; i++) { const u = i / K, x = ax + (bx - ax) * u, z = az + (bz - az) * u; topo.push(p3(x, q.y0, z)); base.push(p3(x, q.y1, z)); }
    for (let i = 0; i < K; i++) {
      const A = topo[i], B = topo[i + 1], D = base[i];
      ctx.setTransform((R * (B[0] - A[0])) / sw, (R * (B[1] - A[1])) / sw, (R * (D[0] - A[0])) / t.h, (R * (D[1] - A[1])) / t.h, R * A[0], R * A[1]);
      ctx.drawImage(t.c, i * sw, 0, sw, t.h, 0, 0, sw + 0.8, t.h);
    }
    ctx.setTransform(R, 0, 0, R, 0, 0);
    const f = Math.min(0.4, nevoa(d));
    if (f > 0.02) { ctx.beginPath(); cantos.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]))); ctx.closePath(); ctx.fillStyle = `rgba(${FOG[0]},${FOG[1]},${FOG[2]},${f * 0.85})`; ctx.fill(); }
    // realces
    const eDest = dest && dest.alvo === q.alvo ? dest : null;
    const eOlhado = q.alvo && olhado === q.alvo;
    if (q.alvo && (eDest || eOlhado)) {
      ctx.beginPath(); cantos.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]))); ctx.closePath();
      ctx.lineJoin = 'round';
      if (eDest && eDest.modo === 'foco') { ctx.lineWidth = 9; ctx.strokeStyle = '#ffffff'; ctx.stroke(); ctx.lineWidth = 5; ctx.strokeStyle = '#2f7bff'; ctx.stroke(); }
      else if (eDest) { ctx.lineWidth = 8; ctx.strokeStyle = 'rgba(245,163,12,.35)'; ctx.stroke(); ctx.lineWidth = 4; ctx.strokeStyle = '#f5a30c'; ctx.stroke(); ctx.fillStyle = 'rgba(255,214,130,.14)'; ctx.fill(); }
      else { ctx.lineWidth = 3; ctx.strokeStyle = 'rgba(245,163,12,.8)'; ctx.stroke(); }
    }
  }

  // ----- cenas -----
  function desenhaCorredor() {
    const { pal, quads } = cena;
    const seg = PASSO / (cena.sala?.tema.textura === 'grelha' ? 12 : cena.sala?.tema.textura === 'paineis' ? 2 : 4), z0 = Z_INI, z1 = Z_FIM + 0.4;
    for (let z = z0; z < z1 - 1e-6; z += seg) {
      const za = z, zb = Math.min(z + seg, z1), zm = (za + zb) / 2;
      const dm = dist(0, zm);
      if (Math.abs(zm - cz) > ALCANCE + 1) continue;
      const fase = (zm - PASSO * Math.round(zm / PASSO)) / (PASSO * 0.34);
      const luz = 0.78 + 0.5 * Math.exp(-fase * fase);                 // poça de luz sob cada lâmpada
      const alt = (Math.round((za - z0) / seg) % 2) * 0.18;
      poligono([[-LARG, ALT, za], [LARG, ALT, za], [LARG, ALT, zb], [-LARG, ALT, zb]], mistura(pal.chao, dm, luz));
      poligono([[-LARG, -ALT, za], [LARG, -ALT, za], [LARG, -ALT, zb], [-LARG, -ALT, zb]], mistura(pal.teto, dm, 0.9 + luz * 0.2));
      for (const lado of [-1, 1]) {
        const x = lado * LARG;
        poligono([[x, ALT, za], [x, 0.5, za], [x, 0.5, zb], [x, ALT, zb]], mistura(pal.dado, dm, luz + alt));
        poligono([[x, 0.5, za], [x, -ALT, za], [x, -ALT, zb], [x, 0.5, zb]], mistura(pal.parede, dm, luz + alt));
        poligono([[x, 0.5, za], [x, 0.44, za], [x, 0.44, zb], [x, 0.5, zb]], mistura(pal.friso, dm, 1.0));   // friso
      }
    }
    for (let k = 0; k <= 4; k++) {                                    // lâmpadas no teto, na cor do polo
      const z = k * PASSO, dm = dist(0, z);
      poligono([[-0.5, -ALT + 0.01, z - 0.28], [0.5, -ALT + 0.01, z - 0.28], [0.5, -ALT + 0.01, z + 0.28], [-0.5, -ALT + 0.01, z + 0.28]], mistura(pal.luz, dm, 1.15));
    }
    poligono([[-LARG, -ALT, Z_INI], [LARG, -ALT, Z_INI], [LARG, ALT, Z_INI], [-LARG, ALT, Z_INI]], mistura(pal.friso, 1, 0.6));
    poligono([[-LARG, -ALT, Z_FIM + 0.4], [LARG, -ALT, Z_FIM + 0.4], [LARG, ALT, Z_FIM + 0.4], [-LARG, ALT, Z_FIM + 0.4]], mistura(pal.dado, dist(0, Z_FIM), 0.8));
    const ord = quads.slice().sort((a, b) => dist(b.centro[0], b.centro[1]) - dist(a.centro[0], a.centro[1]));
    for (const q of ord) desenhaQuad(q);
  }
  function desenhaHub() {
    const { paineis, quads, N } = cena;
    const pal = PALETA_HUB;
    for (let j = 0; j < N; j++) {
      const p = paineis[j], a = p.a, b = p.b;
      const dm = dist(p.centro[0], p.centro[1]);
      poligono([[0, ALT, 0], [a[0], ALT, a[1]], [b[0], ALT, b[1]]], mistura(pal.chao, Math.max(dm, 2.5), 1.05 + (j % 2) * 0.05));
      poligono([[0, -ALT, 0], [a[0], -ALT, a[1]], [b[0], -ALT, b[1]]], mistura(pal.teto, dm, 1.0));
      poligono([[a[0], ALT, a[1]], [a[0], 0.5, a[1]], [b[0], 0.5, b[1]], [b[0], ALT, b[1]]], mistura(pal.dado, dm, 0.95));
      poligono([[a[0], 0.5, a[1]], [a[0], -ALT, a[1]], [b[0], -ALT, b[1]], [b[0], 0.5, b[1]]], mistura(pal.parede, dm, 0.95 + (j % 2) * 0.05));
      poligono([[a[0], 0.5, a[1]], [a[0], 0.44, a[1]], [b[0], 0.44, b[1]], [b[0], 0.5, b[1]]], mistura([240, 170, 40], dm, 1.0));
    }
    // o cruzamento: anel de luz no chão e lâmpada redonda no teto
    const anel = (y, r, cor) => poligono(Array.from({ length: 24 }, (_, i) => [Math.sin((i / 24) * 2 * Math.PI) * r, y, Math.cos((i / 24) * 2 * Math.PI) * r]), cor);
    anel(ALT - 0.005, 1.1, 'rgba(255,214,130,.20)'); anel(ALT - 0.004, 0.55, 'rgba(255,214,130,.28)');
    anel(-ALT + 0.01, 0.9, 'rgb(255,226,150)');
    const ord = quads.slice().sort((a, b) => dist(b.centro[0], b.centro[1]) - dist(a.centro[0], a.centro[1]));
    for (const q of ord) desenhaQuad(q);
  }

  function desenhar() {
    raf = 0; pendente = false;
    if (!ctx) return;
    const t0 = performance.now();
    ctx.setTransform(R, 0, 0, R, 0, 0);
    ctx.fillStyle = `rgb(${FOG[0]},${FOG[1]},${FOG[2]})`; ctx.fillRect(0, 0, W, H);
    cs = Math.cos(cam.yaw); sn = Math.sin(cam.yaw); cy = cam.y || 0;
    if (cena.tipo === 'hub') { const dir = cam.dir == null ? cam.yaw : cam.dir; cx = Math.sin(dir) * cam.d; cz = Math.cos(dir) * cam.d; desenhaHub(); }
    else { cx = 0; cz = cam.z; desenhaCorredor(); }
    if (veu > 0.001) { ctx.fillStyle = `rgba(${FOG[0]},${FOG[1]},${FOG[2]},${Math.min(1, veu)})`; ctx.fillRect(0, 0, W, H); }
    posicionaBotoes();
    medidas.push(performance.now() - t0); if (medidas.length > 900) medidas.shift();
  }
  function pedir() { if (!pendente) { pendente = true; raf = requestAnimationFrame(desenhar); } }

  // ----- animação -----
  function correr(dur, passo, fim) {
    cancelar();
    const t0 = performance.now();
    const quadro = (agora) => {
      const t = Math.min(1, (agora - t0) / dur);
      passo(suaviza(t));
      desenhar();
      if (t < 1) anim = requestAnimationFrame(quadro); else { anim = null; fim && fim(); }
    };
    anim = requestAnimationFrame(quadro);
  }
  function cancelar() { if (anim) { cancelAnimationFrame(anim); anim = null; } }

  function alvoCam(p) {
    if (p.no === 'hub') return { yaw: rad(modelo.anguloSaida(p.olhar)), z: 0, d: 0, y: 0 };
    return { yaw: 0, z: 0, d: 0, y: 0 };
  }
  // para cada movimento: [como a câmara sai da cena velha, de onde parte na cena nova]
  const SAIDA = {
    seguir: { z: Z_FIM * 0.8 }, aprofundar: { y: 1.0, z: 2.2 }, subir: { y: -1.0, z: 2.2 },
    otimista: { yaw: 0.55, z: Z_POLO }, catastrofico: { yaw: -0.55, z: Z_POLO },
  };
  const CHEGADA = {
    seguir: { z: -1.0 }, aprofundar: { y: -1.0 }, subir: { y: 1.0 }, otimista: { yaw: -0.4, z: -0.6 }, catastrofico: { yaw: 0.4, z: -0.6 },
  };
  const INV = { 'inv-seguir': 'seguir', 'inv-aprofundar': 'aprofundar', 'inv-subir': 'subir', 'inv-otimista': 'otimista', 'inv-catastrofico': 'catastrofico' };

  function mostrar(p, o = {}) {
    const antes = posAtual;
    posAtual = p; olhado = p.no === 'hub' ? modelo.saidaEm(p) : null;
    const alvo = alvoCam(p);
    const animar = o.animar !== false && !pausado() && cena;
    if (!animar) {
      cancelar(); veu = 0;
      if (cenaId !== p.no || p.no !== 'hub') definirCena(p);
      cam = { ...alvo, dir: alvo.yaw }; desenhar(); return;
    }
    const ini = { yaw: cam.yaw, z: cam.z || 0, d: cam.d || 0, y: cam.y || 0 };
    if (cenaId === 'hub' && p.no === 'hub') {          // hub: vira
      const dyaw = dif(alvo.yaw, ini.yaw), yaw0 = ini.yaw;
      correr(Math.min(900, 300 + Math.abs(dyaw) * 140), (t) => { cam = { yaw: yaw0 + dyaw * t, z: 0, d: 0, y: 0, dir: yaw0 + dyaw * t }; veu = veu * (1 - t); });
      return;
    }
    const mov = antes ? modelo.movimento(antes, p) : 'salto';
    const deHub = cenaId === 'hub', paraHub = p.no === 'hub', v0 = veu;
    const saida = mov === 'hub-no' || paraHub ? null : SAIDA[mov] || (INV[mov] ? { z: -1.2 } : null);
    const chegada = mov === 'hub-no' ? { z: -1.2 } : paraHub ? null : CHEGADA[mov] || (INV[mov] ? { z: 1.0 } : null);
    correr(230, (t) => {
      veu = v0 + (1 - v0) * t;
      if (deHub) cam = { yaw: ini.yaw, z: 0, d: ini.d + t * RAIO_HUB * 0.55, y: 0, dir: ini.yaw };
      else {
        const s = saida || { z: paraHub ? -1.2 : 0 };
        cam = { yaw: ini.yaw + (s.yaw || 0) * t, z: ini.z + (s.z || 0) * t, d: 0, y: ini.y + (s.y || 0) * t };
      }
    }, () => {
      definirCena(p);
      const c0 = paraHub ? { yaw: alvo.yaw, z: 0, d: RAIO_HUB * 0.5, y: 0, dir: alvo.yaw }
        : { yaw: (chegada && chegada.yaw) || 0, z: (chegada && chegada.z) || 0, d: 0, y: (chegada && chegada.y) || 0 };
      cam = { ...c0 };
      correr(300, (t) => {
        veu = 1 - t;
        cam = { yaw: c0.yaw * (1 - t) + alvo.yaw * t, z: c0.z * (1 - t), d: (c0.d || 0) * (1 - t), y: c0.y * (1 - t), dir: alvo.yaw };
      }, () => { veu = 0; desenhar(); });
    });
  }

  function destacar(alvo, modo) {
    const novo = alvo ? { alvo, modo: modo || 'hover' } : null;
    if ((dest && dest.alvo) === (novo && novo.alvo) && (dest && dest.modo) === (novo && novo.modo)) return;
    dest = novo; if (!anim) pedir();
  }

  function medir() {
    const r = host.getBoundingClientRect();
    W = Math.max(1, Math.round(r.width)); H = Math.max(1, Math.round(r.height));
    const lim = 1500 / Math.max(W, H);                    // resolução limitada: no máx. ~1500 px no lado maior
    R = Math.max(0.5, Math.min(window.devicePixelRatio || 1, 1.5, lim));
    canvas.width = Math.round(W * R); canvas.height = Math.round(H * R);
    F = W / 2 / Math.tan(rad(W < H ? 32 : 34));
    for (const q of cena ? cena.quads : []) q.css = null;
    if (cena) desenhar();
  }

  function montar(contentor, m, o) {
    modelo = m; opc = o; host = contentor;
    canvas = document.createElement('canvas'); canvas.className = 'palco'; canvas.setAttribute('aria-hidden', 'true');
    camada = document.createElement('div'); camada.className = 'alvos';
    host.prepend(camada); host.prepend(canvas);
    ctx = canvas.getContext('2d', { alpha: false });
    medir();
    ouvResize = () => medir();
    window.addEventListener('resize', ouvResize);
  }
  function desmontar() {
    cancelar(); if (raf) cancelAnimationFrame(raf);
    window.removeEventListener('resize', ouvResize);
    canvas && canvas.remove(); camada && camada.remove();
    modelo = opc = host = canvas = ctx = camada = cena = cenaId = null; botoes.clear();
  }

  return { montar, mostrar, destacar, desmontar, medidas, nome: '2d' };
}
