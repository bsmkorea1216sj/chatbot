# STATUS (작업 시작 시 이 파일만 먼저 읽기)

**마지막 갱신:** 2026-11-03 · claude

## 현재 상태
- 10-1 PostgreSQL 아키텍처: **완료** → `cd10-1/output/CD10-1_PostgreSQL(26).pptx` (45장, 노트 전체 작성)
- 10-1 부속: `CD10-1_Colab_Lab(26).ipynb`, `CD10-1_RDS_Proxy_흐름도(26).pptx`(1장, 교안 미삽입)
- 10-2, 10-3: 원본만 `source/`에 있음, 미착수

## 다음 할 일 (위에서부터)
1. **10-2 Index·Join 보강** → `cd10-2/output/CD10-2_Index_Join(26).pptx`
   - 방법: 10-1과 같음 (`cd10-1/scripts/build.py` 구조 복사 → 원고만 새로 작성)
   - 사례 후보: 인덱스 누락으로 인한 Seq Scan 장애, 조인 방식 선택(Nested Loop/Hash/Merge)
   - Colab 후보: CREATE INDEX 전후 EXPLAIN 비교, B-tree/GIN/BRIN
2. **10-3 RAID 보강** → `cd10-3/output/CD10-3_RAID(26).pptx`
   - 사례 후보: AWS EBS 볼륨과 RAID 0/1, RDS Multi-AZ와 RAID 1 비교
3. (선택) 흐름도에 "앱(EC2/Lambda) → Proxy → RDS", "RDS Proxy는 VPC 내부 전용" 표기 추가

## 확인 필요
- 10-1 슬라이드 13 OpenAI 사례 출처(PGConf.dev 2025 발표) 원문 확인
- Colab 코드는 실제 RDS에서 아직 실행 검증 전

## 참고 파일
- 10-1 원고: `cd10-1/scripts/cd101_new.py`(추가 슬라이드), `notes_v2.py`(노트), `fix_body.py`(본문 수정)
- 강의자와의 Q&A 정리: `docs/CD10-1_스터디노트.md`
