/// <reference types="vite/client" />

// Electron 预加载脚本暴露的 desktop / fs API 类型声明
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

  fs?: {
    readFile: (
      filePath: string,
    ) => Promise<{ success: boolean; content?: string; error?: string }>
    writeFile: (
      filePath: string,
      content: string,
    ) => Promise<{ success: boolean; error?: string }>
  }

  shell?: {
    execute: (id: string, command: string, cwd?: string, args?: string[]) => void
    abort: (id: string) => void
    onData: (callback: (data: {
      id: string
      stdout?: string
      stderr?: string
      exitCode?: number | null
    }) => void) => (() => void)
  }
}
