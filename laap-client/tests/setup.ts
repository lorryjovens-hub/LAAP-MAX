/**
 * Vitest 全局测试前置配置
 *
 * 为 Electron 预加载 API、localStorage 等提供基础 mock，避免在 jsdom 环境中崩溃。
 */

import { beforeEach } from 'vitest'

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
    registerHotkeys: () => {},
  },
})

// 提供 shell IPC 基础 mock，避免依赖 shell 的组件/逻辑在 jsdom 中崩溃
Object.assign(window, {
  shell: {
    execute: () => {},
    abort: () => {},
    onData: () => () => {},
  },
})

// jsdom 未实现 ResizeObserver，提供空实现避免 LiquidGlass 等组件在测试中崩溃
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}

// 清理 localStorage，避免测试之间的持久化状态相互污染
beforeEach(() => {
  window.localStorage.clear()
})
