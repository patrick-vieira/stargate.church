import { registar } from "../motor.js";

// Atmosfera «A IA afetiva» (STAR-44, protótipo aprovado no STAR-51): cidade ao entardecer cuja
// janela acende com o progresso, conversa que se escreve ao rolar, cartões em cascata e uma
// comparação ficção × 2026. Sem lib externa: tudo é DOM e CSS. Escopo: .aa-raiz.
registar("atmosfera:ia-afetiva", async ({ el, reduzido }) => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const raiz = el.closest(".aa-raiz");
  const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  const movel = () => innerWidth < 900;
  let pausado = reduzido;
  if (reduzido) raiz.classList.add("aa-estatico");

  // ---------- a cidade: prédios com janelas que acendem ----------
  const rnd = (i) => {
    const x = Math.sin(i * 91.7 + 13.3) * 43758.5453;
    return x - Math.floor(x);
  };
  function monta(id, n, wmin, wmax, hmin, hmax, seed) {
    let x = -2;
    let h1 = "";
    let h2 = "";
    for (let i = 0; i < n; i++) {
      const w = wmin + rnd(seed + i) * (wmax - wmin);
      const h = hmin + rnd(seed + i + 40) * (hmax - hmin);
      const g = `left:${x.toFixed(1)}%;width:${w.toFixed(1)}%;height:${h.toFixed(0)}%;--o:${(0.35 + rnd(seed + i + 80) * 0.65).toFixed(2)};--an:${rnd(seed + i + 120) < 0.5 ? 0 : 90}deg;--gp:${28 + Math.floor(rnd(seed + i + 7) * 34)}px`;
      h1 += `<div class="aa-pred" style="${g}"></div>`;
      h2 += `<div class="aa-pred aa-z" style="${g}"></div>`;
      x += w * (0.55 + rnd(seed + i + 9) * 0.5);
    }
    $(id).innerHTML = h1;
    $(id + "z").innerHTML = h2;
  }
  monta("#aa-l3", 20, 7, 12, 38, 78, 1);
  monta("#aa-l2", 16, 8, 13, 26, 60, 100);
  monta("#aa-l1", 12, 9, 15, 14, 40, 200);

  // ---------- a conversa (diálogo inventado) ----------
  const MSG = [
    ["u", "Cheguei. Dia comprido."],
    ["a", "Que bom que chegou. Quer começar pelo que pesou mais?"],
    ["u", "A reunião das cinco. Ninguém ouviu minha ideia."],
    ["a", "Você preparou isso a semana toda. Quer ensaiar como dizer amanhã?"],
    ["u", "Quero. Mas primeiro só conversar."],
    ["a", "Estou aqui. E depois, que tal ligar para a Bia? Ela perguntou de você."],
  ];
  const TOT = MSG.reduce((a, m) => a + m[1].length, 0);
  const chat = $("#aa-chat");
  const bolhas = MSG.map((m) => {
    const e = document.createElement("div");
    e.className = "aa-b aa-" + m[0];
    chat.appendChild(e);
    return e;
  });
  $("#aa-chat-sr").textContent = MSG.map((m) => (m[0] === "u" ? "Você: " : "Assistente: ") + m[1]).join(" ");
  let nVis = -1;
  function escreve(n) {
    // retoque 2 (REVISAO-5): a 1.ª bolha já está inteira quando o painel entra
    n = Math.max(Math.round(n), MSG[0][1].length);
    if (n === nVis) return;
    nVis = n;
    let acc = 0;
    MSG.forEach((m, i) => {
      const l = m[1].length;
      const k = clamp(n - acc, 0, l);
      acc += l;
      const e = bolhas[i];
      e.textContent = m[1].slice(0, k);
      e.classList.toggle("aa-v", k > 0);
      if (k > 0 && k < l && !reduzido) {
        const c = document.createElement("span");
        c.className = "aa-cur";
        e.appendChild(c);
      }
    });
  }

  // ---------- ato 2: cartões em cascata alternada ----------
  const carts = $$(".aa-cart", raiz);
  const ordem = [0, 3, 1, 4, 2, 5];
  function cascata() {
    const vh = innerHeight;
    carts.forEach((c, i) => {
      if (c.classList.contains("aa-v")) return;
      if (c.getBoundingClientRect().top < vh * 0.9) {
        setTimeout(() => c.classList.add("aa-v"), reduzido ? 0 : ordem[i] * 90);
      }
    });
  }

  // ---------- ato 3: os limites e a comparação ----------
  const NOTAS = {
    avisar: "Dizer sempre que é um software evita atribuir à voz uma vida interior que a fluência não prova.",
    pausa: "Sugerir pausas e outras pessoas mantém a conversa como parte da vida, não como substituta dela.",
    apagar: "Poder apagar a memória quando quiser deixa o humano livre para sair, com o que já contou.",
  };
  const ROT = {
    avisar: "avisar sempre que é um software",
    pausa: "sugerir pausas e outras pessoas",
    apagar: "apagar a memória quando quiser",
  };
  const NOTA0 = "Escolha um limite ao lado: a comparação mostra o que um bom produto faria.";
  const limite = () => {
    const c = $("input[name=aa-lim]:checked", raiz);
    return c ? c.value : null;
  };
  function escolhe() {
    const l = limite();
    $$(".aa-comp tbody tr", raiz).forEach((r) => r.classList.toggle("aa-sel", r.dataset.r === l));
    $("#aa-nota-c").textContent = l ? NOTAS[l] : NOTA0;
  }
  $("#aa-limites").addEventListener("change", escolhe);
  $("#aa-registrar").addEventListener("click", () => {
    const l = limite();
    const n = $("#aa-f-nome").value.trim();
    $("#aa-registro").textContent = l
      ? `Registrado nesta página: ${n ? n + " deve " : "o assistente deve "}${ROT[l]}. Conversa: ${$("#aa-f-quando").value.toLowerCase()}${$("#aa-f-aval").checked ? "; pede aval antes de guardar algo novo" : ""}.`
      : "Escolha primeiro o limite mais importante.";
  });
  $("#aa-limpar").addEventListener("click", () => {
    $$("input[name=aa-lim]", raiz).forEach((i) => (i.checked = false));
    $("#aa-f-nome").value = "";
    $("#aa-f-quando").selectedIndex = 0;
    $("#aa-f-aval").checked = true;
    $("#aa-registro").textContent = "";
    escolhe();
  });

  // ---------- a luz da janela ilumina os componentes vindos da direção dela ----------
  const cid = $("#aa-cidade");
  const jan = $("#aa-janela");
  const cam = ["#aa-l3", "#aa-l3z", "#aa-l2", "#aa-l2z", "#aa-l1", "#aa-l1z"].map((s) => $(s));
  const K = [0.5, 0.5, 0.9, 0.9, 1.5, 1.5];
  let quentes = [];
  let WX = 0;
  let WY = 0;
  let bAtual = -1;
  let sY = -1;
  let PX = innerWidth / 2;
  let cx = PX;
  function medeJanela() {
    const r = jan.getBoundingClientRect();
    WX = r.left + r.width / 2;
    WY = r.top + r.height / 2;
  }
  function brilho() {
    const h = document.documentElement.scrollHeight - innerHeight;
    const f = h > 0 ? scrollY / h : 1;
    return reduzido ? 1 : 0.25 + 0.75 * clamp(f * 1.15);
  }
  function luz() {
    const vh = innerHeight;
    const b = bAtual < 0 ? 1 : bAtual;
    for (const e of quentes) {
      const r = e.getBoundingClientRect();
      if (r.bottom < -200 || r.top > vh + 200) continue;
      const mx = r.left + r.width / 2;
      const my = r.top + r.height / 2;
      const dx = mx - WX;
      const dy = my - WY;
      const d = Math.hypot(dx, dy) || 1;
      const m = 5 + 18 * Math.max(0, 1 - d / 1400);
      const s = e.style;
      const ex = Math.max(r.left - WX, 0, WX - r.right);
      const ey = Math.max(r.top - WY, 0, WY - r.bottom);
      const de = Math.hypot(ex, ey);
      s.setProperty("--lx", (WX - r.left).toFixed(0) + "px");
      s.setProperty("--ly", (WY - r.top).toFixed(0) + "px");
      s.setProperty("--li", (Math.pow(Math.max(0, 1 - de / 1100), 0.9) * clamp(b * 1.1, 0.3, 1)).toFixed(2));
      s.setProperty("--sx", Math.round(((dx / d) * m) / 3) * 3 + "px");
      s.setProperty("--sy", Math.round(((dy / d) * m * 0.6 + 6) / 3) * 3 + "px");
    }
  }
  function progressoAto1() {
    if (movel() || reduzido) {
      const r = $("#aa-chat-cx").getBoundingClientRect();
      return reduzido ? 1 : clamp(((innerHeight * 0.9 - r.top) / (Math.max(r.height, 1) + innerHeight * 0.25)) * 1.25);
    }
    const a = $("#aa-ato1");
    const r = a.getBoundingClientRect();
    return clamp((-r.top / Math.max(1, a.offsetHeight - innerHeight) - 0.04) / 0.62);
  }
  addEventListener(
    "pointermove",
    (e) => {
      if (e.pointerType === "touch" || movel()) return;
      PX = e.clientX;
    },
    { passive: true },
  );
  function atualiza(force) {
    const b = brilho();
    if (force || Math.abs(b - bAtual) > 0.004) {
      bAtual = b;
      cid.style.setProperty("--b", b.toFixed(3));
    }
    if (force || scrollY !== sY) {
      sY = scrollY;
      escreve(progressoAto1() * TOT);
      cascata();
      luz();
    }
  }

  // ---------- loop, pausa, visibilidade ----------
  let raf = 0;
  let ag = false;
  function frame() {
    raf = 0;
    if (pausado || document.hidden) return;
    atualiza(false);
    if (!movel()) {
      cx += (PX - cx) * 0.08;
      const dx = (cx / innerWidth - 0.5) * 2;
      cam.forEach((c, i) => {
        c.style.transform = `translate3d(${(-dx * K[i] * 10).toFixed(1)}px,${(-scrollY * 0.02 * K[i]).toFixed(1)}px,0)`;
      });
    }
    raf = requestAnimationFrame(frame);
  }
  function liga() {
    if (!raf && !pausado && !document.hidden) raf = requestAnimationFrame(frame);
  }
  addEventListener(
    "scroll",
    () => {
      if (ag) return;
      ag = true;
      requestAnimationFrame(() => {
        ag = false;
        if (pausado) atualiza(false);
      });
    },
    { passive: true },
  );
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      if (raf) {
        cancelAnimationFrame(raf);
        raf = 0;
      }
    } else liga();
  });
  const bt = $("#aa-pausa");
  function rotulo() {
    bt.textContent = reduzido ? "movimento pausado (modo reduzido)" : pausado ? "retomar movimento" : "pausar movimento";
    bt.setAttribute("aria-pressed", String(pausado));
    raiz.classList.toggle("aa-pausado", pausado);
  }
  if (reduzido) bt.disabled = true;
  bt.addEventListener("click", () => {
    if (reduzido) return;
    pausado = !pausado;
    rotulo();
    if (pausado) {
      if (raf) {
        cancelAnimationFrame(raf);
        raf = 0;
      }
    } else liga();
  });
  rotulo();
  addEventListener("resize", () => {
    medeJanela();
    quentes = $$(".aa-quente", raiz);
    atualiza(true);
  });
  quentes = $$(".aa-quente", raiz);
  medeJanela();
  escolhe();
  atualiza(true);
  addEventListener("load", () => {
    medeJanela();
    atualiza(true);
  });
  if (reduzido) {
    escreve(TOT);
    carts.forEach((c) => c.classList.add("aa-v"));
  } else liga();
});
