import { useEffect, useRef, useState } from "react";
import { ChevronDown, Check } from "lucide-react";
import { TYPE_OPTIONS } from "@/data/cards";

export type TabKey = "featured" | "popular" | "recent";
export type PriceFilter = "all" | "free" | "premium";

const TABS: Array<{ key: TabKey; label: string }> = [
  { key: "featured", label: "Featured" },
  { key: "popular", label: "Popular" },
  { key: "recent", label: "Recent" },
];

function Dropdown({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: Array<{ value: string; label: string }>;
  value: string;
  onChange: (v: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const close = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  const current = options.find((o) => o.value === value);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="inline-flex items-center justify-center gap-1.5 px-5 py-2 text-sm font-medium rounded-full overflow-hidden isolate hover:opacity-90 transition-opacity whitespace-nowrap bg-[#202020] text-white/72"
      >
        {value === options[0].value ? label : current?.label}
        <ChevronDown size={14} className={`transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      {open && (
        <div className="absolute right-0 mt-2 w-44 rounded-xl border border-white/10 bg-[#1e1e1e] shadow-[0_16px_40px_rgba(0,0,0,0.5)] p-1 z-40 max-h-72 overflow-auto scrollbar-none">
          {options.map((o) => (
            <button
              key={o.value}
              onClick={() => {
                onChange(o.value);
                setOpen(false);
              }}
              className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors ${
                o.value === value
                  ? "text-foreground bg-white/10"
                  : "text-white/65 hover:text-foreground hover:bg-white/5"
              }`}
            >
              {o.label}
              {o.value === value && <Check size={14} />}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export function FilterBar({
  tab,
  setTab,
  type,
  setType,
  price,
  setPrice,
}: {
  tab: TabKey;
  setTab: (t: TabKey) => void;
  type: string;
  setType: (t: string) => void;
  price: PriceFilter;
  setPrice: (p: PriceFilter) => void;
}) {
  return (
    <div className="flex flex-row items-center justify-between gap-2 mb-6 flex-wrap">
      {/* segmented tabs */}
      <div className="relative inline-flex items-center p-1 rounded-full border border-white/10">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`relative px-5 py-1.5 text-sm font-medium rounded-full transition-colors whitespace-nowrap ${
              tab === t.key ? "bg-[#202020] text-white" : "text-white/72 hover:text-white"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* dropdowns */}
      <div className="flex items-center gap-2">
        <Dropdown
          label="Type"
          value={type}
          onChange={setType}
          options={TYPE_OPTIONS.map((t) => ({
            value: t === "All Types" ? "all" : t,
            label: t,
          }))}
        />
        <Dropdown
          label="Pricing"
          value={price}
          onChange={(v) => setPrice(v as PriceFilter)}
          options={[
            { value: "all", label: "All Pricing" },
            { value: "free", label: "Free" },
            { value: "premium", label: "Premium" },
          ]}
        />
      </div>
    </div>
  );
}
