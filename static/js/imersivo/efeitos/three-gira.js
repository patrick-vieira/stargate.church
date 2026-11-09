import { registar } from "../motor.js";

// Cena 3D (three 0.160.0 via importmap). O motor só chama isto quando o ato está perto;
// em movimento reduzido a lib nem é baixada: o canvas fica vazio e o texto basta.
registar("three:gira", async ({ el, parametros, reduzido, progresso }) => {
  const canvas = el.querySelector("canvas[data-three]");
  const cont = canvas && canvas.closest("[data-carrega]");
  const carrega = (fim) => window.Carregando && cont && window.Carregando[fim](cont);
  if (reduzido) return carrega("pronto"); // sem three: o esqueleto sai e o texto basta
  if (!canvas) throw new Error("canvas ausente");
  try {
    await montar();
  } catch (e) {
    carrega("erro");
    throw e;
  }
  carrega("pronto");

  async function montar() {
  const THREE = await import("three");
  const voltas = typeof parametros.voltas === "number" ? parametros.voltas : 2;
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  const camera = new THREE.PerspectiveCamera(50, canvas.width / canvas.height, 0.1, 10);
  camera.position.z = 3;
  const cena = new THREE.Scene();
  const malha = new THREE.Mesh(new THREE.TorusKnotGeometry(0.8, 0.25, 96, 16), new THREE.MeshNormalMaterial());
  cena.add(malha);
  progresso((p) => {
    malha.rotation.y = p * Math.PI * 2 * voltas;
    renderer.render(cena, camera);
  });
  }
});
