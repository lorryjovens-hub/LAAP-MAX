"use strict";
const electron = require("electron");
electron.contextBridge.exposeInMainWorld("laapAPI", {
  baseUrl: "http://localhost:8081",
  wsUrl: "ws://localhost:8766"
});
