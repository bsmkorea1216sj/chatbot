# ============================================================
# Gemini CLI setup for PTU application auto-fill (autorec)
# This file is pure ASCII on purpose: Korean text in a .ps1 breaks
# on Windows PowerShell 5.1 when the file has no UTF-8 BOM.
# Korean content lives in separate downloaded files.
# Usage:  .\install-gemini.ps1
# ============================================================

$ErrorActionPreference = "Stop"

$WorkDir   = $PSScriptRoot
if (-not $WorkDir) { $WorkDir = (Get-Location).Path }

$Base      = "https://raw.githubusercontent.com/bsmkorea1216sj/chatbot/claude/bsm-chatbot-investment-plan-gs0t6q/automation/autorec/assets"
$TargetUrl = "https://login.ptu.ac.kr/nx/index.html?loginGbn=pfic"
$ChromeProf= "C:\chrome_mcp_profile"

Write-Host ""
Write-Host "Work dir: $WorkDir"
Write-Host ""

# --- 1. Node / Gemini CLI -----------------------------------
Write-Host "[1/5] Checking Node.js and Gemini CLI" -ForegroundColor Cyan
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "  Node.js not found. Install LTS from https://nodejs.org then re-run." -ForegroundColor Red
    exit 1
}
Write-Host ("  node " + (node --version))
if (Get-Command gemini -ErrorAction SilentlyContinue) {
    Write-Host "  gemini CLI already installed."
} else {
    Write-Host "  Installing @google/gemini-cli ..."
    npm install -g @google/gemini-cli
    if ($LASTEXITCODE -ne 0) { Write-Host "  npm install failed." -ForegroundColor Red; exit 1 }
}

# --- 2. Download config files (Korean content stays in files) -
Write-Host "[2/5] Downloading config files" -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path (Join-Path $WorkDir ".gemini") | Out-Null

$files = @(
    @{ Url = "$Base/gemini-settings.json"; Out = ".gemini\settings.json" },
    @{ Url = "$Base/GEMINI.md";            Out = "GEMINI.md" }
)
foreach ($f in $files) {
    $dest = Join-Path $WorkDir $f.Out
    try {
        Invoke-WebRequest -Uri $f.Url -OutFile $dest -UseBasicParsing
        $size = (Get-Item -LiteralPath $dest).Length
        Write-Host ("  OK  " + $f.Out + "  (" + $size + " bytes)")
    } catch {
        Write-Host ("  FAILED  " + $f.Out + " : " + $_.Exception.Message) -ForegroundColor Red
        exit 1
    }
}

# --- 3. Verify the downloaded JSON --------------------------
Write-Host "[3/5] Verifying settings.json" -ForegroundColor Cyan
try {
    $json = Get-Content -LiteralPath (Join-Path $WorkDir ".gemini\settings.json") -Raw -Encoding UTF8 | ConvertFrom-Json
    $names = $json.mcpServers.PSObject.Properties.Name -join ", "
    Write-Host ("  mcpServers: " + $names)
} catch {
    Write-Host "  settings.json is not valid JSON." -ForegroundColor Red; exit 1
}

# --- 4. Debug Chrome on CDP 9222 ----------------------------
Write-Host "[4/5] Checking debug Chrome on port 9222" -ForegroundColor Cyan
$cdpUp = $false
try {
    $r = Invoke-WebRequest -Uri "http://localhost:9222/json/version" -TimeoutSec 3 -UseBasicParsing
    if ($r.StatusCode -eq 200) { $cdpUp = $true }
} catch { $cdpUp = $false }

if ($cdpUp) {
    Write-Host "  Already running. Reusing that window (same one Codex used)." -ForegroundColor Green
} else {
    $chrome = "C:\Program Files\Google\Chrome\Application\chrome.exe"
    if (-not (Test-Path -LiteralPath $chrome)) {
        $chrome = "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    }
    if (Test-Path -LiteralPath $chrome) {
        Write-Host "  Launching Chrome with remote debugging ..."
        Start-Process -FilePath $chrome -ArgumentList @(
            "--remote-debugging-port=9222",
            "--user-data-dir=$ChromeProf",
            $TargetUrl
        )
        Start-Sleep -Seconds 4
        try {
            $r = Invoke-WebRequest -Uri "http://localhost:9222/json/version" -TimeoutSec 5 -UseBasicParsing
            if ($r.StatusCode -eq 200) { Write-Host "  CDP endpoint is up." -ForegroundColor Green }
        } catch {
            Write-Host "  Not up yet. Check again after Chrome finishes loading." -ForegroundColor Yellow
        }
    } else {
        Write-Host "  Chrome not found. Launch it manually with --remote-debugging-port=9222" -ForegroundColor Yellow
    }
}

# --- 5. Next steps ------------------------------------------
Write-Host "[5/5] Done" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Green
Write-Host "  1) Log in to PTU yourself in the Chrome window that opened"
Write-Host "  2) In this folder run:  gemini"
Write-Host "  3) Type /mcp to confirm playwright and filesystem are connected"
Write-Host "  4) First prompt (paste the Korean line from the chat):"
Write-Host "     read the three progress docs and report current state only, change nothing"
Write-Host ""
Write-Host "Note: PTU logs you out after 30 minutes of inactivity." -ForegroundColor Yellow
Write-Host "Note: GEMINI.md and .gemini\settings.json were downloaded as UTF-8 files." -ForegroundColor Yellow
