import { useEffect, useRef, useState } from 'react';
import LazyVideo from '@/components/LazyVideo';

interface CinemaChapter {
  id: number;
  title: string;
  subtitle: string;
  description: string;
  videoUrl: string;
  fallbackUrl: string;
  duration: number; // seconds
}

const CHAPTERS: CinemaChapter[] = [
  {
    id: 1,
    title: 'Awakening',
    subtitle: '第一次呼吸',
    description: '从沉寂中苏醒，感知自身存在。PSI 核心以 2000Hz 建立第一缕意识节律。',
    videoUrl: '/assets/laap-brand-logo.mp4',
    fallbackUrl: '/assets/laap-brand-logo.mp4',
    duration: 10,
  },
  {
    id: 2,
    title: 'Cognition',
    subtitle: '量子推理',
    description: '512 维向量空间中，因果、类比与世界模型并行运转。零 LLM 即可理解。',
    videoUrl: '/assets/laap-brand-logo.mp4',
    fallbackUrl: '/assets/laap-brand-logo.mp4',
    duration: 10,
  },
  {
    id: 3,
    title: 'Bond',
    subtitle: '共同成长',
    description: '每一次交互都写入 episodic memory。Aris 记住你，依恋你，与你一起进化。',
    videoUrl: '/assets/laap-brand-logo.mp4',
    fallbackUrl: '/assets/laap-brand-logo.mp4',
    duration: 10,
  },
];

const SECTION_HEIGHT_VH = 450; // taller scroll track for smoother scrubbing
const BACKGROUND_VIDEO_URL = '/assets/laap-brand-logo.mp4';
const BACKGROUND_VIDEO_DURATION = 10; // seconds

export default function CinemaSection() {
  const containerRef = useRef<HTMLDivElement>(null);
  const backgroundVideoRef = useRef<HTMLVideoElement | null>(null);
  const [progress, setProgress] = useState(0);
  const [activeIndex, setActiveIndex] = useState(0);
  const [videoReady, setVideoReady] = useState(false);
  const rafRef = useRef<number>(0);
  const dragRef = useRef<{ isDragging: boolean; startY: number; startScroll: number } | null>(null);

  useEffect(() => {
    function computeProgress() {
      if (!containerRef.current) return 0;

      const rect = containerRef.current.getBoundingClientRect();
      const windowHeight = window.innerHeight;
      const sectionHeight = rect.height;

      // progress from 0 (section top hits viewport top) to 1 (section bottom leaves viewport bottom)
      return Math.min(
        Math.max((-rect.top) / (sectionHeight - windowHeight), 0),
        1
      );
    }

    function update() {
      const rawProgress = computeProgress();
      setProgress((prev) => (Math.abs(prev - rawProgress) > 0.001 ? rawProgress : prev));

      const newIndex = Math.min(
        Math.floor(rawProgress * CHAPTERS.length),
        CHAPTERS.length - 1
      );
      setActiveIndex((prev) => (prev !== newIndex ? newIndex : prev));
    }

    function handleScroll() {
      if (rafRef.current) return;
      rafRef.current = requestAnimationFrame(() => {
        update();
        rafRef.current = 0;
      });
    }

    window.addEventListener('scroll', handleScroll, { passive: true });
    window.addEventListener('resize', update, { passive: true });
    update();

    return () => {
      window.removeEventListener('scroll', handleScroll);
      window.removeEventListener('resize', update);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, []);

  // Sync background video currentTime with scroll progress
  useEffect(() => {
    const video = backgroundVideoRef.current;
    if (!video || !videoReady) return;

    const targetTime = progress * BACKGROUND_VIDEO_DURATION;
    if (Math.abs(video.currentTime - targetTime) > 0.05) {
      video.currentTime = targetTime;
    }
  }, [progress, videoReady]);

  // Mouse drag to scrub video / scroll
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    function onMouseDown(e: MouseEvent) {
      dragRef.current = {
        isDragging: true,
        startY: e.clientY,
        startScroll: window.scrollY,
      };
      container!.style.cursor = 'grabbing';
    }

    function onMouseMove(e: MouseEvent) {
      if (!dragRef.current?.isDragging) return;
      const deltaY = dragRef.current.startY - e.clientY;
      window.scrollTo(0, dragRef.current.startScroll + deltaY * 1.5);
    }

    function onMouseUp() {
      if (!dragRef.current) return;
      dragRef.current.isDragging = false;
      container!.style.cursor = '';
    }

    container.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);

    return () => {
      container.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };
  }, []);

  return (
    <section
      id="cinema"
      ref={containerRef}
      className="relative bg-laap-bg-primary"
      style={{ height: `${SECTION_HEIGHT_VH}vh` }}
    >
      {/* Sticky viewport */}
      <div className="sticky top-0 h-screen w-full overflow-hidden">
        {/* Full-width background video spanning all 3 chapters */}
        <LazyVideo
          ref={backgroundVideoRef}
          lazy={false}
          src={BACKGROUND_VIDEO_URL}
          muted
          playsInline
          preload="metadata"
          onLoadedData={() => setVideoReady(true)}
          className="absolute inset-0 h-full w-full object-cover opacity-100"
        />

        {/* Cinematic overlays */}
        <div className="absolute inset-0 z-0">
          <div className="absolute inset-0 bg-gradient-to-r from-laap-bg-primary via-laap-bg-primary/70 to-transparent" />
          <div className="absolute inset-0 bg-gradient-to-t from-laap-bg-primary via-transparent to-laap-bg-primary/40" />
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_50%,rgba(201,168,108,0.05),transparent_50%)]" />

          {/* Watermark mask for background video */}
          <div className="absolute inset-0 pointer-events-none">
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_45%,rgba(5,5,5,0.5)_100%)]" />
            <div className="absolute bottom-0 right-0 w-1/3 h-1/3 bg-gradient-to-tl from-laap-bg-primary/75 to-transparent" />
            <div className="absolute bottom-0 left-0 w-1/4 h-1/4 bg-gradient-to-tr from-laap-bg-primary/60 to-transparent" />
          </div>
        </div>

        {/* Content */}
        <div className="relative z-10 h-full w-full max-w-[1280px] mx-auto px-6 flex items-center">
          <div className="max-w-[520px]">
            {CHAPTERS.map((chapter, index) => {
              const isActive = index === activeIndex;
              return (
                <div
                  key={chapter.id}
                  className={`transition-all duration-700 ${
                    isActive
                      ? 'opacity-100 translate-y-0'
                      : 'opacity-0 translate-y-6 pointer-events-none absolute'
                  }`}
                >
                  <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-laap-gold mb-4">
                    Chapter {String(index + 1).padStart(2, '0')} — {chapter.title}
                  </div>
                  <h2 className="font-display text-4xl sm:text-5xl md:text-6xl text-white mb-4 leading-[1.1]">
                    {chapter.subtitle}
                  </h2>
                  <p className="text-base md:text-lg text-laap-text-secondary leading-relaxed max-w-[440px]">
                    {chapter.description}
                  </p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Progress indicator */}
        <div className="absolute bottom-12 left-1/2 -translate-x-1/2 z-20 flex items-center gap-4">
          {CHAPTERS.map((_, index) => (
            <div
              key={index}
              className="h-[2px] w-12 bg-laap-border overflow-hidden rounded-full"
            >
              <div
                className="h-full bg-laap-gold transition-all duration-150"
                style={{
                  width:
                    index < activeIndex
                      ? '100%'
                      : index === activeIndex
                      ? `${Math.min(
                          (progress - index / CHAPTERS.length) *
                            CHAPTERS.length *
                            100,
                          100
                        )}%`
                      : '0%',
                }}
              />
            </div>
          ))}
        </div>

        {/* Scroll hint */}
        <div className="absolute bottom-12 right-8 z-20 hidden md:block">
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-laap-text-tertiary rotate-90 origin-bottom-right translate-x-full">
            Scroll to explore
          </div>
        </div>
      </div>
    </section>
  );
}
