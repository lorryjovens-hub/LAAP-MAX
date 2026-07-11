[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls13
$wc = New-Object System.Net.WebClient
$wc.Proxy = $null
$wc.Headers.Add('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
$wc.Headers.Add('Referer', 'https://www.nvidia.cn/')
try {
    $page = $wc.DownloadString('https://www.nvidia.cn/Download/driverResults.aspx/228901/cn')
    # Find download links
    $pattern = '(?i)(https?://[^""'']+\.exe[^""'']*)'
    $matches = [regex]::Matches($page, $pattern)
    $matches | ForEach-Object { 
        $url = $_.Groups[1].Value
        if ($url -match 'nvidia') {
            Write-Host "URL:$url"
        }
    }
    # Also just check if the page has any exe reference
    if ($page -match 'driverVersion["\s:=]+["'']?([^"''<>\s]+)') {
        Write-Host "VER:$($matches[1])"
    }
    if ($page -match '(\d+\.\d+)-desktop') {
        Write-Host "DVR:$($matches[1])"
    }
} catch {
    Write-Host "ERROR:$($_.Exception.Message)"
}
