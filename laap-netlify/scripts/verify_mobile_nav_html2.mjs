import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 375, height: 812 }, isMobile: true, hasTouch: true });
const page = await context.newPage();
await page.goto('http://localhost:5173/');
await page.waitForLoadState('networkidle');
await page.waitForTimeout(500);

const html = await page.evaluate(() => {
  const nav = document.querySelector('nav');
  return nav ? nav.outerHTML.slice(5000, 10000) : 'no nav';
});
console.log('Nav HTML part 2:', html);
await browser.close();
