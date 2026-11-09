import { registar } from "../motor.js";

// Atmosfera «O quase-presente» (STAR-47, protótipo aprovado no STAR-51/07): cidade azul de vigilância,
// luz de varredura que desce com o scroll e incide nos cartões, celular que racha, grafo de registros,
// avisos de exemplo dispensáveis e espelho com salvaguardas. Tudo local: sem rede, sem biblioteca, sem gravar nada.
// Estado só nesta função; a rolagem é medida relativamente à raiz (a página tem o cabeçalho do site por cima).
registar("atmosfera:quase-presente", ({ el, reduzido, progresso }) => {
  const root = el.closest(".qp-raiz");
  const $ = (s, r = root) => r.querySelector(s);
  const $$ = (s, r = root) => [...r.querySelectorAll(s)];
  const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  const movel = () => innerWidth < 900;
  const TOPO = 76; // cabeçalho do site: o sticky começa abaixo dele
  let pausado = reduzido;
  if (reduzido) root.classList.add("qp-estatico");

  // ---------- a cidade (nós criados pela API do DOM) ----------
  function rnd(i) {
    const x = Math.sin(i * 91.7 + 13.3) * 43758.5453;
    return x - Math.floor(x);
  }
  function monta(id, n, wmin, wmax, hmin, hmax, seed) {
    let x = -2;
    const cont = $(id);
    for (let i = 0; i < n; i++) {
      const w = wmin + rnd(seed + i) * (wmax - wmin);
      const a = hmin + rnd(seed + i + 40) * (hmax - hmin);
      const d = document.createElement("div");
      d.className = "qp-pred";
      d.style.left = x.toFixed(1) + "%";
      d.style.width = w.toFixed(1) + "%";
      d.style.height = a.toFixed(0) + "%";
      cont.appendChild(d);
      x += w * (0.55 + rnd(seed + i + 9) * 0.5);
    }
  }
  monta("#qp-l3", 20, 7, 12, 38, 78, 1);
  monta("#qp-l2", 16, 8, 13, 26, 60, 100);
  monta("#qp-l1", 12, 9, 15, 14, 40, 200);
  const cam = [$("#qp-l3"), $("#qp-l2"), $("#qp-l1")];
  const K = [0.5, 0.9, 1.5];

  // ---------- o grafo de registros ----------
  const REG = ["Trajeto", "Compra", "Câmera", "Cadastro", "Mensagem", "Pontuação"];
  const NP = [[70, 70], [230, 30], [390, 70], [400, 250], [230, 300], [60, 250]];
  const C = [230, 170];
  const gsvg = $("#qp-grafo");
  const NS = gsvg.namespaceURI;
  const no = (tag, attrs, texto) => {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (texto) e.textContent = texto;
    gsvg.appendChild(e);
    return e;
  };
  const lig = NP.map((p) => no("path", { class: "qp-lig", pathLength: "1", d: `M${p[0]} ${p[1]}L${C[0]} ${C[1]}` }));
  NP.forEach((p, i) => {
    no("circle", { class: "qp-nr", cx: p[0], cy: p[1], r: 12 });
    no("text", { x: p[0], y: p[1] + 4, "text-anchor": "middle" }, String(i + 1));
  });
  no("circle", { class: "qp-perfil", cx: C[0], cy: C[1], r: 34 });
  no("text", { x: C[0], y: C[1] - 2, "text-anchor": "middle" }, "perfil de");
  no("text", { x: C[0], y: C[1] + 13, "text-anchor": "middle" }, "exemplo");
  const mira = no("circle", { class: "qp-mira", cx: NP[0][0], cy: NP[0][1], r: 22 });
  const chips = REG.map((r, i) => {
    const li = document.createElement("li");
    li.className = "qp-reg";
    li.textContent = `${i + 1} · ${r}`;
    $("#qp-regs").appendChild(li);
    return li;
  });
  function grafo(q) {
    lig.forEach((l, i) => l.style.setProperty("--d", (1 - clamp((q - (0.08 + i * 0.08)) / 0.14)).toFixed(3)));
    const m = clamp((q - 0.2) / 0.7) * 5;
    const i = Math.min(4, Math.floor(m));
    const f = m - i;
    const a = NP[i];
    const b = NP[i + 1];
    mira.setAttribute("cx", (a[0] + (b[0] - a[0]) * f).toFixed(1));
    mira.setAttribute("cy", (a[1] + (b[1] - a[1]) * f).toFixed(1));
    const alvo = f < 0.5 ? i : i + 1;
    chips.forEach((c, k) => c.classList.toggle("qp-alvo", k === alvo && q > 0.2));
  }

  // ---------- os avisos de exemplo (dispensáveis) ----------
  const ROTULO = "AVISO DE EXEMPLO · FICÇÃO";
  const AV = [
    "Sua rota de hoje foi comparada com a de ontem.",
    "Uma compra recente entrou no seu perfil de exemplo.",
    "Uma câmera registrou o seu trajeto de exemplo.",
    "Seu cadastro foi cruzado com outro cadastro.",
    "Uma mensagem de exemplo foi classificada como «rotina».",
    "Sua pontuação de exemplo mudou de 0,58 para 0,62.",
    "Nenhum destes avisos é real: é um exemplo de ficção.",
  ];
  let p2Atual = 0;
  const avs = AV.map((t, i) => {
    const d = document.createElement("div");
    d.className = "qp-aviso qp-fora";
    d.style.setProperty("--ar", ((i % 2 ? 1 : -1) * (0.6 + i * 0.2)).toFixed(1) + "deg");
    const b = document.createElement("b");
    b.textContent = ROTULO;
    const p = document.createElement("p");
    p.textContent = t;
    const x = document.createElement("button");
    x.type = "button";
    x.className = "qp-x";
    x.setAttribute("aria-label", "Dispensar este aviso de exemplo");
    x.textContent = "×";
    x.addEventListener("click", () => {
      d.dataset.d = "1";
      d.hidden = true;
      conta();
    });
    d.append(b, p, x);
    $("#qp-avisos").appendChild(d);
    return d;
  });
  function conta() {
    const n = avs.filter((a) => !a.dataset.d).length;
    $("#qp-n-av").textContent = n + (n === 1 ? " aviso de exemplo" : " avisos de exemplo");
  }
  function entra(q) {
    avs.forEach((a, i) => a.classList.toggle("qp-fora", q < 0.12 + i * 0.09));
  }
  $("#qp-restaura").addEventListener("click", () => {
    avs.forEach((a) => {
      delete a.dataset.d;
      a.hidden = false;
    });
    conta();
    entra(p2Atual);
  });

  // ---------- progressos (cada ato mede o próprio elemento) ----------
  const pista = $("#qp-pista1");
  const cel1 = $("#qp-cel1");
  const cel2 = $("#qp-cel2");
  const enche = $(".qp-enche", cel1);
  const faixaEl = enche.parentElement;
  const espelho = $("#qp-espelho");
  let crackAtual = 0;
  function ato1() {
    let crack, faixa;
    if (reduzido) {
      crack = 1;
      faixa = 1;
    } else if (movel()) {
      const r = cel1.getBoundingClientRect();
      const vh = innerHeight;
      crack = clamp((vh * 0.9 - r.top) / (r.height * 0.8));
      faixa = clamp((vh * 0.9 - r.top - r.height * 0.25) / (r.height * 0.7));
    } else {
      const r = pista.getBoundingClientRect();
      const p = clamp(-(r.top - TOPO) / Math.max(1, pista.offsetHeight - (innerHeight - TOPO)));
      crack = clamp((p - 0.05) / 0.4);
      faixa = clamp((p - 0.2) / 0.35);
    }
    crackAtual = crack;
    root.style.setProperty("--rk", (1 - crack).toFixed(3));
    enche.style.setProperty("--q", faixa.toFixed(3));
    faixaEl.style.setProperty("--q", faixa.toFixed(3));
  }
  function ato2() {
    const r = $("#qp-ato2").getBoundingClientRect();
    const q = reduzido ? 1 : clamp((innerHeight * 0.85 - r.top) / (r.height * 0.85));
    p2Atual = q;
    grafo(q);
    entra(q);
  }
  function ato3() {
    const r = cel2.getBoundingClientRect();
    const q = reduzido ? 1 : clamp((innerHeight * 0.9 - r.top) / (r.height * 0.6));
    espelho.style.setProperty("--e", q.toFixed(3));
  }

  // ---------- a luz de vigilância: a varredura segue o scroll da raiz ----------
  const varre = $("#qp-varre");
  let vig = [];
  let PX = innerWidth * 0.6;
  let cx = PX;
  let tremor = 0;
  const reflexo = $("#qp-reflexo");
  addEventListener("pointermove", (e) => {
    if (e.pointerType === "touch" || movel()) return;
    PX = e.clientX;
    cx = PX;
    const r = cel2.getBoundingClientRect();
    reflexo.style.setProperty("--rx", (clamp((e.clientX - r.left) / r.width) * 100).toFixed(0) + "%");
  }, { passive: true });
  const yRaiz = () => -root.getBoundingClientRect().top;
  function varredura() {
    const vh = innerHeight;
    const h = Math.max(1, root.offsetHeight - vh);
    const f = reduzido ? 0.3 : clamp(yRaiz() / h);
    const BY = vh * (0.14 + 0.8 * f);
    varre.style.transform = `translate3d(0,${BY.toFixed(0)}px,0)`;
    for (const e of vig) {
      const r = e.getBoundingClientRect();
      if (r.bottom < -200 || r.top > vh + 200) continue;
      const my = r.top + r.height / 2;
      const dy = my - BY;
      const li = clamp(1 - Math.max(0, Math.abs(dy) - r.height / 2) / 260);
      const s = e.style;
      s.setProperty("--lx", (cx - r.left).toFixed(0) + "px");
      s.setProperty("--ly", (BY - r.top).toFixed(0) + "px");
      s.setProperty("--li", li.toFixed(2));
      s.setProperty("--sy", (dy > 0 ? 10 : -4) + "px");
    }
    // tremor do celular só enquanto racha (desktop, sem pausa)
    if (!reduzido && !pausado && crackAtual > 0.02 && crackAtual < 0.98 && !movel()) {
      tremor = 1.6;
      const t = performance.now();
      cel1.style.transform = `translate(${(Math.sin(t / 23) * tremor).toFixed(2)}px,${(Math.cos(t / 31) * tremor).toFixed(2)}px)`;
    } else if (tremor) {
      tremor = 0;
      cel1.style.transform = "";
    }
  }
  function atualiza() {
    ato1();
    ato2();
    ato3();
    varredura();
  }
  function medir() {
    vig = $$(".qp-vig");
    atualiza();
  }

  // ---------- ato 3: salvaguardas e espelho ----------
  const R = {
    evidencia: ["Evidência", "Prioridade: evidência. Antes de uma pontuação valer, quem a usa mostra os dados, o método e a taxa de erro por grupo.", "Exemplo fictício: uma pontuação de risco sem ficha de erros por bairro."],
    escolha: ["Escolha", "Prioridade: escolha. A pessoa pode recusar a coleta e continuar usando o serviço, sem punição escondida.", "Exemplo fictício: um aplicativo que só abre com acesso total ao histórico de rotas."],
    reparacao: ["Reparação", "Prioridade: reparação. Quando a pontuação erra, há um caminho curto, humano e rápido para corrigir o registro e o dano.", "Exemplo fictício: um cadastro com erro que continua circulando meses depois."],
  };
  const sv = () => {
    const c = $("input[name=qp-sv]:checked");
    return c && R[c.value] ? c.value : null;
  };
  $("#qp-salv").addEventListener("change", () => {
    const v = sv();
    $("#qp-eco").textContent = v ? R[v][0] : "";
  });
  $("#qp-registrar").addEventListener("click", () => {
    const v = sv();
    const out = $("#qp-registro");
    if (!v) {
      out.textContent = "Escolha primeiro a salvaguarda mais urgente.";
      return;
    }
    const d = $("#qp-f-dec").value.trim();
    out.textContent = R[v][1] + (d ? " Decisão para contestar: " + d + "." : "") + " Pode pedir revisão: " + $("#qp-f-quem").value.toLowerCase() + "." + ($("#qp-f-ex").checked ? " " + R[v][2] : "");
  });
  $("#qp-limpar").addEventListener("click", () => {
    $$("input[name=qp-sv]").forEach((i) => (i.checked = false));
    $("#qp-f-dec").value = "";
    $("#qp-f-quem").selectedIndex = 0;
    $("#qp-f-ex").checked = true;
    $("#qp-registro").textContent = "";
    $("#qp-eco").textContent = "";
  });

  // ---------- loop, pausa, visibilidade ----------
  let raf = 0;
  function frame() {
    raf = 0;
    if (pausado || document.hidden) return;
    if (movel()) cx = innerWidth * 0.5;
    else cx += (PX - cx) * 0.1;
    atualiza();
    if (!movel()) {
      const dx = (cx / innerWidth - 0.5) * 2;
      const y = yRaiz();
      cam.forEach((c, i) => (c.style.transform = `translate3d(${(-dx * K[i] * 10).toFixed(1)}px,${(-y * 0.02 * K[i]).toFixed(1)}px,0)`));
    }
    raf = requestAnimationFrame(frame);
  }
  function liga() {
    if (!raf && !pausado && !document.hidden) raf = requestAnimationFrame(frame);
  }
  function para() {
    if (raf) {
      cancelAnimationFrame(raf);
      raf = 0;
    }
  }
  document.addEventListener("visibilitychange", () => (document.hidden ? para() : liga()));
  const bt = $("#qp-pausa");
  function rotulo() {
    bt.textContent = pausado ? "Retomar movimento" : "Pausar movimento";
    bt.setAttribute("aria-pressed", String(pausado));
    root.classList.toggle("qp-pausado", pausado);
  }
  if (reduzido) {
    bt.hidden = true; // tudo já está estático: o botão não aparece
  } else {
    bt.addEventListener("click", () => {
      pausado = !pausado;
      rotulo();
      if (pausado) para();
      else liga();
    });
    rotulo();
  }
  addEventListener("resize", medir);
  addEventListener("load", medir);
  conta();
  medir();
  if (reduzido) {
    avs.forEach((a) => a.classList.remove("qp-fora"));
    entra(1);
  } else {
    liga();
    // o scroll também atualiza com o loop parado (o texto dos atos continua a trocar)
    progresso(() => {
      if (pausado) atualiza();
    });
  }
});
