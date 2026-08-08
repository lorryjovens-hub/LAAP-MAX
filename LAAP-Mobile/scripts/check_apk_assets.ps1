$bt = (Get-ChildItem "$env:LOCALAPPDATA\Android\Sdk\build-tools" | Sort-Object Name -Descending | Select-Object -First 1).Name
$aapt = "$env:LOCALAPPDATA\Android\Sdk\build-tools\$bt\aapt.exe"
$apk = "D:\LAAP\LAAP-Mobile\src\android\app\build\outputs\apk\debug\app-debug.apk"
& $aapt l $apk | Select-String "alpine-minirootfs|proot-aarch64"
