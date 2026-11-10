// som.js: efeitos sonoros discretos sintetizados com WebAudio (sem ficheiros externos) e a narração por bloco.
// O som vem DESLIGADO por padrão e guarda-se em localStorage (em try/catch). Nada toca sem um gesto do leitor:
// o AudioContext só é criado dentro de `tocar`/`ligar`, chamados a partir de um clique ou tecla.

const CHAVE = 'stargate.som';
function ler() { try { return localStorage.getItem(CHAVE) === '1'; } catch (e) { return false; } }
function gravar(v) { try { localStorage.setItem(CHAVE, v ? '1' : '0'); } catch (e) { /* sem armazenamento: segue sem guardar */ } }

// notas de cada efeito: [frequência Hz, início s, duração s, tipo, ganho]
const EFEITOS = {
  seguir: [[392, 0, 0.09, 'sine', 0.05], [523, 0.07, 0.12, 'sine', 0.04]],
  aprofundar: [[330, 0, 0.16, 'triangle', 0.05], [247, 0.12, 0.2, 'triangle', 0.05], [185, 0.26, 0.28, 'triangle', 0.045]],
  subir: [[247, 0, 0.12, 'triangle', 0.04], [330, 0.09, 0.14, 'triangle', 0.04], [440, 0.19, 0.2, 'triangle', 0.04]],
  otimista: [[523, 0, 0.22, 'sine', 0.04], [659, 0.06, 0.22, 'sine', 0.035], [784, 0.12, 0.34, 'sine', 0.035]],
  catastrofico: [[110, 0, 0.5, 'sawtooth', 0.025], [117, 0, 0.5, 'sawtooth', 0.025], [165, 0.1, 0.4, 'square', 0.012]],
  recuar: [[294, 0, 0.1, 'sine', 0.035]],
};

export function criarSom() {
  let ligado = ler(), ctx = null;
  const api = {
    get ligado() { return ligado; },
    get criado() { return !!ctx; },
    ligar(v) { ligado = !!v; gravar(ligado); if (ligado) api.tocar('seguir'); return ligado; },
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
    // narração: toca `caminho` (ficheiro) a pedido do leitor; devolve uma promessa que nunca rejeita
    narrar(caminho) {
      return new Promise((res) => {
        try { const a = new Audio(caminho); a.volume = 0.8; const p = a.play(); if (p && p.then) p.then(() => res(true), () => res(false)); else res(true); }
        catch (e) { res(false); }
      });
    },
  };
  return api;
}
