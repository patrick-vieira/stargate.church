import { registar } from "../motor.js";

// Linha do tempo por décadas: trilho horizontal com parallax por estação.
// Sem animação com movimento reduzido (a lista fica vertical por CSS).
registar("linha-tempo:decadas", ({ el, parametros, reduzido, progresso }) => {
  const trilho = el.querySelector(".im-trilho");
  if (!trilho) return;
  const estacoes = [...trilho.querySelectorAll(".im-estacao")];
  const palco = el.closest(".im-palco");
  // Luz por década: sépia (1920) → âmbar → verde → magenta → azul (2000+, com balões).
  const luzDe = (d) => (d < 1950 ? 0 : d < 1980 ? 1 : d < 1990 ? 2 : d < 2000 ? 3 : 4);
  const acender = (e) => {
    if (palco && e) palco.dataset.luz = String(luzDe(Number(e.dataset.decada)));
  };
  if (palco && estacoes[0]) acender(estacoes[0]);
  if (reduzido) {
    estacoes.forEach((e) => e.classList.add("on"));
    return;
  }
  let pausado = false;
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "im-pausa";
  btn.setAttribute("aria-pressed", "false");
  btn.textContent = "Pausar movimento";
  btn.addEventListener("click", () => {
    pausado = !pausado;
    btn.setAttribute("aria-pressed", String(pausado));
    btn.textContent = pausado ? "Retomar movimento" : "Pausar movimento";
    if (palco) palco.classList.toggle("im-pausado", pausado);
    if (!pausado) pedir();
  });
  el.parentNode.insertBefore(btn, el);
  const k = typeof parametros.intensidade === "number" ? parametros.intensidade : 0.5;
  trilho.classList.add("im-trilho--ativo");
  let empurra = 0;
  let agendado = false;
  const aplicar = () => {
    agendado = false;
    if (pausado) return;
    const tr = trilho.getBoundingClientRect();
    const centro = tr.left + tr.width / 2;
    for (const e of estacoes) {
      const r = e.getBoundingClientRect();
      const d = (r.left + r.width / 2 - centro) * k * 0.25 + empurra;
      e.style.setProperty("--d", d.toFixed(1) + "px");
    }
  };
  const pedir = () => {
    if (!agendado) {
      agendado = true;
      requestAnimationFrame(aplicar);
    }
  };
  // A luz segue a fracção de scroll do trilho mapeada para o índice da estação
  // (0 → primeira, fim → última). A qualquer largura (1920 com várias estações
  // visíveis, 390 com uma) percorre 0→1→2→3→4 sem saltar a luz 3.
  const luzPorScroll = () => {
    const max = trilho.scrollWidth - trilho.clientWidth;
    const f = max > 0 ? Math.min(1, Math.max(0, trilho.scrollLeft / max)) : 0;
    acender(estacoes[Math.round(f * (estacoes.length - 1))]);
  };
  trilho.addEventListener("scroll", luzPorScroll, { passive: true });
  trilho.addEventListener("scroll", pedir, { passive: true });
  window.addEventListener("resize", luzPorScroll);
  window.addEventListener("resize", pedir);
  progresso((p) => {
    empurra = (p - 0.5) * 60 * k;
    pedir();
  });
  const obs = new IntersectionObserver(
    (entradas) => {
      for (const en of entradas) {
        en.target.classList.toggle("on", en.isIntersecting);
      }
    },
    { root: trilho, threshold: 0.6 },
  );
  estacoes.forEach((e) => obs.observe(e));
  luzPorScroll();
  pedir();
});
