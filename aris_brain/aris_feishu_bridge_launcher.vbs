' Aris Feishu Bridge 持久启动器
' 隐藏窗口运行，崩溃自动重启
' 完全独立于 Hermes，可在后台永久运行

Dim WshShell, retryCount
Set WshShell = CreateObject("WScript.Shell")

retryCount = 0

Do While True
    ' 静默启动飞书桥（隐藏窗口）
    retryCount = retryCount + 1
    WshShell.Run "cmd /c cd /d D:\LAAP\aris_brain && set ARIS_MODE=llm && python aris_feishu_bridge.py", 0, True
    
    ' Python 进程退出了（不管是因为崩溃还是正常退出）
    ' 等待 3 秒后自动重启
    WScript.Sleep 3000
    
    ' 如果连续重启超过 10 次，等久一点（可能是持续性错误）
    If retryCount >= 10 Then
        WScript.Sleep 30000  ' 等 30 秒
        retryCount = 0
    End If
Loop
