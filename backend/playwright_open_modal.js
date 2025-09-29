const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  page.on('console', msg => {
    console.log('PAGE LOG:', msg.text());
  });

  // Adjust URL/selector as needed to open the modal for workstation 7
  await page.goto('http://127.0.0.1:5173');

  // Wait for main app to render
  await page.waitForSelector('body');

  // Try to find a workstation item with data-id="7" and click it
  const wsSelector = '[data-workstation-id="7"]';
  try {
    await page.waitForSelector(wsSelector, { timeout: 5000 });
    await page.click(wsSelector);
    console.log('Clicked workstation element');
  } catch (e) {
    console.log('Could not find workstation element selector:', e.message);
  }

  // Wait a bit for modal open and websocket activity
  await page.waitForTimeout(3000);

  await browser.close();
})();
