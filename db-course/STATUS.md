# STATUS (작업 시작 시 이 파일만 먼저 읽기)

**마지막 갱신:** 2026-11-11 · claude
**드라이브 폴더:** https://drive.google.com/drive/folders/1WL8_UI8wvOyqXormXoXFx4L9ykGRkxdS

## 현재 상태
- 10-1 기준본: `CD10-1_PostgreSQL26.pptx` (48장, 강의자 편집 중). 약어 주석 전체 반영 완료
  - Colab `CD10-1_Colab_Lab(26).ipynb`: 실제 RDS 실행 확인됨(postgresql-lab-01:5433, DB=postgres), 결과 인사이트 셀 포함
- 10-2 초안: `CD10-2_Index_Join(26).pptx` (36장, 11-04 02:39) — 원본 31장 + GitLab 사례·조인 방식 3가지·Colab 실습 3장, 노트 전체, 약어 주석, 원본 오류 5곳 수정
  - Colab `CD10-2_Colab_Lab(26).ipynb`: 각 셀 자동 접속, 트리·비교 표 출력 — 실행 검증 전. 교안 29~35 결과 패널은 '예상 결과' → 실행 후 실측값으로 교체 필요
- 11-3 초안: `[클라우드데이터베이스기초] 11-3_데이터베이스 설계실습(26).pptx` (22장, 11-2 정규화 패턴, 미션 정답 19·20쪽) + `CD11-3_Colab_설계실습.ipynb` (SQLite, 확인 도우미 코드 숨김, 미션1~5·과제(교안 순서: 상담=미션4 14쪽, 결제=미션5 17쪽) input() 입력→즉시 ✅/❌·3회 재입력, 도우미 미실행 시 자동 불러옴, 🔎예측 퀴즈 4개, 정답은 교안 버튼 아래·19·20쪽). 11-1·11-2는 Codex/강의자 작업본(이 저장소에 기록 없음)
- 11-1 보강본 `…11-1_데이터베이스 설계 개요(26)_보강.pptx` (48장): Claude가 5·6·9·12·25·29·30·31쪽 보강 → 상세는 `db-course/HANDOFF.md` (Codex 인수인계)
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
| 11-2 패턴(강의자) | [클라우드데이터베이스기초] 11-2_정규화.pptx | 1kpLd9222ZqByf4NxcInQsgOhGEw08dgQ |
| 11-3 교안 | [클라우드데이터베이스기초] 11-3_데이터베이스 설계실습(26).pptx | 16mLq0QLxmGUH1mR2QWdsGam0tufQbYum |
| 11-1 교안(보강) | [클라우드데이터베이스기초] 11-1_데이터베이스 설계 개요(26)_보강.pptx | 1zYS43RH1IpcrfJiDsCbz95kl_Wf2du2F |
| 11-1 Colab | CD11-1_Colab_Lab(26).ipynb | 1fQ--R38hR6exXmFtyl8wvDKpZNn9DSP1 |
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
