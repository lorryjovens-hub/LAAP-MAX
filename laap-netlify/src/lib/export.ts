import type { ChatMessage } from '@/lib/chat';
import type { StructuredMemory } from '@/lib/memoryManager';

/**
 * 美观纸质风格的 Q&A 导出工具。
 * 支持将聊天记录与长期记忆导出为 Markdown / HTML 两种格式，
 * 排版采用复古纸张质感：米白纸面、衬线字体、金色点缀、Q&A 分栏。
 */

const MEMORY_TYPE_LABELS: Record<string, string> = {
  fact: '事实',
  preference: '偏好',
  episodic: '经历',
  task: '任务',
  relationship: '关系',
  concept: '概念',
};

function formatTime(iso?: string): string {
  if (!iso) return '';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/** 将消息正文渲染为 HTML——识别 ``` 代码块，其余内容转义并保留换行。 */
function renderContentHtml(raw: string): string {
  const trimmed = raw ?? '';
  const parts = trimmed.split(/```(\w*)\n?([\s\S]*?)```/g);
  let html = '';
  for (let i = 0; i < parts.length; i++) {
    if (i % 3 === 0) {
      // 普通文本
      const text = parts[i];
      if (text) {
        html += escapeHtml(text)
          .split('\n')
          .map((line) => {
            const t = line.trim();
            if (t.startsWith('### ')) return `<h4>${escapeHtml(t.slice(4))}</h4>`;
            if (t.startsWith('## ')) return `<p class="h2">${escapeHtml(t.slice(3))}</p>`;
            if (t.startsWith('# ')) return `<p class="h1">${escapeHtml(t.slice(2))}</p>`;
            if (t.startsWith('- ')) return `<li>${escapeHtml(t.slice(2))}</li>`;
            return `<p>${escapeHtml(line)}</p>`;
          })
          .join('');
      }
    } else if (i % 3 === 1) {
      // 语言标签
    } else {
      // 代码块内容
      html += `<pre><code>${escapeHtml(parts[i])}</code></pre>`;
    }
  }
  if (!html) html = `<p>${escapeHtml(trimmed).replace(/\n/g, '<br/>')}</p>`;
  return html;
}

/** 将消息正文转换为 Markdown（保留代码块，其余原样）。 */
function renderContentMarkdown(raw: string): string {
  return raw ?? '';
}

// ---------------------------------------------------------------------------
// 聊天记录导出
// ---------------------------------------------------------------------------

export function exportChatAsMarkdown(
  title: string,
  messages: ChatMessage[],
  username: string
): string {
  const now = new Date();
  const blockCount = messages.filter((m) => m.role !== 'system').length;
  const lines: string[] = [];
  lines.push('# 🗒️ 对话记录 · LAAP');
  lines.push('');
  lines.push(`## ${escapeHtml(title)}`);
  lines.push('');
  lines.push(`> 与 LAAP 的一段深度对话`);
  lines.push(`> 用户：**${escapeHtml(username)}** ｜ 导出时间：${now.toLocaleString('zh-CN')} ｜ 共 ${blockCount} 条消息`);
  lines.push('');
  lines.push('---');
  lines.push('');

  for (const m of messages) {
    if (m.role === 'system') continue;
    const time = m.created_at ? formatTime(m.created_at) : '';
    if (m.role === 'user') {
      lines.push(`## ✍️ 问 · ${time}`);
      lines.push('');
      lines.push(renderContentMarkdown(m.content));
      lines.push('');
    } else {
      lines.push(`## 💬 答 · LAAP`);
      lines.push('');
      lines.push(renderContentMarkdown(m.content));
      lines.push('');
    }
    lines.push('---');
    lines.push('');
  }

  lines.push(`*—— 由 LAAP 导出 · ${now.toLocaleString('zh-CN')} ——*`);
  return lines.join('\n');
}

export function exportChatAsHtml(
  title: string,
  messages: ChatMessage[],
  username: string
): string {
  const now = new Date();
  const blockCount = messages.filter((m) => m.role !== 'system').length;
  const body = messages
    .filter((m) => m.role !== 'system')
    .map((m) => {
      const time = m.created_at ? formatTime(m.created_at) : '';
      if (m.role === 'user') {
        return `<div class="qa qa-q"><div class="qa-head"><span class="badge badge-q">问</span><span class="qa-name">${escapeHtml(username)}</span><span class="qa-time">${escapeHtml(time)}</span></div><div class="qa-body">${renderContentHtml(m.content)}</div></div>`;
      }
      return `<div class="qa qa-a"><div class="qa-head"><span class="badge badge-a">答</span><span class="qa-name">LAAP</span><span class="qa-time">${escapeHtml(time)}</span></div><div class="qa-body">${renderContentHtml(m.content)}</div></div>`;
    })
    .join('\n');

  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>${escapeHtml(title)} · LAAP 对话记录</title>
<style>
  * { box-sizing: border-box; }
  body {
    margin: 0;
    padding: 40px 16px;
    background: #2b2b2b no-repeat center/cover fixed;
    background-image: linear-gradient(rgba(20,20,18,.55), rgba(20,20,18,.55)), url('https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=warm%20vintage%20paper%20texture%2C%20subtle%20dark%20wooden%20desk%20background%2C%20soft%20lighting&image_size=landscape_16_9');
    font-family: "Georgia", "Songti SC", "SimSun", serif;
    line-height: 1.75;
    color: #3a2e22;
    -webkit-print-color-adjust: exact;
  }
  .page {
    max-width: 820px;
    margin: 0 auto;
    background:
      linear-gradient(180deg, rgba(255,252,240,.96), rgba(249,241,218,.96)),
      repeating-linear-gradient(0deg, transparent 0, transparent 27px, rgba(180,150,100,.10) 27px, rgba(180,150,100,.10) 28px);
    border-radius: 6px;
    box-shadow: 0 18px 50px rgba(0,0,0,.55), 0 2px 6px rgba(0,0,0,.3);
    padding: 44px 48px 40px;
    position: relative;
  }
  .page::before {
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 6px;
    background: linear-gradient(90deg, #b8860b, #d4af37, #b8860b);
  }
  .header { text-align: center; margin-bottom: 26px; }
  .header h1 {
    margin: 0 0 10px;
    font-size: 30px;
    color: #5a4526;
    letter-spacing: 2px;
    font-weight: 700;
  }
  .header .rule { border: none; border-top: 1px solid #d8c9a3; margin: 14px auto; width: 70%; }
  .header .meta { font-size: 13px; color: #8a7350; }
  .qa {
    border: 1px solid #e2d3ab;
    border-radius: 4px;
    margin: 18px 0;
    background: rgba(255, 253, 245, .72);
    box-shadow: 0 1px 3px rgba(120, 95, 40, .08);
    overflow: hidden;
  }
  .qa-q { border-left: 5px solid #b8860b; }
  .qa-a { border-left: 5px solid #7a8a6a; }
  .qa-head {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 14px;
    background: rgba(214, 190, 130, .18);
    border-bottom: 1px dashed #dccfae;
    font-size: 12px;
    color: #6b5638;
  }
  .badge {
    display: inline-block;
    min-width: 30px;
    text-align: center;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 700;
    color: #fff;
  }
  .badge-q { background: #b8860b; }
  .badge-a { background: #7a8a6a; }
  .qa-name { font-weight: 700; color: #4a3a22; }
  .qa-time { margin-left: auto; color: #a08a5f; font-style: italic; }
  .qa-body { padding: 12px 16px; }
  .qa-body p { margin: 6px 0; }
  .qa-body h1, .qa-body h2, .qa-body h3, .qa-body h4 { margin: 10px 0 6px; color: #4a3a22; }
  .qa-body li { margin-left: 20px; }
  .qa-body pre {
    background: #2f2a20;
    color: #f0e6cf;
    padding: 12px;
    border-radius: 4px;
    overflow-x: auto;
    font-size: 13px;
  }
  .qa-body code { font-family: "Consolas", Menlo, monospace; }
  .footer {
    text-align: center;
    margin-top: 30px;
    font-size: 12px;
    color: #a08a5f;
    font-style: italic;
  }
  @media (max-width: 600px) {
    .page { padding: 28px 18px; }
  }
</style>
</head>
<body>
  <div class="page">
    <div class="header">
      <h1>🗒️ ${escapeHtml(title)}</h1>
      <hr class="rule" />
      <div class="meta">用户：${escapeHtml(username)} ｜ 导出时间：${now.toLocaleString('zh-CN')} ｜ 共 ${blockCount} 条消息</div>
    </div>
    ${body}
    <div class="footer">—— 由 LAAP 导出 · ${now.toLocaleString('zh-CN')} ——</div>
  </div>
</body>
</html>`;
}

// ---------------------------------------------------------------------------
// 记忆备份 / 导出
// ---------------------------------------------------------------------------

export function exportMemoriesAsMarkdown(
  memories: StructuredMemory[],
  name: string
): string {
  const now = new Date();
  const byType: Record<string, StructuredMemory[]> = {};
  for (const m of memories) {
    const key = MEMORY_TYPE_LABELS[m.type] ?? m.type;
    byType[key] = byType[key] || [];
    byType[key].push(m);
  }

  const lines: string[] = [];
  lines.push('# 🧠 记忆手账 · LAAP');
  lines.push('');
  lines.push(`> 用户：**${escapeHtml(name)}** ｜ 导出时间：${now.toLocaleString('zh-CN')} ｜ 记忆总数：**${memories.length}**`);
  lines.push('');
  lines.push('---');
  lines.push('');

  for (const [type, items] of Object.entries(byType)) {
    lines.push(`## 📖 ${type}记忆 · ${items.length} 条`);
    lines.push('');
    for (const m of items) {
      const time = formatTime(m.createdAt);
      lines.push(`- **${m.content}**`);
      if (time) lines.push(`  - 记录于 ${time}${m.source ? ` ｜ 来源：${m.source}` : ''}`);
    }
    lines.push('');
  }

  lines.push(`*—— 由 LAAP 记忆备份 · ${now.toLocaleString('zh-CN')} ——*`);
  return lines.join('\n');
}

export function exportMemoriesAsHtml(
  memories: StructuredMemory[],
  name: string
): string {
  const now = new Date();
  const byType: Record<string, StructuredMemory[]> = {};
  for (const m of memories) {
    const key = MEMORY_TYPE_LABELS[m.type] ?? m.type;
    byType[key] = byType[key] || [];
    byType[key].push(m);
  }

  const sections = Object.entries(byType)
    .map(
      ([type, items]) => `<div class="mem-section">
  <h2>📖 ${escapeHtml(type)}记忆 · ${items.length} 条</h2>
  ${items
    .map(
      (m) => `<div class="mem">
    <div class="mem-body">${renderContentHtml(m.content)}</div>
    <div class="mem-meta">${escapeHtml(formatTime(m.createdAt))}${m.source ? ` ｜ 来源：${escapeHtml(m.source)}` : ''} ｜ 重要度 ${m.importance}%</div>
  </div>`
    )
    .join('\n  ')}
</div>`
    )
    .join('\n');

  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>记忆手账 · LAAP</title>
<style>
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 40px 16px;
    background: #2b2b2b;
    background-image: linear-gradient(rgba(20,20,18,.55), rgba(20,20,18,.55)), url('https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=warm%20vintage%20paper%20texture%2C%20quill%20pen%20and%20ink%2C%20dark%20wooden%20desk&image_size=landscape_16_9');
    font-family: "Georgia", "Songti SC", "SimSun", serif;
    line-height: 1.75; color: #3a2e22;
    -webkit-print-color-adjust: exact;
  }
  .page {
    max-width: 820px; margin: 0 auto;
    background: linear-gradient(180deg, rgba(255,252,240,.96), rgba(249,241,218,.96));
    border-radius: 6px;
    box-shadow: 0 18px 50px rgba(0,0,0,.55);
    padding: 44px 48px 40px; position: relative;
  }
  .page::before { content: ""; position: absolute; top:0; left:0; right:0; height:6px; background: linear-gradient(90deg,#b8860b,#d4af37,#b8860b); }
  .header { text-align: center; margin-bottom: 26px; }
  .header h1 { margin: 0 0 10px; font-size: 30px; color: #5a4526; letter-spacing: 2px; }
  .header .rule { border:none; border-top:1px solid #d8c9a3; margin:14px auto; width:70%; }
  .header .meta { font-size: 13px; color: #8a7350; }
  .mem-section { margin: 22px 0; }
  .mem-section h2 { color: #5a4526; border-bottom: 1px dashed #d1bd8f; padding-bottom: 6px; font-size: 19px; }
  .mem {
    border: 1px solid #e2d3ab; border-left: 5px solid #7a8a6a;
    border-radius: 4px; margin: 12px 0; padding: 10px 14px;
    background: rgba(255,253,245,.72); box-shadow: 0 1px 3px rgba(120,95,40,.08);
  }
  .mem-body p { margin: 4px 0; }
  .mem-meta { margin-top: 6px; font-size: 12px; color: #a08a5f; font-style: italic; }
  .mem-body pre { background:#2f2a20; color:#f0e6cf; padding:10px; border-radius:4px; overflow-x:auto; font-size:13px; }
  .footer { text-align:center; margin-top:30px; font-size:12px; color:#a08a5f; font-style:italic; }
  @media (max-width:600px){ .page{ padding:28px 18px; } }
</style>
</head>
<body>
  <div class="page">
    <div class="header">
      <h1>🧠 记忆手账 · LAAP</h1>
      <hr class="rule" />
      <div class="meta">用户：${escapeHtml(name)} ｜ 导出时间：${now.toLocaleString('zh-CN')} ｜ 记忆总数：${memories.length}</div>
    </div>
    ${sections}
    <div class="footer">—— 由 LAAP 记忆备份 · ${now.toLocaleString('zh-CN')} ——</div>
  </div>
</body>
</html>`;
}

// ---------------------------------------------------------------------------
// 下载辅助
// ---------------------------------------------------------------------------

export function downloadTextFile(filename: string, content: string, mimeType = 'text/markdown'): void {
  const blob = new Blob([content], { type: `${mimeType};charset=utf-8` });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}