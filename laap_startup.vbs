' LAAP 静默启动器 — 绝对无窗口
Set WshShell = CreateObject("WScript.Shell")

' 1. Aris 飞书网关
WshShell.Run "pythonw ""C:\Users\user\AppData\Local\hermes\start_feishu_gateway.py""", 0, False

' 2. Ao V10 大脑
WshShell.Run "pythonw ""D:\LAAP\aris_brain\pi_psi_server.py"" 11529", 0, False

' 3. Ao 飞书桥接
WshShell.Run "pythonw ""D:\LAAP\aris_brain\ao_v10_feishu_bridge.py""", 0, False
