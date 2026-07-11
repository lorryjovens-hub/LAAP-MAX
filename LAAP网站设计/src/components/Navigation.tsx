import { useState, useEffect } from 'react';
import { useActiveSection } from '@/hooks/useActiveSection';
import { Menu, X } from 'lucide-react';

const NAV_ITEMS = [
  { id: 'features', label: 'Features' },
  { id: 'experience', label: 'Experience' },
  { id: 'architecture', label: 'Architecture' },
  { id: 'docs', label: 'Docs' },
  { id: 'security', label: 'Trust' },
];

export default function Navigation() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const activeSection = useActiveSection();

  useEffect(() => {
    function onScroll() {
      setScrolled(window.scrollY > 100);
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  function scrollTo(id: string) {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
      setMobileOpen(false);
    }
  }

  function scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    setMobileOpen(false);
  }

  return (
    <>
      <nav
        className={`fixed top-0 left-0 right-0 z-50 h-16 flex items-center transition-all duration-300 ${
          scrolled
            ? 'bg-[rgba(10,10,10,0.8)] backdrop-blur-[12px] border-b border-[#27272a]'
            : 'bg-transparent'
        }`}
      >
        <div className="w-full max-w-[1200px] mx-auto px-6 flex items-center justify-between">
          {/* Logo */}
          <button
            onClick={scrollToTop}
            className="flex items-center gap-2 group"
          >
            <span
              className="text-white font-medium text-base tracking-[0.1em]"
              style={{ fontFamily: '"Inter", sans-serif' }}
            >
              LAAP
            </span>
            <span className="w-1 h-1 rounded-full bg-laap-emerald animate-pulse-glow" />
          </button>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-8">
            {NAV_ITEMS.map((item) => (
              <button
                key={item.id}
                onClick={() => scrollTo(item.id)}
                className="relative text-[13px] transition-colors duration-150 hover:text-white"
                style={{
                  color:
                    activeSection === item.id ? '#ffffff' : '#a1a1aa',
                }}
              >
                {item.label}
                {activeSection === item.id && (
                  <span className="absolute -bottom-1 left-0 right-0 h-[2px] bg-laap-cyan rounded-full" />
                )}
              </button>
            ))}
          </div>

          {/* CTA + Mobile toggle */}
          <div className="flex items-center gap-4">
            <a
              href="https://github.com/lorryjovens-hub/LAAP-Living-Agent-Application-Protocol-"
              target="_blank"
              rel="noopener noreferrer"
              className="hidden sm:inline-flex items-center px-5 py-2 text-sm text-white bg-laap-bg-secondary border border-[#27272a] rounded-lg transition-all duration-150 hover:scale-[0.98]"
            >
              GitHub
            </a>

            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="md:hidden text-white p-1"
            >
              {mobileOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>
      </nav>

      {/* Mobile Menu */}
      {mobileOpen && (
        <div className="fixed inset-0 z-[60] bg-[rgba(10,10,10,0.98)] flex flex-col items-center justify-center gap-8 md:hidden">
          <button
            onClick={() => setMobileOpen(false)}
            className="absolute top-5 right-6 text-white p-1"
          >
            <X size={28} />
          </button>
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              onClick={() => scrollTo(item.id)}
              className="text-2xl font-medium text-white"
            >
              {item.label}
            </button>
          ))}
          <a
            href="https://github.com/lorryjovens-hub/LAAP-Living-Agent-Application-Protocol-"
            target="_blank"
            rel="noopener noreferrer"
            className="mt-4 px-6 py-3 text-lg text-white border border-[#27272a] rounded-lg"
          >
            GitHub
          </a>
        </div>
      )}
    </>
  );
}
