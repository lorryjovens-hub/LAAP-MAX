import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
await page.goto('http://localhost:5173/studio');
await page.waitForLoadState('networkidle');
await page.keyboard.press('Escape');
await page.waitForTimeout(300);

// Find chat input
const inputs = await page.locator('textarea, input').all();
const chatInputs = [];
for (const i of inputs) {
  const placeholder = await i.getAttribute('placeholder');
  if (placeholder && (placeholder.includes('消息') || placeholder.includes('输入') || placeholder.includes('说点什么') || placeholder.includes('发送'))) {
    chatInputs.push({ tag: await i.evaluate(el => el.tagName), placeholder });
  }
}
console.log('Chat inputs:', chatInputs);

// Find send button
const sendBtns = (await Promise.all((await page.locator('button').all()).map(async b => {
  const text = (await b.textContent())?.trim() || '';
  const aria = await b.getAttribute('aria-label');
  return { text, aria };
}))).filter(x => x.text.includes('发送') || x.aria?.includes('发送') || x.text.includes('Send') || x.text.includes('→'));
console.log('Send buttons:', sendBtns);

await page.screenshot({ path: 'scripts/recon_chat.png', fullPage: true });
await browser.close();
