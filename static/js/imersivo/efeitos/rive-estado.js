import { registar } from "../motor.js";

// Rive 2.35.0 vendorizado (UMD -> window.rive); lógica herdada de lab-spike.js (STAR-19).
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

registar("rive:estado", async ({ el, parametros, reduzido, progresso }) => {
  if (reduzido) return; // sem runtime nem wasm: o texto basta
  const canvas = el.querySelector("canvas[data-rive]");
  if (!canvas) throw new Error("canvas ausente");
  const nomeProp = parametros.propriedade || "progressoLeitura";
  await carregarScript(canvas.dataset.rivJs);
  window.rive.RuntimeLoader.setWasmUrl(canvas.dataset.rivWasm);
  await new Promise((ok, erro) => {
    const r = new window.rive.Rive({
      src: canvas.dataset.rivSrc,
      canvas,
      autoplay: true,
      autoBind: true,
      onLoad: () => {
        try {
          r.resizeDrawingSurfaceToCanvas();
          const prop = r.viewModelInstance.number(nomeProp);
          if (!prop) throw new Error("propriedade ausente: " + nomeProp);
          progresso((p) => (prop.value = p * 100));
          ok();
        } catch (e) {
          erro(e);
        }
      },
      onLoadError: (e) => erro(new Error(String(e && e.data ? e.data : e))),
    });
  });
});
