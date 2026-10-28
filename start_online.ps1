# BTP Tender Analyzer - Public Online Launch Script (Cloudflare Tunnel)
$ErrorActionPreference = "Continue"

$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $rootDir

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " 🏗️  LANCEMENT EN LIGNE - BTP PUBLIC TENDER ANALYZER" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Start FastAPI server if not running
$serverRunning = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if (-not $serverRunning) {
    Write-Host "[1/3] Démarrage du serveur FastAPI local..." -ForegroundColor Yellow
    $serverProcess = Start-Process python -ArgumentList "run.py" -WorkingDirectory $rootDir -PassThru
    Start-Sleep -Seconds 3
} else {
    Write-Host "[1/3] Le serveur FastAPI tourne déjà sur le port 8000." -ForegroundColor Green
}

# 2. Start Cloudflare Tunnel
$cloudflaredPath = Join-Path $rootDir "cloudflared.exe"
$tunnelLog = Join-Path $rootDir "tunnel.log"

if (Test-Path $tunnelLog) {
    Remove-Item $tunnelLog -Force -ErrorAction SilentlyContinue
}

Write-Host "[2/3] Création du tunnel sécurisé Cloudflare..." -ForegroundColor Yellow
$tunnelProcess = Start-Process $cloudflaredPath -ArgumentList "tunnel --url http://127.0.0.1:8000 --logfile `"$tunnelLog`"" -PassThru

# 3. Extract public URL from log
Write-Host "[3/3] Recherche de l'URL publique mondiale..." -ForegroundColor Yellow
$publicUrl = $null
$timeoutSeconds = 25
$start = Get-Date

while ((Get-Date) - $start -lt [TimeSpan]::FromSeconds($timeoutSeconds)) {
    Start-Sleep -Seconds 1
    if (Test-Path $tunnelLog) {
        $content = Get-Content $tunnelLog -Raw -ErrorAction SilentlyContinue
        if ($content -match "https://[a-zA-Z0-9-]+\.trycloudflare\.com") {
            $publicUrl = $matches[0]
            break
        }
    }
}

if ($publicUrl) {
    Write-Host ""
    Write-Host "==========================================================" -ForegroundColor Green
    Write-Host " 🌍 SITE EN LIGNE ACCESSIBLE PARTOUT DANS LE MONDE !" -ForegroundColor Green
    Write-Host " 🔗 URL PUBLIQUE : $publicUrl" -ForegroundColor Cyan
    Write-Host "==========================================================" -ForegroundColor Green
    Write-Host "Vous pouvez ouvrir cette URL depuis votre téléphone, tablette"
    Write-Host "ou la partager avec des artisans et collègues partout dans le monde."
    Write-Host ""
} else {
    Write-Host "[!] Impossible de récupérer l'URL du tunnel. Consultez $tunnelLog" -ForegroundColor Red
}
