# Script pour pousser automatiquement vers GitHub
param (
    [string]$RepoUrl = "https://github.com/misymmedo5-pixel/btp-tender-analyzer.git",
    [string]$Token = ""
)

$git = "C:\Users\Admin\.gemini\antigravity\scratch\git-min\cmd\git.exe"
$dir = "C:\Users\Admin\.gemini\antigravity\scratch\btp-tender-analyzer"
Set-Location $dir

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " 🚀 ENVOI VERS GITHUB - BTP PUBLIC TENDER ANALYZER" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

if ($Token) {
    # If personal access token provided
    $authUrl = $RepoUrl.Replace("https://", "https://$Token@")
    & $git remote set-url origin $authUrl
} else {
    & $git remote set-url origin $RepoUrl
}

Write-Host "Publication de la branche main vers $RepoUrl..." -ForegroundColor Yellow
& $git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Dépôt GitHub publié avec succès !" -ForegroundColor Green
    Write-Host "🔗 Lien : $RepoUrl" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "⚠️ Si le dépôt n'existe pas encore sur GitHub :" -ForegroundColor Yellow
    Write-Host "1. Ouvrez https://github.com/new"
    Write-Host "2. Nommez le dépôt : btp-tender-analyzer"
    Write-Host "3. Cliquez sur 'Create repository'"
    Write-Host "4. Relancez ce script : .\push_to_github.ps1"
}
