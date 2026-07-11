import { useEffect, useRef } from 'react';

export function useScrollReveal(threshold = 0.1) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('animate-in');
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold }
    );

    const children = el.querySelectorAll('.scroll-reveal');
    if (children.length > 0) {
      children.forEach((child) => observer.observe(child));
    } else {
      observer.observe(el);
    }

    return () => observer.disconnect();
  }, [threshold]);

  return ref;
}
