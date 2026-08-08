"use strict";
var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));
const electron = require("electron");
const fs = require("fs");
const path = require("path");
electron.app.commandLine.appendSwitch("disable-background-timer-throttling");
electron.app.commandLine.appendSwitch("disable-renderer-backgrounding");
electron.app.commandLine.appendSwitch("disable-backgrounding-occluded-windows");
electron.app.commandLine.appendSwitch("enable-gpu-rasterization");
electron.app.commandLine.appendSwitch("enable-accelerated-2d-canvas");
let mainWindow = null;
let splashWindow = null;
let tray = null;
let overlayWindow = null;
const windowStatePath = path.join(electron.app.getPath("userData"), "window-state.json");
function loadWindowState() {
  const defaultState = {
    width: 1280,
    height: 720,
    isMaximized: false,
    isFullScreen: false
  };
  try {
    if (fs.existsSync(windowStatePath)) {
      const raw = fs.readFileSync(windowStatePath, "utf-8");
      const parsed = JSON.parse(raw);
      return { ...defaultState, ...parsed };
    }
  } catch (err) {
    console.error("[ERROR] 读取窗口状态失败:", err);
  }
  return defaultState;
}
function saveWindowState() {
  if (!mainWindow) return;
  try {
    const bounds = mainWindow.getBounds();
    const state = {
      width: bounds.width,
      height: bounds.height,
      x: bounds.x,
      y: bounds.y,
      isMaximized: mainWindow.isMaximized(),
      isFullScreen: mainWindow.isFullScreen()
    };
    fs.writeFileSync(windowStatePath, JSON.stringify(state, null, 2));
  } catch (err) {
    console.error("[ERROR] 保存窗口状态失败:", err);
  }
}
function ensureVisible(state) {
  const displays = electron.screen.getAllDisplays();
  if (displays.length === 0) return state;
  const { x = 0, y = 0, width, height } = state;
  const windowRect = { x, y, width, height };
  const isVisible = displays.some((display) => {
    const { workArea } = display;
    return windowRect.x < workArea.x + workArea.width && windowRect.x + windowRect.width > workArea.x && windowRect.y < workArea.y + workArea.height && windowRect.y + windowRect.height > workArea.y;
  });
  if (!isVisible) {
    const primary = electron.screen.getPrimaryDisplay().workArea;
    return {
      ...state,
      x: primary.x + Math.round((primary.width - width) / 2),
      y: primary.y + Math.round((primary.height - height) / 2)
    };
  }
  return state;
}
function getTrayIconPath() {
  if (process.env.NODE_ENV === "development") {
    return path.join(__dirname, "../../public/logo-32.png");
  }
  return path.join(__dirname, "../../dist/logo-32.png");
}
function createTray() {
  const iconPath = getTrayIconPath();
  tray = new electron.Tray(iconPath);
  tray.setToolTip("LAAP Client");
  const contextMenu = electron.Menu.buildFromTemplate([
    {
      label: "显示主窗口",
      click: () => {
        showMainWindow();
      }
    },
    {
      label: "退出",
      click: () => {
        electron.app.isQuiting = true;
        electron.app.quit();
      }
    }
  ]);
  tray.setContextMenu(contextMenu);
  tray.on("click", () => {
    showMainWindow();
  });
}
function showMainWindow() {
  if (!mainWindow) {
    createWindow();
    return;
  }
  if (mainWindow.isMinimized()) {
    mainWindow.restore();
  }
  mainWindow.show();
  mainWindow.focus();
}
function hideMainWindow() {
  mainWindow == null ? void 0 : mainWindow.hide();
}
function toggleMainWindow() {
  if (!mainWindow) {
    createWindow();
    return;
  }
  if (mainWindow.isVisible() && !mainWindow.isMinimized()) {
    hideMainWindow();
  } else {
    showMainWindow();
  }
}
function createSplashWindow() {
  splashWindow = new electron.BrowserWindow({
    width: 420,
    height: 320,
    frame: false,
    transparent: true,
    backgroundColor: "#00000000",
    alwaysOnTop: true,
    skipTaskbar: true,
    resizable: false,
    movable: true,
    webPreferences: {
      preload: path.join(__dirname, "../preload/preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false
    }
  });
  splashWindow.center();
  if (process.env.NODE_ENV === "development") {
    splashWindow.loadFile(path.join(__dirname, "../../public/splash.html"));
  } else {
    splashWindow.loadFile(path.join(__dirname, "../../dist/splash.html"));
  }
  splashWindow.on("closed", () => {
    splashWindow = null;
  });
}
function createOverlayWindow() {
  const primary = electron.screen.getPrimaryDisplay().workArea;
  const width = 360;
  const height = 120;
  overlayWindow = new electron.BrowserWindow({
    width,
    height,
    x: primary.x + primary.width - width - 20,
    y: primary.y + 40,
    frame: false,
    transparent: true,
    backgroundColor: "#00000000",
    alwaysOnTop: true,
    skipTaskbar: true,
    focusable: false,
    show: false,
    resizable: false,
    movable: false,
    webPreferences: {
      preload: path.join(__dirname, "../preload/preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
      backgroundThrottling: false
    }
  });
  if (process.env.NODE_ENV === "development") {
    overlayWindow.loadURL("http://localhost:5173/overlay.html");
  } else {
    overlayWindow.loadFile(path.join(__dirname, "../../dist/overlay.html"));
  }
  overlayWindow.on("closed", () => {
    overlayWindow = null;
  });
}
function showOverlay(title, content) {
  if (!overlayWindow) {
    createOverlayWindow();
  }
  if (!overlayWindow) return;
  overlayWindow.webContents.send("overlay:show", { title, content });
  overlayWindow.showInactive();
  overlayWindow.setOpacity(0);
  let opacity = 0;
  const fadeIn = setInterval(() => {
    opacity += 0.1;
    overlayWindow == null ? void 0 : overlayWindow.setOpacity(Math.min(1, opacity));
    if (opacity >= 1) clearInterval(fadeIn);
  }, 30);
  setTimeout(() => {
    let fadeOpacity = 1;
    const fadeOut = setInterval(() => {
      fadeOpacity -= 0.05;
      overlayWindow == null ? void 0 : overlayWindow.setOpacity(Math.max(0, fadeOpacity));
      if (fadeOpacity <= 0) {
        clearInterval(fadeOut);
        overlayWindow == null ? void 0 : overlayWindow.hide();
      }
    }, 40);
  }, 3e3);
}
let currentHotkeys = {
  showWindow: "CommandOrControl+Shift+L",
  ptt: "CommandOrControl+Shift+Space"
};
function registerGlobalShortcuts(hotkeys = currentHotkeys) {
  electron.globalShortcut.unregisterAll();
  currentHotkeys = hotkeys;
  if (hotkeys.showWindow) {
    electron.globalShortcut.register(hotkeys.showWindow, () => {
      toggleMainWindow();
    });
  }
  if (hotkeys.ptt) {
    electron.globalShortcut.register(hotkeys.ptt, () => {
      mainWindow == null ? void 0 : mainWindow.webContents.send("voice:pttPressed");
    });
  }
}
function updateGlobalShortcuts(hotkeys) {
  registerGlobalShortcuts(hotkeys);
}
function createWindow() {
  const savedState = ensureVisible(loadWindowState());
  mainWindow = new electron.BrowserWindow({
    width: savedState.width,
    height: savedState.height,
    x: savedState.x,
    y: savedState.y,
    minWidth: 960,
    minHeight: 540,
    title: "LAAP Client",
    icon: path.join(__dirname, "../../public/logo-256.png"),
    show: false,
    // 无边框 + 透明背景
    frame: false,
    transparent: true,
    backgroundColor: "#00000000",
    webPreferences: {
      // 预加载脚本路径（相对于主进程构建产物）
      preload: path.join(__dirname, "../preload/preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
      backgroundThrottling: false
    }
  });
  if (savedState.isFullScreen) {
    mainWindow.setFullScreen(true);
  } else if (savedState.isMaximized) {
    mainWindow.maximize();
  }
  if (process.env.NODE_ENV === "development") {
    mainWindow.loadURL("http://localhost:5173");
  } else {
    mainWindow.loadFile(path.join(__dirname, "../../dist/index.html"));
  }
  mainWindow.once("ready-to-show", () => {
    splashWindow == null ? void 0 : splashWindow.close();
    mainWindow == null ? void 0 : mainWindow.show();
  });
  mainWindow.on("maximize", broadcastWindowState);
  mainWindow.on("unmaximize", broadcastWindowState);
  mainWindow.on("enter-full-screen", broadcastWindowState);
  mainWindow.on("leave-full-screen", broadcastWindowState);
  mainWindow.on("minimize", broadcastWindowState);
  mainWindow.on("restore", broadcastWindowState);
  const saveDebounced = debounce(saveWindowState, 250);
  mainWindow.on("move", saveDebounced);
  mainWindow.on("resize", saveDebounced);
  mainWindow.on("maximize", saveDebounced);
  mainWindow.on("unmaximize", saveDebounced);
  mainWindow.on("enter-full-screen", saveDebounced);
  mainWindow.on("leave-full-screen", saveDebounced);
  mainWindow.on("close", (event) => {
    if (!electron.app.isQuiting) {
      event.preventDefault();
      hideMainWindow();
    } else {
      saveWindowState();
    }
  });
  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}
function debounce(fn, wait) {
  let timer = null;
  return (...args) => {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => fn(...args), wait);
  };
}
function getWindowState() {
  return {
    isMaximized: (mainWindow == null ? void 0 : mainWindow.isMaximized()) ?? false,
    isFullScreen: (mainWindow == null ? void 0 : mainWindow.isFullScreen()) ?? false,
    isMinimized: (mainWindow == null ? void 0 : mainWindow.isMinimized()) ?? false
  };
}
function broadcastWindowState() {
  const state = getWindowState();
  mainWindow == null ? void 0 : mainWindow.webContents.send("window:stateChanged", state);
}
electron.app.whenReady().then(async () => {
  try {
    const { startLaapMockServer: startLaapMockServer2 } = await Promise.resolve().then(() => mockServer);
    await startLaapMockServer2();
  } catch (err) {
    console.error("[Main] 启动 Mock Server 失败:", err);
  }
  createSplashWindow();
  createWindow();
  createTray();
  createOverlayWindow();
  registerGlobalShortcuts();
  electron.app.on("activate", () => {
    if (electron.BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    } else {
      showMainWindow();
    }
  });
});
electron.app.on("window-all-closed", () => {
  if (process.platform !== "darwin") ;
});
electron.app.on("will-quit", () => {
  electron.globalShortcut.unregisterAll();
});
electron.ipcMain.handle("window:minimize", () => {
  mainWindow == null ? void 0 : mainWindow.minimize();
});
electron.ipcMain.handle("window:maximize", () => {
  if (mainWindow == null ? void 0 : mainWindow.isMaximized()) {
    mainWindow.unmaximize();
  } else {
    mainWindow == null ? void 0 : mainWindow.maximize();
  }
});
electron.ipcMain.handle("window:close", () => {
  hideMainWindow();
});
electron.ipcMain.handle("window:toggleFullscreen", () => {
  const isFullScreen = (mainWindow == null ? void 0 : mainWindow.isFullScreen()) ?? false;
  mainWindow == null ? void 0 : mainWindow.setFullScreen(!isFullScreen);
});
electron.ipcMain.handle("window:getState", () => {
  return getWindowState();
});
electron.ipcMain.on("window:openDevTools", () => {
  mainWindow == null ? void 0 : mainWindow.webContents.openDevTools({ mode: "detach" });
});
electron.ipcMain.on("overlay:show", (_event, { title, content }) => {
  showOverlay(title, content);
});
electron.ipcMain.handle("hotkeys:register", (_event, hotkeys) => {
  updateGlobalShortcuts(hotkeys);
});
function inferVideoMime(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  switch (ext) {
    case ".webm":
      return "video/webm";
    case ".mov":
      return "video/quicktime";
    case ".mkv":
      return "video/x-matroska";
    case ".avi":
      return "video/x-msvideo";
    case ".mp4":
    default:
      return "video/mp4";
  }
}
electron.ipcMain.handle("desktop:selectVideo", async () => {
  if (!mainWindow) return { canceled: true };
  const result = await electron.dialog.showOpenDialog(mainWindow, {
    properties: ["openFile"],
    filters: [
      {
        name: "视频文件",
        extensions: ["mp4", "webm", "mov", "mkv", "avi"]
      }
    ]
  });
  return {
    canceled: result.canceled,
    filePath: result.filePaths[0]
  };
});
electron.ipcMain.handle("desktop:readVideoFile", async (_event, filePath) => {
  try {
    if (!fs.existsSync(filePath)) {
      return { exists: false, data: "", type: "" };
    }
    const buffer = fs.readFileSync(filePath);
    return {
      exists: true,
      data: buffer.toString("base64"),
      type: inferVideoMime(filePath)
    };
  } catch (err) {
    return {
      exists: false,
      data: "",
      type: "",
      error: err instanceof Error ? err.message : String(err)
    };
  }
});
function generateBeepWavBase64() {
  const sampleRate = 8e3;
  const duration = 1;
  const frequency = 440;
  const numSamples = sampleRate * duration;
  const buffer = new ArrayBuffer(44 + numSamples * 2);
  const view = new DataView(buffer);
  const writeString = (offset, str) => {
    for (let i = 0; i < str.length; i += 1) {
      view.setUint8(offset + i, str.charCodeAt(i));
    }
  };
  writeString(0, "RIFF");
  view.setUint32(4, 36 + numSamples * 2, true);
  writeString(8, "WAVE");
  writeString(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeString(36, "data");
  view.setUint32(40, numSamples * 2, true);
  for (let i = 0; i < numSamples; i += 1) {
    const t = i / sampleRate;
    const sample = Math.sin(2 * Math.PI * frequency * t) * 0.5;
    const value = Math.max(-1, Math.min(1, sample));
    view.setInt16(44 + i * 2, value * 32767, true);
  }
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (let i = 0; i < bytes.byteLength; i += 1) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}
function generateId() {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}
function createMessage(topic, type, payload, sender = "mock-backend") {
  return {
    id: generateId(),
    type,
    topic,
    payload,
    timestamp: Date.now(),
    sender
  };
}
const PSI_PHASES = ["perception", "selection", "integration", "learning"];
const colonyAgents = [
  { id: "agent-1", name: "Aris", status: "online", role: "协调者", resource: 78 },
  { id: "agent-2", name: "Codex", status: "busy", role: "代码专家", resource: 62 },
  { id: "agent-3", name: "Guardian", status: "offline", role: "安全审查", resource: 0 },
  { id: "agent-4", name: "Nexus", status: "online", role: "记忆检索", resource: 55 }
];
const colonyEdges = [
  { id: "e1", from: "agent-1", to: "agent-2", label: "任务分派", intensity: 0.8 },
  { id: "e2", from: "agent-2", to: "agent-3", label: "代码审查", intensity: 0.5 },
  { id: "e3", from: "agent-3", to: "agent-1", label: "报告风险", intensity: 0.3 },
  { id: "e4", from: "agent-4", to: "agent-1", label: "上下文同步", intensity: 0.6 }
];
const colonyMessageTemplates = [
  { from: "agent-1", to: "agent-2", summary: "请优化推理链" },
  { from: "agent-2", to: "agent-3", summary: "请求安全审计" },
  { from: "agent-3", to: "agent-1", summary: "发现潜在风险" },
  { from: "agent-4", to: "agent-1", summary: "已召回相关记忆" }
];
function generateColonyMessage(tick) {
  const template = colonyMessageTemplates[tick % colonyMessageTemplates.length];
  return {
    id: generateId(),
    ...template,
    summary: `${template.summary} #${tick}`,
    timestamp: Date.now()
  };
}
function buildScenePatch(tick) {
  const index = tick % 8 + 1;
  switch (index) {
    case 1:
      return {
        kind: "metric",
        label: "CPU 占用",
        value: Math.round(20 + Math.random() * 60),
        unit: "%"
      };
    case 2:
      return {
        kind: "text",
        content: `动态场景内容 #${tick}，由 mock server 生成。`
      };
    case 3:
      return {
        kind: "choice",
        content: "请选择下一步操作",
        options: ["继续对话", "执行工具", "查看场景"],
        selected: "继续对话"
      };
    case 4:
      return {
        kind: "progress",
        label: "任务进度",
        value: Math.round(Math.random() * 100),
        max: 100
      };
    case 5:
      return {
        kind: "weather",
        location: "上海",
        temperature: Math.round(18 + Math.random() * 12),
        condition: tick % 2 === 0 ? "晴" : "多云"
      };
    case 6:
      return {
        kind: "image",
        src: "/logo.svg",
        alt: "LAAP Logo"
      };
    case 7:
      return {
        kind: "media",
        src: "/logo.svg",
        caption: "示例媒体面片"
      };
    case 8:
      return {
        kind: "layout",
        title: "主布局",
        children: ["surface-1", "surface-2", "surface-3"]
      };
    default:
      return { kind: "text", content: `默认内容 #${tick}` };
  }
}
async function startLaapMockServer(options = {}) {
  const { WebSocketServer } = await import("ws");
  const port = options.port ?? 8765;
  const host = options.host ?? "127.0.0.1";
  const psiEventIntervalMs = options.psiEventIntervalMs ?? 1;
  const lifecycleIntervalMs = options.lifecycleIntervalMs ?? 2500;
  const wss = new WebSocketServer({ host, port });
  console.log(`[MockServer] WebSocket 监听 ws://${host}:${port}`);
  wss.on("connection", (ws) => {
    console.log("[MockServer] 客户端已连接");
    let psiPhaseIndex = 0;
    let psiProgress = 0;
    let lifecycleTick = 0;
    const psiTimer = setInterval(() => {
      if (ws.readyState !== 1) return;
      psiProgress += 0.05;
      if (psiProgress >= 1) {
        psiProgress = 0;
        psiPhaseIndex = (psiPhaseIndex + 1) % PSI_PHASES.length;
      }
      const phase = PSI_PHASES[psiPhaseIndex];
      const msg = createMessage("v12_kernel", "v12_kernel", {
        phase,
        progress: Math.min(1, psiProgress),
        frequencyHz: 1e3 + Math.floor(Math.random() * 1e3)
      });
      ws.send(JSON.stringify(msg));
    }, psiEventIntervalMs);
    const lifecycleTimer = setInterval(() => {
      if (ws.readyState !== 1) return;
      lifecycleTick += 1;
      const needs = ["need_curiosity", "need_trust", "need_competence"];
      const needTopic = needs[lifecycleTick % needs.length];
      ws.send(
        JSON.stringify(
          createMessage(needTopic, "need_update", {
            value: 0.3 + Math.random() * 0.6,
            delta: (Math.random() - 0.5) * 0.1
          })
        )
      );
      const emotions = ["emotion_pleasure", "emotion_arousal", "emotion_dominance", "emotion_sociality", "emotion_stress"];
      emotions.forEach((emotion) => {
        ws.send(
          JSON.stringify(
            createMessage(emotion, "emotion_update", {
              value: Math.random()
            })
          )
        );
      });
      if (lifecycleTick % 3 === 0) {
        ws.send(
          JSON.stringify(
            createMessage("harness_execution_result", "harness_execution_result", {
              success: Math.random() > 0.2,
              durationMs: 120 + Math.floor(Math.random() * 400),
              output: `mock-execution-${lifecycleTick}`
            })
          )
        );
      }
      const surfaceId = `surface-${lifecycleTick % 8 + 1}`;
      const patch = buildScenePatch(lifecycleTick);
      ws.send(
        JSON.stringify(
          createMessage("scene.patch", "scene_patch", {
            surfaceId,
            patch
          })
        )
      );
      colonyAgents.forEach((agent) => {
        if (Math.random() > 0.7) {
          const statuses = ["online", "busy", "offline"];
          agent.status = statuses[Math.floor(Math.random() * statuses.length)];
        }
        agent.resource = Math.min(100, Math.max(0, (agent.resource ?? 50) + Math.round((Math.random() - 0.5) * 10)));
      });
      ws.send(
        JSON.stringify(
          createMessage("colony.agent", "colony_update", {
            agents: colonyAgents.map((a) => ({ ...a })),
            edges: colonyEdges.map((e) => ({ ...e })),
            messages: [generateColonyMessage(lifecycleTick)]
          })
        )
      );
    }, lifecycleIntervalMs);
    ws.on("message", (rawData) => {
      const data = Buffer.isBuffer(rawData) ? rawData.toString("utf-8") : String(rawData);
      let message;
      try {
        message = JSON.parse(data);
      } catch {
        console.warn("[MockServer] 收到非 JSON 消息:", data.slice(0, 200));
        return;
      }
      console.log("[MockServer] 收到消息:", message.topic);
      if (message.topic === "ping") {
        ws.send(JSON.stringify(createMessage("pong", "pong", { timestamp: message.timestamp })));
        return;
      }
      if (message.topic === "tool.retry") {
        const payload = message.payload;
        const toolCall = payload == null ? void 0 : payload.toolCall;
        if (toolCall) {
          ws.send(
            JSON.stringify(
              createMessage("tool_call", "tool_call", {
                toolCall: {
                  id: toolCall.id ?? generateId(),
                  name: toolCall.name ?? "mock_search",
                  arguments: toolCall.arguments ?? {},
                  status: "running"
                }
              })
            )
          );
          setTimeout(() => {
            ws.send(
              JSON.stringify(
                createMessage("tool_result", "tool_result", {
                  toolCall: {
                    id: toolCall.id ?? generateId(),
                    name: toolCall.name ?? "mock_search",
                    arguments: toolCall.arguments ?? {},
                    status: "success",
                    result: { found: true, summary: "重新执行后的模拟结果" }
                  }
                })
              )
            );
          }, 300);
        }
        return;
      }
      if (message.topic === "user.input") {
        const text = message.payload.text ?? "";
        streamReply(ws, text);
      }
      if (message.topic === "voice.input") {
        handleVoiceInput(ws, message);
      }
    });
    ws.on("close", () => {
      console.log("[MockServer] 客户端已断开");
      clearInterval(psiTimer);
      clearInterval(lifecycleTimer);
    });
  });
  return () => {
    wss.clients.forEach((client) => {
      client.terminate();
    });
    wss.close();
    console.log("[MockServer] 已关闭");
  };
}
function handleVoiceInput(ws, message) {
  const audio = message.payload.audio ?? "";
  const length = Math.min(audio.length, 120);
  const mockText = `收到语音输入（长度 ${length}），这是模拟识别结果。`;
  setTimeout(() => {
    if (ws.readyState !== 1) return;
    ws.send(
      JSON.stringify(
        createMessage("voice.recognized", "voice_recognized", {
          text: mockText,
          confidence: 0.85
        })
      )
    );
    setTimeout(() => {
      if (ws.readyState !== 1) return;
      const ttsPayload = {
        speaking: true,
        text: "好的，已收到您的语音指令。"
      };
      {
        ttsPayload.audioBase64 = generateBeepWavBase64();
        ttsPayload.mimeType = "audio/wav";
      }
      ws.send(JSON.stringify(createMessage("voice.tts", "voice_tts", ttsPayload)));
    }, 400);
  }, 300);
}
function streamReply(ws, userText) {
  const replyId = generateId();
  setTimeout(() => {
    if (ws.readyState !== 1) return;
    ws.send(
      JSON.stringify(
        createMessage("chunk", "stream_chunk", {
          replyId,
          text: `收到消息：${userText}
`
        })
      )
    );
    setTimeout(() => {
      ws.send(
        JSON.stringify(
          createMessage("thought_chunk", "thought_chunk", {
            replyId,
            text: "正在分析用户意图...",
            type: "reasoning",
            confidence: 0.92
          })
        )
      );
      setTimeout(() => {
        const toolId = generateId();
        ws.send(
          JSON.stringify(
            createMessage("tool_call", "tool_call", {
              replyId,
              toolCall: {
                id: toolId,
                name: "mock_search",
                arguments: { query: userText.slice(0, 20) },
                status: "running"
              }
            })
          )
        );
        setTimeout(() => {
          ws.send(
            JSON.stringify(
              createMessage("tool_result", "tool_result", {
                replyId,
                toolCall: {
                  id: toolId,
                  name: "mock_search",
                  arguments: { query: userText.slice(0, 20) },
                  status: "success",
                  result: { found: true, summary: "模拟检索结果" }
                }
              })
            )
          );
          setTimeout(() => {
            ws.send(
              JSON.stringify(
                createMessage(
                  "harness_execution_result",
                  "harness_execution_result",
                  {
                    replyId,
                    success: true,
                    durationMs: 560,
                    output: "流式回复完成"
                  }
                )
              )
            );
          }, 120);
        }, 200);
      }, 180);
    }, 160);
  }, 500);
}
const mockServer = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  startLaapMockServer
}, Symbol.toStringTag, { value: "Module" }));
