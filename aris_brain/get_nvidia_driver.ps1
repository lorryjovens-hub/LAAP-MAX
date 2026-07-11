[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$wc = New-Object System.Net.WebClient
$wc.Headers.Add('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
$wc.Headers.Add('Referer', 'https://www.nvidia.cn/')
try {
    $page = $wc.DownloadString('https://www.nvidia.cn/Download/driverResults.aspx/228901/cn')
    Write-Host "Page length: $($page.Length)"
    # Look for download URL pattern
    if ($page -match '"https?://[^"]*\.exe[^"]*"') {
        Write-Host "DOWNLOAD_URL=$($matches[0])"
    } elseif ($page -match 'downloadUrl[=:][^<"]+') {
        Write-Host "DOWNLOAD_URL=$($matches[0])"
    } elseif ($page -match '(https?://[^"\s]+\.exe)') {
        Write-Host "DOWNLOAD_URL=$($matches[1])"
    } else {
        Write-Host "NO_DOWNLOAD_URL_FOUND"
        # Try to find the driver version
        if ($page -match '[0-9]{3}\.[0-9]{2}') {
            Write-Host "VERSIONS_FOUND"
            $versions = [regex]::Matches($page, '[0-9]{3}\.[0-9]{2}')
            $versions | ForEach-Object { Write-Host "VER:$($_.Value)" } | Sort-Object -Unique
        }
    }
} catch {
    Write-Host "ERROR: $($_.Exception.Message)"
}
