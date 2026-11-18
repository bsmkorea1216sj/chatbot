# STATUS (작업 시작 시 이 파일만 먼저 읽기)

**마지막 갱신:** 2026-11-18 · codex
**드라이브 폴더:** https://drive.google.com/drive/folders/1WL8_UI8wvOyqXormXoXFx4L9ykGRkxdS

**CD 작업 기록:** [CD강의.md](CD강의.md)

## 현재 상태
- **12-3 최종 과제:** 12-3 최종 과제 ③ 추가(교안 57쪽, RDS 삭제 58쪽, 총 60장). 여성 액세서리몰 검색·카테고리·가격/재고 카드·주문 조회 화면 틀을 제공하고, 학생이 상품 필터와 주문·주문상세·상품 조인 SQL을 완성한다. 저장 당시 단가, 무결성 제약, 주문 조회 실행 계획을 제출한 뒤 최종 삭제한다. 로컬 HTTP·구문·교안 렌더 검증, 실제 AWS 미실행. `cd12-series/final-assignment/`.
- **12장 교안 흐름·약어 보강:** 이론 → Colab·과제 → 마무리. 실습 시작 12-1 32쪽, 12-2 25쪽, 12-3 54쪽. 안내표 단계별 셀 링크와 노트북 쪽수 동기화. `cloud_architecture/CA강의.md` 형식으로 약어가 나오는 70쪽에 영문 원어·한글 뜻. `cd12-series/reorder_labs.py`·`add_abbreviation_footers.py`.
- **12장 여성 액세서리몰 연속 실습 완료:** 교안 3종(36/31/60쪽)·Colab 3종을 기존 Drive ID/파일명 그대로 갱신. 귀걸이·목걸이·헤어핀, 후속 팔찌·반지·브로치. 같은 RDS `cd12-shop-lab`·`shop` 유지. 기준/재현: `cd12-series/README.md`·`update_accessories.py`(이전 생성기 실행 뒤 마지막 보정 필수).
- **이어하기:** 12-1 DB·실제 화면 웹앱, 12-2 5표→7개 엔티티·결제/배송/리뷰·CRUD, 12-3 논리 열 정렬·제약·물리 최적화. 기존 예제 상품명만 전환하며 가격·재고·주문·사용자 상품 보존. 각 intro에 조건/공통 상품/다음 파트 링크, 교안 개요·노트·마무리도 정렬.
- **종료:** 12-1·2의 DELETE API 분기를 제거하고 STOP만 제공. 12-3 마지막8번 셀에서만 최종 DELETE(실습 태그·식별자 재입력·삭제방지/상태 확인·삭제 완료 waiter). 공용 DB_HOST는 삭제 차단. 12-3 첫 `hf` 실행불가 셀은 같은 ID의 안내 markdown으로 변경.
- **검증/다음:** 코드 구문·전체 Colab anchor·미디어/테마/레이아웃 보존·모의16분기·SQLite fixture 상품전환/재실행 통과. 36/31/60쪽 렌더링, 12-2/3 목표·Summary 한글 표시 보정, 저장본6개 바이트 대조 완료. 이번 변경의 실제 AWS·PostgreSQL 전체 실행은 미검증(기존12-1 AWS 검증 이력과 구분), 다음 확인 필요.
- 10-1 기준본: `CD10-1_PostgreSQL26.pptx` (48장, 강의자 편집 중). 약어 주석 전체 반영 완료
  - Colab `CD10-1_Colab_Lab(26).ipynb`: 실제 RDS 실행 확인됨(postgresql-lab-01:5433, DB=postgres), 결과 인사이트 셀 포함
- 10-2 초안: `CD10-2_Index_Join(26).pptx` (36장, 11-04 02:39) — 원본 31장 + GitLab 사례·조인 방식 3가지·Colab 실습 3장, 노트 전체, 약어 주석, 원본 오류 5곳 수정
  - Colab `CD10-2_Colab_Lab(26).ipynb`: 각 셀 자동 접속, 트리·비교 표 출력 — 실행 검증 전. 교안 29~35 결과 패널은 '예상 결과' → 실행 후 실측값으로 교체 필요
- 11-3 초안: `[클라우드데이터베이스기초] 11-3_데이터베이스 설계실습(26).pptx` (22장, 11-2 정규화 패턴, 미션 정답 19·20쪽) + `CD11-3_Colab_설계실습.ipynb` (SQLite, 확인 도우미 코드 숨김, 미션1~5·과제(교안 순서: 상담=미션4 14쪽, 결제=미션5 17쪽) input() 입력→즉시 ✅/❌·3회 재입력, 도우미 미실행 시 자동 불러옴, 🔎예측 퀴즈 4개, 정답은 교안 버튼 아래·19·20쪽).
- 11-1 보강본 `…11-1_데이터베이스 설계 개요(26)_보강.pptx` (48장): Claude가 5·6·9·12·25·29·30·31쪽 보강 → 상세는 `db-course/HANDOFF.md` (Codex 인수인계)
- 11-2 정규화(26) 기준본(41장): 13~15쪽 2NF와 22~27쪽 4NF의 문제→이상→분리·검증 흐름 통일, 제품 3행·주문목록 6행 및 4NF 조합 6행 복원 검증(`cd11-2/scripts/align_2nf_4nf_flow.py`). 22쪽에 사원 10의 독립 목록 2×3 조합과 4차 정규화 분리 예시·발표자 노트 추가(`cd11-2/scripts/slide22_4nf_intro.py`). 24쪽에 사원 10의 조합 표와 입력·수정·삭제 이상 색상 카드 및 노트 추가(`cd11-2/scripts/slide24_4nf_anomalies.py`). 27쪽은 SI·OO의 사원 10 DBA 기록을 구분하고 일반 DBA 경험자(10·20)와 PA DBA 경험자(20)를 비교. 31~41쪽은 Colab 셀 11개와 바로가기·출력·제출 안내 동기화(`cd11-2/scripts/slide27_4nf_applied.py`, `cd11-2/scripts/sync_colab_slides_31_41.py`). 기존 Drive ID 반영·렌더링 확인.
- ⚠️ 11-3 Colab은 옛 탭이 열려 있으면 자동 저장으로 덮어씀 → 업로드 후 탭 새로 열기
- 10-3 초안: `CD10-3_RAID(26).pptx` (31장) + `CD10-3_Colab_Lab(26).ipynb` (실습 3 RDS 조회만 실행 검증 전)

## 기준본 파일 ID (같은 이름 파일이 있으니 ID로 작업)
| 장 | 파일명 | ID |
|---|---|---|
| 10-1 교안 | CD10-1_PostgreSQL(26).pptx | 1QqGN8GBVzgOGRJjd7hlicKhei2oKa1th |
| 10-1 Colab | CD10-1_Colab_Lab(26).ipynb | 1AfCr5c2lGQwY9CXWRxLIh5LJc3_6rPUm |
| 10-2 교안 | CD10-2_Index_Join(26).pptx | 1D6ougQSnW71Glc1a1R9n8n82wMhmJWWk |
| 10-2 Colab | CD10-2_Colab_Lab(26).ipynb | 1Jb5PZw_Qqo0aYcYQPySpeWM6IEKnT4KL |
| 10-3 교안 | CD10-3_RAID(26).pptx | 1RODCGBNgtqHxTZiK-vBGZ8b7W85-ZNbg |
| 10-3 Colab | CD10-3_Colab_Lab(26).ipynb | 1tZUZBWdqPzQIemlBHJ_gW5TyevIi0F-Q |
| 실습 DB 준비 | CD10_RDS_DB생성(26).ipynb | 1LCZQRDjSoCETzQZ_Has8BfoL2JMbD3Ic |
| 11-2 교안 | [클라우드데이터베이스기초] 11-2_정규화(26).pptx | 1kpLd9222ZqByf4NxcInQsgOhGEw08dgQ |
| 11-3 교안 | [클라우드데이터베이스기초] 11-3_데이터베이스 설계실습(26).pptx | 16mLq0QLxmGUH1mR2QWdsGam0tufQbYum |
| 11-1 교안(보강) | [클라우드데이터베이스기초] 11-1_데이터베이스 설계 개요(26)_보강.pptx | 1zYS43RH1IpcrfJiDsCbz95kl_Wf2du2F |
| 11-1 Colab | CD11-1_Colab_Lab(26).ipynb | 1fQ--R38hR6exXmFtyl8wvDKpZNn9DSP1 |
| 12-1 교안 | [클라우드데이터베이스기초] 12-1데이터베이스 설계.Part1(26).pptx | 1Gu6kZNfazuj6jpYexa_Jd7aVNd0XVwmu |
| 12-1 Colab | CD12-1_Colab_쇼핑몰DB_웹앱(26).ipynb | 1URPntHhY0jY96psj9cK0Khrzq3gLb8KX |
| 12-2 교안 | [클라우드데이터베이스기초] 12-2_개념적모델링(26).pptx | 1VBrZI-xw8Nk5BPrE5m9cQudmQDjx7dfB |
| 12-2 Colab | CD12-2_Colab_개념모델_RDS(26).ipynb | 1bUdKHLpCey3gCNt-3Qyx-8SCy9QCZfTY |
| 12-3 교안 | [클라우드데이터베이스] 12-3_논리적물리적모델링(26).pptx | 15z0sVLvy--Je1DqqJD9ZxK24g03mDOaJ |
| 12-3 Colab | CD12-3_Colab_논리물리모델_RDS(26).ipynb | 16zKCRFtxxvxd3m9DJeg2F73dIiQWhCVN |
| 12-3 원본 | [클라우드데이터베이스] 12-3_논리적물리적모델링.pptx | 18OCGd8-ZLmTlUzHJKIXYw_dlUFSt1C5y |
| 11-3 Colab | CD11-3_Colab_설계실습.ipynb | 1mJEtXxBEUK9THq9pVF607BVqO_vDO5Qg |
- 주의: ID 14CJxBnMIlYSo1l6hwC7Z796F7-dVmvdr 도 이름이 CD10-1_PostgreSQL(26).pptx (예전 원본 내용) → 작업 대상 아님

## 다음 할 일
1. 강의자 10-2 검토 반영 (요청된 페이지만, 같은 파일에)
2. 강의자 10-3 검토 반영. 10-2·10-3 Colab 실행 후 '예상 결과' 패널을 실측값으로 교체

## 확인 필요
- 10-3 AWS EBS RAID 문서(RAID 5·6 비권장 문구) 원문 확인
- 10-1 OpenAI 사례 출처(PGConf.dev 2025), 10-2 GitLab 문서(Adding database indexes) 원문 문구 확인
- RDS에 dvdrental 미설치 → `CD10_RDS_DB생성(26).ipynb` 3번 셀로 복원 가능 (실행 검증 전)
- 10-2 17번(EXPLAIN) 원본 본문이 표 위쪽과 살짝 겹침 (원본부터 있던 배치)

## 참고
- 초안 생성: `cd10-2/scripts/build.py <원본.pptx> <출력.pptx>` (원본은 드라이브 `[클라우드데이터베이스기초] 10-2_…pptx`)
- 약어 주석 규칙·코드: AGENTS.md 규칙 8, `cd10-1/scripts/footnotes.py`
- 강의자 Q&A: `docs/CD10-1_스터디노트.md`
