export interface TableCell {
  value: string;
  rowSpan?: number;
  colSpan?: number;
  align?: 'left' | 'center' | 'right';
  bold?: boolean;
}

export interface TableData {
  title?: string;
  headers: string[];
  rows: (string | TableCell)[][];
  caption?: string;
  theme?: 'dark' | 'light';
}

function escapeXml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

function measureTextWidth(text: string, fontSize: number, bold = false): number {
  // Approximate width: CJK chars count as 1.6x latin width
  let width = 0;
  for (const char of String(text)) {
    const code = char.charCodeAt(0);
    const isCjk = code >= 0x4e00 && code <= 0x9fff;
    width += isCjk ? fontSize * 1.6 : fontSize * 0.55;
  }
  return width + (bold ? fontSize * 0.2 : 0);
}

function computeColumnWidths(data: TableData, fontSize: number): number[] {
  const padding = fontSize * 1.2;
  const colCount = data.headers.length;
  const widths = new Array(colCount).fill(fontSize * 4);

  data.headers.forEach((h, i) => {
    widths[i] = Math.max(widths[i], measureTextWidth(h, fontSize, true) + padding * 2);
  });

  for (const row of data.rows) {
    row.forEach((cell, i) => {
      if (i >= colCount) return;
      const value = typeof cell === 'string' ? cell : cell.value;
      const bold = typeof cell === 'object' ? cell.bold : false;
      widths[i] = Math.max(widths[i], measureTextWidth(value, fontSize, bold) + padding * 2);
    });
  }

  return widths.map((w) => Math.min(w, fontSize * 28));
}

function buildTableSvg(data: TableData): { svg: string; width: number; height: number } {
  const fontSize = 14;
  const headerFontSize = 14;
  const titleFontSize = 16;
  const captionFontSize = 12;
  const rowHeight = fontSize * 2.4;
  const titleHeight = data.title ? titleFontSize * 2.8 : 0;
  const captionHeight = data.caption ? captionFontSize * 2.4 : 0;

  const isDark = data.theme !== 'light';
  const bgColor = isDark ? '#1a1a1a' : '#ffffff';
  const textColor = isDark ? '#e5e5e5' : '#1a1a1a';
  const headerBg = isDark ? '#2a2a2a' : '#f3f4f6';
  const borderColor = isDark ? '#404040' : '#d1d5db';
  const titleColor = isDark ? '#f5c542' : '#b45309';
  const captionColor = isDark ? '#9ca3af' : '#6b7280';

  const widths = computeColumnWidths(data, fontSize);
  const tableWidth = widths.reduce((a, b) => a + b, 0) + (widths.length + 1);
  const tableHeight = rowHeight * (1 + data.rows.length) + 2;
  const width = Math.max(tableWidth, data.title ? Math.min(measureTextWidth(data.title, titleFontSize, true) + 32, 720) : 0);
  const height = titleHeight + tableHeight + captionHeight + 16;

  let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">`;
  svg += `<rect width="${width}" height="${height}" fill="${bgColor}"/>`;

  let y = 8;
  if (data.title) {
    svg += `<text x="${width / 2}" y="${y + titleFontSize}" font-family="system-ui, -apple-system, sans-serif" font-size="${titleFontSize}" font-weight="bold" fill="${titleColor}" text-anchor="middle">${escapeXml(data.title)}</text>`;
    y += titleHeight;
  }

  // Table background
  const tableX = Math.max(0, (width - tableWidth) / 2);
  svg += `<rect x="${tableX}" y="${y}" width="${tableWidth}" height="${tableHeight}" fill="${bgColor}" stroke="${borderColor}" stroke-width="1"/>`;

  // Header row
  let x = tableX + 1;
  for (let i = 0; i < data.headers.length; i++) {
    const w = widths[i];
    svg += `<rect x="${x}" y="${y + 1}" width="${w}" height="${rowHeight}" fill="${headerBg}"/>`;
    svg += `<text x="${x + w / 2}" y="${y + 1 + rowHeight / 2 + headerFontSize * 0.35}" font-family="system-ui, -apple-system, sans-serif" font-size="${headerFontSize}" font-weight="bold" fill="${textColor}" text-anchor="middle">${escapeXml(data.headers[i])}</text>`;
    x += w;
  }

  // Horizontal line under header
  svg += `<line x1="${tableX}" y1="${y + 1 + rowHeight}" x2="${tableX + tableWidth}" y2="${y + 1 + rowHeight}" stroke="${borderColor}" stroke-width="1"/>`;

  // Rows
  let rowY = y + 1 + rowHeight;
  for (const row of data.rows) {
    x = tableX + 1;
    for (let i = 0; i < data.headers.length; i++) {
      const cell = row[i];
      if (cell === undefined) continue;
      const w = widths[i];
      const value = typeof cell === 'string' ? cell : cell.value;
      const align = typeof cell === 'object' ? cell.align : 'left';
      const bold = typeof cell === 'object' ? cell.bold : false;
      let textX: number;
      switch (align) {
        case 'center':
          textX = x + w / 2;
          break;
        case 'right':
          textX = x + w - fontSize * 0.8;
          break;
        default:
          textX = x + fontSize * 0.8;
      }
      const anchor = align === 'center' ? 'middle' : align === 'right' ? 'end' : 'start';
      const weight = bold ? 'bold' : 'normal';
      svg += `<text x="${textX}" y="${rowY + rowHeight / 2 + fontSize * 0.35}" font-family="system-ui, -apple-system, sans-serif" font-size="${fontSize}" font-weight="${weight}" fill="${textColor}" text-anchor="${anchor}">${escapeXml(value)}</text>`;
      x += w;
    }
    rowY += rowHeight;
  }

  // Vertical lines
  x = tableX + 1;
  for (const w of widths) {
    x += w;
    svg += `<line x1="${x}" y1="${y + 1}" x2="${x}" y2="${y + tableHeight - 1}" stroke="${borderColor}" stroke-width="1"/>`;
  }

  if (data.caption) {
    const captionY = y + tableHeight + captionFontSize + 8;
    svg += `<text x="${width / 2}" y="${captionY}" font-family="system-ui, -apple-system, sans-serif" font-size="${captionFontSize}" fill="${captionColor}" text-anchor="middle">${escapeXml(data.caption)}</text>`;
  }

  svg += '</svg>';
  return { svg, width, height };
}

export async function renderTableToPng(data: TableData): Promise<string> {
  const { svg, width, height } = buildTableSvg(data);
  const svgBlob = new Blob([svg], { type: 'image/svg+xml;charset=utf-8' });
  const url = URL.createObjectURL(svgBlob);

  try {
    const img = new Image();
    const canvas = document.createElement('canvas');
    const scale = 2;
    canvas.width = width * scale;
    canvas.height = height * scale;
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('无法创建 canvas 上下文');

    await new Promise<void>((resolve, reject) => {
      img.onload = () => {
        ctx.scale(scale, scale);
        ctx.drawImage(img, 0, 0, width, height);
        URL.revokeObjectURL(url);
        resolve();
      };
      img.onerror = reject;
      img.src = url;
    });

    return canvas.toDataURL('image/png').replace(/^data:image\/png;base64,/, '');
  } catch {
    URL.revokeObjectURL(url);
    throw new Error('表格图片生成失败');
  }
}

export function parseMarkdownTable(markdown: string): TableData | null {
  const lines = markdown.split('\n').map((l) => l.trim()).filter(Boolean);
  if (lines.length < 2) return null;

  // Detect if second line is separator
  const separator = lines[1];
  const isSeparator = /^[\|\-:\s]+$/.test(separator);
  if (!isSeparator) return null;

  const headers = lines[0]
    .split('|')
    .map((c) => c.trim())
    .filter((c) => c);

  const rows = lines.slice(2).map((line) =>
    line
      .split('|')
      .map((c) => c.trim())
      .filter((c) => c)
  );

  return { headers, rows };
}
