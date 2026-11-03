# 공동 작업 규칙 (Claude Code ↔ ChatGPT Codex)

대학 강의 **클라우드 데이터베이스** 수업 자료(10장부터)를 Claude Code와 Codex가 번갈아 만든다.

## 역할 분담
- **Google Drive = 실제 파일** (PPTX, Colab 노트북 등). 폴더는 하나만 쓴다, 하위 폴더 만들지 않는다.
  - 강의 자료 폴더: https://drive.google.com/drive/folders/1WL8_UI8wvOyqXormXoXFx4L9ykGRkxdS
  - 강의자가 PC와 이 폴더를 동기화한다.
- **GitHub = 소통용 텍스트만** (이 규칙, `db-course/STATUS.md`, `db-course/LOG.md`, 스크립트·원고 `.py`, 메모 `.md`)
  - PPTX·PDF·ipynb 등 바이너리는 GitHub에 올리지 않는다.

## 파일 규칙 (가장 중요)
1. AI가 만든 첫 초안: 원래 이름 끝에 **(26)** → 예: `CD10-2_Index_Join(26).pptx`
2. 강의자가 그 파일을 열어 수정·저장한다. **드라이브의 그 파일이 항상 기준본**이다.
3. 이후 수정은 **새 파일을 만들지 않고 같은 파일에 계속 업데이트**한다 (날짜 붙인 사본 만들지 않음).
   - 특히 Colab(.ipynb)은 수정 사항을 그 파일에 바로 적용한다.
4. 기존 파일·슬라이드·셀을 **함부로 지우지 않는다.** 강의자가 붙인 이미지·직접 고친 내용은 요청 없이 바꾸지 않는다.
5. 드라이브 파일 내용을 직접 덮어쓸 수 없는 환경이면(예: Claude Code 드라이브 연결은 새 파일 생성만 가능),
   새 파일을 만들지 말고 **바꿀 슬라이드·셀 내용만 강의자에게 제시**해 강의자가 붙여넣게 한다.

## 시작할 때
1. `git pull origin claude/setup-claude-cli-AS1R6`
2. `db-course/STATUS.md`만 먼저 읽는다 (토큰 절약).
3. 작업할 PPTX는 드라이브 폴더의 최신 기준본을 사용한다.

## 끝낼 때 (토큰이 떨어지기 전에 반드시)
1. 결과를 드라이브의 해당 파일에 반영 (불가하면 바꿀 내용을 강의자에게 제시)
2. `db-course/STATUS.md` 갱신 (현재 상태 / 다음 할 일, 5줄 이내)
3. `db-course/LOG.md` 맨 위에 한 줄: `YYYY-MM-DD HH:MM [claude|codex] 한 일 → 드라이브 파일명`
4. 커밋 메시지 앞에 `[claude]` 또는 `[codex]`, 같은 브랜치에 푸시

## 브랜치
- 공유 브랜치 `claude/setup-claude-cli-AS1R6` 하나만 사용. 두 AI가 동시에 작업하지 않는다. main에 직접 푸시 금지.

## 교안 제작 규칙
1. 원본 교안의 디자인·레이아웃 유지 (원본 슬라이드를 복제해서 추가, 새 디자인 금지)
2. 빅테크/기업 공개 사례 + Colab 실습(psycopg2 → AWS RDS PostgreSQL, DB: dvdrental)과 연계
3. 설명은 PPTX **노트(설명란)**: `【슬라이드 핵심】` / `【강의 설명】` / `【연결】` / `【출처】`
4. 노트와 본문 일치: 노트에서 강조한 핵심은 본문에도 넣고, 본문 오류는 바로잡는다
5. 사례는 확인 가능한 공개 자료만, 불확실하면 STATUS.md에 "확인 필요"로 남긴다
6. 결과는 LMS 업로드용 PPTX만 (PDF·이미지 등 부가 파일 만들지 않음)
7. 렌더링해서 글자 넘침·겹침 확인

## 금지
- 비밀번호·AWS 키·`.streamlit/secrets.toml` 커밋 금지 (Colab은 `userdata.get(...).strip()`)
- 드라이브 파일 삭제, 하위 폴더 생성, 날짜 붙인 사본 생성 금지
- Colab 접속 방식: 보안비밀 `AWS_ACCESS_KEY`/`AWS_SECRET_KEY` + `DB_HOST` 등, DB 비밀번호는 getpass, RDS SSL(verify-full)
  (기준 코드: `db-course/cd10-1/scripts/colab_nb.py`)
