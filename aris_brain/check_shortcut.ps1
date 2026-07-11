$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut("C:\ProgramData\Microsoft\Windows\Start Menu\Programs\NVIDIA Corporation\NVIDIA App.lnk")
Write-Host "Target: $($shortcut.TargetPath)"
Write-Host "Args: $($shortcut.Arguments)"
Write-Host "WorkingDir: $($shortcut.WorkingDirectory)"
