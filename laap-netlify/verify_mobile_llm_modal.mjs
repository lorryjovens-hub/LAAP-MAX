import { chromium } from 'playwright';

const EDGE_PATH = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const URL = 'http://localhost:5173/studio';

(async () => {
  console.log('[verify] 启动 Edge 浏览器（移动端视口）...');

  const browser = await chromium.launch({
    headless: false,
    executablePath: EDGE_PATH,
    args: ['--remote-allow-origins=*'],
  });

  const context = await browser.newContext({
    viewport: { width: 375, height: 812 },
    user_agent:
      'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15',
  });

  const page = await context.newPage();

  // 清除所有存储，模拟首次访问
  await page.goto(URL, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('networkidle', { timeout: 15000 });

  await context.clearCookies();
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
  await page.evaluate(async () => {
    const dbs = await window.indexedDB.databases?.();
    if (dbs) {
      for (const db of dbs) {
        if (db.name) window.indexedDB.deleteDatabase(db.name);
      }
    }
  });

  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('networkidle', { timeout: 15000 });
  await page.waitForTimeout(3000);

  // 步骤 1：首次弹窗
  if (await page.isVisible('text=欢迎使用 LAAP Studio')) {
    console.log('✓ 步骤 1/4: FirstRunModal 已弹出');
    if (await page.isVisible('button:has-text("稍后配置")')) {
      await page.click('button:has-text("稍后配置")');
      await page.waitForTimeout(1000);
    }
  } else {
    console.log('ℹ 步骤 1/4: FirstRunModal 未弹出');
  }

  // 步骤 2：打开移动端侧边栏
  if (!(await page.isVisible('[data-slot="sheet-content"][data-state="open"]'))) {
    await page.click('button[aria-label="打开左侧面板"]', { timeout: 5000, force: true });
  }
  const sidebarOpen = await page.isVisible('[data-slot="sheet-content"][data-state="open"]');
  console.log(sidebarOpen ? '✓ 步骤 2/4: 移动端侧边栏已打开' : '✗ 步骤 2/4: 移动端侧边栏未打开');
  await page.waitForTimeout(800);

  // 步骤 3：点击「打开 LLM 配置弹窗」
  await page.$$eval('button', (buttons) => {
    const btn = buttons.find(
      (b) => b.innerText.includes('打开 LLM 配置弹窗') && b.offsetParent !== null
    );
    if (btn) btn.click();
  });
  console.log('✓ 步骤 3/4: 已点击「打开 LLM 配置弹窗」');

  await page.waitForTimeout(2000);

  // 步骤 4：验证 LLMConfigModal 内容
  const modalText = await page.locator('[data-slot="dialog-content"]:has-text("LLM 配置")').innerText().catch(() => '');
  const modalVisible = modalText.includes('LLM 配置');
  console.log(modalVisible ? '✓ 步骤 4/4: LLMConfigModal 已成功弹出' : '✗ 步骤 4/4: LLMConfigModal 未弹出');

  if (modalVisible) {
    // 检查弹窗内的关键元素
    const hasOmniRoute = modalText.includes('OmniRoute');
    const hasBaseURL = modalText.includes('BASE URL');
    const hasAPIKey = modalText.includes('API KEY');
    const hasSave = modalText.includes('保存');
    console.log(`[verify] 弹窗内容检查: OmniRoute=${hasOmniRoute}, BaseURL=${hasBaseURL}, APIKey=${hasAPIKey}, 保存=${hasSave}`);

    // 尝试点击 OmniRoute 预设按钮（进一步验证弹窗可交互）
    await page.$$eval('button', (buttons) => {
      const btn = buttons.find((b) => b.innerText.includes('OmniRoute') && b.offsetParent !== null);
      if (btn) btn.click();
    });
    await page.waitForTimeout(500);

    const modalText2 = await page.locator('[data-slot="dialog-content"]:has-text("LLM 配置")').innerText().catch(() => '');
    const modelSectionVisible = modalText2.includes('模型');
    console.log(modelSectionVisible ? '[verify] 点击 OmniRoute 后模型选择区可见' : '[verify] 模型选择区未显示');
  }

  // 保存最终截图
  await page.screenshot({ path: 'verify_mobile_llm_modal_final.png', fullPage: true });
  console.log('[verify] 已保存最终截图: verify_mobile_llm_modal_final.png');

  // 停留 8 秒方便肉眼确认
  console.log('[verify] 浏览器将保持打开 8 秒，请观察...');
  await page.waitForTimeout(8000);

  await browser.close();
  console.log('[verify] 验证结束');
})();
