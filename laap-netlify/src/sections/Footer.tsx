import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

const qqGroup = {
  name: 'LAAP AGI 数字生命体',
  number: '1030235021',
  qr: '/assets/qq-group-qr.png.jpg',
};

const douyinGroup = {
  name: 'LAAP 技术交流群',
  number: '829049981107',
  qr: '/assets/douyin-group-qr.png.jpg',
};

const sponsor = {
  qr: '/assets/sponsor-qr.png.jpg',
  text: '如果喜欢本项目，可以请博主喝一杯奶茶',
};

const followPlatforms = [
  {
    name: '哔哩哔哩',
    qr: '/assets/bilibili-profile-qr.png.jpg',
    url: 'https://space.bilibili.com/',
  },
  {
    name: '抖音',
    qr: '/assets/douyin-profile-qr.png.jpg',
    url: 'https://v.douyin.com/aoiZVm3RKTA/',
  },
];

function BilibiliIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M17.813 4.653h.854c1.51.054 2.769.578 3.773 1.574 1.004.995 1.524 2.249 1.56 3.76v7.36c-.036 1.51-.556 2.769-1.56 3.773s-2.262 1.524-3.773 1.56H5.333c-1.51-.036-2.769-.556-3.773-1.56S.036 18.858 0 17.347v-7.36c.036-1.511.556-2.765 1.56-3.76 1.004-.996 2.262-1.52 3.773-1.574h.774l-1.174-1.12a1.234 1.234 0 0 1-.373-.906c0-.356.124-.659.373-.907l.027-.027c.267-.249.573-.373.92-.373.347 0 .653.124.92.373L9.653 4.44c.071.071.134.142.187.213h4.267a.836.836 0 0 1 .16-.213l2.853-2.747c.267-.249.573-.373.92-.373.347 0 .662.151.929.4.267.249.391.551.391.907 0 .355-.124.657-.373.906zM5.333 7.24c-.746.018-1.373.276-1.88.773-.506.498-.769 1.13-.786 1.894v7.52c.017.764.28 1.395.786 1.893.507.498 1.134.756 1.88.773h13.334c.746-.017 1.373-.275 1.88-.773.506-.498.769-1.129.786-1.893v-7.52c-.017-.765-.28-1.396-.786-1.894-.507-.497-1.134-.755-1.88-.773zM8 11.107c.373 0 .684.124.933.373.25.249.383.569.4.96H7.2c.018-.391.151-.711.4-.96.249-.249.56-.373.933-.373zm8 0c.373 0 .684.124.933.373.25.249.383.569.4.96h-2.666c.018-.391.151-.711.4-.96.249-.249.56-.373.933-.373zm-7.547 4.8c-.32-.178-.52-.453-.6-.822-.08-.373.018-.711.293-1.013.276-.302.627-.453 1.053-.453h5.6c.427 0 .778.151 1.053.453.276.302.373.64.294 1.013-.08.369-.28.644-.6.822-.32.178-.667.267-1.04.267H9.493c-.373 0-.72-.089-1.04-.267z" />
    </svg>
  );
}

function DouyinIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M19.59 6.27c-.17-.02-.34-.04-.5-.08a5.78 5.78 0 0 1-4.15-3.94c-.07-.25-.12-.5-.16-.76V.5h-4.1v16.2a3.24 3.24 0 0 1-1.05 2.36 3.32 3.32 0 0 1-4.83-.5 3.4 3.4 0 0 1 .72-4.5 3.3 3.3 0 0 1 3.54-.55c.2.08.4.18.58.3V8.74a7.5 7.5 0 0 0-6.64 3.12A7.7 7.7 0 0 0 5.4 21.3a7.5 7.5 0 0 0 9.12-1.4 7.67 7.67 0 0 0 2.04-5.22V8.66a9.2 9.2 0 0 0 5.04 1.5V6.27h-2.01z" />
    </svg>
  );
}

function QqIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12.003 2c-2.265 0-6.29 1.364-6.29 7.325v1.195S3.55 14.96 3.55 17.474c0 .665.17 1.025.281 1.025.114 0 .902-.484 1.748-2.072 0 0-.18 2.197 1.904 3.967 0 0-1.77.495-1.77 1.182 0 .686 4.078.43 6.29.43 2.21 0 6.29.256 6.29-.43 0-.687-1.77-1.182-1.77-1.182 2.085-1.77 1.904-3.967 1.904-3.967.846 1.588 1.634 2.072 1.748 2.072.111 0 .281-.36.281-1.025 0-2.514-2.164-6.954-2.164-6.954V9.325C18.293 3.364 14.268 2 12.003 2z" />
    </svg>
  );
}

export default function Footer() {
  return (
    <TooltipProvider delayDuration={100}>
      <footer className="bg-laap-bg-secondary border-t border-[#27272a]">
        <div className="max-w-[1200px] mx-auto px-6 py-12">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-8">
            {/* Left */}
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-white font-medium text-base tracking-[0.1em]">LAAP</span>
                <span className="w-1 h-1 rounded-full bg-laap-emerald animate-pulse-glow" />
              </div>
              <p className="text-[13px] text-laap-text-tertiary">
                Living Agent Application Protocol
              </p>
              <p className="text-[13px] text-laap-text-tertiary mt-1">
                &copy; 2026 LAAP Protocol
              </p>
              <p className="text-[13px] text-laap-gold/80 mt-2">
                欢迎加入“hraness工程架构学派”“打造你的专属数字生命体”
              </p>
            </div>

            {/* Center */}
            <div className="flex flex-wrap items-center gap-6">
              <a
                href="https://github.com/lorryjovens-hub/LAAP-Living-Agent-Application-Protocol-"
                target="_blank"
                rel="noopener noreferrer"
                className="text-[13px] text-laap-text-secondary hover:text-white transition-colors"
              >
                GitHub
              </a>
              <button
                onClick={() => document.getElementById('docs')?.scrollIntoView({ behavior: 'smooth' })}
                className="text-[13px] text-laap-text-secondary hover:text-white transition-colors"
              >
                Docs
              </button>
              <button
                onClick={() => document.getElementById('architecture')?.scrollIntoView({ behavior: 'smooth' })}
                className="text-[13px] text-laap-text-secondary hover:text-white transition-colors"
              >
                Research
              </button>
              <a
                href="/downloads"
                className="text-[13px] text-laap-text-secondary hover:text-white transition-colors"
              >
                Downloads
              </a>
              <span className="text-[13px] text-laap-text-secondary">Contact</span>
            </div>

            {/* Right */}
            <div className="text-right">
              <div className="font-mono text-[12px] text-laap-text-tertiary truncate max-w-[200px]">
                did:laap:a3f7c8e2...
              </div>
              <div className="font-mono text-[12px] text-laap-text-tertiary mt-1">
                v2.1.0
              </div>
            </div>
          </div>

          {/* Community & Sponsor Section */}
          <div className="mt-10 grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* QQ Group */}
            <div className="rounded-xl border border-[#27272a] bg-laap-bg-primary p-5 transition-colors hover:border-[#3f3f46]">
              <div className="flex items-center gap-2 mb-4">
                <QqIcon className="w-5 h-5 text-[#12B7F5]" />
                <h3 className="text-sm font-medium text-white">QQ 交流群</h3>
              </div>
              <div className="flex items-center gap-4">
                <div className="relative w-24 h-24 rounded-lg overflow-hidden border border-[#27272a] bg-white flex-shrink-0">
                  <img
                    src={qqGroup.qr}
                    alt={qqGroup.name}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = 'none';
                    }}
                  />
                </div>
                <div className="min-w-0">
                  <p className="text-sm text-white font-medium truncate">{qqGroup.name}</p>
                  <p className="text-xs text-laap-text-tertiary mt-1">群号：{qqGroup.number}</p>
                  <p className="text-xs text-laap-text-secondary mt-2">扫码加入，一起交流</p>
                </div>
              </div>
            </div>

            {/* Douyin Group */}
            <div className="rounded-xl border border-[#27272a] bg-laap-bg-primary p-5 transition-colors hover:border-[#3f3f46]">
              <div className="flex items-center gap-2 mb-4">
                <DouyinIcon className="w-5 h-5 text-[#24F6F0]" />
                <h3 className="text-sm font-medium text-white">抖音交流群</h3>
              </div>
              <div className="flex items-center gap-4">
                <div className="relative w-24 h-24 rounded-lg overflow-hidden border border-[#27272a] bg-white flex-shrink-0">
                  <img
                    src={douyinGroup.qr}
                    alt={douyinGroup.name}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = 'none';
                    }}
                  />
                </div>
                <div className="min-w-0">
                  <p className="text-sm text-white font-medium truncate">{douyinGroup.name}</p>
                  <p className="text-xs text-laap-text-tertiary mt-1">群号：{douyinGroup.number}</p>
                  <p className="text-xs text-laap-text-secondary mt-2">扫码加入，一起交流</p>
                </div>
              </div>
            </div>

            {/* Sponsor */}
            <div className="rounded-xl border border-[#27272a] bg-laap-bg-primary p-5 transition-colors hover:border-[#3f3f46]">
              <div className="flex items-center gap-2 mb-4">
                <svg className="w-5 h-5 text-laap-gold" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm.31-8.86c-1.77-.45-2.34-.94-2.34-1.67 0-.84.79-1.43 2.1-1.43 1.38 0 1.9.66 1.94 1.64h1.71c-.05-1.34-.87-2.57-2.49-2.97V5H10.9v1.69c-1.51.32-2.72 1.3-2.72 2.81 0 1.79 1.49 2.69 3.66 3.21 1.95.46 2.34 1.15 2.34 1.87 0 .53-.39 1.39-2.1 1.39-1.6 0-2.23-.72-2.32-1.76H8.04c.1 1.7 1.36 2.66 2.86 2.97V19h2.34v-1.67c1.52-.29 2.72-1.16 2.73-2.77-.01-2.2-1.9-2.96-3.66-3.42z" />
                </svg>
                <h3 className="text-sm font-medium text-white">赞助支持</h3>
              </div>
              <div className="flex items-center gap-4">
                <div className="relative w-24 h-24 rounded-lg overflow-hidden border border-[#27272a] bg-white flex-shrink-0">
                  <img
                    src={sponsor.qr}
                    alt="赞助二维码"
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = 'none';
                    }}
                  />
                </div>
                <div className="min-w-0">
                  <p className="text-sm text-laap-gold font-medium">{sponsor.text}</p>
                  <p className="text-xs text-laap-text-secondary mt-2">微信扫码，感谢支持</p>
                </div>
              </div>
            </div>
          </div>

          {/* Follow Platforms */}
          <div className="mt-8 flex items-center justify-center gap-6">
            <span className="text-xs text-laap-text-tertiary">关注我们</span>
            {followPlatforms.map((platform) => (
              <Tooltip key={platform.name}>
                <TooltipTrigger asChild>
                  <a
                    href={platform.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="group relative flex items-center justify-center w-10 h-10 rounded-full border border-[#27272a] bg-laap-bg-primary text-laap-text-secondary transition-all duration-300 hover:border-[#3f3f46] hover:text-white hover:scale-110"
                    aria-label={platform.name}
                  >
                    {platform.name === '哔哩哔哩' ? (
                      <BilibiliIcon className="w-5 h-5" />
                    ) : (
                      <DouyinIcon className="w-5 h-5" />
                    )}
                  </a>
                </TooltipTrigger>
                <TooltipContent
                  side="top"
                  sideOffset={12}
                  className="bg-laap-bg-primary border border-[#27272a] p-3 rounded-xl shadow-2xl max-w-[180px]"
                >
                  <div className="flex flex-col items-center gap-2">
                    <p className="text-xs text-white font-medium">{platform.name}</p>
                    <div className="w-32 h-32 rounded-lg overflow-hidden border border-[#27272a] bg-white">
                      <img
                        src={platform.qr}
                        alt={`${platform.name}二维码`}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          (e.target as HTMLImageElement).style.display = 'none';
                        }}
                      />
                    </div>
                    <p className="text-[10px] text-laap-text-tertiary">扫码关注</p>
                  </div>
                </TooltipContent>
              </Tooltip>
            ))}
          </div>

          {/* Douyin card */}
          <div className="mt-8">
            <a
              href="https://v.douyin.com/aoiZVm3RKTA/"
              target="_blank"
              rel="noopener noreferrer"
              className="group inline-flex items-center gap-4 max-w-full rounded-xl border border-[#27272a] bg-laap-bg-primary p-4 transition-all duration-300 hover:border-[#3f3f46] hover:bg-[#0a0a0a]"
            >
              <div className="relative flex-shrink-0 w-14 h-14 rounded-lg bg-gradient-to-br from-[#1c1c1c] to-[#0a0a0a] flex items-center justify-center border border-[#27272a] group-hover:border-[#3f3f46] transition-colors">
                {/* Douyin icon */}
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path
                    d="M19.59 6.27c-.17-.02-.34-.04-.5-.08a5.78 5.78 0 0 1-4.15-3.94c-.07-.25-.12-.5-.16-.76V.5h-4.1v16.2a3.24 3.24 0 0 1-1.05 2.36 3.32 3.32 0 0 1-4.83-.5 3.4 3.4 0 0 1 .72-4.5 3.3 3.3 0 0 1 3.54-.55c.2.08.4.18.58.3V8.74a7.5 7.5 0 0 0-6.64 3.12A7.7 7.7 0 0 0 5.4 21.3a7.5 7.5 0 0 0 9.12-1.4 7.67 7.67 0 0 0 2.04-5.22V8.66a9.2 9.2 0 0 0 5.04 1.5V6.27h-2.01z"
                    fill="url(#douyin-gradient)"
                  />
                  <defs>
                    <linearGradient id="douyin-gradient" x1="12" y1="0.5" x2="12" y2="23.5" gradientUnits="userSpaceOnUse">
                      <stop stopColor="#24F6F0" />
                      <stop offset="1" stopColor="#F91955" />
                    </linearGradient>
                  </defs>
                </svg>
                <div className="absolute -bottom-1 -right-1 w-5 h-5 rounded-full bg-laap-bg-primary border border-[#27272a] flex items-center justify-center">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="white">
                    <path d="M8 5v14l11-7z" />
                  </svg>
                </div>
              </div>
              <div className="min-w-0">
                <div className="text-[14px] font-medium text-white group-hover:text-laap-gold transition-colors truncate">
                  抖音视频
                </div>
                <div className="text-[12px] text-laap-text-tertiary mt-0.5 line-clamp-2">
                  觉醒了？！我做了一个 harness 意识工程 LAAP 数字生命体。
                </div>
              </div>
            </a>
          </div>

          {/* Bottom bar */}
          <div className="mt-8 pt-6 border-t border-[#27272a] flex flex-col sm:flex-row items-center justify-between gap-4">
            <span className="text-[12px] text-laap-text-tertiary">
              本项目由 LORRY 领衔 LAAP 团队开发，深圳智擎科技有限公司。
            </span>
            <div className="flex items-center gap-6">
              <span className="text-[12px] text-laap-text-tertiary hover:text-laap-text-secondary cursor-pointer transition-colors">
                Terms
              </span>
              <span className="text-[12px] text-laap-text-tertiary hover:text-laap-text-secondary cursor-pointer transition-colors">
                Privacy
              </span>
            </div>
          </div>
        </div>
      </footer>
    </TooltipProvider>
  );
}
