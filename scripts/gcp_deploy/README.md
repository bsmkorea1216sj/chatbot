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

## 인증: 키 파일을 만들지 않는 방법(권장)

서비스 계정 키를 내려받지 않고 **단기 액세스 토큰**으로 인증합니다. 토큰은 약
**1시간** 뒤 자동으로 죽으므로, 유출되어도 피해 범위가 키 파일보다 훨씬 작습니다.
별도 서비스 계정이나 역할 부여도 필요 없습니다 — 발급한 사람의 권한을 그대로 씁니다.

Google Cloud Shell(브라우저)에서 한 줄:

```
gcloud auth print-access-token
```

출력된 `ya29.` 로 시작하는 값을 환경 시크릿 **`GCP_ACCESS_TOKEN`** 에 넣습니다.
만료되면 같은 명령으로 다시 발급해 갱신하고, **멈춘 단계부터** 다시 실행하면 됩니다.
만료 시 실행기가 알려줍니다.

> 토큰이든 키든 **채팅창에 붙여넣지 마세요.** 환경 시크릿에만 넣습니다.

### 등록해야 하는 환경 시크릿

세션 제목줄의 환경 메뉴 → **Edit** → 시크릿. 등록 후에는 **새 세션**이 값을 읽습니다.

| 이름 | 필수 | 용도 |
|---|---|---|
| `GCP_ACCESS_TOKEN` | 필수 | 단기 액세스 토큰 (키 파일 불필요) |
| `GEMINI_API_KEY` | 필수 | 6단계에서 Secret Manager 에 저장, 14단계 측정에 사용 |
| `INPUT_USD_PER_MILLION` | 12단계 전 필수 | 입력 100만 토큰 단가 (예: `0.30`) |
| `OUTPUT_USD_PER_MILLION` | 12단계 전 필수 | 출력 100만 토큰 단가 (예: `2.50`) |
| `KRW_PER_USD` | 12단계 전 필수 | 환율 (예: `1380`) |
| `GROUNDING_MAX_MICRO_KRW` | 12단계 전 필수 | 검색 1회 최대 비용(마이크로원). 60원 = `60000000` |
| `GEMINI_MODEL` | 선택 | 기본 `gemini-3.8-flash`. 2.5 계열은 2026-10-16 종료 |
| `PURCHASE_URL` | 선택 | 카페24 상품 페이지 |
| `TRIAL_POOL_KRW` | 선택 | 무료 체험 전체 예산. 기본 50000 |
| `CLOUDBUILD_SA` | 선택 | 빌드가 서비스 계정 오류로 막힐 때 쓸 빌드 전용 계정 이메일 |

토큰은 1시간만 살아 있으므로 **등록 직후 1~13 + 15단계를 한 번에** 돌리는 편이 좋습니다.
배포까지 보통 5~10분이면 끝납니다.

## 대안: 서비스 계정 키 (권장하지 않음)

토큰 방식을 쓸 수 없을 때만 씁니다. 키 JSON 본문을 `GCP_SA_KEY` 에 넣고, 계정에
아래 역할을 줍니다. **작업이 끝나면 키와 계정을 반드시 삭제하세요.**

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
roles/firebasehosting.admin            15단계 기본 도메인 릴리스
```

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
| 15 | 기본 도메인 `{프로젝트}.web.app` 을 Cloud Run 으로 연결 | 거의 없음 |

## 사람이 직접 해야 하는 두 가지

API 로 대신할 수 없습니다. 안 하면 배포는 되지만 로그인이 전부 실패합니다.

1. Firebase 콘솔 → Authentication → 시작하기 → **Google 공급자 사용 설정**
2. Authentication → 설정 → **승인된 도메인**에 15단계가 출력한 도메인 3개 모두 추가
   (`{프로젝트}.web.app`, `{프로젝트}.firebaseapp.com`, Cloud Run 도메인)

## 알아둘 점

- 배포 소스는 `services/research-api/` 입니다. 출처는 그 안의 `PROVENANCE.md` 를 보세요.
  원문은 고치지 않고, 9단계가 **빌드 사본에만** 패치를 적용합니다.
- 13단계는 공개 경로만 검증합니다. 로그인 이후 경로(`/api/research`)는 실제
  구글 로그인 토큰이 필요하므로 브라우저에서 확인해야 합니다.
- 14단계는 상한 없이(`cap`) 측정하므로 호출 비용이 실제로 발생합니다.
  기본 3회 + 심층 2회이며 `N_BASIC`, `N_DEEP` 로 조절합니다.
- 50% 원가 예산은 **서버 내부 운영 정책**입니다. 고객 상품 설명이나 API 응답에
  노출하지 않습니다. 고객에게는 리서치 크레딧과 유형별 차감량으로 안내합니다.

## 발급되는 URL

12단계와 15단계가 각각 주소를 만듭니다. 둘 다 **기본 도메인**이고, 도메인을
따로 사지 않아도 바로 쓸 수 있습니다.

| 단계 | 주소 | 성격 |
|---|---|---|
| 12 | `https://bsm-research-<프로젝트번호>.asia-northeast3.run.app` | Cloud Run 원본 |
| 15 | `https://aichat-507914.web.app` | 대표 주소로 쓰기 좋음 |
| 15 | `https://aichat-507914.firebaseapp.com` | 위와 같은 사이트의 예비 주소 |

15단계는 Hosting 의 모든 경로(`**`)를 Cloud Run 서비스로 넘깁니다. 정적 파일은
올리지 않으므로 화면과 API 모두 Cloud Run 이 그대로 처리합니다.
Hosting → Cloud Run 연결은 `asia-northeast3` 에서 지원되지만, 지연시간만 보면
Hosting 과 가까운 리전이 더 빠릅니다. 국내 사용자 대상이므로 서울을 유지했습니다.
