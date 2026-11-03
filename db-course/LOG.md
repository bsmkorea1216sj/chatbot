# LOG (최신이 위, 한 줄씩)

- 2026-11-04 [claude] 기준본 23번(Uber)에 약어 주석(MVCC·WAL·ACID) 추가. 규칙 추가: 약어는 해당 페이지 하단 주석
- 2026-11-04 [claude] 기준본 CD10-1_PostgreSQL26.pptx 21번(Utility 주요 프로세스)만 수정: 역할별 4묶음 보강, 그림 Backend→Background Writer 오타, 노트에 UPDATE 흐름 추가
- 2026-11-04 [claude] Colab 실행 결과 인사이트 셀 4개 추가(실습1·2·3·심화 제목 아래). 실측: PID 23416/23421, max_connections 81, shared_buffers 185MB, Parallel Seq Scan 45ms, work_mem 4MB도 external merge
- 2026-11-04 [claude] Colab 실습3·심화: payment 없으면 cd10_lab_payment(20만 행) 자동 생성 (RDS에 dvdrental 미설치, 드라이브 dvdrental/dvdrental.tar 있음)
- 2026-11-04 [claude] Colab 실습1 셀: 엔드포인트·포트 자동 조회(기존 postgresql-lab-01:5433), DB_PASSWORD 보안비밀 우선, dvdrental 없으면 postgres
- 2026-11-04 [claude] rclone 연결, CD10-1_Colab_Lab(26).ipynb 같은 파일에 직접 수정(안내문·pip 셀·실습1 셀)
- 2026-11-04 [claude] 규칙 변경: 같은 파일에 계속 업데이트(사본 금지, 삭제 금지). Colab 접속을 AWS_ACCESS_KEY/AWS_SECRET_KEY 방식으로 변경(colab_nb.py), 교체 셀 코드 강의자 전달
- 2026-11-03 [claude] 역할 분리: 파일은 Google Drive 한 폴더, GitHub는 규칙·상태·원고만. 버전은 이름 끝 날짜_시간, 덮어쓰기 금지

- 2026-11-03 [claude] 공동 작업 구조 세팅(AGENTS.md, STATUS.md, 폴더), 10-1 스크립트를 저장소 기준 build.py로 통합
- 2026-11-03 [claude] RDS Proxy 흐름도 1장 → cd10-1/output/CD10-1_RDS_Proxy_흐름도(26).pptx
- 2026-11-03 [claude] 10-1 노트 45장 재작성, 본문-노트 일치 수정(학습목표, 4번 사례, System Memory, Parser 오류 등)
- 2026-11-03 [claude] 10-1 보강: 빅테크 사례 4장 + Colab 실습 5장 추가 → CD10-1_PostgreSQL(26).pptx, Colab 노트북
