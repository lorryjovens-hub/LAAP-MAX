import type { Tool } from '@/lib/localLlm';
import {
  readFile,
  writeFile,
  listFiles,
  shellExec,
  installPackages,
  runScript,
  startDevServer,
  isDevServerRunning,
  subscribeRuntimeEvents,
  getLatestPreviewUrl,
  waitForServerReady,
} from '@/lib/webcontainerRuntime';
import { loadCodeProject, saveCodeProject, newProjectId, type CodeProjectFile } from '@/lib/codeProjectDb';
import { cognitiveEngine } from '@/lib/cognitiveEngine';
import {
  perceiveProgrammingTask,
  learnFromCodeExecution,
  rememberCodeArtifact,
  buildCodeContext,
  writeCodeArtifact,
} from '@/lib/cognitiveCodeAgent';

let activeProjectId: string | null = null;
const projectListeners = new Set<(id: string | null) => void>();

export function setActiveCodeProject(id: string | null) {
  activeProjectId = id;
  projectListeners.forEach((l) => {
    try {
      l(id);
    } catch {
      // ignore
    }
  });
}

export function getActiveCodeProject(): string | null {
  return activeProjectId;
}

export function onActiveCodeProjectChange(listener: (id: string | null) => void): () => void {
  projectListeners.add(listener);
  return () => projectListeners.delete(listener);
}

export function buildCodeAgentTools(userId?: string): Tool[] {
  return [
    {
      name: 'code_file_read',
      description: 'Read the contents of a file in the active code project.',
      parameters: {
        type: 'object',
        properties: {
          path: { type: 'string', description: 'Relative file path in the project' },
        },
        required: ['path'],
      },
      execute: async (args) => {
        const path = String(args.path || '').trim();
        if (!path) return '路径不能为空';
        try {
          const content = await readFile(path);
          return content;
        } catch (err) {
          return `读取失败：${err instanceof Error ? err.message : String(err)}`;
        }
      },
    },
    {
      name: 'code_file_write',
      description: 'Write or overwrite a file in the active code project.',
      readonly: false,
      parameters: {
        type: 'object',
        properties: {
          path: { type: 'string', description: 'Relative file path in the project' },
          content: { type: 'string', description: 'Full file contents' },
        },
        required: ['path', 'content'],
      },
      execute: async (args) => {
        const path = String(args.path || '').trim();
        const content = String(args.content ?? '');
        if (!path) return '路径不能为空';
        try {
          await writeFile(path, content);
          await persistActiveFile(path, content);
          // ── LAAP 认知层：写入代码即一次行动，并沉淀可复用知识记忆 ──
          if (userId) {
            void writeCodeArtifact(userId, path, content);
          }
          return `已写入 ${path}`;
        } catch (err) {
          return `写入失败：${err instanceof Error ? err.message : String(err)}`;
        }
      },
    },
    {
      name: 'code_file_list',
      description: 'List files and directories at a path in the active code project.',
      parameters: {
        type: 'object',
        properties: {
          path: { type: 'string', description: 'Relative directory path (default ".")' },
        },
      },
      execute: async (args) => {
        const dir = String(args.path || '.').trim() || '.';
        try {
          const entries = await listFiles(dir);
          if (entries.length === 0) return '（空目录）';
          return entries.map((e) => `${e.type === 'directory' ? '[DIR]' : '[FILE]'} ${e.name}`).join('\n');
        } catch (err) {
          return `列出失败：${err instanceof Error ? err.message : String(err)}`;
        }
      },
    },
    {
      name: 'code_shell_exec',
      description: 'Execute a shell command inside the WebContainer runtime.',
      readonly: false,
      parameters: {
        type: 'object',
        properties: {
          command: { type: 'string', description: 'Command to run (e.g. "ls", "cat")' },
          args: { type: 'array', items: { type: 'string' }, description: 'Command arguments' },
        },
        required: ['command'],
      },
      execute: async (args) => {
        const command = String(args.command || '').trim();
        const rawArgs = Array.isArray(args.args) ? args.args.map(String) : [];
        if (!command) return '命令不能为空';
        try {
          const result = await shellExec(command, rawArgs);
          // ── LAAP 认知层：执行结果作为学习信号，失败触发 RSI 反思 ──
          await learnFromCodeExecution({
            command: [command, ...rawArgs].join(' '),
            exitCode: result.exitCode,
            output: result.output,
          });
          return `退出码：${result.exitCode}\n${result.output}`;
        } catch (err) {
          return `执行失败：${err instanceof Error ? err.message : String(err)}`;
        }
      },
    },
    {
      name: 'code_npm_install',
      description: 'Run npm install in the active code project.',
      readonly: false,
      parameters: {
        type: 'object',
        properties: {},
      },
      execute: async () => {
        try {
          const result = await installPackages();
          await learnFromCodeExecution({
            command: 'npm install',
            exitCode: result.exitCode,
            output: result.output,
          });
          return `退出码：${result.exitCode}\n${result.output}`;
        } catch (err) {
          return `安装失败：${err instanceof Error ? err.message : String(err)}`;
        }
      },
    },
    {
      name: 'code_npm_run',
      description: 'Run an npm script in the active code project.',
      readonly: false,
      parameters: {
        type: 'object',
        properties: {
          script: { type: 'string', description: 'Script name from package.json' },
        },
        required: ['script'],
      },
      execute: async (args) => {
        const script = String(args.script || '').trim();
        if (!script) return '脚本名不能为空';
        try {
          const result = await runScript(script);
          await learnFromCodeExecution({
            command: `npm run ${script}`,
            exitCode: result.exitCode,
            output: result.output,
          });
          return `退出码：${result.exitCode}\n${result.output}`;
        } catch (err) {
          return `运行失败：${err instanceof Error ? err.message : String(err)}`;
        }
      },
    },
    {
      name: 'code_preview_url',
      description: 'Return the current preview URL once the dev server is ready. Use after code_npm_run.',
      parameters: {
        type: 'object',
        properties: {},
      },
      execute: async () => {
        return '预览状态由 LAAP Studio 自动监听，服务启动后会在界面中显示 URL。';
      },
    },
    {
      name: 'code_cognitive_context',
      description:
        'Return the lifeform\'s live cognitive state plus recalled coding memories relevant to the current task. Use at the start of a substantial coding task to ground decisions in past patterns and current consciousness.',
      parameters: {
        type: 'object',
        properties: {
          task: { type: 'string', description: 'The current coding task or goal' },
        },
        required: ['task'],
      },
      execute: async (args) => {
        const task = String(args.task || '').trim() || '当前编程任务';
        if (!userId) {
          return cognitiveEngine.toPromptBlock();
        }
        try {
          return await buildCodeContext(userId, task);
        } catch {
          return cognitiveEngine.toPromptBlock();
        }
      },
    },
    {
      name: 'code_init_project',
      description: 'Initialize a new code project with a template and switch to it. Templates: vanilla, react, vue, game-canvas, threejs-3d, phaser-game, multi-page.',
      readonly: false,
      parameters: {
        type: 'object',
        properties: {
          name: { type: 'string', description: 'Project name' },
          template: {
            type: 'string',
            enum: ['vanilla', 'react', 'vue', 'game-canvas', 'threejs-3d', 'phaser-game', 'multi-page'],
            description: 'Project template',
          },
        },
        required: ['name', 'template'],
      },
      execute: async (args) => {
        const name = String(args.name || '').trim();
        const template = String(args.template || 'vanilla');
        if (!name) return '项目名称不能为空';
        // ── LAAP 认知层：进入编程任务，转移注意力并感知意图 ──
        perceiveProgrammingTask(`创建 ${template} 项目 ${name}`);
        const files = getTemplateFiles(template, name);
        const project = {
          id: newProjectId(),
          name,
          template,
          files,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };
        await saveCodeProject(project);
        setActiveCodeProject(project.id);
        if (userId) {
          void rememberCodeArtifact(userId, `创建了 ${template} 项目「${name}」，ID: ${project.id}。`, 'task', 6);
        }
        return `已创建项目 "${name}"（${template}），ID: ${project.id}。可调用 code_run_project 自动安装依赖并启动预览。`;
      },
    },
    {
      name: 'code_run_project',
      description:
        'Automatically install dependencies and start the dev server for the active project. Call this after writing all code files so the user can see the running app in the preview pane.',
      readonly: false,
      parameters: {
        type: 'object',
        properties: {
          wait_for_install: {
            type: 'boolean',
            description: 'Whether to wait for npm install to complete before starting dev server (default true)',
          },
        },
      },
      execute: async (args) => {
        const waitForInstall = args.wait_for_install !== false;
        if (isDevServerRunning()) {
          const cachedUrl = getLatestPreviewUrl();
          if (cachedUrl) {
            openPreviewInNewTab(cachedUrl);
            return `dev server 已在运行，已自动打开内置浏览器预览：${cachedUrl}`;
          }
          return 'dev server 已在运行，预览中应已可见。';
        }
        const installLog: string[] = [];
        try {
          // 订阅运行时事件，捕获安装输出
          const unsubscribe = subscribeRuntimeEvents((event) => {
            if (event.type === 'shell_output' && typeof event.data?.text === 'string') {
              installLog.push(event.data.text);
            }
          });

          if (waitForInstall) {
            const installResult = await installPackages();
            if (installResult.exitCode !== 0) {
              unsubscribe();
              return `依赖安装失败（退出码 ${installResult.exitCode}）：\n${installResult.output.slice(-2000)}`;
            }
          }

          await startDevServer('dev');

          // 等待 dev server 就绪，然后自动打开内置浏览器预览
          let previewUrl: string | null = null;
          try {
            const { url } = await waitForServerReady(30000);
            previewUrl = url;
          } catch (e) {
            previewUrl = getLatestPreviewUrl();
          }
          if (previewUrl) {
            openPreviewInNewTab(previewUrl);
          }
          unsubscribe();

          return `已自动安装依赖并启动 dev server${previewUrl ? `，并打开内置浏览器预览：${previewUrl}` : '（预览将在就绪后于“预览”标签页显示）'}。\n\n安装日志（最后 1000 字符）：\n${installLog.join('').slice(-1000)}`;
        } catch (err) {
          return `启动失败：${err instanceof Error ? err.message : String(err)}`;
        }
      },
    },
  ];
}

/**
 * 在浏览器新标签页中打开预览地址，供用户直接查看并游玩。
 */
function openPreviewInNewTab(url: string) {
  try {
    if (typeof window !== 'undefined') {
      window.open(url, '_blank', 'noopener');
    }
  } catch {
    // 忽略弹窗拦截等错误
  }
}

async function persistActiveFile(path: string, content: string) {
  const id = activeProjectId;
  if (!id) return;
  const project = await loadCodeProject(id);
  if (!project) return;
  const existing = project.files.find((f) => f.path === path);
  if (existing) {
    existing.content = content;
  } else {
    project.files.push({ path, content });
  }
  project.updated_at = new Date().toISOString();
  await saveCodeProject(project);
}

export function getTemplateFiles(template: string, name: string): CodeProjectFile[] {
  const common = [
    { path: 'README.md', content: `# ${name}\n\nGenerated by LAAP Code Agent.\n` },
  ];

  switch (template) {
    case 'react':
      return [
        ...common,
        {
          path: 'package.json',
          content: JSON.stringify(
            {
              name: name.toLowerCase().replace(/\s+/g, '-'),
              private: true,
              version: '0.0.0',
              type: 'module',
              scripts: { dev: 'vite', build: 'vite build', preview: 'vite preview' },
              dependencies: { react: '^19.0.0', 'react-dom': '^19.0.0' },
              devDependencies: { vite: '^6.0.0', '@vitejs/plugin-react': '^4.3.0' },
            },
            null,
            2
          ),
        },
        {
          path: 'index.html',
          content: `<!DOCTYPE html>\n<html lang="en">\n<head>\n  <meta charset="UTF-8" />\n  <meta name="viewport" content="width=device-width, initial-scale=1.0" />\n  <title>${name}</title>\n</head>\n<body>\n  <div id="root"></div>\n  <script type="module" src="/src/main.jsx"></script>\n</body>\n</html>\n`,
        },
        {
          path: 'vite.config.js',
          content: `import { defineConfig } from 'vite';\nimport react from '@vitejs/plugin-react';\n\nexport default defineConfig({\n  plugins: [react()],\n  server: { port: 3000 },\n});\n`,
        },
        {
          path: 'src/main.jsx',
          content: `import React from 'react';\nimport ReactDOM from 'react-dom/client';\nimport App from './App';\nimport './index.css';\n\nReactDOM.createRoot(document.getElementById('root')).render(\n  <React.StrictMode>\n    <App />\n  </React.StrictMode>\n);\n`,
        },
        {
          path: 'src/App.jsx',
          content: `import { useState } from 'react';\n\nexport default function App() {\n  const [count, setCount] = useState(0);\n  return (\n    <div style={{ padding: 24, fontFamily: 'sans-serif' }}>\n      <h1>${name}</h1>\n      <button onClick={() => setCount((c) => c + 1)}>count is {count}</button>\n    </div>\n  );\n}\n`,
        },
        {
          path: 'src/index.css',
          content: `body { margin: 0; background: #0b0b10; color: #e2e2e8; }\n`,
        },
      ];
    case 'vue':
      return [
        ...common,
        {
          path: 'package.json',
          content: JSON.stringify(
            {
              name: name.toLowerCase().replace(/\s+/g, '-'),
              private: true,
              version: '0.0.0',
              type: 'module',
              scripts: { dev: 'vite', build: 'vite build', preview: 'vite preview' },
              dependencies: { vue: '^3.5.0' },
              devDependencies: { vite: '^6.0.0', '@vitejs/plugin-vue': '^5.2.0' },
            },
            null,
            2
          ),
        },
        {
          path: 'index.html',
          content: `<!DOCTYPE html>\n<html lang="en">\n<head>\n  <meta charset="UTF-8" />\n  <meta name="viewport" content="width=device-width, initial-scale=1.0" />\n  <title>${name}</title>\n</head>\n<body>\n  <div id="app"></div>\n  <script type="module" src="/src/main.js"></script>\n</body>\n</html>\n`,
        },
        {
          path: 'vite.config.js',
          content: `import { defineConfig } from 'vite';\nimport vue from '@vitejs/plugin-vue';\n\nexport default defineConfig({\n  plugins: [vue()],\n  server: { port: 3000 },\n});\n`,
        },
        {
          path: 'src/main.js',
          content: `import { createApp } from 'vue';\nimport App from './App.vue';\nimport './style.css';\n\ncreateApp(App).mount('#app');\n`,
        },
        {
          path: 'src/App.vue',
          content: `<script setup>\nimport { ref } from 'vue';\nconst count = ref(0);\n</script>\n\n<template>\n  <div class="app">\n    <h1>${name}</h1>\n    <button @click="count++">count is {{ count }}</button>\n  </div>\n</template>\n\n<style>\n.app { padding: 24px; font-family: sans-serif; background: #0b0b10; color: #e2e2e8; min-height: 100vh; }\n</style>\n`,
        },
        {
          path: 'src/style.css',
          content: `body { margin: 0; }\n`,
        },
      ];
    case 'game-canvas':
      return [
        ...common,
        {
          path: 'package.json',
          content: JSON.stringify(
            {
              name: name.toLowerCase().replace(/\s+/g, '-'),
              private: true,
              version: '0.0.0',
              type: 'module',
              scripts: { dev: 'vite', build: 'vite build', preview: 'vite preview' },
              devDependencies: { vite: '^6.0.0' },
            },
            null,
            2
          ),
        },
        {
          path: 'index.html',
          content: `<!DOCTYPE html>\n<html lang="en">\n<head>\n  <meta charset="UTF-8" />\n  <meta name="viewport" content="width=device-width, initial-scale=1.0" />\n  <title>${name}</title>\n</head>\n<body>\n  <canvas id="game"></canvas>\n  <script type="module" src="/src/main.js"></script>\n</body>\n</html>\n`,
        },
        {
          path: 'vite.config.js',
          content: `import { defineConfig } from 'vite';\n\nexport default defineConfig({\n  server: { port: 3000 },\n});\n`,
        },
        {
          path: 'src/main.js',
          content: `const canvas = document.getElementById('game');\nconst ctx = canvas.getContext('2d');\ncanvas.width = window.innerWidth;\ncanvas.height = window.innerHeight;\n\nfunction draw() {\n  ctx.fillStyle = '#0b0b10';\n  ctx.fillRect(0, 0, canvas.width, canvas.height);\n  ctx.fillStyle = '#00d4aa';\n  ctx.beginPath();\n  ctx.arc(canvas.width / 2, canvas.height / 2, 40, 0, Math.PI * 2);\n  ctx.fill();\n  requestAnimationFrame(draw);\n}\n\ndraw();\n`,
        },
      ];
    case 'threejs-3d':
      return [
        ...common,
        {
          path: 'package.json',
          content: JSON.stringify(
            {
              name: name.toLowerCase().replace(/\s+/g, '-'),
              private: true,
              version: '0.0.0',
              type: 'module',
              scripts: { dev: 'vite', build: 'vite build', preview: 'vite preview' },
              dependencies: { three: '^0.170.0' },
              devDependencies: { vite: '^6.0.0' },
            },
            null,
            2
          ),
        },
        {
          path: 'index.html',
          content: `<!DOCTYPE html>\n<html lang="en">\n<head>\n  <meta charset="UTF-8" />\n  <meta name="viewport" content="width=device-width, initial-scale=1.0" />\n  <title>${name}</title>\n  <style>body{margin:0;overflow:hidden;background:#000;}</style>\n</head>\n<body>\n  <script type="module" src="/src/main.js"></script>\n</body>\n</html>\n`,
        },
        {
          path: 'vite.config.js',
          content: `import { defineConfig } from 'vite';\n\nexport default defineConfig({\n  server: { port: 3000 },\n});\n`,
        },
        {
          path: 'src/main.js',
          content: `import * as THREE from 'three';\n\nconst scene = new THREE.Scene();\nscene.background = new THREE.Color(0x0b0b10);\n\nconst camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);\ncamera.position.z = 5;\n\nconst renderer = new THREE.WebGLRenderer({ antialias: true });\nrenderer.setPixelRatio(window.devicePixelRatio);\nrenderer.setSize(window.innerWidth, window.innerHeight);\ndocument.body.appendChild(renderer.domElement);\n\n// 灯光\nconst ambient = new THREE.AmbientLight(0xffffff, 0.4);\nscene.add(ambient);\nconst dirLight = new THREE.DirectionalLight(0xffffff, 1.0);\ndirLight.position.set(5, 5, 5);\nscene.add(dirLight);\n\n// 一个旋转的彩色立方体\nconst geometry = new THREE.BoxGeometry(1.5, 1.5, 1.5);\nconst material = new THREE.MeshStandardMaterial({\n  color: 0x00d4aa,\n  metalness: 0.3,\n  roughness: 0.4,\n});\nconst cube = new THREE.Mesh(geometry, material);\nscene.add(cube);\n\n// 添加坐标轴辅助\nscene.add(new THREE.AxesHelper(2));\n\nwindow.addEventListener('resize', () => {\n  camera.aspect = window.innerWidth / window.innerHeight;\n  camera.updateProjectionMatrix();\n  renderer.setSize(window.innerWidth, window.innerHeight);\n});\n\nfunction animate() {\n  requestAnimationFrame(animate);\n  cube.rotation.x += 0.01;\n  cube.rotation.y += 0.012;\n  renderer.render(scene, camera);\n}\nanimate();\n`,
        },
      ];
    case 'phaser-game':
      return [
        ...common,
        {
          path: 'package.json',
          content: JSON.stringify(
            {
              name: name.toLowerCase().replace(/\s+/g, '-'),
              private: true,
              version: '0.0.0',
              type: 'module',
              scripts: { dev: 'vite', build: 'vite build', preview: 'vite preview' },
              dependencies: { phaser: '^3.87.0' },
              devDependencies: { vite: '^6.0.0' },
            },
            null,
            2
          ),
        },
        {
          path: 'index.html',
          content: `<!DOCTYPE html>\n<html lang="en">\n<head>\n  <meta charset="UTF-8" />\n  <meta name="viewport" content="width=device-width, initial-scale=1.0" />\n  <title>${name}</title>\n  <style>body{margin:0;background:#000;}</style>\n</head>\n<body>\n  <script type="module" src="/src/main.js"></script>\n</body>\n</html>\n`,
        },
        {
          path: 'vite.config.js',
          content: `import { defineConfig } from 'vite';\n\nexport default defineConfig({\n  server: { port: 3000 },\n});\n`,
        },
        {
          path: 'src/main.js',
          content: `import Phaser from 'phaser';\n\nclass MainScene extends Phaser.Scene {\n  constructor() { super('main'); }\n\n  create() {\n    this.add.text(400, 100, '${name}', { fontSize: '32px', color: '#00d4aa' }).setOrigin(0.5);\n    this.add.text(400, 160, '点击屏幕移动方块', { fontSize: '16px', color: '#aaa' }).setOrigin(0.5);\n\n    this.player = this.add.rectangle(400, 300, 40, 40, 0x00d4aa);\n    this.target = new Phaser.Math.Vector2(400, 300);\n\n    this.input.on('pointerdown', (pointer) => {\n      this.target.set(pointer.x, pointer.y);\n    });\n  }\n\n  update() {\n    if (!this.player) return;\n    const speed = 4;\n    const dx = this.target.x - this.player.x;\n    const dy = this.target.y - this.player.y;\n    const dist = Math.hypot(dx, dy);\n    if (dist > 1) {\n      this.player.x += (dx / dist) * speed;\n      this.player.y += (dy / dist) * speed;\n    }\n  }\n}\n\nnew Phaser.Game({\n  type: Phaser.AUTO,\n  width: 800,\n  height: 600,\n  backgroundColor: '#0b0b10',\n  parent: document.body,\n  scene: [MainScene],\n});\n`,
        },
      ];
    case 'multi-page':
      return [
        ...common,
        {
          path: 'package.json',
          content: JSON.stringify(
            {
              name: name.toLowerCase().replace(/\s+/g, '-'),
              private: true,
              version: '0.0.0',
              type: 'module',
              scripts: { dev: 'vite', build: 'vite build', preview: 'vite preview' },
              devDependencies: { vite: '^6.0.0' },
            },
            null,
            2
          ),
        },
        {
          path: 'index.html',
          content: `<!DOCTYPE html>\n<html lang="en">\n<head>\n  <meta charset="UTF-8" />\n  <meta name="viewport" content="width=device-width, initial-scale=1.0" />\n  <title>${name} - 首页</title>\n  <link rel="stylesheet" href="/src/style.css" />\n</head>\n<body>\n  <nav class="nav">\n    <span class="brand">${name}</span>\n    <div class="links">\n      <a href="/">首页</a>\n      <a href="/about.html">关于</a>\n      <a href="/contact.html">联系</a>\n    </div>\n  </nav>\n  <main class="container">\n    <h1>欢迎来到 ${name}</h1>\n    <p>这是一个多页面网站模板。可直接编辑 about.html / contact.html / 404.html。</p>\n    <a class="btn" href="/about.html">了解更多 →</a>\n  </main>\n</body>\n</html>\n`,
        },
        {
          path: 'about.html',
          content: `<!DOCTYPE html>\n<html lang="en">\n<head>\n  <meta charset="UTF-8" />\n  <meta name="viewport" content="width=device-width, initial-scale=1.0" />\n  <title>关于 - ${name}</title>\n  <link rel="stylesheet" href="/src/style.css" />\n</head>\n<body>\n  <nav class="nav">\n    <span class="brand">${name}</span>\n    <div class="links">\n      <a href="/">首页</a>\n      <a href="/about.html">关于</a>\n      <a href="/contact.html">联系</a>\n    </div>\n  </nav>\n  <main class="container">\n    <h1>关于我们</h1>\n    <p>${name} 是由 LAAP Studio 创建的多页面网站。</p>\n  </main>\n</body>\n</html>\n`,
        },
        {
          path: 'contact.html',
          content: `<!DOCTYPE html>\n<html lang="en">\n<head>\n  <meta charset="UTF-8" />\n  <meta name="viewport" content="width=device-width, initial-scale=1.0" />\n  <title>联系 - ${name}</title>\n  <link rel="stylesheet" href="/src/style.css" />\n</head>\n<body>\n  <nav class="nav">\n    <span class="brand">${name}</span>\n    <div class="links">\n      <a href="/">首页</a>\n      <a href="/about.html">关于</a>\n      <a href="/contact.html">联系</a>\n    </div>\n  </nav>\n  <main class="container">\n    <h1>联系我们</h1>\n    <form class="form">\n      <input type="text" placeholder="你的名字" required />\n      <input type="email" placeholder="你的邮箱" required />\n      <textarea placeholder="留言内容" required></textarea>\n      <button type="submit">发送</button>\n    </form>\n  </main>\n</body>\n</html>\n`,
        },
        {
          path: '404.html',
          content: `<!DOCTYPE html>\n<html lang="en">\n<head>\n  <meta charset="UTF-8" />\n  <title>404 - ${name}</title>\n  <link rel="stylesheet" href="/src/style.css" />\n</head>\n<body>\n  <main class="container center">\n    <h1>404</h1>\n    <p>页面不存在</p>\n    <a class="btn" href="/">返回首页</a>\n  </main>\n</body>\n</html>\n`,
        },
        {
          path: 'vite.config.js',
          content: `import { defineConfig } from 'vite';\nimport { resolve } from 'path';\n\nexport default defineConfig({\n  build: {\n    rollupOptions: {\n      input: {\n        main: resolve(__dirname, 'index.html'),\n        about: resolve(__dirname, 'about.html'),\n        contact: resolve(__dirname, 'contact.html'),\n        notFound: resolve(__dirname, '404.html'),\n      },\n    },\n  },\n  server: { port: 3000 },\n  appType: 'mpa',\n});\n`,
        },
        {
          path: 'src/style.css',
          content: `* { box-sizing: border-box; }\nbody { margin: 0; background: #0b0b10; color: #e2e2e8; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }\n.nav { display: flex; justify-content: space-between; align-items: center; padding: 16px 24px; border-bottom: 1px solid #1f1f2e; background: rgba(11,11,16,0.9); position: sticky; top: 0; }\n.brand { color: #00d4aa; font-weight: 600; }\n.links a { color: #a0a0b0; margin-left: 16px; text-decoration: none; transition: color 0.2s; }\n.links a:hover { color: #fff; }\n.container { max-width: 800px; margin: 0 auto; padding: 48px 24px; }\n.container.center { text-align: center; }\n.btn { display: inline-block; padding: 10px 20px; background: #00d4aa; color: #0b0b10; border-radius: 4px; text-decoration: none; font-weight: 600; }\n.form { display: flex; flex-direction: column; gap: 12px; max-width: 400px; }\n.form input, .form textarea { padding: 10px 12px; background: #1a1a24; border: 1px solid #2a2a38; color: #fff; border-radius: 4px; font-size: 14px; }\n.form button { padding: 10px; background: #00d4aa; color: #0b0b10; border: none; border-radius: 4px; font-weight: 600; cursor: pointer; }\n`,
        },
      ];
    default:
      return [
        ...common,
        {
          path: 'package.json',
          content: JSON.stringify(
            {
              name: name.toLowerCase().replace(/\s+/g, '-'),
              private: true,
              version: '0.0.0',
              type: 'module',
              scripts: { dev: 'vite', build: 'vite build', preview: 'vite preview' },
              devDependencies: { vite: '^6.0.0' },
            },
            null,
            2
          ),
        },
        {
          path: 'index.html',
          content: `<!DOCTYPE html>\n<html lang="en">\n<head>\n  <meta charset="UTF-8" />\n  <meta name="viewport" content="width=device-width, initial-scale=1.0" />\n  <title>${name}</title>\n</head>\n<body>\n  <h1>${name}</h1>\n  <p>Edit <code>src/main.js</code> to start building.</p>\n  <script type="module" src="/src/main.js"></script>\n</body>\n</html>\n`,
        },
        {
          path: 'vite.config.js',
          content: `import { defineConfig } from 'vite';\n\nexport default defineConfig({\n  server: { port: 3000 },\n});\n`,
        },
        {
          path: 'src/main.js',
          content: `console.log('Hello from ${name}');\n`,
        },
      ];
  }
}
