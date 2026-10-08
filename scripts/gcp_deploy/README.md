# 단계별 실행기 (코랩 없이 GCP 직접 배포)

코랩 노트북 `notebooks/research/BSM_AI_Research_RUN_v1.ipynb` 와 **같은 14단계**를
gcloud CLI 없이 Google REST API 로 수행합니다. 브라우저 OAuth 를 쓰지 않으므로
코랩의 `401` 오류가 발생하지 않습니다.

```
python3 run.py --list          # 단계 목록
python3 run.py --step 1        # 1단계만
python3 run.py --from 3 --to 7 # 구간
python3 run.py --all           # 1~13단계 (14단계는 과금되므로 제외)
```

각 단계는 **반복 실행해도 안전**합니다(이미 있으면 건너뛰고, 설정만 맞춥니다).
실패하면 그 단계에서 멈추고 재실행 명령을 알려줍니다. 단계 간 상태는
`/tmp/bsm_build/state.json` 에 남습니다.

## 등록해야 하는 환경 시크릿

세션 제목줄의 환경 메뉴 → **Edit** → 시크릿(또는 환경변수)에 등록합니다.
**값을 채팅창에 붙여넣지 마세요.** 등록 후에는 **새 세션**이 값을 읽습니다.

| 이름 | 필수 | 용도 |
|---|---|---|
| `GCP_SA_KEY` | 필수 | 배포용 서비스 계정 키 **JSON 본문 전체** |
| `GEMINI_API_KEY` | 필수 | 6단계에서 Secret Manager 에 저장, 14단계 측정에 사용 |
| `INPUT_USD_PER_MILLION` | 12단계 전 필수 | 입력 100만 토큰 단가 (예: `0.30`) |
| `OUTPUT_USD_PER_MILLION` | 12단계 전 필수 | 출력 100만 토큰 단가 (예: `2.50`) |
| `KRW_PER_USD` | 12단계 전 필수 | 환율 (예: `1380`) |
| `GROUNDING_MAX_MICRO_KRW` | 12단계 전 필수 | 검색 1회 최대 비용(마이크로원). 60원 = `60000000` |
| `GEMINI_MODEL` | 선택 | 기본 `gemini-3.8-flash`. 2.5 계열은 2026-10-16 종료 |
| `PURCHASE_URL` | 선택 | 카페24 상품 페이지 |
| `TRIAL_POOL_KRW` | 선택 | 무료 체험 전체 예산. 기본 50000 |
| `CLOUDBUILD_SA` | 선택 | 빌드가 서비스 계정 오류로 막힐 때 쓸 빌드 전용 계정 이메일 |

## 배포용 서비스 계정 만들기

콘솔 → IAM 및 관리자 → 서비스 계정 → **만들기**. 이름 `claude-deployer`.
가장 간단한 길은 `roles/owner` 지만, 아래 13개로 좁히는 편이 안전합니다.

```
roles/browser                          1단계 프로젝트 조회
roles/serviceusage.serviceUsageAdmin   3단계 API 활성화
roles/datastore.owner                  4단계 Firestore 생성
roles/cloudtasks.admin                 4단계 큐
roles/iam.serviceAccountAdmin          5단계 서비스 계정 생성
roles/resourcemanager.projectIamAdmin  5단계 프로젝트 IAM
roles/secretmanager.admin              6단계 시크릿
roles/firebase.developAdmin            7단계 웹 앱 구성
roles/storage.admin                    12단계 빌드 소스 버킷
roles/artifactregistry.admin           12단계 이미지 저장소
roles/cloudbuild.builds.editor         12단계 컨테이너 빌드
roles/run.admin                        12단계 Cloud Run
roles/iam.serviceAccountUser           12단계 런타임 계정으로 배포
```

키 추가 → JSON → 내려받은 파일 **내용 전체**를 `GCP_SA_KEY` 에 넣습니다.

**작업이 끝나면 이 키와 계정을 삭제하세요.** 프로젝트를 바꿀 수 있는 권한입니다.
콘솔 → 서비스 계정 → `claude-deployer` → 키 삭제 → 계정 삭제.

## 단계별로 하는 일

| 단계 | 내용 | 비용 발생 |
|---|---|---|
| 1 | 인증 주체와 프로젝트 접근 확인 | 없음 |
| 2 | 설정·단가·앱 소스 점검 | 없음 |
| 3 | 필요한 API 13개 활성화 | 없음 |
| 4 | Firestore Native 생성, 작업 큐(동시 5건·3회 시도) | 거의 없음 |
| 5 | 런타임/호출 서비스 계정과 IAM | 없음 |
| 6 | `GEMINI_API_KEY` 를 Secret Manager 에 저장 | 거의 없음 |
| 7 | Firebase 웹 앱 구성 조회 | 없음 |
| 8 | 빌드 사본을 `/tmp/bsm_build/app` 에 전개 | 없음 |
| 9 | `quote()` 의 `gemini-2.5-flash` 하드코딩 해제 패치 | 없음 |
| 10 | 단위 테스트 12건 | 없음 |
| 11 | 무료 체험 예산 시드 | 없음 |
| 12 | 컨테이너 빌드 + Cloud Run 배포 + 권한 | 빌드·호스팅 |
| 13 | `/health`·`/`·`/api/config`·무인증 차단 5건 검증 | 거의 없음 |
| 14 | **실제 모델 호출로 원가 측정** | **모델 호출 과금** |

## 사람이 직접 해야 하는 두 가지

API 로 대신할 수 없습니다. 안 하면 배포는 되지만 로그인이 전부 실패합니다.

1. Firebase 콘솔 → Authentication → 시작하기 → **Google 공급자 사용 설정**
2. Authentication → 설정 → **승인된 도메인**에 12단계가 출력한 Cloud Run 도메인 추가

## 알아둘 점

- 배포 소스는 `services/research-api/` 입니다. 출처는 그 안의 `PROVENANCE.md` 를 보세요.
  원문은 고치지 않고, 9단계가 **빌드 사본에만** 패치를 적용합니다.
- 13단계는 공개 경로만 검증합니다. 로그인 이후 경로(`/api/research`)는 실제
  구글 로그인 토큰이 필요하므로 브라우저에서 확인해야 합니다.
- 14단계는 상한 없이(`cap`) 측정하므로 호출 비용이 실제로 발생합니다.
  기본 3회 + 심층 2회이며 `N_BASIC`, `N_DEEP` 로 조절합니다.
- 50% 원가 예산은 **서버 내부 운영 정책**입니다. 고객 상품 설명이나 API 응답에
  노출하지 않습니다. 고객에게는 리서치 크레딧과 유형별 차감량으로 안내합니다.
