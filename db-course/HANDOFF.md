# Codex 공유용 인수인계 (Claude → Codex) · 2026-11-11

> 규칙은 루트 `AGENTS.md`, 현재 상태·파일 ID는 `db-course/STATUS.md`, 한 줄 기록은 `db-course/LOG.md`(최신이 위).
> 실제 파일(PPTX·ipynb)은 Google Drive 폴더에만 있고, GitHub에는 스크립트·기록만 있다.
> 브랜치: `claude/setup-claude-cli-AS1R6` (main 직접 푸시 금지)

## 1. 작업 대상 파일 (Drive, ID로 작업)
| 파일 | Drive ID | 상태 |
|---|---|---|
| [클라우드데이터베이스기초] 11-1_데이터베이스 설계 개요(26)_보강.pptx | `1zYS43RH1IpcrfJiDsCbz95kl_Wf2du2F` | 48장, 강의자가 Google Slides에서 계속 편집 중 |
| [클라우드데이터베이스기초] 11-3_데이터베이스 설계실습(26).pptx | `16mLq0QLxmGUH1mR2QWdsGam0tufQbYum` | 22장 |
| CD11-3_Colab_설계실습.ipynb | `1mJEtXxBEUK9THq9pVF607BVqO_vDO5Qg` | 30셀, SQLite |

## 2. 11-1 보강본에서 Claude가 바꾼 페이지 (현재 쪽 번호 기준)
| 쪽 | 내용 | 스크립트 (`db-course/cd11-1/scripts/`) |
|---|---|---|
| 5·6 | 데이터의 구분 사례: 이란 표적 추적 → **Palantir × 반도체 공정 데이터(Athinia: Merck KGaA·Palantir 2021, Micron 2022)**. 이후 강의자가 6쪽을 직접 재디자인(“Palantir Foundry와 데이터 레포지터리”) | `case_semiconductor.py` |
| 9 | 본문 사례 연결 1 · 데이터의 세 세계: 원본 제목 자리, 3단 카드+아이콘, 현실→Ontology→PostgreSQL, 같은 주문 B0001 추적 | `slide9_three_worlds.py` |
| 12 | 데이터 모델링 사례 · **Meta Muse**: 귀찮은 환불 신청을 대신하는 AI 에이전트(2026.09 출시), 신청서 칸=열·채우기=INSERT·주문번호=FK, 알렉산더 왕 사진(CC BY-SA 4.0, Meta 제공) | `slide_meta_muse.py` |
| 25 | **의미 객체 모델 vs ER 모델**: 도서관 대출을 Chen ER / Kroenke 의미 객체 다이어그램으로 나란히 + 비교 표 | `slide_som_vs_er.py` |
| 29 | 적용 사례 | 주문·결제의 **개념(Palantir Ontology)·논리(Google Knowledge Catalog)·물리(AWS DynamoDB)** 3단 행 + 관계형 대응 SQL + 단계별 토론 | `slide_case_levels.py` |
| 39 | Palantir Ontology: 현실 업무를 데이터 모델로 → **개념·논리·물리** 3단 행 추가, 빈 글머리표 제거, 노트 교체 | `slide_ontology_levels.py` |
| 30·31 | 실습 예제 · 동네 도서관 대출(개념→논리→물리 문제, 카드 아래 작은 정답) / 정답 pgAdmin SQL(주석=정답 설명). 강의자가 18쪽 뒤 → 30·31쪽으로 옮김 | `slide_library_example.py`, SQL: `../sql/library_answer.sql` (PostgreSQL 16 실행 검증) |

모든 추가 슬라이드: 원본 템플릿 레이아웃, 노트 【슬라이드 핵심】【강의 설명】【연결】【출처】, 하단 `※ 약어` 주석, 출처 줄.

## 3. 11-3에서 바꾼 것 (`db-course/cd11-3/scripts/`)
- 교안↔Colab 미션 연계: 교안 🎯 버튼 → 노트북 `#scrollTo=mission_m1..m5, mission_hw`
- 미션 순서 = 교안 순서: 미션4 = 상담 카드(14·15쪽), 미션5 = 나눠 낸 결제(17쪽)
- 노트북: 확인 도우미 셀 코드 숨김(`#@title`), `input()` 입력 → 즉시 ✅/❌, 틀리면 셀 안에서 3회 재입력, 도우미 미실행·옛 버전이면 미션 셀이 자동으로 불러옴(HELPER_V=2), 🔎 예측 퀴즈 4개
- 정답: 교안 버튼 아래 작은 글씨 + 19·20쪽 미션 정답 / 실습1 정답은 5개 테이블(합계·부가세는 계산값, 회원·포인트는 과제), 예외(판매 당시 단가 저장) 표기
- 주요 파일: `missions.py`(미션·도우미 원고), `colab_nb.py`(노트북 생성), `answers.py`(정답·오답), `answer_marks.py`, `renumber_45.py`, `p7_p10_calc.py`

## 4. 작업 시 주의
1. **강의자가 Google Slides/Colab에서 동시에 편집한다.** 업로드 직전 Drive 수정 시각을 다시 보고, 바뀌었으면 최신본을 다시 받아 그 위에 적용한다(덮어쓰기 금지).
2. Google Slides 재저장 시 도형 이름·ID가 바뀐다 → 도형은 이름이 아니라 **텍스트로** 찾는다.
3. 11-1에는 제목이 같은 슬라이드가 있다(예: “적용 사례” 29쪽·36쪽) → 제목만으로 찾지 말고 내용까지 확인.
4. 11-3 Colab: 옛 탭이 열려 있으면 자동 저장으로 새 버전을 덮어쓴다 → 업로드 후 강의자에게 탭 새로고침 안내.
5. 슬라이드를 추가하면 뒤쪽 쪽 번호가 밀린다(노트 속 “○쪽” 참조 확인).

## 5. 확인 필요 / 다음 할 일
- 11-1 25쪽 의미 객체 다이어그램의 개수 표기(1.1, 0.N)는 Kroenke 교재 방식으로 그렸으나 원문 표기 직접 확인 전
- 11-1 12쪽 Muse 절감액 사례는 사용자·직원 게시물 위주로 독립 검증 전(슬라이드·노트에 명시)
- 10-2·10-3 Colab 실행 후 ‘예상 결과’ 패널을 실측값으로 교체 (STATUS ‘다음 할 일’)
