// cartao.js: as peças do cartão de um bloco (modo lúdico), construídas SÓ por DOM (createElement + textContent).
// Nenhum texto que venha do JSON passa por innerHTML. O sóbrio estático (sobrio.js) usa o mesmo conteúdo, escapado com esc().
// Fontes, texto da narração e notas de produção (`visual`, `som`) são campos opcionais do nó (BRIEF-3).

export function el(doc, tag, attrs, ...filhos) {
  const e = doc.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === false || v == null) continue;
    if (k === 'class') e.className = v; else if (k === 'text') e.textContent = v; else e.setAttribute(k, v === true ? '' : String(v));
  }
  for (const f of filhos) if (f != null) e.append(f);
  return e;
}

// «[MOCK]» fica sempre visível, como etiqueta
export function tituloDom(doc, t) {
  const s = String(t == null ? '' : t), f = doc.createDocumentFragment();
  if (s.startsWith('[MOCK]')) { f.append(el(doc, 'span', { class: 'etiqueta', text: '[MOCK]' }), doc.createTextNode(s.slice(6))); } else f.append(doc.createTextNode(s));
  return f;
}

export const urlSegura = (u) => /^https?:\/\//i.test(String(u || ''));
export const verificada = (f) => f && f.verificada !== false && f.verificada !== null && f.verificada !== '' && f.verificada !== undefined;

// Lista curta de fontes: «veículo · data» como link (rel="noopener noreferrer" target="_blank"); fonte por verificar leva a marca.
export function fontesDom(doc, fontes) {
  if (!Array.isArray(fontes) || !fontes.length) return null;
  const ul = el(doc, 'ul', { class: 'fontes-lista' });
  for (const f of fontes) {
    const li = el(doc, 'li');
    const rot = `${f.veiculo} · ${f.data}`;
    if (urlSegura(f.url)) {
      li.append(el(doc, 'a', { href: f.url, rel: 'noopener noreferrer', target: '_blank', title: f.titulo, text: rot }),
        el(doc, 'span', { class: 'so-leitor', text: `: ${f.titulo} (abre em outra aba)` }));
    } else li.append(el(doc, 'span', { text: rot }));
    if (!verificada(f)) li.append(' ', el(doc, 'span', { class: 'por-verificar', text: 'por verificar' }));
    ul.append(li);
  }
  return el(doc, 'section', { class: 'fontes', 'aria-label': 'Fontes' }, el(doc, 'h3', { text: 'Fontes' }), ul);
}

// Botão «ver texto da narração» + o texto (escondido até abrir). Devolve {botao, painel} ou null.
export function narracaoDom(doc, texto, idPainel) {
  if (!texto) return null;
  const painel = el(doc, 'div', { class: 'narracao-txt', id: idPainel, hidden: true }, el(doc, 'p', { text: texto }));
  const botao = el(doc, 'button', { type: 'button', class: 'btn ver-narracao', id: 'ver-narracao', 'aria-expanded': 'false', 'aria-controls': idPainel, text: 'Ver texto da narração' });
  botao.addEventListener('click', () => {
    const abre = painel.hidden;
    painel.hidden = !abre;
    botao.setAttribute('aria-expanded', String(abre));
    botao.textContent = abre ? 'Esconder texto da narração' : 'Ver texto da narração';
  });
  return { botao, painel };
}

// Notas de produção (`visual`, `som`): só existem no DOM com ?producao=1
export const producaoAtiva = (loc) => { try { return new URLSearchParams(loc.search).get('producao') === '1'; } catch (e) { return false; } };
export function producaoDom(doc, p) {
  if (!p || (!p.visual && !p.som)) return null;
  const dl = el(doc, 'dl');
  if (p.visual) dl.append(el(doc, 'dt', { text: 'Visual' }), el(doc, 'dd', { text: p.visual }));
  if (p.som) dl.append(el(doc, 'dt', { text: 'Som' }), el(doc, 'dd', { text: p.som }));
  return el(doc, 'aside', { class: 'producao', 'aria-label': 'Notas de produção' }, el(doc, 'h3', { text: 'Notas de produção' }), dl);
}
