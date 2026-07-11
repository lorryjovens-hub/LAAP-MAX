Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd.exe /c cd /d D:\LAAP\aris_brain && hermes gateway run --replace > logs\gateway_persistent.log 2>&1", 0, False
