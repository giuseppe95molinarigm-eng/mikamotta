const { chromium } = require('playwright');
(async () => {
  const [,, inp, out] = process.argv;
  const b = await chromium.launch();
  const p = await b.newPage();
  p.on('console', m => { if (m.type()==='error') console.log('CONSOLE', m.text()); });
  await p.goto('file://' + inp, { waitUntil: 'load' });
  await p.waitForFunction(() => window.__pagedDone === true, null, { timeout: 180000 });
  await p.evaluate(() => {
    document.querySelectorAll('.pagedjs_page').forEach(pg => {
      if (pg.querySelector('h1.cap-titolo, h1.ins-titolo, h1.nota-titolo, .front')) {
        pg.querySelectorAll('.pagedjs_margin-top .pagedjs_margin-content').forEach(m => m.style.visibility = 'hidden');
        pg.querySelectorAll('.pagedjs_margin-top-center').forEach(m => m.style.visibility = 'hidden');
      }
    });
  });
  const n = await p.evaluate(() => document.querySelectorAll('.pagedjs_page').length);
  console.log('pagine', n);
  await p.pdf({ path: out, width: '6in', height: '9in', printBackground: true, preferCSSPageSize: true });
  await b.close();
})();
