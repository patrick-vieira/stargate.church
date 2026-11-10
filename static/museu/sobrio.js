// sobrio.js: o modo sóbrio, renderizado a partir do MESMO JSON do lúdico (séries, notícias e o grafo de blocos).
// HTML semântico, sem JS de interação: as escolhas do livro-jogo são links normais (<a href="#n7">Aprofundar: vai a 7</a>).
// gerar_dados.py corre ESTA função (por node) para gravar o sóbrio estático no index.html, para quem não tem JS.

const ESC = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#x27;' };
export const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ESC[c]);
// «[MOCK]» fica sempre visível, como etiqueta
export function etiquetar(t) {
  const e = esc(t);
  return e.startsWith('[MOCK]') ? '<span class="etiqueta">[MOCK]</span>' + e.slice(6) : e;
}
// peças opcionais do bloco (BRIEF-3): fontes, texto da narração e notas de produção (estas só se mostram com ?producao=1)
const urlSegura = (u) => /^https?:\/\//i.test(String(u || ''));
const eVerificada = (f) => f.verificada !== false && f.verificada !== null && f.verificada !== undefined && f.verificada !== '';
export function htmlFontes(fontes) {
  if (!Array.isArray(fontes) || !fontes.length) return '';
  return '<section class="fontes" aria-label="Fontes"><h4>Fontes</h4><ul class="fontes-lista">' + fontes.map((f) => {
    const rot = `${esc(f.veiculo)} · ${esc(f.data)}`;
    return '<li>' + (urlSegura(f.url)
      ? `<a href="${esc(f.url)}" rel="noopener noreferrer" target="_blank" title="${esc(f.titulo)}">${rot}</a><span class="so-leitor">: ${esc(f.titulo)} (abre em outra aba)</span>`
      : `<span>${rot}</span>`) + (eVerificada(f) ? '' : ' <span class="por-verificar">por verificar</span>') + '</li>';
  }).join('') + '</ul></section>';
}
function htmlNarracao(n) {
  if (!n.narracao && !n.narracao_audio_endpoint) return '';
  return '<section class="narracao" aria-label="Narração">' +
    (n.narracao ? `<details><summary>Ver texto da narração</summary><p>${esc(n.narracao)}</p></details>` : '') +
    (n.narracao_audio_endpoint ? `<button type="button" class="btn ouvir" data-audio-endpoint="${esc(n.narracao_audio_endpoint)}">Ouvir a narração</button>` : '') +
    '</section>';
}
function htmlProducao(n) {
  if (!n.visual && !n.som) return '';
  return '<aside class="producao" aria-label="Notas de produção" hidden><h4>Notas de produção</h4><dl>' +
    (n.visual ? `<dt>Visual</dt><dd>${esc(n.visual)}</dd>` : '') + (n.som ? `<dt>Som</dt><dd>${esc(n.som)}</dd>` : '') + '</dl></aside>';
}
const ROT = { seguir: 'Seguir', aprofundar: 'Aprofundar', subir: 'Subir', otimista: 'Lado otimista', catastrofico: 'Lado sombrio', museu: 'Peças do museu' };
const ORDEM = ['seguir', 'aprofundar', 'subir', 'otimista', 'catastrofico', 'museu'];

function htmlPeca(n) {
  if (n.tipo === 'video') {
    const v = n.video;
    return `<div data-video-no="${esc(n.id)}"><p>${esc(v.legenda)}</p></div>`;
  }
  if (n.tipo === 'camadas') return n.camadas.map(c => `<details><summary>${esc(c.rotulo)}</summary><p>${esc(c.texto)}</p></details>`).join('');
  if (n.tipo === 'dialogo') {
    const d = n.dialogo;
    return `<section class="peca"><h4>${esc(d.personagem.nome)} · ${esc(d.personagem.papel)}</h4>` + d.falas.map(f => `<p>${esc(f)}</p>`).join('') + d.respostas.map(r => `<p><a class="btn resposta" href="#n${esc(r.vai)}">${esc(r.texto)}</a></p>`).join('') + '</section>';
  }
  return '';
}
function htmlLivro(g, serie) {
  const o = [];
  const por = new Map(g.nos.map((n) => [n.id, n]));
  o.push(`<section id="livro-jogo" aria-labelledby="h-livro"><div class="wrap"><span class="sob">Livro-jogo</span><h2 id="h-livro">${etiquetar(serie ? serie.titulo : 'Livro-jogo')}: escolha o caminho</h2>` +
    `<p>Cada bloco tem um número. No fim de cada um você escolhe: seguir, aprofundar, subir ou ir a um dos lados (otimista ou sombrio). ` +
    `<a href="#n${esc(g.entrada)}">Começar pelo bloco ${esc(g.entrada)}</a>.</p>`);
  for (const v of g.visitas || []) o.push(`<nav class="percurso-visita" aria-label="Percurso da visita"><h3>${esc(v.nome)}</h3><ol>` + v.passos.map((id,i) => `<li><a href="#n${esc(id)}">Passo ${i+1}: ${esc(por.get(id).titulo)}</a> ${i < v.passos.length-1 ? `<a href="#n${esc(v.passos[i+1])}">Seguinte</a>` : ''}</li>`).join('') + '</ol></nav>');
  for (const s of g.salas || []) o.push(`<nav aria-label="${esc(s.nome)}"><h3>${esc(s.nome)}</h3><p>${esc(s.contexto)}</p>` + g.nos.filter(n => n.sala === s.id).map(n => `<a class="btn" href="#n${esc(n.id)}">${esc(n.titulo)}</a>`).join(' ') + '</nav>');
  for (const n of g.nos) {
    const lado = n.polo > 0 ? ' · lado otimista' : n.polo < 0 ? ' · lado sombrio' : '';
    o.push(`<article class="bloco" id="n${esc(n.id)}" aria-labelledby="nt${esc(n.id)}"><h3 id="nt${esc(n.id)}"><span class="num">${esc(n.id)}</span> ${etiquetar(n.titulo)}</h3>` +
      `<p class="prov">Bloco ${esc(n.id)} · nível ${n.nivel | 0}${lado}</p>` + n.texto.map((p) => `<p>${esc(p)}</p>`).join('') + htmlPeca(n) + `<p class="placa-sala">${esc((g.salas || []).find(s => s.id === n.sala)?.nome || '')}</p>` + '<ul class="escolhas" aria-label="Escolhas do bloco ' + esc(n.id) + '">');
    for (const t of ORDEM) {
      const v = n.ligacoes[t];
      if (v == null) continue;
      o.push(`<li><a href="#n${esc(v)}" data-tipo="${t}">${esc(n.rotulos?.[t] || ROT[t] + ": vai a " + v)}</a></li>`);
    }
    o.push('</ul>' + htmlFontes(n.fontes) + htmlNarracao(n) + htmlProducao(n) + '</article>');
  }
  o.push('</div></section>');
  return o.join('');
}

export function htmlSobrio(d) {
  const o = [];
  const g = d.grafo || null;
  const grafoDaSerie = (slug) => g && (g.series ? g.series[slug] : g.serie === slug ? { entrada: g.entrada, ids: g.nos.map(n => n.id) } : null);
  o.push('<div class="wrap hero"><span class="sob">Stargate</span><h1>Notícias e séries sobre o futuro que já começou</h1>' +
    '<p>O mesmo conteúdo da versão lúdica, em páginas normais: lê-se de cima para baixo, navega-se pelo teclado e funciona com leitor de tela.</p></div>');
  o.push('<section id="series" aria-labelledby="h-series"><div class="wrap"><span class="sob">Séries</span><h2 id="h-series">As séries do Stargate</h2>');
  for (const s of d.series) {
    const eGrafo = grafoDaSerie(s.slug);
    o.push(`<article class="card" id="serie-${esc(s.slug)}" aria-labelledby="t-${esc(s.slug)}"><h3 id="t-${esc(s.slug)}">${etiquetar(s.titulo)}</h3><p>${esc(s.resumo)}</p>` +
      (eGrafo ? `<p><a class="btn" href="#n${esc(eGrafo.entrada)}">Começar o livro-jogo</a></p>` : '') +
      `<ol class="eps" aria-label="Episódios de ${esc(s.titulo)}">`);
    for (const e of s.episodios) {
      const n = String(e.numero).padStart(2, '0');
      o.push(e.url
        ? `<li><a href="${esc(e.url)}"><small>${n}</small>${etiquetar(e.titulo)}</a></li>`
        : `<li><span class="sem-post"><small>${n}</small>${etiquetar(e.titulo)} <em>(rascunho, sem post)</em></span></li>`);
    }
    o.push('</ol></article>');
  }
  o.push('<p class="prov porta-fechada">Porta fechada: a próxima série chega em breve.</p></div></section>');
  if (g) o.push(htmlLivro(g, null));
  o.push('<section id="noticias" aria-labelledby="h-not"><div class="wrap"><span class="sob">Notícias</span><h2 id="h-not">Últimas notícias</h2><ul class="grade">');
  for (const n of d.noticias) {
    o.push(n.url
      ? `<li class="card"><h3><a href="${esc(n.url)}">${etiquetar(n.titulo)}</a></h3>${n.resumo ? `<p>${esc(n.resumo)}</p>` : ''}</li>`
      : `<li class="card"><h3>${etiquetar(n.titulo)}</h3><p class="prov">Rascunho, sem página ainda.</p></li>`);
  }
  o.push('</ul></div></section>');
  const atrio = d.series.length < 3;
  o.push(`<section id="mapa" class="mapa" aria-labelledby="h-mapa"><div class="wrap"><span class="sob">Mapa</span><h2 id="h-mapa">Mapa do site</h2>` +
    `<nav aria-label="Mapa do site"><ul><li><a href="#principal">${atrio ? 'Átrio' : 'Cruzamento'} (início)</a><ul>`);
  for (const s of d.series) {
    const eGrafo = grafoDaSerie(s.slug);
    const quantidade = eGrafo ? eGrafo.ids.length : s.episodios.length;
    const unidade = eGrafo ? (quantidade === 1 ? 'bloco' : 'blocos') : (quantidade === 1 ? 'episódio' : 'episódios');
    o.push(`<li><a href="#${eGrafo ? 'livro-jogo' : 'serie-' + esc(s.slug)}">Corredor: ${etiquetar(s.titulo)}</a> <span class="prov">(${quantidade} ${unidade})</span></li>`);
  }
  o.push('<li><a href="#noticias">Corredor das notícias</a></li><li><span class="prov">Porta fechada: em breve.</span></li></ul></li></ul></nav></div></section>');
  return o.join('');
}

// O sóbrio estático já vem no HTML (gerar_dados.py corre htmlSobrio por node); se faltar, monta-se por DOMParser, sem innerHTML.
// ?producao=1 mostra as notas de produção (escondidas por padrão).
export function renderSobrio(dados, alvo, producao) {
  if (dados) {
    const doc = new DOMParser().parseFromString('<body>' + htmlSobrio(dados) + '</body>', 'text/html');
    alvo.replaceChildren(...doc.body.childNodes);
  }
  if (producao) alvo.querySelectorAll('.producao[hidden]').forEach((e) => e.removeAttribute('hidden'));
}
