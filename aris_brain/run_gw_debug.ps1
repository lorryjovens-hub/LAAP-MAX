cd D:\LAAP\aris_brain
$logFile = "D:\LAAP\aris_brain\logs\gw_debug.log"
"=== Starting gateway at $(Get-Date -Format 'HH:mm:ss') ===" | Out-File $logFile -Encoding UTF8
hermes gateway run --replace 2>&1 | Add-Content $logFile -Encoding UTF8
"=== Gateway exited at $(Get-Date -Format 'HH:mm:ss') ===" | Add-Content $logFile -Encoding UTF8
pause
