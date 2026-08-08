import { contextBridge, ipcRenderer, type IpcRendererEvent } from 'electron'

// 安全存储 API
contextBridge.exposeInMainWorld('electronAPI', {
  /**
   * 读取指定 key 的安全存储值
   */
  getSecureConfig: (key: string): Promise<string | null> =>
    ipcRenderer.invoke('secure-config:get', key),

  /**
   * 写入指定 key 的安全存储值
   */
  setSecureConfig: (key: string, value: string): Promise<void> =>
    ipcRenderer.invoke('secure-config:set', key, value),
})

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

// Shell 执行结果数据类型
interface ShellData {
  id: string
  stdout?: string
  stderr?: string
  exitCode?: number | null
}

// 全局热键配置类型
interface HotkeyConfig {
  showWindow: string
  ptt: string
}

// 桌面扫描结果项类型
interface DesktopScanItem {
  name: string
  detail?: string
}

// 桌面扫描结果类型
interface DesktopScanResult {
  type: 'system' | 'agents' | 'desktop'
  summary: string
  items: DesktopScanItem[]
  error?: string
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

  /**
   * 扫描系统资源（进程 / 性能）
   */
  scanSystem: (): Promise<DesktopScanResult> => ipcRenderer.invoke('desktop:scanSystem'),

  /**
   * 扫描本地已安装的 Agent / 服务
   */
  scanAgents: (): Promise<DesktopScanResult> => ipcRenderer.invoke('desktop:scanAgents'),

  /**
   * 扫描桌面文件（返回 sanitized 摘要，不暴露完整路径）
   */
  scanDesktop: (): Promise<DesktopScanResult> => ipcRenderer.invoke('desktop:scanDesktop'),
})

// 暴露给渲染进程的安全文件系统 API
contextBridge.exposeInMainWorld('fs', {
  /**
   * 读取允许路径范围内的文本文件
   */
  readFile: (
    filePath: string,
  ): Promise<{ success: boolean; content?: string; error?: string }> =>
    ipcRenderer.invoke('fs:readFile', filePath),

  /**
   * 向允许路径范围内的文本文件写入内容
   */
  writeFile: (
    filePath: string,
    content: string,
  ): Promise<{ success: boolean; error?: string }> =>
    ipcRenderer.invoke('fs:writeFile', filePath, content),
})

// 暴露给渲染进程的安全 Shell API
contextBridge.exposeInMainWorld('shell', {
  /**
   * 在本地执行 shell 命令（命令字符串 + 可选参数）
   */
  execute: (id: string, command: string, cwd?: string, args?: string[]): void =>
    ipcRenderer.send('shell:execute', id, command, cwd, args),

  /**
   * 中止指定 id 的 shell 进程
   */
  abort: (id: string): void => ipcRenderer.send('shell:abort', id),

  /**
   * 监听 shell 进程的 stdout/stderr/exit 数据
   * 返回取消监听的函数
   */
  onData: (callback: (data: ShellData) => void): (() => void) => {
    const handler = (_event: IpcRendererEvent, data: ShellData) => callback(data)
    ipcRenderer.on('shell:data', handler)
    return () => ipcRenderer.removeListener('shell:data', handler)
  },
})

// 托盘行为与全局热键唤醒 API
contextBridge.exposeInMainWorld('setCloseToTray', (enabled: boolean): void => {
  ipcRenderer.invoke('app:setCloseToTray', enabled)
})

contextBridge.exposeInMainWorld('onHotkeyWake', (callback: () => void): (() => void) => {
  const handler = (_event: IpcRendererEvent) => callback()
  ipcRenderer.on('voice:hotkey-wake', handler)
  return () => ipcRenderer.removeListener('voice:hotkey-wake', handler)
})

// 语音唤醒状态同步 API（托盘菜单 ↔ 渲染进程设置）
contextBridge.exposeInMainWorld('setVoiceWakeEnabled', (enabled: boolean): void => {
  ipcRenderer.send('voice:setWakeEnabled', enabled)
})

contextBridge.exposeInMainWorld('onVoiceWakeToggle', (callback: (enabled: boolean) => void): (() => void) => {
  const handler = (_event: IpcRendererEvent, enabled: boolean) => callback(enabled)
  ipcRenderer.on('voice:toggle-wake', handler)
  return () => ipcRenderer.removeListener('voice:toggle-wake', handler)
})

// 渲染进程请求主窗口显示 / 通用 IPC 通道
contextBridge.exposeInMainWorld('electron', {
  showWindow: (): void => ipcRenderer.send('window:show'),
  send: (channel: string, ...args: unknown[]): void => ipcRenderer.send(channel, ...args),
})
