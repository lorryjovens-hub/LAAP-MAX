import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
const page = await context.newPage();

const screenshots = [];
async function snap(name) {
  const p = `scripts/${name}.png`;
  await page.screenshot({ path: p, fullPage: true });
  screenshots.push(p);
}

page.on('console', msg => console.log('CONSOLE:', msg.text()));
page.on('pageerror', err => console.log('PAGEERROR:', err.message));

// Mock SenseNova completions
await page.route('**/api/sensenova/v1/chat/completions', async (route, request) => {
  let body = {};
  try { body = request.postDataJSON() || {}; } catch { /* ignore */ }
  if (body && body.stream) {
    return route.fulfill({
      status: 200,
      contentType: 'text/event-stream; charset=utf-8',
      body: 'data: {"choices":[{"delta":{"content":"你好，这是模拟回复。"}}]}\n\ndata: [DONE]\n\n',
    });
  }
  return route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ choices: [{ message: { content: '你好，这是模拟回复。' } }] }),
  });
});

await page.goto('http://localhost:5173/studio');
await page.waitForLoadState('networkidle');

// Dismiss first-run LLM config modal
await page.keyboard.press('Escape');
await page.waitForTimeout(300);
await snap('01_studio');

// ---------------- Registration ----------------
await page.locator('button:has-text("登录 / 注册")').first().click();
await page.waitForTimeout(300);
await page.locator('button:has-text("立即注册")').first().click();
await page.waitForTimeout(300);

const regInputs = await page.locator('[data-slot="dialog-content"] input').all();
await regInputs[0].fill('TestUser');
await regInputs[1].fill(`test${Date.now()}@example.com`);
await regInputs[2].fill('password123');
await regInputs[3].fill('password123');
await snap('02_register_filled');

await page.locator('[data-slot="dialog-content"] button[type="submit"]').click();
// Wait for dialog to close (press Escape if it stays open)
try {
  await page.waitForSelector('[data-slot="dialog-content"]', { state: 'detached', timeout: 2000 });
} catch {
  await page.keyboard.press('Escape');
  await page.waitForTimeout(300);
}
await page.waitForTimeout(800);
await snap('03_registered');

const displayName = await page.evaluate(() => {
  const el = document.querySelector('[class*="text-sm text-white"]');
  return el?.textContent?.trim() || '';
});
console.log('Registered display name:', displayName);
if (!displayName.includes('TestUser')) {
  console.error('FAIL: expected display name TestUser');
}

// ---------------- Username change ----------------
await page.locator('button:has-text("高级设置")').first().click();
await page.waitForTimeout(500);
await snap('04_settings_open');

// Find username input by label
const settingsDialog = page.locator('[data-slot="dialog-content"]').last();
const usernameInput = settingsDialog.locator('input').first();
await usernameInput.fill('VerifiedUser');
await snap('05_username_changed');

// Save settings (look for save button in settings dialog)
const saveBtn = settingsDialog.locator('button:has-text("保存")').first();
await saveBtn.click();
await page.waitForTimeout(800);
await snap('06_settings_saved');
// Close settings dialog
await page.keyboard.press('Escape');
await page.waitForTimeout(300);

const newDisplayName = await page.evaluate(() => {
  const el = document.querySelector('[class*="text-sm text-white"]');
  return el?.textContent?.trim() || '';
});
console.log('After username change:', newDisplayName);
if (!newDisplayName.includes('VerifiedUser')) {
  console.error('FAIL: expected display name VerifiedUser');
}

// ---------------- Free call limit ----------------
// Get current user id for count key
const userId = await page.evaluate(() => {
  return localStorage.getItem('laap_local_account_user_id')
    || localStorage.getItem('laap_local_user_id')
    || 'guest';
});
console.log('User id:', userId);

// Inspect LLM config for debugging
const llmConfigDebug = await page.evaluate(() => localStorage.getItem('llm_config_v2'));
console.log('LLM config:', llmConfigDebug);

// Set count to 30 so next call exceeds limit
await page.evaluate((uid) => {
  localStorage.setItem(`laap_free_call_count_${uid}`, '30');
}, userId);

const chatTa = page.locator('textarea[placeholder*="输入消息"]');
await chatTa.click();
await chatTa.fill('这是一条测试消息');
await snap('07_message_typed');
await chatTa.press('Enter');
await page.waitForTimeout(2000);
await snap('08_limit_error');
const errorText = await page.evaluate(() => document.body.innerText);
console.log('Page text contains limit error:', errorText.includes('免费调用次数已用完'));
console.log('Page text snippet:', errorText.slice(0, 800));

const pageText = await page.evaluate(() => document.body.innerText);
if (pageText.includes('免费调用次数已用完')) {
  console.log('PASS: free call limit message shown');
} else {
  console.error('FAIL: free call limit message not found');
}

// ---------------- Export chat ----------------
// Clear count and send a couple messages with mock to have assistant messages
await page.evaluate((uid) => {
  localStorage.setItem(`laap_free_call_count_${uid}`, '0');
}, userId);

for (let i = 0; i < 2; i++) {
  await chatTa.fill(`测试问题 ${i + 1}`);
  await chatTa.press('Enter');
  await page.waitForTimeout(1200);
}
await snap('09_chat_messages');

await page.locator('button:has-text("高级设置")').first().click();
await page.waitForTimeout(500);
const settings2 = page.locator('[data-slot="dialog-content"]').last();
await settings2.locator('button:has-text("数据")').first().click();
await page.waitForTimeout(300);
await snap('09b_data_tab');

// Intercept downloads
const downloaded = [];
page.on('download', async download => {
  const filePath = path.join('scripts', download.suggestedFilename());
  await download.saveAs(filePath);
  downloaded.push(filePath);
});

// Click export .md and .html
const exportMdBtn = settings2.locator('button:has-text("导出 .md")');
const exportHtmlBtn = settings2.locator('button:has-text("导出 .html")');
console.log('Export md visible:', await exportMdBtn.isVisible().catch(() => false));
console.log('Export html visible:', await exportHtmlBtn.isVisible().catch(() => false));
if (await exportMdBtn.isVisible().catch(() => false)) {
  await exportMdBtn.click();
  await page.waitForTimeout(800);
}
if (await exportHtmlBtn.isVisible().catch(() => false)) {
  await exportHtmlBtn.click();
  await page.waitForTimeout(800);
}
await snap('10_export_clicked');

console.log('Downloaded files:', downloaded);
for (const f of downloaded) {
  if (fs.existsSync(f)) {
    const content = fs.readFileSync(f, 'utf-8');
    console.log(`--- ${f} ---`);
    console.log(content.slice(0, 500));
    if (f.endsWith('.html') && content.includes('class="page"')) {
      console.log('PASS: HTML export contains paper-style page class');
    }
    if (f.endsWith('.md') && content.includes('问')) {
      console.log('PASS: Markdown export contains Q&A markers');
    }
  }
}

await browser.close();
console.log('Screenshots:', screenshots);
