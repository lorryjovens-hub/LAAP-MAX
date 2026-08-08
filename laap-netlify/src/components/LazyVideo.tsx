import {
  useEffect,
  useState,
  useRef,
  forwardRef,
  useImperativeHandle,
  type ReactEventHandler,
} from 'react';

interface LazyVideoProps extends React.VideoHTMLAttributes<HTMLVideoElement> {
  src: string;
  className?: string;
  lazy?: boolean;
  rootMargin?: string;
  retryCount?: number;
}

const LazyVideo = forwardRef<HTMLVideoElement, LazyVideoProps>(
  (
    {
      src,
      className = '',
      lazy = false,
      rootMargin = '200px',
      retryCount = 2,
      poster,
      autoPlay,
      muted,
      loop,
      playsInline,
      preload = 'metadata',
      onError,
      children,
      ...rest
    },
    forwardedRef
  ) => {
    const localRef = useRef<HTMLVideoElement>(null);
    const [shouldLoad, setShouldLoad] = useState(!lazy);
    const [errorCount, setErrorCount] = useState(0);

    useImperativeHandle(forwardedRef, () => localRef.current!);

    useEffect(() => {
      if (!lazy) return;
      const el = localRef.current;
      if (!el) return;

      const observer = new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting) {
            setShouldLoad(true);
            observer.disconnect();
          }
        },
        { rootMargin }
      );

      observer.observe(el);
      return () => observer.disconnect();
    }, [lazy, rootMargin]);

    const handleError: ReactEventHandler<HTMLVideoElement> = (e) => {
      if (errorCount < retryCount) {
        setErrorCount((c) => c + 1);
        const video = e.currentTarget;
        video.load();
        return;
      }
      onError?.(e);
    };

    return (
      <video
        ref={localRef}
        className={className}
        poster={poster}
        src={shouldLoad ? src : undefined}
        autoPlay={autoPlay}
        muted={muted}
        loop={loop}
        playsInline={playsInline}
        preload={preload}
        onError={handleError}
        {...rest}
      >
        {children}
      </video>
    );
  }
);

LazyVideo.displayName = 'LazyVideo';

export default LazyVideo;
