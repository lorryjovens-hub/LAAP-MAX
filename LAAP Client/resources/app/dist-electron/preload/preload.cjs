"use strict";
const electron = require("electron");
electron.contextBridge.exposeInMainWorld("desktop", {
  /**
   * 最小化窗口
   */
  minimize: () => electron.ipcRenderer.invoke("window:minimize"),
  /**
   * 最大化 / 还原窗口
   */
  maximize: () => electron.ipcRenderer.invoke("window:maximize"),
  /**
   * 关闭窗口（最小化到托盘）
   */
  close: () => electron.ipcRenderer.invoke("window:close"),
  /**
   * 切换全屏状态
   */
  toggleFullscreen: () => electron.ipcRenderer.invoke("window:toggleFullscreen"),
  /**
   * 获取当前窗口状态
   */
  getWindowState: () => electron.ipcRenderer.invoke("window:getState"),
  /**
   * 监听窗口状态变化
   */
  onWindowState: (callback) => {
    electron.ipcRenderer.on("window:stateChanged", (_event, state) => callback(state));
  },
  /**
   * 打开开发者工具
   */
  openDevTools: () => electron.ipcRenderer.send("window:openDevTools"),
  /**
   * 打开视频文件选择对话框
   */
  selectVideo: () => electron.ipcRenderer.invoke("desktop:selectVideo"),
  /**
   * 读取本地视频文件为 base64 数据
   */
  readVideoFile: (filePath) => electron.ipcRenderer.invoke("desktop:readVideoFile", filePath),
  /**
   * 监听全局 PTT 热键按下事件
   */
  onPttPressed: (callback) => {
    electron.ipcRenderer.on("voice:pttPressed", () => callback());
  },
  /**
   * 触发桌面悬浮通知
   */
  showOverlay: (payload) => electron.ipcRenderer.send("overlay:show", payload),
  /**
   * 监听悬浮通知显示事件（用于 overlay 渲染进程）
   */
  onOverlayShow: (callback) => {
    electron.ipcRenderer.on("overlay:show", (_event, payload) => callback(payload));
  },
  /**
   * 注册/更新全局热键
   */
  registerHotkeys: (hotkeys) => electron.ipcRenderer.invoke("hotkeys:register", hotkeys)
});
