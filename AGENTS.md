# 공동 작업 규칙 (Claude Code ↔ ChatGPT Codex)

이 저장소의 `db-course/`는 대학 강의 **클라우드 데이터베이스** 수업 자료(10장부터)를 Claude Code와 Codex가 번갈아 개발하는 공간이다.
사용자(강의자)는 GitHub 커밋 기록으로 진행 상황을 확인한다.

## 시작할 때 (반드시)
1. `git pull origin claude/setup-claude-cli-AS1R6`
2. `db-course/STATUS.md`만 먼저 읽는다. LOG.md·원본 파일은 필요할 때만 읽는다 (토큰 절약).

## 끝낼 때 (토큰이 떨어지기 전에 반드시)
1. `db-course/STATUS.md`의 "현재 상태 / 다음 할 일"을 5줄 이내로 갱신
2. `db-course/LOG.md` 맨 위에 한 줄 추가: `YYYY-MM-DD [claude|codex] 한 일 → 결과 파일`
3. 커밋 메시지 앞에 `[claude]` 또는 `[codex]`를 붙여 커밋 후 같은 브랜치에 푸시
4. 작업 중간이라도 30분 또는 큰 단계마다 커밋·푸시 (중단돼도 이어받을 수 있게)

## 브랜치
- 공유 브랜치: `claude/setup-claude-cli-AS1R6` 하나만 사용. 두 AI가 동시에 작업하지 않는다.
- main 브랜치에 직접 푸시하지 않는다.

## 폴더 규칙
```
db-course/cdXX-N/source/   원본 교안(PPTX/PDF) – 수정 금지
db-course/cdXX-N/scripts/  생성 스크립트(build.py) + 노트·추가 슬라이드 원고(.py)
db-course/cdXX-N/output/   결과물: 파일명 끝에 (26)
db-course/docs/            스터디 노트, 인수인계 문서
```
- 결과 PPTX를 손으로 고치지 말고 **scripts의 원고를 고친 뒤 build.py로 다시 생성**한다.
- 최종 결과물은 **LMS 업로드용 PPTX만** 만든다 (PDF·이미지 등 부가 파일 생성 금지).
- 용량 절약: scripts·STATUS·LOG는 수시로 커밋, **output PPTX는 장(章) 완성 시점에만 커밋**한다.
- 실행: `pip install python-pptx` → `python db-course/cd10-1/scripts/build.py`

## 교안 제작 규칙 (강의자 요구사항)
1. 원본 교안의 디자인·레이아웃 유지 (원본 슬라이드를 복제해서 추가, 새 디자인 금지)
2. 빅테크/기업 공개 사례 + Colab 실습(psycopg2 → AWS RDS PostgreSQL, DB: dvdrental)과 연계
3. 설명은 PPTX **노트(설명란)**에, 형식은 아래와 같다:
   `【슬라이드 핵심】 본문 요약` / `【강의 설명】 강사 멘트·질문·정답` / `【연결】 관련 슬라이드 번호` / `【출처】 공식 링크`
4. **노트와 본문 일치**: 노트에서 강조한 핵심은 본문에도 있어야 하고, 본문 오류는 바로잡는다
5. 사례는 출처가 확인 가능한 공개 자료만 쓰고, 불확실하면 STATUS.md에 "확인 필요"로 남긴다
6. 결과는 LibreOffice로 PDF 렌더링해 글자 넘침·겹침을 확인한다

## 금지
- 비밀번호·AWS 키·`.streamlit/secrets.toml` 커밋 금지 (Colab은 `userdata.get(...).strip()` 사용)
- 원본 source 파일 수정·삭제 금지
