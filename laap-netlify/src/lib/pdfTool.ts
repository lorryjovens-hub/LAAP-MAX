import type { Tool } from '@/lib/localLlm';
import { generatePdfReport, downloadBlob, type ReportPayload, type ReportSection } from '@/lib/pdfReport';

export function buildGeneratePdfTool(): Tool {
  return {
    name: 'generate_pdf_report',
    description:
      'Generate a downloadable PDF report with text, tables, charts, and formulas. Use when the user asks for a PDF summary, visual report, chart analysis, or any structured content that would be easier to understand as a document.',
    parameters: {
      type: 'object',
      properties: {
        title: { type: 'string', description: 'Report title' },
        subtitle: { type: 'string', description: 'Optional subtitle' },
        filename: { type: 'string', description: 'Output filename without extension, e.g. "SAE_analysis_report"' },
        theme: { type: 'string', enum: ['dark', 'light'], description: 'Color theme, defaults to dark' },
        sections: {
          type: 'array',
          description: 'Report sections in order',
          items: {
            type: 'object',
            properties: {
              type: {
                type: 'string',
                enum: ['heading', 'paragraph', 'table', 'chart', 'formula'],
              },
              content: { type: 'string', description: 'For heading, paragraph, or formula' },
              level: { type: 'number', description: 'Heading level 1-4' },
              caption: { type: 'string', description: 'Caption for table or chart' },
              data: {
                type: 'object',
                description: 'For table or chart sections',
              },
            },
            required: ['type'],
          },
        },
      },
      required: ['title', 'filename', 'sections'],
    },
    execute: async (args) => {
      const title = String(args.title || '');
      const filename = String(args.filename || 'report');
      if (!title) return '缺少报告标题';
      if (!Array.isArray(args.sections)) return 'sections 必须是数组';

      const sections: ReportSection[] = [];
      for (const raw of args.sections) {
        if (!raw || typeof raw !== 'object') continue;
        const type = String(raw.type);
        switch (type) {
          case 'heading':
            sections.push({ type: 'heading', content: String(raw.content || ''), level: Number(raw.level) || 2 });
            break;
          case 'paragraph':
            sections.push({ type: 'paragraph', content: String(raw.content || '') });
            break;
          case 'formula':
            sections.push({ type: 'formula', content: String(raw.content || '') });
            break;
          case 'table': {
            const data = raw.data as { headers?: unknown; rows?: unknown } | undefined;
            const headers = Array.isArray(data?.headers) ? data.headers.map(String) : [];
            const rows = Array.isArray(data?.rows)
              ? data.rows.map((row: unknown) => (Array.isArray(row) ? row.map(String) : [String(row)]))
              : [];
            sections.push({ type: 'table', data: { headers, rows }, caption: raw.caption ? String(raw.caption) : undefined });
            break;
          }
          case 'chart': {
            const data = raw.data as
              | { type?: string; labels?: unknown; datasets?: unknown }
              | undefined;
            const labels = Array.isArray(data?.labels) ? data.labels.map(String) : [];
            const datasets = Array.isArray(data?.datasets)
              ? data.datasets.map((ds: unknown, i: number) => {
                  const d = ds as { label?: string; data?: unknown; color?: string } | undefined;
                  return {
                    label: d?.label ? String(d.label) : `Series ${i + 1}`,
                    data: Array.isArray(d?.data) ? d.data.map((v: unknown) => Number(v) || 0) : [],
                    color: d?.color ? String(d.color) : undefined,
                  };
                })
              : [];
            sections.push({
              type: 'chart',
              data: { type: data?.type === 'line' ? 'line' : 'bar', labels, datasets },
              caption: raw.caption ? String(raw.caption) : undefined,
            });
            break;
          }
        }
      }

      const payload: ReportPayload = {
        title,
        subtitle: args.subtitle ? String(args.subtitle) : undefined,
        sections,
        theme: args.theme === 'light' ? 'light' : 'dark',
      };

      try {
        const blob = await generatePdfReport(payload);
        const safeName = filename.replace(/[^\w\u4e00-\u9fa5\-]/g, '_');
        downloadBlob(blob, `${safeName}.pdf`);
        return `已生成并下载 PDF 报告：${safeName}.pdf`;
      } catch (err) {
        return `PDF 生成失败：${err instanceof Error ? err.message : String(err)}`;
      }
    },
  };
}
