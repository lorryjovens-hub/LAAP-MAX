' Hermes Feishu Gateway 持久启动器
' 隐藏窗口运行，崩溃自动重启
' 完全独立于 CLI，后台永久运行

Dim WshShell, retryCount, hermesPath
Set WshShell = CreateObject("WScript.Shell")
hermesPath = "D:\hermes-agent-main (1)\hermes-agent-main\.venv\Scripts\hermes"
workDir = "D:\hermes-agent-main (1)\hermes-agent-main"

retryCount = 0

Do While True
    retryCount = retryCount + 1
    WshShell.CurrentDirectory = workDir
    WshShell.Run """" & hermesPath & """ gateway run", 0, True
    
    ' 网关退出（崩溃），等待后重启
    WScript.Sleep 3000
    
    If retryCount >= 10 Then
        WScript.Sleep 30000  ' 连续崩10次，等30秒
        retryCount = 0
    End If
Loop
