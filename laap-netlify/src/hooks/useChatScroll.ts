import { useEffect, useRef, useState } from 'react';

interface UseChatScrollOptions {
  dependency: unknown;
  smooth?: boolean;
  threshold?: number;
}

export function useChatScroll<T extends HTMLElement>(options: UseChatScrollOptions) {
  const containerRef = useRef<T>(null);
  const [isAtBottom, setIsAtBottom] = useState(true);
  const userScrolledRef = useRef(false);

  const { dependency, smooth = true, threshold = 80 } = options;

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const scrollToBottom = () => {
      el.scrollTo({
        top: el.scrollHeight,
        behavior: smooth ? 'smooth' : 'auto',
      });
    };

    if (isAtBottom || !userScrolledRef.current) {
      const timeoutId = setTimeout(scrollToBottom, 30);
      return () => clearTimeout(timeoutId);
    }
  }, [dependency, smooth, isAtBottom]);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const handleScroll = () => {
      userScrolledRef.current = true;
      const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
      setIsAtBottom(distanceFromBottom <= threshold);
    };

    el.addEventListener('scroll', handleScroll, { passive: true });
    return () => el.removeEventListener('scroll', handleScroll);
  }, [threshold]);

  function scrollToBottom(force = false) {
    const el = containerRef.current;
    if (!el) return;
    if (force || isAtBottom) {
      el.scrollTo({ top: el.scrollHeight, behavior: smooth ? 'smooth' : 'auto' });
    }
  }

  return { containerRef, isAtBottom, scrollToBottom };
}
