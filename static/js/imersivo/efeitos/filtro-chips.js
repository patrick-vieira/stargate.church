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
  for (const c of chips) {
    c.addEventListener("click", () => {
      aplicar(c.getAttribute("aria-pressed") === "true" ? null : c);
    });
  }
  aplicar(null);
});
