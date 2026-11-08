// Motor imersivo (STAR-38). Cada [data-ato] declara um efeito; o motor carrega
// o módulo do efeito sob demanda, quando o ato se aproxima do viewport.
// Com prefers-reduced-motion nada anima e nenhuma lib pesada é carregada.
const reduzidoGlobal = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

// Com animation-timeline: view() o CSS anima parallax e revela; o JS fica de fora.
export const cssScroll =
  typeof CSS !== "undefined" && CSS.supports("animation-timeline: view()");

export const efeitos = new Map();
export function registar(nome, fn) {
  efeitos.set(nome, fn);
}

const estado = { atos: [], reduzido: reduzidoGlobal };
window.__imersivoEstado = estado;

// Progresso do ato: 0 quando a base entra no viewport, 1 quando o topo sai.
function calcularProgresso(el) {
  const r = el.getBoundingClientRect();
  const total = window.innerHeight + r.height;
  return total > 0 ? Math.min(1, Math.max(0, (window.innerHeight - r.top) / total)) : 0;
}

const ouvintes = new Set();
let agendado = false;
function atualizar() {
  agendado = false;
  ouvintes.forEach((f) => f());
}
function pedirAtualizacao() {
  if (!agendado) {
    agendado = true;
    requestAnimationFrame(atualizar);
  }
}
window.addEventListener("scroll", pedirAtualizacao, { passive: true });
window.addEventListener("resize", pedirAtualizacao);

function lerParametros(el) {
  try {
    const p = JSON.parse(el.dataset.parametros || "{}");
    return p && typeof p === "object" ? p : {};
  } catch (e) {
    return {};
  }
}

// GSAP e Lenis são opcionais: só se o servidor indicou que existem (sem 404 na consola).
async function libsOpcionais(palco) {
  const libs = {};
  if (reduzidoGlobal) return libs;
  let urls = {};
  try {
    urls = JSON.parse(palco.dataset.libs || "{}");
  } catch (e) {
    return libs;
  }
  for (const [nome, url] of Object.entries(urls)) {
    if (!url) continue;
    try {
      const m = await import(/* @vite-ignore */ url);
      libs[nome] = m.default || m;
    } catch (e) {
      // opcional: degrada para o fallback nativo
    }
  }
  return libs;
}

async function iniciarAto(el, registo, libs) {
  const efeito = el.dataset.efeito;
  try {
    if (!efeitos.has(efeito)) await import("./efeitos/" + efeito.replace(":", "-") + ".js");
    const fn = efeitos.get(efeito);
    if (!fn) throw new Error("efeito não registrado: " + efeito);
    const ctx = {
      el,
      parametros: lerParametros(el),
      reduzido: reduzidoGlobal,
      libs,
      progresso(cb) {
        const f = () => cb(calcularProgresso(el));
        ouvintes.add(f);
        f();
      },
    };
    await fn(ctx);
    registo.ok = true;
  } catch (e) {
    registo.erro = String(e && e.message ? e.message : e);
    console.warn("Imersivo:", efeito, registo.erro);
  }
}

async function principal() {
  const palco = document.querySelector("[data-imersivo]");
  const atos = [...document.querySelectorAll("[data-ato]")];
  const libs = palco ? await libsOpcionais(palco) : {};
  const registos = atos.map((el) => ({ efeito: el.dataset.efeito, ok: false, erro: "" }));
  estado.atos = registos;
  const pendentes = atos.map((el, i) => new Promise((fim) => {
    if (reduzidoGlobal && el.dataset.reduzido === "omitir") {
      registos[i].ok = true;
      fim();
      return;
    }
    const obs = new IntersectionObserver(
      (entradas) => {
        if (!entradas.some((e) => e.isIntersecting)) return;
        obs.disconnect();
        iniciarAto(el, registos[i], libs).then(fim);
      },
      { rootMargin: "100% 0px" },
    );
    obs.observe(el);
  }));
  estado.pronto = Promise.all(pendentes);
}

principal();
