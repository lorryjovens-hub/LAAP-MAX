' Aether Agent Framework — 开机自启 v7
' 架构: Aether Runtime (独立认知引擎) + Rust PSI Core + Hermes (通信壳)
' =====================================

Dim shell
Set shell = CreateObject("WScript.Shell")

' 1. 启动 Rust PSI Core + Aether Runtime
shell.Run "D:\LAAP\aris_brain\ArisAGI_startup.bat", 0, False

' 2. 等待引擎初始化
WScript.Sleep 3000

' 3. 启动 Hermes 飞书网关（仅通信壳）
shell.Run "cmd.exe /c cd /d D:\hermes-agent-main (1)\hermes-agent-main && .venv\Scripts\hermes gateway run --replace --profile aris", 0, False

Set shell = Nothing
