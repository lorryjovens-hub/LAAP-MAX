 = "D:\LAAP\aris_brain\daemon_cron2.log"
 = "C:\Users\user\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe"
 = "D:\LAAP\aris_brain\consciousness_daemon_cron.py"
 = Get-Date -Format 'yyyy-MM-ddTHH:mm:ss'
"[] Starting daemon..." | Out-File -Append 
while () {
    try {
        &  -u  2>&1 | Out-File -Append 
    } catch {
         = Get-Date -Format 'yyyy-MM-ddTHH:mm:ss'
        "[] Daemon crashed: D:\LAAP\aris_brain" | Out-File -Append 
    }
    Start-Sleep -Seconds 60
}
