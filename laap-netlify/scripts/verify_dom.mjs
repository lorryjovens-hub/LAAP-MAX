import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
await page.goto('http://localhost:5173/studio');
await page.waitForLoadState('networkidle');
await page.keyboard.press('Escape');
await page.waitForTimeout(300);
// get html of login/register button and its surrounding
const html = await page.evaluate(() => {
  const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('登录 / 注册'));
  if (!btn) return 'not found';
  return btn.outerHTML + '\n---parent---\n' + (btn.parentElement?.outerHTML || '');
});
console.log('Login button HTML:', html);
await page.screenshot({ path: 'scripts/recon_dom.png', fullPage: true });
await browser.close();
