import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
await page.goto('http://localhost:5173/studio');
await page.waitForLoadState('networkidle');
await page.keyboard.press('Escape');
await page.waitForTimeout(300);
await page.locator('button:has-text("登录 / 注册")').first().click();
await page.waitForTimeout(300);
await page.locator('button:has-text("立即注册")').first().click();
await page.waitForTimeout(300);
const html = await page.evaluate(() => {
  const dialog = document.querySelector('[data-slot="dialog-content"]');
  return dialog ? dialog.innerHTML.slice(0, 4000) : 'no dialog';
});
console.log('Register form HTML:', html);
const inputs = await page.locator('[data-slot="dialog-content"] input').all();
console.log('Register inputs:', await Promise.all(inputs.map(async i => ({
  type: await i.getAttribute('type'),
  placeholder: await i.getAttribute('placeholder'),
  label: await i.evaluate(el => (el.previousElementSibling?.textContent?.trim() || el.parentElement?.querySelector('label')?.textContent?.trim() || '')),
}))));
const buttons = await page.locator('[data-slot="dialog-content"] button').all();
console.log('Buttons:', (await Promise.all(buttons.map(b => b.textContent()))).map(t=>t?.trim()).filter(Boolean));
await page.screenshot({ path: 'scripts/recon_register_switch.png', fullPage: true });
await browser.close();
