import { Rocket } from "lucide-react";

/** In-grid academy promo card (sits in the first row, 3rd slot) */
export function PromoCard() {
  return (
    <a
      href="#"
      className="h-full flex flex-col items-start justify-between p-6 bg-neutral-900 rounded-2xl border border-border hover:border-muted-foreground/40 card-hover transition-colors"
    >
      <div className="flex items-center gap-2">
        <span className="flex items-center justify-center w-7 h-7 rounded-lg bg-gradient-to-br from-orange-400 to-rose-500">
          <Rocket size={15} className="text-white" />
        </span>
        <span className="font-black italic tracking-tight text-foreground text-sm uppercase">
          Prompt Academy
        </span>
      </div>
      <div>
        <h3 className="text-foreground font-bold text-2xl leading-tight mb-2">
          Learn to design beautiful websites using AI tools.
        </h3>
        <p className="text-muted-foreground text-sm mb-4">Master AI-powered design</p>
        <span className="inline-flex px-4 py-2.5 rounded-full bg-white text-[#09090b] text-sm font-medium hover:bg-white/90 transition-colors">
          Start Learning for Free
        </span>
      </div>
    </a>
  );
}

/** Full-width spanning cell: BACKGROUNDS header inside the grid */
export function BackgroundsCell() {
  return (
    <div className="col-span-1 sm:col-span-2 row-span-2 bg-[#1a1a1a] rounded-3xl p-6 sm:p-8 flex flex-col justify-between min-h-[300px]">
      <span className="text-[11px] font-medium tracking-[0.22em] uppercase text-muted-foreground">
        Backgrounds
      </span>
      <div>
        <h2 className="text-foreground font-bold text-2xl leading-snug max-w-[380px] mb-4">
          Animated backgrounds built to convert, impress, and amaze.
        </h2>
        <a
          href="#"
          className="inline-flex px-4 py-2.5 rounded-full bg-white text-[#09090b] text-sm font-medium hover:bg-white/90 transition-colors"
        >
          Explore Videos
        </a>
      </div>
    </div>
  );
}
