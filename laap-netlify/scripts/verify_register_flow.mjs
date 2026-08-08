import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
const page = await context.newPage();

page.on('console', msg => console.log('CONSOLE:', msg.text()));
page.on('pageerror', err => console.log('PAGEERROR:', err.message));

await page.goto('http://localhost:5173/studio');
await page.waitForLoadState('networkidle');
await page.keyboard.press('Escape');
await page.waitForTimeout(300);

await page.locator('button:has-text("登录 / 注册")').first().click();
await page.waitForTimeout(300);
await page.locator('button:has-text("注册")').first().click({ force: true });
await page.waitForTimeout(300);

// Get all inputs and pick the last email/password
const inputs = await page.locator('input').all();
const inputTypes = await Promise.all(inputs.map(i => i.getAttribute('type')));
const textInputs = inputs.filter((_, idx) => ['text','email','password'].includes(inputTypes[idx] || 'text'));
console.log('Auth input count:', textInputs.length);
// Fill last two inputs: email then password
const email = `test${Date.now()}@example.com`;
const password = 'password123';
await textInputs[textInputs.length - 2]?.fill(email);
await textInputs[textInputs.length - 1]?.fill(password);

await page.screenshot({ path: 'scripts/recon_register_filled.png', fullPage: true });

// Click 立即注册
await page.locator('button:has-text("立即注册")').first().click();
await page.waitForTimeout(1000);

console.log('Dialogs after register:', await page.locator('[role="dialog"]').count());
const displayName = await page.evaluate(() => {
  const el = document.querySelector('[class*="text-sm text-white"]');
  return el?.textContent?.trim() || '';
});
console.log('Display name after register:', displayName);
await page.screenshot({ path: 'scripts/recon_register_done.png', fullPage: true });
await browser.close();
