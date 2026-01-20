# System Resource Monitor
# Displays real-time GPU, RAM, and CPU usage.

while ($true) {
    Clear-Host
    Write-Host "=== System Monitoring ===" -ForegroundColor Cyan
    Write-Host "Press Ctrl+C to stop"
    Write-Host ""

    # GPU Status (Nvidia)
    if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
        Write-Host "--- GPU Status ---" -ForegroundColor Yellow
        nvidia-smi --query-gpu=temp.gpu, utilization.gpu, memory.used, memory.total --format=csv
    }
    else {
        Write-Host "--- GPU Status ---" -ForegroundColor Yellow
        Write-Host "NVIDIA-SMI not found. Skipping GPU stats."
    }

    Write-Host ""
    Write-Host "--- RAM Status ---" -ForegroundColor Yellow
    $osInfo = Get-CimInstance -ClassName Win32_OperatingSystem
    $totalRam = [math]::Round($osInfo.TotalVisibleMemorySize / 1MB, 2)
    $freeRam = [math]::Round($osInfo.FreePhysicalMemory / 1MB, 2)
    $usedRam = [math]::Round($totalRam - $freeRam, 2)
    Write-Host "Total: $totalRam GB"
    Write-Host "Used:  $usedRam GB"
    Write-Host "Free:  $freeRam GB"

    Write-Host ""
    Write-Host "--- CPU Status ---" -ForegroundColor Yellow
    $cpu = Get-Counter '\Processor(_Total)\% Processor Time' -ErrorAction SilentlyContinue
    if ($cpu) {
        $load = [math]::Round($cpu.CounterSamples.CookedValue, 1)
        Write-Host "CPU Load: $load %"
    }
    else {
        Write-Host "Calculating CPU load..."
    }

    Start-Sleep -Seconds 5
}
