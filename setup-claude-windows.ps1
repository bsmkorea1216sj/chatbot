# Claude Code Windows VM 로그인 문제 사전 방지 스크립트
# 관리자 권한으로 실행하세요: PowerShell (관리자) -> .\setup-claude-windows.ps1

param(
    [string]$ClaudeDir = "D:\claude"
)

Write-Host "=== Claude Code Windows VM 설정 시작 ===" -ForegroundColor Cyan

# 1. D:\claude 폴더 생성
if (-not (Test-Path $ClaudeDir)) {
    New-Item -ItemType Directory -Path $ClaudeDir -Force | Out-Null
    Write-Host "[OK] $ClaudeDir 폴더 생성 완료" -ForegroundColor Green
} else {
    Write-Host "[OK] $ClaudeDir 폴더 이미 존재" -ForegroundColor Yellow
}

$claudeDataDir = "$ClaudeDir\.claude"
$userClaudeDir = "$env:USERPROFILE\.claude"

# 2. 기존 .claude 폴더를 D드라이브로 이동
if (Test-Path $userClaudeDir) {
    if (-not (Test-Path $claudeDataDir)) {
        Move-Item $userClaudeDir $claudeDataDir
        Write-Host "[OK] 기존 .claude 폴더를 $claudeDataDir 로 이동 완료" -ForegroundColor Green
    } else {
        Write-Host "[SKIP] $claudeDataDir 이미 존재 - 이동 생략" -ForegroundColor Yellow
    }
} else {
    # .claude 폴더가 없으면 새로 생성
    New-Item -ItemType Directory -Path $claudeDataDir -Force | Out-Null
    Write-Host "[OK] $claudeDataDir 폴더 생성 완료" -ForegroundColor Green
}

# 3. C드라이브에 심볼릭 링크 생성 (Claude Code가 기본 경로를 참조하도록)
if (-not (Test-Path $userClaudeDir)) {
    try {
        New-Item -ItemType SymbolicLink -Path $userClaudeDir -Target $claudeDataDir -ErrorAction Stop | Out-Null
        Write-Host "[OK] 심볼릭 링크 생성: $userClaudeDir -> $claudeDataDir" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] 심볼릭 링크 생성 실패. 관리자 권한으로 실행했는지 확인하세요." -ForegroundColor Red
        Write-Host "       오류: $_" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[OK] 심볼릭 링크 이미 존재" -ForegroundColor Yellow
}

# 4. 환경변수 설정 (CLAUDE_CONFIG_DIR) - 세션 간 유지
[System.Environment]::SetEnvironmentVariable("CLAUDE_CONFIG_DIR", $claudeDataDir, "User")
Write-Host "[OK] 환경변수 CLAUDE_CONFIG_DIR=$claudeDataDir 설정 완료" -ForegroundColor Green

# 5. 현재 세션에도 환경변수 적용
$env:CLAUDE_CONFIG_DIR = $claudeDataDir

# 6. D:\claude\chatbot 프로젝트 폴더 생성
$projectDir = "$ClaudeDir\chatbot"
if (-not (Test-Path $projectDir)) {
    New-Item -ItemType Directory -Path $projectDir -Force | Out-Null
    Write-Host "[OK] 프로젝트 폴더 $projectDir 생성 완료" -ForegroundColor Green
}

# 7. claude auth login 브라우저 문제 대비 - 안내 메시지
Write-Host ""
Write-Host "=== 설정 완료 ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "다음 단계:" -ForegroundColor White
Write-Host "  1. 터미널을 재시작하세요 (환경변수 적용)" -ForegroundColor White
Write-Host "  2. Claude Code 로그인:" -ForegroundColor White
Write-Host "     - 브라우저 자동 열림:  claude auth login" -ForegroundColor Cyan
Write-Host "     - VM 브라우저 문제 시:  claude auth login --print-token" -ForegroundColor Cyan
Write-Host ""
Write-Host "  3. 프로젝트 실행:" -ForegroundColor White
Write-Host "     cd $projectDir" -ForegroundColor Cyan
Write-Host "     claude" -ForegroundColor Cyan
Write-Host ""
Write-Host "로그인 정보 저장 위치: $claudeDataDir" -ForegroundColor Gray
