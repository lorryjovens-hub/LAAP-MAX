export default function Footer() {
  return (
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
              &copy; 2024 LAAP Protocol
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

        {/* Bottom bar */}
        <div className="mt-8 pt-6 border-t border-[#27272a] flex flex-col sm:flex-row items-center justify-between gap-4">
          <span className="text-[12px] text-laap-text-tertiary">
            Built with consciousness.
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
  );
}
