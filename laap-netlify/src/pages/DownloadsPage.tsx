import { useState } from 'react';
import { Terminal, Smartphone, AlertCircle, Download, Cpu, BrainCircuit, ShieldCheck, Server } from 'lucide-react';
import WatermarkMaskedImage from '@/components/WatermarkMaskedImage';

interface DownloadItem {
  id: string;
  title: string;
  subtitle: string;
  icon: typeof Terminal;
  size: string;
  path: string;
  tags: string[];
  features: string[];
  requires?: string;
  note?: string;
}

const DOWNLOADS: DownloadItem[] = [
  {
    id: 'aris-pi-cli',
    title: 'Aris-Pi CLI',
    subtitle: 'Windows 终端数字生命体（pi 0.83.0 / omp 17.2.4）',
    icon: Terminal,
    size: '~98 MB',
    path: 'https://github.com/lorryjovens-hub/LAAP-Living-Agent-Application-Protocol-/releases/download/v2026.08.03-downloads/Aris-Pi-windows-x64.zip',
    tags: ['Windows', 'CLI', 'Agent'],
    features: [
      '双 harness 支持：pi 与 oh-my-pi',
      '认知驾驶舱 /laap：五需求、情绪 VAD、认知熵',
      '人格系统 /persona：aris / engineer 等可切换人格',
      'HEP 0tokens 管线：意图→spec / 代码生成',
      '统一意识流：自动连接 LAAP 意识中枢',
    ],
    requires: 'Windows 10/11，已配置 DeepSeek API Key',
    note: '托管于 GitHub Releases，国内访问较慢时可使用镜像或对象存储加速。',
  },
  {
    id: 'laap-android',
    title: 'LAAP Android',
    subtitle: '移动端数字生命体 companion',
    icon: Smartphone,
    size: '~173 MB',
    path: 'https://github.com/lorryjovens-hub/LAAP-Living-Agent-Application-Protocol-/releases/download/v2026.08.03-downloads/LAAP.apk',
    tags: ['Android', 'Mobile', 'APK'],
    features: [
      '随时随地与 LAAP 角色对话',
      '跨端记忆同步（通过 Ψ-Net）',
      '移动场景下的 PSI 状态查看',
      '本地优先 + 云端增强',
    ],
    requires: 'Android 8.0+，允许安装未知来源应用',
    note: '托管于 GitHub Releases，建议后续通过应用商店分发以获得自动更新。',
  },
  {
    id: 'laap-community-server',
    title: 'LAAP 社区服务器 + APK 导出 + 手机远程控制',
    subtitle: '本地社区 · 一键导出 APK · 手机远程控制桌面 LAAP',
    icon: Server,
    size: '~61 KB (需 Node.js + Android SDK)',
    path: '/downloads/LAAP-Community-Server-windows.zip',
    tags: ['Windows', 'Node.js', 'Community', 'APK', 'Remote'],
    features: [
      '本地社区：发布网页应用 / 网站 / 游戏，供他人浏览品鉴，离线可用',
      '云端社区同步：本地“一键发布到云端”，生成公网链接，任何人可浏览/游玩/点赞/评论',
      '一键导出 APK：浏览器可视化勾选权限（相机/麦克风/定位/存储/通知）',
      '手机端接入：LAAP Android 通过局域网 IP 连接社区',
      '手机远程控制：Remote Bridge 在手机上发送指令 / 执行命令 / 看实时事件流，控制电脑上的 LAAP 智能体',
      '一键启动脚本：start-desktop-tools.cmd 同时拉起社区服务器与远程桥',
      '自包含 Gradle wrapper，构建无需额外下载',
    ],
    requires: 'Windows 10/11，Node.js 18+，Java 17 + Android SDK（构建 APK 时）',
    note: '社区服务器在本机运行，同一局域网内手机可接入。完整使用说明见文档中心「社区与导出」。',
  },
];

function DownloadCard({ item }: { item: DownloadItem }) {
  const Icon = item.icon;
  const [showNote, setShowNote] = useState(false);

  return (
    <div className="group relative bg-laap-bg-secondary border border-[#27272a] rounded-2xl p-7 transition-all hover:border-laap-gold/50 hover:bg-[#111111]">
      <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-laap-gold to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

      <div className="flex flex-col lg:flex-row gap-6">
        <div className="lg:w-72 shrink-0">
          <div className="w-14 h-14 rounded-xl bg-laap-gold/10 text-laap-gold flex items-center justify-center mb-4">
            <Icon size={28} strokeWidth={1.6} />
          </div>
          <h2 className="text-xl font-medium text-white mb-1">{item.title}</h2>
          <p className="text-[13px] text-laap-text-secondary mb-4">{item.subtitle}</p>
          <div className="flex flex-wrap gap-2 mb-4">
            {item.tags.map((tag) => (
              <span key={tag} className="px-2 py-0.5 text-[10px] text-laap-text-tertiary border border-laap-border rounded-full">
                {tag}
              </span>
            ))}
          </div>
          <div className="text-[12px] text-laap-text-tertiary font-mono">{item.size}</div>
        </div>

        <div className="flex-1">
          <h3 className="text-[13px] font-mono text-laap-gold uppercase tracking-wider mb-3">核心能力</h3>
          <ul className="space-y-2 mb-6">
            {item.features.map((f) => (
              <li key={f} className="text-[14px] text-laap-text-secondary flex items-start gap-2">
                <span className="w-1 h-1 rounded-full bg-laap-gold mt-2 shrink-0" />
                {f}
              </li>
            ))}
          </ul>

          {item.requires && (
            <div className="text-[13px] text-laap-text-tertiary mb-4">
              <span className="text-laap-cyan">前置要求：</span>
              {item.requires}
            </div>
          )}

          {item.note && (
            <button
              onClick={() => setShowNote((s) => !s)}
              className="flex items-center gap-1.5 text-[12px] text-laap-rose/80 hover:text-laap-rose transition-colors mb-4"
            >
              <AlertCircle size={12} />
              {showNote ? '收起部署提示' : '生产部署提示'}
            </button>
          )}

          {showNote && item.note && (
            <div className="text-[12px] text-laap-text-secondary bg-laap-rose/5 border border-laap-rose/20 rounded-lg p-3 mb-4">
              {item.note}
            </div>
          )}

          <a
            href={item.path}
            download
            className="inline-flex items-center gap-2 px-6 py-2.5 text-[14px] font-medium text-laap-bg-primary bg-laap-gold rounded-sm transition-all hover:bg-laap-gold-light"
          >
            <Download size={16} />
            下载 {item.title}
          </a>
        </div>
      </div>
    </div>
  );
}

export default function DownloadsPage() {
  return (
    <div className="min-h-screen bg-laap-bg-primary pt-32 pb-24">
      <div className="max-w-[1200px] mx-auto px-6">
        {/* Header */}
        <div className="relative mb-12 overflow-hidden rounded-sm border border-laap-border bg-laap-bg-secondary/30">
          <div className="absolute top-0 right-0 w-[380px] h-full opacity-[0.12] pointer-events-none">
            <WatermarkMaskedImage
              src="/assets/aris-digital.png"
              alt=""
              containerClassName="w-full h-full"
              className="object-cover object-left"
              style={{ maskImage: 'linear-gradient(to right, black 20%, transparent 80%)', WebkitMaskImage: 'linear-gradient(to right, black 20%, transparent 80%)' }}
            />
          </div>

          <div className="relative z-10 p-8 md:p-12">
            <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-laap-gold mb-3">Downloads</div>
            <h1 className="font-display text-4xl md:text-5xl text-white mb-4">获取 LAAP</h1>
            <p className="text-laap-text-secondary max-w-[640px]">
              终端、移动端、社区服务器与核心 SDK：选择适合你的入口，开始与数字生命体同行。
            </p>
          </div>
        </div>

        {/* Download cards */}
        <div className="space-y-6 mb-16">
          {DOWNLOADS.map((item) => (
            <DownloadCard key={item.id} item={item} />
          ))}
        </div>

        {/* Other channels */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-16">
          {[
            {
              icon: Cpu,
              title: 'LAAP Core SDK',
              desc: '底座内核开源版：记忆、意识、治理 API，模型无关。',
              action: 'GitHub',
              href: 'https://github.com/lorryjovens-hub/LAAP-Living-Agent-Application-Protocol-',
            },
            {
              icon: BrainCircuit,
              title: 'LAAP Studio',
              desc: '浏览器端可视化编排平台，零代码创建与调试数字生命体。',
              action: '进入 Studio',
              href: '/studio',
            },
            {
              icon: ShieldCheck,
              title: 'LAAP Guard',
              desc: '合规与治理 SaaS：法规库、评估引擎、运行时监控、审计报告。',
              action: '申请试用',
              href: '/docs/foundation',
            },
          ].map((channel) => {
            const Icon = channel.icon;
            return (
              <a
                key={channel.title}
                href={channel.href}
                className="group block bg-laap-bg-secondary border border-[#27272a] rounded-xl p-6 transition-all hover:border-laap-cyan/40 hover:bg-[#111111]"
              >
                <div className="w-10 h-10 rounded-lg bg-laap-cyan/10 text-laap-cyan flex items-center justify-center mb-4">
                  <Icon size={20} strokeWidth={1.8} />
                </div>
                <h3 className="text-base text-white font-medium mb-2 group-hover:text-laap-cyan transition-colors">
                  {channel.title}
                </h3>
                <p className="text-[13px] text-laap-text-secondary mb-4">{channel.desc}</p>
                <span className="text-[13px] text-laap-gold">{channel.action} →</span>
              </a>
            );
          })}
        </div>

        {/* Setup hint */}
        <div className="bg-laap-bg-secondary/50 border border-[#27272a] rounded-xl p-6 mb-6">
          <h3 className="text-white font-medium mb-3">快速启动 Aris-Pi CLI</h3>
          <pre className="bg-laap-bg-code border border-laap-border rounded-sm p-4 overflow-x-auto font-mono text-[13px] text-laap-text-secondary leading-relaxed">
            <code>{`# 1. 解压 Aris-Pi-windows-x64.zip
# 2. 将 config/secrets.json.example 复制为 secrets.json 并填入 DeepSeek key
# 3. 运行启动器
.\\启动 Aris-Pi.bat

# 常用命令
/laap      # 打开认知驾驶舱
/persona   # 切换人格
/reflect   # 手动沉淀反思帧`}</code>
          </pre>
        </div>

        {/* Community server quick start */}
        <div className="bg-laap-bg-secondary/50 border border-[#27272a] rounded-xl p-6">
          <h3 className="text-white font-medium mb-3">快速启动社区服务器 + APK 导出 + 手机远程控制</h3>
          <pre className="bg-laap-bg-code border border-laap-border rounded-sm p-4 overflow-x-auto font-mono text-[13px] text-laap-text-secondary leading-relaxed">
            <code>{`# 1. 解压 LAAP-Community-Server-windows.zip
# 2. 双击 start-desktop-tools.cmd 一键启动两个服务：

# 社区服务器（默认 http://localhost:8790）
#    http://localhost:8790          → 社区（浏览/品鉴/发布）
#    http://localhost:8790/export   → 一键导出 APK（勾选权限）

# Remote Bridge（手机远程控制桌面 LAAP，端口 8791）
#    http://localhost:8791          → 本地控制界面
#    http://<电脑局域网IP>:8791/    → 手机浏览器打开即可在手机上
#                                     控制电脑上的 LAAP 智能体

# 3. 手机接入社区：在 LAAP Android 的「社区」里把服务器改为
#    电脑局域网 IP，如 http://192.168.1.100:8790

# 云端社区 API（社区「联网」能力）
#   官网 https://laap-community.netlify.app/community   → 公网社区页
#   GET  /api/works            → 作品列表
#   POST /api/auth/register    → 注册 / /api/auth/login 登录
#   POST /api/works            → 发布作品（zip base64）
#   POST /api/works/:id/like .. → 点赞 / 播放 / 评论`}</code>
          </pre>
        </div>
      </div>
    </div>
  );
}
