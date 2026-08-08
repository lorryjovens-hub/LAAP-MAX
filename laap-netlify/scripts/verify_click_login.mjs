import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
await page.goto('http://localhost:5173/studio');
await page.waitForLoadState('networkidle');
await page.keyboard.press('Escape');
await page.waitForTimeout(300);
const btn = page.locator('button:has-text("登录 / 注册")').first();
await btn.click();
await page.waitForTimeout(1000);
console.log('Dialogs:', await page.locator('[role="dialog"]').count());
const buttons = (await Promise.all((await page.locator('button').all()).map(b => b.textContent()))).map(t => t?.trim()).filter(Boolean);
console.log('Buttons:', buttons);
const inputs = await page.locator('input').all();
console.log('Inputs:', await Promise.all(inputs.map(async i => ({
  type: await i.getAttribute('type'),
  placeholder: await i.getAttribute('placeholder'),
}))));
await page.screenshot({ path: 'scripts/recon_click_login.png', fullPage: true });
await browser.close();
