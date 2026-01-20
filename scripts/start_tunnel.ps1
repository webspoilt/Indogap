# IndoGap Cloudflared Tunnel Script for Windows
# This script helps you start a tunnel to your local Ollama instance.

$OLLAMA_PORT = 11434

Write-Host "--- IndoGap Local AI Tunnel Helper ---" -ForegroundColor Cyan

# Check if cloudflared is installed
if (!(Get-Command cloudflared -ErrorAction SilentlyContinue)) {
    Write-Host "[!] cloudflared not found in PATH." -ForegroundColor Yellow
    Write-Host "Please download it from: https://github.com/cloudflare/cloudflared/releases"
    Write-Host "Or install via winget: winget install cloudflare.cloudflared"
    exit
}

Write-Host "[+] Starting tunnel to http://localhost:$OLLAMA_PORT..." -ForegroundColor Green
Write-Host "[i] Copy the URL ending in '.trycloudflare.com' and use it as OLLAMA_BASE_URL in your Render settings." -ForegroundColor Gray
Write-Host "---"

cloudflared tunnel --url http://localhost:$OLLAMA_PORT
