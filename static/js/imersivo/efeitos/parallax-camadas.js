import { registar, cssScroll } from "../motor.js";

// Camadas fundo/meio/frente deslocadas por translate3d conforme o progresso.
const VELOCIDADE = { fundo: 0.25, meio: 0.6, frente: 1 };

registar("parallax:camadas", ({ el, parametros, reduzido, progresso }) => {
  if (reduzido) return; // camadas ficam na posição estática do CSS
  if (cssScroll) return; // o CSS (animation-timeline: view()) anima sem JS
  const intensidade = typeof parametros.intensidade === "number" ? parametros.intensidade : 0.5;
  const camadas = [...el.querySelectorAll("[data-camada]")];
  progresso((p) => {
    camadas.forEach((c) => {
      const v = VELOCIDADE[c.dataset.camada] || 0;
      const deslocamento = (p - 0.5) * 2 * 10 * intensidade * v; // em % da altura
      c.style.transform = `translate3d(0, ${deslocamento.toFixed(2)}%, 0)`;
    });
  });
});
