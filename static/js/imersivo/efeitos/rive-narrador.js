import { registar } from "../motor.js";

// Narrador Rive (STAR-38): runtime 2.35.0 vendorizado, ViewModel Narrador
// (progresso 0-100, era 0-6, humor 0-2, cor ARGB). Sem rede externa.
const COR_POR_ERA = ["E6C48F", "FFB000", "3DDC7A", "FF5FE0", "7DB8F0", "F4F6F8", "EB5A3C"];

function carregarScript(src) {
  if (window.rive) return Promise.resolve();
  return new Promise((ok, erro) => {
    const s = document.createElement("script");
    s.src = src;
    s.onload = ok;
    s.onerror = () => erro(new Error("rive js"));
    document.head.appendChild(s);
  });
}

// Peso (STAR-38): o runtime (js + wasm) fica fora da carga inicial. Só carrega
// depois de `load` E da primeira interação, em ocioso. Até lá fica o SVG estático.
function aposCargaEInteracao() {
  const carga = new Promise((ok) => {
    if (document.readyState === "complete") ok();
    else window.addEventListener("load", ok, { once: true });
  });
  const interacao = new Promise((ok) => {
    const evs = ["scroll", "pointerdown", "keydown"];
    const feito = () => {
      evs.forEach((e) => window.removeEventListener(e, feito));
      ok();
    };
    evs.forEach((e) => window.addEventListener(e, feito, { once: true, passive: true }));
  });
  return Promise.all([carga, interacao]).then(
    () =>
      new Promise((ok) => {
        if ("requestIdleCallback" in window) window.requestIdleCallback(() => ok());
        else setTimeout(ok, 200);
      })
  );
}

registar("rive:narrador", async ({ el, parametros, reduzido, progressoPagina }) => {
  const era = Math.min(6, Math.max(0, Math.round(Number(parametros.era)) || 0));
  el.dataset.era = String(era);
  if (reduzido) return; // estático: o glifo SVG com a pele da era, sem runtime nem wasm
  const canvas = el.querySelector("canvas[data-rive]");
  if (!canvas) throw new Error("canvas ausente");
  await aposCargaEInteracao();
  await carregarScript(canvas.dataset.rivJs);
  window.rive.RuntimeLoader.setWasmUrl(canvas.dataset.rivWasm);
  await new Promise((ok, erro) => {
    const r = new window.rive.Rive({
      src: canvas.dataset.rivSrc,
      canvas,
      autoplay: true,
      autoBind: true,
      stateMachines: "State Machine 1",
      onLoad: () => {
        try {
          r.resizeDrawingSurfaceToCanvas();
          const vm = r.viewModelInstance;
          vm.number("era").value = era;
          vm.number("humor").value = 0;
          vm.color("cor").value = parseInt("FF" + COR_POR_ERA[era], 16);
          const prog = vm.number("progresso");
          progressoPagina((p) => (prog.value = p * 100));
          el.classList.add("nr-vivo");
          ok();
        } catch (e) {
          erro(e);
        }
      },
      onLoadError: (e) => erro(new Error(String(e && e.data ? e.data : e))),
    });
  });
});
