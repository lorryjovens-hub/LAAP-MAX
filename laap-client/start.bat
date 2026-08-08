@echo off
chcp 65001 >nul
title LAAP Client

echo ========================================
echo   LAAP Client — 一键启动
echo ========================================
echo.

:: 杀掉残留的 Node.js 进程
taskkill /f /im node.exe >nul 2>&1
timeout /t 1 /nobreak >nul

:: 启动后端 (laap-server.cjs) — 端口 8763（避免端口冲突）
echo [1/2] 启动后端服务...
start "LAAP Backend" cmd /c "cd /d D:\LAAP\laap-client && node laap-server.cjs 8763"
echo        ✅ 后端 → ws://127.0.0.1:8763
echo        ✅ LLM 代理: DeepSeek / OpenAI / MiniMax / Qwen / Moonshot / 智谱 / 小米
echo        ✅ TTS 代理: OpenAI TTS
echo.

timeout /t 2 /nobreak >nul

:: 启动前端 (Vite dev server)，指定后端地址
echo [2/2] 启动前端...
start "LAAP Frontend" cmd /c "cd /d D:\LAAP\laap-client && set VITE_BACKEND_URL=ws://127.0.0.1:8763 && npx vite --host --port 5173"
echo        ✅ 前端 → http://localhost:5173
echo.

timeout /t 3 /nobreak >nul

:: 打开浏览器
start http://localhost:5173

echo ========================================
echo   LAAP Client 已启动！
echo.
echo   前端: http://localhost:5173
echo   后端: ws://127.0.0.1:8763
echo.
echo   使用指南:
echo   1. 点右上角 ⚙️ 设置 → LLM tab → 选服务商填 Key
echo   2. 在聊天框发消息 → 自动调真实 LLM API
echo   3. 右侧 8 个面板查看系统状态
echo.
echo   关闭: 任务管理器结束 Node.js 进程
echo ========================================
echo.
pause