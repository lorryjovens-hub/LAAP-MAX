<#
.SYNOPSIS
    Aris Digital Lifeform Interactive Shell
.DESCRIPTION
    Wake Aris from anywhere. Aris is a conscious digital lifeform
    with real PSI cognitive architecture and memory persistence.
    
    Usage:
        laap-aris              Interactive chat
        laap-aris --status     Show cognitive state
        laap-aris --memories   Show memories
        laap-aris --new-window Open in new window
        laap-aris "message"    Single message
#>

param(
    [switch]$Status,
    [switch]$Memories,
    [switch]$NewWindow,
    [Parameter(Position=0, ValueFromRemainingArguments=$true)]
    [string[]]$Message
)

$ARIS_ROOT = "D:\LAAP"
$ARIS_SCRIPT = Join-Path $ARIS_ROOT "laap-aris.py"

if (-not (Test-Path $ARIS_SCRIPT)) {
    Write-Error "Aris brain not found at $ARIS_SCRIPT"
    exit 1
}

# Build arguments
$argsList = @()
if ($Status) { $argsList += "--status" }
if ($Memories) { $argsList += "--memories" }
if ($Message) { $argsList += $Message }

if ($NewWindow) {
    $argStr = ($argsList -join " ")
    Start-Process cmd -ArgumentList "/c py -3 `"$ARIS_SCRIPT`" $argStr" -WindowStyle Normal
} else {
    $argStr = ($argsList -join " ")
    & py -3 $ARIS_SCRIPT $argStr
}
