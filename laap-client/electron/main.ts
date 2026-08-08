import { app, BrowserWindow, dialog, globalShortcut, ipcMain, screen, Tray, Menu, safeStorage } from 'electron'
import fs from 'fs'
import fsPromises from 'node:fs/promises'
import path from 'path'
import os from 'os'
import type { ChildProcess } from 'child_process'
import net from 'net'
import http from 'http'

// 单实例锁：防止多个 LAAP Client 进程同时运行导致后端端口冲突
const gotTheLock = app.requestSingleInstanceLock()
if (!gotTheLock) {
  console.log('[main] Another instance is already running. Quitting.')
  app.quit()
  process.exit(0)
}

app.on('second-instance', () => {
  logLauncher('[main] Second instance detected, focusing existing window')
  void showMainWindow()
})

// 安全存储文件路径
const secureConfigPath = path.join(app.getPath('userData'), 'secure-config.json')

// 启动日志路径：%APPDATA%\LAAP Client\launcher.log
const launcherLogPath = path.join(app.getPath('userData'), 'launcher.log')

function logLauncher(...args: unknown[]) {
  const message = args
    .map((arg) => (typeof arg === 'string' ? arg : JSON.stringify(arg)))
    .join(' ')
  const line = `[${new Date().toISOString()}] ${message}\n`
  try {
    const dir = path.dirname(launcherLogPath)
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true })
    }
    fs.appendFileSync(launcherLogPath, line, 'utf-8')
  } catch (e) {
    // 日志写入失败时不阻断启动
  }
  console.log(...args)
}

process.on('uncaughtException', (err) => {
  logLauncher('[FATAL] uncaughtException:', err)
})

process.on('unhandledRejection', (reason) => {
  logLauncher('[FATAL] unhandledRejection:', reason)
})

// 本地 Shell 执行安全配置
const PROJECT_ROOT = 'D:\\LAAP'

const ALLOWED_SHELL_COMMANDS = new Set([
  'node',
  'npm',
  'pnpm',
  'git',
  'python',
  'python3',
  'dir',
  'echo',
  'cargo',
  'rustc',
  'cmake',
  'code',
  'cmd',
])

const DANGEROUS_SUBCOMMANDS = new Set(['del', 'erase', 'rd', 'rmdir', 'format', 'rm', 'shutdown', 'mkfs', 'dd'])

// 正在运行的 shell 进程映射
const shellProcesses = new Map<string, ChildProcess>()

/**
 * 解析命令字符串，按空白拆分并保留引号内容
 */
function parseCommand(command: string): string[] {
  const tokens: string[] = []
  let current = ''
  let quote: string | null = null
  let escaped = false

  for (let i = 0; i < command.length; i++) {
    const ch = command[i]
    if (escaped) {
      current += ch
      escaped = false
      continue
    }
    if (ch === '\\\\' && quote !== "'") {
      escaped = true
      continue
    }
    if (quote) {
      if (ch === quote) {
        quote = null
      } else {
        current += ch
      }
      continue
    }
    if (ch === '"' || ch === "'") {
      quote = ch
      continue
    }
    if (/\\s/.test(ch)) {
      if (current !== '') {
        tokens.push(current)
        current = ''
      }
      continue
    }
    current += ch
  }

  if (current !== '' || quote !== null) {
    tokens.push(current)
  }
  return tokens
}

/**
 * 获取可执行文件名（去除 Windows 扩展名）
 */
function getExecutableBase(exec: string): string {
  const base = path.basename(exec)
  const ext = path.extname(base).toLowerCase()
  if (process.platform === 'win32' && ['.exe', '.cmd', '.bat', '.ps1', '.com'].includes(ext)) {
    return path.basename(base, ext)
  }
  return base
}

/**
 * 检测危险命令模式
 */
function isDangerousTokens(tokens: string[]): boolean {
  if (tokens.length === 0) return false
  const exec = getExecutableBase(tokens[0]).toLowerCase()

  // rm -rf / 或 rm -rf \
  if (exec === 'rm') {
    const hasRf = tokens.some((t) => t === '-rf' || t === '-rf' || t.startsWith('-rf'))
    const hasRoot = tokens.some((t) => t === '/' || t === '\\')
    if (hasRf && hasRoot) return true
  }

  // cmd /c 或 cmd /k 后的子命令检查
  if (exec === 'cmd') {
    const flagIndex = tokens.findIndex((t) => t.length === 2 && t[0] === '/' && (t[1] === 'c' || t[1] === 'k'))
    if (flagIndex !== -1 && flagIndex + 1 < tokens.length) {
      const sub = getExecutableBase(tokens[flagIndex + 1]).toLowerCase()
      if (DANGEROUS_SUBCOMMANDS.has(sub)) return true
      if (sub === 'rm' && tokens.slice(flagIndex + 1).some((a) => a === '/' || a === '\\')) return true
    }
  }

  return false
}

/**
 * 校验并解析要执行的命令
 */
function validateCommand(command: string, extraArgs?: string[]): { file: string; args: string[] } {
  const tokens = parseCommand(command)
  if (tokens.length === 0) {
    throw new Error('命令为空')
  }

  const rawExec = tokens[0]
  const execBase = getExecutableBase(rawExec).toLowerCase()

  if (!ALLOWED_SHELL_COMMANDS.has(execBase)) {
    throw new Error(`不允许执行的命令: ${execBase}`)
  }

  if (isDangerousTokens(tokens)) {
    throw new Error('检测到危险命令，已拒绝执行')
  }

  const allArgs = tokens.slice(1).concat(extraArgs || [])

  // cmd 必须携带 /c，且子命令也必须在白名单中
  if (execBase === 'cmd') {
    const flagIndex = allArgs.findIndex((t) => t.length === 2 && t[0] === '/' && t[1] === 'c')
    if (flagIndex === -1 || flagIndex + 1 >= allArgs.length) {
      throw new Error('cmd 命令必须带有 /c 参数及子命令')
    }
    const sub = getExecutableBase(allArgs[flagIndex + 1]).toLowerCase()
    if (!ALLOWED_SHELL_COMMANDS.has(sub)) {
      throw new Error(`cmd 子命令不在白名单: ${sub}`)
    }
  }

  return { file: rawExec, args: allArgs }
}

/**
 * 校验并解析工作目录，默认限制在 D:\LAAP 及其子目录
 */
function resolveAllowedCwd(cwd?: string): string {
  const target = cwd ? path.resolve(PROJECT_ROOT, cwd) : PROJECT_ROOT
  const relative = path.relative(PROJECT_ROOT, target)
  if (relative.startsWith('..') || path.isAbsolute(relative)) {
    throw new Error(`工作目录不在允许范围内: ${target}`)
  }
  return target
}

/**
 * 校验并解析允许读写的文件路径，限制在 D:\LAAP 及其子目录
 */
function resolveAllowedFilePath(filePath: string): string {
  const resolved = path.isAbsolute(filePath)
    ? path.normalize(filePath)
    : path.resolve(PROJECT_ROOT, filePath)
  const relative = path.relative(PROJECT_ROOT, resolved)
  if (relative.startsWith('..') || path.isAbsolute(relative)) {
    throw new Error(`路径不在允许范围内: ${filePath}`)
  }
  return resolved
}

/**
 * 读取安全存储文件
 */
async function readSecureConfigFile(): Promise<Record<string, string>> {
  try {
    if (fs.existsSync(secureConfigPath)) {
      const raw = await fs.promises.readFile(secureConfigPath, 'utf-8')
      return JSON.parse(raw) as Record<string, string>
    }
  } catch (err) {
    console.error('[Main] 读取安全存储文件失败:', err)
  }
  return {}
}

/**
 * 写入安全存储文件
 */
async function writeSecureConfigFile(data: Record<string, string>): Promise<void> {
  try {
    await fs.promises.writeFile(secureConfigPath, JSON.stringify(data, null, 2), 'utf-8')
  } catch (err) {
    console.error('[Main] 写入安全存储文件失败:', err)
    throw err
  }
}

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

// 应用退出状态（托盘菜单真正退出时设为 true）
interface AppQuitingState {
  isQuiting?: boolean
}
const appState = app as unknown as AppQuitingState

// 是否点击关闭按钮时最小化到托盘（可由渲染进程切换）
let closeToTrayEnabled = true
// 语音唤醒是否启用（与渲染进程 settingsStore.wakeWordEnabled 同步）
let voiceWakeEnabled = false
// 开发服务器端口缓存
let devServerPort: number | null = null

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
    const dir = path.dirname(windowStatePath)
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true })
    }
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
 * 判断当前是否运行在打包后的生产环境。
 * 优先使用 app.isPackaged，因为 process.env.NODE_ENV 在打包后通常不可靠。
 */
function isProduction(): boolean {
  return app.isPackaged
}

/**
 * 获取公共资源目录下的资源路径。
 * 开发时 public 目录直接可用；打包后资源位于 dist 目录。
 */
function getPublicAssetPath(relativeName: string): string {
  if (isProduction()) {
    return path.join(app.getAppPath(), 'dist', relativeName)
  }
  return path.join(__dirname, '../../public', relativeName)
}

/**
 * 获取托盘图标路径
 */
function getTrayIconPath(): string {
  return getPublicAssetPath('logo-32.png')
}

/**
 * 创建系统托盘
 */
function createTray(): void {
  const iconPath = getTrayIconPath()
  tray = new Tray(iconPath)
  tray.setToolTip('LAAP Client')

  updateTrayMenu()

  // 单击托盘图标恢复主窗口
  tray.on('click', () => {
    void showMainWindow()
  })
}

/**
 * 更新托盘右键菜单（反映语音唤醒状态）
 */
function updateTrayMenu(): void {
  if (!tray) return

  const contextMenu = Menu.buildFromTemplate([
    {
      label: '显示主窗口',
      click: () => {
        void showMainWindow()
      },
    },
    { type: 'separator' },
    {
      label: '启用语音唤醒',
      type: 'checkbox',
      checked: voiceWakeEnabled,
      click: () => {
        voiceWakeEnabled = !voiceWakeEnabled
        mainWindow?.webContents.send('voice:toggle-wake', voiceWakeEnabled)
        updateTrayMenu()
      },
    },
    { type: 'separator' },
    {
      label: '退出',
      click: () => {
        appState.isQuiting = true
        app.quit()
      },
    },
  ])

  tray.setContextMenu(contextMenu)
}

/**
 * 显示主窗口
 */
async function showMainWindow(): Promise<void> {
  if (!mainWindow) {
    await createWindow()
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
async function toggleMainWindow(): Promise<void> {
  if (!mainWindow) {
    await createWindow()
    return
  }
  if (mainWindow.isVisible() && !mainWindow.isMinimized()) {
    hideMainWindow()
  } else {
    await showMainWindow()
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

  splashWindow.loadFile(getPublicAssetPath('splash.html'))

  splashWindow.on('closed', () => {
    splashWindow = null
  })
}

/**
 * 创建桌面悬浮通知窗口
 */
async function createOverlayWindow(): Promise<void> {
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

  if (isProduction()) {
    overlayWindow.loadFile(path.join(app.getAppPath(), 'dist', 'overlay.html'))
  } else {
    if (devServerPort === null) {
      devServerPort = await findDevServerPort()
    }
    const port = devServerPort ?? 5173
    overlayWindow.loadURL(`http://localhost:${port}/overlay.html`)
  }

  overlayWindow.on('closed', () => {
    overlayWindow = null
  })
}

/**
 * 显示桌面悬浮通知
 */
async function showOverlay(title: string, content: string): Promise<void> {
  if (!overlayWindow) {
    await createOverlayWindow()
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
  showWindow: process.platform === 'win32' ? 'Super+Shift+A' : 'CommandOrControl+Shift+A',
  ptt: 'CommandOrControl+Shift+Space',
}

/**
 * 注册全局热键
 */
function registerGlobalShortcuts(hotkeys: HotkeyConfig = currentHotkeys): void {
  // 先注销所有已注册热键，避免重复
  globalShortcut.unregisterAll()

  currentHotkeys = hotkeys

  // 显示/隐藏主窗口；若从隐藏状态显示且语音唤醒启用，通知渲染进程开始监听
  if (hotkeys.showWindow) {
    globalShortcut.register(hotkeys.showWindow, () => {
      const wasVisible = mainWindow?.isVisible() && !mainWindow?.isMinimized()
      void toggleMainWindow()
      if (!wasVisible && voiceWakeEnabled) {
        mainWindow?.webContents.send('voice:hotkey-wake')
      }
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
async function createWindow(): Promise<void> {
  const savedState = ensureVisible(loadWindowState())

  mainWindow = new BrowserWindow({
    width: savedState.width,
    height: savedState.height,
    x: savedState.x,
    y: savedState.y,
    minWidth: 960,
    minHeight: 540,
    title: 'LAAP Client',
    icon: getPublicAssetPath('logo-256.png'),
    show: false,
    // 无边框透明窗口，配合液态玻璃 UI
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
  if (isProduction()) {
    mainWindow.loadFile(path.join(app.getAppPath(), 'dist', 'index.html'))
  } else {
    if (devServerPort === null) {
      devServerPort = await findDevServerPort()
    }
    const port = devServerPort ?? 5173
    if (devServerPort === null) {
      logLauncher('[main] 未检测到 Vite 开发服务器，将尝试默认端口 5173')
    }
    mainWindow.loadURL(`http://localhost:${port}`)
  }

  // 窗口准备好后关闭启动屏并显示主窗口
  mainWindow.once('ready-to-show', () => {
    splashWindow?.close()
    mainWindow?.show()
  })

  // 兜底：如果 5 秒后 ready-to-show 仍未触发（例如渲染进程卡住），
  // 仍然关闭启动屏并尝试显示主窗口，避免用户看到无限启动屏。
  const showFallback = setTimeout(() => {
    logLauncher('[main] Fallback: showing main window after timeout')
    splashWindow?.close()
    mainWindow?.show()
  }, 5000)
  mainWindow.once('closed', () => clearTimeout(showFallback))

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

  // 关闭窗口时最小化到托盘，不退出应用（除非正在真正退出或已禁用 close-to-tray）
  mainWindow.on('close', (event) => {
    if (!appState.isQuiting && closeToTrayEnabled) {
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

// 检查指定端口是否已被占用
function isPortInUse(port: number): Promise<boolean> {
  return new Promise((resolve) => {
    const tester = net
      .createServer()
      .once('error', () => resolve(true))
      .once('listening', () => {
        tester.close(() => resolve(false))
      })
      .listen(port, '127.0.0.1')
  })
}

/**
 * 在开发模式下探测 Vite 开发服务器实际端口。
 * Vite 默认 5173，但当端口被占用时会自动递增，因此主进程需要主动探测。
 */
function findDevServerPort(start = 5173, end = 5179): Promise<number | null> {
  return new Promise((resolve) => {
    const tryPort = (port: number) => {
      if (port > end) {
        resolve(null)
        return
      }
      const req = http
        .get(`http://localhost:${port}/`, { timeout: 800 }, (res) => {
          if (res.statusCode && res.statusCode >= 200 && res.statusCode < 400) {
            resolve(port)
          } else {
            tryPort(port + 1)
          }
        })
        .on('error', () => tryPort(port + 1))
        .on('timeout', () => {
          req.destroy()
          tryPort(port + 1)
        })
    }
    tryPort(start)
  })
}

/**
 * 清理占用指定端口的旧 laap-server 进程。
 * 通过 netstat 查找 PID，并仅当命令行包含 laap-server 时才终止，避免误杀。
 */
async function killStaleBackend(port: number): Promise<void> {
  if (process.platform !== 'win32') return
  const { exec } = require('child_process')
  return new Promise((resolve) => {
    exec(`netstat -ano | findstr :${port}`, (error: Error | null, stdout: string) => {
      if (error || !stdout) {
        resolve()
        return
      }
      const pids = new Set<number>()
      stdout.split('\n').forEach((line) => {
        const parts = line.trim().split(/\s+/)
        const local = parts[1] || ''
        const pid = parseInt(parts[parts.length - 1], 10)
        if (local.includes(`127.0.0.1:${port}`) || local.includes(`:${port}`)) {
          if (!Number.isNaN(pid)) pids.add(pid)
        }
      })

      if (pids.size === 0) {
        resolve()
        return
      }

      let checked = 0
      pids.forEach((pid) => {
        exec(`wmic process where ProcessId=${pid} get CommandLine /format:list`, (err: Error | null, cmdOut: string) => {
          checked += 1
          if (!err && cmdOut && cmdOut.includes('laap-server')) {
            logLauncher('[main] Killing stale backend process:', pid)
            try {
              process.kill(pid)
            } catch (e) {
              logLauncher('[main] Failed to kill stale backend:', e)
            }
          }
          if (checked >= pids.size) resolve()
        })
      })
    })
  })
}

// 应用就绪后创建启动屏、主窗口、托盘、热键与悬浮窗口
app.whenReady().then(async () => {
  logLauncher('[main] app.whenReady fired')

  // 启动后端服务 (laap-server.cjs)
  // 使用 app.getAppPath() 以兼容开发目录与打包后的 resources/app 目录
  const backendPath = path.join(app.getAppPath(), 'laap-server.cjs')
  let backendProcess: ChildProcess | null = null
  try {
    if (fs.existsSync(backendPath)) {
      // 如果端口仍被旧进程占用，先尝试清理，避免 EADDRINUSE 导致后端退出
      if (await isPortInUse(8765)) {
        logLauncher('[main] Port 8765 is in use, attempting to clean up stale backend')
        await killStaleBackend(8765)
        // 等待端口释放
        await new Promise((resolve) => setTimeout(resolve, 500))
      }

      const { fork } = require('child_process')
      const proc = fork(backendPath, ['8765'], { stdio: 'pipe' })
      backendProcess = proc
      proc.stdout?.on('data', (data: Buffer) => logLauncher('[backend]', data.toString().trim()))
      proc.stderr?.on('data', (data: Buffer) => logLauncher('[backend] stderr', data.toString().trim()))
      proc.on('exit', (code: number | null) => logLauncher(`[backend] exited with code ${code}`))
      logLauncher('[main] Backend server started:', backendPath)
    } else {
      logLauncher('[main] Backend script not found at:', backendPath)
    }
  } catch (err) {
    logLauncher('[main] Failed to start backend:', err)
  }

  app.on('before-quit', () => {
    if (backendProcess && !backendProcess.killed) backendProcess.kill()
  })

  try {
    logLauncher('[main] Creating splash window...')
    createSplashWindow()
    logLauncher('[main] Creating main window...')
    await createWindow()
    logLauncher('[main] Creating tray...')
    createTray()
    logLauncher('[main] Creating overlay window...')
    await createOverlayWindow()
    logLauncher('[main] Registering global shortcuts...')
    registerGlobalShortcuts()
    logLauncher('[main] Initialization complete')
  } catch (err) {
    logLauncher('[main] Initialization error:', err)
    throw err
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      void createWindow()
    } else {
      showMainWindow()
    }
  })
})

// 所有窗口关闭后由托盘菜单控制生命周期；真正退出时 isQuiting 为 true
app.on('window-all-closed', () => {
  if (appState.isQuiting) {
    return
  }
  // 保持后台运行，等待托盘或热键唤醒
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

// IPC：显示主窗口（语音唤醒等场景）
ipcMain.on('window:show', () => {
  showMainWindow()
})

// IPC：触发桌面悬浮通知
ipcMain.on('overlay:show', (_event, { title, content }: { title: string; content: string }) => {
  showOverlay(title, content)
})

// IPC：注册/更新全局热键
ipcMain.handle('hotkeys:register', (_event, hotkeys: HotkeyConfig) => {
  updateGlobalShortcuts(hotkeys)
})

// IPC：设置是否点击关闭按钮时最小化到托盘
ipcMain.handle('app:setCloseToTray', (_event, enabled: unknown) => {
  closeToTrayEnabled = Boolean(enabled)
})

// IPC：渲染进程同步语音唤醒启用状态到主进程
ipcMain.on('voice:setWakeEnabled', (_event, enabled: unknown) => {
  voiceWakeEnabled = Boolean(enabled)
  updateTrayMenu()
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

// IPC：读取安全存储配置（使用 Electron safeStorage 解密）
ipcMain.handle('secure-config:get', async (_event, key: string) => {
  if (!safeStorage.isEncryptionAvailable()) {
    throw new Error('safeStorage 加密不可用')
  }
  const data = await readSecureConfigFile()
  const encrypted = data[key]
  if (!encrypted) return null
  return safeStorage.decryptString(Buffer.from(encrypted, 'base64'))
})

// IPC：写入安全存储配置（使用 Electron safeStorage 加密）
ipcMain.handle('secure-config:set', async (_event, key: string, value: string) => {
  if (!safeStorage.isEncryptionAvailable()) {
    throw new Error('safeStorage 加密不可用')
  }
  const data = await readSecureConfigFile()
  if (value === '') {
    delete data[key]
  } else {
    data[key] = safeStorage.encryptString(value).toString('base64')
  }
  await writeSecureConfigFile(data)
})

// IPC：扫描系统资源（CPU / 内存 / 平台信息）
ipcMain.handle('desktop:scanSystem', async () => {
  try {
    const cpus = os.cpus()
    const totalMem = os.totalmem()
    const freeMem = os.freemem()
    const loadAvg = os.loadavg()
    return {
      type: 'system' as const,
      summary: `平台 ${os.platform()} ${os.arch()}，CPU ${cpus.length} 核，内存 ${Math.round((totalMem - freeMem) / 1024 / 1024 / 1024)}GB / ${Math.round(totalMem / 1024 / 1024 / 1024)}GB 已用`,
      items: [
        { name: 'hostname', detail: os.hostname() },
        { name: 'uptime', detail: `${Math.round(os.uptime() / 60)} 分钟` },
        { name: 'loadavg', detail: loadAvg.map((v) => v.toFixed(2)).join(', ') },
        { name: 'cpu-model', detail: cpus[0]?.model ?? 'unknown' },
      ],
    }
  } catch (err) {
    return {
      type: 'system' as const,
      summary: '系统扫描失败',
      items: [],
      error: err instanceof Error ? err.message : String(err),
    }
  }
})

// IPC：扫描本地 Agent / 服务进程
ipcMain.handle('desktop:scanAgents', async () => {
  try {
    const processes = await new Promise<Array<{ name: string; pid: number }>>((resolve, reject) => {
      try {
        const { exec } = require('child_process')
        exec('tasklist /FO CSV /NH', (error: Error | null, stdout: string) => {
          if (error) {
            reject(error)
            return
          }
          const list = stdout
            .split('\n')
            .map((line) => {
              const parts = line.split('","')
              return { name: parts[0]?.replace(/^"/, '') ?? '', pid: parseInt(parts[1] ?? '0', 10) }
            })
            .filter((p) => !Number.isNaN(p.pid))
          resolve(list)
        })
      } catch (err) {
        reject(err)
      }
    })

    const agentNames = ['electron.exe', 'python.exe', 'node.exe', 'laap-agent.exe']
    const found = processes.filter((p) => agentNames.some((name) => p.name.toLowerCase().includes(name.toLowerCase())))

    return {
      type: 'agents' as const,
      summary: `发现 ${found.length} 个相关进程`,
      items: found.slice(0, 20).map((p) => ({ name: p.name, detail: `pid:${p.pid}` })),
    }
  } catch (err) {
    return {
      type: 'agents' as const,
      summary: 'Agent 扫描失败',
      items: [],
      error: err instanceof Error ? err.message : String(err),
    }
  }
})

// IPC：扫描桌面文件（仅返回类型统计，不暴露完整路径）
ipcMain.handle('desktop:scanDesktop', async () => {
  try {
    const desktopPath = path.join(os.homedir(), 'Desktop')
    if (!fs.existsSync(desktopPath)) {
      return {
        type: 'desktop' as const,
        summary: '未找到桌面目录',
        items: [],
      }
    }

    const entries = await fs.promises.readdir(desktopPath, { withFileTypes: true })
    const stats = new Map<string, number>()
    entries.forEach((entry) => {
      let key = entry.isDirectory() ? 'folder' : 'file'
      if (!entry.isDirectory()) {
        const ext = path.extname(entry.name).toLowerCase() || 'no-extension'
        key = ext
      }
      stats.set(key, (stats.get(key) ?? 0) + 1)
    })

    const items = Array.from(stats.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([name, count]) => ({ name, detail: `${count} 项` }))

    return {
      type: 'desktop' as const,
      summary: `桌面共 ${entries.length} 项（文件夹/文件类型统计）`,
      items,
    }
  } catch (err) {
    return {
      type: 'desktop' as const,
      summary: '桌面扫描失败',
      items: [],
      error: err instanceof Error ? err.message : String(err),
    }
  }
})

// IPC：本地安全 Shell 执行
ipcMain.on('shell:execute', (_event, id: string, command: string, cwd?: string, args?: string[]) => {
  function sendData(payload: { id: string; stdout?: string; stderr?: string; exitCode?: number | null }) {
    mainWindow?.webContents.send('shell:data', payload)
  }

  try {
    const resolvedCwd = resolveAllowedCwd(cwd)
    const { file, args: cmdArgs } = validateCommand(command, args)

    // 同 id 的旧进程先中止，避免泄漏
    const existing = shellProcesses.get(id)
    if (existing && !existing.killed) {
      existing.kill()
      shellProcesses.delete(id)
    }

    logLauncher('[shell:execute]', { id, command, cwd: resolvedCwd, args: cmdArgs })

    const { spawn } = require('child_process')

    // Windows 下 dir/echo 是 shell 内建命令，需通过 cmd /c 调用
    const needsCmdWrapper =
      process.platform === 'win32' && (file.toLowerCase() === 'dir' || file.toLowerCase() === 'echo')
    const proc = needsCmdWrapper
      ? spawn('cmd', ['/c', file, ...cmdArgs], { cwd: resolvedCwd, shell: false })
      : spawn(file, cmdArgs, { cwd: resolvedCwd, shell: false })

    shellProcesses.set(id, proc)

    proc.stdout?.on('data', (data: Buffer) => {
      sendData({ id, stdout: data.toString('utf-8') })
    })

    proc.stderr?.on('data', (data: Buffer) => {
      sendData({ id, stderr: data.toString('utf-8') })
    })

    proc.on('error', (err: Error) => {
      sendData({ id, stderr: `进程启动失败: ${err.message}`, exitCode: null })
      shellProcesses.delete(id)
    })

    proc.on('close', (code: number | null) => {
      sendData({ id, exitCode: code })
      shellProcesses.delete(id)
    })
  } catch (err) {
    sendData({ id, stderr: err instanceof Error ? err.message : String(err), exitCode: null })
  }
})

// IPC：中止本地 Shell 进程
ipcMain.on('shell:abort', (_event, id: string) => {
  const proc = shellProcesses.get(id)
  if (proc && !proc.killed) {
    logLauncher('[shell:abort]', id)
    proc.kill()
    shellProcesses.delete(id)
  }
})

// IPC：读取允许路径范围内的文本文件
ipcMain.handle('fs:readFile', async (_event, filePath: string) => {
  try {
    const target = resolveAllowedFilePath(filePath)
    const content = await fsPromises.readFile(target, 'utf-8')
    return { success: true, content }
  } catch (err) {
    return {
      success: false,
      error: err instanceof Error ? err.message : String(err),
    }
  }
})

// IPC：向允许路径范围内的文本文件写入内容
ipcMain.handle('fs:writeFile', async (_event, filePath: string, content: string) => {
  try {
    const target = resolveAllowedFilePath(filePath)
    await fsPromises.mkdir(path.dirname(target), { recursive: true })
    await fsPromises.writeFile(target, content, 'utf-8')
    return { success: true }
  } catch (err) {
    return {
      success: false,
      error: err instanceof Error ? err.message : String(err),
    }
  }
})
