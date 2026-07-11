' 静默启动飞书网关 — 绝对无窗口
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "pythonw C:\Users\user\AppData\Local\hermes\start_feishu_gateway.py", 0, False
