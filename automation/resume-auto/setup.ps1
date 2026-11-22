# 평택대 이력서 자동 입력 - 윈도우 셋팅
# 사용법: PowerShell 에서  .\setup.ps1
$ErrorActionPreference = "Stop"

Write-Host "[1/4] Node.js 확인" -ForegroundColor Cyan
try { $v = (node --version) } catch { $v = $null }
if (-not $v) {
  Write-Host "  Node.js 가 없습니다. https://nodejs.org 에서 LTS 를 설치한 뒤 다시 실행하세요." -ForegroundColor Red
  exit 1
}
Write-Host "  Node $v"

Write-Host "[2/4] Gemini CLI 설치" -ForegroundColor Cyan
npm install -g @google/gemini-cli

Write-Host "[3/4] Playwright 브라우저 내려받기" -ForegroundColor Cyan
npx -y playwright install chromium

Write-Host "[4/4] resume.yaml 준비" -ForegroundColor Cyan
if (-not (Test-Path "resume.yaml")) {
  Copy-Item "resume.example.yaml" "resume.yaml"
  Write-Host "  resume.yaml 을 만들었습니다. 내용을 채운 뒤 진행하세요." -ForegroundColor Yellow
} else {
  Write-Host "  resume.yaml 이 이미 있습니다."
}

Write-Host ""
Write-Host "셋팅 끝. 다음 순서로 하세요:" -ForegroundColor Green
Write-Host "  1) resume.yaml 을 채웁니다"
Write-Host "  2) 첨부할 파일은 files\ 폴더에 넣습니다"
Write-Host "  3) 이 폴더에서  gemini  를 실행합니다"
Write-Host "  4) /mcp  를 쳐서 playwright 와 filesystem 이 연결됐는지 확인합니다"
Write-Host "  5) '사이트를 열어줘' 라고 말하고, 로그인은 직접 합니다"
