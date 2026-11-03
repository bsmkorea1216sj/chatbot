# STATUS (작업 시작 시 이 파일만 먼저 읽기)

**마지막 갱신:** 2026-11-03 · claude
**드라이브 폴더:** https://drive.google.com/drive/folders/1WL8_UI8wvOyqXormXoXFx4L9ykGRkxdS

## 현재 상태
- 10-1 기준본: 드라이브 `CD10-1_PostgreSQL26.pptx` (48장, 강의자 편집 중 · Google 슬라이드로 편집). AI 수정은 이 파일에 요청된 페이지만
  - 부속: `CD10-1_Colab_Lab(26).ipynb`, `CD10-1_RDS_Proxy_흐름도(26).pptx`(1장)
- 드라이브 현재 파일: `CD10-1_PostgreSQL26.pptx`(강의자 수정 중, 11-03 16:40 저장),
  `CD10-1_PostgreSQL(26).pptx`·`CD10-2_Index_Join(26).pptx`·`CD10-3_RAID(26).pptx`(이름은 (26)이지만 내용은 원본)
- Colab `CD10-1_Colab_Lab(26).ipynb`: AWS 키 보안비밀 방식으로 같은 파일에 반영 완료(11-04), 실제 실행 검증 전
- 10-2, 10-3: 미착수

## 다음 할 일
1. 강의자에게 10-1 기준본 파일명 확인 → 이후 요청은 그 파일에서 작업
2. 10-2 Index·Join 보강 (사례: 인덱스 누락 Seq Scan 장애, 조인 방식 선택 / Colab: CREATE INDEX 전후 EXPLAIN)
3. 10-3 RAID 보강 (사례: AWS EBS와 RAID 0/1, RDS Multi-AZ)

## 확인 필요
- 기준본 43·44번 Colab 슬라이드 코드가 예전 PG_HOST 방식 → 노트북(AWS 키 방식)과 불일치, 강의자 확인 후 수정
- 10-1 OpenAI 사례 출처(PGConf.dev 2025) 원문 확인
- Colab 코드 실제 RDS 실행 검증 전

## 참고
- 10-1 초안 생성 원고: `cd10-1/scripts/` (build.py는 원본에서 초안을 만드는 기록용, 이후 수정은 드라이브 기준본에서)
- 강의자 Q&A: `docs/CD10-1_스터디노트.md`
