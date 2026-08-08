import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
await page.goto('http://localhost:5173/studio');
await page.waitForLoadState('networkidle');
await page.keyboard.press('Escape');
await page.waitForTimeout(300);

const html = await page.evaluate(() => {
  const ta = document.querySelector('textarea[placeholder*="输入消息"]');
  if (!ta) return 'textarea not found';
  return ta.parentElement?.outerHTML?.slice(0, 2000) || '';
});
console.log('Chat input parent:', html);
await browser.close();
