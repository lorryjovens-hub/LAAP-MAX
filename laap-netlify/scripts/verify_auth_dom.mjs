import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
await page.goto('http://localhost:5173/studio');
await page.waitForLoadState('networkidle');
await page.keyboard.press('Escape');
await page.waitForTimeout(300);
await page.locator('button:has-text("登录 / 注册")').first().click();
await page.waitForTimeout(500);

const html = await page.evaluate(() => {
  // Find element containing 登录 / 注册 forms
  const all = Array.from(document.querySelectorAll('div, section, aside'));
  const el = all.find(e => e.textContent.includes('立即注册') && e.children.length > 2);
  return el ? el.outerHTML.slice(0, 4000) : 'not found';
});
console.log('Auth container:', html);
await page.screenshot({ path: 'scripts/recon_auth_dom.png', fullPage: true });
await browser.close();
