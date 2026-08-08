import { chromium, devices } from 'playwright';

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: 375, height: 812 },
  userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
  isMobile: true,
  hasTouch: true,
});
const page = await context.newPage();

page.on('console', msg => console.log('CONSOLE:', msg.text()));
page.on('pageerror', err => console.log('PAGEERROR:', err.message));

// Mock completions for mobile chat test
await page.route('**/api/sensenova/v1/chat/completions', async (route, request) => {
  let body = {};
  try { body = request.postDataJSON() || {}; } catch { /* ignore */ }
  if (body && body.stream) {
    return route.fulfill({
      status: 200,
      contentType: 'text/event-stream; charset=utf-8',
      body: 'data: {"choices":[{"delta":{"content":"移动端模拟回复"}}]}\n\ndata: [DONE]\n\n',
    });
  }
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ choices: [{ message: { content: '移动端模拟回复' } }] }),
  });
});

await page.goto('http://localhost:5173/');
await page.waitForLoadState('networkidle');
await page.waitForTimeout(500);
await page.screenshot({ path: 'scripts/mobile_home.png', fullPage: true });

const homeBtns = (await Promise.all((await page.locator('button, a').all()).map(el => el.textContent())))
  .map(t => t?.trim()).filter(Boolean);
console.log('Homepage mobile buttons/links:', homeBtns.slice(0, 30));

// Navigate to Studio
await page.goto('http://localhost:5173/studio');
await page.waitForLoadState('networkidle');
await page.keyboard.press('Escape');
await page.waitForTimeout(300);
await page.screenshot({ path: 'scripts/mobile_studio.png', fullPage: true });

const studioBtns = (await Promise.all((await page.locator('button').all()).map(b => b.textContent())))
  .map(t => t?.trim()).filter(Boolean);
console.log('Studio mobile buttons:', studioBtns.slice(0, 40));

// Open mobile menu if hamburger exists
const menuBtn = page.locator('button[aria-label*="菜单"], button[aria-label*="menu"], button:has-text("☰")').first();
if (await menuBtn.isVisible().catch(() => false)) {
  await menuBtn.tap();
  await page.waitForTimeout(500);
  await page.screenshot({ path: 'scripts/mobile_menu.png', fullPage: true });
}

// Try sending a message on mobile
const chatTa = page.locator('textarea[placeholder*="输入消息"]');
if (await chatTa.isVisible().catch(() => false)) {
  await chatTa.tap();
  await chatTa.fill('移动端测试');
  await chatTa.press('Enter');
  await page.waitForTimeout(1500);
  await page.screenshot({ path: 'scripts/mobile_chat.png', fullPage: true });
  const text = await page.evaluate(() => document.body.innerText);
  console.log('Mobile chat contains reply:', text.includes('移动端模拟回复'));
}

// Check horizontal overflow
const hasOverflow = await page.evaluate(() => {
  return document.documentElement.scrollWidth > window.innerWidth;
});
console.log('Horizontal overflow:', hasOverflow);

await browser.close();
