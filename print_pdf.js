/**
 * Print an HTML file to PDF using headless Chrome.
 *
 * Usage: node print_pdf.js <input.html> [output.pdf]
 */
const puppeteer = require('puppeteer');
const path = require('path');

const args = process.argv.slice(2);
if (args.length < 1) {
  console.error('Usage: node print_pdf.js <input.html> [output.pdf]');
  process.exit(1);
}

const htmlPath = path.resolve(args[0]);
const pdfPath = args[1]
  ? path.resolve(args[1])
  : htmlPath.replace(/\.html$/, '.pdf');

(async () => {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();

  await page.goto(`file://${htmlPath}`, { waitUntil: 'networkidle0' });

  // Wait for KaTeX to finish rendering (skip if no math on page)
  await page.waitForFunction(() => {
    const mathElements = document.querySelectorAll('.math-display, .math-inline');
    if (mathElements.length === 0) return true;
    return document.querySelectorAll('.katex').length > 0;
  }, { timeout: 10000 });

  await page.pdf({
    path: pdfPath,
    format: 'A4',
    margin: { top: '48px', bottom: '48px', left: '48px', right: '48px' },
    printBackground: true
  });

  await browser.close();
  console.log(`PDF written to ${pdfPath}`);
})();
