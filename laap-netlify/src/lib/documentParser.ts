import * as pdfjs from 'pdfjs-dist';
import { extractRawText } from 'mammoth';
import pdfjsWorkerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url';

pdfjs.GlobalWorkerOptions.workerSrc = pdfjsWorkerUrl;

const MAX_DOCUMENT_TEXT_LENGTH = 100_000;

export interface DocumentAttachment {
  id: string;
  name: string;
  type: 'document';
  mimeType: string;
  size: number;
  text: string;
  pages?: number;
}

export interface ParseDocumentResult {
  attachment: DocumentAttachment;
  truncated: boolean;
}

function getDocumentExtension(name: string): string {
  const lower = name.toLowerCase();
  const lastDot = lower.lastIndexOf('.');
  return lastDot >= 0 ? lower.slice(lastDot) : '';
}

function truncateText(text: string): { text: string; truncated: boolean } {
  if (text.length <= MAX_DOCUMENT_TEXT_LENGTH) {
    return { text, truncated: false };
  }
  return {
    text: text.slice(0, MAX_DOCUMENT_TEXT_LENGTH) + '\n\n[文档内容过长，已截断至前 100,000 字符]',
    truncated: true,
  };
}

async function readFileAsText(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result ?? ''));
    reader.onerror = () => reject(reader.error);
    reader.readAsText(file);
  });
}

async function readFileAsArrayBuffer(file: File): Promise<ArrayBuffer> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as ArrayBuffer);
    reader.onerror = () => reject(reader.error);
    reader.readAsArrayBuffer(file);
  });
}

async function parsePdf(file: File): Promise<{ text: string; pages: number }> {
  const arrayBuffer = await readFileAsArrayBuffer(file);
  const pdf = await pdfjs.getDocument({ data: arrayBuffer }).promise;
  const pages = pdf.numPages;
  const texts: string[] = [];

  for (let i = 1; i <= pages; i++) {
    const page = await pdf.getPage(i);
    const content = await page.getTextContent();
    const pageText = content.items
      .map((item) => ('str' in item ? item.str : ''))
      .join('');
    texts.push(pageText);
  }

  return { text: texts.join('\n\n'), pages };
}

async function parseDocx(file: File): Promise<{ text: string }> {
  const arrayBuffer = await readFileAsArrayBuffer(file);
  const result = await extractRawText({ arrayBuffer });
  return { text: result.value };
}

export function isDocumentFile(file: File): boolean {
  const ext = getDocumentExtension(file.name);
  return ext === '.pdf' || ext === '.docx' || ext === '.doc' || ext === '.txt' || ext === '.md' || ext === '.markdown';
}

export async function parseDocument(file: File): Promise<ParseDocumentResult> {
  const ext = getDocumentExtension(file.name);
  let rawText = '';
  let pages: number | undefined;

  if (ext === '.pdf') {
    const result = await parsePdf(file);
    rawText = result.text;
    pages = result.pages;
  } else if (ext === '.docx' || ext === '.doc') {
    const result = await parseDocx(file);
    rawText = result.text;
  } else if (ext === '.txt' || ext === '.md' || ext === '.markdown') {
    rawText = await readFileAsText(file);
  } else {
    throw new Error(`不支持的文档格式：${ext || file.type || '未知'}`);
  }

  const { text, truncated } = truncateText(rawText);

  return {
    attachment: {
      id: crypto.randomUUID(),
      name: file.name,
      type: 'document',
      mimeType: file.type || 'application/octet-stream',
      size: file.size,
      text,
      pages,
    },
    truncated,
  };
}
