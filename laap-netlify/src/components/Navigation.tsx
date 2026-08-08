import { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router';
import { useActiveSection } from '@/hooks/useActiveSection';
import { useGitHubStars } from '@/hooks/useGitHubStars';
import { Menu, X, User, Star } from 'lucide-react';
import { getCurrentUser, isLoggedIn, AUTH_CHANGE_EVENT } from '@/lib/auth';
import type { User as AuthUser } from '@/lib/auth';

const GITHUB_REPO = 'lorryjovens-hub/laap-AGI';

const HOME_ANCHORS = [
  { id: 'features', label: 'Features' },
  { id: 'innovation', label: 'Innovation' },
  { id: 'solutions', label: 'Solutions' },
  { id: 'foundation', label: 'Foundation' },
  { id: 'experience', label: 'Experience' },
  { id: 'architecture', label: 'Architecture' },
  { id: 'security', label: 'Trust' },
];

const ROUTE_LINKS = [
  { to: '/docs', label: 'Docs' },
  { to: '/news', label: 'News' },
  { to: '/downloads', label: 'Downloads' },
  { to: '/community', label: 'Community' },
  { to: '/studio', label: 'Studio' },
];

export default function Navigation() {
  const location = useLocation();
  const navigate = useNavigate();
  const isHome = location.pathname === '/';
  const activeSection = useActiveSection();
  const stars = useGitHubStars(GITHUB_REPO);

  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [loggedIn, setLoggedIn] = useState(isLoggedIn());
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    let mounted = true;

    async function sync() {
      const current = await getCurrentUser();
      if (mounted) {
        setLoggedIn(!!current);
        setUser(current);
      }
    }

    sync();
    window.addEventListener(AUTH_CHANGE_EVENT, sync);
    return () => {
      mounted = false;
      window.removeEventListener(AUTH_CHANGE_EVENT, sync);
    };
  }, []);

  useEffect(() => {
    function onScroll() {
      setScrolled(window.scrollY > 80);
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  function scrollTo(id: string) {
    if (!isHome) {
      navigate(`/#${id}`);
      return;
    }
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
      setMobileOpen(false);
    }
  }

  function scrollToTop() {
    if (!isHome) {
      navigate('/');
      return;
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
    setMobileOpen(false);
  }

  function isAnchorActive(id: string) {
    return isHome && activeSection === id;
  }

  function isRouteActive(path: string) {
    if (path === '/docs') return location.pathname.startsWith('/docs');
    if (path === '/news') return location.pathname.startsWith('/news');
    return location.pathname === path;
  }

  return (
    <>
      <nav
        className={`fixed top-0 left-0 right-0 z-50 h-20 flex items-center transition-all duration-500 ${
          scrolled
            ? 'bg-laap-bg-primary/85 backdrop-blur-[16px] border-b border-laap-border'
            : 'bg-transparent'
        }`}
      >
        <div className="w-full max-w-[1280px] mx-auto px-6 flex items-center justify-between">
          {/* Logo */}
          <button
            onClick={scrollToTop}
            className="flex items-center gap-2.5 group"
          >
            <img
              src="/assets/laap-logo.jpg"
              alt="LAAP"
              className="h-8 w-auto object-contain rounded-sm"
            />
            <span className="w-1.5 h-1.5 rounded-full bg-laap-gold animate-pulse-glow" />
          </button>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-10">
            {HOME_ANCHORS.map((item) => (
              <button
                key={item.id}
                onClick={() => scrollTo(item.id)}
                className="relative text-[13px] font-medium tracking-wide uppercase transition-colors duration-200 hover:text-white group"
                style={{ color: isAnchorActive(item.id) ? '#ffffff' : '#9ca3af' }}
              >
                {item.label}
                <span
                  className={`absolute -bottom-1 left-0 h-[1px] bg-laap-gold transition-all duration-300 ${
                    isAnchorActive(item.id) ? 'w-full' : 'w-0 group-hover:w-full'
                  }`}
                />
              </button>
            ))}
            {ROUTE_LINKS.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className={`relative text-[13px] font-medium tracking-wide uppercase transition-colors duration-200 hover:text-white group ${
                  isRouteActive(item.to) ? 'text-white' : 'text-laap-text-secondary'
                }`}
              >
                {item.label}
                <span
                  className={`absolute -bottom-1 left-0 h-[1px] bg-laap-gold transition-all duration-300 ${
                    isRouteActive(item.to) ? 'w-full' : 'w-0 group-hover:w-full'
                  }`}
                />
              </Link>
            ))}
          </div>

          {/* CTA + Auth + Mobile toggle */}
          <div className="flex items-center gap-4">
            <a
              href={`https://github.com/${GITHUB_REPO}`}
              target="_blank"
              rel="noopener noreferrer"
              className="hidden sm:inline-flex items-center gap-2 px-5 py-2.5 text-[13px] tracking-wide text-white border border-laap-border rounded-sm transition-all duration-200 hover:border-laap-gold hover:text-laap-gold"
            >
              GitHub
              {stars !== null && (
                <span className="inline-flex items-center gap-1 text-laap-gold">
                  <Star size={12} fill="currentColor" />
                  {stars.toLocaleString()}
                </span>
              )}
            </a>

            {loggedIn ? (
              <Link
                to="/studio"
                className="hidden sm:inline-flex items-center gap-2 px-5 py-2.5 text-[13px] tracking-wide text-laap-gold border border-laap-gold/40 rounded-sm transition-all duration-200 hover:bg-laap-gold/10"
              >
                <User size={15} />
                <span className="max-w-[80px] truncate">{user?.username || 'Studio'}</span>
              </Link>
            ) : (
              <Link
                to="/auth"
                className="hidden sm:inline-flex items-center px-5 py-2.5 text-[13px] tracking-wide text-laap-bg-primary bg-laap-gold rounded-sm transition-all duration-200 hover:bg-laap-gold-light"
              >
                登录
              </Link>
            )}

            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="md:hidden text-white p-2 hover:text-laap-gold transition-colors"
            >
              {mobileOpen ? <X size={22} /> : <Menu size={22} />}
            </button>
          </div>
        </div>
      </nav>

      {/* Mobile Menu */}
      {mobileOpen && (
        <div className="fixed inset-0 z-[60] bg-laap-bg-primary/98 backdrop-blur-xl flex flex-col items-center justify-center gap-8 md:hidden">
          <button
            onClick={() => setMobileOpen(false)}
            className="absolute top-6 right-6 text-white p-2 hover:text-laap-gold transition-colors"
          >
            <X size={26} />
          </button>

          <button
            onClick={scrollToTop}
            className="font-display text-3xl text-white hover:text-laap-gold transition-colors"
          >
            Home
          </button>

          {HOME_ANCHORS.map((item) => (
            <button
              key={item.id}
              onClick={() => scrollTo(item.id)}
              className="font-display text-3xl text-white hover:text-laap-gold transition-colors"
            >
              {item.label}
            </button>
          ))}

          {ROUTE_LINKS.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              onClick={() => setMobileOpen(false)}
              className={`font-display text-3xl transition-colors ${
                isRouteActive(item.to) ? 'text-laap-gold' : 'text-white hover:text-laap-gold'
              }`}
            >
              {item.label}
            </Link>
          ))}

          <div className="flex flex-col items-center gap-4 mt-4">
            <a
              href={`https://github.com/${GITHUB_REPO}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-8 py-3 text-white border border-laap-gold rounded-sm hover:bg-laap-gold hover:text-laap-bg-primary transition-all"
            >
              GitHub
              {stars !== null && (
                <span className="inline-flex items-center gap-1">
                  <Star size={14} fill="currentColor" />
                  {stars.toLocaleString()}
                </span>
              )}
            </a>
            {loggedIn ? (
              <Link
                to="/studio"
                onClick={() => setMobileOpen(false)}
                className="px-8 py-3 text-laap-gold border border-laap-gold/40 rounded-sm hover:bg-laap-gold/10 transition-all"
              >
                {user?.username || 'Studio'}
              </Link>
            ) : (
              <Link
                to="/auth"
                onClick={() => setMobileOpen(false)}
                className="px-8 py-3 text-laap-bg-primary bg-laap-gold rounded-sm hover:bg-laap-gold-light transition-all"
              >
                登录 / 注册
              </Link>
            )}
          </div>
        </div>
      )}
    </>
  );
}
