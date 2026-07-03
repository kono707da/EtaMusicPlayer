# Kill stale EtaMusic backend processes on port 8000.
# Only kills processes whose command line looks like our uvicorn.
# Returns: 0 if port is free (or was freed), 1 if still occupied by us, 2 if occupied by other.

$ErrorActionPreference = 'SilentlyContinue'
$port = 8000

function Get-PortOwners {
    param([int]$Port)
    $conns = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
    $owners = @()
    foreach ($c in $conns) {
        $pid_ = $c.OwningProcess
        if (-not $pid_) { continue }
        $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$pid_" -ErrorAction SilentlyContinue
        $owners += [PSCustomObject]@{
            Pid       = $pid_
            Name      = $proc.Name
            CmdLine   = $proc.CommandLine
            IsOurs    = ($proc.CommandLine -like '*app.main:app*') -or ($proc.CommandLine -like '*uvicorn*--port 8000*')
        }
    }
    return $owners
}

$owners = Get-PortOwners -Port $port
if (-not $owners -or $owners.Count -eq 0) {
    Write-Output 'FREE'
    exit 0
}

Write-Output "FOUND $(@($owners).Count) process(es) on port ${port}:"
foreach ($o in $owners) {
    $tag = if ($o.IsOurs) { 'OURS' } else { 'OTHER' }
    Write-Output "  [$tag] PID=$($o.Pid) NAME=$($o.Name)"
    Write-Output "        CMD=$($o.CmdLine)"
}

# Kill ours
$killed = 0
foreach ($o in $owners) {
    if ($o.IsOurs) {
        Write-Output "Killing PID=$($o.Pid) ($($o.Name))..."
        # taskkill /F /T kills the process tree (parent + children)
        & taskkill /F /T /PID $o.Pid 2>$null | Out-Null
        Stop-Process -Id $o.Pid -Force -ErrorAction SilentlyContinue
        $killed++
    }
}

if ($killed -gt 0) {
    Write-Output "KILLED $killed of our process(es)."
    # Wait up to 30 seconds for port to be released (TIME_WAIT etc.)
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Milliseconds 1000
        $remaining = Get-PortOwners -Port $port
        $oursRemaining = @($remaining | Where-Object { $_.IsOurs })
        if ($oursRemaining.Count -eq 0) {
            Write-Output "Port $port released after $($i+1)s."
            # Check if any OTHER process is still there
            $otherRemaining = @($remaining | Where-Object { -not $_.IsOurs })
            if ($otherRemaining.Count -gt 0) {
                Write-Output "WARN: port still held by other process(es):"
                foreach ($o in $otherRemaining) {
                    Write-Output "  PID=$($o.Pid) NAME=$($o.Name)"
                }
                Write-Output 'OTHER'
                exit 2
            }
            Write-Output 'FREE'
            exit 0
        }
    }
    Write-Output "ERROR: our process still on port $port after 30s."
    exit 1
} else {
    Write-Output "No our processes to kill. Port held by other program(s)."
    Write-Output 'OTHER'
    exit 2
}
