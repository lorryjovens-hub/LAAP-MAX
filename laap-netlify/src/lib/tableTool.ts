import type { Tool } from '@/lib/localLlm';
import { renderTableToPng, type TableData, parseMarkdownTable } from '@/lib/tableRenderer';

export function buildRenderTableTool(): Tool {
  return {
    name: 'render_table_as_image',
    description:
      'Render a data table as a shareable PNG image. Use when the user asks for a table, chart-like summary, or wants to export structured data as an image. Accepts either explicit headers/rows or a markdown table string.',
    parameters: {
      type: 'object',
      properties: {
        title: { type: 'string', description: 'Optional title shown above the table' },
        caption: { type: 'string', description: 'Optional caption shown below the table' },
        headers: {
          type: 'array',
          items: { type: 'string' },
          description: 'Column headers',
        },
        rows: {
          type: 'array',
          items: {
            type: 'array',
            items: { type: 'string' },
          },
          description: 'Table rows, each is an array of cell strings matching headers',
        },
        markdownTable: {
          type: 'string',
          description: 'Alternative: a markdown table string. If provided, headers and rows are ignored.',
        },
        theme: {
          type: 'string',
          enum: ['dark', 'light'],
          description: 'Color theme. Defaults to dark to match LAAP Studio.',
        },
      },
      oneOf: [
        { required: ['headers', 'rows'] },
        { required: ['markdownTable'] },
      ],
    },
    execute: async (args) => {
      let data: TableData;
      const theme = args.theme === 'light' ? 'light' : 'dark';
      const markdownTable = String(args.markdownTable || '').trim();

      if (markdownTable) {
        const parsed = parseMarkdownTable(markdownTable);
        if (!parsed) {
          return '无法解析 markdown 表格，请检查格式（需要表头行和分隔符行）。';
        }
        data = { ...parsed, theme };
      } else {
        const headers = Array.isArray(args.headers)
          ? args.headers.map(String)
          : [];
        const rows = Array.isArray(args.rows)
          ? args.rows.map((row: unknown) =>
              Array.isArray(row) ? row.map(String) : [String(row)]
            )
          : [];
        if (headers.length === 0) return '缺少表格表头';
        data = {
          title: args.title ? String(args.title) : undefined,
          caption: args.caption ? String(args.caption) : undefined,
          headers,
          rows,
          theme,
        };
      }

      try {
        const base64 = await renderTableToPng(data);
        return `TABLE_IMAGE:${base64}`;
      } catch (err) {
        return `表格图片生成失败：${err instanceof Error ? err.message : String(err)}`;
      }
    },
  };
}
