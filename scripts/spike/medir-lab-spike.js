// Medição do spike STAR-19 (/lab/spike/): peso, fps, 390 px, prefers-reduced-motion e estado do Rive.
// Uso: node medir-lab-spike.js <url-base> [pasta-de-prints]
//   ex.: node medir-lab-spike.js http://127.0.0.1:8291 /tmp/prints-star19
// Requer playwright-core (ou playwright) resolúvel e um Chromium; PLAYWRIGHT_CHROMIUM=<caminho> opcional.
// O palco tem de estar numa porta livre (nunca 8170). Saída: JSON em stdout.
const fs = require("fs");
const path = require("path");
let chromium;
try { ({ chromium } = require("playwright-core")); } catch (e) { ({ chromium } = require("playwright")); }

const base = (process.argv[2] || "").replace(/\/$/, "");
const prints = process.argv[3] || "prints";
if (!base) { console.error("falta <url-base>"); process.exit(2); }
fs.mkdirSync(prints, { recursive: true });
const URL_ = base + "/lab/spike/";

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

(async () => {
  const browser = await chromium.launch({
    executablePath: process.env.PLAYWRIGHT_CHROMIUM || undefined,
    args: ["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"],
  });
  const out = { url: URL_, data: new Date().toISOString(), nota_fps: "swiftshader = GL por software; num portátil real os fps serão maiores. Repetir com GPU se possível." };

  for (const [nome, cfg] of Object.entries({
    desktop: { w: 1440, h: 900, reduzido: false },
    mobile390: { w: 390, h: 844, reduzido: false },
    reduzido: { w: 1440, h: 900, reduzido: true },
  })) {
    const { ctx, page, bytes, erros } = await sessao(browser, cfg);
    const r = {
      peso_bytes_sem_compressao: bytes.total,
      peso_por_tipo: bytes.porTipo,
      peso_por_url: bytes.porUrl,
      scrollWidth: await page.evaluate(() => document.documentElement.scrollWidth),
      innerWidth: await page.evaluate(() => innerWidth),
      estado: await page.evaluate(() => window.__labEstado || null),
      modo_texto: await page.evaluate(() => document.getElementById("lab-modo").textContent),
      erros,
    };
    r.sem_scroll_horizontal = r.scrollWidth <= r.innerWidth;
    if (!cfg.reduzido) r.fps = await fps(page);
    await page.screenshot({ path: path.join(prints, `${nome}-fim.png`) });
    await page.evaluate(() => scrollTo(0, 0)); await page.waitForTimeout(500);
    await page.screenshot({ path: path.join(prints, `${nome}-topo.png`) });
    out[nome] = r;
    await ctx.close();
  }
  await browser.close();
  console.log(JSON.stringify(out, null, 2));
})();
