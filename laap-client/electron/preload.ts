import { contextBridge, ipcRenderer } from 'electron'

// 窗口状态类型
interface WindowState {
  isMaximized: boolean
  isFullScreen: boolean
  isMinimized: boolean
}

// 桌面悬浮通知内容类型
interface OverlayPayload {
  title: string
  content: string
}

// 全局热键配置类型
interface HotkeyConfig {
  showWindow: string
  ptt: string
}

// 暴露给渲染进程的安全 API
contextBridge.exposeInMainWorld('desktop', {
  /**
   * 最小化窗口
   */
  minimize: (): Promise<void> => ipcRenderer.invoke('window:minimize'),

  /**
   * 最大化 / 还原窗口
   */
  maximize: (): Promise<void> => ipcRenderer.invoke('window:maximize'),

  /**
   * 关闭窗口（最小化到托盘）
   */
  close: (): Promise<void> => ipcRenderer.invoke('window:close'),

  /**
   * 切换全屏状态
   */
  toggleFullscreen: (): Promise<void> => ipcRenderer.invoke('window:toggleFullscreen'),

  /**
   * 获取当前窗口状态
   */
  getWindowState: (): Promise<WindowState> => ipcRenderer.invoke('window:getState'),

  /**
   * 监听窗口状态变化
   */
  onWindowState: (callback: (state: WindowState) => void): void => {
    ipcRenderer.on('window:stateChanged', (_event, state) => callback(state))
  },

  /**
   * 打开开发者工具
   */
  openDevTools: (): void => ipcRenderer.send('window:openDevTools'),

  /**
   * 打开视频文件选择对话框
   */
  selectVideo: (): Promise<{ canceled: boolean; filePath?: string }> =>
    ipcRenderer.invoke('desktop:selectVideo'),

  /**
   * 读取本地视频文件为 base64 数据
   */
  readVideoFile: (
    filePath: string,
  ): Promise<{ exists: boolean; data: string; type: string; error?: string }> =>
    ipcRenderer.invoke('desktop:readVideoFile', filePath),

  /**
   * 监听全局 PTT 热键按下事件
   */
  onPttPressed: (callback: () => void): void => {
    ipcRenderer.on('voice:pttPressed', () => callback())
  },

  /**
   * 触发桌面悬浮通知
   */
  showOverlay: (payload: OverlayPayload): void => ipcRenderer.send('overlay:show', payload),

  /**
   * 监听悬浮通知显示事件（用于 overlay 渲染进程）
   */
  onOverlayShow: (callback: (payload: OverlayPayload) => void): void => {
    ipcRenderer.on('overlay:show', (_event, payload) => callback(payload))
  },

  /**
   * 注册/更新全局热键
   */
  registerHotkeys: (hotkeys: HotkeyConfig): Promise<void> =>
    ipcRenderer.invoke('hotkeys:register', hotkeys),
})
