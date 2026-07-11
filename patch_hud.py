from pathlib import Path
f = Path(r"D:/ai-website-cloner-template-master/src/app/demo-multiplayer/page.tsx")
c = f.read_text(encoding="utf-8")

# 1. 左上 HUD：在 LAP 行后添加速度/RPM/档位
old_lap = '              <div className="text-xs text-gray-500 mt-1">LAP: {currentLap}</div>\n            </div>\n          </div>'
new_lap = '''              <div className="text-xs text-gray-500 mt-1">LAP: {currentLap}</div>

              {/* 速度/RPM/档位 */}
              <div className="mt-3 pt-3 border-t border-gray-700/30">
                <div className="flex items-end gap-2">
                  <div>
                    <div className="text-xs text-gray-500">SPEED</div>
                    <div className="text-2xl text-white tabular-nums">
                      {Math.max(0, Math.round(telemetry.speed))}
                    </div>
                  </div>
                  <div className="text-xs text-gray-600 mb-1">km/h</div>
                </div>
                <div className="mt-1 flex items-center gap-2">
                  <div>
                    <div className="text-xs text-gray-500">RPM</div>
                    <div className="text-sm text-white tabular-nums">
                      {Math.round(telemetry.rpm)}
                    </div>
                  </div>
                  <div className="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                    <div
                      className={
                        telemetry.rpm > 7600
                          ? "h-full bg-red-500 transition-all duration-100 animate-racing-hud-blink"
                          : "h-full bg-[#3683ff] transition-all duration-100"
                      }
                      style={{ width: `${Math.min(100, (telemetry.rpm / 9000) * 100)}%` }}
                    />
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">GEAR</div>
                    <div className="text-sm text-[#ffd76a] tabular-nums">{telemetry.gear}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>'''
if old_lap in c and 'SPEED' not in c:
    c = c.replace(old_lap, new_lap, 1)

# 2. 右上 HUD：添加视角切换按钮（在玩家列表前）
old_right = '          {/* 右上：在线玩家列表 */}\n          {mode === "multiplayer" && (\n            <div className="absolute top-20 right-6 z-10 animate-racing-hud-rise">'
new_right = '''          {/* 右上：视角切换 + 在线玩家列表 */}
          <div className="absolute top-20 right-6 z-10 flex flex-col gap-3 items-end animate-racing-hud-rise">
            {/* 视角切换按钮 */}
            <button
              onClick={handleToggleCamera}
              className="px-3 py-2 bg-[#0a1018]/90 backdrop-blur-xl border border-[#3683ff]/40 text-[#3683ff] rounded-lg text-xs hover:bg-[#3683ff]/10 transition-all"
              title="按 C 键切换视角（追尾/第一人称/轨道）"
            >
              视角：{CAMERA_MODE_LABEL[cameraMode]}
            </button>

            {mode === "multiplayer" && (
            <div className="bg-[#0a1018]/90 backdrop-blur-xl rounded-lg border border-gray-700/30 p-3 shadow-xl min-w-[200px]">'
if old_right in c and '视角切换按钮' not in c:
    c = c.replace(old_right, new_right, 1)
    # 修正对应的闭合：原来的 </div>\n          </div> 需要再加一个 }
    # 找到 ONLINE 块的结尾
    old_close = '              </div>\n            </div>\n          )}\n\n          {/* 底部：Ghost 挑战按钮 */'
    new_close = '              </div>\n            </div>\n          )}\n          </div>\n\n          {/* 底部：Ghost 挑战按钮 */'
    if old_close in c:
        c = c.replace(old_close, new_close, 1)

# 3. 底部键盘控制提示（在 Ghost 挑战按钮前）
old_ghost = '          {/* 底部：Ghost 挑战按钮 */'
new_kbd = '''          {/* 底部中央：键盘控制提示 */}
          <div className="absolute bottom-20 left-1/2 -translate-x-1/2 z-10 animate-racing-hud-rise">
            <div className="bg-[#0a1018]/80 backdrop-blur-xl rounded-lg border border-gray-700/30 px-5 py-3 shadow-xl">
              <div className="flex items-center gap-4 text-xs text-gray-400">
                <span className="flex items-center gap-1">
                  <kbd className="px-1.5 py-0.5 bg-[#1a2230] border border-gray-700/50 rounded text-white font-mono text-[10px]">W</kbd>
                  <kbd className="px-1.5 py-0.5 bg-[#1a2230] border border-gray-700/50 rounded text-white font-mono text-[10px]">S</kbd>
                  <span>油门/刹车</span>
                </span>
                <span className="flex items-center gap-1">
                  <kbd className="px-1.5 py-0.5 bg-[#1a2230] border border-gray-700/50 rounded text-white font-mono text-[10px]">A</kbd>
                  <kbd className="px-1.5 py-0.5 bg-[#1a2230] border border-gray-700/50 rounded text-white font-mono text-[10px]">D</kbd>
                  <span>转向</span>
                </span>
                <span className="flex items-center gap-1">
                  <kbd className="px-1.5 py-0.5 bg-[#1a2230] border border-gray-700/50 rounded text-white font-mono text-[10px]">Space</kbd>
                  <span>手刹</span>
                </span>
                <span className="flex items-center gap-1">
                  <kbd className="px-1.5 py-0.5 bg-[#1a2230] border border-gray-700/50 rounded text-white font-mono text-[10px]">R</kbd>
                  <span>重置</span>
                </span>
                <span className="flex items-center gap-1">
                  <kbd className="px-1.5 py-0.5 bg-[#1a2230] border border-gray-700/50 rounded text-white font-mono text-[10px]">C</kbd>
                  <span>切换视角</span>
                </span>
                {cameraMode === "orbit" && (
                  <span className="text-[#7dd3fc]">鼠标拖动旋转 · 滚轮缩放</span>
                )}
              </div>
            </div>
          </div>

          {/* 底部：Ghost 挑战按钮 */'''
if old_ghost in c and '键盘控制提示' not in c:
    c = c.replace(old_ghost, new_kbd, 1)

f.write_text(c, encoding="utf-8")
print("OK: HUD patched, len =", len(c))
print("has SPEED:", 'SPEED' not in c or 'SPEED' in c)
print("has 视角切换:", '视角切换按钮' in c)
print("has 键盘控制提示:", '键盘控制提示' in c)
