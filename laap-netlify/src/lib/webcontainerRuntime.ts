import { WebContainer, type FileSystemAPI, type WebContainerProcess, type FileSystemTree, type FileNode, type DirectoryNode } from '@webcontainer/api';

export interface ShellExecResult {
  output: string;
  exitCode: number;
}

export interface RuntimeEvent {
  type: 'boot' | 'ready' | 'shell_output' | 'server_ready' | 'error' | 'file_change';
  data?: Record<string, unknown>;
}

export type RuntimeEventListener = (event: RuntimeEvent) => void;

let instance: WebContainer | null = null;
let bootPromise: Promise<WebContainer> | null = null;
let latestPreviewUrl: string | null = null;
const listeners = new Set<RuntimeEventListener>();

function emit(type: RuntimeEvent['type'], data?: Record<string, unknown>) {
  const event: RuntimeEvent = { type, data };
  listeners.forEach((l) => {
    try {
      l(event);
    } catch {
      // ignore listener errors
    }
  });
}

export function subscribeRuntimeEvents(listener: RuntimeEventListener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export async function getWebContainer(): Promise<WebContainer> {
  if (instance) return instance;
  if (bootPromise) return bootPromise;

  emit('boot');
  bootPromise = WebContainer.boot()
    .then((wc) => {
      instance = wc;
      wc.on('server-ready', (port, url) => {
        latestPreviewUrl = url;
        emit('server_ready', { port, url });
      });
      emit('ready');
      return wc;
    })
    .catch((err) => {
      bootPromise = null;
      emit('error', { message: err instanceof Error ? err.message : String(err) });
      throw err;
    });

  return bootPromise;
}

export async function getFs(): Promise<FileSystemAPI> {
  const wc = await getWebContainer();
  return wc.fs;
}

function buildFileSystemTree(files: Record<string, string>): FileSystemTree {
  const root: FileSystemTree = {};
  for (const [path, contents] of Object.entries(files)) {
    const parts = path.split('/').filter(Boolean);
    let current = root;
    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      const isLast = i === parts.length - 1;
      if (isLast) {
        const fileNode: FileNode = { file: { contents } };
        current[part] = fileNode;
      } else {
        if (!current[part]) {
          const dirNode: DirectoryNode = { directory: {} };
          current[part] = dirNode;
        }
        const node = current[part];
        if (!('directory' in node)) {
          const dirNode: DirectoryNode = { directory: {} };
          current[part] = dirNode;
        }
        current = (current[part] as DirectoryNode).directory;
      }
    }
  }
  return root;
}

export async function mountProject(files: Record<string, string>): Promise<void> {
  const wc = await getWebContainer();
  const tree = buildFileSystemTree(files);
  await wc.mount(tree);
}

export async function readFile(path: string): Promise<string> {
  const fs = await getFs();
  return fs.readFile(path, 'utf-8');
}

export async function writeFile(path: string, contents: string): Promise<void> {
  const fs = await getFs();
  await fs.writeFile(path, contents, 'utf-8');
  emit('file_change', { path, op: 'write' });
}

export async function listFiles(dir = '.'): Promise<{ name: string; type: 'file' | 'directory' }[]> {
  const fs = await getFs();
  const entries = await fs.readdir(dir, { withFileTypes: true });
  return entries.map((e) => ({ name: e.name, type: e.isDirectory() ? 'directory' : 'file' }));
}

export async function shellExec(command: string, args: string[] = []): Promise<ShellExecResult> {
  const wc = await getWebContainer();
  const process = await wc.spawn(command, args);
  return captureProcess(process);
}

function captureProcess(process: WebContainerProcess): Promise<ShellExecResult> {
  return new Promise((resolve) => {
    const output: string[] = [];

    process.output.pipeTo(
      new WritableStream<string>({
        write(chunk) {
          output.push(chunk);
          emit('shell_output', { text: chunk });
        },
      })
    );

    process.exit.then((exitCode) => {
      resolve({ output: output.join(''), exitCode });
    });
  });
}

export async function installPackages(): Promise<ShellExecResult> {
  return shellExec('npm', ['install']);
}

export async function runScript(script: string): Promise<ShellExecResult> {
  return shellExec('npm', ['run', script]);
}

let devProcess: WebContainerProcess | null = null;

export async function startDevServer(script = 'dev', onExit?: (exitCode: number) => void): Promise<void> {
  const wc = await getWebContainer();
  const process = await wc.spawn('npm', ['run', script]);
  devProcess = process;

  void process.output.pipeTo(
    new WritableStream<string>({
      write(chunk) {
        emit('shell_output', { text: chunk });
      },
    })
  ).catch((err) => {
    emit('error', { message: `dev server output error: ${err instanceof Error ? err.message : String(err)}` });
  });

  process.exit.then((exitCode) => {
    devProcess = null;
    emit('shell_output', { text: `\n[dev server exited with code ${exitCode}]\n` });
    onExit?.(exitCode);
  });
}

export function stopDevServer(): void {
  if (devProcess) {
    try {
      devProcess.kill();
    } catch {
      // ignore
    }
    devProcess = null;
  }
}

export function isDevServerRunning(): boolean {
  return devProcess !== null;
}

export function isWebContainerSupported(): boolean {
  return typeof window !== 'undefined' && 'crossOriginIsolated' in window && (window as typeof window & { crossOriginIsolated?: boolean }).crossOriginIsolated === true;
}

/**
 * 返回最近一次 dev server 就绪时的预览地址（若尚未就绪则为 null）。
 */
export function getLatestPreviewUrl(): string | null {
  return latestPreviewUrl;
}

/**
 * 等待 dev server 就绪并返回预览地址。若已有缓存地址则立即返回。
 * 超时（默认 30s）则 reject。
 */
export function waitForServerReady(timeoutMs = 30000): Promise<{ port: number; url: string }> {
  return new Promise((resolve, reject) => {
    if (latestPreviewUrl) {
      resolve({ port: 0, url: latestPreviewUrl });
      return;
    }
    const unsubscribe = subscribeRuntimeEvents((event) => {
      if (event.type === 'server_ready' && event.data?.url) {
        unsubscribe();
        resolve({ port: Number(event.data.port) || 0, url: String(event.data.url) });
      }
    });
    const timer = setTimeout(() => {
      unsubscribe();
      reject(new Error('等待 dev server 就绪超时'));
    }, timeoutMs);
    void timer;
  });
}
