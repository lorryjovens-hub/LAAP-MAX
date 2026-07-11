try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $wc = New-Object System.Net.WebClient
    $wc.Proxy = $null
    $wc.Headers.Add('User-Agent', 'Mozilla/5.0')
    $wc.Headers.Add('Referer', 'https://www.nvidia.cn/')
    
    Write-Host "START"
    $page = $wc.DownloadString('https://www.nvidia.cn/Download/driverResults.aspx/228901/cn')
    Write-Host ("PAGE_SIZE:" + $page.Length)
    
    # Search for downloadable driver
    if ($page -match 'href=["'']([^"'']+nvidia[^"'']+\.exe[^"'']*)["'']') {
        Write-Host ("DL1:" + $matches[1])
    }
    if ($page -match 'driverVersion["\s:=>]+["'']?([^"''<>&]+)') {
        Write-Host ("VER:" + $matches[1])
    }
    
    # Check for any exe references
    $count = 0
    $exeRefs = [regex]::Matches($page, '["'']([^"'']+\.exe[^"'']*)["'']')
    foreach ($r in $exeRefs) {
        Write-Host ("EXE:" + $r.Groups[1].Value)
        $count++
        if ($count -gt 3) { break }
    }
    
} catch {
    Write-Host ("ERR:" + $_.Exception.Message)
}
Write-Host "END"
