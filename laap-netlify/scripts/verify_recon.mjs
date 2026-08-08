import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
await page.goto('http://localhost:5173/');
await page.waitForLoadState('networkidle');
console.log('URL:', page.url());
console.log('Title:', await page.title());
const buttons = await page.locator('button').all();
console.log('Buttons:', (await Promise.all(buttons.map(b => b.textContent()))).map(t => t?.trim()).filter(Boolean));
const links = await page.locator('a').all();
console.log('Links:', (await Promise.all(links.map(l => l.textContent()))).map(t => t?.trim()).filter(Boolean));
await page.screenshot({ path: 'scripts/recon_home.png', fullPage: true });
console.log('Screenshot saved');
await browser.close();
