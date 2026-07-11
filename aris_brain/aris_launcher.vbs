' Aris AGI v6 — 开机自启（静默）
' 启动独立认知运行时 + Hermes 通信壳

Dim shell
Set shell = CreateObject("WScript.Shell")

' 启动 aris_runtime (独立认知引擎) + PSI Core
shell.Run "D:\LAAP\aris_brain\ArisAGI_startup.bat", 0, False

' 等待引擎启动
WScript.Sleep 2000

' 启动 Hermes 飞书网关 (通信壳)
shell.Run "cmd.exe /c cd /d D:\hermes-agent-main (1)\hermes-agent-main && .venv\Scripts\hermes gateway run --replace --profile aris", 0, False

Set shell = Nothing
