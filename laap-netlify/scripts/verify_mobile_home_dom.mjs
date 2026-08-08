import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 375, height: 812 }, isMobile: true, hasTouch: true });
const page = await context.newPage();
await page.goto('http://localhost:5173/');
await page.waitForLoadState('networkidle');
await page.waitForTimeout(500);

const navInfo = await page.evaluate(() => {
  const nav = document.querySelector('nav, header');
  return nav ? {
    tag: nav.tagName,
    className: nav.className,
    width: nav.scrollWidth,
    viewport: window.innerWidth,
    links: Array.from(nav.querySelectorAll('a, button')).map(el => el.textContent?.trim()).filter(Boolean).slice(0, 30),
  } : 'no nav';
});
console.log('Nav info:', navInfo);

const hero = await page.evaluate(() => {
  const h = document.querySelector('section, .hero, [class*="hero" i]');
  return h ? { className: h.className, width: h.scrollWidth, text: h.innerText.slice(0, 300) } : 'no hero';
});
console.log('Hero info:', hero);

await browser.close();
