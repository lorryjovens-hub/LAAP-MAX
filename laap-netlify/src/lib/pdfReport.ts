import html2canvas from 'html2canvas-pro';
import { jsPDF } from 'jspdf';

export interface ReportTableData {
  headers: string[];
  rows: string[][];
}

export interface ReportChartDataset {
  label: string;
  data: number[];
  color?: string;
}

export interface ReportChartData {
  type: 'bar' | 'line';
  labels: string[];
  datasets: ReportChartDataset[];
}

export type ReportSection =
  | { type: 'heading'; content: string; level?: number }
  | { type: 'paragraph'; content: string }
  | { type: 'table'; data: ReportTableData; caption?: string }
  | { type: 'chart'; data: ReportChartData; caption?: string }
  | { type: 'formula'; content: string };

export interface ReportPayload {
  title: string;
  subtitle?: string;
  sections: ReportSection[];
  theme?: 'dark' | 'light';
}

const THEME = {
  dark: {
    bg: '#1a1a1a',
    text: '#e5e5e5',
    muted: '#9ca3af',
    accent: '#f5c542',
    border: '#404040',
    headerBg: '#2a2a2a',
    chartGrid: '#404040',
  },
  light: {
    bg: '#ffffff',
    text: '#1a1a1a',
    muted: '#6b7280',
    accent: '#b45309',
    border: '#d1d5db',
    headerBg: '#f3f4f6',
    chartGrid: '#d1d5db',
  },
};

const CHART_COLORS = ['#f5c542', '#22d3ee', '#34d399', '#f472b6', '#a78bfa', '#fb923c'];

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function renderFormula(content: string): string {
  // Render inline math with KaTeX-style formatting fallback
  return `<div style="padding:12px 16px;background:rgba(245,197,66,0.08);border-left:3px solid ${THEME.dark.accent};font-family:'Courier New',monospace;font-size:13px;color:${THEME.dark.text};white-space:pre-wrap;border-radius:2px;">${escapeHtml(content)}</div>`;
}

function renderTable(data: ReportTableData, theme: typeof THEME.dark): string {
  const headerCells = data.headers.map((h) => `<th style="padding:10px 12px;background:${theme.headerBg};border:1px solid ${theme.border};font-weight:600;text-align:left;">${escapeHtml(h)}</th>`).join('');
  const bodyRows = data.rows
    .map(
      (row) =>
        `<tr>${row.map((cell) => `<td style="padding:8px 12px;border:1px solid ${theme.border};">${escapeHtml(cell)}</td>`).join('')}</tr>`
    )
    .join('');
  return `<table style="width:100%;border-collapse:collapse;margin:12px 0;font-size:13px;"><thead><tr>${headerCells}</tr></thead><tbody>${bodyRows}</tbody></table>`;
}

function renderChart(data: ReportChartData, theme: typeof THEME.dark): string {
  const width = 560;
  const height = 240;
  const padding = { top: 24, right: 24, bottom: 48, left: 48 };
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;

  const allValues = data.datasets.flatMap((d) => d.data);
  const maxValue = Math.max(...allValues, 1);
  const minValue = Math.min(...allValues, 0);
  const range = maxValue - minValue || 1;

  const labelX = (i: number) => padding.left + (i / (data.labels.length - 1 || 1)) * chartW;
  const valueY = (v: number) => padding.top + chartH - ((v - minValue) / range) * chartH;

  let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" style="max-width:100%;">`;

  // Grid lines
  for (let i = 0; i <= 5; i++) {
    const y = padding.top + (i / 5) * chartH;
    const value = maxValue - (i / 5) * range;
    svg += `<line x1="${padding.left}" y1="${y}" x2="${width - padding.right}" y2="${y}" stroke="${theme.chartGrid}" stroke-width="1"/>`;
    svg += `<text x="${padding.left - 8}" y="${y + 4}" font-size="10" fill="${theme.muted}" text-anchor="end">${value.toFixed(1)}</text>`;
  }

  // Axes
  svg += `<line x1="${padding.left}" y1="${padding.top}" x2="${padding.left}" y2="${height - padding.bottom}" stroke="${theme.border}" stroke-width="1"/>`;
  svg += `<line x1="${padding.left}" y1="${height - padding.bottom}" x2="${width - padding.right}" y2="${height - padding.bottom}" stroke="${theme.border}" stroke-width="1"/>`;

  // X labels
  data.labels.forEach((label, i) => {
    const x = labelX(i);
    svg += `<text x="${x}" y="${height - padding.bottom + 20}" font-size="10" fill="${theme.muted}" text-anchor="middle">${escapeHtml(label)}</text>`;
  });

  // Datasets
  data.datasets.forEach((dataset, dsIndex) => {
    const color = dataset.color || CHART_COLORS[dsIndex % CHART_COLORS.length];
    if (data.type === 'line') {
      let path = '';
      dataset.data.forEach((v, i) => {
        const x = labelX(i);
        const y = valueY(v);
        path += i === 0 ? `M ${x} ${y}` : ` L ${x} ${y}`;
        svg += `<circle cx="${x}" cy="${y}" r="3" fill="${color}"/>`;
      });
      svg += `<path d="${path}" fill="none" stroke="${color}" stroke-width="2"/>`;
    } else {
      const barW = chartW / data.labels.length / (data.datasets.length + 1);
      dataset.data.forEach((v, i) => {
        const x = labelX(i) - (chartW / data.labels.length / 2) + dsIndex * barW + barW / 2;
        const y = valueY(v);
        const h = height - padding.bottom - y;
        svg += `<rect x="${x}" y="${y}" width="${barW * 0.8}" height="${h}" fill="${color}" rx="2"/>`;
      });
    }
  });

  // Legend
  data.datasets.forEach((dataset, i) => {
    const color = dataset.color || CHART_COLORS[i % CHART_COLORS.length];
    const lx = width - padding.right - 120;
    const ly = padding.top + i * 18;
    svg += `<rect x="${lx}" y="${ly - 8}" width="10" height="10" fill="${color}"/>`;
    svg += `<text x="${lx + 16}" y="${ly}" font-size="10" fill="${theme.text}">${escapeHtml(dataset.label)}</text>`;
  });

  svg += '</svg>';
  return `<div style="margin:12px 0;padding:12px;border:1px solid ${theme.border};border-radius:4px;background:${theme.headerBg};">${svg}</div>`;
}

function buildReportHtml(payload: ReportPayload): string {
  const theme = THEME[payload.theme === 'light' ? 'light' : 'dark'];
  const sectionsHtml = payload.sections
    .map((section) => {
      switch (section.type) {
        case 'heading':
          const level = Math.min(Math.max(section.level || 2, 1), 4);
          const fontSize = 22 - (level - 1) * 3;
          return `<h${level} style="margin:24px 0 12px;color:${theme.accent};font-size:${fontSize}px;font-weight:600;">${escapeHtml(section.content)}</h${level}>`;
        case 'paragraph':
          return `<p style="margin:10px 0;line-height:1.7;color:${theme.text};font-size:13px;">${escapeHtml(section.content).replace(/\n/g, '<br/>')}</p>`;
        case 'table':
          return `<div style="margin:12px 0;">${section.caption ? `<div style="font-size:12px;color:${theme.muted};margin-bottom:6px;">${escapeHtml(section.caption)}</div>` : ''}${renderTable(section.data, theme)}</div>`;
        case 'chart':
          return `<div style="margin:12px 0;">${section.caption ? `<div style="font-size:12px;color:${theme.muted};margin-bottom:6px;">${escapeHtml(section.caption)}</div>` : ''}${renderChart(section.data, theme)}</div>`;
        case 'formula':
          return renderFormula(section.content);
        default:
          return '';
      }
    })
    .join('');

  return `
    <div style="width:640px;padding:40px;background:${theme.bg};color:${theme.text};font-family:system-ui,-apple-system,sans-serif;box-sizing:border-box;">
      <div style="border-bottom:2px solid ${theme.accent};padding-bottom:16px;margin-bottom:24px;">
        <h1 style="margin:0;font-size:24px;color:${theme.accent};">${escapeHtml(payload.title)}</h1>
        ${payload.subtitle ? `<p style="margin:8px 0 0;color:${theme.muted};font-size:13px;">${escapeHtml(payload.subtitle)}</p>` : ''}
      </div>
      ${sectionsHtml}
    </div>
  `;
}

export async function generatePdfReport(payload: ReportPayload): Promise<Blob> {
  const container = document.createElement('div');
  container.innerHTML = buildReportHtml(payload);
  container.style.position = 'fixed';
  container.style.left = '-9999px';
  container.style.top = '0';
  document.body.appendChild(container);

  try {
    const canvas = await html2canvas(container, {
      scale: 2,
      useCORS: true,
      backgroundColor: null,
      width: 640,
      height: container.scrollHeight,
    });

    const imgData = canvas.toDataURL('image/png');
    const pdf = new jsPDF({
      orientation: 'p',
      unit: 'px',
      format: [canvas.width / 2, canvas.height / 2],
    });
    pdf.addImage(imgData, 'PNG', 0, 0, canvas.width / 2, canvas.height / 2);
    return pdf.output('blob');
  } finally {
    document.body.removeChild(container);
  }
}

export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
