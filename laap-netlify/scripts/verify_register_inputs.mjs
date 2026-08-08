import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
await page.goto('http://localhost:5173/studio');
await page.waitForLoadState('networkidle');
await page.keyboard.press('Escape');
await page.waitForTimeout(300);
await page.locator('button:has-text("登录 / 注册")').first().click();
await page.waitForTimeout(300);
// Click register tab using exact text to avoid overlay issue? use force click
const regTab = page.locator('button:has-text("注册")').first();
await regTab.click({ force: true });
await page.waitForTimeout(300);
const inputs = await page.locator('input').all();
console.log('Register inputs:', await Promise.all(inputs.map(async (i, idx) => ({
  idx,
  type: await i.getAttribute('type'),
  placeholder: await i.getAttribute('placeholder'),
  label: await i.evaluate(el => {
    const id = el.id;
    const aria = el.getAttribute('aria-labelledby') || el.getAttribute('aria-label');
    const label = id ? document.querySelector(`label[for="${id}"]`)?.textContent?.trim() : '';
    return label || aria || '';
  }),
}))));
const buttons = (await Promise.all((await page.locator('button').all()).map(b => b.textContent()))).map(t => t?.trim()).filter(Boolean);
console.log('Buttons:', buttons);
await page.screenshot({ path: 'scripts/recon_register_inputs.png', fullPage: true });
await browser.close();
