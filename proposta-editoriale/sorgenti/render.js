const { chromium } = require('playwright');
(async () => {
  const [,, inp, out, label] = process.argv;
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.goto('file://' + inp, { waitUntil: 'networkidle' });
  await p.evaluate(() => document.fonts.ready);
  await p.pdf({ path: out, format: 'A4', preferCSSPageSize: true, printBackground: true,
    displayHeaderFooter: true, headerTemplate: '<span></span>',
    footerTemplate: `<div style="width:100%;font-family:Inter,sans-serif;font-size:7.5px;color:#8a837a;padding:0 21mm;display:flex;justify-content:space-between;letter-spacing:.04em"><span>Elite Publishing · ${label}</span><span class="pageNumber"></span></div>` });
  await b.close();
})();
