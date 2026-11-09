import { registar } from "../motor.js";

// Corredor 3D feito só de aros geométricos (arte original); a câmera avança com o scroll.
// A lib three só é baixada quando o ato entra em vista; com movimento reduzido nem isso.
registar("three:corredor", async ({ el, parametros, reduzido, progresso }) => {
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
  const aros = typeof parametros.profundidade === "number" ? Math.round(parametros.profundidade) : 16;
  const passo = 1.5;
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  const camera = new THREE.PerspectiveCamera(60, canvas.width / canvas.height, 0.1, aros * passo + 5);
  const cena = new THREE.Scene();
  cena.background = new THREE.Color(0x1f1914);
  cena.fog = new THREE.Fog(0x1f1914, 2, aros * passo);
  const moldura = new THREE.EdgesGeometry(new THREE.BoxGeometry(2, 2, 0.05));
  for (let i = 0; i < aros; i++) {
    const cor = i === aros - 1 ? 0xeb5a3c : 0xf3e6d3;
    const aro = new THREE.LineSegments(moldura, new THREE.LineBasicMaterial({ color: cor }));
    aro.position.z = -i * passo;
    cena.add(aro);
  }
  const luz = new THREE.Mesh(
    new THREE.SphereGeometry(0.25, 16, 12),
    new THREE.MeshBasicMaterial({ color: 0xeb5a3c }),
  );
  luz.position.z = -(aros - 1) * passo - 1;
  cena.add(luz);
  progresso((p) => {
    camera.position.z = 2 - p * (aros - 1) * passo;
    renderer.render(cena, camera);
  });
  }
});
