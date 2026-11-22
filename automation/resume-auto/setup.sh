#!/usr/bin/env bash
# 평택대 이력서 자동 입력 - 맥/리눅스 셋팅
set -euo pipefail

echo "[1/4] Node.js 확인"
command -v node >/dev/null || { echo "  Node.js 가 없습니다. https://nodejs.org 에서 LTS 설치 후 다시 실행하세요."; exit 1; }
echo "  Node $(node --version)"

echo "[2/4] Gemini CLI 설치"
npm install -g @google/gemini-cli

echo "[3/4] Playwright 브라우저 내려받기"
npx -y playwright install chromium

echo "[4/4] resume.yaml 준비"
if [ ! -f resume.yaml ]; then
  cp resume.example.yaml resume.yaml
  echo "  resume.yaml 을 만들었습니다. 내용을 채운 뒤 진행하세요."
else
  echo "  resume.yaml 이 이미 있습니다."
fi

cat <<'TXT'

셋팅 끝. 다음 순서로 하세요:
  1) resume.yaml 을 채웁니다
  2) 첨부할 파일은 files/ 폴더에 넣습니다
  3) 이 폴더에서  gemini  를 실행합니다
  4) /mcp  를 쳐서 playwright 와 filesystem 이 연결됐는지 확인합니다
  5) "사이트를 열어줘" 라고 말하고, 로그인은 직접 합니다
TXT
