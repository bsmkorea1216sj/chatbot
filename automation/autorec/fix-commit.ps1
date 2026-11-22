# ============================================================
# autorec 커밋 복구 스크립트
# 증상: git identity 미설정으로 commit 이 멈춰 푸시된 것이 없음
# 쓰는 법: PowerShell 에 통째로 붙여넣고 Enter
# ============================================================

function Invoke-AutorecFix {
    $WorkDir  = "G:\내 드라이브\(G)개인\이력서자동화"
    $Branch   = "main"
    $GitName  = "김성진"
    $GitEmail = "bsmkorea1216@gmail.com"

    if (-not (Test-Path -LiteralPath $WorkDir)) {
        Write-Host "폴더가 없습니다: $WorkDir" -ForegroundColor Red; return
    }
    Push-Location -LiteralPath $WorkDir
    try {
        git rev-parse --is-inside-work-tree 2>$null | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "git 저장소가 아닙니다: $WorkDir" -ForegroundColor Red; return
        }

        # 1) 커밋이 막혔던 원인. 이 저장소에만 적용합니다(--global 아님)
        Write-Host "[1/5] git 사용자 정보 설정" -ForegroundColor Cyan
        git config user.name  $GitName
        git config user.email $GitEmail
        Write-Host ("  user.name  = " + (git config user.name))
        Write-Host ("  user.email = " + (git config user.email))

        # 2) 줄바꿈 정규화. 없으면 GitHub Actions 가 RESUME.md 를 매번 다시 커밋합니다
        Write-Host "[2/5] .gitattributes 확인" -ForegroundColor Cyan
        $gaPath = Join-Path $WorkDir ".gitattributes"
        if (-not (Test-Path -LiteralPath $gaPath)) {
            $enc = New-Object System.Text.UTF8Encoding($false)
            [System.IO.File]::WriteAllText($gaPath, "* text=auto eol=lf`n", $enc)
            Write-Host "  생성했습니다."
        } else {
            Write-Host "  이미 있습니다."
        }

        # 3) 올릴 파일만 골라서 스테이징
        Write-Host "[3/5] 스테이징" -ForegroundColor Cyan
        $targets = @(
            ".gitattributes",
            ".gitignore",
            ".vscode/mcp.json",
            "data/resume_master.json",
            "scripts/generate_resume.py",
            ".github/workflows/resume-sync.yml",
            "RESUME.md"
        )
        foreach ($t in $targets) {
            if (Test-Path -LiteralPath (Join-Path $WorkDir $t)) {
                git add -- $t
            } else {
                Write-Host "  (없음, 건너뜀) $t" -ForegroundColor DarkGray
            }
        }
        Write-Host "  --- 현재 상태 ---"
        git status -s

        # 4) 커밋
        Write-Host "[4/5] 커밋" -ForegroundColor Cyan
        git diff --cached --quiet
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  스테이징된 변경이 없습니다. 이미 커밋되었을 수 있습니다." -ForegroundColor Yellow
        } else {
            git commit -m "feat: MCP 설정과 이력서 자동 생성 파이프라인 추가"
            if ($LASTEXITCODE -ne 0) {
                Write-Host "  커밋에 실패했습니다. 위 메시지를 확인하세요." -ForegroundColor Red; return
            }
        }

        # 5) 푸시
        Write-Host "[5/5] 푸시" -ForegroundColor Cyan
        git push -u origin $Branch
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  푸시에 실패했습니다. 위 메시지를 확인하세요." -ForegroundColor Red; return
        }

        Write-Host "`n--- 결과 ---" -ForegroundColor Green
        git log --oneline -3
        git status -sb
        Write-Host "`nActions 실행 확인: https://github.com/bsmkorea1216sj/autorec/actions" -ForegroundColor Yellow
    }
    finally {
        Pop-Location
    }
}

Invoke-AutorecFix
