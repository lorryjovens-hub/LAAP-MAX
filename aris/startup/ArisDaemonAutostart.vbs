' Aris 感官系统开机自启脚本
' 位置: %APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\ArisDaemon.vbs
' 或手动运行

Set WshShell = CreateObject("WScript.Shell")

' 启动 Ollama 服务（如果没在运行）
WshShell.Run "cmd /c start /B C:\Users\user\AppData\Local\Programs\Ollama\ollama.exe serve", 0, False

' 等待 Ollama 就绪
WScript.Sleep 5000

' 启动 Aris 感官守护进程
WshShell.CurrentDirectory = "D:\LAAP\aris"
WshShell.Run "cmd /c python aris_daemon.py --daemon", 1, False

' 启动视觉模型服务器（后台常驻）
' 取消注释以下行可启动本地大模型视觉服务器（需 15GB+ 内存）
' WshShell.CurrentDirectory = "D:\user\Documents\llama\models"
' WshShell.Run "cmd /c start /B /MIN D:\user\Documents\llama\llama-server.exe -m Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ3_M.gguf --mmproj mmproj-Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-f16.gguf --host 127.0.0.1 --port 8088 -c 8192 -ngl 12", 0, False
