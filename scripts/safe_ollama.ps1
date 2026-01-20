# Safe Ollama Runner
# Runs Ollama with resource limits and monitors GPU temperature.

$MAX_TEMP = 85
$MODEL = "llama3.1:8b"

# Set Resource Limits via Environment Variables
$env:OLLAMA_NUM_PARALLEL = 1
$env:OLLAMA_KEEP_ALIVE = "300s"

Write-Host "Starting Safe Ollama Runner..." -ForegroundColor Green
Write-Host "Limits Set: Parallel=1, KeepAlive=300s" -ForegroundColor Gray
Write-Host "Max Temp Limit: $MAX_TEMP C" -ForegroundColor Gray

# Start Ollama in the background (if not already running)
if (!(Get-Process ollama -ErrorAction SilentlyContinue)) {
    Write-Host "Starting Ollama service..."
    Start-Process "ollama" -ArgumentList "serve" -NoNewWindow
    Start-Sleep -Seconds 5
}

# Monitoring Loop
while ($true) {
    if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
        # Get GPU Temperature
        $gpuInfo = nvidia-smi --query-gpu=temperature.gpu --format=csv, noheader, nounits
        $temp = [int]$gpuInfo

        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] GPU Temp: $temp C" -ForegroundColor Gray

        if ($temp -gt $MAX_TEMP) {
            Write-Host "⚠️ CRITICAL: GPU too hot ($temp C)!" -ForegroundColor Red
            Write-Host "Stopping Ollama to protect hardware..." -ForegroundColor Red
            
            # Stop Ollama Process
            Stop-Process -Name "ollama" -Force -ErrorAction SilentlyContinue
            Stop-Process -Name "ollama app" -Force -ErrorAction SilentlyContinue
            
            Write-Host "Ollama stopped. Cooldown initiated."
            exit 1
        }
    }
    else {
        Write-Host "NVIDIA-SMI not found. Cannot monitor GPU temp." -ForegroundColor Yellow
    }

    Start-Sleep -Seconds 60
}
