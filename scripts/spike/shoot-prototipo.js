const { chromium } = require('/home/patrck/.npm/_npx/e41f203b7505f1fb/node_modules/playwright-core');
(async () => {
  const b = await chromium.launch({ executablePath: '/home/patrck/.cache/ms-playwright/chromium-1161/chrome-linux/chrome', args:['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist'] });
  for (const [w,h] of [[1920,1080],[390,844]]) {
    const p = await b.newPage({viewport:{width:w,height:h}});
    p.on('pageerror', e => console.log('ERR', w, e.message));
    for (const beat of [0,2,3,4,6]) {
      await p.goto('file://' + __dirname + '/index.html?beat=' + beat); await p.waitForTimeout(1800);
      await p.screenshot({path:`prints/beat${beat}-${w}.png`});
    }
    const sw = await p.evaluate(()=>document.documentElement.scrollWidth); console.log(w, 'scrollWidth', sw);
    await p.goto('file://' + __dirname + '/index.html?reduzido=1&beat=3'); await p.waitForTimeout(800);
    await p.screenshot({path:`prints/reduzido-beat3-${w}.png`});
  }
  await b.close();
})();
