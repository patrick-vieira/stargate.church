import { registar } from "../motor.js";

// Olho geométrico: a pupila segue o cursor (rato). Com toque não há cursor, então
// ela acompanha o scroll. Com movimento reduzido fica parada no centro.
registar("olho:segue", ({ el, parametros, reduzido, progresso }) => {
  const pupila = el.querySelector("[data-pupila]");
  if (!pupila || reduzido) return;
  const alcance = (typeof parametros.alcance === "number" ? parametros.alcance : 0.5) * 24;
  let usaRato = false;
  let alvo = [0, 0];
  let agendado = false;
  const pintar = () => {
    agendado = false;
    pupila.setAttribute("transform", `translate(${alvo[0].toFixed(1)} ${alvo[1].toFixed(1)})`);
  };
  const mover = (x, y) => {
    alvo = [x * alcance, y * alcance];
    if (!agendado) {
      agendado = true;
      requestAnimationFrame(pintar);
    }
  };
  window.addEventListener(
    "pointermove",
    (e) => {
      if (e.pointerType === "touch") return;
      usaRato = true;
      const r = el.getBoundingClientRect();
      const dx = e.clientX - (r.left + r.width / 2);
      const dy = e.clientY - (r.top + r.height / 2);
      const d = Math.hypot(dx, dy) || 1;
      const f = Math.min(1, d / 200);
      mover((dx / d) * f, (dy / d) * f);
    },
    { passive: true },
  );
  progresso((p) => {
    if (usaRato) return;
    mover(Math.sin(p * Math.PI * 2), Math.cos(p * Math.PI * 2) * 0.5);
  });
});
