// Spike STAR-19: scroll -> progresso 0..1 -> three, Rive e diagrama.
// Com prefers-reduced-motion: sem animação contínua; só estados estáticos.
const reduzido = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const modo = document.getElementById("lab-modo");
const palco = document.querySelector("[data-lab-palco]");
let progresso = 0;
const ouvintes = [];

function calcular() {
  const r = palco.getBoundingClientRect();
  const total = r.height - window.innerHeight;
  progresso = total > 0 ? Math.min(1, Math.max(0, -r.top / total)) : 0;
  ouvintes.forEach((f) => f(progresso));
}

function diagrama() {
  const passos = document.querySelectorAll(".lab-passo");
  passos.forEach((p) => p.style.setProperty("--len", Math.ceil(p.getTotalLength())));
  ouvintes.push((v) => passos.forEach((p, i) => p.classList.toggle("on", reduzido || v >= i / passos.length)));
}

async function cena() {
  const canvas = document.getElementById("lab-three");
  try {
    const THREE = await import("three");
    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    const camera = new THREE.PerspectiveCamera(50, canvas.width / canvas.height, 0.1, 10);
    camera.position.z = 3;
    const palcoCena = new THREE.Scene();
    const malha = new THREE.Mesh(new THREE.TorusKnotGeometry(0.8, 0.25, 96, 16), new THREE.MeshNormalMaterial());
    palcoCena.add(malha);
    const desenhar = (v) => {
      malha.rotation.y = reduzido ? 0.6 : v * Math.PI * 4;
      renderer.render(palcoCena, camera);
    };
    ouvintes.push(desenhar);
    desenhar(progresso);
    return true;
  } catch (e) {
    return false;
  }
}

// Rive 2.35.0 vendorizado (UMD -> window.rive); o .wasm vem do mesmo diretório.
function carregarRive(js) {
  return new Promise((ok, erro) => {
    const s = document.createElement("script");
    s.src = js;
    s.onload = ok;
    s.onerror = () => erro(new Error("rive js"));
    document.head.appendChild(s);
  });
}

let erroRive = "";
async function rive() {
  const canvas = document.getElementById("lab-rive");
  try {
    await carregarRive(canvas.dataset.rivJs);
    window.rive.RuntimeLoader.setWasmUrl(canvas.dataset.rivWasm);
    await new Promise((ok, erro) => {
      const r = new window.rive.Rive({
        src: canvas.dataset.rivSrc,
        canvas,
        autoplay: !reduzido,
        autoBind: true, // instância por defeito do ViewModel «Reading»
        onLoad: () => {
          try {
            r.resizeDrawingSurfaceToCanvas();
            const prop = r.viewModelInstance.number(canvas.dataset.rivProp);
            if (!prop) throw new Error("propriedade ausente: " + canvas.dataset.rivProp);
            ouvintes.push((v) => (prop.value = v * 100));
            // Leitura do estado atual do ViewModel (para a medição).
            window.__labRive = { propriedade: canvas.dataset.rivProp, valor: () => prop.value };
            ok();
          } catch (e) {
            erro(e);
          }
        },
        onLoadError: (e) => erro(new Error(String(e && e.data ? e.data : e))),
      });
    });
    return true;
  } catch (e) {
    erroRive = e.message;
    console.error("Rive:", e);
    return false;
  }
}

diagrama();
window.addEventListener("scroll", calcular, { passive: true });
window.addEventListener("resize", calcular);
const [tres, riv] = await Promise.all([cena(), rive()]);
calcular();
modo.textContent =
  (reduzido ? "Movimento reduzido ativo. " : "Movimento completo. ") +
  `Cena 3D: ${tres ? "ok" : "indisponível"}. Rive: ${riv ? "ok (ViewModel ligado)" : "indisponível " + erroRive}.`;
window.__labEstado = { tres, riv, erroRive, reduzido };
