import { registar } from "../motor.js";

// Linha do tempo por décadas: trilho horizontal com parallax por estação.
// Sem animação com movimento reduzido (a lista fica vertical por CSS).
registar("linha-tempo:decadas", ({ el, parametros, reduzido, progresso }) => {
  const trilho = el.querySelector(".im-trilho");
  if (!trilho) return;
  const estacoes = [...trilho.querySelectorAll(".im-estacao")];
  if (reduzido) {
    estacoes.forEach((e) => e.classList.add("on"));
    return;
  }
  const k = typeof parametros.intensidade === "number" ? parametros.intensidade : 0.5;
  trilho.classList.add("im-trilho--ativo");
  let empurra = 0;
  let agendado = false;
  const aplicar = () => {
    agendado = false;
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
  trilho.addEventListener("scroll", pedir, { passive: true });
  window.addEventListener("resize", pedir);
  progresso((p) => {
    empurra = (p - 0.5) * 60 * k;
    pedir();
  });
  const obs = new IntersectionObserver(
    (entradas) => {
      for (const en of entradas) en.target.classList.toggle("on", en.isIntersecting);
    },
    { root: trilho, threshold: 0.6 },
  );
  estacoes.forEach((e) => obs.observe(e));
  pedir();
});
