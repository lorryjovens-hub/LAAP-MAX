import { ArrowRight } from "lucide-react";

/** Layered gradient word: blurred glow copy behind + gradient text + noise */
function GradientWord({ word }: { word: string }) {
  return (
    <span className="relative inline-block">
      <span
        aria-hidden
        className="animate-gradient-shift gradient-glow absolute -inset-x-1 -inset-y-2 select-none"
      >
        {word}
      </span>
      <span className="animate-gradient-shift gradient-word relative">{word}</span>
      <span aria-hidden className="noise-overlay absolute -inset-1 rounded-lg pointer-events-none" />
    </span>
  );
}

export function Hero() {
  return (
    <header className="flex flex-col items-center pt-12 sm:pt-16 pb-10">
      {/* pill badge */}
      <span className="relative inline-flex items-center mb-2">
        <span className="px-3 py-[3px] rounded-full border border-blue-500/30 bg-blue-500/5 text-[10px] font-semibold tracking-[0.18em] uppercase bg-clip-text text-transparent bg-gradient-to-r from-blue-300 via-purple-400 to-rose-400">
          Zero-Token generation
        </span>
      </span>

      {/* headline */}
      <h1 className="text-[38px] sm:text-[48px] md:text-[56px] text-foreground font-black uppercase text-center mb-3 leading-[34px] sm:leading-[40px] md:leading-[46px] tracking-[-0.03em]">
        <span className="relative inline-block">
          LAAP HEP — Assemble
          <span aria-hidden className="noise-overlay absolute -inset-1 rounded-lg pointer-events-none" />
        </span>
        <br />
        <span className="relative inline-block">
          Don&#39;t <GradientWord word="generate" />
        </span>
      </h1>

      {/* subline */}
      <p className="text-neutral-400 text-base text-center max-w-[520px] leading-relaxed">
        Pick a style, paste your content, and get a complete website in milliseconds.
        No LLM calls. No waiting. Zero tokens.
      </p>

      {/* CTA */}
      <a
        href="/generator.html"
        className="mt-6 flex items-center justify-center gap-1 px-8 py-2 h-14 text-lg font-semibold rounded-full border-t-2 border-white cursor-pointer text-[#09090b] bg-gradient-to-b from-white via-white to-indigo-200 shadow-[0_10px_44px_-8px_rgba(199,210,254,0.55)] hover:brightness-105 transition"
      >
        Start Building <ArrowRight size={19} strokeWidth={2.4} />
      </a>
    </header>
  );
}
