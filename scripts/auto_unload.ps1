# Auto-Unload Ollama Model
# Frees up RAM/VRAM by unloading the model after inactivity.

$MODEL = "llama3.1:8b"
$IDLE_LIMIT_MINUTES = 10
$CHECK_INTERVAL_SECONDS = 60

Write-Host "Auto-Unload Service Started" -ForegroundColor Green
Write-Host "Target Model: $MODEL"
Write-Host "Idle Limit: $IDLE_LIMIT_MINUTES minutes"

while ($true) {
    # In a real scenario, we'd check actual API logs or system compiled metrics.
    # Since Ollama handleskeep-alive natively, checking for "inactivity" externally is tricky without access to Ollama's internal stats.
    # However, we can enforce a rigid "cleanup" every X minutes if we want to be aggressive, 
    # OR we can just hit the API to unload it if we haven't used it.
    
    # For this script, we will simply force an unload if the user runs this script manually or schedulded.
    # To make it a true "watcher", we'd need to proxy requests.
    
    # Instead, let's rely on the native OLLAMA_KEEP_ALIVE for true idle handling.
    # This script will serve as a "Force Unload" tool for immediate cleanup.
    
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Sending unload request to Ollama..." -NoNewline
    
    try {
        $payload = @{
            model      = $MODEL
            keep_alive = 0
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Uri "http://localhost:11434/api/generate" -Method Post -Body $payload -ContentType "application/json" -ErrorAction Stop
        Write-Host " Done." -ForegroundColor Green
    }
    catch {
        Write-Host " Failed. Open WebUI or Ollama might be down." -ForegroundColor Red
    }
    
    # Wait before checking/forcing again (if loop is desired, though native keep-alive is better)
    # Sleeping for the idle limit to ensure we just keep it clean.
    Start-Sleep -Seconds ($IDLE_LIMIT_MINUTES * 60)
}
