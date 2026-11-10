// app.js: liga tudo. Lê o JSON embutido, cria o modelo (grafo), escolhe o modo (lúdico/sóbrio), monta o renderizador 2D, o controle,
// o mapa, o cartão do bloco (texto, narração e escolhas), o som e a transição para os posts.
import { criarModelo } from './modelo.js';
import { montarControlo } from './controlo.js';
import { renderSobrio } from './sobrio.js';
import { el, tituloDom, fontesDom, narracaoDom, producaoDom, producaoAtiva } from './cartao.js';
import { desenharMapa } from './mapa.js';
import { criarRender2d } from './render2d.js';
import { criarSom } from './som.js';
import { conteudoMuseu, criarVisita } from './museu.js';

const $ = (id) => document.getElementById(id);
const lerLS = (k) => { try { return localStorage.getItem(k); } catch (e) { return null; } };
const gravarLS = (k, v) => { try { localStorage.setItem(k, v); } catch (e) { /* sem armazenamento */ } };
const lerSS = (k) => { try { return sessionStorage.getItem(k); } catch (e) { return null; } };
const gravarSS = (k, v) => { try { sessionStorage.setItem(k, v); } catch (e) { /* idem */ } };

const dados = JSON.parse($('dados').textContent);
if (!dados) { document.querySelectorAll('button').forEach(b => b.hidden = true); }
else {
const modelo = criarModelo(dados);
const som = criarSom();
const reduzido = matchMedia('(prefers-reduced-motion: reduce)').matches;
renderSobrio(dados, $('principal'), producaoAtiva(location));

let pos = modelo.posicaoInicial();
const visitados = new Set();
let modo = 'sobrio', pausado = lerLS('stargate.pausa') === '1';
let render = null, desmontaControlo = null, mapaSel = null, hudPronto = false, avisoT = 0;
const semMov = () => pausado || reduzido;

// ---------- estado guardado (a mesma aba: voltar de um post cai no mesmo bloco) ----------
try {
  const e = JSON.parse(lerSS('stargate.estado') || 'null');
  if (e && modelo.valida(e.pos)) { pos = e.pos; (e.visitados || []).forEach((id) => modelo.nos.has(id) && visitados.add(id)); }
} catch (e) { /* estado inválido: começa do zero */ }
const guardar = () => gravarSS('stargate.estado', JSON.stringify({ pos, visitados: [...visitados] }));
const marcar = () => { if (!modelo.emHub(pos)) visitados.add(pos.no); };
marcar();

// ---------- avisos ----------
function aviso(t) {
  const a = $('aviso'); a.textContent = t; a.classList.add('on');
  clearTimeout(avisoT); avisoT = setTimeout(() => a.classList.remove('on'), 3800);
}

// ---------- ações ----------
const SOM_DE = { seguir: 'seguir', aprofundar: 'aprofundar', subir: 'subir', otimista: 'otimista', catastrofico: 'catastrofico', 'hub-no': 'seguir' };
let visita = null;
function mover(novo, guiada = false) {
  if (!novo || novo === pos) return false;
  if (!guiada && visita) visita.navegar();
  const mov = modelo.movimento(pos, novo);
  pos = novo; marcar(); guardar();
  if (render) render.mostrar(pos, { animar: true });
  atualizar();
  som.tocar(SOM_DE[mov] || (/^inv-|no-hub/.test(mov) ? 'recuar' : null));
  return true;
}
const noAtual = () => modelo.noDe(pos);
const acoes = {
  avancar() {
    const s = modelo.saidaEm(pos);
    if (s && s.fechada) { aviso('Porta fechada: a próxima série chega em breve.'); return; }
    if (!s && !modelo.escolha(pos, 'seguir')) { aviso('Sem passagem em frente neste bloco: escolha outra porta ou volte.'); return; }
    mover(modelo.seguir(pos));
  },
  recuar() { mover(modelo.voltar(pos)); },
  virar(d) {
    const p = modelo.virar(pos, d);
    if (p === pos && !modelo.emHub(pos)) aviso(d < 0 ? 'Este bloco não tem lado sombrio.' : 'Este bloco não tem lado otimista.');
    mover(p);
  },
  aprofundar() { const p = modelo.aprofundar(pos); if (p === pos && !modelo.emHub(pos)) aviso('Sem passagem para baixo neste bloco.'); mover(p); },
  subir() { const p = modelo.subir(pos); if (p === pos && !modelo.emHub(pos)) aviso('Sem passagem para cima neste bloco.'); mover(p); },
  voltar() { mover(modelo.voltar(pos)); },
  mapa() { abrirMapa(); },
  ativar() {
    if (modelo.emHub(pos)) { acoes.avancar(); return; }
    const n = noAtual();
    if (n && n.url) abrirPost(n);
  },
};
function aoAtivarAlvo(a) {
  if (a.fechada !== undefined) {                       // porta do hub
    if (a.fechada) { aviso('Porta fechada: a próxima série chega em breve.'); return; }
    mover(modelo.entrar(modelo.irParaSaida(a.id)));
  } else mover(modelo.ir(pos, a.tipo));                // porta de um bloco
}

// ---------- transição para um post ----------
function abrirPost(n) {
  if (!n.url) { aviso(`${n.titulo}: rascunho [MOCK], sem post publicado.`); return; }
  guardar();
  const destino = new URL(n.url, location.href).href;
  const ir = () => { if (window.__stargateTeste && window.__stargateTeste.navegar) window.__stargateTeste.navegar(destino); else location.href = destino; };   // gancho só para a prova (print da transição)
  if (semMov()) { ir(); return; }
  $('cortina').textContent = n.titulo;
  const vt = document.startViewTransition;
  if (vt) {
    document.documentElement.classList.add('vt');
    const t = document.startViewTransition(() => { document.documentElement.classList.add('saindo'); });
    Promise.race([t.finished, new Promise((r) => setTimeout(r, 700))]).then(() => setTimeout(ir, 60), () => ir());
  } else { document.documentElement.classList.add('saindo'); setTimeout(ir, 280); }
}
addEventListener('pageshow', (e) => { if (e.persisted) document.documentElement.classList.remove('saindo', 'vt'); });

// ---------- o cartão do bloco (só DOM: nenhum texto do JSON passa por innerHTML) ----------
function textoLado(n) { return n.polo > 0 ? ' · lado otimista' : n.polo < 0 ? ' · lado sombrio' : ''; }
const PRODUCAO = producaoAtiva(location);
function atualizarCartao() {
  const c = $('cartao'); if (!c) return;
  const tinhaFoco = c.contains(document.activeElement);
  const n = noAtual(), d = document;
  const partes = [];
  if (!n) {
    const s = modelo.saidaEm(pos), onde = modelo.tipoHub === 'atrio' ? 'Átrio' : 'Cruzamento';
    c.className = 'cartao cartao-hub'; c.dataset.polo = '0'; delete c.dataset.nivel;
    partes.push(el(d, 'p', { class: 'sob', text: onde }), el(d, 'h2', { tabindex: '-1' }, s.fechada ? 'Porta fechada' : tituloDom(d, s.titulo)),
      el(d, 'p', { text: s.fechada ? 'A próxima série chega em breve.' : s.resumo || '' }));
    if (!s.fechada) {
      const e = el(d, 'button', { type: 'button', class: 'btn acao', id: 'entrar',
        text: `Entrar no corredor (${s.tipo === 'noticias' ? s.passos + ' notícias' : s.grafo ? s.passos + ' blocos' : s.passos + ' episódios'})` });
      e.addEventListener('click', () => acoes.avancar());
      partes.push(el(d, 'p', null, e));
    }
  } else {
    const es = modelo.escolhas(pos), serie = modelo.porId.get(n.serie);
    c.className = 'cartao'; c.dataset.polo = String(n.polo); c.dataset.nivel = String(n.nivel);
    const rotulo = n.serie === 'noticias' ? 'Notícia' : n.polo || n.nivel || serie.grafo ? 'Nível ' + n.nivel + textoLado(n) : 'Episódio ' + n.num;
    const ouvir = n.audio
      ? el(d, 'button', { type: 'button', class: 'btn ouvir', id: 'ouvir', 'aria-label': `Ouvir a narração do bloco ${n.num}`, text: 'Ouvir' })
      : el(d, 'button', { type: 'button', class: 'btn ouvir', id: 'ouvir', disabled: true, text: 'Narração em breve' });
    if (n.audio) ouvir.addEventListener('click', () => som.narrar(n.audio).then((ok) => { if (!ok) aviso('Não foi possível tocar a narração.'); }));
    const nar = narracaoDom(d, n.narracao, 'narracao-txt');
    partes.push(el(d, 'div', { class: 'cartao-topo' }, el(d, 'span', { class: 'num', role: 'img', 'aria-label': `Bloco ${n.num}`, text: n.num }),
      el(d, 'span', { class: 'sob', text: rotulo }), ouvir, nar && nar.botao));
    partes.push(el(d, 'h2', { tabindex: '-1' }, tituloDom(d, n.titulo)));
    if (nar) partes.push(nar.painel);
    const sala = dados.grafo.salas.find(s => s.id === n.sala);
    if (sala) partes.unshift(el(d,'aside',{class:'placa-sala',role:'status'},el(d,'strong',{text:sala.nome}),el(d,'p',{text:sala.contexto})));
    n.texto.forEach((t) => partes.push(el(d, 'p', { text: t })));
    partes.push(conteudoMuseu(d,n,{ir:id => mover(modelo.irParaNo(pos,id)),aoVideo:() => visita && visita.pausar()}));
    if (es.length) {
      const ul = el(d, 'ul', { class: 'escolhas', 'aria-label': 'Escolhas' });
      es.forEach((e) => {
        const b = el(d, 'button', { type: 'button', class: `btn esc esc-${e.tipo}`, 'data-tipo': e.tipo, text: e.texto });
        b.addEventListener('click', () => mover(modelo.ir(pos, e.tipo)));
        ul.append(el(d, 'li', null, b));
      });
      partes.push(ul);
    } else partes.push(el(d, 'p', { class: 'prov', text: 'Sem escolhas aqui. Use ▼ ou Esc para voltar.' }));
    if (n.url) {
      const ap = el(d, 'button', { type: 'button', class: 'btn acao abrir-post', id: 'abrir-post', text: 'Abrir o post' });
      ap.addEventListener('click', () => abrirPost(n));
      partes.push(el(d, 'p', null, ap));
    }
    partes.push(fontesDom(d, n.fontes));
    if (PRODUCAO) partes.push(producaoDom(d, n.producao));
  }
  const texto = el(d, 'div', { class: 'cartao-texto', tabindex: '0', 'aria-label': 'Conteúdo do bloco (rolável)' }, ...partes.filter(Boolean));
  const rodape = el(d, 'div', { class: 'cartao-acoes', 'aria-label': 'Respostas e escolhas' });
  texto.querySelectorAll('.resposta, .escolhas, .abrir-post').forEach(a => rodape.append(a));
  c.replaceChildren(texto, rodape);
  c.scrollTop = 0;
  c.closest('.hud').scrollTop = 0;
  if (tinhaFoco) { const h = c.querySelector('h2'); if (h) h.focus({ preventScroll: true }); }
}

// ---------- mapas ----------
function serieAtual() { return modelo.emHub(pos) ? null : noAtual().serie; }
function ctxMapa(grande) {
  const sel = grande ? mapaSel : serieAtual();
  const s = sel && sel !== 'hub' ? modelo.porId.get(sel) : null;
  return {
    modo: s ? 'serie' : 'hub', grande, mapaHub: modelo.mapaHub(pos), layout: s ? modelo.layout(s.id) : null,
    atualId: modelo.emHub(pos) ? null : pos.no, visitados,
    aoNo: (id) => { fecharMapa(); mover(modelo.irParaNo(pos, id)); },
    aoSerie: (id) => { mapaSel = id; desenharMapaGrande(); },
    aoHub: () => { fecharMapa(); mover(modelo.irParaHub(pos)); },
  };
}
function desenharMapaPequeno() { const s = document.querySelector('#mapa-bt svg'); if (s) desenharMapa(s, ctxMapa(false)); }
function desenharMapaGrande() {
  const dlg = $('mapa-grande'); if (!dlg) return;
  desenharMapa(dlg.querySelector('svg'), ctxMapa(true));
  const caixa = dlg.querySelector('.mg-series'); caixa.replaceChildren();
  const mk = (id, txt) => { const b = document.createElement('button'); b.type = 'button'; b.className = 'btn'; b.textContent = txt; b.setAttribute('aria-pressed', String(mapaSel === id)); b.addEventListener('click', () => { mapaSel = id; desenharMapaGrande(); }); caixa.appendChild(b); };
  mk('hub', modelo.tipoHub === 'atrio' ? 'Átrio' : 'Cruzamento');
  modelo.saidas.filter((s) => !s.fechada).forEach((s) => mk(s.id, s.titulo));
  dados.grafo.salas.forEach(s => {
    const grupo = el(document,'section',{class:'mapa-sala'},el(document,'h3',{text:s.nome}));
    dados.grafo.nos.filter(n => n.sala === s.id).forEach(n => {
      const b = el(document,'button',{class:'btn',type:'button',text:n.id + ' · ' + n.titulo});
      b.addEventListener('click',() => { fecharMapa(); mover(modelo.irParaNo(pos,String(n.id))); }); grupo.append(b);
    }); caixa.append(grupo);
  });
  const sel = modelo.porId.get(mapaSel);
  $('mg-leg').textContent = sel && sel.grafo ? 'Blocos cheios já foram visitados. Clique ou use Enter num bloco para saltar.' : 'Clique ou use Enter para saltar.';
}
function abrirMapa() {
  const dlg = $('mapa-grande'); if (!dlg || dlg.open) return;
  mapaSel = modelo.emHub(pos) ? 'hub' : noAtual().serie;
  desenharMapaGrande();
  if (dlg.showModal) dlg.showModal(); else dlg.setAttribute('open', '');
  const f = dlg.querySelector('.m-bt') || $('mg-fechar'); if (f && f.focus) f.focus();
}
function fecharMapa() { const dlg = $('mapa-grande'); if (dlg && dlg.open) dlg.close(); }

// ---------- HUD ----------
function atualizar() {
  $('estado').textContent = modelo.descrever(pos);
  atualizarCartao(); desenharMapaPequeno();
  const n = noAtual(), p = $('pos');
  if (p) p.textContent = n ? `Bloco ${n.num} · nível ${n.nivel}` : (modelo.tipoHub === 'atrio' ? 'Átrio' : 'Cruzamento');
  const d = $('dica');
  if (d) d.innerHTML = n ? '<b>↑</b> seguir · <b>↓</b> voltar · <b>←/→</b> lado sombrio/otimista · <b>PgDn/PgUp</b> aprofundar/subir · <b>M</b> mapa'
    : '<b>←/→</b> escolhem a porta · <b>↑</b> ou role para entrar · <b>M</b> mapa';
}
function montarHud() {
  if (hudPronto) return; hudPronto = true;
  const topo = document.querySelector('header.topo');
  const medirTopo = () => document.documentElement.style.setProperty('--topo-cartao', `${topo.getBoundingClientRect().bottom + 8}px`);
  new ResizeObserver(medirTopo).observe(topo);
  medirTopo();
  const c = $('cena');
  c.insertAdjacentHTML('beforeend',
    '<div class="vig" aria-hidden="true"></div><div class="borda borda-e" aria-hidden="true">◀</div><div class="borda borda-d" aria-hidden="true">▶</div>' +
    '<div class="hud"><section class="cartao" id="cartao" aria-label="Bloco atual"></section>' +
    '<div class="hud-baixo"><p class="dica" id="dica"></p>' +
    '<div class="ctrl" role="group" aria-label="Controles de movimento">' +
    '<button type="button" class="btn" data-a="virar-e" aria-label="Virar à esquerda: lado sombrio">◀</button>' +
    '<button type="button" class="btn" data-a="avancar" aria-label="Seguir em frente">▲</button>' +
    '<button type="button" class="btn" data-a="recuar" aria-label="Voltar ao bloco anterior">▼</button>' +
    '<button type="button" class="btn" data-a="virar-d" aria-label="Virar à direita: lado otimista">▶</button></div>' +
    '<button type="button" class="mapa-peq" id="mapa-bt" aria-label="Abrir o mapa grande (tecla M)"><svg aria-hidden="true" focusable="false"></svg><span id="pos"></span></button></div></div>' +
    '<dialog id="mapa-grande" aria-labelledby="mg-t"><h2 id="mg-t">Mapa do labirinto</h2><div class="mg-series" role="group" aria-label="Escolher corredor"></div>' +
    '<svg role="group" aria-label="Mapa: escolha um bloco para saltar"></svg><p class="prov" id="mg-leg"></p>' +
    '<p class="mg-leg-eixos prov">Eixos: para a direita, seguir; para baixo, aprofundar; para cima e para a direita, lado otimista; para baixo e para a esquerda, lado sombrio.</p>' +
    '<button type="button" class="btn" id="mg-fechar">Fechar (Esc)</button></dialog>' +
    '<div id="estado" class="so-leitor" role="status" aria-live="polite"></div>');
  const q = { 'virar-e': () => acoes.virar(-1), avancar: () => acoes.avancar(), recuar: () => acoes.recuar(), 'virar-d': () => acoes.virar(1) };
  c.querySelectorAll('.ctrl .btn').forEach((b) => b.addEventListener('click', () => q[b.dataset.a]()));
  $('mapa-bt').addEventListener('click', abrirMapa);
  $('mg-fechar').addEventListener('click', fecharMapa);
  $('mapa-grande').addEventListener('click', (e) => { if (e.target === $('mapa-grande')) fecharMapa(); });
}

// ---------- modos ----------
function montarLudico() {
  montarHud();
  render = criarRender2d();
  render.montar($('cena'), modelo, { aoAtivar: aoAtivarAlvo, aoFocar: (a) => { if (a.fechada !== undefined) mover(modelo.irParaSaida(a.id)); }, pausado: semMov });
  desmontaControlo = montarControlo($('cena'), acoes, {
    pausado: semMov, bloqueado: () => { const d = $('mapa-grande'); return !!(d && d.open); }, bordaAtiva: () => modelo.emHub(pos),
  });
  render.mostrar(pos, { animar: false });
  atualizar();
}
function desmontarLudico() {
  fecharMapa();
  if (desmontaControlo) { desmontaControlo(); desmontaControlo = null; }
  if (render) { render.desmontar(); render = null; }
}
function aplicarModo(m, guardarEscolha) {
  if (m === modo && (m === 'sobrio' || render)) return;
  modo = m;
  document.documentElement.dataset.modo = m;
  const sw = $('modo'); sw.setAttribute('aria-checked', String(m === 'ludico'));
  $('pausa').hidden = m !== 'ludico'; $('som').hidden = m !== 'ludico';
  if (m === 'ludico') montarLudico(); else desmontarLudico();
  if (visita) { visita.pausar(); visita.atualizar(); }
  if (guardarEscolha) gravarLS('stargate.modo', m);
}
function ligarControlos() {
  const sw = $('modo'); sw.hidden = false;
  sw.addEventListener('click', () => aplicarModo(modo === 'ludico' ? 'sobrio' : 'ludico', true));
  const pa = $('pausa'), so = $('som');
  const pintaPausa = () => { pa.setAttribute('aria-pressed', String(semMov())); pa.textContent = semMov() ? 'Retomar movimento' : 'Pausar movimento'; document.documentElement.classList.toggle('sem-movimento', semMov()); };
  pa.addEventListener('click', () => { pausado = !pausado; gravarLS('stargate.pausa', pausado ? '1' : '0'); pintaPausa(); });
  pa.disabled = reduzido; pintaPausa();
  const pintaSom = () => { so.setAttribute('aria-checked', String(som.ligado)); so.querySelector('.rot').textContent = som.ligado ? 'Som: ligado' : 'Som: desligado'; };
  so.addEventListener('click', () => { som.ligar(!som.ligado); pintaSom(); });
  pintaSom();
}
ligarControlos();
const guardado = lerLS('stargate.modo');
aplicarModo(reduzido ? 'sobrio' : guardado === 'ludico' || guardado === 'sobrio' ? guardado : 'ludico', false);

visita = criarVisita(dados, { modo:() => modo, reduzido, mover(id, guiada) {
  if (modo === 'sobrio') { location.hash = '#n' + id; document.getElementById('n' + id)?.scrollIntoView(); }
  else mover(modelo.irParaNo(pos,id),guiada);
} });
// Hidrata o vídeo estático: nenhum src de vídeo antes da ação explícita.
document.querySelectorAll('[data-video-no]').forEach(c => {
 const n = dados.grafo.nos.find(n => String(n.id) === c.dataset.videoNo);
 c.replaceChildren(conteudoMuseu(document,n,{sobrio:true,aoVideo:() => visita.pausar()}));
});
document.querySelector('#principal').addEventListener('click',e => { if(e.target.closest('a[href^="#n"]')) visita.navegar(); });
window.__stargate = { modelo, som, get visita() { return visita.estado; }, irPara(id) { return mover(modelo.irParaNo(pos, id)); },   // gancho de teste: salto direto (como o mapa)
   get pos() { return pos; }, get visitados() { return [...visitados]; }, get modo() { return modo; }, get medidas() { return render ? render.medidas : []; } };

}
