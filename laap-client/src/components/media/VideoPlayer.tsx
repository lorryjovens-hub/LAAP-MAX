/**
 * VideoPlayer：原生 HTML5 视频播放器
 *
 * 默认加载项目规范视频，支持播放/暂停、静音、可拖动进度条与循环播放。
 * 当默认视频不存在或读取失败时，提供占位提示与本地文件选择。
 * 支持通过 src 属性指定路径：绝对本地路径、相对路径或 http(s) URL。
 */

import { useEffect, useRef, useState } from 'react'
import { Play, Pause, Volume2, VolumeX, Film } from 'lucide-react'
import { GlassPanel } from '../glass/GlassPanel'

const DEFAULT_VIDEO_PATH =
  'D:\\LAAP\\.trae\\specs\\integrate-aether-orchestration-into-laap\\互动视频.mp4'

export interface VideoPlayerProps {
  /** 视频路径：绝对本地路径、相对路径或 http(s) URL；不传则使用默认视频 */
  src?: string
}

function base64ToBlob(base64: string, type: string): Blob {
  const byteString = atob(base64)
  const array = new Uint8Array(byteString.length)
  for (let i = 0; i < byteString.length; i += 1) {
    array[i] = byteString.charCodeAt(i)
  }
  return new Blob([array], { type })
}

function formatTime(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function getFileNameFromPath(filePath: string): string {
  return filePath.split(/[/\\]/).pop() || '本地视频'
}

function resolveUrl(src: string): string {
  if (/^https?:\/\//i.test(src)) return src
  return new URL(src, window.location.href).href
}

function isAbsoluteLocalPath(src: string): boolean {
  // Windows 盘符路径，如 D:\... 或 D:/...
  if (/^[a-zA-Z]:[\\/]/.test(src)) return true
  // Unix / macOS 绝对路径
  if (src.startsWith('/')) return true
  return false
}

export function VideoPlayer({ src }: VideoPlayerProps = {}) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const objectUrlRef = useRef<string | null>(null)
  const [videoSrc, setVideoSrc] = useState<string | null>(null)
  const [fileName, setFileName] = useState<string>('')
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading')
  const [playing, setPlaying] = useState(false)
  const [muted, setMuted] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [seeking, setSeeking] = useState(false)

  const revokeCurrentUrl = () => {
    if (objectUrlRef.current) {
      URL.revokeObjectURL(objectUrlRef.current)
      objectUrlRef.current = null
    }
  }

  const loadDirectUrl = (url: string, name: string) => {
    revokeCurrentUrl()
    setVideoSrc(url)
    setFileName(name)
    setStatus('ready')
    setCurrentTime(0)
    setDuration(0)
    setPlaying(false)
  }

  const loadLocalFile = async (filePath: string) => {
    try {
      const desktop = window.desktop
      if (!desktop?.readVideoFile) {
        setStatus('error')
        return
      }
      const result = await desktop.readVideoFile(filePath)
      if (!result.exists || !result.data) {
        setStatus('error')
        return
      }
      revokeCurrentUrl()
      const blob = base64ToBlob(result.data, result.type || 'video/mp4')
      const url = URL.createObjectURL(blob)
      objectUrlRef.current = url
      setVideoSrc(url)
      setFileName(getFileNameFromPath(filePath))
      setStatus('ready')
      setCurrentTime(0)
      setDuration(0)
      setPlaying(false)
    } catch {
      setStatus('error')
    }
  }

  useEffect(() => {
    let mounted = true

    async function load() {
      const source = src ?? DEFAULT_VIDEO_PATH
      if (isAbsoluteLocalPath(source)) {
        await loadLocalFile(source)
      } else {
        const url = resolveUrl(source)
        const name = getFileNameFromPath(source)
        loadDirectUrl(url, name)
      }
    }

    load()

    return () => {
      mounted = false
      revokeCurrentUrl()
      // 仅用于避免未使用变量的 lint 警告
      void mounted
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [src])

  const togglePlay = () => {
    const video = videoRef.current
    if (!video) return
    if (video.paused) {
      video.play().catch(() => {})
    } else {
      video.pause()
    }
  }

  const toggleMute = () => {
    const video = videoRef.current
    if (!video) return
    video.muted = !video.muted
    setMuted(video.muted)
  }

  const handleTimeUpdate = () => {
    if (!seeking) {
      setCurrentTime(videoRef.current?.currentTime ?? 0)
    }
  }

  const handleLoadedMetadata = () => {
    setDuration(videoRef.current?.duration ?? 0)
  }

  const handleSeekChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = Number(e.target.value)
    setCurrentTime(value)
    if (videoRef.current) {
      videoRef.current.currentTime = value
    }
  }

  const handleSeekStart = () => setSeeking(true)
  const handleSeekEnd = () => setSeeking(false)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const url = URL.createObjectURL(file)
    loadDirectUrl(url, file.name)
    objectUrlRef.current = url
    e.target.value = ''
  }

  const handleSelectFile = async () => {
    try {
      const result = await window.desktop?.selectVideo()
      if (result?.filePath) {
        await loadLocalFile(result.filePath)
      }
    } catch {
      setStatus('error')
    }
  }

  if (status === 'error') {
    return (
      <GlassPanel
        className="p-6 flex flex-col items-center justify-center text-center gap-3"
        intensity="sm"
        radius="var(--laap-radius-md)"
      >
        <Film className="w-10 h-10 text-white/30" />
        <div>
          <p className="text-sm text-white/70">视频未能加载</p>
          <p className="text-xs text-white/40 mt-1 break-all">
            {src || DEFAULT_VIDEO_PATH}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleSelectFile}
            className="px-3 py-1.5 rounded-lg bg-white/[0.08] hover:bg-white/[0.12] text-xs text-white/80 transition-colors"
          >
            选择本地视频
          </button>
          <label className="px-3 py-1.5 rounded-lg bg-white/[0.08] hover:bg-white/[0.12] text-xs text-white/80 transition-colors cursor-pointer">
            浏览文件
            <input
              type="file"
              accept="video/*"
              className="hidden"
              onChange={handleFileChange}
            />
          </label>
        </div>
      </GlassPanel>
    )
  }

  return (
    <GlassPanel
      className="overflow-hidden flex flex-col"
      intensity="sm"
      radius="var(--laap-radius-md)"
    >
      <div className="relative aspect-video bg-black/40 group">
        {videoSrc ? (
          <video
            ref={videoRef}
            src={videoSrc}
            loop
            className="w-full h-full object-contain"
            onPlay={() => setPlaying(true)}
            onPause={() => setPlaying(false)}
            onTimeUpdate={handleTimeUpdate}
            onLoadedMetadata={handleLoadedMetadata}
            onClick={togglePlay}
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-8 h-8 border-2 border-white/20 border-t-laap-accent rounded-full animate-spin" />
          </div>
        )}

        {/* 中央播放按钮 */}
        {!playing && videoSrc && (
          <button
            type="button"
            onClick={togglePlay}
            className="absolute inset-0 flex items-center justify-center bg-black/20 hover:bg-black/30 transition-colors"
          >
            <div className="w-12 h-12 rounded-full bg-white/10 backdrop-blur-sm flex items-center justify-center border border-white/20">
              <Play className="w-5 h-5 text-white ml-0.5" />
            </div>
          </button>
        )}

        {/* 底部控制栏 */}
        <div className="absolute bottom-0 left-0 right-0 px-3 py-2 bg-gradient-to-t from-black/80 to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
          <input
            type="range"
            min={0}
            max={duration || 100}
            step={0.1}
            value={currentTime}
            onChange={handleSeekChange}
            onMouseDown={handleSeekStart}
            onMouseUp={handleSeekEnd}
            onTouchStart={handleSeekStart}
            onTouchEnd={handleSeekEnd}
            className="w-full h-1 mb-2 rounded-lg appearance-none bg-white/20 accent-laap-accent cursor-pointer"
          />
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={togglePlay}
                className="p-1.5 rounded-lg hover:bg-white/10 text-white/90 transition-colors"
              >
                {playing ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
              </button>
              <span className="text-[10px] font-mono text-white/70">
                {formatTime(currentTime)} / {formatTime(duration)}
              </span>
            </div>
            <button
              type="button"
              onClick={toggleMute}
              className="p-1.5 rounded-lg hover:bg-white/10 text-white/90 transition-colors"
            >
              {muted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </div>

      {fileName && (
        <div className="px-3 py-2 text-[10px] text-white/50 truncate border-t border-white/[0.06]">
          {fileName}
        </div>
      )}
    </GlassPanel>
  )
}
