import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
const page = await context.newPage();
await page.goto('http://localhost:5173/studio');
await page.waitForLoadState('networkidle');
console.log('URL:', page.url());
console.log('Title:', await page.title());
await page.screenshot({ path: 'scripts/recon_studio.png', fullPage: true });
const buttons = (await Promise.all((await page.locator('button').all()).map(b => b.textContent()))).map(t => t?.trim()).filter(Boolean);
console.log('Buttons:', buttons);
const inputs = await page.locator('input').all();
console.log('Inputs:', await Promise.all(inputs.map(async i => ({
  type: await i.getAttribute('type'),
  placeholder: await i.getAttribute('placeholder'),
  name: await i.getAttribute('name'),
  id: await i.getAttribute('id'),
}))));
const dialogs = await page.locator('[role="dialog"]').all();
console.log('Dialogs count:', dialogs.length);
if (dialogs.length) {
  const titles = await Promise.all(dialogs.map(async d => await d.locator('h2, h3').first().textContent().catch(()=>'')));
  console.log('Dialog titles:', titles);
}
await browser.close();
