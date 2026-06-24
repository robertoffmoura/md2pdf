const puppeteer = require('puppeteer');
const path = require('path');

(async () => {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();

  const htmlPath = path.resolve(__dirname, 'pipeline_overview.html');
  await page.goto(`file://${htmlPath}`, { waitUntil: 'networkidle0' });

  // Wait for KaTeX to finish rendering
  await page.waitForFunction(() => {
    const mathElements = document.querySelectorAll('.math-display, .math-inline');
    return mathElements.length > 0 &&
      document.querySelectorAll('.katex').length > 0;
  }, { timeout: 10000 });

  await page.pdf({
    path: 'pipeline_overview.pdf',
    format: 'A4',
    margin: { top: '48px', bottom: '48px', left: '48px', right: '48px' },
    printBackground: true
  });

  await browser.close();
  console.log('PDF written to pipeline_overview.pdf');
})();
