/**
 * Vitest 全局测试前置配置
 *
 * 为 Electron 预加载 API、localStorage 等提供基础 mock，避免在 jsdom 环境中崩溃。
 */

// 提供 window.desktop 基础 mock，使依赖 IPC 的组件能够渲染
Object.assign(window, {
  desktop: {
    minimize: () => Promise.resolve(),
    maximize: () => Promise.resolve(),
    close: () => Promise.resolve(),
    toggleFullscreen: () => Promise.resolve(),
    getWindowState: () =>
      Promise.resolve({ isMaximized: false, isFullScreen: false, isMinimized: false }),
    onWindowState: () => {},
    openDevTools: () => {},
    selectVideo: () => Promise.resolve({ canceled: true }),
    readVideoFile: () => Promise.resolve({ exists: false, data: '', type: '' }),
    onPttPressed: () => {},
    showOverlay: () => {},
    onOverlayShow: () => {},
  },
})

// 清理 localStorage，避免测试之间的持久化状态相互污染
beforeEach(() => {
  window.localStorage.clear()
})
