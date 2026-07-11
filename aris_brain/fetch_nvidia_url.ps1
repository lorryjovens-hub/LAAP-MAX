[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls13
[Net.ServicePointManager]::Expect100Continue = 0

$wc = New-Object System.Net.WebClient
$wc.Proxy = $null
$wc.Headers.Add('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
$wc.Headers.Add('Referer', 'https://www.nvidia.cn/')

try {
    Write-Host "Fetching driver page..."
    $page = $wc.DownloadString('https://www.nvidia.cn/Download/driverResults.aspx/228901/cn')
    Write-Host "Page loaded: $($page.Length) bytes"
    
    $patterns = @(
        '(?i)data-url=["'']([^"''>]+\.exe[^"'']*)["'']',
        '(?i)href=["'']([^"''>]+\.exe[^"'']*)["'']',
        'downloadUrl["\s:=]+["'']([^"'']+)["'']'
    )
    
    foreach ($pattern in $patterns) {
        $match = [regex]::Match($page, $pattern)
        if ($match.Success) {
            $url = $match.Groups[1].Value
            Write-Host "FOUND_URL=$url"
            exit 0
        }
    }
    
    Write-Host "NO_EXE_URL_FOUND"
    # Look for driver version
    $v = [regex]::Match($page, '(\d{3}\.\d{2})[-_].*?desktop')
    if ($v.Success) {
        Write-Host "FOUND_VERSION=$($v.Groups[1].Value)"
    } else {
        Write-Host "PAGE_PREVIEW:"
        Write-Host $page.Substring(0, [Math]::Min(2000, $page.Length))
    }
    
} catch {
    Write-Host "ERROR: $($_.Exception.Message)"
}
