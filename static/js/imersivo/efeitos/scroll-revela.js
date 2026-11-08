import { registar } from "../motor.js";

// Revela as formas quando o ato entra no viewport (IntersectionObserver + CSS).
registar("scroll:revela", ({ el, parametros, reduzido }) => {
  const alvo = el.querySelector(".im-revela");
  if (!alvo) return;
  if (reduzido) {
    alvo.classList.add("im-revela--on");
    return;
  }
  const atraso = typeof parametros.atraso === "number" ? parametros.atraso : 0;
  alvo.querySelectorAll(".im-forma").forEach((f, i) => {
    f.style.transitionDelay = `${(atraso + i * 0.12).toFixed(2)}s`;
  });
  const obs = new IntersectionObserver(
    (entradas) => {
      if (entradas.some((e) => e.isIntersecting)) {
        alvo.classList.add("im-revela--on");
        obs.disconnect();
      }
    },
    { threshold: 0.25 },
  );
  obs.observe(alvo);
});
