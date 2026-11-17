# Colab 보안 비밀로 AWS RDS 실습 만들기 (12-1 기준 형식)

> 대상: 12장 이후 AWS RDS 실습 노트북·교안을 만들 때 Claude·Codex가 따르는 형식
> 기준 구현: `db-course/cd12-1/scripts/split_notebook.py` · `deck_cell_links.py` · `deck_erd_runcheck.py`
> 결과: Colab `CD12-1_Colab_쇼핑몰DB_웹앱(26).ipynb` (ID `1URPntHhY0jY96psj9cK0Khrzq3gLb8KX`), 교안 `[클라우드데이터베이스기초] 12-1데이터베이스 설계.Part1(26).pptx` (ID `1Gu6kZNfazuj6jpYexa_Jd7aVNd0XVwmu`)

---

## 1. 원칙

1. **PostgreSQL이 없는 초기 상태에서 시작**한다. 1번 셀이 AWS에 실습 RDS를 만들고(없을 때만, 중지돼 있으면 시작), 마지막 셀은 **STOP(중지)** 해 다음 차시가 같은 RDS·`shop` 스키마를 이어서 쓴다. **최종 삭제는 장의 마지막 차시(12-3) 마지막 셀**에서 한다(이어하기 구현: `cd12-1/scripts/continue_chain.py`).
2. **접근은 Colab 보안 비밀만**: 학생은 열쇠 아이콘에 값을 넣고 각 항목의 **노트북 액세스**를 켠다. 키·비밀번호는 코드·출력에 절대 나오지 않는다.

| 보안 비밀 | 값 |
|---|---|
| `AWS_ACCESS_KEY`, `AWS_SECRET_KEY` | 학생 본인 AWS 키 |
| `DB_PASSWORD` | 새 RDS 관리자 비밀번호(8자 이상, 직접 정함) |
| `AWS_SESSION_TOKEN` | 임시 자격 증명일 때만 |
| `AWS_REGION` | 선택(기본 ap-northeast-2) |
| `DB_HOST`·`DB_PORT`·`DB_NAME`·`DB_USER` | 강사 공용 RDS를 쓸 때만 (그러면 생성·삭제 건너뜀) |

3. **셀 = 교안 실습 단계**. 교안의 Colab 버튼은 해당 셀 마크다운의 `metadata.id`로 이동한다(`#scrollTo=<id>`).
4. **앞 셀을 안 돌렸으면 NameError 대신 안내로 멈춘다**: `if "transaction" not in globals(): raise SystemExit("⚠️ 먼저 1. DB 생성 셀을 실행하세요.")`
5. 이미 검증된 연결 방식은 유지: AWS 공식 CA 번들 자동 다운로드, `sslmode=verify-full`, 런타임 전용 스키마.
6. IAM DB 인증(rds_iam, rds-db:connect)은 학생 권한 설정이 많아 **기본 형식에서 제외**(접근 단순화). 필요하면 별도 심화.

---

## 2. 셀 구성 (12-1)

| 셀 id | 제목 | 하는 일 | 출력 |
|---|---|---|---|
| `shop-db-create` | 1. DB 생성 | STS 인증 → RDS `cd12-shop-lab` 없으면 생성(db.t4g.micro, 공개, 암호화, 백업 0, 5~15분 진행 표시) → 실습 보안 그룹에 **현재 Colab IP/32만** 허용(재실행 때 갱신) → CA 다운로드 → TLS 접속 | ①②③④ |
| `shop-tables` | 2. 표 만들기 | 런타임 전용 스키마 + 표 생성, 관계(FK) 목록 출력 | ⑤ |
| `shop-verify` | 3. 자동 검증 | 별도 스키마에서 시나리오 자동 검증 후 삭제 | ⑥ 통과 |
| `shop-webapp` | 4. 웹앱 실행 | `output.serve_kernel_port_as_iframe` | ⑦ |
| `shop-submit` | 제출 | 캡처 안내 | |
| `shop-delete` | 5. 삭제 | `DELETE` 입력 시 RDS 삭제. **런타임 재시작 후 단독 실행 가능**(보안 비밀로 다시 인증) | |

출력 번호 ①~⑦은 교안·노트북 안내 표에서 그대로 쓴다(예: ④ 연결 확인 = RDS TLS 접속, ⑥ 통과 = 검증 성공).

---

## 3. 오류 안내 (원인별 문구)

| 상황 | 문구 요지 |
|---|---|
| `userdata.NotebookAccessError` | 열쇠 아이콘 → 해당 항목 노트북 액세스 켜기 → 탭 새로고침 → 1번 셀 |
| `userdata.TimeoutException` | 접근 허용 창 시간 초과 → 새로고침 후 다시 실행해 '허용' |
| STS `ExpiredToken`/`InvalidClientTokenId`/`SignatureDoesNotMatch` | 임시 키 만료 / 세션 토큰 누락 / 키 짝 불일치 |
| psycopg2 timeout·refused | 런타임이 바뀌어 IP가 달라짐 → 1번 셀 재실행(보안 그룹 갱신) |
| `password authentication failed` | DB_PASSWORD가 생성 때 값과 다름 → 되돌리거나 5번으로 삭제 후 재생성 |
| certificate/ssl | 별칭이 아닌 RDS 엔드포인트, CA 다시 받기 |

---

## 4. 교안 연결 규칙

- 실습과 관련된 모든 쪽 오른쪽/왼쪽 아래에 `Colab · N. 셀 이름` 버튼(둥근 사각형, 글자 링크와 도형 클릭 링크 둘 다). 링크 주소의 관계(rId)를 공유하므로 **관계 주소만 바꾼다**. 다른 쪽에서 복제한 버튼은 새 관계를 만든다.
- 'Colab 실습' 개요 쪽: 셀 표(1~5)와 노트북 전체 주소, 버튼 2개(1. DB 생성 / 핵심 셀).
- '실습 끝내기' 쪽: 5. 삭제 버튼 + "RDS는 켜져 있는 동안 요금" 문구.
- 노트 형식 【슬라이드 핵심】【강의 설명】【연결】【출처】, 약어는 그 쪽 하단 `※` 주석.

---

## 5. 시험 방법 (업로드 전)

- 로컬 PostgreSQL 16에 **TLS(자체 서명 인증서)** 를 켜고, `google.colab.userdata/output`, `boto3`, `botocore.exceptions` 를 스텁으로 바꿔 노트북 코드 셀을 순서대로 `exec`.
- CA 다운로드는 자체 서명 인증서로 대체 → 실제 `verify-full` 경로로 접속 확인.
- 시나리오: ① 처음(RDS 없음 → 생성) ② 기존(중지·보안 그룹 미연결) ③ 셀 건너뛰기(안내로 멈춤) ④ 런타임 재시작 후 5번 단독 삭제. 실제 AWS 실행은 강사가 1회 확인.

---

## 6. 수업자료로 공유할 때

1. Colab은 **보기 전용으로 공유**하고, 학생은 **파일 → Drive에 사본 저장** 후 실행(편집 권한이면 학생 실행 결과가 원본에 자동 저장됨).
2. 보안 비밀은 노트북에 포함되지 않고 사용자별이라 공유해도 키가 노출되지 않는다.
3. 학생마다 **본인 AWS 계정 키**(RDS 생성·삭제, EC2 보안 그룹 권한). 강사 키 배포 금지.
4. **요금**: 수업 끝에 5. 삭제 셀 실행 안내(교안 '실습 끝내기' 쪽에도 명시).
5. 업로드한 노트북은 출력이 비어 있어야 한다(개인 실행 결과·엔드포인트가 남지 않게).
