import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
const page = await context.newPage();
await page.goto('http://localhost:5173/studio');
await page.waitForLoadState('networkidle');

const closeBtn = page.locator('[role="dialog"] button:has-text("Close"), [role="dialog"] button[aria-label="Close"]').first();
if (await closeBtn.isVisible().catch(() => false)) {
  await closeBtn.click();
  await page.waitForTimeout(300);
}

await page.locator('button:has-text("登录 / 注册")').first().click();
await page.waitForTimeout(500);

// Click the 注册 tab
await page.locator('button:has-text("注册")').first().click();
await page.waitForTimeout(500);
await page.screenshot({ path: 'scripts/recon_register.png', fullPage: true });
const inputs = await page.locator('input').all();
console.log('Register inputs:', await Promise.all(inputs.map(async i => ({
  type: await i.getAttribute('type'),
  placeholder: await i.getAttribute('placeholder'),
  value: await i.inputValue().catch(() => ''),
}))));
const buttons = (await Promise.all((await page.locator('button').all()).map(b => b.textContent()))).map(t => t?.trim()).filter(Boolean);
console.log('Buttons:', buttons);
await browser.close();
