import { useEffect, useMemo, useRef, useState } from 'react';
import Editor from '@monaco-editor/react';
import {
  Folder,
  FileCode,
  Play,
  Package,
  Save,
  RefreshCw,
  ChevronRight,
  ChevronDown,
  X,
  Terminal,
  Globe,
  ExternalLink,
  AlertCircle,
  Bot,
  Maximize2,
  Minimize2,
  Share2,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  listCodeProjects,
  loadCodeProject,
  saveCodeProject,
  newProjectId,
  type CodeProject,
} from '@/lib/codeProjectDb';
import {
  getWebContainer,
  mountProject,
  readFile,
  writeFile,
  subscribeRuntimeEvents,
  installPackages,
  startDevServer,
  stopDevServer,
  isDevServerRunning,
  isWebContainerSupported,
} from '@/lib/webcontainerRuntime';
import { setActiveCodeProject } from '@/lib/codeAgentTools';
import { getTemplateFiles } from '@/lib/codeAgentTools';
import { CodeAgentPanel } from '@/components/studio/CodeAgentPanel';
import { encodeSharedProject, buildProjectShareUrl } from '@/lib/share';

interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  children?: FileNode[];
}

interface CodeWorkbenchProps {
  initialProjectId?: string;
  onClose?: () => void;
}

export function CodeWorkbench({ initialProjectId, onClose }: CodeWorkbenchProps) {
  const [projects, setProjects] = useState<CodeProject[]>([]);
  const [activeProject, setActiveProject] = useState<CodeProject | null>(null);
  const [openFiles, setOpenFiles] = useState<string[]>([]);
  const [activeFile, setActiveFile] = useState<string | null>(null);
  const [fileContents, setFileContents] = useState<Record<string, string>>({});
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [status, setStatus] = useState<string>('就绪');
  const [logs, setLogs] = useState<string>('');
  const [expandedDirs, setExpandedDirs] = useState<Set<string>>(new Set(['.']));
  const [supported, setSupported] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'editor' | 'preview'>('editor');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectTemplate, setNewProjectTemplate] = useState('vanilla');
  const [devRunning, setDevRunning] = useState(false);
  const [agentPanelOpen, setAgentPanelOpen] = useState(true);
  const [fullscreen, setFullscreen] = useState(false);
  const [shareCopied, setShareCopied] = useState(false);
  const logEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setSupported(isWebContainerSupported());
    void loadProjects();
  }, []);

  useEffect(() => {
    if (!initialProjectId) return;
    void activateProject(initialProjectId);
  }, [initialProjectId]);

  useEffect(() => {
    const unsubscribe = subscribeRuntimeEvents((event) => {
      if (event.type === 'boot') {
        setStatus('正在启动 WebContainer…');
      } else if (event.type === 'ready') {
        setStatus('WebContainer 已就绪');
      } else if (event.type === 'server_ready' && event.data?.url) {
        const url = String(event.data.url);
        setPreviewUrl(url);
        setStatus(`预览服务已启动: ${url}`);
        setActiveTab('preview');
      } else if (event.type === 'shell_output' && typeof event.data?.text === 'string') {
        setLogs((prev) => prev + event.data!.text);
      } else if (event.type === 'error') {
        setStatus(`错误: ${String(event.data?.message || '未知错误')}`);
      } else if (event.type === 'file_change') {
        // File tree is rebuilt from activeProject state; external writes are reflected on next reload.
      }
    });
    return unsubscribe;
  }, [activeProject]);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  useEffect(() => {
    return () => {
      stopDevServer();
    };
  }, []);

  async function loadProjects() {
    const list = await listCodeProjects();
    setProjects(list);
  }

  async function activateProject(id: string) {
    setStatus('正在加载项目…');
    stopDevServer();
    setDevRunning(false);
    setPreviewUrl(null);
    const project = await loadCodeProject(id);
    if (!project) {
      setStatus('项目不存在');
      return;
    }
    setActiveProject(project);
    setActiveCodeProject(project.id);
    try {
      await getWebContainer();
      await mountProject(Object.fromEntries(project.files.map((f) => [f.path, f.content])));
      setStatus('项目已挂载');
      setOpenFiles([]);
      setActiveFile(null);
      setFileContents({});
    } catch (err) {
      setStatus(`挂载失败: ${err instanceof Error ? err.message : String(err)}`);
    }
  }

  async function createProject(name: string, template: string) {
    const files = getTemplateFiles(template, name);
    const project: CodeProject = {
      id: newProjectId(),
      name,
      template,
      files,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    await saveCodeProject(project);
    await loadProjects();
    await activateProject(project.id);
  }

  const fileTree = useMemo<FileNode>(() => {
    if (!activeProject) return { name: '.', path: '.', type: 'directory', children: [] };
    const root: FileNode = { name: activeProject.name, path: '.', type: 'directory', children: [] };
    for (const file of activeProject.files) {
      const parts = file.path.split('/').filter(Boolean);
      let current = root;
      for (let i = 0; i < parts.length; i++) {
        const part = parts[i];
        const isFile = i === parts.length - 1;
        const path = parts.slice(0, i + 1).join('/');
        let child = current.children?.find((c) => c.name === part);
        if (!child) {
          child = { name: part, path, type: isFile ? 'file' : 'directory', children: isFile ? undefined : [] };
          current.children = current.children || [];
          current.children.push(child);
        }
        current = child;
      }
    }
    return root;
  }, [activeProject]);

  async function openFile(path: string) {
    if (!activeProject) return;
    if (!openFiles.includes(path)) {
      setOpenFiles((prev) => [...prev, path]);
    }
    setActiveFile(path);
    const cached = fileContents[path];
    if (cached !== undefined) return;
    try {
      const content = await readFile(path);
      setFileContents((prev) => ({ ...prev, [path]: content }));
    } catch (err) {
      const projectFile = activeProject.files.find((f) => f.path === path);
      const content = projectFile?.content ?? '';
      setFileContents((prev) => ({ ...prev, [path]: content }));
    }
  }

  function closeFile(path: string) {
    setOpenFiles((prev) => prev.filter((p) => p !== path));
    if (activeFile === path) {
      const remaining = openFiles.filter((p) => p !== path);
      setActiveFile(remaining[remaining.length - 1] ?? null);
    }
  }

  async function saveActiveFile() {
    if (!activeFile || !activeProject) return;
    const content = fileContents[activeFile];
    if (content === undefined) return;
    try {
      await writeFile(activeFile, content);
      const updated = { ...activeProject };
      const existing = updated.files.find((f) => f.path === activeFile);
      if (existing) {
        existing.content = content;
      } else {
        updated.files.push({ path: activeFile, content });
      }
      updated.updated_at = new Date().toISOString();
      await saveCodeProject(updated);
      setActiveProject(updated);
      setStatus(`已保存 ${activeFile}`);
    } catch (err) {
      setStatus(`保存失败: ${err instanceof Error ? err.message : String(err)}`);
    }
  }

  async function handleInstall() {
    setStatus('正在安装依赖…');
    setLogs('');
    try {
      const result = await installPackages();
      setLogs(result.output);
      setStatus(`依赖安装完成，退出码 ${result.exitCode}`);
    } catch (err) {
      setStatus(`安装失败: ${err instanceof Error ? err.message : String(err)}`);
    }
  }

  async function handleRun() {
    if (devRunning || isDevServerRunning()) {
      setStatus('dev server 已在运行');
      return;
    }
    setStatus('正在启动 dev server…');
    setLogs('');
    setDevRunning(true);
    try {
      await startDevServer('dev', () => setDevRunning(false));
      setStatus('dev server 已启动');
    } catch (err) {
      setDevRunning(false);
      setStatus(`启动失败: ${err instanceof Error ? err.message : String(err)}`);
    }
  }

  function toggleDir(path: string) {
    setExpandedDirs((prev) => {
      const next = new Set(prev);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
  }

  function handleOpenPreview() {
    if (!previewUrl) {
      setStatus('预览尚未就绪，请先运行 npm run dev');
      return;
    }
    window.open(previewUrl, '_blank', 'noopener');
  }

  async function handleShareProject() {
    if (!activeProject) return;
    const token = encodeSharedProject(activeProject);
    if (!token) {
      setStatus('项目过大，无法生成分享链接（上限 256KB）');
      return;
    }
    const url = buildProjectShareUrl(token);
    try {
      await navigator.clipboard?.writeText(url);
      setShareCopied(true);
      setStatus(`分享链接已复制：${url}`);
      setTimeout(() => setShareCopied(false), 2000);
    } catch {
      setStatus(`分享链接：${url}`);
    }
  }

  function renderNode(node: FileNode, depth = 0): React.ReactElement {
    const isExpanded = expandedDirs.has(node.path);
    const icon = node.type === 'directory'
      ? (isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />)
      : <FileCode size={14} className="text-laap-cyan" />;

    return (
      <div key={node.path}>
        <button
          type="button"
          onClick={() => {
            if (node.type === 'directory') {
              toggleDir(node.path);
            } else {
              void openFile(node.path);
            }
          }}
          className={cn(
            'flex items-center gap-1 w-full text-left px-2 py-1 text-xs hover:bg-white/5 transition-colors',
            activeFile === node.path && 'bg-white/10'
          )}
          style={{ paddingLeft: `${8 + depth * 12}px` }}
        >
          <span className="text-laap-text-tertiary">{icon}</span>
          <span className="truncate">{node.name}</span>
        </button>
        {node.type === 'directory' && isExpanded && node.children && (
          <div>
            {node.children
              .slice()
              .sort((a, b) => (a.type === b.type ? a.name.localeCompare(b.name) : a.type === 'directory' ? -1 : 1))
              .map((child) => renderNode(child, depth + 1))}
          </div>
        )}
      </div>
    );
  }

  if (!supported) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-center text-laap-text-secondary">
        <AlertCircle size={48} className="mb-4 text-laap-rose" />
        <h3 className="text-lg font-medium text-laap-text-primary mb-2">WebContainer 需要跨域隔离</h3>
        <p className="text-sm max-w-md">
          当前页面未启用 COOP/COEP 响应头，浏览器微型电脑无法启动。请确保生产环境配置了
          Cross-Origin-Opener-Policy 和 Cross-Origin-Embedder-Policy 头。
        </p>
        {onClose && (
          <Button variant="outline" className="mt-6" onClick={onClose}>
            关闭
          </Button>
        )}
      </div>
    );
  }

  return (
    <div
      className={cn(
        'flex flex-col h-full bg-laap-bg-secondary text-laap-text-primary',
        fullscreen && 'fixed inset-0 z-50 h-screen w-screen'
      )}
    >
      {/* Toolbar */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-white/10">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-laap-text-secondary">LAAP Code Workbench</span>
          {activeProject && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-laap-cyan/10 text-laap-cyan">{activeProject.name}</span>
          )}
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            className="h-7 text-xs gap-1"
            onClick={() => setShowCreateForm((v) => !v)}
          >
            <Folder size={14} /> 新建
          </Button>
          <Button variant="ghost" size="sm" className="h-7 text-xs gap-1" onClick={() => activeProject && void activateProject(activeProject.id)}>
            <RefreshCw size={14} /> 重载
          </Button>
          <Button variant="ghost" size="sm" className="h-7 text-xs gap-1" onClick={handleInstall}>
            <Package size={14} /> npm install
          </Button>
          <Button variant="ghost" size="sm" className="h-7 text-xs gap-1" onClick={handleRun} disabled={devRunning || !activeProject}>
            <Play size={14} /> {devRunning ? '运行中…' : 'npm run dev'}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 text-xs gap-1 text-laap-cyan"
            onClick={handleOpenPreview}
            disabled={!previewUrl}
            title="在新浏览器标签页打开预览进行游玩"
          >
            <ExternalLink size={14} /> 打开预览
          </Button>
          <Button variant="ghost" size="sm" className="h-7 text-xs gap-1" onClick={saveActiveFile} disabled={!activeFile}>
            <Save size={14} /> 保存
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className={cn('h-7 text-xs gap-1', agentPanelOpen && 'bg-white/10 text-laap-cyan')}
            onClick={() => setAgentPanelOpen((v) => !v)}
          >
            <Bot size={14} /> {agentPanelOpen ? '隐藏 Agent' : 'Agent'}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 text-xs gap-1"
            onClick={handleShareProject}
            disabled={!activeProject}
            title="生成项目分享链接并复制到剪贴板"
          >
            <Share2 size={14} /> {shareCopied ? '已复制' : '分享项目'}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 w-7 p-0"
            onClick={() => setFullscreen((v) => !v)}
            title={fullscreen ? '退出全屏' : '全屏工作台'}
            aria-label={fullscreen ? '退出全屏' : '全屏工作台'}
          >
            {fullscreen ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
          </Button>
          {onClose && (
            <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={onClose}>
              <X size={14} />
            </Button>
          )}
        </div>
      </div>

      {showCreateForm && (
        <div className="px-3 py-2 border-b border-white/10 bg-white/5 flex items-center gap-2">
          <input
            type="text"
            placeholder="项目名称"
            value={newProjectName}
            onChange={(e) => setNewProjectName(e.target.value)}
            className="h-7 px-2 text-xs bg-black/30 border border-white/10 rounded-sm focus:outline-none focus:border-laap-cyan/50 text-laap-text-primary"
          />
          <select
            value={newProjectTemplate}
            onChange={(e) => setNewProjectTemplate(e.target.value)}
            className="h-7 px-2 text-xs bg-black/30 border border-white/10 rounded-sm focus:outline-none focus:border-laap-cyan/50 text-laap-text-primary"
          >
            <option value="vanilla">Vanilla</option>
            <option value="react">React</option>
            <option value="vue">Vue</option>
            <option value="game-canvas">Game Canvas</option>
            <option value="threejs-3d">Three.js 3D</option>
            <option value="phaser-game">Phaser 游戏</option>
            <option value="multi-page">多页面网站</option>
          </select>
          <Button
            size="sm"
            className="h-7 text-xs"
            onClick={() => {
              if (!newProjectName.trim()) return;
              void createProject(newProjectName.trim(), newProjectTemplate);
              setShowCreateForm(false);
              setNewProjectName('');
            }}
          >
            创建
          </Button>
          <Button variant="ghost" size="sm" className="h-7 text-xs" onClick={() => setShowCreateForm(false)}>
            取消
          </Button>
        </div>
      )}

      {!activeProject ? (
        <div className="flex-1 overflow-auto p-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {projects.length === 0 && (
              <div className="col-span-full text-sm text-laap-text-secondary">
                暂无项目。点击上方“新建”创建一个网页或游戏项目。
              </div>
            )}
            {projects.map((p) => (
              <button
                key={p.id}
                type="button"
                onClick={() => void activateProject(p.id)}
                className="text-left p-3 rounded border border-white/10 bg-white/5 hover:bg-white/10 transition-colors"
              >
                <div className="text-sm font-medium">{p.name}</div>
                <div className="text-xs text-laap-text-tertiary mt-1">{p.template}</div>
                <div className="text-[10px] text-laap-text-tertiary mt-2">{p.files.length} 个文件</div>
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="flex-1 flex min-h-0">
          {/* File tree */}
          <div className="w-48 border-r border-white/10 flex flex-col">
            <div className="px-2 py-1.5 text-[10px] uppercase tracking-wider text-laap-text-tertiary">文件</div>
            <ScrollArea className="flex-1">
              <div className="py-1">{renderNode(fileTree)}</div>
            </ScrollArea>
          </div>

          {/* Editor / Preview */}
          <div className="flex-1 flex flex-col min-w-0">
            <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'editor' | 'preview')} className="flex flex-col h-full">
              <div className="flex items-center border-b border-white/10">
                <TabsList className="bg-transparent h-8">
                  <TabsTrigger value="editor" className="text-xs gap-1">
                    <FileCode size={12} /> 编辑器
                  </TabsTrigger>
                  <TabsTrigger value="preview" className="text-xs gap-1">
                    <Globe size={12} /> 预览
                  </TabsTrigger>
                </TabsList>
                {activeFile && (
                  <div className="flex items-center ml-2">
                    {openFiles.map((path) => (
                      <button
                        key={path}
                        type="button"
                        onClick={() => setActiveFile(path)}
                        className={cn(
                          'flex items-center gap-1 px-2 py-1 text-[11px] border-r border-white/10 hover:bg-white/5',
                          activeFile === path && 'bg-white/10'
                        )}
                      >
                        <span className="truncate max-w-[120px]">{path.split('/').pop()}</span>
                        <X
                          size={10}
                          className="hover:text-laap-rose"
                          onClick={(e) => {
                            e.stopPropagation();
                            closeFile(path);
                          }}
                        />
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <TabsContent value="editor" className="flex-1 m-0 mt-0 data-[state=inactive]:hidden">
                {activeFile ? (
                  <Editor
                    height="100%"
                    language={languageForPath(activeFile)}
                    theme="vs-dark"
                    value={fileContents[activeFile] ?? ''}
                    onChange={(value) => {
                      if (value !== undefined) {
                        setFileContents((prev) => ({ ...prev, [activeFile]: value }));
                      }
                    }}
                    options={{
                      minimap: { enabled: false },
                      fontSize: 13,
                      automaticLayout: true,
                      scrollBeyondLastLine: false,
                      wordWrap: 'on',
                    }}
                  />
                ) : (
                  <div className="flex items-center justify-center h-full text-sm text-laap-text-secondary">
                    在左侧选择一个文件开始编辑
                  </div>
                )}
              </TabsContent>

              <TabsContent value="preview" className="flex-1 m-0 mt-0 data-[state=inactive]:hidden">
                {previewUrl ? (
                  <iframe
                    src={previewUrl}
                    title="Preview"
                    className="w-full h-full border-0"
                    sandbox="allow-scripts allow-same-origin allow-forms"
                  />
                ) : (
                  <div className="flex flex-col items-center justify-center h-full text-sm text-laap-text-secondary">
                    <Globe size={32} className="mb-3 text-laap-text-tertiary" />
                    <p>运行 npm run dev 后，预览将在此显示</p>
                  </div>
                )}
              </TabsContent>
            </Tabs>

            {/* Terminal / Status */}
            <div className="h-32 border-t border-white/10 bg-black/30 flex flex-col">
              <div className="flex items-center justify-between px-3 py-1 border-b border-white/10">
                <div className="flex items-center gap-1 text-[10px] text-laap-text-tertiary">
                  <Terminal size={10} /> 终端
                </div>
                <span className="text-[10px] text-laap-text-tertiary truncate max-w-[60%]">{status}</span>
              </div>
              <ScrollArea className="flex-1 p-2">
                <pre className="text-[10px] font-mono text-laap-text-secondary whitespace-pre-wrap">
                  {logs || '（无输出）'}
                  <div ref={logEndRef} />
                </pre>
              </ScrollArea>
            </div>
          </div>

          {agentPanelOpen && (
            <CodeAgentPanel projectId={activeProject?.id || 'workbench'} />
          )}
        </div>
      )}
    </div>
  );
}

function languageForPath(path: string): string {
  const ext = path.split('.').pop()?.toLowerCase();
  const map: Record<string, string> = {
    js: 'javascript',
    jsx: 'javascript',
    ts: 'typescript',
    tsx: 'typescript',
    html: 'html',
    css: 'css',
    json: 'json',
    md: 'markdown',
    vue: 'html',
  };
  return map[ext || ''] || 'plaintext';
}
