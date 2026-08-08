import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router';
import { ChevronLeft, ChevronRight, Headphones, Pause, Play } from 'lucide-react';

interface PodcastEpisode {
  id: string;
  title: string;
  description: string;
  cover: string;
  audio: string;
}

const EPISODES: PodcastEpisode[] = [
  {
    id: 'episode-1',
    title: 'LAAP：揭秘 AGI 数字生命体架构',
    description: '深入解析 LAAP 意识工程与 PSI-RSI 双重驱动的数字生命体架构。',
    cover: '/assets/LAAP揭秘AGI数字生命体架构.jpg',
    audio: '/assets/LAAP：揭秘AGI数字生命体架构.mp3',
  },
  {
    id: 'episode-2',
    title: 'LAAP-Hermes：AI 学会思考的突破',
    description: '探索 Hermes 认知架构如何赋予 AI 真正的反思与成长能力。',
    cover: '/assets/AI学会思考的突破.jpg',
    audio: '/assets/LAAP-Hermes：AI学会思考的突破.mp3',
  },
];

export default function PodcastPage() {
  const navigate = useNavigate();
  const [index, setIndex] = useState(0);
  const [playingId, setPlayingId] = useState<string | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const leftEpisode = EPISODES[index % EPISODES.length];
  const rightEpisode = EPISODES[(index + 1) % EPISODES.length];

  function prev() {
    setIndex((i) => (i - 1 + EPISODES.length) % EPISODES.length);
  }

  function next() {
    setIndex((i) => (i + 1) % EPISODES.length);
  }

  function togglePlay(id: string, src: string) {
    const audio = audioRef.current;
    if (!audio) return;

    if (playingId === id) {
      audio.pause();
      setPlayingId(null);
      return;
    }

    if (audio.src !== src) {
      audio.src = src;
      audio.load();
    }

    audio.play().then(() => {
      setPlayingId(id);
    }).catch(() => {
      setPlayingId(null);
    });
  }

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    function onTimeUpdate() {
      setCurrentTime(audio!.currentTime);
    }

    function onLoadedMetadata() {
      setDuration(audio!.duration || 0);
    }

    function onEnded() {
      setPlayingId(null);
      setCurrentTime(0);
    }

    audio.addEventListener('timeupdate', onTimeUpdate);
    audio.addEventListener('loadedmetadata', onLoadedMetadata);
    audio.addEventListener('ended', onEnded);

    return () => {
      audio.removeEventListener('timeupdate', onTimeUpdate);
      audio.removeEventListener('loadedmetadata', onLoadedMetadata);
      audio.removeEventListener('ended', onEnded);
    };
  }, []);

  return (
    <div className="min-h-screen bg-laap-bg-primary pt-32 pb-24">
      <div className="max-w-[1280px] mx-auto px-6">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-3 px-4 py-2 border border-laap-border rounded-full mb-6">
            <Headphones size={16} className="text-laap-gold" />
            <span className="font-mono text-[11px] uppercase tracking-[0.15em] text-laap-text-secondary">
              Podcast
            </span>
          </div>
          <h1 className="font-display text-4xl md:text-5xl text-white mb-4">LAAP 播客解析</h1>
          <p className="text-laap-text-secondary max-w-[600px] mx-auto">
            用声音走进 LAAP 的意识工程世界。左右切换手机框，点击播放即可收听解析。
          </p>
        </div>

        {/* Carousel */}
        <div className="flex items-center justify-center gap-6 md:gap-10">
          <CarouselButton direction="left" onClick={prev} />

          <div className="flex flex-col md:flex-row items-center justify-center gap-8 md:gap-12">
            <PhoneFrame
              episode={leftEpisode}
              isPlaying={playingId === leftEpisode.id}
              onTogglePlay={() => togglePlay(leftEpisode.id, leftEpisode.audio)}
            />
            <PhoneFrame
              episode={rightEpisode}
              isPlaying={playingId === rightEpisode.id}
              onTogglePlay={() => togglePlay(rightEpisode.id, rightEpisode.audio)}
            />
          </div>

          <CarouselButton direction="right" onClick={next} />
        </div>

        {/* Progress */}
        {playingId && (
          <div className="max-w-md mx-auto mt-12">
            <div className="flex items-center justify-between text-xs text-laap-text-tertiary mb-2">
              <span>{formatTime(currentTime)}</span>
              <span>{formatTime(duration)}</span>
            </div>
            <div className="h-1 bg-laap-border rounded-full overflow-hidden">
              <div
                className="h-full bg-laap-gold rounded-full transition-all"
                style={{ width: `${duration ? (currentTime / duration) * 100 : 0}%` }}
              />
            </div>
          </div>
        )}

        {/* Back to docs */}
        <div className="mt-16 text-center">
          <button
            onClick={() => navigate('/docs')}
            className="inline-flex items-center gap-2 px-6 py-3 text-sm text-laap-text-secondary border border-laap-border rounded-sm hover:border-laap-gold hover:text-laap-gold transition-colors"
          >
            返回文档中心
          </button>
        </div>
      </div>

      <audio ref={audioRef} preload="metadata" className="hidden" />
    </div>
  );
}

function PhoneFrame({
  episode,
  isPlaying,
  onTogglePlay,
}: {
  episode: PodcastEpisode;
  isPlaying: boolean;
  onTogglePlay: () => void;
}) {
  return (
    <div className="relative w-[260px] md:w-[300px] shrink-0">
      {/* Phone body */}
      <div className="relative rounded-[2.5rem] border-[6px] border-laap-border bg-laap-bg-secondary shadow-2xl overflow-hidden">
        {/* Notch */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-28 h-6 bg-laap-border rounded-b-2xl z-20" />

        {/* Screen */}
        <div className="relative aspect-[9/19] bg-laap-bg-primary overflow-hidden">
          <img
            src={episode.cover}
            alt={episode.title}
            className="absolute inset-0 w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-laap-bg-primary via-laap-bg-primary/40 to-transparent" />

          {/* Content overlay */}
          <div className="absolute inset-x-0 bottom-0 p-5 z-10">
            <div className="font-mono text-[10px] text-laap-gold uppercase tracking-wider mb-2">
              LAAP Podcast
            </div>
            <h3 className="font-display text-lg text-white leading-snug mb-2 line-clamp-2">
              {episode.title}
            </h3>
            <p className="text-[11px] text-laap-text-secondary line-clamp-2 mb-4">
              {episode.description}
            </p>

            <button
              onClick={onTogglePlay}
              className={`w-full flex items-center justify-center gap-2 py-3 rounded-full text-sm font-medium transition-all ${
                isPlaying
                  ? 'bg-white text-laap-bg-primary'
                  : 'bg-laap-gold text-laap-bg-primary hover:bg-laap-gold-light'
              }`}
            >
              {isPlaying ? <Pause size={16} /> : <Play size={16} fill="currentColor" />}
              {isPlaying ? '暂停播放' : '点击播放'}
            </button>
          </div>
        </div>
      </div>

      {/* Side button detail */}
      <div className="absolute top-24 -right-[8px] w-[3px] h-10 bg-laap-border rounded-r-sm" />
      <div className="absolute top-40 -right-[8px] w-[3px] h-14 bg-laap-border rounded-r-sm" />
    </div>
  );
}

function CarouselButton({ direction, onClick }: { direction: 'left' | 'right'; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="hidden md:flex items-center justify-center w-12 h-12 rounded-full border border-laap-border text-laap-text-secondary hover:text-white hover:border-laap-gold hover:bg-laap-bg-secondary transition-colors"
      aria-label={direction === 'left' ? '上一组' : '下一组'}
    >
      {direction === 'left' ? <ChevronLeft size={22} /> : <ChevronRight size={22} />}
    </button>
  );
}

function formatTime(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) return '00:00';
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}
