import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
await page.goto('http://localhost:5173/studio');
await page.waitForLoadState('networkidle');
await page.keyboard.press('Escape');
await page.waitForTimeout(300);
await page.locator('button:has-text("登录 / 注册")').first().click();
await page.waitForTimeout(300);

// Click register tab and inspect its DOM
const regTab = page.locator('button:has-text("注册")').first();
console.log('register tab visible:', await regTab.isVisible());
await regTab.click({ force: true });
await page.waitForTimeout(500);

// Get the dialog HTML
const dialogHtml = await page.evaluate(() => {
  const dialog = document.querySelector('[role="dialog"]');
  return dialog ? dialog.innerHTML.slice(0, 3000) : 'no dialog';
});
console.log('Dialog HTML snippet:', dialogHtml);
await page.screenshot({ path: 'scripts/recon_register_state.png', fullPage: true });
await browser.close();
