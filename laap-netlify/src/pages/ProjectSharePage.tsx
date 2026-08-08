import { useEffect, useMemo, useState } from 'react';
import { useParams, Link } from 'react-router';
import { ArrowLeft, AlertCircle, FileCode, Download, Globe, Code2 } from 'lucide-react';
import { decodeSharedProject, type SharedProject } from '@/lib/share';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export default function ProjectSharePage() {
  const { token } = useParams<{ token: string }>();
  const [shared, setShared] = useState<SharedProject | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!token) {
      setError('分享链接无效');
      return;
    }
    const decoded = decodeSharedProject(token);
    if (!decoded) {
      setError('无法解析分享内容，链接可能已损坏或项目过大。');
      return;
    }
    setShared(decoded);
  }, [token]);

  return (
    <div className="min-h-screen bg-laap-bg-primary text-laap-text-primary">
      <header className="h-16 border-b border-laap-border bg-laap-bg-primary/90 backdrop-blur-md flex items-center justify-between px-4 sm:px-6">
        <Link
          to="/"
          className="flex items-center gap-2 text-sm text-laap-text-secondary hover:text-white transition-colors"
        >
          <ArrowLeft size={16} />
          返回 LAAP
        </Link>
        <div className="font-display text-white tracking-wide">LAAP Studio</div>
        <Link
          to="/studio"
          className="text-sm text-laap-gold hover:text-laap-gold-light transition-colors"
        >
          打开工作台
        </Link>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8">
        {error ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <AlertCircle size={48} className="text-laap-rose mb-4" />
            <h1 className="text-xl text-white mb-2">项目分享无法打开</h1>
            <p className="text-sm text-laap-text-secondary">{error}</p>
          </div>
        ) : !shared ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="w-10 h-10 border-2 border-laap-gold border-t-transparent rounded-full animate-spin mb-4" />
            <p className="text-sm text-laap-text-secondary">正在加载项目…</p>
          </div>
        ) : (
          <ProjectPreview shared={shared} />
        )}
      </main>
    </div>
  );
}

function ProjectPreview({ shared }: { shared: SharedProject }) {
  const [activeFilePath, setActiveFilePath] = useState<string | null>(null);
  const [view, setView] = useState<'preview' | 'code'>('preview');

  const fileMap = useMemo(() => {
    const map = new Map<string, string>();
    for (const f of shared.files) {
      map.set(f.path, f.content);
    }
    return map;
  }, [shared]);

  const indexHtml = useMemo(() => {
    const candidates = ['index.html', 'src/index.html', 'public/index.html'];
    for (const c of candidates) {
      if (fileMap.has(c)) return { path: c, content: fileMap.get(c)! };
    }
    const anyHtml = shared.files.find((f) => f.path.endsWith('.html'));
    return anyHtml ? { path: anyHtml.path, content: anyHtml.content } : null;
  }, [fileMap, shared.files]);

  const srcDoc = useMemo(() => {
    if (!indexHtml) return null;
    return inlineAssets(indexHtml.content, fileMap);
  }, [indexHtml, fileMap]);

  useEffect(() => {
    if (!activeFilePath && shared.files.length > 0) {
      const first = shared.files[0]?.path;
      if (first) setActiveFilePath(first);
    }
  }, [activeFilePath, shared.files]);

  const activeFileContent = activeFilePath ? fileMap.get(activeFilePath) ?? '' : '';

  function downloadFile(path: string) {
    const content = fileMap.get(path);
    if (content === undefined) return;
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = path.split('/').pop() || 'file.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  return (
    <>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-display text-white mb-1">{shared.name}</h1>
          <p className="text-xs text-laap-text-tertiary">
            模板 {shared.template} · {shared.files.length} 个文件 · 分享于 {new Date(shared.exportedAt).toLocaleString('zh-CN')}
          </p>
        </div>
        <div className="flex items-center gap-1 p-1 bg-laap-bg-secondary/40 border border-laap-border rounded-sm">
          <button
            type="button"
            onClick={() => setView('preview')}
            className={cn(
              'flex items-center gap-1.5 px-3 py-1 text-xs rounded-sm transition-colors',
              view === 'preview' ? 'bg-laap-gold/15 text-laap-gold' : 'text-laap-text-secondary hover:text-white'
            )}
          >
            <Globe size={12} /> 预览
          </button>
          <button
            type="button"
            onClick={() => setView('code')}
            className={cn(
              'flex items-center gap-1.5 px-3 py-1 text-xs rounded-sm transition-colors',
              view === 'code' ? 'bg-laap-gold/15 text-laap-gold' : 'text-laap-text-secondary hover:text-white'
            )}
          >
            <Code2 size={12} /> 源代码
          </button>
        </div>
      </div>

      {view === 'preview' ? (
        <div className="grid grid-cols-1 lg:grid-cols-[200px_1fr] gap-4">
          <aside className="lg:border-r lg:border-laap-border lg:pr-3">
            <div className="text-[10px] uppercase tracking-wider text-laap-text-tertiary mb-2">文件</div>
            <ScrollArea className="h-[60vh] lg:h-[70vh]">
              <div className="space-y-0.5">
                {shared.files.map((f) => (
                  <button
                    key={f.path}
                    type="button"
                    onClick={() => {
                      setActiveFilePath(f.path);
                      setView('code');
                    }}
                    className="flex items-center gap-1.5 w-full text-left px-2 py-1 text-xs hover:bg-white/5 rounded-sm transition-colors"
                  >
                    <FileCode size={12} className="text-laap-cyan flex-shrink-0" />
                    <span className="truncate">{f.path}</span>
                  </button>
                ))}
              </div>
            </ScrollArea>
          </aside>

          <div className="border border-laap-border rounded-sm overflow-hidden bg-white">
            {srcDoc ? (
              <iframe
                title={shared.name}
                srcDoc={srcDoc}
                className="w-full h-[60vh] lg:h-[70vh] border-0"
                sandbox="allow-scripts allow-forms allow-modals allow-popups"
              />
            ) : (
              <div className="w-full h-[60vh] lg:h-[70vh] flex flex-col items-center justify-center text-laap-text-secondary bg-laap-bg-secondary">
                <AlertCircle size={36} className="mb-3 text-laap-text-tertiary" />
                <p className="text-sm">未找到 index.html，无法生成预览。</p>
                <Button variant="outline" className="mt-4" onClick={() => setView('code')}>
                  查看源代码
                </Button>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-[220px_1fr] gap-4">
          <aside className="lg:border-r lg:border-laap-border lg:pr-3">
            <div className="text-[10px] uppercase tracking-wider text-laap-text-tertiary mb-2">文件</div>
            <ScrollArea className="h-[60vh] lg:h-[70vh]">
              <div className="space-y-0.5">
                {shared.files.map((f) => (
                  <button
                    key={f.path}
                    type="button"
                    onClick={() => setActiveFilePath(f.path)}
                    className={cn(
                      'flex items-center gap-1.5 w-full text-left px-2 py-1 text-xs hover:bg-white/5 rounded-sm transition-colors',
                      activeFilePath === f.path && 'bg-white/10 text-white'
                    )}
                  >
                    <FileCode size={12} className="text-laap-cyan flex-shrink-0" />
                    <span className="truncate">{f.path}</span>
                  </button>
                ))}
              </div>
            </ScrollArea>
          </aside>

          <div className="border border-laap-border rounded-sm overflow-hidden bg-laap-bg-secondary/40 flex flex-col">
            <div className="flex items-center justify-between px-3 py-2 border-b border-laap-border bg-laap-bg-tertiary/40">
              <span className="text-xs font-mono text-laap-text-secondary">{activeFilePath ?? '—'}</span>
              {activeFilePath && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 text-xs gap-1"
                  onClick={() => downloadFile(activeFilePath)}
                >
                  <Download size={12} /> 下载
                </Button>
              )}
            </div>
            <ScrollArea className="flex-1 h-[58vh] lg:h-[68vh]">
              <pre className="text-xs font-mono text-laap-text-primary whitespace-pre p-3 leading-relaxed">
                {activeFileContent || '（空文件）'}
              </pre>
            </ScrollArea>
          </div>
        </div>
      )}
    </>
  );
}

/**
 * Inline local CSS and JS references into a single HTML document so it can be
 * rendered via iframe srcDoc without a server. Only relative, same-folder
 * references are inlined; cross-origin URLs are preserved as-is.
 */
function inlineAssets(html: string, files: Map<string, string>): string {
  let result = html;

  // Inline <link rel="stylesheet" href="X">
  result = result.replace(
    /<link[^>]*rel=["']stylesheet["'][^>]*href=["']([^"']+)["'][^>]*>/gi,
    (match, href: string) => {
      const local = resolveLocalPath(href);
      if (!local) return match;
      const content = files.get(local);
      if (content === undefined) return match;
      return `<style data-src="${escapeAttr(href)}">\n${content}\n</style>`;
    }
  );

  // Inline <script src="X"></script>
  result = result.replace(
    /<script[^>]*src=["']([^"']+)["'][^>]*>\s*<\/script>/gi,
    (match, src: string) => {
      const local = resolveLocalPath(src);
      if (!local) return match;
      const content = files.get(local);
      if (content === undefined) return match;
      return `<script data-src="${escapeAttr(src)}">\n${content}\n</script>`;
    }
  );

  return result;
}

function resolveLocalPath(href: string): string | null {
  if (!href) return null;
  if (/^https?:\/\//i.test(href)) return null;
  if (/^\/\//.test(href)) return null;
  if (/^data:/i.test(href)) return null;
  // strip leading ./ and /
  return href.replace(/^\.\//, '').replace(/^\//, '');
}

function escapeAttr(s: string): string {
  return s.replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
