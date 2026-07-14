/// <reference types="vite/client" />

// Electron 预加载脚本暴露的 desktop API 类型声明
interface Window {
  desktop?: {
    minimize: () => Promise<void>
    maximize: () => Promise<void>
    close: () => Promise<void>
    toggleFullscreen: () => Promise<void>
    getWindowState: () => Promise<{
      isMaximized: boolean
      isFullScreen: boolean
      isMinimized: boolean
    }>
    onWindowState: (callback: (state: {
      isMaximized: boolean
      isFullScreen: boolean
      isMinimized: boolean
    }) => void) => void
    openDevTools: () => void
    selectVideo: () => Promise<{ canceled: boolean; filePath?: string }>
    readVideoFile: (
      filePath: string,
    ) => Promise<{ exists: boolean; data: string; type: string; error?: string }>
    onPttPressed: (callback: () => void) => void
    showOverlay: (payload: { title: string; content: string }) => void
    registerHotkeys: (hotkeys: { showWindow: string; ptt: string }) => Promise<void>
  }
}
