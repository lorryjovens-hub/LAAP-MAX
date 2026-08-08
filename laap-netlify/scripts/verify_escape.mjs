import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
await page.goto('http://localhost:5173/studio');
await page.waitForLoadState('networkidle');
console.log('Dialogs before:', await page.locator('[role="dialog"]').count());
await page.keyboard.press('Escape');
await page.waitForTimeout(500);
console.log('Dialogs after escape:', await page.locator('[role="dialog"]').count());
await page.screenshot({ path: 'scripts/recon_escape.png', fullPage: true });
await browser.close();
