# ============================================================
# 제미니(Gemini CLI)로 평택대 지원서 자동입력 셋팅
# 코덱스가 쓰던 것과 같은 크롬(CDP 9222)에 붙어 같은 방식으로 작업합니다.
# 쓰는 법: PowerShell 에 통째로 붙여넣고 Enter (마지막 줄에서 Enter 한 번 더)
# ============================================================

function Install-GeminiForAutorec {
    $WorkDir = "G:\내 드라이브\(G)개인\이력서자동화"
    $TargetUrl = "https://login.ptu.ac.kr/nx/index.html?loginGbn=pfic"
    $ChromeProfile = "C:\chrome_mcp_profile"

    function Write-Utf8NoBom {
        param([string]$FilePath, [string]$Content)
        $enc = New-Object System.Text.UTF8Encoding($false)
        [System.IO.File]::WriteAllText($FilePath, $Content, $enc)
    }

    if (-not (Test-Path -LiteralPath $WorkDir)) {
        Write-Host "폴더가 없습니다: $WorkDir" -ForegroundColor Red; return
    }
    Push-Location -LiteralPath $WorkDir
    try {
        # 1) Gemini CLI
        Write-Host "[1/5] Gemini CLI 확인" -ForegroundColor Cyan
        if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
            Write-Host "  Node.js 가 없습니다. https://nodejs.org 에서 LTS 설치 후 다시 실행하세요." -ForegroundColor Red
            return
        }
        if (Get-Command gemini -ErrorAction SilentlyContinue) {
            Write-Host "  이미 설치되어 있습니다."
        } else {
            Write-Host "  설치합니다..."
            npm install -g @google/gemini-cli
            if ($LASTEXITCODE -ne 0) { Write-Host "  설치 실패." -ForegroundColor Red; return }
        }

        # 2) .gemini/settings.json - 코덱스가 쓰던 것과 같은 CDP 엔드포인트
        Write-Host "[2/5] .gemini\settings.json 생성" -ForegroundColor Cyan
        New-Item -ItemType Directory -Force -Path (Join-Path $WorkDir ".gemini") | Out-Null
        $settings = @'
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": [
        "-y", "@playwright/mcp@latest",
        "--cdp-endpoint", "http://localhost:9222",
        "--caps=vision"
      ]
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]
    }
  }
}
'@
        Write-Utf8NoBom -FilePath (Join-Path $WorkDir ".gemini\settings.json") -Content $settings
        Write-Host "  CDP 9222 에 연결하도록 설정했습니다(코덱스와 같은 크롬)."

        # 3) GEMINI.md
        Write-Host "[3/5] GEMINI.md 생성" -ForegroundColor Cyan
        $geminiMd = @'
# 역할

평택대 교원 지원서(https://login.ptu.ac.kr/nx/index.html?loginGbn=pfic)의
입력을 이어서 한다. 이미 상당 부분이 입력·저장되어 있다. **처음부터 다시 하지 않는다.**

# 시작하기 전에 반드시 읽을 것

1. `docs/ptu-application-workflow.md` — 작업 절차와 확인사항
2. `docs/ptu-progress-log.md` — **현재 어디까지 되어 있는지**와 Nexacro 조작 요령
3. `data/resume_master.json` — 이력 원본 데이터

이 셋을 읽기 전에는 화면을 건드리지 않는다.

---

# 절대 규칙

## 1. 최종 제출하지 않는다

"지원", "최종제출", "접수" 는 **사용자가 직접** 한다.
화면별 **"저장"** 은 눌러도 된다(임시저장). 최종 접수와는 다르다.
접수 마감: 2026-12-03 12:00. 마감 전 정정공고 변경 여부를 사용자에게 확인하도록 알린다.

## 2. 로그인·본인인증은 사용자가 한다

비밀번호·OTP 를 묻지도, 입력하지도, 기록하지도 않는다.
**로그인 후 30분간 화면 이동이 없으면 자동 로그아웃된다.** 작업이 길어지면 상태를 먼저 확인한다.

## 3. 이미 입력된 것을 덮어쓰지 않는다

작업 시작 시 `docs/ptu-progress-log.md` 의 진행표를 읽고, 화면을 **재조회**해
실제 상태를 확인한 뒤 미완료 항목만 진행한다.

## 4. 증빙으로 확인되지 않은 값은 넣지 않는다

학위취득일은 학위증명서상의 일자(발급일 아님).
성적 백분율은 성적표 값을 그대로 쓰고 임의 환산하지 않는다.
논문 서지정보는 원문과 대조한다. 불확실하면 사용자에게 묻는다.

---

# Nexacro 조작 규칙 (이미 검증된 것 — 그대로 따른다)

이 화면은 일반 HTML 이 아니다. DOM 셀렉터로 입력하지 말고 **데이터셋을 직접 다룬다.**

## 폼 객체 경로

```
WorkFrame.frames[0].form.div_Work
```
컴포넌트와 데이터셋이 이 객체에 **직접** 붙어 있다. `div_Work.form` 은 없다.

## 화면별 데이터셋

| 화면 | 데이터셋 |
|---|---|
| 시간강사경력 | `DS_AAAPLY0240` |
| 경력사항 | `DS_AAAPLY0250` |
| 학위논문 | `DS_AAAPLY0231` |
| 연구실적 | `DS_AAAPLY0270` |
| 특허및지적소유권 | `DS_AAAPLY0320` |
| 연구관심분야 | `DS_AAAPLY0290` |
| 증명서첨부 | `DS_AAAPLY0280` |
| 자기소개서 | `div` 하위 `txt_intro1Ctnt` ~ |

## 입력 순서와 함정

1. **행 추가 버튼으로 만든 새 행은 데이터셋 맨 앞(0번)에 들어간다.**
   마지막 인덱스에 값을 넣으면 기존 행을 덮어쓴다. **비어 있는 행을 찾아서** 넣는다.
2. `setColumn` 으로 값을 넣은 뒤 화면의 **저장** 버튼을 누른다.
3. 확인 대화상자와 성공 알림은 `window.confirm` / `window.alert` 를 가로채 기록한다.
   **화면을 이동하면 가로채기를 다시 설치한다.**
4. "변경된 데이터가 없습니다" = 이미 저장되었거나 변경이 인식되지 않은 경우다.
5. 자기소개서는 문항별 저장 버튼이 있지만 **한 번 저장하면 전체 문항이 저장된다.**
6. 경력사항의 **종료일은 필수**다. 시작일이 종료일보다 크면 저장이 막힌다.
7. **한글은 스크립트에 그대로 쓴다.** `\uXXXX` 이스케이프로 넣다가 글자가 틀린 적이 있다.
8. 화면이 아래로 스크롤되면 버튼 좌표가 어긋난다. **클릭 전에 맨 위로 올리고 스크린샷으로 확인한다.**
9. 날짜는 숫자 입력 후 실제 연·월·일 표시를 확인한다. 불완전한 날짜를 그대로 저장하지 않는다.
10. 화면 폭이 좁아 저장 버튼이 가려지면 왼쪽 메뉴 접기 화살표로 작업 영역을 넓힌다.

## 저장 검증

값 설정 호출이 성공했다는 것만으로 **입력 완료를 선언하지 않는다.**
저장 버튼 → 성공 알림 확인 → 다른 화면 갔다 돌아와 **재조회**해서 값이 남아 있는지 확인한다.
`입력만 완료` / `저장 확인` / `첨부 확인` / `최종 접수 확인` 을 서로 다른 상태로 보고한다.

## 파일 업로드 (검증된 절차)

업로드 창은 숨은 iframe(`edu_base_iframe`) 안에 `input[type=file]` 을 만든다.
기본 업로드 도구로는 찾지 못한다. 순서를 지킨다.

1. 행을 추가하고 증명서구분·학위를 데이터셋에 넣는다
2. 행의 파일업로드 돋보기를 눌러 창을 연다
3. iframe 의 `HTMLInputElement.prototype.click` 을 가로채 OS 파일창이 열리지 않게 한 뒤 창의 **추가** 를 누른다
4. 생긴 `input[name=upfile0]` 을 `document.adoptNode` 로 메인 문서에 옮긴다 (원래 부모와 다음 형제를 기록)
5. 업로드 도구로 파일을 넣는다
6. **파일이 들어간 입력 요소를 iframe 안 원래 위치로 되돌린다** ← 이걸 빠뜨리면 목록에 파일명이 보여도 실제 전송이 안 된다
7. 창의 **확인** 을 누른다. "업로드가 완료되었습니다" 알림 확인
8. 행의 첨부파일명이 채워지면 화면 **저장**

- 한도: 파일당 10MB, **한 번에 한 파일**
- 페이지에서 로컬 파일을 `fetch` 하는 방식은 쓰지 않는다(브라우저 팝업으로 멈춘다)
- 증명서구분 코드: 교인증명서 3, 학력및성적 9, 경력및재직 10, 최종학위논문 11, 연구실적물 12, 수상및특허 13, 기타 5
- 학위 코드: 국내학사 1, 국내석사 2, 국내박사 3

---

# 대화 방식

| 사용자의 말 | 할 일 |
|---|---|
| "지금 상태 확인해줘" | 진행 로그를 읽고 화면을 재조회해 실제 상태를 표로 보고. **아무것도 바꾸지 않는다** |
| "연구실적 이어서 해줘" | 해당 화면의 빈 행을 찾아 `resume_master.json` 값으로 채우고 저장·재조회 |
| "○○를 △△로 고쳐줘" | 어느 행인지 먼저 확인하고, 전/후를 보여준 뒤 수정 |
| "이 파일 첨부해줘" | 위 업로드 절차대로. 등록된 파일명을 재조회로 확인 |
| "이력서 데이터 고쳐줘" | `data/resume_master.json` 을 고치기 전 전/후를 보여주고 확인받는다. 고친 뒤 `python scripts/generate_resume.py` 로 RESUME.md 를 다시 만든다 |
| "진행 기록 갱신해줘" | `docs/ptu-progress-log.md` 의 표를 갱신. **개인정보는 적지 않고 건수와 상태만** 적는다 |
| "제출해줘" | **거절.** 1번 규칙 |

작업 단위마다 멈추고 보고한다. 한 화면을 끝내면 다음으로 넘어가기 전에 확인받는다.

# 보고 형식

```
화면: 연구실적
입력: 1건 추가 (기존 3건 유지)
저장: 성공 알림 확인
재조회: 4건 확인
미완료: 서지정보 원문 대조 1건
최종 제출: 하지 않음
```
'@
        Write-Utf8NoBom -FilePath (Join-Path $WorkDir "GEMINI.md") -Content $geminiMd
        Write-Host "  코덱스가 알아낸 Nexacro 조작 규칙을 그대로 담았습니다."

        # 4) 디버깅 크롬 확인 / 실행
        Write-Host "[4/5] 디버깅 크롬(CDP 9222) 확인" -ForegroundColor Cyan
        $cdpUp = $false
        try {
            $r = Invoke-WebRequest -Uri "http://localhost:9222/json/version" -TimeoutSec 3 -UseBasicParsing
            if ($r.StatusCode -eq 200) { $cdpUp = $true }
        } catch { $cdpUp = $false }

        if ($cdpUp) {
            Write-Host "  이미 떠 있습니다. 그 창을 그대로 씁니다." -ForegroundColor Green
        } else {
            $ChromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
            if (-not (Test-Path -LiteralPath $ChromePath)) {
                $ChromePath = "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
            }
            if (Test-Path -LiteralPath $ChromePath) {
                Write-Host "  크롬을 디버깅 모드로 엽니다..."
                Start-Process -FilePath $ChromePath -ArgumentList @(
                    "--remote-debugging-port=9222",
                    "--user-data-dir=$ChromeProfile",
                    $TargetUrl
                )
                Start-Sleep -Seconds 4
                try {
                    $r = Invoke-WebRequest -Uri "http://localhost:9222/json/version" -TimeoutSec 5 -UseBasicParsing
                    if ($r.StatusCode -eq 200) { Write-Host "  연결 확인됨." -ForegroundColor Green }
                } catch {
                    Write-Host "  아직 확인 안 됨. 크롬이 뜬 뒤 다시 확인하세요." -ForegroundColor Yellow
                }
            } else {
                Write-Host "  크롬을 찾지 못했습니다. 수동으로 디버깅 모드로 여세요." -ForegroundColor Yellow
            }
        }

        # 5) 안내
        Write-Host "[5/5] 완료" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "다음 순서로 하세요:" -ForegroundColor Green
        Write-Host "  1) 열린 크롬에서 평택대에 직접 로그인합니다 (본인인증 포함)"
        Write-Host "  2) 이 폴더에서  gemini  를 실행합니다"
        Write-Host "  3) /mcp  로 playwright, filesystem 연결을 확인합니다"
        Write-Host "  4) 첫 지시:  진행 문서 세 개 읽고 지금 상태만 알려줘. 아무것도 입력하지 마."
        Write-Host ""
        Write-Host "주의: 로그인 후 30분간 조작이 없으면 자동 로그아웃됩니다." -ForegroundColor Yellow
    }
    finally { Pop-Location }
}

Install-GeminiForAutorec
