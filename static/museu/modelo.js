// modelo.js: o grafo do labirinto (livro-jogo). PURO: sem DOM, sem relógio, sem aleatoriedade.
// O mundo é um grafo de blocos. O hub é o cruzamento (átrio com menos de 3 séries) com uma saída por série/galeria e
// uma porta fechada «em breve». Cada série é um corredor de blocos; cada bloco tem as ligações
//   seguir (ao longo do corredor), aprofundar / subir (nível), otimista / catastrofico (polo)
// que apontam para outro bloco ou para null. A série de prova («Energia sem fim?», grafo editorial do Konan) vem de dados.grafo; as outras séries
// e as notícias são cadeias lineares de blocos (só `seguir`), cada um com a ligação direta ao post (`url`).
// Uma posição é imutável: {no:'hub', olhar, vindo} ou {no:<id do bloco>, vindo}; `vindo` é a pilha dos blocos anteriores.

export const TIPOS = ['seguir', 'aprofundar', 'subir', 'otimista', 'catastrofico', 'museu'];
export const ROTULOS = { seguir: 'Seguir', aprofundar: 'Aprofundar', subir: 'Subir', otimista: 'Lado otimista', catastrofico: 'Lado sombrio', museu: 'Peças do museu' };
export const OBJETOS = ['porta', 'livro', 'ecrã', 'quadro'];
export const PASSO_ANGULO_ATRIO = 40;
export const MIN_SERIES_CRUZAMENTO = 3;
const MAX_VINDO = 300;

export function criarModelo(dados) {
  const series = (dados && dados.series) || [];
  const noticias = (dados && dados.noticias) || [];
  const grafo = dados && dados.grafo;
  const nos = new Map();
  const saidas = [];
  const nulas = () => ({ seguir: null, aprofundar: null, subir: null, otimista: null, catastrofico: null });

  const cadeia = (id, titulo, tipo, tema, mock, itens, resumo) => {
    const ids = itens.map((it, i) => `${id}:${i}`);
    itens.forEach((it, i) => {
      nos.set(ids[i], {
        id: ids[i], num: String(it.numero), serie: id, titulo: it.titulo, texto: it.resumo ? [it.resumo] : [], nivel: 0, polo: 0, audio: null, fontes: [], narracao: '', producao: { visual: '', som: '' },
        url: it.url || '', mock: !!(mock || it.mock), tipo: it.objeto || OBJETOS[it.numero % 4], tema,
        ligacoes: { ...nulas(), seguir: ids[i + 1] || null },
      });
    });
    saidas.push({ id, tipo, titulo, resumo: resumo || '', tema, mock, fechada: false, passos: itens.length, entrada: ids[0] || null, grafo: false });
  };
  for (const s of series) {
    if (grafo && grafo.serie === s.slug) {
      grafo.nos.forEach((n) => {
        const lig = nulas();
        TIPOS.forEach((t) => { const v = n.ligacoes && n.ligacoes[t]; lig[t] = v == null ? null : String(v); });
        nos.set(String(n.id), {
          id: String(n.id), num: String(n.id), serie: s.slug, titulo: n.titulo, texto: n.texto || [], nivel: n.nivel | 0, polo: n.polo | 0,
          audio: n.audio || null, fontes: Array.isArray(n.fontes) ? n.fontes : [], narracao: typeof n.narracao === 'string' ? n.narracao : '',
          producao: { visual: typeof n.visual === 'string' ? n.visual : '', som: typeof n.som === 'string' ? n.som : '' }, url: '', mock: true, tipo: n.tipo || 'texto', sala: n.sala, video: n.video, camadas: n.camadas, dialogo: n.dialogo, tema: s.tema | 0, ligacoes: lig, rotulos: n.rotulos,
        });
      });
      saidas.push({ id: s.slug, tipo: 'serie', titulo: s.titulo, resumo: s.resumo || '', tema: s.tema | 0, mock: !!s.mock, fechada: false, passos: grafo.nos.length, entrada: String(grafo.entrada), grafo: true });
    } else {
      cadeia(s.slug, s.titulo, 'serie', s.tema | 0, !!s.mock, s.episodios || [], s.resumo);
    }
  }
  if (noticias.length) {
    cadeia('noticias', 'Notícias', 'noticias', 1, noticias.every((n) => n.mock),
      noticias.map((n, i) => ({ numero: i + 1, titulo: n.titulo, resumo: n.resumo || '', url: n.url || '', objeto: 'quadro', mock: n.mock })), 'Últimas notícias do Stargate.');
  }
  saidas.push({ id: 'em-breve', tipo: 'fechada', titulo: 'Em breve', resumo: '', tema: 0, mock: false, fechada: true, passos: 0, entrada: null, grafo: false });

  const m = saidas.length;
  const tipoHub = series.length < MIN_SERIES_CRUZAMENTO ? 'atrio' : 'cruzamento';
  const passoAngulo = tipoHub === 'atrio' ? PASSO_ANGULO_ATRIO : 360 / m;
  const porId = new Map(saidas.map((s) => [s.id, s]));
  const nOlhar = (o) => (tipoHub === 'atrio' ? Math.max(0, Math.min(m - 1, o)) : ((o % m) + m) % m);
  const emHub = (p) => p.no === 'hub';
  const hub = (olhar, vindo) => ({ no: 'hub', olhar: olhar | 0, vindo: vindo || [] });
  const empilha = (p, para) => ({ no: para, vindo: (emHub(p) ? p.vindo : [...p.vindo, p.no]).slice(-MAX_VINDO) });

  const api = {
    nos, saidas, tipoHub, passoAngulo, porId, grafo: grafo || null,
    posicaoInicial: () => hub(0),
    emHub,
    noDe: (p) => (emHub(p) ? null : nos.get(p.no) || null),
    serieDe: (p) => (emHub(p) ? null : porId.get(nos.get(p.no).serie)),
    saidaEm: (p) => (emHub(p) ? saidas[nOlhar(p.olhar)] : null),
    // as escolhas disponíveis num bloco: [{tipo, rotulo, alvo: id, no, texto}]
    escolhas(p) {
      const n = api.noDe(p);
      if (!n) return [];
      return TIPOS.filter((t) => n.ligacoes[t] != null).map((t) => {
        const d = nos.get(n.ligacoes[t]);
        return { tipo: t, rotulo: ROTULOS[t], alvo: d.id, num: d.num, no: d, texto: n.rotulos?.[t] || `${ROTULOS[t]}: vai a ${d.num}` };
      });
    },
    escolha(p, tipo) { return api.escolhas(p).find((e) => e.tipo === tipo) || null; },
    valida(p) {
      if (!p || typeof p !== 'object' || !Array.isArray(p.vindo)) return false;
      if (emHub(p)) return Number.isInteger(p.olhar) && p.olhar >= 0 && p.olhar < m;
      return nos.has(p.no) && p.vindo.every((id) => nos.has(id));
    },
    // ---- transições ----
    ir(p, tipo) {                                       // seguir | aprofundar | subir | otimista | catastrofico
      const n = api.noDe(p);
      const alvo = n && n.ligacoes[tipo];
      return alvo ? empilha(p, alvo) : p;
    },
    seguir: (p) => (emHub(p) ? api.entrar(p) : api.ir(p, 'seguir')),
    aprofundar: (p) => api.ir(p, 'aprofundar'),
    subir: (p) => api.ir(p, 'subir'),
    otimista: (p) => api.ir(p, 'otimista'),
    catastrofico: (p) => api.ir(p, 'catastrofico'),
    // virar: no hub escolhe a saída; num bloco, para a esquerda = lado sombrio, para a direita = lado otimista
    virar(p, dir) {
      const d = dir < 0 ? -1 : 1;
      if (emHub(p)) { const o = nOlhar(p.olhar + d); return o === p.olhar ? p : hub(o, p.vindo); }
      return api.ir(p, d < 0 ? 'catastrofico' : 'otimista');
    },
    entrar(p) {
      if (!emHub(p)) return p;
      const s = saidas[nOlhar(p.olhar)];
      return s.fechada || !s.entrada ? p : { no: s.entrada, vindo: [] };
    },
    // recuar/Esc: o bloco de onde se veio; sem histórico, o hub (a olhar para a saída desta série)
    voltar(p) {
      if (emHub(p)) return p;
      if (p.vindo.length) return { no: p.vindo[p.vindo.length - 1], vindo: p.vindo.slice(0, -1) };
      return hub(Math.max(0, saidas.findIndex((s) => s.id === nos.get(p.no).serie)));
    },
    irParaNo(p, id) { return nos.has(id) && id !== p.no ? empilha(p, id) : p; },
    irParaSaida(id) { const i = saidas.findIndex((s) => s.id === id); return i < 0 ? null : hub(i); },
    irParaHub: (p) => (emHub(p) ? p : hub(Math.max(0, saidas.findIndex((s) => s.id === nos.get(p.no).serie)))),
    // como se foi de a para b: um tipo de ligação, 'inv-<tipo>' (recuo), 'hub-no', 'no-hub', 'hub-hub', 'salto' ou 'mesmo'
    movimento(a, b) {
      if (a.no === b.no && (a.olhar | 0) === (b.olhar | 0)) return 'mesmo';
      if (emHub(a) && emHub(b)) return 'hub-hub';
      if (emHub(a)) return 'hub-no';
      if (emHub(b)) return 'no-hub';
      const na = nos.get(a.no), nb = nos.get(b.no);
      for (const t of TIPOS) if (na.ligacoes[t] === b.no) return t;
      for (const t of TIPOS) if (nb.ligacoes[t] === a.no) return 'inv-' + t;
      return 'salto';
    },
    anguloSaida: (i) => i * passoAngulo,
    // layout do mapa de uma série (sem geometria de ecrã): col (seguir), nivel e polo de cada bloco, e as arestas
    layout(serieId) {
      const ids = [...nos.values()].filter((n) => n.serie === serieId);
      const s = porId.get(serieId);
      if (!s || !ids.length) return { nos: [], arestas: [], colunas: 0, niveis: 0 };
      const col = new Map(), fila = [s.entrada];
      col.set(s.entrada, 0);
      while (fila.length) {
        const a = fila.shift(), n = nos.get(a);
        for (const t of TIPOS) {
          const v = n.ligacoes[t];
          if (v == null || col.has(v) || nos.get(v).serie !== serieId) continue;
          col.set(v, col.get(a) + (t === 'seguir' ? 1 : 0)); fila.push(v);
        }
      }
      const lista = ids.map((n) => ({ id: n.id, num: n.num, titulo: n.titulo, sala: n.sala, col: col.get(n.id) || 0, nivel: n.nivel, polo: n.polo }));
      const arestas = [];
      ids.forEach((n) => TIPOS.forEach((t) => { const v = n.ligacoes[t]; if (v != null && nos.get(v).serie === serieId) arestas.push({ de: n.id, para: v, tipo: t }); }));
      return { nos: lista, arestas, colunas: Math.max(...lista.map((x) => x.col)) + 1, niveis: Math.max(...lista.map((x) => x.nivel)) + 1 };
    },
    mapaHub(p) {
      return { tipoHub, nos: saidas.map((s, i) => ({ id: s.id, titulo: s.titulo, tipo: s.tipo, fechada: s.fechada, mock: s.mock, passos: s.passos, angulo: i * passoAngulo, indice: i })),
        atual: emHub(p) ? null : nos.get(p.no).serie };
    },
    descrever(p) {
      const onde = tipoHub === 'atrio' ? 'Átrio' : 'Cruzamento';
      if (emHub(p)) {
        const s = saidas[nOlhar(p.olhar)];
        return s.fechada ? `${onde}. Você olha para a porta fechada: em breve, a próxima série.`
          : `${onde}. Você olha para ${s.tipo === 'noticias' ? 'o corredor das notícias' : 'o corredor da série ' + s.titulo}. Role ou tecle Enter para entrar.`;
      }
      const n = nos.get(p.no), es = api.escolhas(p);
      return `Bloco ${n.num}: ${n.titulo}. Nível ${n.nivel}${n.polo > 0 ? ', lado otimista' : n.polo < 0 ? ', lado sombrio' : ''}. ` +
        (es.length ? 'Escolhas: ' + es.map((e) => e.texto).join('; ') + '.' : 'Sem escolhas aqui: volte.');
    },
  };
  return api;
}
