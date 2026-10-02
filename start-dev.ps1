#Requires -Version 5.1
# start-dev.ps1 — Lance l'environnement de dev Dexter en un coup (Voie B, natif) :
#   1. PostgreSQL natif (detache) + attente de disponibilite
#   2. Backend uvicorn (port 8000, depuis backend/.venv)
#   3. Frontend Vite (port 4173, via node direct — scripts npm *:node)
#
# Usage : powershell -ExecutionPolicy Bypass -File .\start-dev.ps1
#         ou clic droit > Executer avec PowerShell
# Arret : fermer les deux fenetres ouvertes par le script ; PostgreSQL reste actif
#         (relancer le script plus tard ne redemarre pas ce qui tourne deja : il verifie).

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

$pgBin    = 'C:\Users\Edwin Jamel Kouokam\PostgreSQL\pgsql16\bin'
$pgData   = 'C:\Users\Edwin Jamel Kouokam\PostgreSQL\data'
$pgIsReady = Join-Path $pgBin 'pg_isready.exe'
$pgCtl    = Join-Path $pgBin 'pg_ctl.exe'

$backendDir = Join-Path $root 'backend'
$frontendDir = Join-Path $root 'frontend'
$pythonExe = Join-Path $backendDir '.venv\Scripts\python.exe'
# NB : uvicorn.exe (lanceur du venv) echoue silencieusement dans ce contexte — passer par python -m uvicorn

# --- 1) PostgreSQL : demarre si necessaire, puis attente de disponibilite ---
Write-Host '== [1/3] PostgreSQL ==' -ForegroundColor Cyan
function Test-PgReady {
    # pg_isready retourne 0 quand le serveur accepte les connexions (fiable, independant de la langue)
    & $pgIsReady -h localhost -p 5432 | Out-Null
    return ($LASTEXITCODE -eq 0)
}

if (-not (Test-PgReady)) {
    Write-Host 'PostgreSQL est arrete : demarrage...'
    if (Test-Path (Join-Path $pgData 'postmaster.pid')) {
        # pid residual (arret force anterieur) : PostgreSQL n'est pas en memoire, on peut le retirer
        Remove-Item (Join-Path $pgData 'postmaster.pid') -Force
        Write-Host 'postmaster.pid residuel supprime.'
    }
    $logFile = Join-Path $pgData ("pg_start_" + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.log')
    Start-Process -FilePath $pgCtl -ArgumentList @(
        '-D', ('"' + $pgData + '"'),
        '-l', ('"' + $logFile + '"'),
        'start'
    ) -WindowStyle Hidden
} else {
    Write-Host 'PostgreSQL tourne deja.'
}

# Attente de disponibilite (90 s max : la recuperation WAL peut etre longue au 1er demarrage)
$timeoutSec = 90
$elapsed = 0
while ($elapsed -lt $timeoutSec -and -not (Test-PgReady)) {
    Start-Sleep -Seconds 2
    $elapsed += 2
}
if (-not (Test-PgReady)) {
    throw "PostgreSQL n'est pas devenu disponible en $timeoutSec s. Voir le dernier log pg_start_*.log dans $pgData"
}
Write-Host 'PostgreSQL pret (localhost:5432).' -ForegroundColor Green

# --- 2) Backend uvicorn : port 8000, fenetre dediee ---
Write-Host '== [2/3] Backend uvicorn (port 8000) ==' -ForegroundColor Cyan
$backendUp = $false
try {
    $resp = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/health' -UseBasicParsing -TimeoutSec 2
    $backendUp = ($resp.StatusCode -eq 200)
} catch { $backendUp = $false }

if ($backendUp) {
    Write-Host 'Backend deja actif sur :8000.'
} else {
    if (-not (Test-Path $pythonExe)) {
        throw "python introuvable : $pythonExe (venv backend incomplet ?)"
    }
    Start-Process -FilePath 'powershell.exe' -ArgumentList @(
        '-NoExit', '-Command',
        "Set-Location -LiteralPath '$backendDir'; " +
        "Write-Host '--- Backend Dexter (Ctrl+C pour arreter) ---' -ForegroundColor Cyan; " +
        "& '.venv\Scripts\python.exe' -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
    ) -WindowStyle Normal
    Write-Host 'Backend lance dans une nouvelle fenetre (http://127.0.0.1:8000 — /docs pour Swagger).'
}

# --- 3) Frontend Vite : port 4173, fenetre dediee ---
Write-Host '== [3/3] Frontend Vite (port 4173) ==' -ForegroundColor Cyan
$frontendUp = $false
try {
    $resp = Invoke-WebRequest -Uri 'http://localhost:4173/' -UseBasicParsing -TimeoutSec 2
    $frontendUp = ($resp.StatusCode -eq 200)
    Write-Host 'Frontend deja actif sur :4173.'
} catch { $frontendUp = $false }

if (-not $frontendUp) {
    if (-not (Test-Path (Join-Path $frontendDir 'node_modules\vite\bin\vite.js'))) {
        throw "vite introuvable : lancer 'npm install' dans frontend/ d'abord."
    }
    Start-Process -FilePath 'powershell.exe' -ArgumentList @(
        '-NoExit', '-Command',
        "Set-Location -LiteralPath '$frontendDir'; " +
        "Write-Host '--- Frontend Dexter (Ctrl+C pour arreter) ---' -ForegroundColor Cyan; " +
        "node node_modules/vite/bin/vite.js"
    ) -WindowStyle Normal
    Write-Host 'Frontend lance dans une nouvelle fenetre (http://localhost:4173/).'
}

Write-Host ''
Write-Host 'Environnement pret :' -ForegroundColor Green
Write-Host '  - Application : http://localhost:4173/  (connexion : etudiant.test@dexter.dev / Etudiant2026! ou professeur.test@dexter.dev / Professeur2026!)'
Write-Host '  - API : http://127.0.0.1:8000  (Swagger : /docs)'
Write-Host 'Arret : fermer les fenetres backend/frontend ; PostgreSQL continue de tourner.'