import { useState } from "react";
import { Copy, Check, Lock, X, ExternalLink } from "lucide-react";
import { MiniSite } from "@/components/MiniSite";
import type { CardType } from "@/data/cards";
import { getPreviewUrl, getGeneratorUrl } from "@/data/cards";

export function PromptCard({ card }: { card: CardType }) {
  const [copied, setCopied] = useState(false);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewLoaded, setPreviewLoaded] = useState(false);

  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation();
    const text = `Design a premium ${card.category.toLowerCase()} called "${card.name}" — dark editorial layout, bold typography, smooth scroll animations.`;
    navigator.clipboard?.writeText(text).catch(() => {});
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  };

  const handleGenerate = (e: React.MouseEvent) => {
    e.stopPropagation();
    window.open(getGeneratorUrl(card), "_blank");
  };

  const handleCardClick = () => {
    setPreviewOpen(true);
    setPreviewLoaded(false);
  };

  const previewUrl = getPreviewUrl(card);

  return (
    <>
      <div className="bg-card rounded-3xl overflow-visible card-hover flex flex-col cursor-pointer group"
           onClick={handleCardClick}>
        <div className="relative w-full shrink-0 rounded-xl overflow-hidden mb-3 aspect-[4/3]">
          <div className="absolute inset-0 bg-secondary overflow-hidden">
            <div className="absolute inset-0 -translate-x-full animate-shimmer bg-gradient-to-r from-transparent via-white/[0.04] to-transparent" />
          </div>
          <MiniSite name={card.name} />
          <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-all duration-300 flex items-center justify-center">
            <span className="opacity-0 group-hover:opacity-100 transition-opacity duration-300 text-white text-sm font-medium px-4 py-2 rounded-full bg-white/20 backdrop-blur-sm">
              <ExternalLink size={14} className="inline mr-1" /> Click to preview
            </span>
          </div>
        </div>

        <div className="flex items-center justify-between gap-2 px-4 pb-4">
          <div className="min-w-0">
            <h3 className="text-foreground font-bold text-lg truncate">{card.name}</h3>
            <p className="text-muted-foreground text-sm">{card.category}</p>
          </div>
          {card.premium ? (
            <button onClick={(e) => e.stopPropagation()}
              className="flex items-center gap-1.5 bg-secondary hover:bg-accent text-muted-foreground hover:text-foreground px-3 py-2 rounded-xl text-sm font-medium transition-colors shrink-0">
              <Lock size={14} /> Premium
            </button>
          ) : (
            <div className="flex items-center gap-2">
              <button onClick={handleCopy}
                className="flex items-center gap-1.5 bg-secondary hover:bg-green-500/20 text-muted-foreground hover:text-green-400 px-3 py-2 rounded-xl text-sm font-medium transition-colors shrink-0">
                {copied ? <Check size={14} className="text-green-400" /> : <Copy size={14} />}
                {copied ? "Copied" : "Copy"}
              </button>
              <button onClick={handleGenerate}
                className="flex items-center gap-1.5 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-400 hover:to-purple-400 text-white px-3 py-2 rounded-xl text-sm font-medium transition-all shrink-0 shadow-lg shadow-blue-500/20">
                <span>⚡</span> Generate
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Preview Modal */}
      {previewOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
             onClick={() => setPreviewOpen(false)}>
          <div className="relative w-full max-w-6xl h-[90vh] bg-[#0a0a0a] rounded-2xl overflow-hidden border border-white/10 shadow-2xl"
               onClick={(e) => e.stopPropagation()}>
            <div className="absolute top-0 left-0 right-0 z-10 flex items-center justify-between px-4 py-3 bg-gradient-to-b from-black/60 to-transparent">
              <div className="flex items-center gap-3">
                <span className="text-white text-sm font-medium">{card.name}</span>
                <span className="text-white/40 text-xs px-2 py-0.5 rounded-full bg-white/10">{card.category}</span>
              </div>
              <div className="flex items-center gap-2">
                <button onClick={() => window.open(getGeneratorUrl(card), '_blank')}
                  className="flex items-center gap-1.5 px-4 py-1.5 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 text-white text-xs font-semibold hover:brightness-110 transition">
                  ⚡ Generate Yours
                </button>
                <button onClick={() => setPreviewOpen(false)}
                  className="p-1.5 rounded-full bg-white/10 text-white/60 hover:bg-white/20 hover:text-white transition">
                  <X size={16} />
                </button>
              </div>
            </div>
            {!previewLoaded && (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-6 h-6 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
              </div>
            )}
            <iframe
              src={previewUrl}
              className="w-full h-full border-0"
              onLoad={() => setPreviewLoaded(true)}
              title={card.name}
            />
          </div>
        </div>
      )}
    </>
  );
}
