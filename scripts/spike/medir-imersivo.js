// Medição do motor imersivo (STAR-38) em /imersivo/<slug>/: peso inicial, fps, overflow e prefers-reduced-motion.
// Uso: node medir-imersivo.js <url-base> [pasta-de-prints] [slug=demo-provisorio]
//   ex.: node medir-imersivo.js http://127.0.0.1:8291 /tmp/prints-star38 demo-provisorio
// Mede a 1920, a 390 e em modo reduzido (1440). Falha (código 1) se o peso inicial passar de 1,5 MB,
// se houver scroll horizontal ou se algum ato terminar com erro em window.__imersivoEstado.
// Requer playwright-core (ou playwright) resolúvel e um Chromium; PLAYWRIGHT_CHROMIUM=<caminho> opcional.
// O palco tem de estar numa porta livre (nunca 8170). Saída: JSON em stdout e medicao.json na pasta de prints.
const fs = require("fs");
const path = require("path");
let chromium;
try { ({ chromium } = require("playwright-core")); } catch (e) { ({ chromium } = require("playwright")); }

const LIMITE_BYTES = 1.5 * 1024 * 1024;
const base = (process.argv[2] || "").replace(/\/$/, "");
const prints = process.argv[3] || "prints";
const slug = process.argv[4] || "demo-provisorio";
const saida = path.join(prints, "medicao.json");
if (!base) { console.error("falta <url-base>"); process.exit(2); }
fs.mkdirSync(prints, { recursive: true });
const URL_ = `${base}/imersivo/${slug}/`;

async function sessao(browser, { w, h, reduzido }) {
  const ctx = await browser.newContext({ viewport: { width: w, height: h }, reducedMotion: reduzido ? "reduce" : "no-preference" });
  const page = await ctx.newPage();
  const bytes = { total: 0, porTipo: {}, porUrl: {} };
  const erros = [];
  page.on("pageerror", (e) => erros.push(String(e.message)));
  page.on("console", (m) => { if (m.type() === "error") erros.push(m.text()); });
  page.on("response", async (r) => {
    try {
      const b = (await r.body()).length; // sem compressão (o runserver não comprime)
      const u = new URL(r.url()).pathname;
      bytes.total += b;
      bytes.porUrl[u] = b;
      const t = r.request().resourceType();
      bytes.porTipo[t] = (bytes.porTipo[t] || 0) + b;
    } catch (e) { /* redirecionamentos sem corpo */ }
  });
  await page.goto(URL_, { waitUntil: "networkidle" });
  await page.waitForTimeout(1500);
  return { ctx, page, bytes, erros };
}

async function fps(page) {
  // Rola do topo ao fim em ~4 s e conta frames de rAF.
  return page.evaluate(() => new Promise((ok) => {
    const total = document.documentElement.scrollHeight - innerHeight;
    const dur = 4000; const t0 = performance.now(); let n = 0; const dts = []; let ult = t0;
    function f(t) {
      n++; dts.push(t - ult); ult = t;
      scrollTo(0, total * Math.min(1, (t - t0) / dur));
      if (t - t0 < dur) requestAnimationFrame(f); else {
        dts.sort((a, b) => a - b);
        ok({ frames: n, fps_medio: +(n / ((t - t0) / 1000)).toFixed(1), p95_ms: +dts[Math.floor(dts.length * 0.95)].toFixed(1), pior_ms: +dts[dts.length - 1].toFixed(1) });
      }
    }
    requestAnimationFrame(f);
  }));
}

const lerEstado = (page) => page.evaluate(() => {
  const e = window.__imersivoEstado;
  return e ? { atos: e.atos, reduzido: e.reduzido } : null;
});
async function rolarFim(page) { await page.evaluate(() => scrollTo(0, document.documentElement.scrollHeight)); await page.waitForTimeout(1500); }
async function rolarTopo(page) { await page.evaluate(() => scrollTo(0, 0)); await page.waitForTimeout(800); }

(async () => {
  const browser = await chromium.launch({
    executablePath: process.env.PLAYWRIGHT_CHROMIUM || undefined,
    args: ["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"],
  });
  const falhas = [];
  const out = { url: URL_, data: new Date().toISOString(), limite_peso_inicial_bytes: LIMITE_BYTES, nota_fps: "swiftshader = GL por software; num portátil real os fps serão maiores. Repetir com GPU se possível." };

  for (const [nome, cfg] of Object.entries({
    desktop1920: { w: 1920, h: 1080, reduzido: false },
    mobile390: { w: 390, h: 844, reduzido: false },
    reduzido: { w: 1440, h: 900, reduzido: true },
  })) {
    const { ctx, page, bytes, erros } = await sessao(browser, cfg);
    await rolarTopo(page);
    const r = {
      viewport: `${cfg.w}x${cfg.h}`,
      peso_inicial_bytes_sem_compressao: bytes.total, // medido ANTES de rolar: three/rive/wasm não podem estar aqui
      peso_por_tipo: { ...bytes.porTipo },
      peso_por_url: { ...bytes.porUrl },
      scrollWidth: await page.evaluate(() => document.documentElement.scrollWidth),
      innerWidth: await page.evaluate(() => innerWidth),
      estado_inicial: await lerEstado(page),
      erros_iniciais: [...erros],
    };
    r.sem_scroll_horizontal = r.scrollWidth <= r.innerWidth;
    r.pesados_no_carregamento = Object.keys(bytes.porUrl).filter((u) => /three|rive|\.wasm/.test(u));
    if (!cfg.reduzido) r.fps = await fps(page);
    await rolarFim(page);
    r.estado_final = await lerEstado(page);
    r.peso_total_apos_scroll_bytes = bytes.total;
    r.reduzido_ativo = r.estado_final ? r.estado_final.reduzido : null;
    r.erros = erros;
    if (r.peso_inicial_bytes_sem_compressao > LIMITE_BYTES) falhas.push(`${nome}: peso inicial ${r.peso_inicial_bytes_sem_compressao} > ${LIMITE_BYTES}`);
    if (!r.sem_scroll_horizontal) falhas.push(`${nome}: scrollWidth ${r.scrollWidth} > innerWidth ${r.innerWidth}`);
    if (!r.estado_final) falhas.push(`${nome}: window.__imersivoEstado ausente`);
    else {
      r.estado_final.atos.filter((a) => a.erro).forEach((a) => falhas.push(`${nome}: ato ${a.efeito} com erro: ${a.erro}`));
      if (cfg.reduzido && !r.estado_final.reduzido) falhas.push(`${nome}: reduzido não detetado`);
    }
    if (cfg.reduzido) {
      const pesados = Object.keys(bytes.porUrl).filter((u) => /three|rive|\.wasm/.test(u));
      if (pesados.length) falhas.push(`${nome}: libs pesadas carregadas em movimento reduzido: ${pesados.join(", ")}`);
    } else if (r.pesados_no_carregamento.length) {
      falhas.push(`${nome}: libs pesadas no 1.º carregamento: ${r.pesados_no_carregamento.join(", ")}`);
    }
    await page.screenshot({ path: path.join(prints, `${nome}-fim.png`) });
    await rolarTopo(page);
    await page.screenshot({ path: path.join(prints, `${nome}-topo.png`) });
    out[nome] = r;
    await ctx.close();
  }
  await browser.close();
  out.falhas = falhas;
  fs.writeFileSync(saida, JSON.stringify(out, null, 2));
  console.log(JSON.stringify(out, null, 2));
  if (falhas.length) { console.error("FALHAS:\n" + falhas.join("\n")); process.exit(1); }
})();
