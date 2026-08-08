import { hashCode } from "@/data/cards";

// ── CSS animation keyframes ──
const animStyles = `
@keyframes blob-float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(3%, -2%) scale(1.05); }
  66% { transform: translate(-2%, 3%) scale(0.95); }
}
@keyframes aurora-pulse {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}
@keyframes shimmer-move {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(200%); }
}
@keyframes breathe {
  0%, 100% { opacity: 0.7; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.02); }
}
@keyframes float-up {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
}
@keyframes glow-pulse {
  0%, 100% { box-shadow: 0 0 4px rgba(255,255,255,0.1); }
  50% { box-shadow: 0 0 12px rgba(255,255,255,0.2); }
}
@keyframes gradient-shift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
`;

if (typeof document !== 'undefined') {
  const style = document.createElement('style');
  style.textContent = animStyles;
  document.head.appendChild(style);
}

/**
 * Procedural "mini website" thumbnails drawn purely with CSS.
 * Every card deterministically picks a theme + palette from its name,
 * so the grid looks like a wall of real site previews.
 */

type Palette = {
  bg: string;
  fg: string;
  muted: string;
  accent: string;
  accent2: string;
};

const DARK: Palette[] = [
  { bg: "#0d0d12", fg: "#f5f5f7", muted: "#8b8b96", accent: "#8b5cf6", accent2: "#ec4899" },
  { bg: "#0a0f0d", fg: "#eef7f2", muted: "#7d8f86", accent: "#10b981", accent2: "#84cc16" },
  { bg: "#0c0a12", fg: "#f3eefc", muted: "#8f87a3", accent: "#7c3aed", accent2: "#38bdf8" },
  { bg: "#101014", fg: "#f5f5f5", muted: "#8a8a8a", accent: "#f97316", accent2: "#f43f5e" },
  { bg: "#0b1220", fg: "#eaf1fb", muted: "#8296b3", accent: "#3b82f6", accent2: "#22d3ee" },
  { bg: "#120d0a", fg: "#faf3ec", muted: "#a3907f", accent: "#eab308", accent2: "#f97316" },
];

const LIGHT: Palette[] = [
  { bg: "#f4efe6", fg: "#1c1917", muted: "#78716c", accent: "#c2410c", accent2: "#0f766e" },
  { bg: "#eef2f6", fg: "#111827", muted: "#6b7280", accent: "#2563eb", accent2: "#7c3aed" },
  { bg: "#f7f4ef", fg: "#292524", muted: "#84796d", accent: "#be185d", accent2: "#b45309" },
  { bg: "#e8ede9", fg: "#14201a", muted: "#5f7268", accent: "#047857", accent2: "#65a30d" },
];

function Bar({ w, h = 4, c, r = 2, o = 1 }: { w: number | string; h?: number; c: string; r?: number; o?: number }) {
  return <div style={{ width: w, height: h, background: c, borderRadius: r, opacity: o }} />;
}

function MiniNav({ p, dark }: { p: Palette; dark: boolean }) {
  return (
    <div className="flex items-center justify-between" style={{ padding: "7% 8% 0" }}>
      <div className="flex items-center gap-[6px]">
        <div style={{ width: 10, height: 10, borderRadius: 3, background: `linear-gradient(135deg, ${p.accent}, ${p.accent2})` }} />
        <Bar w={26} h={4} c={p.fg} o={0.9} />
      </div>
      <div className="flex items-center gap-[7px]">
        {[0.55, 0.45, 0.5].map((o, i) => (
          <Bar key={i} w={14} h={3} c={dark ? "#ffffff" : p.muted} o={o} />
        ))}
        <div style={{ width: 22, height: 9, borderRadius: 99, background: p.accent }} />
      </div>
    </div>
  );
}

/** dark hero with glowing gradient blob + floating particles */
function AuroraHero({ p, seed }: { p: Palette; seed: number }) {
  const x = 20 + (seed % 50);
  const dots = Array.from({length: 5}, (_, i) => ({
    left: `${(seed * (i+1) * 7) % 80 + 10}%`,
    top: `${(seed * (i+1) * 13) % 70 + 15}%`,
    size: 3 + (i % 3),
    delay: i * 0.6,
  }));
  return (
    <div className="absolute inset-0" style={{
      background: `${p.bg}`,
      animation: 'gradient-shift 6s ease-in-out infinite',
      backgroundSize: '200% 200%',
    }}>
      <div
        className="absolute rounded-full"
        style={{
          width: "70%", height: "70%", left: `${x - 20}%`, top: "20%",
          background: `radial-gradient(circle, ${p.accent}cc, ${p.accent2}55 45%, transparent 70%)`,
          filter: "blur(18px)",
          animation: "blob-float 8s ease-in-out infinite",
        }}
      />
      {dots.map((d, i) => (
        <div key={i}
          className="absolute rounded-full"
          style={{
            left: d.left, top: d.top,
            width: d.size, height: d.size,
            background: p.accent,
            opacity: 0.5,
            animation: `float-up ${2 + (i % 3)}s ease-in-out ${d.delay}s infinite`,
          }}
        />
      ))}
      <MiniNav p={p} dark />
      <div className="flex flex-col items-center gap-[7px]" style={{ padding: "13% 12% 0" }}>
        <Bar w="62%" h={9} c={p.fg} r={3} />
        <Bar w="45%" h={9} c={p.fg} r={3} />
        <Bar w="38%" h={4} c={p.muted} />
        <div className="mt-[6px]" style={{
          width: 42, height: 13, borderRadius: 99,
          background: `linear-gradient(90deg, ${p.accent}, ${p.accent2})`,
          animation: 'glow-pulse 3s ease-in-out infinite',
        }} />
      </div>
    </div>
  );
}

/** light editorial layout with serif-like mass */
function Editorial({ p, seed }: { p: Palette; seed: number }) {
  const left = seed % 2 === 0;
  return (
    <div className="absolute inset-0" style={{ background: p.bg }}>
      <MiniNav p={p} dark={false} />
      <div className="flex" style={{ padding: "7% 8%", gap: "6%" }}>
        <div className="flex flex-col gap-[7px]" style={{ width: "52%", order: left ? 0 : 1 }}>
          <Bar w="90%" h={11} c={p.fg} r={2} />
          <Bar w="70%" h={11} c={p.fg} r={2} />
          <Bar w="55%" h={4} c={p.muted} />
          <Bar w="45%" h={4} c={p.muted} />
          <div className="mt-[8px]" style={{ width: 38, height: 12, borderRadius: 2, background: p.fg }} />
        </div>
        <div
          style={{
            width: "42%", height: 86, borderRadius: 6, order: left ? 1 : 0,
            background: `linear-gradient(150deg, ${p.accent}, ${p.accent2})`,
          }}
        />
      </div>
    </div>
  );
}

/** SaaS dashboard mock */
function Dashboard({ p, seed }: { p: Palette; seed: number }) {
  const bars = [40, 65, 45, 80, 55, 70, 50];
  const rot = seed % bars.length;
  const vals = [...bars.slice(rot), ...bars.slice(0, rot)];
  return (
    <div className="absolute inset-0 flex" style={{ background: p.bg }}>
      <div className="flex flex-col gap-[8px]" style={{ width: "24%", padding: "9% 5%", borderRight: `1px solid ${p.fg}14` }}>
        <div style={{ width: 12, height: 12, borderRadius: 4, background: p.accent }} />
        {[0.7, 0.5, 0.6, 0.4].map((o, i) => <Bar key={i} w="80%" h={3} c={p.fg} o={o} />)}
      </div>
      <div className="flex-1 flex flex-col" style={{ padding: "8% 7%", gap: "9%" }}>
        <div className="flex gap-[6%]">
          {[p.accent, p.accent2, p.muted].map((c, i) => (
            <div key={i} style={{ flex: 1, height: 22, borderRadius: 5, background: `${c}26`, border: `1px solid ${c}44` }} />
          ))}
        </div>
        <div className="flex items-end gap-[6px] flex-1">
          {vals.map((v, i) => (
            <div key={i} style={{ flex: 1, height: `${v}%`, borderRadius: 3, background: i === 3 ? p.accent : `${p.fg}30` }} />
          ))}
        </div>
      </div>
    </div>
  );
}

/** ecommerce product tile */
function Product({ p, seed }: { p: Palette; seed: number }) {
  return (
    <div className="absolute inset-0" style={{ background: p.bg }}>
      <MiniNav p={p} dark={false} />
      <div className="flex" style={{ padding: "6% 8%", gap: "6%" }}>
        <div
          className="flex items-center justify-center"
          style={{ width: "48%", height: 100, borderRadius: 8, background: `linear-gradient(160deg, ${p.accent}33, ${p.accent2}22)` }}
        >
          <div
            style={{
              width: 46, height: 46, borderRadius: seed % 2 ? "50%" : 8,
              background: `linear-gradient(135deg, ${p.accent}, ${p.accent2})`,
              boxShadow: "0 8px 20px rgba(0,0,0,.18)",
            }}
          />
        </div>
        <div className="flex flex-col gap-[7px] justify-center" style={{ width: "46%" }}>
          <Bar w="80%" h={8} c={p.fg} r={2} />
          <Bar w="60%" h={4} c={p.muted} />
          <Bar w="40%" h={4} c={p.muted} />
          <Bar w="35%" h={7} c={p.accent} r={2} />
          <div className="mt-[4px]" style={{ width: 40, height: 12, borderRadius: 99, background: p.fg }} />
        </div>
      </div>
    </div>
  );
}

/** big-type neon hero */
function Neon({ p, seed }: { p: Palette; seed: number }) {
  return (
    <div className="absolute inset-0" style={{ background: p.bg }}>
      <div
        className="absolute"
        style={{
          inset: 0,
          background: `linear-gradient(180deg, transparent 55%, ${p.accent}30)`,
        }}
      />
      <MiniNav p={p} dark />
      <div className="flex flex-col gap-[8px]" style={{ padding: "12% 9% 0" }}>
        <div
          style={{
            width: `${68 + (seed % 18)}%`, height: 13, borderRadius: 4,
            background: `linear-gradient(90deg, ${p.accent}, ${p.accent2})`,
            boxShadow: `0 0 18px ${p.accent}88`,
          }}
        />
        <div
          style={{
            width: "58%", height: 13, borderRadius: 4,
            background: `linear-gradient(90deg, ${p.accent2}, ${p.accent})`,
            boxShadow: `0 0 18px ${p.accent2}66`,
          }}
        />
        <Bar w="42%" h={4} c={p.muted} />
        <div className="flex gap-[8px] mt-[6px]">
          <div style={{ width: 40, height: 13, borderRadius: 99, background: p.fg }} />
          <div style={{ width: 40, height: 13, borderRadius: 99, border: `1px solid ${p.fg}55` }} />
        </div>
      </div>
    </div>
  );
}

/** hero + 3 cards row */
function GridThree({ p, seed }: { p: Palette; seed: number }) {
  return (
    <div className="absolute inset-0" style={{ background: p.bg }}>
      <MiniNav p={p} dark />
      <div className="flex flex-col items-center gap-[6px]" style={{ padding: "9% 10% 0" }}>
        <Bar w="55%" h={8} c={p.fg} r={3} />
        <Bar w="35%" h={4} c={p.muted} />
      </div>
      <div className="flex" style={{ padding: "7% 8% 0", gap: "5%" }}>
        {[0, 1, 2].map((i) => (
          <div key={i} className="flex-1 flex flex-col gap-[5px]" style={{ height: 62, borderRadius: 7, background: `${p.fg}0d`, border: `1px solid ${p.fg}14`, padding: 8 }}>
            <div style={{ width: 12, height: 12, borderRadius: 4, background: i === (seed % 3) ? p.accent : `${p.fg}2e` }} />
            <Bar w="75%" h={4} c={p.fg} o={0.85} />
            <Bar w="55%" h={3} c={p.muted} />
          </div>
        ))}
      </div>
    </div>
  );
}

/** animated-gradient video background with play button */
function PlayBg({ p, seed }: { p: Palette; seed: number }) {
  const angle = 120 + (seed % 120);
  return (
    <div
      className="absolute inset-0 flex items-center justify-center"
      style={{ background: `linear-gradient(${angle}deg, ${p.bg}, ${p.accent}55 50%, ${p.accent2}44)` }}
    >
      <div
        className="absolute"
        style={{
          width: "60%", height: "55%", right: "-10%", top: "-15%",
          background: `radial-gradient(circle, ${p.accent2}66, transparent 65%)`,
          filter: "blur(16px)",
        }}
      />
      <div
        className="flex items-center justify-center"
        style={{
          width: 34, height: 34, borderRadius: "50%",
          background: "rgba(255,255,255,.16)",
          border: "1px solid rgba(255,255,255,.4)",
          backdropFilter: "blur(4px)",
        }}
      >
        <div
          style={{
            width: 0, height: 0, marginLeft: 3,
            borderTop: "6px solid transparent", borderBottom: "6px solid transparent",
            borderLeft: "9px solid #fff",
          }}
        />
      </div>
      <div className="absolute flex flex-col gap-[5px]" style={{ left: "8%", bottom: "9%" }}>
        <Bar w={70} h={7} c="#ffffff" r={3} o={0.95} />
        <Bar w={48} h={4} c="#ffffff" o={0.6} />
      </div>
    </div>
  );
}

/** split hero with image panel */
function Split({ p, seed }: { p: Palette; seed: number }) {
  return (
    <div className="absolute inset-0" style={{ background: p.bg }}>
      <MiniNav p={p} dark />
      <div className="flex items-center" style={{ padding: "6% 8%", gap: "7%" }}>
        <div className="flex flex-col gap-[7px]" style={{ width: "48%" }}>
          <Bar w="85%" h={10} c={p.fg} r={3} />
          <Bar w="65%" h={10} c={p.fg} r={3} />
          <Bar w="50%" h={4} c={p.muted} />
          <div className="mt-[6px]" style={{ width: 42, height: 13, borderRadius: 99, background: p.accent }} />
        </div>
        <div
          style={{
            width: "45%", height: 92, borderRadius: 10,
            background: `linear-gradient(${140 + (seed % 60)}deg, ${p.accent}, ${p.accent2})`,
            boxShadow: `0 12px 30px ${p.accent}44`,
          }}
        />
      </div>
    </div>
  );
}

const THEMES = [AuroraHero, Editorial, Dashboard, Product, Neon, GridThree, PlayBg, Split];

export function MiniSite({ name }: { name: string }) {
  const seed = hashCode(name);
  const Theme = THEMES[seed % THEMES.length];
  const pool = Theme === Editorial || Theme === Product ? LIGHT : DARK;
  const p = pool[seed % pool.length];
  return (
    <div className="absolute inset-0 overflow-hidden select-none" aria-hidden>
      <Theme p={p} seed={seed >> 3} />
      <div className="absolute inset-0 pointer-events-none" style={{
        background: 'linear-gradient(105deg, transparent 40%, rgba(255,255,255,0.03) 45%, rgba(255,255,255,0.06) 50%, transparent 55%)',
        animation: 'shimmer-move 4s ease-in-out infinite',
      }} />
    </div>
  );
}
