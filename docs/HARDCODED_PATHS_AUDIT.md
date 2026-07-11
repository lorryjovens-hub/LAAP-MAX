# LAAP 硬编码路径审计报告

## 扫描方法

- 扫描范围：`d:\LAAP` 全仓库（排除了 `.git/`、`.venv/`、`node_modules/` 等二进制/依赖目录，但保留了 `_archive/`、`external/` 的统计）。
- 扫描模式：
  - Windows 绝对路径：`[A-Za-z]:\\`
  - Unix 绝对路径：`/(home|Users|opt|tmp)/`
- 重点关注文件：
  - `laap/ui/tui.py`
  - `laap/agent_core/hermes_tool_bridge.py`
  - `laap/agi/hermes_integration.py`
  - `laap/agi/guardian.py`
  - `laap/agi/safety.py`
  - `laap/agi/rsi_engine.py`

## 关键发现

1. **TUI 视频路径写死**：`laap/ui/tui.py:652` 直接写死 `D:\LAAP\.trae\specs\integrate-aether-orchestration-into-laap\互动视频.mp4`，这是本次路径模块要重点解决的场景。
2. **Hermes 根目录散落多处**：`laap/agent_core/hermes_tool_bridge.py`、`laap/agi/hermes_integration.py`、`laap/hermes_bridge.py`、`laap/handshake.py`、`laap/agent_core/laap_agent.py`、`laap/agent_core/agent.py` 都各自维护一份 `D:\hermes-agent-main (1)\hermes-agent-main` 等候选路径列表。
3. **LAAP 根目录默认 fallback 为 `D:\LAAP`**：`laap/agi/evolution_engine.py`、`laap/agi/code_minimizer.py`、`laap/agi/multi_agent.py`、`laap/agi/quality_assurance.py`、`laap/agi/self_healing.py`、`laap/agi/heartbeat_daemon.py` 等大量文件在环境变量缺失时默认使用 `D:\LAAP`。
4. **aris_brain 与启动脚本大量硬编码**：`.bat`/`.ps1`/`.cmd` 启动脚本、aris_brain 内的桥接/守护进程几乎全部采用 `D:\LAAP`、`D:\hermes-agent-main (1)\hermes-agent-main`、`C:\Python313\python.exe` 等绝对路径。
5. **测试与调试脚本写死 `D:\LAAP`**：`tests/`、`debug_*.py`、`tmp_tui_test*.py` 中大量 `sys.path.insert(0, r"D:\LAAP")` 或 `ProjectPerception(root_path="d:\\LAAP")`。
6. **模型/语音缓存路径写死在用户目录**：`test_moss_tts.py`、`moss_realtime_server.py`、`laap/voicetools/*.py` 使用 `E:\models\...` 或 `C:\Users\user\AppData\Local\hermes\audio_cache\...`。
7. **`external/` 与 `_archive/` 为第三方/历史代码**：包含大量硬编码路径，不建议纳入当前运行时路径治理，应视为外部依赖。

## 扫描结果统计

| 区域 | Windows 路径命中 | Unix 路径命中 | 备注 |
|------|------------------|---------------|------|
| `laap/`（运行时包） | 约 80+ | 约 10+ | 业务代码，需统一治理 |
| 根目录脚本/调试文件 | 约 60+ | 约 5+ | `.bat`/`.ps1`/`.py` 等 |
| `aris_brain/` | 约 50+ | 约 5+ | 旧版 Aris 脑模块 |
| `tests/` | 约 40+ | 约 5+ | 测试代码 |
| `_archive/` | 约 30+ | 约 40+ | 历史归档，建议不改动 |
| `external/` | 约 10+ | 约 30+ | 第三方依赖，建议不改动 |

> 注：以上数字为近似值，含注释、字符串、正则表达式与示例数据。

## 重点硬编码路径清单

### 1. `laap/` 运行时包

| 文件路径 | 行号 | 当前硬编码值 | 用途说明 | 建议替换方式 |
|----------|------|--------------|----------|--------------|
| `laap/ui/tui.py` | 652 | `D:\LAAP\.trae\specs\integrate-aether-orchestration-into-laap\互动视频.mp4` | TUI 左侧互动视频播放器加载路径 | `get_video_dir()` / `LAAP_VIDEO_DIR` |
| `laap/ui/dragon_logo.py` | 38 | `D:\LAAP\龙logo.jpg` | Logo 图片默认路径候选 | `get_laap_root() / "龙logo.jpg"` 或配置项 |
| `laap/agent_core/hermes_tool_bridge.py` | 46 | `D:\hermes-agent-main (1)\hermes-agent-main` | Hermes 根目录常量 | `get_hermes_root()` / `HERMES_ROOT` |
| `laap/agent_core/hermes_tool_bridge.py` | 47 | `D:\LAAP` | LAAP 根目录常量 | `get_laap_root()` / `LAAP_ROOT` |
| `laap/agent_core/agent.py` | 300 | `D:\hermes-agent-main\hermes-agent-main` | Hermes 检测候选路径 | `get_hermes_root()` |
| `laap/agent_core/agent.py` | 301 | `D:\hermes-agent-main (1)\hermes-agent-main` | Hermes 检测候选路径 | `get_hermes_root()` |
| `laap/agent_core/laap_agent.py` | 36 | `D:\hermes-agent-main\hermes-agent-main` | Hermes 检测候选路径 | `get_hermes_root()` |
| `laap/agent_core/laap_agent.py` | 37 | `D:\hermes-agent-main (1)\hermes-agent-main` | Hermes 检测候选路径 | `get_hermes_root()` |
| `laap/agi/hermes_integration.py` | 67 | `D:\hermes-agent-LAAP数字生命版\hermes-agent-LAAP` | Hermes 检测候选路径 | `get_hermes_root()` |
| `laap/agi/hermes_integration.py` | 68 | `D:\hermes-agent-main (1)\hermes-agent-main` | Hermes 检测候选路径 | `get_hermes_root()` |
| `laap/hermes_bridge.py` | 58 | `D:\hermes-agent-LAAP数字生命版\hermes-agent-LAAP` | Hermes 检测候选路径 | `get_hermes_root()` |
| `laap/hermes_bridge.py` | 59 | `D:\hermes-agent-main (1)\hermes-agent-main` | Hermes 检测候选路径 | `get_hermes_root()` |
| `laap/handshake.py` | 546 | `D:\hermes-agent-main (1)\hermes-agent-main` | Hermes 检测候选路径 | `get_hermes_root()` |
| `laap/handshake.py` | 547 | `D:\hermes-agent-LAAP数字生命版\hermes-agent-LAAP` | Hermes 检测候选路径 | `get_hermes_root()` |
| `laap/agi/evolution_engine.py` | 27 | `D:\LAAP` | LAAP_ROOT 默认值 | `get_laap_root()` |
| `laap/agi/evolution_engine.py` | 150-154 | `D:\LAAP\external_{repo.name}\...` | LLM 提示词中写死的相对建议路径 | 使用 `get_laap_root()` 拼接 |
| `laap/agi/code_minimizer.py` | 115, 400, 478, 645, 700 | `D:\LAAP` | LAAP_ROOT 默认值/回退 | `get_laap_root()` |
| `laap/agi/code_evolution.py` | 802, 981 | `D:\LAAP` | repo_root 默认值 | `get_laap_root()` |
| `laap/agi/multi_agent.py` | 348, 486 | `D:\LAAP` | repo_root 默认值 | `get_laap_root()` |
| `laap/agi/quality_assurance.py` | 235, 453, 584, 704 | `D:\LAAP` | repo_root 默认值 | `get_laap_root()` |
| `laap/agi/self_healing.py` | 271, 396, 504 | `D:\LAAP` | repo_root 默认值 | `get_laap_root()` |
| `laap/agi/self_healing.py` | 319, 338, 363, 364 | `'D:\\LAAP'` | 生成修复代码片段中硬编码 | 使用 `get_laap_root()` 生成 |
| `laap/agi/heartbeat_daemon.py` | 21 | `D:\LAAP` | _laap_root 默认值 | `get_laap_root()` |
| `laap/agent/laap_bridge.py` | 118 | `D:\hermes-agent-LAAP数字生命版\hermes-agent-LAAP` | Hermes 根目录 | `get_hermes_root()` |
| `laap/agent/laap_bridge.py` | 120 | `D:\LAAP` | LAAP 根目录 | `get_laap_root()` |
| `laap/agent/laap_bridge.py` | 129, 131, 133 | `D:\\LAAP` | 注释/文档中的示例路径 | 删除或改为相对说明 |
| `laap/bci/safety.py` | 29 | `D:\LAAP\.laap\bci_audit.log` | BCI 审计日志默认路径 | `get_logs_dir() / "bci_audit.log"` |
| `laap/bci/calibration.py` | 23 | `D:\LAAP\.laap\bci_calibration` | BCI 校准输出目录 | `get_state_dir() / "bci_calibration"` |
| `laap/bridge/avatar_ws_server.py` | 26 | 注释 `D:\LAAP` | 根目录推导注释 | 无需替换，仅说明 |
| `laap/cli/laap_main.py` | 6 | 注释 `D:\LAAP` | 根目录推导注释 | 无需替换 |
| `laap/cli/logo_art.py` | 5 | `D:\\LAAP\\龙logo.jpg` | 文档字符串默认路径 | 配置项 / `get_laap_root()` |
| `laap/cli/subcommands/reach_cmd.py` | 33 | `D:\\LAAP\\Agent-Reach` | 安装提示中的路径 | 使用 `get_laap_root() / "Agent-Reach"` |
| `laap/integrations/agent_reach/adapter.py` | 48, 260 | `D:\\LAAP\\Agent-Reach` | Agent-Reach 安装提示 | `get_laap_root() / "Agent-Reach"` |
| `laap/integrations/claw_in_chrome/adapter.py` | 30 | `D:\claw-in-chrome-main\claw-in-chrome-main` | Chrome 扩展目录 | 配置项 / `CLAW_IN_CHROME_ROOT` |
| `laap/integrations/claw_in_chrome/verify.py` | 16, 229 | `D:\claw-in-chrome-main\claw-in-chrome-main` | 扩展目录与提示 | 配置项 |
| `laap/integrations/claw_in_chrome/troubleshoot.py` | 174, 332 | `D:\claw-in-chrome-main\claw-in-chrome-main` | 扩展目录与提示 | 配置项 |
| `laap/integrations/claw_in_chrome/test_real_chrome.py` | 86 | `D:\claw-in-chrome-main\claw-in-chrome-main` | 测试扩展目录 | 配置项 |
| `laap/ui/templates/index.html` | 228 | `D:\LAAP` | 表单默认值 | 占位符或动态填充 |
| `laap/voicetools/lafei_voice.py` | 51, 68 | `C:/Users/user/AppData/Local/hermes/audio_cache/...` | 语音缓存临时文件 | `get_cache_dir() / "audio_cache"` |
| `laap/voicetools/aris_listener_v2.py` | 55, 74 | `C:/Users/user/AppData/Local/hermes/audio_cache/...` | 语音缓存临时文件 | `get_cache_dir() / "audio_cache"` |
| `laap/voicetools/aris_listener.py` | 50 | `C:/Users/user/AppData/Local/hermes/audio_cache/...` | 语音缓存临时文件 | `get_cache_dir() / "audio_cache"` |
| `laap/voicetools/aris_voice_daemon.bat` | 3-16 | `D:\LAAP\laap\voicetools`、`D:\hermes-agent-LAAP数字生命版\...` | 语音守护进程启动脚本 | 环境变量 / 路径模块 |
| `laap/voicetools/aris_voice.bat` | 10-16 | 同上 | 语音批处理脚本 | 环境变量 / 路径模块 |
| `laap/voicetools/aris_listener.bat` | 3-9 | 同上 | 语音批处理脚本 | 环境变量 / 路径模块 |
| `laap/voicetools/aris_daemon.bat` | 3-4 | 同上 | 语音批处理脚本 | 环境变量 / 路径模块 |
| `laap/voicetools/aris_autostart.vbs` | 1 | `D:\LAAP\laap\voicetools\aris_voice_daemon.bat` | 开机启动脚本 | 环境变量 / 路径模块 |

### 2. 根目录关键脚本

| 文件路径 | 行号 | 当前硬编码值 | 用途说明 | 建议替换方式 |
|----------|------|--------------|----------|--------------|
| `kernel_patch.py` | 21 | `D:\hermes-agent-LAAP数字生命版\hermes-agent-LAAP` | HERMES_ROOT 常量 | `get_hermes_root()` |
| `kernel_patch.py` | 31 | `D:\\LAAP` | LAAP_ROOT 默认 fallback | `get_laap_root()` |
| `launch_ao.py` | 8, 11 | `D:\LAAP` | 设置/定义 LAAP_ROOT | `get_laap_root()` |
| `launch_ao.py` | 12 | `D:\hermes-agent-main (1)\hermes-agent-main` | 定义 HERMES_ROOT | `get_hermes_root()` |
| `verify_integration.py` | 5 | `D:\hermes-agent-main (1)\hermes-agent-main` | HERMES 常量 | `get_hermes_root()` |
| `verify_integration.py` | 6 | `D:\LAAP` | LAAP 常量 | `get_laap_root()` |
| `debug_api.py` 等 `debug_*.py` | 6 | `D:\LAAP` | `sys.path.insert` 便于本地调试 | 使用路径推导或相对导入 |
| `brotherhood_connect.py` | 7, 70, 89 | `D:\LAAP\brotherhood\` 等 | 共享状态与用户提示 | `get_laap_root() / "brotherhood"` |
| `moss_realtime_server.py` | 8 | `C:/Users/user/AppData/Roaming/Python/Python313/site-packages` | 强制插入 site-packages | 使用虚拟环境 / PYTHONPATH |
| `moss_realtime_server.py` | 21, 23, 81 | `E:\models\...` | TTS 模型与参考音频路径 | `LAAP_MODELS_DIR` / 配置 |
| `test_moss_tts.py` | 14, 16, 77 | `E:\models\...` | 测试模型/音频路径 | `LAAP_MODELS_DIR` / 配置 |
| `test_moss_stream.py` | 14, 17, 71, 101 | `E:\models\...` | 测试模型/音频路径 | `LAAP_MODELS_DIR` / 配置 |
| `test_z_image.py` | 3, 13 | `C:/Users/.../site-packages`、`E:\models\...` | 测试环境与模型路径 | 配置 / 环境变量 |
| `clean_cache.py` | 2 | `C:/Users/user/.cache/huggingface/...` | 清理 HuggingFace 缓存 | `get_cache_dir()` / `HF_HOME` |
| `_setup_integration.py` | 4, 27, 42, 45, 48, 51 | `C:\Users\user\AppData\...`、`D:\LAAP` 等 | 安装启动项与脚本 | 路径模块 + 配置 |
| `_cleanup_aris.py` | 51 | `C:\Users\user\AppData\Local` | LOCALAPPDATA 回退 | `Path.home() / "AppData/Local"` |

### 3. `tests/` 测试代码

| 文件路径 | 行号 | 当前硬编码值 | 用途说明 | 建议替换方式 |
|----------|------|--------------|----------|--------------|
| `tests/fixtures.py` | 3 | `D:\LAAP` | `sys.path.insert` | 相对导入 / 路径推导 |
| `tests/test_agent.py` | 3 | `D:\LAAP` | `sys.path.insert` | 相对导入 / 路径推导 |
| `tests/test_codex.py` | 5 | `D:\LAAP` | `sys.path.insert` | 相对导入 / 路径推导 |
| `tests/test_llm_provider.py` | 3 | `D:\LAAP` | `sys.path.insert` | 相对导入 / 路径推导 |
| `tests/test_lifelike.py` | 3 | `D:\LAAP` | `sys.path.insert` | 相对导入 / 路径推导 |
| `tests/test_stream_handler.py` | 3 | `D:\LAAP` | `sys.path.insert` | 相对导入 / 路径推导 |
| `tests/test_stability.py` | 7 | `D:\LAAP` | `sys.path.insert` | 相对导入 / 路径推导 |
| `tests/test_session_persistence.py` | 3 | `D:\LAAP` | `sys.path.insert` | 相对导入 / 路径推导 |
| `tests/unit/test_agent_actor.py` | 9 | `D:\LAAP` | `sys.path.insert` | 相对导入 / 路径推导 |
| `tests/test_production.py` | 137-138 | `C:\Users\Public\...`、`D:\test\...` | 路径安全测试数据 | 保持为测试 fixture 即可 |
| `tests/test_production.py` | 228, 234 | `D:\LAAP` | 测试运行目录 | `get_laap_root()` / 参数化 |
| `tests/workspace/test_perception_git.py` | 多处 | `d:\\LAAP` | 在真实仓库上测试 | 参数化 / `get_laap_root()` |
| `tests/workspace/test_perception_files.py` | 241, 248, 254 | `d:\\LAAP` | 在真实仓库上测试 | 参数化 / `get_laap_root()` |
| `tests/workspace/test_perception_deps.py` | 多处 | `d:\\LAAP` | 在真实仓库上测试 | 参数化 / `get_laap_root()` |
| `tests/integration/test_workspace_e2e.py` | 23, 80, 119 | `d:\\LAAP` | E2E 测试根路径 | 参数化 / `get_laap_root()` |
| `tests/test_debug_loop.py` | 21, 28 | `D:\LAAP\loop_debug.txt` 等 | 调试日志输出路径 | 临时目录 / `get_logs_dir()` |
| `tests/test_core_deprecation.py` | 9 | `D:\LAAP` | `sys.path.insert` | 相对导入 |
| `laap/agi/test_memory_system.py` | 7 | `D:\LAAP` | `sys.path.insert` | 相对导入 |
| `laap/agi/test_unified_memory.py` | 7 | `D:\LAAP` | `sys.path.insert` | 相对导入 |

### 4. `aris_brain/` 关键路径（旧 Aris 模块）

| 文件路径 | 行号 | 当前硬编码值 | 用途说明 | 建议替换方式 |
|----------|------|--------------|----------|--------------|
| `aris_brain/ao_hal.py` | 57 | `C:\Users\Unknown` | USERPROFILE 回退 | `Path.home()` |
| `aris_brain/ao_hal.py` | 83 | `/Users/Unknown` | HOME 回退 | `Path.home()` |
| `aris_brain/aris_copilot_bridge_v8.py` | 50 | `C:\Users\user\Desktop\Windows-Copilot-API-master` | Copilot API 工作目录 | 配置项 |
| `aris_brain/arisocr.py` | 17 | `D:\LAAP\aris_brain\vision_microservice.py` | 微服务脚本路径 | `get_laap_root() / "aris_brain/vision_microservice.py"` |
| `aris_brain/arisocr.py` | 18 | `C:\Python313\python.exe` | Python 解释器路径 | `sys.executable` / 配置 |
| `aris_brain/aris_image_ocr.py` | 112-116 | `C:\Users\user\AppData\Local\hermes\profiles\aris\image_cache\...` | 测试图片路径 | 配置 / 临时 fixture |
| `aris_brain/aris_image_ocr.py` | 9 | `C:\Program Files\Tesseract-OCR\tesseract.exe` | Tesseract 可执行文件 | `PATH` / `TESSERACT_CMD` |
| `aris_brain/local_llm.py` | 38 | `C:/Users/user/.docker/bin/inference/llama-server.exe` | llama-server 路径 | `PATH` / 配置 |
| `aris_brain/cli_integration.py` | 33 | `D:\hermes-agent-main (1)\hermes-agent-main` | Hermes 根目录 | `get_hermes_root()` |
| `aris_brain/cli_integration.py` | 34 | `D:\LAAP` | LAAP 根目录 | `get_laap_root()` |
| `aris_brain/ao_quantum_db.py` | 146 | `D:\LAAP` | 语义记忆示例 | 配置 / 删除 |
| `aris_brain/consciousness_cron_sync.py` | 30 | `C:/Users/user/AppData/Local/hermes/profiles/aris/consciousness.json` | 意识同步配置文件 | 配置 / `get_state_dir()` |
| `aris_brain/ollama_vision.py` | 13 | `C:/Users/user/AppData/Local/hermes/profiles/laap-avatar-v4/image_cache` | 图片缓存目录 | `get_cache_dir() / "image_cache"` |
| `aris_brain/_token_analysis.py` | 8, 50 | `C:/Users/user/AppData/Local/hermes/profiles/aris/...` | 会话/数据库路径 | `get_state_dir()` |
| `aris_brain/_db_analyze*.py` | 8 | 同上 | 状态数据库路径 | `get_state_dir()` |
| `aris_brain/aris_orchestration_bridge.py` | 1298-1300 | `C:\Program Files\Godot\...`、`D:\godot\...`、`E:\迅雷下载\...` | Godot 可执行文件候选 | `PATH` / `GODOT_EXECUTABLE` |
| `aris_brain/aris_xiaozhi_mqtt_bridge.py` | 251, 265 | `C:\Windows\System32\drivers\etc\hosts` | hosts 文件路径 | 平台约定 / `Path("/etc/hosts")` |

### 5. 启动脚本 / 批处理（部分示例）

| 文件路径 | 行号 | 当前硬编码值 | 用途说明 | 建议替换方式 |
|----------|------|--------------|----------|--------------|
| `laap.bat` | 3 | `D:\LAAP\laap\cli\main.py` | LAAP CLI 入口 | `LAAP_ROOT` 环境变量 |
| `start.bat` | 12 | `C:\Python313\python.exe` | Python 解释器 | `py` / 环境变量 |
| `start.bat` | 21 | `D:\LAAP\laap_web.py` | Web 入口 | `LAAP_ROOT` |
| `start-web-full.bat` | 13 | `D:\hermes-agent-main (1)\hermes-agent-main\.venv\Scripts\python.exe` | Hermes venv Python | `HERMES_ROOT` |
| `LAAP_Launcher.bat` | 4, 24, 33, 47 | `D:\LAAP` / `D:\LAAP\laap_web.py` | 启动器 | `LAAP_ROOT` |
| `laap_startup.bat` | 19, 30, 41 | `C:\Python313\pythonw.exe`、`D:\hermes-agent-main (1)\...` 等 | 开机启动服务 | 环境变量 |
| `aris_brain/aris_boot.bat` | 10, 21-22, 34 | `C:\Python313\python.exe`、`D:\models\...`、`D:\LAAP\...` | Aris 启动 | 配置 / 环境变量 |
| `aris_brain/start_daemon.bat` | 2 | `C:\Users\user\AppData\Local\hermes\...\python.exe` | 守护进程 Python | `HERMES_ROOT` |
| `setup_autostart.bat` | 3 | `D:\LAAP\aris_tray.pyw` | 计划任务目标 | `LAAP_ROOT` |
| `install.bat` | 17-22 | `C:\Python313\python.exe` 等 | Python 候选路径 | `PATH` / `py` |

### 6. `external/` / `_archive/` 说明

这两个目录包含大量第三方依赖、历史实验代码、 Godot 源码、HarnessX 等。它们的硬编码路径属于外部项目或已废弃代码，**不建议在本次基础设施统一化中修改**。后续可通过 `.gitignore` 或 `external/` 子模块管理，避免扫描工具再次报告。

## 统一替换建议

1. **LAAP 根目录**：所有 `D:\LAAP` / `r"D:\LAAP"` / `"d:\\LAAP"` 替换为 `get_laap_root()`（环境变量 `LAAP_ROOT`）。
2. **Hermes 根目录**：所有 Hermes 候选路径替换为 `get_hermes_root()`（环境变量 `HERMES_ROOT`）。
3. **状态/缓存/日志/模型目录**：分别使用 `get_state_dir()`、`get_cache_dir()`、`get_logs_dir()`、`get_models_dir()`。
4. **TUI 视频目录**：使用 `get_video_dir()`，并通过 `LAAP_VIDEO_DIR` 支持覆盖。
5. **用户目录/平台约定**：`C:\Users\user\...` 类路径统一使用 `pathlib.Path.home()` 或 XDG/平台约定（`%LOCALAPPDATA%`、`~/Library/Application Support`、`.local/state` 等）。
6. **测试代码**：将 `sys.path.insert(0, r"D:\LAAP")` 改为相对导入或 fixture 注入；将真实仓库路径参数化。
7. **批处理/脚本**：优先使用 `LAAP_ROOT`、`HERMES_ROOT` 环境变量，减少对 `D:\LAAP` 的硬编码。

## 备注

- 本次审计未修改任何业务代码，仅作为 Phase 3 前期输入。
- 下一批次（Task 9+）将依据本报告逐步替换上述路径为 `laap.config.paths` 提供的统一接口。
