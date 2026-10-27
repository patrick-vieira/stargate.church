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

async function rive() {
  const canvas = document.getElementById("lab-rive");
  const maquina = canvas.dataset.rivStateMachine;
  try {
    const { Rive } = await import("@rive-app/canvas");
    const r = new Rive({
      src: canvas.dataset.rivSrc,
      canvas,
      stateMachines: maquina,
      autoplay: !reduzido,
      onLoad: () => {
        const entrada = r.stateMachineInputs(maquina).find((i) => i.name === canvas.dataset.rivInput);
        if (entrada) ouvintes.push((v) => (entrada.value = v * 100));
      },
    });
    return true;
  } catch (e) {
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
  `Cena 3D: ${tres ? "ok" : "indisponível"}. Rive: ${riv ? "carregado (aguarda o .riv)" : "indisponível"}.`;
