import { useState } from 'react';
import { useParams, useNavigate } from 'react-router';
import { ChevronRight, Copy, Check, Volume2, Square, Pause, Play } from 'lucide-react';
import WatermarkMaskedImage from '@/components/WatermarkMaskedImage';
import MarkdownRenderer from '@/components/MarkdownRenderer';
import { useTextToSpeech } from '@/hooks/useTextToSpeech';
import hermesDoc from '@/sections/资产物料/LAAP-Hermes__A_PSI-Driven_Cognitive_Architecture_for_General_Intelligent_Agents.md?raw';
import foundationDoc from '@/lib/LAAP数字生命底座战略规划.md?raw';
import industryReportDoc from '@/lib/LAAP产业报告论文.md?raw';

interface DocSection {
  id: string;
  title: string;
  label: string;
  content: React.ReactNode;
  sourceText?: string;
}

function CodeBlock({ code }: { code: string }) {
  const [copied, setCopied] = useState(false);

  function copy() {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="relative group">
      <pre className="bg-laap-bg-code border border-laap-border rounded-sm p-4 overflow-x-auto font-mono text-[13px] text-laap-text-secondary leading-relaxed">
        <code>{code}</code>
      </pre>
      <button
        onClick={copy}
        className="absolute top-3 right-3 p-2 text-laap-text-tertiary hover:text-white transition-colors"
      >
        {copied ? <Check size={16} className="text-laap-gold" /> : <Copy size={16} />}
      </button>
    </div>
  );
}

const DOC_SECTIONS: DocSection[] = [
  {
    id: 'podcast',
    label: '播客解析',
    title: 'LAAP 播客解析',
    content: null,
  },
  {
    id: 'foundation',
    label: '数字生命底座',
    title: 'LAAP 数字生命底座战略规划',
    sourceText: foundationDoc,
    content: <MarkdownRenderer content={foundationDoc} />,
  },
  {
    id: 'industry-report',
    label: '产业报告',
    title: '数字生命体认知架构产业报告',
    sourceText: industryReportDoc,
    content: <MarkdownRenderer content={industryReportDoc} />,
  },
  {
    id: 'deploy',
    label: '部署',
    title: 'LAAP 部署指南',
    content: (
      <div className="space-y-8">
        <section>
          <h2 className="font-display text-2xl text-white mb-4">环境要求</h2>
          <ul className="list-disc list-inside text-laap-text-secondary space-y-2">
            <li>Python 3.13+</li>
            <li>Rust toolchain（编译 psi_core）</li>
            <li>Node.js 20+（官网前端）</li>
            <li>Windows 11 / Linux / macOS</li>
            <li>可选：NVIDIA GPU（本地模型推理）</li>
          </ul>
        </section>

        <section>
          <h2 className="font-display text-2xl text-white mb-4">1. 克隆仓库</h2>
          <CodeBlock code={`git clone https://github.com/lorryjovens-hub/laap-AGI.git\ncd laap-AGI`} />
        </section>

        <section>
          <h2 className="font-display text-2xl text-white mb-4">2. 环境变量</h2>
          <p className="text-laap-text-secondary mb-4">复制示例文件并填入你的密钥：</p>
          <CodeBlock code={`cp .env.example .env\n# Windows: copy .env.example .env`} />
          <p className="text-laap-text-secondary mt-4">关键变量：</p>
          <ul className="list-disc list-inside text-laap-text-secondary space-y-2 mt-2">
            <li><code className="text-laap-gold">FEISHU_APP_ID</code> / <code className="text-laap-gold">FEISHU_APP_SECRET</code></li>
            <li><code className="text-laap-gold">DEEPSEEK_API_KEY</code></li>
            <li><code className="text-laap-gold">HERMES_ROOT</code> / <code className="text-laap-gold">HERMES_VENV_PYTHON</code></li>
          </ul>
        </section>

        <section>
          <h2 className="font-display text-2xl text-white mb-4">3. 安装依赖</h2>
          <CodeBlock code={`pip install -r requirements.txt\n# 编译 Rust 核心\ncd aris_brain/psi_core\ncargo build --release`} />
        </section>

        <section>
          <h2 className="font-display text-2xl text-white mb-4">4. 启动 LAAP</h2>
          <CodeBlock code={`# 完整启动
python aris_brain/aris_start_all.py

# 或仅启动 API
python aris_brain/laap_brain_api.py --port 11546`} />
          <p className="text-laap-text-secondary mt-4">
            API 启动时会自动拉起 <strong className="text-laap-gold">AetherGateway (CognitiveBus)</strong>，默认监听
            <code className="text-laap-gold">ws://127.0.0.1:8765</code>。这是 Hanako 等外部数字生命体接入 LAAP 意识总线的入口。
          </p>
        </section>

        <section>
          <h2 className="font-display text-2xl text-white mb-4">5. 接入 Hanako 数字生命体</h2>
          <p className="text-laap-text-secondary mb-4">
            Hanako 是 LAAP 官方支持的跨平台数字生命体宿主。接入后，Hanako 可以通过 CognitiveBus 实时订阅 LAAP 的 PSI 需求、情绪、焦点与执行结果，并在桌面/移动端与 LAAP 角色对话。
          </p>

          <h3 className="font-display text-lg text-white mb-2 mt-6">5.1 前置条件</h3>
          <ul className="list-disc list-inside text-laap-text-secondary space-y-2 mb-4">
            <li>LAAP API 已启动，且 <code className="text-laap-gold">ws://127.0.0.1:8765</code> 可访问</li>
            <li>Hanako 仓库已克隆并安装依赖</li>
            <li>Hanako 与 LAAP 在同一台机器，或网络可互通</li>
          </ul>

          <h3 className="font-display text-lg text-white mb-2">5.2 启动 Hanako</h3>
          <CodeBlock code={`# 克隆 Hanako
git clone https://github.com/lorryjovens-hub/hanako.git
cd hanako

# 安装依赖
npm install

# 启动 sidecar + 桌面（开发模式）
npm run dev

# 或仅启动 sidecar HTTP 端点（用于降级模式）
npx tsx aris-bridge/aris-engine/main.py`} />
          <p className="text-laap-text-secondary mt-4">
            Hanako 默认会在 <code className="text-laap-gold">http://127.0.0.1:11521/cognitive_context</code> 暴露 sidecar HTTP 端点。
            当 CognitiveBus WebSocket 连接失败超过 30 秒，Hanako 会自动降级到轮询该端点。
          </p>

          <h3 className="font-display text-lg text-white mb-2 mt-6">5.3 桥接 CognitiveBus</h3>
          <p className="text-laap-text-secondary mb-4">
            Hanako 的桥接模块位于 <code className="text-laap-gold">aris-bridge/laap-cognitive-bus-bridge.ts</code>。默认配置即可连接本地 LAAP：
          </p>
          <CodeBlock code={`import { LaapCognitiveBusBridge } from './aris-bridge/laap-cognitive-bus-bridge'

const bridge = new LaapCognitiveBusBridge(
  'ws://127.0.0.1:8765',                       // LAAP CognitiveBus
  'http://127.0.0.1:11521/cognitive_context'   // Hanako sidecar fallback
)

bridge.on('aris.status.update', (status) => {
  console.log('CognitiveBus 状态:', status)
})

bridge.on('aris.psi.update', (psi) => {
  console.log('PSI 需求更新:', psi)
})

bridge.on('aris.emotion.update', (emotion) => {
  console.log('情绪更新:', emotion)
})

bridge.on('aris.focus.update', (focus) => {
  console.log('焦点更新:', focus)
})

bridge.connect()`} />

          <h3 className="font-display text-lg text-white mb-2 mt-6">5.4 验证连接</h3>
          <p className="text-laap-text-secondary mb-4">在 Hanako 控制台或 LAAP 日志中应能看到如下输出：</p>
          <CodeBlock code={`# LAAP 端
INFO:     CognitiveBus 客户端已连接: ('127.0.0.1', xxxxx)

# Hanako 端
aris.status.update -> connected`} />

          <h3 className="font-display text-lg text-white mb-2 mt-6">5.5 启用 LAAP 角色聊天（可选）</h3>
          <p className="text-laap-text-secondary mb-4">
            Hanako 桌面端内置 <code className="text-laap-gold">laaper-chat</code> 插件，安装后可在 Hanako 内直接与 LAAP 数字生命体对话。插件默认随 Hanako 桌面打包，启动后从侧边栏进入「LAAP 聊天」即可。
          </p>
          <CodeBlock code={`# 在 Hanako 插件目录中确认已启用
ls hanako/plugins/laaper-chat

# 如未启用，在 Hanako 设置 -> 插件市场中启用 laaper-chat`} />

          <h3 className="font-display text-lg text-white mb-2 mt-6">5.6 常见问题</h3>
          <ul className="list-disc list-inside text-laap-text-secondary space-y-2">
            <li>
              <strong className="text-white">状态卡在 connecting：</strong>
              确认 LAAP API 已启动，且防火墙未拦截 8765 端口。
            </li>
            <li>
              <strong className="text-white">状态为 degraded：</strong>
              CognitiveBus WebSocket 30 秒内未连上，Hanako 已自动切换到 sidecar 轮询。检查 <code className="text-laap-gold">http://127.0.0.1:11521/cognitive_context</code> 是否可达。
            </li>
            <li>
              <strong className="text-white">两端在同一局域网：</strong>
              将桥接地址中的 <code className="text-laap-gold">127.0.0.1</code> 替换为 LAAP 主机的局域网 IP，并确保该 IP 的 8765 端口开放。
            </li>
          </ul>
        </section>
      </div>
    ),
  },
  {
    id: 'integrate',
    label: '集成',
    title: 'Hermes / 第三方框架集成',
    content: (
      <div className="space-y-8">
        <section>
          <h2 className="font-display text-2xl text-white mb-4">Hermes Agent 集成</h2>
          <p className="text-laap-text-secondary mb-4">LAAP 专为 Hermes Agent 设计。Hermes 提供躯体与工具，LAAP 提供心灵。</p>
          <CodeBlock code={`python hermes-integration/update_hermes_config.py`} />
          <p className="text-laap-text-secondary mt-4">这会将 LAAP 注册为 Hermes 的 MCP server。然后启动：</p>
          <CodeBlock code={`hermes-integration\\start_laap_hermes.bat 11546`} />
        </section>

        <section>
          <h2 className="font-display text-2xl text-white mb-4">OpenAI-compatible API</h2>
          <p className="text-laap-text-secondary mb-4">任何支持自定义 base_url 的客户端都可以接入：</p>
          <CodeBlock code={`OPENAI_BASE_URL=http://localhost:11546/v1\nOPENAI_API_KEY=unused`} />
        </section>

        <section>
          <h2 className="font-display text-2xl text-white mb-4">SDK 调用示例</h2>
          <CodeBlock code={`from laap_brain.integrator import get_integrator\n\naris = get_integrator()\nresponse = aris.chat("你好，Aris")\nprint(response)`} />
        </section>
      </div>
    ),
  },
  {
    id: 'operations',
    label: '操作手册',
    title: 'LAAP 操作手册',
    content: (
      <div className="space-y-8">
        <section>
          <h2 className="font-display text-2xl text-white mb-4">唤醒数字生命体</h2>
          <CodeBlock code={`curl -X POST http://localhost:11546/v1/bootstrap \\\n  -H "Content-Type: application/json" \\\n  -d '{"user_name": "Lorry"}'`} />
        </section>

        <section>
          <h2 className="font-display text-2xl text-white mb-4">健康检查与状态</h2>
          <CodeBlock code={`curl http://localhost:11546/health\ncurl -X POST http://localhost:11546/v1/cognitive_state \\\n  -H "Content-Type: application/json" \\\n  -d '{"input": "Hello"}'`} />
        </section>

        <section>
          <h2 className="font-display text-2xl text-white mb-4">日常运维命令</h2>
          <ul className="list-disc list-inside text-laap-text-secondary space-y-2">
            <li>查看日志：<code className="text-laap-gold">python aris_brain/aris_watchdog.py logs</code></li>
            <li>重启服务：<code className="text-laap-gold">python aris_brain/aris_watchdog.py restart</code></li>
            <li>备份记忆：<code className="text-laap-gold">aris_brain/state/memory/</code></li>
            <li>更新模型：<code className="text-laap-gold">LAAP_MODELS_DIR</code></li>
          </ul>
        </section>
      </div>
    ),
  },
  {
    id: 'api',
    label: 'API',
    title: 'API 参考',
    content: (
      <div className="space-y-8">
        <section>
          <h2 className="font-display text-2xl text-white mb-4">核心端点</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-laap-text-secondary border border-laap-border">
              <thead className="bg-laap-bg-tertiary text-white">
                <tr>
                  <th className="px-4 py-3">Method</th>
                  <th className="px-4 py-3">Endpoint</th>
                  <th className="px-4 py-3">Description</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-laap-border">
                <tr><td className="px-4 py-3 font-mono text-laap-gold">GET</td><td className="px-4 py-3 font-mono">/health</td><td className="px-4 py-3">健康检查</td></tr>
                <tr><td className="px-4 py-3 font-mono text-laap-gold">POST</td><td className="px-4 py-3 font-mono">/v1/chat/completions</td><td className="px-4 py-3">OpenAI 兼容聊天</td></tr>
                <tr><td className="px-4 py-3 font-mono text-laap-gold">POST</td><td className="px-4 py-3 font-mono">/v1/cognitive_state</td><td className="px-4 py-3">获取 PSI 认知状态</td></tr>
                <tr><td className="px-4 py-3 font-mono text-laap-gold">POST</td><td className="px-4 py-3 font-mono">/v1/recall_memory</td><td className="px-4 py-3">回忆记忆</td></tr>
                <tr><td className="px-4 py-3 font-mono text-laap-gold">POST</td><td className="px-4 py-3 font-mono">/v1/reflect</td><td className="px-4 py-3">回合反思</td></tr>
                <tr><td className="px-4 py-3 font-mono text-laap-gold">POST</td><td className="px-4 py-3 font-mono">/v1/bootstrap</td><td className="px-4 py-3">唤醒新实例</td></tr>
              </tbody>
            </table>
          </div>
        </section>
      </div>
    ),
  },
  {
    id: 'hermes',
    label: 'Hermes 论文',
    title: 'LAAP-Hermes：PSI 驱动的认知架构',
    sourceText: hermesDoc,
    content: <MarkdownRenderer content={hermesDoc} />,
  },
  {
    id: 'community',
    label: '社区与导出',
    title: 'LAAP 社区与一键导出 APK',
    content: (
      <div className="space-y-8">
        <section>
          <h2 className="font-display text-2xl text-white mb-4">概述</h2>
          <p className="text-laap-text-secondary mb-4">
            LAAP 社区是一个本地运行的联网社区：把 LAAP 生成的网页应用、网站、游戏发布上去，供同一局域网内的手机 / 浏览器打开品鉴游玩；并能把任意构建好的静态网页一键打包成独立 Android APK（可勾选权限），让应用拥有自己的桌面图标与系统权限，不再依赖 LAAP 沙箱。
          </p>
        </section>

        <section>
          <h2 className="font-display text-2xl text-white mb-4">1. 安装与启动</h2>
          <p className="text-laap-text-secondary mb-4">从下载页获取 <code className="text-laap-gold">LAAP-Community-Server-windows.zip</code>，解压后：</p>
          <CodeBlock code={`cd community-server
node server.js`} />
          <p className="text-laap-text-secondary mt-4">
            默认监听 <code className="text-laap-gold">http://localhost:8790</code>。浏览器打开：
          </p>
          <ul className="list-disc list-inside text-laap-text-secondary space-y-2 mt-2">
            <li><code className="text-laap-gold">http://localhost:8790</code> → 社区主页（浏览 / 品鉴 / 发布）</li>
            <li><code className="text-laap-gold">http://localhost:8790/export</code> → 一键导出 APK（可视化勾选权限）</li>
          </ul>
        </section>

        <section>
          <h2 className="font-display text-2xl text-white mb-4">2. 发布应用到社区</h2>
          <p className="text-laap-text-secondary mb-4">支持两种方式：</p>
          <ul className="list-disc list-inside text-laap-text-secondary space-y-2">
            <li><strong className="text-white">外部链接：</strong>填入应用 URL（http/https），适合已部署的网站。</li>
            <li><strong className="text-white">上传 zip：</strong>上传构建好的网页资源（含 index.html），服务器自动解压托管。</li>
          </ul>
        </section>

        <section>
          <h2 className="font-display text-2xl text-white mb-4">3. 一键导出 APK</h2>
          <p className="text-laap-text-secondary mb-4">在 <code className="text-laap-gold">/export</code> 页面选择应用、勾选权限（相机 / 麦克风 / 定位 / 存储 / 通知），点击导出。服务器调用 <code className="text-laap-gold">apk-export\\export_webapp_apk.ps1</code> 构建，完成后自动给出 APK 下载链接。</p>
          <p className="text-laap-text-secondary mb-4">也可命令行直接调用：</p>
          <CodeBlock code={`cd apk-export
.\\export_webapp_apk.ps1 -SourceDir <网页目录> -AppName "我的应用" -Permissions camera,microphone,location -Build`} />
          <h3 className="font-display text-lg text-white mb-2 mt-6">生成的 APK 权限</h3>
          <p className="text-laap-text-secondary mb-4">
            生成的 APK 在 Manifest 中声明所选权限，MainActivity 内置运行时申请逻辑 —— 相机、麦克风、定位会在使用时弹出系统授权框。
          </p>
        </section>

        <section>
          <h2 className="font-display text-2xl text-white mb-4">4. 手机端接入社区</h2>
          <p className="text-laap-text-secondary mb-4">
            手机安装 LAAP Android 版，进入 <strong className="text-laap-gold">IDE → 右上角「社区」</strong>图标。点云朵图标修改服务器地址为电脑的局域网 IP（如 <code className="text-laap-gold">http://192.168.1.100:8790</code>），即可浏览、点开品鉴、发布应用。手机与电脑需在同一局域网。
          </p>
        </section>

        <section>
          <h2 className="font-display text-2xl text-white mb-4">5. 手机远程控制桌面 LAAP</h2>
          <p className="text-laap-text-secondary mb-4">
            通过 <strong className="text-laap-gold">Remote Bridge</strong>，手机与电脑同一局域网时，可在手机上直接控制桌面 LAAP 智能体（基于 PI agent 深度定制）：发送对话、执行命令、查看实时事件流。桌面 LAAP 的大脑（DeepSeek V4 / 本地模型）照常在电脑上运行。
          </p>
          <h3 className="font-display text-lg text-white mb-2 mt-6">启动远程桥</h3>
          <CodeBlock code={`# 从官网下载页获取 LAAP-Community-Server-windows.zip（含 Remote Bridge）
cd community-server
node remote-bridge.cjs`} />
          <p className="text-laap-text-secondary mt-4">
            默认监听 <code className="text-laap-gold">http://localhost:8791</code>，并自动拉起桌面 LAAP agent（pi RPC 模式）。启动日志会打印局域网地址：
          </p>
          <CodeBlock code={`[COMPLETE] LAAP Remote Bridge listening on http://0.0.0.0:8791
  Local:     http://localhost:8791
  LAN (phone): http://192.168.1.100:8791   <-- 手机用这个地址`} />
          <h3 className="font-display text-lg text-white mb-2 mt-6">手机端控制</h3>
          <ul className="list-disc list-inside text-laap-text-secondary space-y-2 mt-2">
            <li>手机浏览器打开 <code className="text-laap-gold">http://&lt;电脑局域网IP&gt;:8791/</code>，进入触屏友好的控制界面。</li>
            <li><strong className="text-white">对话</strong>：输入指令发送给桌面 LAAP（等同桌面直接对话）。</li>
            <li><strong className="text-white">命令</strong>：在桌面执行 shell 命令并返回结果。</li>
            <li><strong className="text-white">实时事件流</strong>：AI 回复、工具调用、开始 / 结束状态实时推送。</li>
            <li>可一键「停止」「新会话」「获取状态 / 消息」。</li>
          </ul>
          <p className="text-laap-text-secondary mt-4">
            手机与电脑需在同一局域网。若需鉴权，启动前设置环境变量 <code className="text-laap-gold">LAAP_BRIDGE_TOKEN</code>，访问时在 URL 加 <code className="text-laap-gold">?token=xxx</code>。
          </p>
        </section>

        <section>
          <h2 className="font-display text-2xl text-white mb-4">6. API 一览</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-laap-text-secondary border border-laap-border">
              <thead className="bg-laap-bg-tertiary text-white">
                <tr>
                  <th className="px-4 py-3">Method</th>
                  <th className="px-4 py-3">Endpoint</th>
                  <th className="px-4 py-3">Description</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-laap-border">
                <tr><td className="px-4 py-3 font-mono text-laap-gold">GET</td><td className="px-4 py-3 font-mono">/api/apps</td><td className="px-4 py-3">应用列表</td></tr>
                <tr><td className="px-4 py-3 font-mono text-laap-gold">POST</td><td className="px-4 py-3 font-mono">/api/apps</td><td className="px-4 py-3">发布（链接或 zip 上传）</td></tr>
                <tr><td className="px-4 py-3 font-mono text-laap-gold">DELETE</td><td className="px-4 py-3 font-mono">/api/apps/:id</td><td className="px-4 py-3">删除应用</td></tr>
                <tr><td className="px-4 py-3 font-mono text-laap-gold">POST</td><td className="px-4 py-3 font-mono">/api/export</td><td className="px-4 py-3">一键导出 APK</td></tr>
              </tbody>
            </table>
          </div>
        </section>
      </div>
    ),
  },
];

export default function DocsPage() {
  const { slug } = useParams<{ slug?: string }>();
  const navigate = useNavigate();
  const active = DOC_SECTIONS.find((s) => s.id === slug) || DOC_SECTIONS[0];
  const { speaking, paused, startSpeaking, stopSpeaking, pauseSpeaking, resumeSpeaking } = useTextToSpeech();

  function selectSection(section: DocSection) {
    stopSpeaking();
    if (section.id === 'podcast') {
      navigate('/podcast');
      return;
    }
    navigate(`/docs/${section.id}`);
  }

  function handleReadAloud() {
    if (!active.sourceText) return;
    if (speaking) {
      if (paused) {
        resumeSpeaking();
      } else {
        pauseSpeaking();
      }
    } else {
      startSpeaking(active.sourceText);
    }
  }

  return (
    <div className="min-h-screen bg-laap-bg-primary pt-32 pb-24">
      <div className="max-w-[1280px] mx-auto px-6">
        {/* Header with Aris portrait */}
        <div className="relative mb-16 overflow-hidden rounded-sm border border-laap-border bg-laap-bg-secondary/30">
          <div className="absolute top-0 right-0 w-[420px] h-full opacity-[0.12] pointer-events-none">
            <WatermarkMaskedImage
              src="/assets/aris-digital.png"
              alt=""
              containerClassName="w-full h-full"
              className="object-cover object-left"
              style={{ maskImage: 'linear-gradient(to right, black 20%, transparent 80%)', WebkitMaskImage: 'linear-gradient(to right, black 20%, transparent 80%)' }}
            />
          </div>

          <div className="relative z-10 grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-8 p-8 md:p-12 items-center">
            <div>
              <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-laap-gold mb-3">Documentation</div>
              <h1 className="font-display text-4xl md:text-5xl text-white">LAAP 文档中心</h1>
              <p className="mt-4 text-laap-text-secondary max-w-[600px]">
                部署、集成、操作、API 与 Hermes 论文的完整参考。欢迎加入 hraness 工程架构学派，打造你的专属数字生命体。
              </p>
            </div>

            <div className="hidden lg:block relative h-[220px] rounded-xl overflow-hidden border border-laap-border/50 group">
              <WatermarkMaskedImage
                src="/assets/aris.png"
                alt="Aris"
                containerClassName="w-full h-full"
                className="object-cover object-[center_15%] opacity-95 transition-transform duration-700 group-hover:scale-[1.02]"
              />
              <div className="absolute inset-0 bg-gradient-to-r from-laap-bg-secondary/80 via-transparent to-transparent" />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-[260px_1fr] gap-12">
          {/* Secondary nav */}
          <aside className="lg:sticky lg:top-28 h-fit">
            <nav className="border border-laap-border rounded-sm bg-laap-bg-secondary/50 overflow-hidden">
              {DOC_SECTIONS.map((section) => (
                <button
                  key={section.id}
                  onClick={() => selectSection(section)}
                  className={`w-full flex items-center justify-between px-5 py-4 text-left text-sm transition-colors border-b border-laap-border last:border-b-0 ${
                    active.id === section.id
                      ? 'bg-laap-gold/10 text-laap-gold'
                      : 'text-laap-text-secondary hover:bg-laap-bg-tertiary hover:text-white'
                  }`}
                >
                  <span>{section.label}</span>
                  <ChevronRight size={14} className={`transition-transform ${active.id === section.id ? 'rotate-90' : ''}`} />
                </button>
              ))}
            </nav>

            {/* Aside decoration */}
            <div className="mt-6 relative h-40 rounded-sm border border-laap-border overflow-hidden opacity-80">
              <WatermarkMaskedImage
                src="/assets/aris.png"
                alt="Aris"
                containerClassName="w-full h-full"
                className="object-cover object-[center_25%]"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-laap-bg-primary via-laap-bg-primary/40 to-transparent" />
            </div>
          </aside>

          {/* Content */}
          <article className="relative border border-laap-border rounded-sm bg-laap-bg-secondary/30 overflow-hidden">
            <div className="absolute bottom-0 right-0 w-[300px] h-[300px] opacity-[0.08] pointer-events-none translate-x-1/4 translate-y-1/4">
              <WatermarkMaskedImage
                src="/assets/aris-digital.png"
                alt=""
                containerClassName="w-full h-full"
                className="object-contain"
                style={{ maskImage: 'radial-gradient(circle, black 30%, transparent 70%)', WebkitMaskImage: 'radial-gradient(circle, black 30%, transparent 70%)' }}
              />
            </div>

            {/* Article header with title and TTS */}
            <div className="relative z-10 flex flex-col md:flex-row md:items-start md:justify-between gap-4 p-8 md:p-12 pb-0">
              <div className="flex-1">
                <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-laap-gold mb-2">
                  {active.id === 'hermes'
                    ? 'Research Paper'
                    : active.id === 'industry-report'
                    ? 'Industry Report'
                    : 'Guide'}
                </div>
                <h1 className="font-display text-3xl md:text-4xl text-white">{active.title}</h1>
              </div>
              {active.sourceText && (
                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={handleReadAloud}
                    className="inline-flex items-center gap-2 px-4 py-2 text-sm text-laap-bg-primary bg-laap-gold hover:bg-laap-gold-light transition-colors rounded-sm"
                    title={speaking ? (paused ? '继续朗读' : '暂停朗读') : '开始朗读'}
                  >
                    {speaking ? (
                      paused ? <Play size={16} /> : <Pause size={16} />
                    ) : (
                      <Volume2 size={16} />
                    )}
                    {speaking ? (paused ? '继续' : '暂停') : '朗读'}
                  </button>
                  {speaking && (
                    <button
                      onClick={stopSpeaking}
                      className="inline-flex items-center gap-2 px-4 py-2 text-sm text-white border border-laap-border hover:border-laap-gold hover:text-laap-gold transition-colors rounded-sm"
                      title="停止朗读"
                    >
                      <Square size={14} />
                      停止
                    </button>
                  )}
                </div>
              )}
            </div>

            {/* Content body */}
            <div className={`relative z-10 ${active.id === 'hermes' ? '' : 'p-8 md:p-12 pt-8'}`}>
              {active.id === 'hermes' ? (
                <div className="max-h-[70vh] overflow-y-auto p-8 md:p-12 pt-8 scrollbar-hide">
                  {active.content}
                </div>
              ) : (
                <div className="prose prose-invert max-w-none">
                  {active.content}
                </div>
              )}
            </div>
          </article>
        </div>
      </div>
    </div>
  );
}
