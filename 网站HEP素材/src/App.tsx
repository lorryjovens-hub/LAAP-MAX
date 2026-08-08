import { useMemo, useState } from "react";
import { Navbar } from "@/sections/Navbar";
import { Hero } from "@/sections/Hero";
import { FilterBar, type TabKey, type PriceFilter } from "@/sections/FilterBar";
import { PromptCard } from "@/components/PromptCard";
import { PromoCard, BackgroundsCell } from "@/sections/GridExtras";
import { BottomBanner, Footer } from "@/sections/Banner";
import { ALL_CARDS, hashCode, type CardType } from "@/data/cards";

function applyFilters(cards: CardType[], type: string, price: PriceFilter): CardType[] {
  return cards.filter((c) => {
    if (type !== "all" && c.category !== type) return false;
    if (price === "free" && c.premium) return false;
    if (price === "premium" && !c.premium) return false;
    return true;
  });
}

function applyTab(cards: CardType[], tab: TabKey): CardType[] {
  const arr = [...cards];
  if (tab === "popular") arr.sort((a, b) => hashCode(b.name) - hashCode(a.name));
  if (tab === "recent") arr.reverse();
  return arr;
}

export default function App() {
  const [tab, setTab] = useState<TabKey>("featured");
  const [type, setType] = useState("all");
  const [price, setPrice] = useState<PriceFilter>("all");

  const cards = useMemo(() => applyTab(applyFilters(ALL_CARDS, type, price), tab), [tab, type, price]);

  // first 11 cards -> promo inserted at slot 2; then BACKGROUNDS spanning cell; then the rest
  const first = cards.slice(0, 11);
  const rest = cards.slice(11);

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="max-w-[1440px] mx-auto px-6 sm:px-8">
        <Hero />
        <FilterBar tab={tab} setTab={setTab} type={type} setType={setType} price={price} setPrice={setPrice} />

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pb-6 [&>*]:relative [&>*]:z-0">
          {first.slice(0, 2).map((c) => (
            <PromptCard key={c.id} card={c} />
          ))}
          <PromoCard />
          {first.slice(2).map((c) => (
            <PromptCard key={c.id} card={c} />
          ))}
          <BackgroundsCell />
          {rest.map((c) => (
            <PromptCard key={c.id} card={c} />
          ))}
        </div>

        <BottomBanner />
        <Footer />
      </div>
    </div>
  );
}
