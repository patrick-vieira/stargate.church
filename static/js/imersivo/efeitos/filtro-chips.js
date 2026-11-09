import { registar } from "../motor.js";

// Filtro por pergunta: cada chip atenua (sem esconder) as estações do trilho
// cujo slug não casa. Clicar no chip activo limpa o filtro. Igual com movimento
// reduzido: só muda uma classe, sem animação.
registar("filtro:chips", ({ el }) => {
  const chips = [...el.querySelectorAll(".im-chip")];
  const contagem = el.querySelector("[data-contagem]");
  const estacoes = [...document.querySelectorAll(".im-estacao")];
  const aplicar = (chip) => {
    const slugs = chip ? new Set((chip.dataset.slugs || "").split(/\s+/).filter(Boolean)) : null;
    let n = 0;
    for (const e of estacoes) {
      const fora = slugs !== null && !slugs.has(e.dataset.slug || "");
      e.classList.toggle("im-estacao--fora", fora);
      if (!fora) n += 1;
    }
    for (const c of chips) c.setAttribute("aria-pressed", String(c === chip));
    if (contagem) {
      contagem.textContent = n === 1 ? "1 estação" : n + " estações";
    }
  };
  const trilho = document.querySelector(".im-trilho");
  const rolarAteA1a = () => {
    const primeira = estacoes.find((e) => !e.classList.contains("im-estacao--fora"));
    if (!trilho || !primeira) return;
    const reduz = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const alvo =
      trilho.scrollLeft + primeira.getBoundingClientRect().left - trilho.getBoundingClientRect().left;
    trilho.scrollTo({ left: Math.max(0, alvo), behavior: reduz ? "auto" : "smooth" });
  };
  for (const c of chips) {
    c.addEventListener("click", () => {
      const limpar = c.getAttribute("aria-pressed") === "true";
      aplicar(limpar ? null : c);
      if (!limpar) rolarAteA1a();
    });
  }
  aplicar(null);
});
