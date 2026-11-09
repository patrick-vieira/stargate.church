import { registar } from "../motor.js";

// Os traços do diagrama aparecem conforme o progresso; reduzido: completo, sem transição.
registar("diagrama:constroi", ({ el, parametros, reduzido, progresso }) => {
  const passos = [...el.querySelectorAll(".im-passo")];
  passos.forEach((p) => p.style.setProperty("--len", Math.ceil(p.getTotalLength())));
  if (reduzido) {
    passos.forEach((p) => p.classList.add("on"));
    return;
  }
  const atraso = typeof parametros.atraso === "number" ? parametros.atraso : 0;
  passos.forEach((p, i) => {
    p.style.transitionDelay = `${(atraso + i * 0.05).toFixed(2)}s`;
  });
  // O ato ocupa o viewport inteiro de 0 a 1; o diagrama completa aos 60%.
  progresso((v) => passos.forEach((p, i) => p.classList.toggle("on", v >= (0.15 + (0.45 * i) / passos.length))));
});
