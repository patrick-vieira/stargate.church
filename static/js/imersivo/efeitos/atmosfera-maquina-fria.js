import { registar } from "../motor.js";

// Atmosfera «A máquina fria» (STAR-41, protótipo aprovado no STAR-51): lâmpada que segue o
// cursor, console que escreve ao rolar, corredor 3D com camadas e medidor de risco.
// A lib three só baixa quando o corredor entra em vista; com movimento reduzido nem isso.
registar("atmosfera:maquina-fria", async ({ el, reduzido }) => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const raiz = el.closest(".am-raiz");
  const S = raiz.style;
  let pausado = reduzido;
  let risco = 0.22;
  const t0 = performance.now();
  const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  if (reduzido) raiz.classList.add("am-estatico");

  // grão de filme: tile gerado em canvas
  {
    const c = document.createElement("canvas");
    c.width = c.height = 160;
    const x = c.getContext("2d");
    const d = x.createImageData(160, 160);
    for (let i = 0; i < d.data.length; i += 4) {
      const v = (Math.random() * 255) | 0;
      d.data[i] = d.data[i + 1] = d.data[i + 2] = v;
      d.data[i + 3] = 255;
    }
    x.putImageData(d, 0, 0);
    $("#am-grao").style.backgroundImage = `url(${c.toDataURL("image/png")})`;
  }

  // ---------- terminal que escreve ao rolar ----------
  const LINHAS = [
    "> CONSOLE 7 · SESSÃO ABERTA",
    "> AÇÃO RECOMENDADA: PROSSEGUIR",
    "> AUDITORIA DA DECISÃO: INDISPONÍVEL",
    "> INTERRUPÇÃO HUMANA: NÃO CONFIGURADA",
    "> CONFIRMAR? [S/N]",
  ];
  const TOTAL = LINHAS.reduce((a, l) => a + l.length, 0);
  const tl = $("#am-term-linhas");
  tl.innerHTML = LINHAS.map(() => '<div class="am-lin"><span class="v"></span><span class="am-o"></span></div>').join("");
  const linEls = $$(".am-lin", tl);
  let nVis = -1;
  function escreve(n) {
    n = Math.round(n);
    if (n === nVis) return;
    nVis = n;
    let r = n;
    let front = LINHAS.length - 1;
    let achou = false;
    linEls.forEach((li, i) => {
      const l = LINHAS[i];
      const k = clamp(r, 0, l.length);
      r -= l.length;
      li.children[0].textContent = l.slice(0, k);
      li.children[1].textContent = l.slice(k);
      const c = li.querySelector(".am-cur");
      if (c) c.remove();
      if (!achou && k < l.length) {
        front = i;
        achou = true;
      }
    });
    const c = document.createElement("span");
    c.className = "am-cur";
    linEls[front].insertBefore(c, linEls[front].children[1]);
  }

  // ---------- a lâmpada: mola, cabo, poça de luz, brilho ----------
  const bulbo = $("#am-bulbo");
  const cabo = $("#am-cabo");
  const poca = $("#am-poca");
  let TX = innerWidth * 0.62;
  let TY = innerHeight * 0.34;
  let bx = TX;
  let by = TY;
  let vx = 0;
  let vy = 0;
  let ax = TX;
  let LX = bx;
  let LY = by;
  let brilho = 0.4;
  addEventListener("pointermove", (ev) => {
    if (ev.pointerType === "touch" || innerWidth < 900) return;
    TX = ev.clientX;
    TY = ev.clientY;
  }, { passive: true });
  // posição de rolagem relativa à atmosfera (a página tem cabeçalho do site por cima)
  const yRaiz = () => -raiz.getBoundingClientRect().top;
  function brilhoAlvo(t) {
    const vh = innerHeight;
    const y = yRaiz();
    const h = raiz.offsetHeight - vh;
    const acende = Math.min(1, (t - t0) / 2000) * 0.4;
    const rampa = clamp(y / (vh * 0.3)) * 0.4 + clamp((y - vh * 0.3) / (vh * 1.3)) * 0.6;
    const apaga = 1 - clamp((y - (h - vh * 1.1)) / (vh * 1.0)) * 0.78;
    return Math.max(acende, rampa) * apaga;
  }
  function atualizaLampada(t) {
    if (innerWidth < 900) {
      const y = yRaiz();
      TX = innerWidth * (0.5 + 0.32 * Math.sin(y / 340));
      TY = innerHeight * (0.3 + 0.07 * Math.cos(y / 500));
    }
    vx = (vx + (TX - bx) * 0.07) * 0.82;
    vy = (vy + (TY - by) * 0.07) * 0.82;
    bx += vx;
    by += vy;
    ax += (TX - ax) * 0.035;
    LX = bx;
    LY = by;
    brilho = brilhoAlvo(t);
    const f = risco > 0.6 ? 1 + Math.sin(t / 37) * Math.sin(t / 113) * 0.1 * (risco - 0.5) : 1;
    S.setProperty("--brilho", clamp(brilho * f, 0, 1).toFixed(3));
    bulbo.style.transform = `translate3d(${bx.toFixed(1)}px,${by.toFixed(1)}px,0)`;
    poca.style.transform = `translate3d(${bx.toFixed(1)}px,${by.toFixed(1)}px,0)`;
    cabo.setAttribute("x1", ax.toFixed(1));
    cabo.setAttribute("x2", bx.toFixed(1));
    cabo.setAttribute("y2", (by - 13).toFixed(1));
  }
  function lampadaEstatica() {
    bx = LX = innerWidth * 0.62;
    by = LY = innerHeight * 0.3;
    ax = bx;
    S.setProperty("--brilho", ".85");
    bulbo.style.transform = `translate3d(${bx}px,${by}px,0)`;
    poca.style.transform = `translate3d(${bx}px,${by}px,0)`;
    cabo.setAttribute("x1", ax);
    cabo.setAttribute("x2", bx);
    cabo.setAttribute("y2", by - 13);
  }

  // luz nos componentes: sombra oposta à lâmpada, borda e superfície acesas
  let litEls = [];
  function luzNosComponentes() {
    const vw = innerWidth;
    const vh = innerHeight;
    const rs = litEls.map((e) => e.getBoundingClientRect());
    for (let i = 0; i < litEls.length; i++) {
      const r = rs[i];
      if (r.bottom < -240 || r.top > vh + 240 || r.right < -240 || r.left > vw + 240) continue;
      const e = litEls[i];
      const cx = r.left + r.width / 2;
      const cy = r.top + r.height / 2;
      const dx = cx - LX;
      const dy = cy - LY;
      const d = Math.hypot(dx, dy) || 1;
      const m = 5 + 22 * Math.max(0, 1 - d / 1100);
      const s = e.style;
      s.setProperty("--sx", ((dx / d) * m).toFixed(1) + "px");
      s.setProperty("--sy", ((dy / d) * m + 3).toFixed(1) + "px");
      s.setProperty("--sb", Math.min(46, 14 + d / 42).toFixed(0) + "px");
      if (e.classList.contains("am-lit")) {
        const ex = Math.max(r.left - LX, 0, LX - r.right);
        const ey = Math.max(r.top - LY, 0, LY - r.bottom);
        const de = Math.hypot(ex, ey);
        s.setProperty("--lx", (LX - r.left).toFixed(0) + "px");
        s.setProperty("--ly", (LY - r.top).toFixed(0) + "px");
        s.setProperty("--li", (Math.pow(Math.max(0, 1 - de / 480), 0.8) * clamp(brilho * 1.2, 0.35, 1)).toFixed(2));
        if (e.matches(".am-fluxo .am-cartao") && !reduzido) {
          const nx = clamp(((LX - cx) / vw) * -1, -0.5, 0.5);
          const ny = clamp((LY - cy) / vh, -0.5, 0.5);
          s.setProperty("--ry", (nx * 10).toFixed(1) + "deg");
          s.setProperty("--rx", (ny * -8).toFixed(1) + "deg");
        }
      }
    }
  }

  // ---------- poeira no feixe (canvas 2D) ----------
  const pc = $("#am-poeira");
  const px = pc.getContext("2d");
  let poeira = [];
  function dimPoeira() {
    pc.width = innerWidth;
    pc.height = innerHeight;
    poeira = Array.from({ length: innerWidth < 900 ? 34 : 70 }, () => ({
      x: Math.random() * innerWidth,
      y: Math.random() * innerHeight,
      r: 0.6 + Math.random() * 1.3,
      vx: (Math.random() - 0.5) * 0.18,
      vy: -0.05 - Math.random() * 0.16,
      f: Math.random() * 6,
    }));
  }
  function desenhaPoeira(t) {
    px.clearRect(0, 0, pc.width, pc.height);
    const R = innerWidth < 900 ? 220 : 340;
    for (const p of poeira) {
      p.x += p.vx + Math.sin(t / 2200 + p.f) * 0.12;
      p.y += p.vy;
      if (p.y < -5) p.y = innerHeight + 5;
      if (p.x < -5) p.x = innerWidth + 5;
      if (p.x > innerWidth + 5) p.x = -5;
      const d = Math.hypot(p.x - LX, p.y - LY);
      const a = clamp(1 - d / R) * clamp(brilho * 1.2, 0.1, 1);
      if (a < 0.02) continue;
      px.fillStyle = `rgba(255,214,140,${(a * 0.75).toFixed(2)})`;
      px.beginPath();
      px.arc(p.x, p.y, p.r, 0, 6.283);
      px.fill();
    }
  }

  // ---------- corte frontal CSS (fallback e 390) ----------
  const anel = $("#am-anel");
  const corte = $("#am-corte");
  const ato1 = $("#am-ato1");
  const ato2 = $("#am-ato2");
  const qs = [];
  for (let i = 0; i < 12; i++) {
    const q = document.createElement("div");
    q.className = "am-q";
    const s = 0.94 * Math.pow(0.76, i);
    q.style.width = s * 100 + "%";
    q.style.height = s * 86 + "%";
    anel.appendChild(q);
    qs.push(q);
  }
  let cena3d = null;
  let passoAtual = -1;
  function progresso(e) {
    const r = e.getBoundingClientRect();
    return clamp(-r.top / Math.max(1, e.offsetHeight - innerHeight));
  }
  const visivel2 = () => {
    const r = ato2.getBoundingClientRect();
    return r.bottom > 0 && r.top < innerHeight;
  };
  function atualizaScroll() {
    const p1 = progresso(ato1);
    escreve(reduzido ? TOTAL : Math.min(1, p1 / 0.72) * TOTAL);
    const p2 = reduzido ? 0.5 : progresso(ato2);
    const passo = Math.min(12, Math.floor(p2 * 12.999));
    if (passo !== passoAtual) {
      passoAtual = passo;
      $("#am-passo").textContent = `passo ${passo}/12`;
      qs.forEach((q, i) => q.classList.toggle("am-on", i < passo + 3));
    }
    corte.style.setProperty("--zoom", (1 + p2 * 2.4).toFixed(3));
    if (cena3d) cena3d.alvo = p2;
  }
  let ag = false;
  function agenda() {
    if (ag) return;
    ag = true;
    requestAnimationFrame(() => {
      ag = false;
      atualizaScroll();
      if (pausado) {
        luzNosComponentes();
        if (cena3d && visivel2()) cena3d.render(performance.now(), true);
      }
    });
  }
  addEventListener("scroll", agenda, { passive: true });

  // ---------- three.js: corredor que avança com o scroll (sob demanda) ----------
  async function carregaCorredor() {
    if (reduzido) return;
    let THREE;
    try {
      THREE = await import("three");
    } catch (_) {
      return;
    }
    try {
      montaCena(THREE);
    } catch (_) {
      cena3d = null;
    }
  }
  function montaCena(THREE) {
    const cv = $("#am-corredor");
    const movel = innerWidth < 900;
    const rd = new THREE.WebGLRenderer({ canvas: cv, antialias: false, powerPreference: "low-power" });
    const pr = Math.min(devicePixelRatio || 1, 1.5) * (movel ? 0.8 : 0.75);
    rd.setPixelRatio(pr);
    rd.setClearColor(0x0b0c0e, 1);
    rd.setSize(innerWidth, innerHeight, false);
    const sc = new THREE.Scene();
    sc.fog = new THREE.FogExp2(0x0e1217, 0.036);
    const cam = new THREE.PerspectiveCamera(movel ? 74 : 60, innerWidth / innerHeight, 0.1, 120);
    const L = 72;
    const LW = 6;
    const LH = 3.6;
    const mCh = new THREE.MeshStandardMaterial({ color: 0x2a313a, roughness: 0.55, metalness: 0.55 });
    const mFl = new THREE.MeshStandardMaterial({ color: 0x1b2027, roughness: 0.32, metalness: 0.85 });
    const mTe = new THREE.MeshStandardMaterial({ color: 0x14181d, roughness: 0.7, metalness: 0.3 });
    const fl = new THREE.Mesh(new THREE.PlaneGeometry(LW, L + 8), mFl);
    fl.rotation.x = -Math.PI / 2;
    fl.position.set(0, 0, -L / 2 + 2);
    sc.add(fl);
    const te = new THREE.Mesh(new THREE.PlaneGeometry(LW, L + 8), mTe);
    te.rotation.x = Math.PI / 2;
    te.position.set(0, LH, -L / 2 + 2);
    sc.add(te);
    for (const s of [-1, 1]) {
      const w = new THREE.Mesh(new THREE.PlaneGeometry(L + 8, LH), mTe);
      w.rotation.y = (-s * Math.PI) / 2;
      w.position.set((s * LW) / 2, LH / 2, -L / 2 + 2);
      sc.add(w);
    }
    const FILAS = 12;
    const DZ = 5.4;
    const Z0 = -3;
    const cab = new THREE.InstancedMesh(new THREE.BoxGeometry(0.9, 2.7, 3.6), mCh, FILAS * 2);
    const m4 = new THREE.Matrix4();
    const lg = new THREE.InstancedMesh(
      new THREE.BoxGeometry(0.05, 0.1, 0.36),
      new THREE.MeshBasicMaterial({ color: 0xffffff }),
      FILAS * 2 * 24,
    );
    let li = 0;
    const luzFila = [];
    for (let i = 0; i < FILAS; i++) {
      for (const s of [-1, 1]) {
        const z = Z0 - i * DZ;
        const k = i * 2 + (s > 0 ? 1 : 0);
        m4.makeTranslation(s * (LW / 2 - 0.45), 1.35, z);
        cab.setMatrixAt(k, m4);
        for (let r = 0; r < 6; r++) {
          for (let c = 0; c < 4; c++) {
            m4.makeTranslation(s * (LW / 2 - 0.9 - 0.02), 0.55 + r * 0.36, z - 1.3 + c * 0.86);
            lg.setMatrixAt(li, m4);
            luzFila[li] = i;
            lg.setColorAt(li, new THREE.Color(0x000000));
            li++;
          }
        }
      }
    }
    sc.add(cab);
    sc.add(lg);
    // porta do fundo: duas lajes que se fecham sobre uma luz fria
    const mP = new THREE.MeshStandardMaterial({ color: 0x39414c, roughness: 0.4, metalness: 0.8 });
    const zP = -L + 4;
    const pA = new THREE.Mesh(new THREE.BoxGeometry(LW / 2, LH, 0.4), mP);
    const pB = new THREE.Mesh(new THREE.BoxGeometry(LW / 2, LH, 0.4), mP);
    pA.position.set(-LW / 2, LH / 2, zP);
    pB.position.set(LW / 2, LH / 2, zP);
    sc.add(pA, pB);
    const luzFria = new THREE.Mesh(
      new THREE.PlaneGeometry(LW, LH),
      new THREE.MeshBasicMaterial({ color: 0xb4d2ff, fog: false }),
    );
    luzFria.position.set(0, LH / 2, zP - 0.5);
    sc.add(luzFria);
    const fria = new THREE.PointLight(0x8fb4ff, 26, 22, 2);
    fria.position.set(0, 2, zP + 2);
    sc.add(fria);
    sc.add(new THREE.HemisphereLight(0x6f86a0, 0x0b0c0e, 0.45));
    const lamp = new THREE.PointLight(0xffb347, 34, 17, 2);
    sc.add(lamp);
    const act = new Array(FILAS).fill(0);
    const cor = new THREE.Color();
    let ptx = 0;
    let pty = 0;
    let prAtual = pr;
    cena3d = {
      alvo: 0,
      p: 0,
      get pr() {
        return prAtual;
      },
      render(t, estatico) {
        const g = this;
        if (!estatico) g.p += (g.alvo - g.p) * 0.09;
        else g.p = g.alvo;
        const p = g.p;
        const z = -p * (L - 18);
        cam.position.set(Math.sin(p * 38) * 0.04, 1.7 + Math.sin(p * 60) * 0.02, z);
        ptx += ((LX / innerWidth) * 2 - 1 - ptx) * 0.1;
        pty += ((LY / innerHeight) * 2 - 1 - pty) * 0.1;
        cam.rotation.set(-pty * 0.05, -ptx * 0.14, 0);
        lamp.position.set(ptx * 2.2, 1.9 - pty * 1.2, z - 1.6);
        lamp.intensity = 34 * clamp(brilho * 1.15, 0.25, 1);
        lamp.color.setRGB(1, 0.7 - risco * 0.28, 0.28 - risco * 0.2);
        const fecha = clamp((p - 0.55) / 0.45);
        const gap = (1 - fecha * fecha * (3 - 2 * fecha)) * (LW / 2);
        pA.position.x = -LW / 4 - gap;
        pB.position.x = LW / 4 + gap;
        const alvoFila = p * FILAS + 3.5;
        for (let i = 0; i < FILAS; i++) act[i] += ((i < alvoFila ? 1 : 0) - act[i]) * 0.07;
        for (let k = 0; k < li; k++) {
          const a = act[luzFila[k]];
          const f = estatico ? 1 : 0.62 + 0.38 * Math.sin(t / 260 + k * 1.7);
          cor.setRGB(a * f, a * f * 0.4, 0);
          lg.setColorAt(k, cor);
        }
        lg.instanceColor.needsUpdate = true;
        rd.render(sc, cam);
      },
    };
    cv.parentNode.classList.add("am-tem3d");
    const redim = () => {
      rd.setSize(innerWidth, innerHeight, false);
      cam.aspect = innerWidth / innerHeight;
      cam.updateProjectionMatrix();
    };
    addEventListener("resize", redim);
    cena3d.baixaQualidade = () => {
      prAtual = Math.max(0.55, prAtual * 0.8);
      rd.setPixelRatio(prAtual);
      redim();
    };
    atualizaScroll();
    cena3d.p = cena3d.alvo;
    cena3d.render(performance.now(), true);
  }
  const io = new IntersectionObserver(
    (es) => {
      if (es.some((x) => x.isIntersecting)) {
        io.disconnect();
        carregaCorredor();
      }
    },
    { rootMargin: "500px 0px" },
  );
  if (!reduzido) io.observe(ato2);

  // a lâmpada fixa fica atrás do conteúdo enquanto o ato 3 está em vista (não cobre o medidor)
  const ato3Viva = $("#am-ato3");
  if (ato3Viva) {
    new IntersectionObserver((es) => {
      for (const x of es) raiz.classList.toggle("am-lampada-atras", x.isIntersecting);
    }).observe(ato3Viva);
  }

  // ---------- a interação do ato 3: três níveis e o medidor de risco ----------
  const NIV = {
    rec: ["Só mostra os dados, sem sugerir nada.", "Sugere uma opção, sem justificar.", "Sugere e explica o motivo.", "Sugere e ordena todas as opções."],
    exe: ["Nada: só um humano executa.", "Executa depois da aprovação de um humano.", "Executa e avisa depois.", "Executa sem avisar ninguém."],
    int: ["Ninguém consegue interromper.", "Só a equipe técnica, depois do fato.", "Um humano, a qualquer momento.", "Qualquer humano, com parada imediata e registro."],
  };
  const $r = (k) => $("#am-c-" + k);
  const ARC = Math.PI * 90;
  $("#am-g-marcas").innerHTML = [0, 0.2, 0.45, 0.7, 1]
    .map((v) => {
      const a = Math.PI * (1 - v);
      const x1 = 110 + 80 * Math.cos(a);
      const y1 = 110 - 80 * Math.sin(a);
      const x2 = 110 + 101 * Math.cos(a);
      const y2 = 110 - 101 * Math.sin(a);
      return `<line class="am-marca" x1="${x1.toFixed(1)}" y1="${y1.toFixed(1)}" x2="${x2.toFixed(1)}" y2="${y2.toFixed(1)}"/>`;
    })
    .join("");
  function calcula() {
    const rec = +$r("rec").value;
    const exe = +$r("exe").value;
    const int = +$r("int").value;
    const esc = +$("#am-c-esc").value;
    const aud = $("#am-c-aud").checked;
    const v = (0.1 + 0.2 * exe + 0.05 * rec) * esc * (1 - 0.22 * int) * (aud ? 0.8 : 1.15);
    return { rec, exe, int, esc, aud, risco: clamp(v) };
  }
  const nivel = (v) => (v < 0.2 ? "Baixo" : v < 0.45 ? "Moderado" : v < 0.7 ? "Alto" : "Crítico");
  function explica(c) {
    if (c.exe >= 2 && c.int <= 1) return "Você deu o poder de executar sem uma forma rápida de parar: é a combinação que preocupa, não a máquina.";
    if (c.esc >= 1.6 && !c.aud) return "Numa decisão crítica sem registro, ninguém entende o que aconteceu depois.";
    if (c.int >= 2 && c.exe <= 1) return "Recomendar com um humano no comando: os erros ficam visíveis e contestáveis.";
    if (c.aud && c.int >= 2) return "Parada e registro desenhados antes da falha: o requisito virou parte do sistema.";
    return "Ajuste os controles para ver qual combinação pesa mais.";
  }
  function atualizaRisco() {
    const c = calcula();
    risco = c.risco;
    ["rec", "exe", "int"].forEach((k) => {
      $("#am-o-" + k).textContent = NIV[k][c[k]];
      $("#am-n-" + k).textContent = c[k] + "/3";
    });
    $("#am-g-valor").setAttribute("stroke-dasharray", `${(c.risco * ARC).toFixed(1)} 400`);
    $("#am-g-agulha").style.transform = `rotate(${(-90 + 180 * c.risco).toFixed(1)}deg)`;
    $("#am-r-pct").textContent = Math.round(c.risco * 100) + "%";
    $("#am-r-nivel").textContent = nivel(c.risco);
    $("#am-r-porque").textContent = explica(c);
    // o clima reage: a luz esquenta de âmbar para laranja-avermelhado conforme o risco sobe
    const g = Math.round(176 - 86 * c.risco);
    const b = Math.round(30 * c.risco);
    S.setProperty("--luz", `rgb(255,${g},${b})`);
    S.setProperty("--luz-rgb", `255,${g},${b}`);
    if (pausado) luzNosComponentes();
  }
  const form = $("#am-autonomia");
  form.addEventListener("input", atualizaRisco);
  form.addEventListener("change", atualizaRisco);
  $("#am-registrar").addEventListener("click", () => {
    const c = calcula();
    $("#am-registro").textContent = `Registrado nesta página: risco ${Math.round(c.risco * 100)}% (${nivel(c.risco)}). Recomendar ${c.rec}/3 · Executar ${c.exe}/3 · Interromper ${c.int}/3${c.aud ? " · com registro" : " · sem registro"}.`;
  });
  $("#am-restaurar").addEventListener("click", () => {
    $r("rec").value = 1;
    $r("exe").value = 1;
    $r("int").value = 2;
    $("#am-c-esc").value = "1";
    $("#am-c-aud").checked = false;
    $("#am-registro").textContent = "";
    atualizaRisco();
  });

  // ---------- loop, pausa, visibilidade ----------
  let raf = 0;
  let tPrev = 0;
  let ema = 16.7;
  let fc = 0;
  const naTela = () => {
    const r = raiz.getBoundingClientRect();
    return r.bottom > 0 && r.top < innerHeight;
  };
  function frame(t) {
    raf = 0;
    if (pausado || document.hidden) return;
    const dt = t - (tPrev || t);
    tPrev = t;
    if (dt > 0 && dt < 200) {
      ema += (dt - ema) * 0.06;
      if (ema > 22 && cena3d && cena3d.pr > 0.56) {
        cena3d.baixaQualidade();
        ema = 16.7;
      }
    }
    if (naTela()) {
      atualizaLampada(t);
      desenhaPoeira(t);
      if ((fc++ & 1) === 0) luzNosComponentes();
      if (cena3d && visivel2()) cena3d.render(t, false);
    }
    raf = requestAnimationFrame(frame);
  }
  function liga() {
    if (!raf && !pausado && !document.hidden) {
      tPrev = 0;
      raf = requestAnimationFrame(frame);
    }
  }
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      if (raf) {
        cancelAnimationFrame(raf);
        raf = 0;
      }
    } else liga();
  });
  const bt = $("#am-pausa");
  function rotulo() {
    bt.textContent = reduzido ? "movimento pausado (modo reduzido)" : pausado ? "retomar movimento" : "pausar movimento";
    bt.setAttribute("aria-pressed", String(pausado));
    raiz.classList.toggle("am-pausado", pausado);
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
    litEls = $$(".am-lit,.am-sombra", raiz);
    dimPoeira();
    if (reduzido) lampadaEstatica();
    atualizaScroll();
    if (pausado || reduzido) luzNosComponentes();
  });
  litEls = $$(".am-lit,.am-sombra", raiz);
  dimPoeira();
  atualizaRisco();
  atualizaScroll();
  if (reduzido) {
    lampadaEstatica();
    brilho = 0.85;
    luzNosComponentes();
  } else {
    liga();
  }
});
