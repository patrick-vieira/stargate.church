// Conteúdo interativo: dados entram apenas por DOM/textContent.
import { el } from './cartao.js';
export function conteudoMuseu(d, n, { ir, aoVideo = () => {}, sobrio = false } = {}) {
  const caixa = el(d, 'section', { class: 'peca', 'aria-label': 'Peça do museu' });
  if (n.tipo === 'video') {
    const v = n.video;
    const abrir = el(d, 'button', { type: 'button', class: 'btn abrir-video', text: v.endpoint ? 'Abrir vídeo' : 'Vídeo em preparação', disabled: !v.endpoint });
    const estado = el(d, 'p', { role: 'status', text: v.legenda });
    abrir.addEventListener('click', async () => {
      aoVideo(); abrir.disabled = true; estado.textContent = 'Carregando vídeo…';
      try {
        const resposta = await fetch(v.endpoint, {cache: 'no-store'});
        if (!resposta.ok) throw new Error();
        const dados = await resposta.json();
        const url = new URL(dados.url);
        if (url.protocol !== 'https:') throw new Error();
        const video = el(d, 'video', { controls: true, preload: 'none', src: url.href, 'aria-label': v.legenda, playsinline: true, tabindex: '0' });
        video.addEventListener('error', () => { estado.textContent = 'Vídeo indisponível. Continue pelo texto.'; });
        abrir.replaceWith(video); video.focus(); estado.textContent = '';
        video.play().catch(() => {});
      } catch (_) { estado.textContent = 'Vídeo indisponível. Continue pelo texto.'; abrir.disabled = false; }
    });
    caixa.append(abrir, estado);
  }
  if (n.tipo === 'camadas') {
    if (sobrio) {
      n.camadas.forEach(c => { const det = el(d, 'details', null, el(d, 'summary', { text: c.rotulo }), el(d, 'p', { text: c.texto })); caixa.append(det); });
    } else {
      let i = 0;
      const conteudo = el(d, 'div', { 'aria-live': 'polite' });
      const b = el(d, 'button', { class: 'btn abrir-camada', type: 'button', text: 'Abrir mais (1/' + n.camadas.length + ')' });
      b.addEventListener('click', () => {
        const c = n.camadas[i++];
        conteudo.append(el(d, 'section', { class: 'camada' }, el(d, 'h3', { text: c.rotulo }), el(d, 'p', { text: c.texto })));
        b.textContent = i === n.camadas.length ? 'Todas as camadas abertas' : `Abrir mais (${i + 1}/${n.camadas.length})`; b.disabled = i === n.camadas.length;
      });
      caixa.append(conteudo, b);
    }
  }
  if (n.tipo === 'dialogo') {
    const v = n.dialogo, p = v.personagem;
    caixa.append(el(d, 'div', { class: 'retrato', 'aria-hidden': 'true', text: '◉' }), el(d, 'h3', { text: p.nome }), el(d, 'p', { class: 'sob', text: p.papel }));
    if (p.avatar) caixa.prepend(el(d, 'img', { src: p.avatar, alt: '', width: '64', height: '64' }));
    v.falas.forEach(t => caixa.append(el(d, 'p', { text: t })));
    v.respostas.forEach(r => {
      const b = el(d, sobrio ? 'a' : 'button', { class: 'btn resposta', href: sobrio ? '#n' + r.vai : null, type: sobrio ? null : 'button', text: r.texto });
      if (!sobrio) b.addEventListener('click', () => ir(String(r.vai)));
      caixa.append(b);
    });
  }
  return caixa;
}

export function criarVisita(dados, { mover, modo, reduzido }) {
  const d = document, v = dados.grafo.visitas[0];
  let passo = 0, ativa = false, desvio = false, pausa = false, velocidade = 1, timer;
  const painel = el(d, 'nav', { class: 'visita', 'aria-label': 'Visita guiada' });
  const estado = el(d, 'span', { role: 'status' });
  const botao = (txt, fn, cls) => { const b = el(d,'button',{ type:'button', class: 'btn ' + (cls || ''), text:txt }); b.addEventListener('click', fn); return b; };
  function pintar() {
    clearTimeout(timer);
    const baixo = d.querySelector('.hud-baixo');
    if (modo() === 'ludico' && baixo) baixo.before(painel);
    else d.querySelector('header').after(painel);
    estado.textContent = !ativa ? v.nome : `${v.nome} · passo ${passo + 1}/${v.passos.length}${pausa ? ' · pausada' : ''}`;
    retomar.hidden = !desvio;
    retomar.textContent = `Voltar à visita (passo ${passo + 1})`;
    pausar.textContent = pausa ? 'Retomar visita' : 'Pausar visita';
    lista.hidden = !(reduzido || modo() === 'sobrio');
    if (ativa && !pausa && !desvio && !reduzido && modo() !== 'sobrio' && passo < v.passos.length - 1) timer = setTimeout(() => ir(passo + 1), v.segundos_por_passo * 1000 / velocidade);
  }
  function ir(i) { ativa = true; desvio = false; passo = Math.max(0,Math.min(v.passos.length - 1,i)); mover(String(v.passos[passo]), true); pintar(); }
  const inicio = botao('Visita guiada', () => { pausa = false; ir(0); }, 'iniciar-visita');
  const pausar = botao('Pausar visita', () => { pausa = !pausa; pintar(); }, 'pausar-visita');
  const retomar = botao('Voltar à visita', () => ir(passo), 'retomar-visita');
  const select = el(d, 'select', { 'aria-label': 'Velocidade da visita' });
  [0.5,1,2].forEach(n => select.append(el(d, 'option', { value:n, text:String(n).replace('.',',') + 'x', selected:n===1 })));
  select.addEventListener('change', () => { velocidade = Number(select.value); pintar(); });
  const lista = el(d,'ol');
  v.passos.forEach((id,i) => { const n = dados.grafo.nos.find(n => String(n.id) === String(id)); lista.append(el(d,'li',null,botao(n.titulo,() => ir(i)))); });
  painel.append(inicio, estado, select, pausar, botao('Recuar visita',() => ir(passo - 1),'recuar-visita'), botao('Seguinte',() => ir(passo + 1),'seguinte-visita'),retomar,lista);
  d.querySelector('header').after(painel); pintar();
  return { navegar() { if (ativa) { desvio = true; pintar(); } }, pausar() { pausa = true; pintar(); }, atualizar:pintar, get estado() { return {passo,ativa,desvio,pausa,velocidade}; } };
}
