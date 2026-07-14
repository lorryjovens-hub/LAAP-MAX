import { app, BrowserWindow, dialog, globalShortcut, ipcMain, screen, Tray, Menu } from 'electron'
import fs from 'fs'
import path from 'path'

// 性能开关：减少后台节流、启用 GPU 加速
app.commandLine.appendSwitch('disable-background-timer-throttling')
app.commandLine.appendSwitch('disable-renderer-backgrounding')
app.commandLine.appendSwitch('disable-backgrounding-occluded-windows')
app.commandLine.appendSwitch('enable-gpu-rasterization')
app.commandLine.appendSwitch('enable-accelerated-2d-canvas')

// 主窗口实例
let mainWindow: BrowserWindow | null = null
// 启动屏实例
let splashWindow: BrowserWindow | null = null
// 系统托盘实例
let tray: Tray | null = null
// 桌面悬浮通知窗口实例
let overlayWindow: BrowserWindow | null = null

// 窗口状态持久化文件路径
const windowStatePath = path.join(app.getPath('userData'), 'window-state.json')

interface WindowState {
  width: number
  height: number
  x?: number
  y?: number
  isMaximized: boolean
  isFullScreen: boolean
}

interface RuntimeWindowState {
  isMaximized: boolean
  isFullScreen: boolean
  isMinimized: boolean
}

/**
 * 读取持久化的窗口状态
 */
function loadWindowState(): WindowState {
  const defaultState: WindowState = {
    width: 1280,
    height: 720,
    isMaximized: false,
    isFullScreen: false,
  }

  try {
    if (fs.existsSync(windowStatePath)) {
      const raw = fs.readFileSync(windowStatePath, 'utf-8')
      const parsed = JSON.parse(raw) as Partial<WindowState>
      return { ...defaultState, ...parsed }
    }
  } catch (err) {
    console.error('[ERROR] 读取窗口状态失败:', err)
  }

  return defaultState
}

/**
 * 保存窗口状态到 JSON 文件
 */
function saveWindowState(): void {
  if (!mainWindow) return

  try {
    const bounds = mainWindow.getBounds()
    const state: WindowState = {
      width: bounds.width,
      height: bounds.height,
      x: bounds.x,
      y: bounds.y,
      isMaximized: mainWindow.isMaximized(),
      isFullScreen: mainWindow.isFullScreen(),
    }
    fs.writeFileSync(windowStatePath, JSON.stringify(state, null, 2))
  } catch (err) {
    console.error('[ERROR] 保存窗口状态失败:', err)
  }
}

/**
 * 确保窗口位置在当前可用的显示器范围内
 */
function ensureVisible(state: WindowState): WindowState {
  const displays = screen.getAllDisplays()
  if (displays.length === 0) return state

  const { x = 0, y = 0, width, height } = state
  const windowRect = { x, y, width, height }

  const isVisible = displays.some((display) => {
    const { workArea } = display
    return (
      windowRect.x < workArea.x + workArea.width &&
      windowRect.x + windowRect.width > workArea.x &&
      windowRect.y < workArea.y + workArea.height &&
      windowRect.y + windowRect.height > workArea.y
    )
  })

  if (!isVisible) {
    const primary = screen.getPrimaryDisplay().workArea
    return {
      ...state,
      x: primary.x + Math.round((primary.width - width) / 2),
      y: primary.y + Math.round((primary.height - height) / 2),
    }
  }

  return state
}

/**
 * 获取托盘图标路径
 */
function getTrayIconPath(): string {
  if (process.env.NODE_ENV === 'development') {
    return path.join(__dirname, '../../public/logo-32.png')
  }
  return path.join(__dirname, '../../dist/logo-32.png')
}

/**
 * 创建系统托盘
 */
function createTray(): void {
  const iconPath = getTrayIconPath()
  tray = new Tray(iconPath)
  tray.setToolTip('LAAP Client')

  const contextMenu = Menu.buildFromTemplate([
    {
      label: '显示主窗口',
      click: () => {
        showMainWindow()
      },
    },
    {
      label: '退出',
      click: () => {
        ;(app as unknown as { isQuiting?: boolean }).isQuiting = true
        app.quit()
      },
    },
  ])

  tray.setContextMenu(contextMenu)

  // 单击托盘图标恢复主窗口
  tray.on('click', () => {
    showMainWindow()
  })
}

/**
 * 显示主窗口
 */
function showMainWindow(): void {
  if (!mainWindow) {
    createWindow()
    return
  }
  if (mainWindow.isMinimized()) {
    mainWindow.restore()
  }
  mainWindow.show()
  mainWindow.focus()
}

/**
 * 隐藏主窗口
 */
function hideMainWindow(): void {
  mainWindow?.hide()
}

/**
 * 切换主窗口显示/隐藏
 */
function toggleMainWindow(): void {
  if (!mainWindow) {
    createWindow()
    return
  }
  if (mainWindow.isVisible() && !mainWindow.isMinimized()) {
    hideMainWindow()
  } else {
    showMainWindow()
  }
}

/**
 * 创建启动屏窗口
 */
function createSplashWindow(): void {
  splashWindow = new BrowserWindow({
    width: 420,
    height: 320,
    frame: false,
    transparent: true,
    backgroundColor: '#00000000',
    alwaysOnTop: true,
    skipTaskbar: true,
    resizable: false,
    movable: true,
    webPreferences: {
      preload: path.join(__dirname, '../preload/preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  })

  splashWindow.center()

  if (process.env.NODE_ENV === 'development') {
    splashWindow.loadFile(path.join(__dirname, '../../public/splash.html'))
  } else {
    splashWindow.loadFile(path.join(__dirname, '../../dist/splash.html'))
  }

  splashWindow.on('closed', () => {
    splashWindow = null
  })
}

/**
 * 创建桌面悬浮通知窗口
 */
function createOverlayWindow(): void {
  const primary = screen.getPrimaryDisplay().workArea
  const width = 360
  const height = 120

  overlayWindow = new BrowserWindow({
    width,
    height,
    x: primary.x + primary.width - width - 20,
    y: primary.y + 40,
    frame: false,
    transparent: true,
    backgroundColor: '#00000000',
    alwaysOnTop: true,
    skipTaskbar: true,
    focusable: false,
    show: false,
    resizable: false,
    movable: false,
    webPreferences: {
      preload: path.join(__dirname, '../preload/preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
      backgroundThrottling: false,
    },
  })

  if (process.env.NODE_ENV === 'development') {
    overlayWindow.loadURL('http://localhost:5173/overlay.html')
  } else {
    overlayWindow.loadFile(path.join(__dirname, '../../dist/overlay.html'))
  }

  overlayWindow.on('closed', () => {
    overlayWindow = null
  })
}

/**
 * 显示桌面悬浮通知
 */
function showOverlay(title: string, content: string): void {
  if (!overlayWindow) {
    createOverlayWindow()
  }
  if (!overlayWindow) return

  overlayWindow.webContents.send('overlay:show', { title, content })

  overlayWindow.showInactive()
  overlayWindow.setOpacity(0)

  let opacity = 0
  const fadeIn = setInterval(() => {
    opacity += 0.1
    overlayWindow?.setOpacity(Math.min(1, opacity))
    if (opacity >= 1) clearInterval(fadeIn)
  }, 30)

  // 3 秒后淡出
  setTimeout(() => {
    let fadeOpacity = 1
    const fadeOut = setInterval(() => {
      fadeOpacity -= 0.05
      overlayWindow?.setOpacity(Math.max(0, fadeOpacity))
      if (fadeOpacity <= 0) {
        clearInterval(fadeOut)
        overlayWindow?.hide()
      }
    }, 40)
  }, 3000)
}

interface HotkeyConfig {
  showWindow: string
  ptt: string
}

let currentHotkeys: HotkeyConfig = {
  showWindow: 'CommandOrControl+Shift+L',
  ptt: 'CommandOrControl+Shift+Space',
}

/**
 * 注册全局热键
 */
function registerGlobalShortcuts(hotkeys: HotkeyConfig = currentHotkeys): void {
  // 先注销所有已注册热键，避免重复
  globalShortcut.unregisterAll()

  currentHotkeys = hotkeys

  // 显示/隐藏主窗口
  if (hotkeys.showWindow) {
    globalShortcut.register(hotkeys.showWindow, () => {
      toggleMainWindow()
    })
  }

  // PTT：按一次开始，再按一次停止
  if (hotkeys.ptt) {
    globalShortcut.register(hotkeys.ptt, () => {
      mainWindow?.webContents.send('voice:pttPressed')
    })
  }
}

/**
 * 更新全局热键（由渲染进程调用）
 */
function updateGlobalShortcuts(hotkeys: HotkeyConfig): void {
  registerGlobalShortcuts(hotkeys)
}


/**
 * 创建无边框透明主窗口
 */
function createWindow(): void {
  const savedState = ensureVisible(loadWindowState())

  mainWindow = new BrowserWindow({
    width: savedState.width,
    height: savedState.height,
    x: savedState.x,
    y: savedState.y,
    minWidth: 960,
    minHeight: 540,
    title: 'LAAP Client',
    icon: path.join(__dirname, '../../public/logo-256.png'),
    show: false,
    // 无边框 + 透明背景
    frame: false,
    transparent: true,
    backgroundColor: '#00000000',
    webPreferences: {
      // 预加载脚本路径（相对于主进程构建产物）
      preload: path.join(__dirname, '../preload/preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
      backgroundThrottling: false,
    },
  })

  // 恢复最大化 / 全屏状态
  if (savedState.isFullScreen) {
    mainWindow.setFullScreen(true)
  } else if (savedState.isMaximized) {
    mainWindow.maximize()
  }

  // 加载渲染进程入口
  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:5173')
  } else {
    mainWindow.loadFile(path.join(__dirname, '../../dist/index.html'))
  }

  // 窗口准备好后关闭启动屏并显示主窗口
  mainWindow.once('ready-to-show', () => {
    splashWindow?.close()
    mainWindow?.show()
  })

  // 监听窗口状态变化并通知渲染进程
  mainWindow.on('maximize', broadcastWindowState)
  mainWindow.on('unmaximize', broadcastWindowState)
  mainWindow.on('enter-full-screen', broadcastWindowState)
  mainWindow.on('leave-full-screen', broadcastWindowState)
  mainWindow.on('minimize', broadcastWindowState)
  mainWindow.on('restore', broadcastWindowState)

  // 窗口移动、调整大小时保存状态
  const saveDebounced = debounce(saveWindowState, 250)
  mainWindow.on('move', saveDebounced)
  mainWindow.on('resize', saveDebounced)
  mainWindow.on('maximize', saveDebounced)
  mainWindow.on('unmaximize', saveDebounced)
  mainWindow.on('enter-full-screen', saveDebounced)
  mainWindow.on('leave-full-screen', saveDebounced)

  // 关闭窗口时最小化到托盘，不退出应用
  mainWindow.on('close', (event) => {
    if (!app.isQuiting) {
      event.preventDefault()
      hideMainWindow()
    } else {
      saveWindowState()
    }
  })

  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

/**
 * 防抖辅助函数
 */
function debounce<T extends (...args: unknown[]) => void>(fn: T, wait: number) {
  let timer: ReturnType<typeof setTimeout> | null = null
  return (...args: Parameters<T>) => {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => fn(...args), wait)
  }
}

/**
 * 获取当前窗口状态
 */
function getWindowState(): RuntimeWindowState {
  return {
    isMaximized: mainWindow?.isMaximized() ?? false,
    isFullScreen: mainWindow?.isFullScreen() ?? false,
    isMinimized: mainWindow?.isMinimized() ?? false,
  }
}

/**
 * 向渲染进程广播窗口状态
 */
function broadcastWindowState(): void {
  const state = getWindowState()
  mainWindow?.webContents.send('window:stateChanged', state)
}

// 应用就绪后创建启动屏、主窗口、托盘、热键与悬浮窗口
app.whenReady().then(async () => {
  // 验证阶段自动启动 Mock WebSocket 后端，避免依赖真实 LAAP 后端
  try {
    const { startLaapMockServer } = await import('../src/laap/mockServer')
    await startLaapMockServer()
  } catch (err) {
    console.error('[Main] 启动 Mock Server 失败:', err)
  }

  createSplashWindow()
  createWindow()
  createTray()
  createOverlayWindow()
  registerGlobalShortcuts()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    } else {
      showMainWindow()
    }
  })
})

// 所有窗口关闭后退出应用（Windows 行为），但托盘保持时由托盘菜单控制退出
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    // 由托盘图标与右键菜单管理生命周期，不自动退出
  }
})

// 退出前注销全局热键
app.on('will-quit', () => {
  globalShortcut.unregisterAll()
})

// IPC：最小化窗口
ipcMain.handle('window:minimize', () => {
  mainWindow?.minimize()
})

// IPC：最大化 / 还原窗口
ipcMain.handle('window:maximize', () => {
  if (mainWindow?.isMaximized()) {
    mainWindow.unmaximize()
  } else {
    mainWindow?.maximize()
  }
})

// IPC：关闭窗口（最小化到托盘）
ipcMain.handle('window:close', () => {
  hideMainWindow()
})

// IPC：切换全屏
ipcMain.handle('window:toggleFullscreen', () => {
  const isFullScreen = mainWindow?.isFullScreen() ?? false
  mainWindow?.setFullScreen(!isFullScreen)
})

// IPC：获取窗口状态
ipcMain.handle('window:getState', () => {
  return getWindowState()
})

// IPC：打开开发者工具
ipcMain.on('window:openDevTools', () => {
  mainWindow?.webContents.openDevTools({ mode: 'detach' })
})

// IPC：触发桌面悬浮通知
ipcMain.on('overlay:show', (_event, { title, content }: { title: string; content: string }) => {
  showOverlay(title, content)
})

// IPC：注册/更新全局热键
ipcMain.handle('hotkeys:register', (_event, hotkeys: HotkeyConfig) => {
  updateGlobalShortcuts(hotkeys)
})

/**
 * 根据文件扩展名推断视频 MIME 类型
 */
function inferVideoMime(filePath: string): string {
  const ext = path.extname(filePath).toLowerCase()
  switch (ext) {
    case '.webm':
      return 'video/webm'
    case '.mov':
      return 'video/quicktime'
    case '.mkv':
      return 'video/x-matroska'
    case '.avi':
      return 'video/x-msvideo'
    case '.mp4':
    default:
      return 'video/mp4'
  }
}

// IPC：选择本地视频文件
ipcMain.handle('desktop:selectVideo', async () => {
  if (!mainWindow) return { canceled: true }
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile'],
    filters: [
      {
        name: '视频文件',
        extensions: ['mp4', 'webm', 'mov', 'mkv', 'avi'],
      },
    ],
  })
  return {
    canceled: result.canceled,
    filePath: result.filePaths[0],
  }
})

// IPC：读取本地视频文件并返回 base64 数据
ipcMain.handle('desktop:readVideoFile', async (_event, filePath: string) => {
  try {
    if (!fs.existsSync(filePath)) {
      return { exists: false, data: '', type: '' }
    }
    const buffer = fs.readFileSync(filePath)
    return {
      exists: true,
      data: buffer.toString('base64'),
      type: inferVideoMime(filePath),
    }
  } catch (err) {
    return {
      exists: false,
      data: '',
      type: '',
      error: err instanceof Error ? err.message : String(err),
    }
  }
})
