import { Rocket } from "lucide-react";
import { MiniSite } from "@/components/MiniSite";

export function BottomBanner() {
  return (
    <div className="relative w-full p-6 sm:p-8 bg-neutral-800 rounded-2xl flex flex-col justify-center items-start gap-4 mb-8 overflow-hidden">
      {/* decorative tilted thumbnails on the right */}
      <div className="hidden md:block absolute right-10 top-1/2 -translate-y-1/2 pointer-events-none" aria-hidden>
        <div className="relative w-[300px] h-[190px]">
          <div className="absolute right-24 top-4 w-[170px] h-[128px] rounded-xl overflow-hidden rotate-[-8deg] border border-white/10 shadow-2xl opacity-90">
            <MiniSite name="banner deco one" />
          </div>
          <div className="absolute right-0 top-8 w-[170px] h-[128px] rounded-xl overflow-hidden rotate-[7deg] border border-white/10 shadow-2xl">
            <MiniSite name="banner deco two" />
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <span className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-500">
          <Rocket size={16} className="text-white" />
        </span>
        <span className="font-black italic tracking-tight text-foreground uppercase">
          LAAP HEP
        </span>
      </div>

      <h2 className="text-white text-2xl sm:text-3xl lg:text-4xl font-semibold leading-tight max-w-md">
        Zero-token website building.
        Just pick, paste, and ship.
      </h2>
      <p className="text-muted-foreground text-sm font-medium max-w-xl">
        "From blank paper to production-ready website — no LLM calls, no costs, no waiting."
      </p>
      <a
        href="/generator.html"
        className="w-fit px-7 py-4 bg-gradient-to-br from-blue-500 via-purple-400 to-pink-400 rounded-xl shadow-[inset_-4px_-4px_8px_0px_rgba(255,255,255,0.15),inset_4px_4px_4px_0px_rgba(255,255,255,0.15)] inline-flex text-foreground font-medium hover:brightness-110 transition"
      >
        Start Building
      </a>
    </div>
  );
}

export function Footer() {
  return (
      <footer className="border-t border-border py-8 mt-8 text-center text-sm text-muted-foreground">
      <p className="flex items-center justify-center gap-1.5">
        Built with LAAP HEP · Zero-Token
        <Rocket size={14} className="text-blue-400" />
      </p>
    </footer>
  );
}
