// Efeitos sintetizados e mídia só tocam após gesto explícito do leitor.

// notas de cada efeito: [frequência Hz, início s, duração s, tipo, ganho]
const EFEITOS = {
  seguir: [[392, 0, 0.09, 'sine', 0.05], [523, 0.07, 0.12, 'sine', 0.04]],
  aprofundar: [[330, 0, 0.16, 'triangle', 0.05], [247, 0.12, 0.2, 'triangle', 0.05], [185, 0.26, 0.28, 'triangle', 0.045]],
  subir: [[247, 0, 0.12, 'triangle', 0.04], [330, 0.09, 0.14, 'triangle', 0.04], [440, 0.19, 0.2, 'triangle', 0.04]],
  otimista: [[523, 0, 0.22, 'sine', 0.04], [659, 0.06, 0.22, 'sine', 0.035], [784, 0.12, 0.34, 'sine', 0.035]],
  catastrofico: [[110, 0, 0.5, 'sawtooth', 0.025], [117, 0, 0.5, 'sawtooth', 0.025], [165, 0.1, 0.4, 'square', 0.012]],
  recuar: [[294, 0, 0.1, 'sine', 0.035]],
};

export function pintarInterruptorSom(botao, ligado) {
  botao.setAttribute('aria-checked', String(ligado));
  botao.querySelector('.rot').textContent = ligado ? 'Som: ligado' : 'Som: desligado';
}

export function criarSom() {
  let ligado = false, ctx = null, narracao = null, ambiente = null, sequencia = 0;
  function pararAudio(audio) {
    if (!audio) return;
    audio.pause(); audio.removeAttribute('src'); audio.load();
  }
  function pararTudo() {
    sequencia++;
    pararAudio(narracao); pararAudio(ambiente);
    narracao = null; ambiente = null;
  }
  async function abrir(endpoint, alvo, pedido) {
    try {
      const resposta = await fetch(endpoint, { cache: 'no-store', credentials: 'same-origin' });
      if (!resposta.ok) return false;
      const dados = await resposta.json();
      if (pedido !== sequencia) return false;
      if (typeof dados.url !== 'string' || !/^https:\/\//i.test(dados.url)) return false;
      const audio = new Audio(dados.url);
      audio.volume = 0.8;
      if (alvo === 'narracao') narracao = audio; else ambiente = audio;
      const tocando = audio.play();
      if (tocando && tocando.then) await tocando;
      return true;
    } catch (e) { return false; }
  }
  const api = {
    get ligado() { return ligado; },
    get criado() { return !!ctx; },
    ligar(v) { ligado = !!v; if (!ligado) pararTudo(); return ligado; },
    interromper() { pararTudo(); },
    ambiente(endpoint) {
      pararAudio(ambiente); ambiente = null;
      pararAudio(narracao); narracao = null;
      const pedido = ++sequencia;
      if (!ligado || !endpoint) return Promise.resolve(false);
      return abrir(endpoint, 'ambiente', pedido);
    },
    tocar(tipo) {
      if (!ligado || !EFEITOS[tipo]) return;
      try {
        const AC = window.AudioContext || window.webkitAudioContext;
        if (!AC) return;
        if (!ctx) ctx = new AC();
        if (ctx.state === 'suspended') ctx.resume();
        const t0 = ctx.currentTime + 0.01;
        for (const [f, ini, dur, tipoOnda, ganho] of EFEITOS[tipo]) {
          const o = ctx.createOscillator(), g = ctx.createGain();
          o.type = tipoOnda; o.frequency.value = f;
          g.gain.setValueAtTime(0, t0 + ini);
          g.gain.linearRampToValueAtTime(ganho, t0 + ini + 0.02);
          g.gain.exponentialRampToValueAtTime(0.0001, t0 + ini + dur);
          o.connect(g); g.connect(ctx.destination);
          o.start(t0 + ini); o.stop(t0 + ini + dur + 0.05);
        }
      } catch (e) { /* o áudio nunca derruba a página */ }
    },
    // O endpoint resolve URL temporária apenas para um UUID associado ao bloco.
    narrar(endpoint) {
      pararAudio(narracao); narracao = null;
      pararAudio(ambiente); ambiente = null;
      return abrir(endpoint, 'narracao', ++sequencia);
    },
  };
  return api;
}
