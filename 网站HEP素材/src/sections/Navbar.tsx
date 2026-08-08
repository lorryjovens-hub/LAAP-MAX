import { Search } from "lucide-react";

function LogoMark() {
  return (
    <svg width="30" height="30" viewBox="0 0 32 32" fill="none" aria-hidden>
      <defs>
        <linearGradient id="lg-m" x1="2" y1="30" x2="30" y2="2" gradientUnits="userSpaceOnUse">
          <stop stopColor="#7c3aed" />
          <stop offset="0.5" stopColor="#d946ef" />
          <stop offset="1" stopColor="#fb7185" />
        </linearGradient>
      </defs>
      <path
        d="M4 26V10.8c0-1.9 2.4-2.8 3.7-1.4l6.4 6.9c.9 1 2.4 1 3.3 0l6.4-6.9c1.3-1.4 3.7-.5 3.7 1.4V26"
        stroke="url(#lg-m)"
        strokeWidth="4.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function Navbar() {
  return (
    <nav className="w-full px-6 sm:px-8 py-4 flex items-center justify-between max-w-[1440px] mx-auto">
      {/* left: logo + primary links */}
      <div className="flex items-center gap-3">
        <a href="#" className="flex items-center gap-2 shrink-0">
          <LogoMark />
          <span className="text-foreground font-bold text-xl tracking-tight">motionsites</span>
        </a>
        <div className="hidden md:flex items-center gap-1 ml-6">
          <a
            href="#"
            className="px-3 py-2 text-sm font-medium text-foreground rounded-lg hover:bg-white/5 transition-colors"
          >
            Sites
          </a>
          <a
            href="#"
            className="px-3 py-2 text-sm font-medium text-muted-foreground rounded-lg hover:text-foreground transition-colors flex items-center gap-1.5"
          >
            Apps
            <span className="text-[9px] font-semibold px-1 py-px rounded border border-orange-500/50 text-orange-400 leading-tight">
              NEW
            </span>
          </a>
        </div>
      </div>

      {/* right: secondary links + search + CTA */}
      <div className="hidden lg:flex items-center gap-1 sm:gap-2">
        {["Sections", "Backgrounds", "Contact Us"].map((label) => (
          <a
            key={label}
            href="#"
            className="px-3 py-2 text-sm font-medium text-white/70 hover:text-foreground rounded-lg transition-colors"
          >
            {label}
          </a>
        ))}
        <button
          className="p-2 ml-1 text-white/70 hover:text-foreground transition-colors"
          aria-label="Search"
        >
          <Search size={19} strokeWidth={2.2} />
        </button>
        <a
          href="#"
          className="ml-2 px-4 py-2 rounded-full bg-white text-[#09090b] text-sm font-semibold hover:bg-white/90 transition-colors"
        >
          Go Unlimited
        </a>
      </div>
    </nav>
  );
}
