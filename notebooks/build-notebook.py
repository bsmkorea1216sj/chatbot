import json, io

C = []
def md(s): C.append(("markdown", s.strip("\n")))
def code(s): C.append(("code", s.strip("\n")))

md(r"""
# BSM AI FACTORY — GCP 구축 노트북

BSM AI 챗봇 임대 서비스를 **Google Cloud 위에 실제로 올리는** 운영 노트북입니다.
이 노트북 하나로 지식 적재 → 검색 → 답변 → API 배포 → 홈페이지 배포 → 고객 개통까지 수행합니다.

```
고객 → www.bsm-ai.com (Firebase Hosting)
              │
              ├── 회사소개 / 가격 / FAQ          : 정적 페이지
              ├── AI 데모 위젯 ──────────────┐
              └── 구매 → Cafe24 (결제·환불)  │
                                             ▼
                                   api.bsm-ai.com (Cloud Run · FastAPI)
                                             │
                                     Tenant Resolver (Firestore)
                                             │
                                     Hybrid RAG Engine
                                   ┌─────────┴─────────┐
                            Vector Search        Keyword Search
                              (BigQuery)           (BigQuery)
                                   └─────────┬─────────┘
                                            RRF
                                             │
                                          Gemini
                                             │
                                  근거 인용 · 가드레일
                                   ┌─────────┴─────────┐
                                AI 답변            상담 연결
                                                0507-1419-0222
                                                netk@kakao.com
```

| 영역 | 서비스 | 역할 |
|---|---|---|
| 공식 홈페이지 | Firebase Hosting | 브랜드 · 가격 · 데모 · 유입 |
| 챗봇 API | Cloud Run | 질문 처리 · RAG · 고객 분리 |
| 지식/검색 | BigQuery | 문서 · 청크 · 벡터/키워드 검색 |
| 설정/상태 | Firestore | 테넌트 · 회사 설정 |
| 생성 AI | Vertex AI (Gemini) | 답변 생성 · 임베딩 |
| 결제 | Cafe24 | 주문 · 결제 · 환불 |
| 운영 | 이 노트북 | 고객 생성 · 색인 · 평가 · 배포 |

**실행 순서** — 1~5는 최초 1회, 6~9는 지식이 바뀔 때, 10~13은 배포할 때, 14~16은 상시 운영.
""")

md(r"""
## 실행 전 준비

1. **GCP 프로젝트**와 **결제 계정 연결**이 되어 있어야 합니다.
2. 이 노트북을 실행하는 계정에 다음 역할이 필요합니다 — `BigQuery 관리자`, `Cloud Run 관리자`, `Datastore 사용자`, `Vertex AI 사용자`, `서비스 계정 사용자`.
3. **비용이 발생합니다.** 15단계의 예산 알림을 먼저 설정하시길 권합니다. 임베딩·생성 호출과 BigQuery 스캔이 과금 대상입니다.
4. 도메인(`bsm-ai.com`)은 Firebase Hosting 연결 시 필요하며, 없어도 `*.web.app` 기본 도메인으로 먼저 오픈할 수 있습니다.
""")

md("## 1. 라이브러리 설치")

code(r"""
# 최초 1회. 설치 후 런타임 재시작이 필요할 수 있습니다.
!pip -q install --upgrade google-genai google-cloud-bigquery google-cloud-firestore \
                          pandas pypdf beautifulsoup4 requests
print("설치 완료 — 런타임 재시작 후 2단계부터 실행하세요.")
""")

md("## 2. 인증과 기본 설정")

code(r"""
import os, re, json, uuid, time, hashlib, datetime as dt
from google.colab import auth

# 구글 계정 인증. 팝업이 뜨면 GCP 프로젝트 소유 계정으로 로그인하세요.
# 이 한 번으로 클라이언트 라이브러리(ADC)와 gcloud CLI 양쪽이 인증됩니다.
auth.authenticate_user()
print("구글 인증 완료")

# ─── 여기만 본인 환경에 맞게 수정하세요 ──────────────────────────────
PROJECT_ID   = "aichat-507914"              # GCP 프로젝트 ID (프로젝트 이름: AICHat)
LOCATION     = "asia-northeast3"            # 서울 리전 (Cloud Run / Firestore)
VERTEX_LOC   = "global"                     # Vertex AI 위치. 리전 제한이 있으면 "us-central1"
BQ_LOCATION  = "asia-northeast3"            # BigQuery 데이터셋 위치
DATASET      = "bsm_ai"
SERVICE_NAME = "bsm-api"                    # Cloud Run 서비스 이름
SITE_DOMAIN  = "https://www.bsm-ai.com"     # 홈페이지 주소 (없으면 *.web.app 주소)
CAFE24_URL   = "https://bsmshop.cafe24.com" # 결제 스토어
BRAND        = "AI노마드챗봇"                # 서비스 브랜드명

# Firebase Authentication (이메일 인증 회원가입). 콘솔 > 프로젝트 설정 > 웹 앱에서 확인합니다.
FIREBASE_API_KEY     = ""                                    # ← 웹 API 키 붙여넣기
FIREBASE_AUTH_DOMAIN = f"{PROJECT_ID}.firebaseapp.com"
# ──────────────────────────────────────────────────────────────────

# 모델. Gemini 2.5 계열은 2026-10-16 종료 예정이므로 3.x 계열을 사용합니다.
GEN_MODEL   = "gemini-3.8-flash"
EMBED_MODEL = "gemini-embedding-001"
EMBED_DIM   = 768          # 3072/1536/768 중 선택. 낮을수록 저장·검색 비용이 낮습니다.

BSM_TENANT  = "BSM001"     # BSM 자체 홈페이지 챗봇 테넌트

os.environ["GOOGLE_CLOUD_PROJECT"] = PROJECT_ID
!gcloud config set project {PROJECT_ID} -q

DS = f"{PROJECT_ID}.{DATASET}"
print("프로젝트:", PROJECT_ID, "| 데이터셋:", DS, "| 생성모델:", GEN_MODEL)
""")

md("""
## 2-1. 인증과 프로젝트 접근 확인

다음 셀이 모두 통과해야 이후 단계가 진행됩니다. 하나라도 실패하면 아래 안내대로 조치하세요.
""")

code(r"""
ok = True

# (1) 인증 계정 확인
acct = !gcloud auth list --filter=status:ACTIVE --format="value(account)"
acct = [a for a in acct if a.strip()]
if acct:
    print("인증 계정:", acct[0])
else:
    ok = False
    print("인증 계정 없음 — 아래를 실행한 뒤 출력되는 URL에서 인증하세요:")
    print("  !gcloud auth login --no-launch-browser")

# (2) 프로젝트 접근 확인
proj = !gcloud projects describe {PROJECT_ID} --format="value(name,projectId,lifecycleState)" 2>/dev/null
proj = [p for p in proj if p.strip()]
if proj:
    print("프로젝트 확인:", proj[0])
else:
    ok = False
    print(f"프로젝트 {PROJECT_ID}에 접근할 수 없습니다.")
    print("  - 프로젝트 ID 오타를 확인하세요.")
    print("  - 인증 계정에 해당 프로젝트 권한이 있는지 확인하세요.")

# (3) 결제 계정 연결 확인
bill = !gcloud billing projects describe {PROJECT_ID} --format="value(billingEnabled)" 2>/dev/null
bill = [b for b in bill if b.strip()]
if bill and bill[0].strip().lower() == "true":
    print("결제 계정: 연결됨")
else:
    ok = False
    print("결제 계정이 연결되지 않았습니다. Vertex AI와 Cloud Run은 결제 연결이 필요합니다.")
    print("  콘솔 > 결제 > 프로젝트에 결제 계정 연결")

# (4) 클라이언트 라이브러리 인증(ADC) 확인
try:
    import google.auth
    creds, adc_proj = google.auth.default()
    print("ADC 확인:", adc_proj or "(프로젝트 미지정 — 아래에서 지정합니다)")
except Exception as e:
    ok = False
    print("ADC 실패:", e)

# ADC 할당량 프로젝트를 명시해 두면 라이브러리 호출 시 프로젝트 혼선이 없습니다.
os.environ["GOOGLE_CLOUD_QUOTA_PROJECT"] = PROJECT_ID

print()
print("모두 통과" if ok else "실패 항목을 조치한 뒤 이 셀을 다시 실행하세요.")
""")

md("## 3. API 활성화")

code(r"""
# 최초 1회만 실행하면 됩니다. 2~3분 걸립니다.
!gcloud services enable \
  aiplatform.googleapis.com \
  bigquery.googleapis.com \
  firestore.googleapis.com \
  identitytoolkit.googleapis.com \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  -q
print("API 활성화 완료")
""")

md("""
## 4. BigQuery 스키마 생성

7개 테이블을 만듭니다. `chunks.embedding`은 `ARRAY<FLOAT64>`로 두고 BigQuery의 `VECTOR_SEARCH`를 직접 사용합니다.
별도의 벡터 DB나 원격 모델 연결이 필요 없어 그만큼 비용과 설정이 줄어듭니다.
""")

code(r"""
from google.cloud import bigquery

bq = bigquery.Client(project=PROJECT_ID)

# 데이터셋
ds_ref = bigquery.Dataset(DS)
ds_ref.location = BQ_LOCATION
bq.create_dataset(ds_ref, exists_ok=True)

DDL = f'''
CREATE TABLE IF NOT EXISTS `{DS}.tenants` (
  tenant_id STRING NOT NULL, name STRING, plan STRING, status STRING,
  contact_name STRING, phone STRING, email STRING, homepage STRING,
  widget_key STRING, created_at TIMESTAMP, note STRING
);

CREATE TABLE IF NOT EXISTS `{DS}.documents` (
  doc_id STRING NOT NULL, tenant_id STRING NOT NULL, title STRING,
  source_type STRING, source_uri STRING, char_len INT64, created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `{DS}.chunks` (
  chunk_id STRING NOT NULL, tenant_id STRING NOT NULL, doc_id STRING,
  title STRING, content STRING, embedding ARRAY<FLOAT64>,
  char_len INT64, created_at TIMESTAMP
)
PARTITION BY DATE(created_at)
CLUSTER BY tenant_id;

CREATE TABLE IF NOT EXISTS `{DS}.chat_logs` (
  log_id STRING, tenant_id STRING, session_id STRING,
  question STRING, answer STRING, sources ARRAY<STRING>,
  action STRING, grounded BOOL, top_score FLOAT64,
  latency_ms INT64, created_at TIMESTAMP
)
PARTITION BY DATE(created_at)
CLUSTER BY tenant_id;

CREATE TABLE IF NOT EXISTS `{DS}.leads` (
  lead_id STRING, tenant_id STRING, company STRING, contact_name STRING,
  phone STRING, email STRING, homepage STRING, memo STRING,
  source STRING, created_at TIMESTAMP
)
PARTITION BY DATE(created_at);

CREATE TABLE IF NOT EXISTS `{DS}.members` (
  member_id STRING, provider STRING, provider_uid STRING,
  email STRING, name STRING, company STRING, phone STRING,
  created_at TIMESTAMP, last_login_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `{DS}.inquiries` (
  inquiry_id STRING, member_id STRING, tenant_id STRING,
  category STRING, title STRING, body STRING,
  company_name STRING, phone STRING, contact_email STRING,
  channel STRING, status STRING, created_at TIMESTAMP
)
PARTITION BY DATE(created_at);

CREATE TABLE IF NOT EXISTS `{DS}.escalations` (
  esc_id STRING, tenant_id STRING, session_id STRING,
  question STRING, summary STRING, contact_email STRING, memo STRING,
  email_sent BOOL, email_error STRING, status STRING, created_at TIMESTAMP
)
PARTITION BY DATE(created_at);

CREATE TABLE IF NOT EXISTS `{DS}.golden_set` (
  gs_id STRING, tenant_id STRING, question STRING,
  expect_keywords ARRAY<STRING>, note STRING
);
'''

for stmt in [s for s in DDL.split(";") if s.strip()]:
    bq.query(stmt).result()

print("BigQuery 테이블 생성 완료")
for t in bq.list_tables(DS):
    print("  -", t.table_id)
""")

md("""
## 5. Firestore 회사 설정

전화번호·이메일·가격을 **코드나 프롬프트에 하드코딩하지 않고** Firestore에 둡니다.
가격이 바뀌면 이 문서만 고치면 API와 홈페이지가 함께 따라갑니다.
""")

code(r"""
from google.cloud import firestore

fs = firestore.Client(project=PROJECT_ID, database="(default)")

# 요금은 "해결 건수(Resolution)" 기준입니다.
# 해결 = 챗봇이 근거를 갖고 답변을 완료한 대화. 답을 못 해 상담원에게 넘긴 대화는 과금하지 않습니다.
PLANS = {
    "FREE":    {"name": "Free",    "price": 0,      "resolutions": 100,   "pages": 50,
                "note": "위젯에 BSM 배지 표시"},
    "STARTER": {"name": "Starter", "price": 39000,  "resolutions": 500,   "pages": 300,
                "note": "웹 위젯 1채널"},
    "GROWTH":  {"name": "Growth",  "price": 99000,  "resolutions": 2000,  "pages": 1000,
                "note": "카카오톡 채널 연동 · 주간 리포트"},
    "SCALE":   {"name": "Scale",   "price": 249000, "resolutions": 8000,  "pages": 5000,
                "note": "다채널 · API · SSO"},
}

COMPANY = {
    "name": "BSM",
    "phone": "0507-1419-0222",
    "email": "netk@kakao.com",
    "site": SITE_DOMAIN,
    "store": CAFE24_URL,
    "plans": PLANS,
    "overage_per_resolution": 40,     # 포함 건수 초과분 (원)
    "year_discount_months": 2,        # 연납 시 2개월 할인
    "trial_days": 14,
    "onboarding_fee": 300000,
    "onboarding_free_quota": 20,
    "enterprise_from": 12000000,      # 연 기준 시작가
    "franchise_fee": 15000000,
    "franchise_monthly": 300000,
    "partner_share": 40,
    "hours": "평일 09:00-18:00",
    "updated_at": firestore.SERVER_TIMESTAMP,
}
fs.collection("company").document("bsm").set(COMPANY, merge=True)

snap = fs.collection("company").document("bsm").get().to_dict()
print("Firestore 설정 저장 완료\n")
for code_, p in PLANS.items():
    print(f"  {p['name']:<8} {p['price']:>7,}원/월  해결 {p['resolutions']:>5,}건  문서 {p['pages']:>5,}p  {p['note']}")
print(f"\n  초과 해결당 {COMPANY['overage_per_resolution']}원 · 연납 {COMPANY['year_discount_months']}개월 할인")
print(f"  무료 체험 {COMPANY['trial_days']}일 · 분양비 {COMPANY['franchise_fee']:,}원")
""")

md("""
## 5-1. 상담 시나리오 저장

해피톡처럼 버튼으로 시작해 자유 대화로 넘어가는 구조입니다.
시나리오를 코드가 아니라 Firestore에 두면 문구를 바꿀 때 재배포가 필요 없습니다.
""")

code(r"""
FLOW = {
  "home": {
    "text": ("안녕하세요. BSM AI 상담 챗봇입니다.\n"
             "홈페이지와 카카오톡 등 여러 채널의 고객 문의를 AI가 대신 답하도록 만들어 드립니다.\n\n"
             "원하시는 항목을 선택해 주세요."),
    "buttons": [
      {"label": "신규 도입 문의",   "next": "intro"},
      {"label": "가격 · 견적 문의", "next": "price"},
      {"label": "상담 시작하기",    "next": "free", "style": "pri"},
    ],
  },
  "intro": {
    "text": "어떤 것을 만들고 싶으신지 알려주시면 바로 상담해 드립니다.",
    "buttons": [
      {"label": "쇼핑몰 주문·배송 문의를 자동으로 답하게 하고 싶어요", "ask": True},
      {"label": "사내 규정 PDF를 직원이 물어보게 하고 싶어요",         "ask": True},
      {"label": "홈페이지에 24시간 상담 챗봇을 붙이고 싶어요",         "ask": True},
      {"label": "직접 입력할게요", "next": "free", "style": "pri"},
    ],
  },
  "price": {
    "text": ("가격과 견적은 회원 확인 후 안내해 드립니다.\n"
             "카카오 또는 네이버 계정으로 간편하게 시작하실 수 있습니다."),
    "require_login": True,
  },
  "free": {
    "text": ("만들고 싶으신 내용을 편하게 적어주세요.\n"
             "제가 아는 범위는 바로 답해 드리고, 어려운 내용은 담당자에게 전달해 회신해 드립니다."),
    "free_input": True,
  },
}

fs.collection("flows").document("main").set({
    "nodes": FLOW, "updated_at": firestore.SERVER_TIMESTAMP})

print("상담 시나리오 저장 완료")
for k, v in FLOW.items():
    n = len(v.get("buttons", []))
    print(f"  {k:<8} 버튼 {n}개  {v['text'][:34]}...")
""")

md("""
## 5-1-1. Firebase Authentication 준비 (이메일 인증 가입)

카카오·네이버 계정이 없는 고객도 가입할 수 있도록 **이메일 인증 회원가입**을 함께 제공합니다.
Google Cloud Identity Platform과 Firebase Authentication은 같은 백엔드(Identity Toolkit)를 씁니다.

콘솔에서 두 가지만 켜주세요.

1. [Firebase 콘솔](https://console.firebase.google.com) → 프로젝트 선택 → **Authentication → 시작하기 → 이메일/비밀번호 사용 설정**
2. **Authentication → 설정 → 승인된 도메인**에 홈페이지 도메인 추가
   (`<프로젝트ID>.web.app` 은 기본 포함, 커스텀 도메인은 직접 추가)

그다음 **프로젝트 설정 → 내 앱 → 웹 앱**의 `apiKey` 를 2단계 `FIREBASE_API_KEY` 에 넣습니다.
웹 API 키는 공개되어도 되는 값입니다. 실제 권한은 서버가 ID 토큰을 검증해 판단합니다.
""")

code(r"""
# 웹 앱 설정을 자동으로 가져옵니다. 실패하면 콘솔에서 직접 복사해 2단계에 붙여넣으세요.
!npm -q install -g firebase-tools 2>/dev/null | tail -1
cfg = !firebase apps:sdkconfig WEB --project {PROJECT_ID} --json 2>/dev/null
try:
    import json as _j
    sdk = _j.loads("".join(cfg))["result"]["sdkConfig"]
    print("apiKey     :", sdk.get("apiKey"))
    print("authDomain :", sdk.get("authDomain"))
    print("\n위 apiKey 를 2단계 FIREBASE_API_KEY 에 넣고 그 셀을 다시 실행하세요.")
except Exception:
    print("자동 조회 실패 — Firebase 콘솔 > 프로젝트 설정 > 내 앱 > 웹 앱에서 apiKey 를 복사하세요.")
    print("웹 앱이 없다면 콘솔에서 '앱 추가 > 웹'으로 하나 만들면 됩니다.")

print("\n현재 설정")
print("  FIREBASE_API_KEY     :", (FIREBASE_API_KEY[:8] + "...") if FIREBASE_API_KEY else "(비어 있음)")
print("  FIREBASE_AUTH_DOMAIN :", FIREBASE_AUTH_DOMAIN)
if not FIREBASE_API_KEY:
    print("\n키가 없으면 이메일 가입 버튼은 숨겨지고 카카오·네이버만 노출됩니다.")
""")

md("""
## 5-2. 시크릿 등록

소셜 로그인 키와 메일 발송 계정은 노트북에 남기지 않고 Secret Manager에 넣습니다.
아래 셀은 입력값을 화면에 표시하지 않으며, 노트북을 공유해도 키가 새지 않습니다.

- **카카오** — [developers.kakao.com](https://developers.kakao.com) 내 애플리케이션 > 앱 키의 REST API 키와 보안의 Client Secret
- **네이버** — [developers.naver.com](https://developers.naver.com) 애플리케이션 등록 후 Client ID / Secret
- **메일** — Gmail 계정과 앱 비밀번호(2단계 인증 후 발급). 다른 SMTP를 쓰셔도 됩니다.

두 서비스 모두 **Redirect URI**를 등록해야 합니다. Cloud Run 배포 후 출력되는 주소로
`https://<API 주소>/auth/kakao/callback`, `https://<API 주소>/auth/naver/callback` 를 등록하세요.
""")

code(r"""
from getpass import getpass
import secrets as _secrets

!gcloud services enable secretmanager.googleapis.com -q

def put_secret(name, value):
    if not value:
        print(f"  {name}: 건너뜀 (빈 값)")
        return
    import subprocess
    subprocess.run(["gcloud", "secrets", "create", name, "--replication-policy=automatic", "-q"],
                   capture_output=True)
    r = subprocess.run(["gcloud", "secrets", "versions", "add", name, "--data-file=-"],
                       input=value.encode(), capture_output=True)
    print(f"  {name}: {'저장됨' if r.returncode == 0 else '실패 ' + r.stderr.decode()[:80]}")

print("입력하지 않고 엔터를 누르면 해당 항목은 건너뜁니다.\n")
put_secret("SESSION_SECRET",      _secrets.token_urlsafe(32))
put_secret("KAKAO_CLIENT_ID",     getpass("카카오 REST API 키: "))
put_secret("KAKAO_CLIENT_SECRET", getpass("카카오 Client Secret: "))
put_secret("NAVER_CLIENT_ID",     getpass("네이버 Client ID: "))
put_secret("NAVER_CLIENT_SECRET", getpass("네이버 Client Secret: "))
put_secret("SMTP_USER",           getpass("메일 발송 계정(예: bsm@gmail.com): "))
put_secret("SMTP_PASS",           getpass("메일 앱 비밀번호: "))

# Cloud Run 서비스 계정에 시크릿 접근 권한 부여
PROJNUM = !gcloud projects describe {PROJECT_ID} --format="value(projectNumber)"
PROJNUM = PROJNUM[0].strip()
SA = f"{PROJNUM}-compute@developer.gserviceaccount.com"
for name in ["SESSION_SECRET","KAKAO_CLIENT_ID","KAKAO_CLIENT_SECRET",
             "NAVER_CLIENT_ID","NAVER_CLIENT_SECRET","SMTP_USER","SMTP_PASS"]:
    !gcloud secrets add-iam-policy-binding {name} \
      --member=serviceAccount:{SA} --role=roles/secretmanager.secretAccessor -q > /dev/null 2>&1
print(f"\n시크릿 접근 권한 부여: {SA}")
""")

md("""
## 6. 공통 유틸 — 임베딩과 청킹

한국어 문서는 문단 경계를 지키며 자르는 것이 검색 품질에 유리합니다.
겹침(overlap)을 두어 문단 경계에 걸친 내용이 잘려나가지 않게 합니다.
""")

code(r"""
from google import genai
from google.genai import types as gt

gc = genai.Client(vertexai=True, project=PROJECT_ID, location=VERTEX_LOC)

def embed(texts, task="RETRIEVAL_DOCUMENT", batch=32):
    # 문자열 리스트를 임베딩 벡터 리스트로 변환합니다.
    if isinstance(texts, str):
        texts = [texts]
    out = []
    for i in range(0, len(texts), batch):
        r = gc.models.embed_content(
            model=EMBED_MODEL,
            contents=texts[i:i+batch],
            config=gt.EmbedContentConfig(task_type=task, output_dimensionality=EMBED_DIM),
        )
        out.extend([list(e.values) for e in r.embeddings])
    return out

def chunk_text(text, size=900, overlap=150):
    # 문단 단위로 모으다가 size를 넘으면 끊습니다.
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, cur = [], ""
    for p in paras:
        if len(cur) + len(p) + 2 <= size:
            cur = (cur + "\n\n" + p).strip()
        else:
            if cur:
                chunks.append(cur)
            if len(p) <= size:
                cur = p
            else:                       # 한 문단이 너무 길면 문장 단위로 재분할
                sents = re.split(r"(?<=[.!?。？！])\s+|\n", p)
                cur = ""
                for s in sents:
                    if len(cur) + len(s) + 1 <= size:
                        cur = (cur + " " + s).strip()
                    else:
                        if cur:
                            chunks.append(cur)
                        cur = s
    if cur:
        chunks.append(cur)

    if overlap > 0 and len(chunks) > 1:   # 앞 청크 꼬리를 다음 청크 머리에 덧붙임
        merged = [chunks[0]]
        for c in chunks[1:]:
            merged.append(chunks[len(merged)-1][-overlap:] + "\n" + c)
        chunks = merged
    return chunks

def insert(table, rows):
    # DELETE 대상 테이블은 스트리밍 대신 load job 으로 넣습니다.
    # 스트리밍 버퍼의 행은 최대 90분간 DML 로 지울 수 없어 재색인이 실패합니다.
    if not rows:
        return
    bq.load_table_from_json(
        rows, f"{DS}.{table}",
        job_config=bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")).result()

def now():
    return dt.datetime.now(dt.timezone.utc)

print("유틸 준비 완료 — 임베딩 차원:", EMBED_DIM)
""")

md("## 7. 테넌트(고객사) 생성")

code(r"""
def create_tenant(tenant_id, name, plan="BASIC", contact_name="", phone="",
                  email="", homepage="", note=""):
    # 고객사를 BigQuery와 Firestore 양쪽에 등록하고 위젯 키를 발급합니다.
    widget_key = hashlib.sha256(f"{tenant_id}:{PROJECT_ID}".encode()).hexdigest()[:24]
    row = {
        "tenant_id": tenant_id, "name": name, "plan": plan, "status": "ACTIVE",
        "contact_name": contact_name, "phone": phone, "email": email,
        "homepage": homepage, "widget_key": widget_key,
        "created_at": now().isoformat(), "note": note,
    }
    bq.query(f"DELETE FROM `{DS}.tenants` WHERE tenant_id=@t",
             job_config=bigquery.QueryJobConfig(query_parameters=[
                 bigquery.ScalarQueryParameter("t", "STRING", tenant_id)])).result()
    insert("tenants", [row])

    fs.collection("tenants").document(tenant_id).set({
        "name": name, "plan": plan, "status": "ACTIVE",
        "widget_key": widget_key, "homepage": homepage,
        "persona": f"{name}의 안내 도우미",
        "updated_at": firestore.SERVER_TIMESTAMP,
    }, merge=True)

    print(f"테넌트 생성: {tenant_id} ({name})")
    print(f"위젯 스크립트:\n<script src=\"{SITE_DOMAIN}/widget.js\" data-tenant=\"{tenant_id}\"></script>")
    return row

# BSM 자체 홈페이지용 테넌트
create_tenant(BSM_TENANT, "BSM", plan="INTERNAL",
              phone=COMPANY["phone"], email=COMPANY["email"], homepage=SITE_DOMAIN,
              note="공식 홈페이지 상담 챗봇")
""")

md("""
## 8. 문서 등록 — 텍스트 · URL · PDF

세 가지 경로로 지식을 넣습니다. 어느 경로든 `documents` → `chunks` 순으로 저장되고
임베딩까지 한 번에 끝납니다.
""")

code(r"""
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

def _store(tenant_id, title, text, source_type, source_uri=""):
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        print("  (건너뜀) 본문이 비어 있습니다:", title)
        return 0
    doc_id = f"D{uuid.uuid4().hex[:12]}"
    insert("documents", [{
        "doc_id": doc_id, "tenant_id": tenant_id, "title": title,
        "source_type": source_type, "source_uri": source_uri,
        "char_len": len(text), "created_at": now().isoformat()}])

    parts = chunk_text(text)
    vecs = embed(parts, task="RETRIEVAL_DOCUMENT")
    rows = [{
        "chunk_id": f"C{uuid.uuid4().hex[:14]}", "tenant_id": tenant_id, "doc_id": doc_id,
        "title": title, "content": p, "embedding": v,
        "char_len": len(p), "created_at": now().isoformat(),
    } for p, v in zip(parts, vecs)]

    for i in range(0, len(rows), 500):
        insert("chunks", rows[i:i+500])
    print(f"  등록: {title} — {len(rows)}개 청크")
    return len(rows)

def add_text(tenant_id, title, text):
    return _store(tenant_id, title, text, "TEXT")

def add_url(tenant_id, url, title=None):
    html = requests.get(url, timeout=20, headers={"User-Agent": "BSM-AI-Factory/1.0"}).text
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()
    text = soup.get_text("\n")
    return _store(tenant_id, title or (soup.title.string if soup.title else url), text, "URL", url)

def add_pdf(tenant_id, path, title=None):
    reader = PdfReader(path)
    text = "\n\n".join((pg.extract_text() or "") for pg in reader.pages)
    return _store(tenant_id, title or os.path.basename(path), text, "PDF", path)

def reset_tenant_knowledge(tenant_id):
    # 다시 색인하기 전에 기존 지식을 비웁니다.
    p = [bigquery.ScalarQueryParameter("t", "STRING", tenant_id)]
    cfg = bigquery.QueryJobConfig(query_parameters=p)
    bq.query(f"DELETE FROM `{DS}.chunks` WHERE tenant_id=@t", job_config=cfg).result()
    bq.query(f"DELETE FROM `{DS}.documents` WHERE tenant_id=@t", job_config=cfg).result()
    print("지식 초기화:", tenant_id)

print("문서 등록 함수 준비 완료")
""")

md("""
## 9. BSM 자체 지식 적재

홈페이지 챗봇이 답해야 할 내용입니다. 이 챗봇이 **BSM의 첫 번째 고객 사례**이므로
여기서의 정확도가 곧 영업 자료가 됩니다. 숫자는 5단계 Firestore 설정과 일치시킵니다.
""")

code(r"""
reset_tenant_knowledge(BSM_TENANT)

KB = {
"BSM 회사 소개": f'''
BSM은 기업의 자료를 학습해 고객 문의에 답하는 AI 챗봇을 월 구독 형태로 공급하는 회사입니다.
Google Cloud 위에서 동작하는 하이브리드 RAG 엔진을 직접 운영하며, 고객사별로 데이터와 설정을 분리합니다.

문의 전화는 {COMPANY["phone"]}, 메일은 {COMPANY["email"]}입니다. 상담 가능 시간은 {COMPANY["hours"]}입니다.
공식 홈페이지는 {SITE_DOMAIN}이며 결제는 {CAFE24_URL} 스토어에서 처리됩니다.
''',

"BSM AI 챗봇 서비스 개요": '''
BSM AI 챗봇은 PDF, 홈페이지, FAQ, 상품 정보를 학습해 방문객의 질문에 답하는 상담 챗봇입니다.
의미 기반의 벡터 검색과 단어 기반의 키워드 검색을 함께 사용하는 하이브리드 RAG 방식을 씁니다.
그래서 품번, 모델명, 규정 조항처럼 정확한 단어가 중요한 질문에서도 엉뚱한 문서를 인용하지 않습니다.

모든 답변에는 근거가 된 문서를 함께 표시합니다.
근거를 찾지 못하면 답을 지어내지 않고 상담 연결로 넘깁니다. 오답보다 연결이 안전하다고 보기 때문입니다.

설치는 홈페이지에 스크립트 한 줄을 넣는 방식이며 카페24, 워드프레스, 자체 제작 사이트 모두 같습니다.
''',

"요금과 무료 체험": f'''
BSM AI 챗봇의 요금은 해결 건수 기준입니다.
해결이란 챗봇이 근거를 갖고 답변을 완료한 대화를 말합니다.
챗봇이 답하지 못해 상담원에게 넘긴 대화는 해결로 세지 않으며 요금도 발생하지 않습니다.
못 맞힌 대화에는 비용을 청구하지 않는다는 뜻입니다.

요금제는 네 가지입니다. 모두 부가세 별도입니다.
Free는 월 0원이며 해결 100건과 문서 50페이지를 제공하고 위젯에 BSM 배지가 표시됩니다.
Starter는 월 39,000원이며 해결 500건과 문서 300페이지, 웹 위젯 1채널을 제공합니다.
Growth는 월 99,000원이며 해결 2,000건과 문서 1,000페이지, 카카오톡 채널 연동과 주간 리포트를 제공합니다.
Scale은 월 249,000원이며 해결 8,000건과 문서 5,000페이지, 다채널과 API, SSO를 제공합니다.

포함된 해결 건수를 넘기면 해결당 40원이 추가됩니다.
연간 결제하면 두 달치가 할인됩니다.
무료 체험은 {COMPANY["trial_days"]}일간 가능하며 카드 등록이 필요 없습니다.

개통 지원 비용은 {COMPANY["onboarding_fee"]:,}원이지만 현재 초기 {COMPANY["onboarding_free_quota"]}곳까지는 무료입니다.
무료 조건은 도입 후기와 사례 공개에 동의하시는 것입니다.

ERP나 CRM 연동, 사내 데이터베이스 연계, 수만 페이지 규모의 기업 맞춤 구축은 별도 상담이 필요하며
연 {COMPANY["enterprise_from"]:,}원부터 시작합니다.

결제는 카페24 스토어에서 상품을 구매하는 방식이라 별도 가입이나 계약서 없이 시작할 수 있습니다.
카드 결제와 계좌이체가 가능하며 세금계산서를 발행합니다.
''',

"도입 절차": '''
도입은 상담, 자료 전달, 학습과 검수, 스크립트 설치, 오픈 순서로 진행합니다.
자료를 주신 뒤 영업일 기준 2일에서 5일 안에 학습과 검수를 마칩니다.

보내주실 자료는 상품 목록, 이용 안내 문서, 자주 묻는 질문, 홈페이지 주소 무엇이든 좋습니다.
정리되지 않은 파일이어도 괜찮습니다. 정리와 검수는 BSM이 합니다.

개통 후에는 챗봇이 답하지 못한 질문 목록을 매주 보내드립니다. 그 목록이 다음에 보완할 자료가 됩니다.
''',

"분양 파트너 제도": f'''
BSM은 업종 팩과 권역을 묶은 1구좌 단위로 분양 파트너를 모집합니다.
초기 분양비는 {COMPANY["franchise_fee"]:,}원이며 부가세는 별도입니다.
분양비에는 4주 실무 교육, 파트너 포털, 마케팅 자료 일체, 시연 계정, 권역 독점권 12개월이 포함됩니다.

월 플랫폼 사용료는 {COMPANY["franchise_monthly"]:,}원이며 테넌트를 5곳 이상 확보하면 면제됩니다.
파트너 수익은 구독 매출의 {COMPANY["partner_share"]}퍼센트이고 테넌트 20곳을 넘는 분부터는 45퍼센트입니다.
개통비는 파트너가 70퍼센트를 가져갑니다.

테넌트 25곳을 확보하면 월 순수익이 약 200만원 수준으로 추정되며 투자금 회수는 12개월에서 14개월로 봅니다.
다만 이는 추정치이며 보장 수익이 아닙니다.

권역당 한 구좌만 배정해 파트너끼리 경쟁하지 않도록 합니다.
12개월 안에 테넌트 10곳에 이르지 못하면 분양비의 50퍼센트를 환급합니다.
권역별 잔여 구좌는 전화로 확인해 주셔야 합니다.
''',

"기술 구조": '''
BSM은 Google Cloud 기반의 서버리스 구조로 운영됩니다.
홈페이지는 Firebase Hosting, 챗봇 API는 Cloud Run, 지식과 검색은 BigQuery, 설정은 Firestore를 씁니다.
답변 생성에는 Google의 Gemini 모델을 사용합니다.

질문이 들어오면 벡터 검색과 키워드 검색을 동시에 실행하고 두 결과를 RRF 방식으로 합칩니다.
그 뒤 상위 근거만 모델에 전달해 답변을 만들고, 답변에 근거 문서를 표시합니다.
고객사 데이터는 테넌트 단위로 분리되어 다른 고객의 챗봇에 사용되지 않습니다.
''',

"자주 묻는 질문": f'''
질문: 개발자가 없어도 도입할 수 있나요?
답변: 가능합니다. 자료를 보내주시면 학습과 검수까지 BSM이 합니다. 받으신 스크립트 한 줄만 홈페이지에 넣으시면 됩니다.

질문: 엉뚱한 답을 하면 어떻게 되나요?
답변: 근거 문서를 찾지 못하면 답을 지어내지 않고 확인이 필요하다고 안내한 뒤 상담으로 연결합니다.

질문: 카페24 쇼핑몰에도 설치할 수 있나요?
답변: 가능합니다. 상품 정보를 학습시키면 재고, 배송, 교환 문의까지 답할 수 있습니다.

질문: 학습시킨 자료가 유출되지 않나요?
답변: 고객사별로 저장 공간과 권한을 분리합니다. 요청하시면 삭제 후 삭제 확인서를 드립니다.

질문: 카카오톡 상담도 되나요?
답변: 현재는 홈페이지 위젯만 제공합니다. 카카오톡 채널과 음성 상담은 준비 중이며 일정은 전화로 안내합니다.

질문: 기업 맞춤 구축도 가능한가요?
답변: ERP, CRM, 사내 데이터베이스 연동이나 수만 페이지 규모는 별도 상담이 필요합니다. {COMPANY["phone"]}으로 문의해 주세요.
''',
}

total = 0
for title, text in KB.items():
    total += add_text(BSM_TENANT, title, text)
print(f"\nBSM 지식 적재 완료 — 총 {total}개 청크")
""")

md("""
## 10. 하이브리드 검색 — 벡터 + 키워드 + RRF

한 번의 BigQuery 쿼리로 두 검색을 돌리고 RRF(Reciprocal Rank Fusion)로 합칩니다.

키워드 쪽은 BigQuery의 `SEARCH()` 대신 **부분 문자열 매칭**으로 점수를 냅니다.
한국어는 조사가 붙어 "환불규정은"처럼 변형되기 때문에, 토크나이저 기반 정확 일치보다
부분 문자열 매칭이 실제 질문에서 더 잘 맞습니다.
""")

code(r"""
RRF_K = 60      # RRF 상수. 클수록 순위 차이를 완만하게 반영합니다.

def _terms(q, min_len=2, max_n=8):
    # 질문에서 검색어 후보를 뽑습니다. 조사가 붙은 어절은 뒤를 조금 잘라 함께 봅니다.
    raw = re.findall(r"[0-9A-Za-z가-힣]+", q)
    out = []
    for w in raw:
        if len(w) < min_len:
            continue
        out.append(w)
        if len(w) >= 4 and re.match(r"^[가-힣]+$", w):
            out.append(w[:-1])
    seen, uniq = set(), []
    for w in out:
        if w.lower() not in seen:
            seen.add(w.lower()); uniq.append(w)
    return uniq[:max_n]

SEARCH_SQL = f'''
WITH qv AS (SELECT @qvec AS embedding),
vec AS (
  SELECT base.chunk_id AS chunk_id, base.title AS title, base.content AS content,
         ROW_NUMBER() OVER (ORDER BY distance ASC) AS rnk
  FROM VECTOR_SEARCH(
         (SELECT chunk_id, title, content, embedding
            FROM `{DS}.chunks` WHERE tenant_id = @tenant),
         'embedding',
         (SELECT embedding FROM qv),
         top_k => @topk, distance_type => 'COSINE')
),
kw_scored AS (
  SELECT chunk_id, title, content,
         (SELECT IFNULL(SUM(IF(STRPOS(LOWER(CONCAT(IFNULL(title,''),' ',content)),
                                      LOWER(t)) > 0, LENGTH(t), 0)), 0)
            FROM UNNEST(@terms) AS t) AS kscore
    FROM `{DS}.chunks` WHERE tenant_id = @tenant
),
kw AS (
  SELECT chunk_id, title, content, rnk FROM (
    SELECT chunk_id, title, content, kscore,
           ROW_NUMBER() OVER (ORDER BY kscore DESC, chunk_id) AS rnk
      FROM kw_scored WHERE kscore > 0)
  WHERE rnk <= @topk
)
SELECT
  COALESCE(v.chunk_id, k.chunk_id) AS chunk_id,
  COALESCE(v.title,    k.title)    AS title,
  COALESCE(v.content,  k.content)  AS content,
  IFNULL(1.0/({RRF_K}+v.rnk), 0) + IFNULL(1.0/({RRF_K}+k.rnk), 0) AS rrf,
  v.rnk AS vec_rank, k.rnk AS kw_rank
FROM vec v FULL OUTER JOIN kw k ON v.chunk_id = k.chunk_id
ORDER BY rrf DESC
LIMIT @final_k
'''

def search(question, tenant_id=BSM_TENANT, topk=20, final_k=5):
    qvec = embed(question, task="RETRIEVAL_QUERY")[0]
    cfg = bigquery.QueryJobConfig(query_parameters=[
        bigquery.ArrayQueryParameter("qvec", "FLOAT64", qvec),
        bigquery.ArrayQueryParameter("terms", "STRING", _terms(question) or [question]),
        bigquery.ScalarQueryParameter("tenant", "STRING", tenant_id),
        bigquery.ScalarQueryParameter("topk", "INT64", topk),
        bigquery.ScalarQueryParameter("final_k", "INT64", final_k),
    ])
    return [dict(r) for r in bq.query(SEARCH_SQL, job_config=cfg).result()]

# 확인
for h in search("분양 가격이 얼마인가요?"):
    print(f"[{h['rrf']:.4f}] vec={h['vec_rank']} kw={h['kw_rank']} | {h['title']}")
    print("   ", h["content"][:70].replace("\n", " "), "...")
""")

md("""
## 11. 답변 생성 — 근거 인용과 가드레일

세 가지 안전장치를 둡니다.

1. **검색 점수 하한** — 근거가 약하면 모델을 부르지 않고 바로 상담 연결로 넘깁니다.
2. **JSON 강제 출력** — `grounded` 플래그를 모델이 스스로 표시하게 하고, 거짓이면 상담 연결로 바꿉니다.
3. **다음 행동 분류** — `BUY`, `TRIAL`, `CONTACT`, `NONE` 중 하나를 반환해 홈페이지가 알맞은 버튼을 띄웁니다.
""")

code(r"""
MIN_RRF = 0.016      # 이 값보다 근거가 약하면 모델을 호출하지 않습니다.

FALLBACK = (f"제가 가진 자료로는 정확히 답변드리기 어렵습니다.\n"
            f"전화 {COMPANY['phone']} 또는 메일 {COMPANY['email']}로 문의해 주시면 "
            f"담당자가 정확히 안내해 드리겠습니다.")

SYSTEM = f'''당신은 BSM의 상담 도우미입니다. 아래 [근거]에 있는 내용만 사용해 한국어 존댓말로 답하세요.

규칙
- 3~5문장으로 짧게 답합니다. 목록이 필요하면 '- '를 씁니다. 이모지는 쓰지 않습니다.
- [근거]에 없는 숫자나 조건을 지어내지 마세요. 없으면 grounded를 false로 두세요.
- 계약 조항, 세무·법률 판단, 특정 권역의 잔여 구좌처럼 확답이 필요한 내용은 상담 연결로 안내하세요.
- 상대가 채팅에 전화번호나 주소를 적으려 하면 채팅에 남기지 말고 전화나 메일로 달라고 안내하세요.
- 답변 끝에 다음 단계를 한 문장으로 제안하세요.

문의처: 전화 {COMPANY["phone"]}, 메일 {COMPANY["email"]}

action 값 선택
- BUY: 지금 구매·신청 의사가 보일 때
- TRIAL: 무료 체험을 권하는 것이 자연스러울 때
- CONTACT: 기업 맞춤 구축, 분양 상담, 확답이 필요한 문의일 때
- NONE: 그 밖의 일반 안내

반드시 다음 JSON만 출력하세요.
{{"answer": "답변 본문", "grounded": true, "action": "BUY|TRIAL|CONTACT|NONE"}}'''

def answer(question, tenant_id=BSM_TENANT, session_id=None, log=True):
    t0 = time.time()
    hits = search(question, tenant_id=tenant_id)
    top = hits[0]["rrf"] if hits else 0.0

    if not hits or top < MIN_RRF:
        res = {"answer": FALLBACK, "sources": [], "action": "CONTACT",
               "grounded": False, "top_score": top}
    else:
        ctx = "\n\n".join(f"[{i+1}] {h['title']}\n{h['content']}" for i, h in enumerate(hits))
        try:
            r = gc.models.generate_content(
                model=GEN_MODEL,
                contents=f"[근거]\n{ctx}\n\n[질문]\n{question}",
                config=gt.GenerateContentConfig(
                    system_instruction=SYSTEM, temperature=0.2,
                    max_output_tokens=900, response_mime_type="application/json"),
            )
            d = json.loads(r.text)
            grounded = bool(d.get("grounded", False))
            res = {
                "answer": d.get("answer", "").strip() if grounded else FALLBACK,
                "sources": sorted({h["title"] for h in hits[:3]}) if grounded else [],
                "action": d.get("action", "NONE") if grounded else "CONTACT",
                "grounded": grounded, "top_score": top,
            }
        except Exception as e:
            print("  생성 실패:", type(e).__name__, e)
            res = {"answer": FALLBACK, "sources": [], "action": "CONTACT",
                   "grounded": False, "top_score": top}

    res["latency_ms"] = int((time.time() - t0) * 1000)

    if log:
        bq.insert_rows_json(f"{DS}.chat_logs", [{
            "log_id": f"L{uuid.uuid4().hex[:14]}", "tenant_id": tenant_id,
            "session_id": session_id or "notebook", "question": question,
            "answer": res["answer"], "sources": res["sources"], "action": res["action"],
            "grounded": res["grounded"], "top_score": res["top_score"],
            "latency_ms": res["latency_ms"], "created_at": now().isoformat()}])
    return res

print("답변 엔진 준비 완료")
""")

md("## 12. 로컬 테스트")

code(r"""
QUESTIONS = [
    "가격이 얼마인가요?",
    "우리 회사 홈페이지에도 설치할 수 있나요?",
    "PDF도 학습할 수 있나요?",
    "챗봇 분양은 어떻게 하나요?",
    "무료 체험이 있나요?",
    "AI가 모르면 어떻게 하나요?",
    "서울 강남구 구좌가 아직 남아 있나요?",     # 자료에 없는 질문 — 상담 연결로 넘어가야 정상
]

for q in QUESTIONS:
    r = answer(q)
    flag = "근거O" if r["grounded"] else "근거X"
    print(f"\nQ. {q}")
    print(f"A. {r['answer']}")
    print(f"   [{flag} · action={r['action']} · {r['latency_ms']}ms · 근거: {', '.join(r['sources']) or '없음'}]")
""")

md("""
## 13. 골든셋 평가

배포 전에 반드시 통과시켜야 할 관문입니다.
질문마다 **반드시 들어가야 할 키워드**를 정해 두고 답변에 포함되는지 봅니다.
정답률이 기준에 못 미치면 배포하지 말고 지식을 보완하세요.
""")

code(r"""
GOLDEN = [
    ("가격이 얼마인가요?",                    ["99,000"]),
    ("무료 요금제가 있나요?",                 ["Free"]),
    ("가장 저렴한 유료 플랜은?",               ["39,000"]),
    ("해결 건수를 초과하면 어떻게 되나요?",     ["40"]),
    ("해결이 정확히 무슨 뜻인가요?",           ["근거"]),
    ("무료 체험 기간은?",                     ["14"]),
    ("분양비는 얼마인가요?",                   ["1,500"]),
    ("파트너 수익 배분은?",                    ["40"]),
    ("개통까지 얼마나 걸리나요?",              ["2", "5"]),
    ("설치는 어떻게 하나요?",                  ["스크립트"]),
    ("결제는 어디서 하나요?",                  ["카페24"]),
    ("문의 전화번호 알려주세요",               ["0507-1419-0222"]),
    ("답을 못 찾으면 어떻게 하나요?",           ["상담"]),
]

rows = [{"gs_id": f"G{i:03d}", "tenant_id": BSM_TENANT, "question": q,
         "expect_keywords": k, "note": ""} for i, (q, k) in enumerate(GOLDEN, 1)]
bq.query(f"DELETE FROM `{DS}.golden_set` WHERE tenant_id='{BSM_TENANT}'").result()
insert("golden_set", rows)

ok = 0
print(f"{'판정':<6}{'질문'}")
print("-" * 76)
for q, kws in GOLDEN:
    r = answer(q, log=False)
    hit = all(k.replace(",", "") in r["answer"].replace(",", "") for k in kws)
    ok += hit
    print(f"{'통과' if hit else '실패':<6}{q}")
    if not hit:
        print(f"      기대 키워드 {kws} / 답변: {r['answer'][:70]}...")

rate = ok / len(GOLDEN) * 100
print("-" * 76)
print(f"정답률 {rate:.0f}% ({ok}/{len(GOLDEN)})")
print("배포 기준 85% 이상 —", "통과" if rate >= 85 else "미달. 지식을 보완한 뒤 다시 실행하세요.")
""")

md("""
## 14. Cloud Run API 배포

노트북에서 검증한 로직을 그대로 FastAPI로 옮겨 배포합니다.
엔드포인트는 초기에 세 개면 충분합니다 — `POST /chat`, `POST /lead`, `GET /health`.
""")

code(r"""
from pathlib import Path

APP = Path("/content/bsm_api"); APP.mkdir(parents=True, exist_ok=True)
MAIL_TO = COMPANY["email"]

(APP / "requirements.txt").write_text('''fastapi==0.115.6
uvicorn[standard]==0.34.0
google-cloud-bigquery==3.27.0
google-cloud-firestore==2.19.0
google-genai==1.2.0
pydantic==2.10.4
requests==2.32.3
firebase-admin==6.6.0
''')

(APP / "search.sql").write_text(SEARCH_SQL)

(APP / "main.py").write_text(f'''
import os, re, json, time, uuid, hmac, hashlib, base64, smtplib, datetime as dt
from email.message import EmailMessage
from typing import List, Optional, Dict, Any
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from google.cloud import bigquery, firestore
from google import genai
from google.genai import types as gt

PROJECT    = os.environ["PROJECT_ID"]
DATASET    = os.environ.get("DATASET", "{DATASET}")
VERTEX_LOC = os.environ.get("VERTEX_LOC", "{VERTEX_LOC}")
GEN_MODEL  = os.environ.get("GEN_MODEL", "{GEN_MODEL}")
EMB_MODEL  = os.environ.get("EMBED_MODEL", "{EMBED_MODEL}")
EMB_DIM    = int(os.environ.get("EMBED_DIM", "{EMBED_DIM}"))
MIN_RRF    = float(os.environ.get("MIN_RRF", "{MIN_RRF}"))
SITE       = os.environ.get("SITE_DOMAIN", "{SITE_DOMAIN}")
ALLOW      = [o for o in os.environ.get("ALLOW_ORIGINS", "*").split(",") if o]
DS         = PROJECT + "." + DATASET

# 시크릿 (Secret Manager 로 주입)
SESSION_SECRET = os.environ.get("SESSION_SECRET", "dev-only-not-secure")
KAKAO_ID       = os.environ.get("KAKAO_CLIENT_ID", "")
KAKAO_SECRET   = os.environ.get("KAKAO_CLIENT_SECRET", "")
NAVER_ID       = os.environ.get("NAVER_CLIENT_ID", "")
NAVER_SECRET   = os.environ.get("NAVER_CLIENT_SECRET", "")
SMTP_HOST      = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT      = int(os.environ.get("SMTP_PORT", "465"))
SMTP_USER      = os.environ.get("SMTP_USER", "")
SMTP_PASS      = os.environ.get("SMTP_PASS", "")

bq = bigquery.Client(project=PROJECT)
fs = firestore.Client(project=PROJECT)
gc = genai.Client(vertexai=True, project=PROJECT, location=VERTEX_LOC)

SEARCH_SQL = open(os.path.join(os.path.dirname(__file__), "search.sql"), encoding="utf-8").read()

_cache: Dict[str, Any] = {{}}
def cached(key, ttl, loader):
    e = _cache.get(key)
    if e and time.time() - e[0] < ttl:
        return e[1]
    v = loader()
    _cache[key] = (time.time(), v)
    return v

def company():
    return cached("company", 300,
        lambda: fs.collection("company").document("bsm").get().to_dict() or {{}})

def flow():
    return cached("flow", 60,
        lambda: (fs.collection("flows").document("main").get().to_dict() or {{}}).get("nodes", {{}}))

def mail_to():
    return company().get("email", "{MAIL_TO}")

def now_iso():
    return dt.datetime.now(dt.timezone.utc).isoformat()

# ── 세션 토큰: HMAC 서명 문자열. 별도 저장소가 필요 없습니다. ──
def sign(payload: str, ttl_sec: int = 60 * 60 * 24 * 14) -> str:
    exp = str(int(time.time()) + ttl_sec)
    raw = payload + "|" + exp
    sig = hmac.new(SESSION_SECRET.encode(), raw.encode(), hashlib.sha256).hexdigest()[:32]
    return base64.urlsafe_b64encode((raw + "|" + sig).encode()).decode().rstrip("=")

def verify(token: str) -> Optional[str]:
    try:
        pad = "=" * (-len(token) % 4)
        raw = base64.urlsafe_b64decode(token + pad).decode()
        payload, exp, sig = raw.rsplit("|", 2)
        good = hmac.new(SESSION_SECRET.encode(), (payload + "|" + exp).encode(),
                        hashlib.sha256).hexdigest()[:32]
        if not hmac.compare_digest(sig, good):
            return None
        if int(exp) < time.time():
            return None
        return payload
    except Exception:
        return None

def bearer(auth: Optional[str]) -> Optional[str]:
    if not auth or not auth.lower().startswith("bearer "):
        return None
    return verify(auth.split(" ", 1)[1].strip())

# ── 메일 발송 ────────────────────────────────────────────────
def send_mail(subject: str, body: str, reply_to: str = "") -> Dict[str, Any]:
    if not (SMTP_USER and SMTP_PASS):
        return {{"sent": False, "error": "SMTP 미설정"}}
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = mail_to()
        if reply_to:
            msg["Reply-To"] = reply_to
        msg.set_content(body)
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=20) as s:
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
        return {{"sent": True, "error": ""}}
    except Exception as e:
        return {{"sent": False, "error": type(e).__name__ + ": " + str(e)[:200]}}

# ── 검색 ─────────────────────────────────────────────────────
def terms(q):
    out = []
    for w in re.findall(r"[0-9A-Za-z가-힣]+", q):
        if len(w) < 2:
            continue
        out.append(w)
        if len(w) >= 4 and re.match(r"^[가-힣]+$", w):
            out.append(w[:-1])
    seen, uniq = set(), []
    for w in out:
        if w.lower() not in seen:
            seen.add(w.lower()); uniq.append(w)
    return uniq[:8]

def embed_query(q):
    r = gc.models.embed_content(model=EMB_MODEL, contents=[q],
        config=gt.EmbedContentConfig(task_type="RETRIEVAL_QUERY", output_dimensionality=EMB_DIM))
    return list(r.embeddings[0].values)

_notified = set()   # 세션당 미응답 통보 1회

def retrieve(tenant_id, q):
    cfg = bigquery.QueryJobConfig(query_parameters=[
        bigquery.ArrayQueryParameter("qvec", "FLOAT64", embed_query(q)),
        bigquery.ArrayQueryParameter("terms", "STRING", terms(q) or [q]),
        bigquery.ScalarQueryParameter("tenant", "STRING", tenant_id),
        bigquery.ScalarQueryParameter("topk", "INT64", 20),
        bigquery.ScalarQueryParameter("final_k", "INT64", 5)])
    return [dict(r) for r in bq.query(SEARCH_SQL, job_config=cfg).result()]

def system_prompt():
    c = company()
    return (
      "당신은 BSM의 상담 도우미입니다. 아래 [근거]에 있는 내용만 사용해 한국어 존댓말로 답하세요.\\n"
      "규칙\\n"
      "- 3~5문장으로 짧게 답합니다. 목록이 필요하면 - 를 씁니다. 이모지는 쓰지 않습니다.\\n"
      "- [근거]에 없는 숫자나 조건을 지어내지 마세요. 없으면 grounded 를 false 로 두세요.\\n"
      "- 고객이 만들고 싶어 하는 것을 구체적으로 되물어 요구사항을 좁히세요.\\n"
      "- 개인정보는 채팅에 적지 말고 담당자에게 전달하라고 안내하세요.\\n"
      "문의처: 전화 " + str(c.get("phone", "")) + ", 메일 " + str(c.get("email", "")) + "\\n"
      "action 값: BUY(구매 의사) TRIAL(무료 시작) PRICE(가격·견적 문의) CONTACT(상담 연결) NONE(일반 안내)\\n"
      "반드시 다음 JSON만 출력하세요.\\n"
      '{{"answer": "답변 본문", "grounded": true, "action": "BUY|TRIAL|PRICE|CONTACT|NONE"}}'
    )

# ── 앱 ───────────────────────────────────────────────────────
app = FastAPI(title="BSM AI API")
app.add_middleware(CORSMiddleware, allow_origins=ALLOW or ["*"],
                   allow_methods=["POST", "GET"], allow_headers=["*"])

class Turn(BaseModel):
    role: str
    content: str

class ChatIn(BaseModel):
    tenant_id: str = "{BSM_TENANT}"
    question: str
    session_id: Optional[str] = None
    history: List[Turn] = []

class ChatOut(BaseModel):
    answer: str
    sources: List[str] = []
    action: str = "NONE"
    grounded: bool = False
    escalate: bool = False

class EscIn(BaseModel):
    session_id: Optional[str] = None
    question: str
    contact_email: str
    memo: str = ""
    history: List[Turn] = []

class InquiryIn(BaseModel):
    category: str = "PRICE"
    title: str = ""
    body: str = ""
    company_name: str = ""
    phone: str = ""
    channel: str = "web"

@app.get("/health")
def health():
    return {{"ok": True, "model": GEN_MODEL, "ts": now_iso()}}

@app.get("/flow")
def get_flow():
    return {{"nodes": flow()}}

def miss_message():
    c = company()
    return ("제가 가진 자료에서는 이 질문의 근거를 찾지 못했습니다.\\n"
            "정확하지 않은 답변을 드리는 대신 담당자에게 전달해 드리겠습니다.\\n"
            "회신받으실 이메일 주소를 남겨주시면 " + str(c.get("email", "")) +
            " 담당자가 확인 후 회신드리겠습니다.")

def notify_unanswered(session_id, q, vec_hit, kw_hit, top):
    # 고객이 이메일을 남기지 않아도 지식 공백은 담당자가 바로 알아야 합니다.
    if os.environ.get("NOTIFY_UNANSWERED", "true").lower() != "true":
        return
    key = (session_id or "web") + "|" + q[:40]
    if key in _notified:
        return
    if len(_notified) > 5000:
        _notified.clear()
    _notified.add(key)
    send_mail("[BSM 미응답 질문] " + q[:40],
              ("챗봇이 답하지 못한 질문입니다. 지식 보완이 필요합니다.\\n\\n"
               "질문: " + q + "\\n"
               "세션: " + str(session_id) + "\\n"
               "시각: " + now_iso() + "\\n\\n"
               "검색 결과\\n"
               "  벡터 검색 근거: " + ("있음" if vec_hit else "없음") + "\\n"
               "  키워드 검색 근거: " + ("있음" if kw_hit else "없음") + "\\n"
               "  최고 RRF 점수: " + str(round(top, 5)) + " (기준 " + str(MIN_RRF) + ")\\n\\n"
               "고객이 이메일을 남기면 정리된 문의가 별도로 도착합니다."))

@app.post("/chat", response_model=ChatOut)
def chat(inp: ChatIn):
    t0 = time.time()
    q = (inp.question or "").strip()[:500]
    if not q:
        return ChatOut(answer="무엇을 도와드릴까요?", action="NONE")

    # ── 하이브리드 RAG : 두 검색을 각각 판정합니다 ──────────────
    hits = retrieve(inp.tenant_id, q)
    vec_hit = any(h.get("vec_rank") is not None for h in hits)
    kw_hit  = any(h.get("kw_rank") is not None for h in hits)
    top = hits[0]["rrf"] if hits else 0.0
    weak = (not hits) or (top < MIN_RRF)

    if weak:
        # 벡터 검색과 키워드 검색 어느 쪽에서도 쓸 만한 근거가 없습니다.
        # 모델을 호출하지 않고 담당자 전달로 넘깁니다.
        notify_unanswered(inp.session_id, q, vec_hit, kw_hit, top)
        out = ChatOut(answer=miss_message(), action="CONTACT", grounded=False, escalate=True)
    else:
        ctx = "\\n\\n".join("[" + str(i + 1) + "] " + h["title"] + "\\n" + h["content"]
                           for i, h in enumerate(hits))
        convo = ""
        for t in inp.history[-6:]:
            convo += ("고객: " if t.role == "user" else "상담: ") + t.content[:300] + "\\n"
        try:
            r = gc.models.generate_content(
                model=GEN_MODEL,
                contents="[근거]\\n" + ctx + "\\n\\n[이전 대화]\\n" + convo + "\\n[질문]\\n" + q,
                config=gt.GenerateContentConfig(system_instruction=system_prompt(),
                    temperature=0.2, max_output_tokens=900,
                    response_mime_type="application/json"))
            d = json.loads(r.text)
            g = bool(d.get("grounded", False))
            act = d.get("action", "NONE") if g else "CONTACT"
            if not g:
                # 근거는 있었지만 모델이 답을 확신하지 못한 경우도 전달로 넘깁니다.
                notify_unanswered(inp.session_id, q, vec_hit, kw_hit, top)
            out = ChatOut(answer=d.get("answer", "").strip() if g else miss_message(),
                          sources=sorted({{h["title"] for h in hits[:3]}}) if g else [],
                          action=act, grounded=g, escalate=not g)
        except Exception:
            notify_unanswered(inp.session_id, q, vec_hit, kw_hit, top)
            out = ChatOut(answer=miss_message(), action="CONTACT", grounded=False, escalate=True)

    try:
        bq.insert_rows_json(DS + ".chat_logs", [{{
            "log_id": "L" + uuid.uuid4().hex[:14], "tenant_id": inp.tenant_id,
            "session_id": inp.session_id or "web", "question": q, "answer": out.answer,
            "sources": out.sources, "action": out.action, "grounded": out.grounded,
            "top_score": float(top), "latency_ms": int((time.time() - t0) * 1000),
            "created_at": now_iso()}}])
    except Exception:
        pass
    return out

@app.post("/escalate")
def escalate(inp: EscIn):
    # 챗봇이 답하지 못한 문의를 정리해 담당자 메일로 보냅니다.
    email = (inp.contact_email or "").strip()
    if not re.match(r"^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", email):
        return {{"ok": False, "error": "이메일 형식이 올바르지 않습니다."}}

    convo = ""
    for t in inp.history[-12:]:
        convo += ("고객: " if t.role == "user" else "상담: ") + t.content[:400] + "\\n"

    summary = ""
    try:
        r = gc.models.generate_content(
            model=GEN_MODEL,
            contents=("아래 상담 대화를 담당자가 5초 안에 파악할 수 있게 정리하세요.\\n\\n"
                      "[대화]\\n" + convo + "\\n[마지막 질문]\\n" + inp.question +
                      "\\n[고객 메모]\\n" + (inp.memo or "없음")),
            config=gt.GenerateContentConfig(
                system_instruction=(
                  "한국어로 다음 네 항목만 출력하세요. 각 항목은 한두 문장입니다.\\n"
                  "1. 문의 요약\\n2. 고객이 만들려는 것\\n3. 회신에 필요한 정보\\n4. 예상 응대 방향\\n"
                  "추측은 쓰지 말고 대화에 나온 내용만 쓰세요."),
                temperature=0.2, max_output_tokens=600))
        summary = (r.text or "").strip()
    except Exception as e:
        summary = "(요약 생성 실패: " + type(e).__name__ + ")"

    esc_id = "E" + uuid.uuid4().hex[:12]
    body = ("BSM AI 챗봇에서 전달된 문의입니다.\\n\\n"
            "문의번호: " + esc_id + "\\n"
            "회신 이메일: " + email + "\\n"
            "접수 시각: " + now_iso() + "\\n\\n"
            "── 정리 ──\\n" + summary + "\\n\\n"
            "── 마지막 질문 ──\\n" + inp.question + "\\n\\n"
            "── 대화 전문 ──\\n" + (convo or "(없음)"))
    res = send_mail("[BSM 챗봇 문의] " + inp.question[:40], body, reply_to=email)

    try:
        bq.insert_rows_json(DS + ".escalations", [{{
            "esc_id": esc_id, "tenant_id": "{BSM_TENANT}",
            "session_id": inp.session_id or "web", "question": inp.question,
            "summary": summary, "contact_email": email, "memo": inp.memo or "",
            "email_sent": bool(res["sent"]), "email_error": res["error"],
            "status": "NEW", "created_at": now_iso()}}])
    except Exception:
        pass

    return {{"ok": True, "esc_id": esc_id, "email_sent": res["sent"],
            "message": ("문의를 접수했습니다. " + mail_to() + " 담당자가 확인 후 " +
                        email + " 으로 회신드립니다. 문의번호는 " + esc_id + " 입니다.")}}

# ── 소셜 로그인 ──────────────────────────────────────────────
PROVIDERS = {{
  "kakao": {{
    "auth": "https://kauth.kakao.com/oauth/authorize",
    "token": "https://kauth.kakao.com/oauth/token",
    "me": "https://kapi.kakao.com/v2/user/me",
    "scope": "profile_nickname,account_email",
  }},
  "naver": {{
    "auth": "https://nid.naver.com/oauth2.0/authorize",
    "token": "https://nid.naver.com/oauth2.0/token",
    "me": "https://openapi.naver.com/v1/nid/me",
    "scope": "",
  }},
}}

def creds(p):
    return (KAKAO_ID, KAKAO_SECRET) if p == "kakao" else (NAVER_ID, NAVER_SECRET)

def redirect_uri(p):
    base = os.environ.get("API_BASE", "")
    return base + "/auth/" + p + "/callback"

@app.get("/auth/{{provider}}/login")
def social_login(provider: str, redirect: str = ""):
    if provider not in PROVIDERS:
        return {{"ok": False, "error": "지원하지 않는 로그인입니다."}}
    cid, _ = creds(provider)
    if not cid:
        return {{"ok": False, "error": provider + " 로그인 키가 설정되지 않았습니다."}}
    P = PROVIDERS[provider]
    state = sign("rt:" + (redirect or SITE), 600)
    url = (P["auth"] + "?response_type=code&client_id=" + cid +
           "&redirect_uri=" + requests.utils.quote(redirect_uri(provider), safe="") +
           "&state=" + state)
    if P["scope"]:
        url += "&scope=" + requests.utils.quote(P["scope"], safe="")
    return RedirectResponse(url)

@app.get("/auth/{{provider}}/callback")
def social_callback(provider: str, code: str = "", state: str = ""):
    if provider not in PROVIDERS:
        return {{"ok": False, "error": "지원하지 않는 로그인입니다."}}
    back = verify(state or "")
    target = back[3:] if back and back.startswith("rt:") else SITE
    cid, csec = creds(provider)
    P = PROVIDERS[provider]
    try:
        tk = requests.post(P["token"], timeout=15, data={{
            "grant_type": "authorization_code", "client_id": cid, "client_secret": csec,
            "redirect_uri": redirect_uri(provider), "code": code, "state": state,
        }}, headers={{"Content-Type": "application/x-www-form-urlencoded"}}).json()
        at = tk.get("access_token")
        if not at:
            return RedirectResponse(target + "#bsm_login_error=token")

        me = requests.get(P["me"], timeout=15,
                          headers={{"Authorization": "Bearer " + at}}).json()
        if provider == "kakao":
            uid = str(me.get("id", ""))
            acc = me.get("kakao_account", {{}}) or {{}}
            email = acc.get("email", "") or ""
            name = (acc.get("profile", {{}}) or {{}}).get("nickname", "") or ""
        else:
            r0 = me.get("response", {{}}) or {{}}
            uid = str(r0.get("id", ""))
            email = r0.get("email", "") or ""
            name = r0.get("name", "") or r0.get("nickname", "") or ""
        if not uid:
            return RedirectResponse(target + "#bsm_login_error=profile")
    except Exception:
        return RedirectResponse(target + "#bsm_login_error=network")

    member_id = provider + "_" + uid
    ref = fs.collection("members").document(member_id)
    snap = ref.get()
    if not snap.exists:
        ref.set({{"provider": provider, "provider_uid": uid, "email": email, "name": name,
                 "created_at": firestore.SERVER_TIMESTAMP,
                 "last_login_at": firestore.SERVER_TIMESTAMP}})
        try:
            bq.insert_rows_json(DS + ".members", [{{
                "member_id": member_id, "provider": provider, "provider_uid": uid,
                "email": email, "name": name, "company": "", "phone": "",
                "created_at": now_iso(), "last_login_at": now_iso()}}])
        except Exception:
            pass
    else:
        ref.update({{"last_login_at": firestore.SERVER_TIMESTAMP,
                    "email": email or (snap.to_dict() or {{}}).get("email", "")}})

    return RedirectResponse(target + "#bsm_login=" + sign(member_id))

class FbIn(BaseModel):
    id_token: str

@app.post("/auth/firebase")
def auth_firebase(inp: FbIn):
    # Firebase Authentication 이 발급한 ID 토큰을 검증하고 자체 세션을 발급합니다.
    # 이메일 인증을 마치지 않은 계정은 거부합니다.
    try:
        import firebase_admin
        from firebase_admin import auth as fbauth
        if not firebase_admin._apps:
            firebase_admin.initialize_app()
        claims = fbauth.verify_id_token(inp.id_token)
    except Exception:
        return {{"ok": False, "error": "INVALID_TOKEN"}}

    if not claims.get("email_verified"):
        return {{"ok": False, "error": "EMAIL_NOT_VERIFIED"}}

    uid = claims.get("uid") or claims.get("sub", "")
    email = claims.get("email", "")
    name = claims.get("name", "") or (email.split("@")[0] if email else "")
    member_id = "email_" + uid

    ref = fs.collection("members").document(member_id)
    if not ref.get().exists:
        ref.set({{"provider": "email", "provider_uid": uid, "email": email, "name": name,
                 "created_at": firestore.SERVER_TIMESTAMP,
                 "last_login_at": firestore.SERVER_TIMESTAMP}})
        try:
            bq.insert_rows_json(DS + ".members", [{{
                "member_id": member_id, "provider": "email", "provider_uid": uid,
                "email": email, "name": name, "company": "", "phone": "",
                "created_at": now_iso(), "last_login_at": now_iso()}}])
        except Exception:
            pass
    else:
        ref.update({{"last_login_at": firestore.SERVER_TIMESTAMP, "email": email}})

    return {{"ok": True, "token": sign(member_id), "email": email, "name": name}}

@app.get("/me")
def me(authorization: str = ""):
    mid = bearer(authorization)
    if not mid:
        return {{"ok": False}}
    d = fs.collection("members").document(mid).get().to_dict() or {{}}
    return {{"ok": True, "member_id": mid, "email": d.get("email", ""),
            "name": d.get("name", ""), "provider": d.get("provider", "")}}

@app.post("/inquiry")
def inquiry(inp: InquiryIn, authorization: str = ""):
    # 가격·견적 문의는 로그인 후에만 접수합니다.
    mid = bearer(authorization)
    if not mid:
        return {{"ok": False, "error": "LOGIN_REQUIRED"}}
    d = fs.collection("members").document(mid).get().to_dict() or {{}}
    email = d.get("email", "")
    iid = "Q" + uuid.uuid4().hex[:12]
    try:
        bq.insert_rows_json(DS + ".inquiries", [{{
            "inquiry_id": iid, "member_id": mid, "tenant_id": "{BSM_TENANT}",
            "category": inp.category, "title": inp.title[:200], "body": inp.body[:4000],
            "company_name": inp.company_name[:120], "phone": inp.phone[:40],
            "contact_email": email, "channel": inp.channel, "status": "NEW",
            "created_at": now_iso()}}])
    except Exception as e:
        return {{"ok": False, "error": "SAVE_FAILED"}}

    body = ("회원 문의가 접수되었습니다.\\n\\n"
            "문의번호: " + iid + "\\n회원: " + mid + " (" + str(d.get("name", "")) + ")\\n"
            "이메일: " + email + "\\n회사: " + inp.company_name + "\\n연락처: " + inp.phone + "\\n"
            "구분: " + inp.category + "\\n제목: " + inp.title + "\\n\\n" + inp.body)
    res = send_mail("[BSM " + inp.category + " 문의] " + (inp.title or iid)[:40], body, reply_to=email)

    return {{"ok": True, "inquiry_id": iid, "email_sent": res["sent"],
            "message": ("문의가 접수되었습니다. 문의번호 " + iid + " 로 " +
                        (email or "등록하신 이메일") + " 에 회신드립니다.")}}

class LeadIn(BaseModel):
    company: str
    contact_name: str = ""
    phone: str = ""
    email: str = ""
    homepage: str = ""
    memo: str = ""
    source: str = "site"

@app.post("/lead")
def lead(inp: LeadIn):
    row = inp.model_dump()
    row.update({{"lead_id": "LD" + uuid.uuid4().hex[:12], "tenant_id": "{BSM_TENANT}",
                "created_at": now_iso()}})
    bq.insert_rows_json(DS + ".leads", [row])
    send_mail("[BSM 무료 시작 신청] " + inp.company[:40],
              json.dumps(row, ensure_ascii=False, indent=2), reply_to=inp.email)
    return {{"ok": True}}
''')

print("앱 파일 생성 완료:", [p.name for p in sorted(APP.iterdir())])
print("엔드포인트: /chat /escalate /inquiry /auth/{provider}/login /auth/{provider}/callback /me /flow /lead /health")
""")

code(r"""
# Cloud Run 배포. 첫 배포는 3~5분 걸립니다.
# max-instances를 낮게 잡아 비용 폭주를 막습니다.
ALLOW_ORIGINS = f"{SITE_DOMAIN},https://{PROJECT_ID}.web.app"
ENVS = (f"PROJECT_ID={PROJECT_ID},DATASET={DATASET},VERTEX_LOC={VERTEX_LOC},"
        f"GEN_MODEL={GEN_MODEL},EMBED_MODEL={EMBED_MODEL},EMBED_DIM={EMBED_DIM},"
        f"MIN_RRF={MIN_RRF},SITE_DOMAIN={SITE_DOMAIN},ALLOW_ORIGINS={ALLOW_ORIGINS},"
        f"NOTIFY_UNANSWERED=true")
SECRETS = ("SESSION_SECRET=SESSION_SECRET:latest,"
           "KAKAO_CLIENT_ID=KAKAO_CLIENT_ID:latest,"
           "KAKAO_CLIENT_SECRET=KAKAO_CLIENT_SECRET:latest,"
           "NAVER_CLIENT_ID=NAVER_CLIENT_ID:latest,"
           "NAVER_CLIENT_SECRET=NAVER_CLIENT_SECRET:latest,"
           "SMTP_USER=SMTP_USER:latest,SMTP_PASS=SMTP_PASS:latest")

!gcloud run deploy {SERVICE_NAME} \
  --source /content/bsm_api \
  --region {LOCATION} \
  --allow-unauthenticated \
  --memory 512Mi --cpu 1 \
  --min-instances 0 --max-instances 3 \
  --concurrency 20 --timeout 120 \
  --set-env-vars {ENVS} \
  --set-secrets {SECRETS} \
  -q

API_URL = !gcloud run services describe {SERVICE_NAME} --region {LOCATION} --format="value(status.url)"
API_URL = API_URL[0].strip()

# 소셜 로그인 Redirect URI를 만들려면 서비스가 자기 주소를 알아야 합니다.
!gcloud run services update {SERVICE_NAME} --region {LOCATION} \
  --update-env-vars API_BASE={API_URL} -q > /dev/null

print("\nAPI 주소:", API_URL)
print("\n각 개발자 콘솔에 아래 Redirect URI를 등록하세요.")
print("  카카오:", API_URL + "/auth/kakao/callback")
print("  네이버:", API_URL + "/auth/naver/callback")
""")

code(r"""
# 배포 확인
import requests, json as _json

print(requests.get(f"{API_URL}/health", timeout=30).json())

# (1) 아는 질문 — 바로 답해야 합니다.
r = requests.post(f"{API_URL}/chat", timeout=120,
                  json={"tenant_id": BSM_TENANT, "question": "분양 조건과 가격을 알려주세요"})
print("\n[아는 질문]"); print(_json.dumps(r.json(), ensure_ascii=False, indent=2))

# (2) 모르는 질문 — escalate=true 로 담당자 전달 흐름이 떠야 합니다.
r = requests.post(f"{API_URL}/chat", timeout=120,
                  json={"tenant_id": BSM_TENANT,
                        "question": "저희 회사 ERP와 연동하려면 개발 기간이 얼마나 걸리나요?"})
d = r.json(); print("\n[모르는 질문] escalate =", d.get("escalate")); print(d.get("answer"))

# (3) 상담 시나리오
print("\n[시나리오 노드]", list(requests.get(f"{API_URL}/flow", timeout=30).json()["nodes"].keys()))

# (4) 담당자 전달 — 실제로 메일이 발송됩니다. 테스트할 때만 주석을 푸세요.
# r = requests.post(f"{API_URL}/escalate", timeout=120, json={
#     "session_id": "test", "question": "ERP 연동 개발 기간이 궁금합니다",
#     "contact_email": "본인메일@example.com", "memo": "테스트 발송",
#     "history": [{"role": "user", "content": "ERP 연동 가능한가요?"}]})
# print(_json.dumps(r.json(), ensure_ascii=False, indent=2))
""")

md("""
## 15. 홈페이지와 위젯 배포

Firebase Hosting에 올릴 파일을 만듭니다.

- `index.html` — 회사 소개, 가격, 데모 챗봇, 문의처
- `widget.js` — 고객사 홈페이지에 붙이는 스크립트 한 줄의 실체
- `firebase.json` — 호스팅 설정

Cloud Run 서비스에 `run.invoker` 권한이 모두에게 열려 있으므로 브라우저에서 바로 호출됩니다.
""")

code(r"""
from pathlib import Path
PUB = Path("/content/public"); PUB.mkdir(parents=True, exist_ok=True)

# ── widget.js : 해피톡 형태의 버튼 시나리오 + 자유 질문 + 담당자 전달 + 회원 문의 ──
(PUB / "widget.js").write_text('''
(function(){
  var me = document.currentScript;
  var TENANT = (me && me.getAttribute("data-tenant")) || "''' + BSM_TENANT + '''";
  var MODE   = (me && me.getAttribute("data-mode")) || "bubble";   // bubble | center
  var FB_KEY = "''' + FIREBASE_API_KEY + '''";   // Firebase 웹 API 키 (없으면 이메일 가입 숨김)
  var IDT    = "https://identitytoolkit.googleapis.com/v1/accounts:";
  var API    = "''' + API_URL + '''";
  var PHONE  = "''' + COMPANY["phone"] + '''";
  var MAILTO = "''' + COMPANY["email"] + '''";
  var SID    = "s" + Math.random().toString(36).slice(2, 10);
  var LS_KEY = "bsm_token";

  var css = document.createElement("style");
  css.textContent = [
   ".bw{position:fixed;right:20px;bottom:20px;z-index:99999;font-family:system-ui,-apple-system,'Malgun Gothic',sans-serif}",
   ".bw-open{background:#8C2F39;color:#fff;border:none;border-radius:28px;padding:14px 20px;font-size:15px;font-weight:600;cursor:pointer;box-shadow:0 6px 20px rgba(0,0,0,.22)}",
   ".bw-box{display:none;flex-direction:column;width:352px;height:520px;max-height:78vh;background:#fff;border:1px solid #E2DFD8;border-radius:10px;overflow:hidden;box-shadow:0 14px 44px rgba(0,0,0,.22)}",
   ".bw-hd{background:#14161A;color:#fff;padding:12px 14px;font-size:14px;font-weight:600;display:flex;align-items:center;gap:8px}",
   ".bw-hd .who{font-size:11px;font-weight:400;color:#9B978F;margin-left:auto}",
   ".bw-hd .x{cursor:pointer;opacity:.6;font-size:19px;line-height:1;padding-left:8px}",
   ".bw-log{flex:1;overflow-y:auto;padding:14px;display:flex;flex-direction:column;gap:10px;background:#F8F7F5}",
   ".bw-m{max-width:88%;font-size:13.5px;line-height:1.62;padding:9px 12px;border-radius:8px;white-space:pre-wrap;word-break:break-word}",
   ".bw-b{background:#fff;border:1px solid #E2DFD8;color:#14161A;align-self:flex-start}",
   ".bw-u{background:#8C2F39;color:#fff;align-self:flex-end}",
   ".bw-sys{align-self:center;font-size:11.5px;color:#8A8E93;text-align:center;max-width:100%}",
   ".bw-src{font-size:11px;color:#6A6E73;align-self:flex-start;padding-left:2px}",
   ".bw-btns{display:flex;flex-direction:column;gap:6px;align-self:stretch}",
   ".bw-btn{background:#fff;border:1px solid #D9D5CC;border-radius:6px;padding:10px 12px;font-size:13.5px;cursor:pointer;text-align:center;color:#14161A;font-family:inherit}",
   ".bw-btn:hover{border-color:#8C2F39;color:#8C2F39}",
   ".bw-btn.pri{background:#8C2F39;color:#fff;border-color:#8C2F39}",
   ".bw-btn.ka{background:#FEE500;border-color:#FEE500;color:#181600;font-weight:600}",
   ".bw-btn.na{background:#03C75A;border-color:#03C75A;color:#fff;font-weight:600}",
   ".bw-nav{display:flex;gap:6px;justify-content:center;padding:8px 12px;border-top:1px solid #EFEDE8;background:#fff}",
   ".bw-nav button{background:#fff;border:1px solid #E2DFD8;border-radius:14px;padding:5px 12px;font-size:12px;cursor:pointer;color:#4A5056;font-family:inherit}",
   ".bw-nav button:hover{border-color:#8C2F39;color:#8C2F39}",
   ".bw-in{display:flex;gap:6px;padding:10px;border-top:1px solid #E2DFD8;background:#fff}",
   ".bw-in input{flex:1;border:1px solid #E2DFD8;border-radius:5px;padding:9px 10px;font-size:13.5px;min-width:0;font-family:inherit}",
   ".bw-in button{background:#8C2F39;color:#fff;border:none;border-radius:5px;padding:9px 14px;font-size:13.5px;cursor:pointer;font-family:inherit}",
   ".bw-in button:disabled{background:#B9B5AE}",
   ".bw-note{font-size:10.5px;color:#8A8E93;padding:0 12px 9px;background:#fff;line-height:1.5}",
   ".bw-form{align-self:stretch;background:#fff;border:1px solid #E2DFD8;border-radius:8px;padding:12px;display:flex;flex-direction:column;gap:7px}",
   ".bw-form label{font-size:11.5px;color:#6A6E73}",
   ".bw-form input,.bw-form textarea{border:1px solid #E2DFD8;border-radius:5px;padding:8px 9px;font-size:13px;font-family:inherit;width:100%}",
   ".bw-form textarea{min-height:64px;resize:vertical}",
   ".bw.ctr{right:0;bottom:0;top:0;left:0;display:none;align-items:center;justify-content:center;background:rgba(20,22,26,.58);padding:16px}",
   ".bw.ctr.on{display:flex}",
   ".bw.ctr .bw-box{width:420px;max-width:100%;height:620px;max-height:86vh}",
   ".bw.ctr .bw-open{display:none}"
  ].join("");
  document.head.appendChild(css);

  var root = document.createElement("div");
  root.className = (MODE === "center") ? "bw ctr" : "bw";
  root.innerHTML =
    '<div class="bw-box" id="bwBox">' +
      '<div class="bw-hd">BSM AI 상담<span class="who" id="bwWho"></span><span class="x" id="bwX">&times;</span></div>' +
      '<div class="bw-log" id="bwLog"></div>' +
      '<div class="bw-nav"><button id="bwBack">이전으로</button><button id="bwHome">처음으로</button><button id="bwEnd">종료하기</button></div>' +
      '<form class="bw-in" id="bwF"><input id="bwQ" placeholder="버튼을 선택하거나 메시지를 입력해 주세요." autocomplete="off"><button id="bwSend">전송</button></form>' +
      '<div class="bw-note">AI가 생성한 답변입니다. 답변이 어려운 문의는 담당자에게 전달해 회신해 드립니다.</div>' +
    '</div>' +
    '<button class="bw-open" id="bwOpen">AI 상담</button>';
  document.body.appendChild(root);

  var box = root.querySelector("#bwBox"), log = root.querySelector("#bwLog"),
      who = root.querySelector("#bwWho"), inp = root.querySelector("#bwQ"),
      send = root.querySelector("#bwSend");

  var history = [];     // 자유 대화 기록
  var stack   = [];     // 화면 스택 (이전으로)
  var lastQ   = "";
  var member  = null;
  var FLOW    = null;

  function token(){ try { return localStorage.getItem(LS_KEY) || ""; } catch(e){ return ""; } }
  function setToken(t){ try { t ? localStorage.setItem(LS_KEY, t) : localStorage.removeItem(LS_KEY); } catch(e){} }

  function el(cls, text){ var d=document.createElement("div"); d.className=cls; if(text!=null) d.textContent=text; log.appendChild(d); log.scrollTop=log.scrollHeight; return d; }
  function bot(t){ return el("bw-m bw-b", t); }
  function user(t){ return el("bw-m bw-u", t); }
  function sys(t){ return el("bw-m bw-sys", t); }
  function clear(){ log.innerHTML=""; }

  function buttons(items){
    var w=document.createElement("div"); w.className="bw-btns";
    items.forEach(function(it){
      var b=document.createElement("button");
      b.type="button"; b.className="bw-btn"+(it.style?" "+it.style:""); b.textContent=it.label;
      b.onclick=it.onClick;
      w.appendChild(b);
    });
    log.appendChild(w); log.scrollTop=log.scrollHeight; return w;
  }

  // ── 화면 ────────────────────────────────────────────────
  function push(fn){ stack.push(fn); fn(); }
  function back(){ if(stack.length>1){ stack.pop(); var f=stack[stack.length-1]; clear(); f(); } else home(); }
  function home(){ stack=[]; clear(); push(screenHome); }

  function screenHome(){
    bot("안녕하세요. BSM AI 상담 챗봇입니다.\\n홈페이지와 카카오톡 등 여러 채널의 고객 문의를 AI가 대신 답하도록 만들어 드립니다.\\n\\n원하시는 항목을 선택해 주세요.");
    buttons([
      {label:"신규 도입 문의", onClick:function(){ push(screenIntro); }},
      {label:"가격 · 견적 문의", onClick:function(){ push(screenPriceGate); }},
      {label:"상담 시작하기", style:"pri", onClick:function(){ push(screenFree); }}
    ]);
  }

  function screenIntro(){
    clear();
    bot("어떤 것을 만들고 싶으신지 알려주시면 바로 상담해 드립니다.\\n예를 들어 이렇게 물어보셔도 됩니다.");
    buttons([
      {label:"쇼핑몰 주문·배송 문의를 자동으로 답하게 하고 싶어요", onClick:function(){ ask(this.textContent); }},
      {label:"사내 규정 PDF를 직원이 물어보게 하고 싶어요", onClick:function(){ ask(this.textContent); }},
      {label:"홈페이지에 24시간 상담 챗봇을 붙이고 싶어요", onClick:function(){ ask(this.textContent); }},
      {label:"직접 입력할게요", style:"pri", onClick:function(){ push(screenFree); }}
    ]);
  }

  function screenFree(){
    clear();
    bot("만들고 싶으신 내용을 편하게 적어주세요.\\n제가 아는 범위는 바로 답해 드리고, 어려운 내용은 담당자에게 전달해 회신해 드립니다.");
    inp.focus();
  }

  // ── 가격 문의: 회원가입/로그인 후 접수 ──────────────────
  function screenPriceGate(){
    clear();
    if(member){ return screenInquiry(); }
    bot("가격과 견적은 회원 확인 후 안내해 드립니다.\\n아래 방법 중 편하신 것으로 시작하세요.");
    var opts = [
      {label:"카카오로 시작하기", style:"ka", onClick:function(){ login("kakao"); }},
      {label:"네이버로 시작하기", style:"na", onClick:function(){ login("naver"); }}
    ];
    if(FB_KEY){ opts.push({label:"이메일로 가입 · 로그인", onClick:function(){ push(screenEmailAuth); }}); }
    opts.push({label:"로그인 없이 전화 상담", onClick:function(){ location.href="tel:"+PHONE; }});
    buttons(opts);
    sys("가입 시 이름과 이메일만 수집하며, 견적 회신 목적으로만 사용합니다.");
  }

  // ── 이메일 인증 가입 (Firebase Authentication) ──────────
  function idt(method, body){
    return fetch(IDT + method + "?key=" + FB_KEY, {
      method:"POST", headers:{"Content-Type":"application/json"},
      body:JSON.stringify(body)
    }).then(function(r){ return r.json(); });
  }

  function fbFinish(idToken){
    return post("/auth/firebase", {id_token:idToken}).then(function(d){
      if(d && d.ok){
        setToken(d.token);
        member = {name:d.name, email:d.email};
        who.textContent = (d.name || "회원") + " 님";
        stack=[]; clear(); push(screenInquiry);
      } else if(d && d.error === "EMAIL_NOT_VERIFIED"){
        sys("이메일 인증이 아직 완료되지 않았습니다. 메일함의 인증 링크를 눌러주세요.");
      } else {
        sys("로그인 처리에 실패했습니다. 잠시 후 다시 시도해 주세요.");
      }
    });
  }

  function screenEmailAuth(){
    clear();
    bot("이메일로 간편하게 시작하실 수 있습니다.\\n처음이시면 회원가입을 눌러주세요. 인증 메일이 발송됩니다.");
    var f=document.createElement("div"); f.className="bw-form";
    f.innerHTML =
      '<label>이메일</label><input id="bwFE" type="email" placeholder="name@example.com" autocomplete="username">' +
      '<label>비밀번호 (6자 이상)</label><input id="bwFP" type="password" placeholder="••••••" autocomplete="current-password">';
    log.appendChild(f);
    var E=function(){ return (f.querySelector("#bwFE").value||"").trim(); };
    var P=function(){ return f.querySelector("#bwFP").value||""; };

    buttons([
      {label:"로그인", style:"pri", onClick:function(){
        var btn=this; btn.disabled=true;
        idt("signInWithPassword", {email:E(), password:P(), returnSecureToken:true})
        .then(function(d){
          if(d.error){ sys(fbErr(d.error.message)); btn.disabled=false; return; }
          return idt("lookup", {idToken:d.idToken}).then(function(u){
            var ok = u.users && u.users[0] && u.users[0].emailVerified;
            if(!ok){
              sys("이메일 인증이 필요합니다. 인증 메일을 다시 보내드릴까요?");
              buttons([{label:"인증 메일 다시 보내기", onClick:function(){
                idt("sendOobCode", {requestType:"VERIFY_EMAIL", idToken:d.idToken})
                .then(function(){ sys("인증 메일을 보냈습니다. 확인 후 다시 로그인해 주세요."); });
              }}]);
              btn.disabled=false; return;
            }
            return fbFinish(d.idToken);
          });
        })["catch"](function(){ sys("네트워크 오류가 발생했습니다."); btn.disabled=false; });
      }},
      {label:"회원가입", onClick:function(){
        var btn=this; btn.disabled=true;
        idt("signUp", {email:E(), password:P(), returnSecureToken:true})
        .then(function(d){
          if(d.error){ sys(fbErr(d.error.message)); btn.disabled=false; return; }
          return idt("sendOobCode", {requestType:"VERIFY_EMAIL", idToken:d.idToken})
          .then(function(){
            bot("가입이 접수되었습니다.\\n" + E() + " 로 인증 메일을 보냈습니다.\\n" +
                "메일의 링크를 누르신 뒤 로그인 버튼을 눌러주세요.");
            btn.disabled=false;
          });
        })["catch"](function(){ sys("네트워크 오류가 발생했습니다."); btn.disabled=false; });
      }},
      {label:"비밀번호 재설정 메일", onClick:function(){
        if(!E()){ sys("이메일을 입력해 주세요."); return; }
        idt("sendOobCode", {requestType:"PASSWORD_RESET", email:E()})
        .then(function(){ sys("비밀번호 재설정 메일을 보냈습니다."); });
      }}
    ]);
  }

  function fbErr(code){
    var m={EMAIL_EXISTS:"이미 가입된 이메일입니다. 로그인을 눌러주세요.",
           INVALID_LOGIN_CREDENTIALS:"이메일 또는 비밀번호가 올바르지 않습니다.",
           EMAIL_NOT_FOUND:"가입되지 않은 이메일입니다.",
           INVALID_PASSWORD:"비밀번호가 올바르지 않습니다.",
           WEAK_PASSWORD:"비밀번호는 6자 이상이어야 합니다.",
           INVALID_EMAIL:"이메일 형식을 확인해 주세요.",
           TOO_MANY_ATTEMPTS_TRY_LATER:"시도가 많습니다. 잠시 후 다시 시도해 주세요."};
    for(var k in m){ if(code && code.indexOf(k)===0) return m[k]; }
    return "처리에 실패했습니다. 다시 시도해 주세요.";
  }

  function login(provider){
    location.href = API + "/auth/" + provider + "/login?redirect=" + encodeURIComponent(location.href.split("#")[0]);
  }

  function screenInquiry(){
    clear();
    bot("환영합니다" + (member && member.name ? ", " + member.name + "님" : "") + ".\\n아래 내용을 남겨주시면 담당자가 견적과 함께 회신드립니다.");
    var f=document.createElement("div"); f.className="bw-form";
    f.innerHTML =
      '<label>회사명</label><input id="bwC" placeholder="예: 비에스엠">' +
      '<label>연락처</label><input id="bwP" placeholder="010-0000-0000">' +
      '<label>문의 내용</label><textarea id="bwB" placeholder="어떤 챗봇이 필요하신지, 예상 문의량이 어느 정도인지 적어주세요."></textarea>';
    log.appendChild(f);
    buttons([{label:"견적 요청 보내기", style:"pri", onClick:function(){
      var body=(f.querySelector("#bwB").value||"").trim();
      if(!body){ sys("문의 내용을 입력해 주세요."); return; }
      this.disabled=true;
      post("/inquiry", {category:"PRICE", title:"가격·견적 문의",
        body:body, company_name:f.querySelector("#bwC").value||"",
        phone:f.querySelector("#bwP").value||"", channel:"web"}, true)
      .then(function(d){
        if(d && d.ok){ bot(d.message); if(!d.email_sent) sys("메일 발송이 지연될 수 있어 담당자가 별도로 확인합니다."); }
        else if(d && d.error==="LOGIN_REQUIRED"){ setToken(""); member=null; screenPriceGate(); }
        else { bot("접수 중 오류가 발생했습니다. 전화 "+PHONE+"로 문의해 주세요."); }
      });
    }}]);
  }

  // ── 담당자 전달 (답변 불가 시) ──────────────────────────
  function screenEscalate(question){
    var f=document.createElement("div"); f.className="bw-form";
    f.innerHTML =
      '<label>회신받으실 이메일</label><input id="bwE" type="email" placeholder="name@example.com">' +
      '<label>덧붙일 내용 (선택)</label><textarea id="bwM" placeholder="추가로 알려주실 내용이 있으면 적어주세요."></textarea>';
    log.appendChild(f);
    buttons([{label:"담당자에게 전달하기", style:"pri", onClick:function(){
      var email=(f.querySelector("#bwE").value||"").trim();
      if(!/^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test(email)){ sys("이메일 형식을 확인해 주세요."); return; }
      this.disabled=true;
      post("/escalate", {session_id:SID, question:question, contact_email:email,
                         memo:f.querySelector("#bwM").value||"", history:history.slice(-12)})
      .then(function(d){
        if(d && d.ok){
          bot(d.message);
          if(!d.email_sent) sys("메일 발송이 지연될 수 있으나 문의는 정상 접수되었습니다.");
        } else {
          bot("접수에 실패했습니다. "+MAILTO+" 으로 직접 보내주시거나 "+PHONE+"로 전화 주세요.");
        }
      });
    }}]);
    log.scrollTop=log.scrollHeight;
  }

  // ── 통신 ────────────────────────────────────────────────
  function post(path, body, auth){
    var h={"Content-Type":"application/json"};
    if(auth && token()) h["Authorization"]="Bearer "+token();
    return fetch(API+path,{method:"POST",headers:h,body:JSON.stringify(body)})
      .then(function(r){ return r.json(); })["catch"](function(){ return null; });
  }

  function ask(q){
    if(!q) return;
    user(q); history.push({role:"user", content:q});
    lastQ=q; inp.value=""; inp.disabled=true; send.disabled=true;
    var bub=bot("답변을 준비하고 있습니다...");
    post("/chat", {tenant_id:TENANT, question:q, session_id:SID, history:history.slice(-8)})
    .then(function(d){
      if(!d){ bub.textContent="연결이 원활하지 않습니다. 전화 "+PHONE+"로 문의해 주세요."; return; }
      bub.textContent=d.answer;
      history.push({role:"assistant", content:d.answer});
      if(d.sources && d.sources.length) el("bw-src","근거: "+d.sources.join(", "));
      if(d.escalate){ screenEscalate(q); return; }
      if(d.action==="PRICE"){ buttons([{label:"가격·견적 문의 남기기", style:"pri", onClick:function(){ push(screenPriceGate); }}]); }
      else if(d.action==="BUY"){ buttons([{label:"지금 신청하기", style:"pri", onClick:function(){ window.open("''' + CAFE24_URL + '''","_blank"); }}]); }
      else if(d.action==="TRIAL"){ buttons([{label:"무료로 시작하기", style:"pri", onClick:function(){ push(screenPriceGate); }}]); }
      else if(d.action==="CONTACT"){ buttons([{label:"전화 상담", onClick:function(){ location.href="tel:"+PHONE; }},
                                              {label:"담당자에게 메일로 전달", onClick:function(){ screenEscalate(q); }}]); }
    })["finally"](function(){ inp.disabled=false; send.disabled=false; inp.focus(); });
  }

  // ── 이벤트 ──────────────────────────────────────────────
  function openChat(){
    if(MODE==="center"){ root.classList.add("on"); box.style.display="flex"; }
    else { box.style.display="flex"; root.querySelector("#bwOpen").style.display="none"; }
    if(!log.childNodes.length) home();
    setTimeout(function(){ inp.focus(); }, 60);
  }
  function closeChat(){
    if(MODE==="center"){ root.classList.remove("on"); }
    else { box.style.display="none"; root.querySelector("#bwOpen").style.display=""; }
  }
  window.BSMChat = {open:openChat, close:closeChat};

  root.querySelector("#bwOpen").onclick = openChat;
  root.querySelector("#bwX").onclick = closeChat;
  root.addEventListener("click", function(e){ if(MODE==="center" && e.target===root) closeChat(); });
  document.addEventListener("keydown", function(e){ if(e.key==="Escape") closeChat(); });
  root.querySelector("#bwBack").onclick=back;
  root.querySelector("#bwHome").onclick=home;
  root.querySelector("#bwEnd").onclick=function(){
    clear(); bot("상담을 종료했습니다. 이용해 주셔서 감사합니다.\\n추가 문의는 전화 "+PHONE+" 또는 메일 "+MAILTO+" 로 주세요.");
    buttons([{label:"다시 시작하기", onClick:home}]);
  };
  root.querySelector("#bwF").onsubmit=function(e){ e.preventDefault(); ask((inp.value||"").trim()); };

  // 소셜 로그인 복귀 처리
  (function(){
    var h=location.hash||"";
    if(h.indexOf("bsm_login=")>-1){
      setToken(h.split("bsm_login=")[1].split("&")[0]);
      history_replace();
      setTimeout(function(){ openChat(); stack=[]; clear(); push(screenPriceGate); }, 500);
    } else if(h.indexOf("bsm_login_error=")>-1){
      history_replace();
      setTimeout(function(){ openChat(); clear();
        bot("로그인이 완료되지 않았습니다. 다시 시도해 주세요."); push(screenPriceGate); }, 300);
    }
    function history_replace(){
      try { window.history.replaceState(null,"",location.pathname+location.search); } catch(e){}
    }
  })();

  // 로그인 상태 확인
  if(token()){
    fetch(API+"/me",{headers:{"Authorization":"Bearer "+token()}})
      .then(function(r){ return r.json(); })
      .then(function(d){
        if(d && d.ok){ member=d; who.textContent=(d.name||"회원")+" 님"; }
        else setToken("");
      })["catch"](function(){});
  }
})();
''')

# ── index.html : AI노마드챗봇 공식 홈페이지 ──────────────────────
(PUB / "index.html").write_text(f'''<!doctype html>
<html lang="ko"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{BRAND} — 기업용 하이브리드 RAG 상담 챗봇</title>
<meta name="description" content="PDF·홈페이지·FAQ를 학습해 24시간 고객 문의에 답하는 기업 전용 AI 챗봇. 무료로 시작하고 해결한 만큼만 결제하세요.">
<meta property="og:title" content="{BRAND}">
<meta property="og:description" content="근거를 찾아 답하고, 모르면 담당자에게 넘깁니다.">
<style>
*{{box-sizing:border-box}}
:root{{--ink:#14161A;--ink2:#3F464D;--mut:#6E747A;--line:#E6E3DC;--bg:#fff;--soft:#F7F6F3;
       --acc:#8C2F39;--acc2:#B5424D;--ok:#1E6A5B}}
html{{scroll-behavior:smooth}}
body{{margin:0;font-family:system-ui,-apple-system,"Malgun Gothic","Apple SD Gothic Neo",sans-serif;
      color:var(--ink);line-height:1.72;background:var(--bg);-webkit-font-smoothing:antialiased}}
.w{{max-width:1120px;margin:0 auto;padding:0 24px}}
a{{color:inherit}}
h1,h2,h3{{letter-spacing:-.02em;text-wrap:balance}}

/* 내비 */
nav{{position:sticky;top:0;z-index:60;background:rgba(255,255,255,.92);backdrop-filter:blur(8px);
     border-bottom:1px solid var(--line)}}
nav .w{{display:flex;align-items:center;gap:26px;padding:14px 24px}}
.lg{{font-weight:800;font-size:17px;letter-spacing:-.03em;margin-right:auto;white-space:nowrap}}
.lg i{{font-style:normal;color:var(--acc)}}
nav a.mn{{color:var(--ink2);text-decoration:none;font-size:14.5px;font-weight:500}}
nav a.mn:hover{{color:var(--acc)}}
.btn{{display:inline-block;padding:11px 20px;border-radius:8px;font-size:14.5px;font-weight:600;
      text-decoration:none;border:1px solid transparent;cursor:pointer;font-family:inherit;line-height:1.4}}
.b-pri{{background:var(--acc);color:#fff}} .b-pri:hover{{background:#75262f}}
.b-out{{background:#fff;color:var(--ink);border-color:var(--line)}} .b-out:hover{{border-color:var(--acc);color:var(--acc)}}
.b-lg{{padding:16px 34px;font-size:16.5px;border-radius:10px}}

/* 히어로 */
header{{padding:76px 0 66px;text-align:center;background:
   radial-gradient(1200px 420px at 50% -120px, #F3EAEA 0%, rgba(255,255,255,0) 70%)}}
.eyebrow{{display:inline-block;font-size:12.5px;font-weight:700;letter-spacing:.1em;color:var(--acc);
   background:#F6EAEA;border-radius:999px;padding:6px 14px;margin-bottom:22px}}
header h1{{font-size:clamp(32px,5.2vw,54px);line-height:1.2;margin:0 0 20px;font-weight:800}}
header p.sub{{font-size:clamp(15.5px,2vw,18px);color:var(--ink2);max-width:52ch;margin:0 auto 34px}}
.cta{{display:flex;gap:12px;justify-content:center;flex-wrap:wrap}}
.hint{{margin-top:18px;font-size:13px;color:var(--mut)}}
.strip{{margin-top:52px;border-top:1px solid var(--line);padding-top:22px;display:flex;gap:28px;
   justify-content:center;flex-wrap:wrap;font-size:12.5px;letter-spacing:.08em;color:var(--mut);font-weight:600}}

section{{padding:78px 0;border-top:1px solid var(--line);scroll-margin-top:72px}}
.sec-lab{{font-size:12.5px;font-weight:700;letter-spacing:.12em;color:var(--acc);margin:0 0 12px}}
h2{{font-size:clamp(24px,3.4vw,36px);margin:0 0 12px;font-weight:800;line-height:1.3}}
.lede{{color:var(--ink2);max-width:60ch;margin:0 0 38px;font-size:16px}}
.center{{text-align:center}} .center .lede{{margin-left:auto;margin-right:auto}}

.grid4{{display:grid;grid-template-columns:repeat(auto-fit,minmax(232px,1fr));gap:18px}}
.card{{background:var(--soft);border:1px solid var(--line);border-radius:12px;padding:26px 24px}}
.card h3{{margin:0 0 9px;font-size:17px;font-weight:700}}
.card p{{margin:0;font-size:14.5px;color:var(--ink2);line-height:1.66}}
.card .ic{{font-size:12px;font-weight:700;letter-spacing:.1em;color:var(--acc);margin-bottom:12px}}

/* 하이브리드 RAG 흐름 */
.flow{{display:grid;gap:12px;max-width:820px;margin:0 auto}}
.frow{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
.fbox{{background:#fff;border:1px solid var(--line);border-radius:10px;padding:16px 18px}}
.fbox .t{{font-size:12px;font-weight:700;letter-spacing:.08em;color:var(--acc);margin-bottom:6px}}
.fbox .d{{font-size:14px;color:var(--ink2);line-height:1.6}}
.fmid{{background:var(--ink);color:#fff;border-radius:10px;padding:14px 18px;text-align:center;
   font-weight:700;font-size:15px}}
.fmid small{{display:block;font-weight:400;font-size:13px;color:#A9A6A0;margin-top:4px}}
.farrow{{text-align:center;color:#C7C3BB;font-size:15px;line-height:1}}
.fsplit{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
.fend{{border-radius:10px;padding:18px;border:1px solid var(--line)}}
.fend.ok{{background:#E9F2EF;border-color:#BFDCD3}}
.fend.no{{background:#F8EDED;border-color:#E5C9CB}}
.fend h4{{margin:0 0 7px;font-size:15px}}
.fend.ok h4{{color:var(--ok)}} .fend.no h4{{color:var(--acc)}}
.fend p{{margin:0;font-size:13.5px;color:var(--ink2);line-height:1.62}}

/* 요금 */
.plans{{display:grid;grid-template-columns:repeat(auto-fit,minmax(222px,1fr));gap:16px;align-items:start}}
.plan{{border:1px solid var(--line);border-radius:12px;padding:24px 22px;background:#fff}}
.plan.hl{{border:2px solid var(--acc);box-shadow:0 10px 30px -20px rgba(140,47,57,.5)}}
.plan .nm{{font-size:12.5px;font-weight:700;letter-spacing:.1em;color:var(--mut)}}
.plan.hl .nm{{color:var(--acc)}}
.plan .pr{{font-size:29px;font-weight:800;margin:10px 0 2px}}
.plan .pr span{{font-size:14px;font-weight:400;color:var(--mut)}}
.plan .vat{{font-size:12.5px;color:var(--mut)}}
.plan ul{{list-style:none;padding:0;margin:16px 0 0}}
.plan li{{font-size:14px;color:var(--ink2);padding:4px 0 4px 18px;position:relative}}
.plan li:before{{content:"";position:absolute;left:0;top:13px;width:8px;height:1.5px;background:#C7C3BB}}

.steps{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:18px;counter-reset:st}}
.step{{border-top:2px solid var(--acc);padding-top:16px}}
.step .n{{font-size:12px;font-weight:700;color:var(--acc);letter-spacing:.1em;margin-bottom:8px}}
.step h3{{margin:0 0 7px;font-size:16px}}
.step p{{margin:0;font-size:14px;color:var(--ink2)}}

.faq{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}}
.fq{{border:1px solid var(--line);border-radius:10px;padding:20px 22px;background:#fff}}
.fq h3{{margin:0 0 7px;font-size:15px}}
.fq p{{margin:0;font-size:14px;color:var(--ink2);line-height:1.65}}

.band{{background:var(--ink);color:#fff;text-align:center;padding:70px 0;border:0}}
.band h2{{color:#fff}} .band p{{color:#B7B3AC;max-width:52ch;margin:0 auto 30px}}

.cc{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px}}
.cc .b{{border:1px solid var(--line);border-radius:12px;padding:24px;background:var(--soft)}}
.cc .k{{font-size:12px;font-weight:700;letter-spacing:.1em;color:var(--acc);margin-bottom:10px}}
.cc .v{{font-size:20px;font-weight:700;word-break:break-all}}
.cc .v a{{text-decoration:none}} .cc p{{margin:6px 0 0;font-size:13.5px;color:var(--mut)}}

footer{{background:var(--ink);color:#8E8B85;padding:44px 0;font-size:13.5px;line-height:1.8}}
footer a{{color:#C9C5BE}}
footer .top{{color:#fff;font-weight:800;font-size:16px;margin-bottom:10px}}
@media (max-width:760px){{
  nav a.mn{{display:none}}
  .frow,.fsplit{{grid-template-columns:1fr}}
}}
</style></head><body>

<nav><div class="w">
  <span class="lg">AI<i>노마드</i>챗봇</span>
  <a class="mn" href="#feature">기능</a>
  <a class="mn" href="#tech">동작 방식</a>
  <a class="mn" href="#price">요금</a>
  <a class="mn" href="#faq">FAQ</a>
  <a class="mn" href="#contact">문의</a>
  <button class="btn b-pri" onclick="openChat()">상담하기</button>
</div></nav>

<header><div class="w">
  <span class="eyebrow">HYBRID RAG · 24시간 AI 상담</span>
  <h1>고객 문의, 이제<br>AI가 먼저 답합니다</h1>
  <p class="sub">PDF·홈페이지·FAQ를 연결하면 우리 회사 전용 상담 챗봇이 됩니다.
     근거를 찾아 답하고, 모르면 지어내지 않고 담당자에게 넘깁니다.</p>
  <div class="cta">
    <button class="btn b-pri b-lg" onclick="openChat()">AI 상담 시작하기</button>
    <a class="btn b-out b-lg" href="#price">요금 보기</a>
  </div>
  <p class="hint">무료로 시작 · 카드 등록 없이 월 100건까지</p>
  <div class="strip"><span>GOOGLE CLOUD</span><span>BIGQUERY</span><span>GEMINI</span>
    <span>HYBRID RAG</span><span>근거 표시</span></div>
</div></header>

<section id="feature"><div class="w center">
  <p class="sec-lab">WHY {BRAND}</p>
  <h2>답을 지어내지 않는 챗봇</h2>
  <p class="lede">고객 응대에서 가장 위험한 것은 느린 답이 아니라 틀린 답입니다.
     {BRAND}은 근거가 없으면 답하지 않습니다.</p>
  <div class="grid4" style="text-align:left">
    <div class="card"><div class="ic">01</div><h3>내 자료로 학습</h3>
      <p>상품 정보, 이용 안내 PDF, 자주 묻는 질문, 홈페이지 주소까지 그대로 넣으면 됩니다. 정리는 저희가 합니다.</p></div>
    <div class="card"><div class="ic">02</div><h3>근거를 함께 표시</h3>
      <p>어느 문서를 보고 답했는지 함께 보여줍니다. 고객도 담당자도 답변을 검증할 수 있습니다.</p></div>
    <div class="card"><div class="ic">03</div><h3>모르면 사람에게</h3>
      <p>근거를 찾지 못하면 추측하지 않고 담당자에게 전달합니다. 고객에게는 회신 예정을 안내합니다.</p></div>
    <div class="card"><div class="ic">04</div><h3>스크립트 한 줄</h3>
      <p>홈페이지에 한 줄만 붙이면 끝입니다. 카페24·워드프레스·자체 사이트 모두 같습니다.</p></div>
  </div>
</div></section>

<section id="tech"><div class="w center">
  <p class="sec-lab">HOW IT WORKS</p>
  <h2>두 개의 검색을 함께 씁니다</h2>
  <p class="lede">의미로 찾는 벡터 검색과 단어로 찾는 키워드 검색을 동시에 실행하고 RRF로 합칩니다.
     품번·규정 조항처럼 정확한 단어가 중요한 질문에 강한 이유입니다.</p>
  <div class="flow">
    <div class="fmid">고객 질문<small>홈페이지 · 카카오톡 · 상담 위젯</small></div>
    <div class="farrow">&#9660;</div>
    <div class="frow">
      <div class="fbox"><div class="t">VECTOR SEARCH</div>
        <div class="d">의미가 비슷한 문단을 찾습니다. 표현이 달라도 같은 뜻이면 걸립니다.</div></div>
      <div class="fbox"><div class="t">KEYWORD SEARCH</div>
        <div class="d">품번·모델명·조항 번호처럼 정확히 일치해야 하는 단어를 찾습니다.</div></div>
    </div>
    <div class="farrow">&#9660;</div>
    <div class="fmid">RRF 융합<small>두 결과의 순위를 합쳐 상위 근거만 남깁니다</small></div>
    <div class="farrow">&#9660;</div>
    <div class="fsplit">
      <div class="fend ok"><h4>근거 있음</h4>
        <p>Gemini가 근거만 사용해 답변을 만들고, 참고한 문서를 함께 표시합니다. 고객은 즉시 답을 받습니다.</p></div>
      <div class="fend no"><h4>근거 없음</h4>
        <p>답을 만들지 않습니다. 문의 내용을 정리해 <b>{COMPANY["email"]}</b> 담당자에게 전달하고,
           고객에게는 <b>확인 후 회신드리겠습니다</b> 라고 안내합니다.</p></div>
    </div>
  </div>
</div></section>

<section id="price"><div class="w center">
  <p class="sec-lab">PRICING</p>
  <h2>해결한 만큼만 받습니다</h2>
  <p class="lede">상담원 수도, 대화 수도 아닌 <b>해결 건수</b>가 기준입니다.
     답을 찾지 못해 담당자에게 넘긴 대화는 세지 않습니다.</p>
  <div class="plans" style="text-align:left">
    <div class="plan"><div class="nm">FREE</div><div class="pr">0<span>원 / 월</span></div>
      <div class="vat">카드 등록 없이 시작</div>
      <ul><li>해결 100건</li><li>문서 50페이지</li><li>웹 위젯</li><li>브랜드 배지 표시</li></ul></div>
    <div class="plan"><div class="nm">STARTER</div><div class="pr">39,000<span>원 / 월</span></div>
      <div class="vat">VAT 별도</div>
      <ul><li>해결 500건</li><li>문서 300페이지</li><li>웹 위젯 1채널</li><li>배지 제거</li></ul></div>
    <div class="plan hl"><div class="nm">GROWTH · 추천</div><div class="pr">99,000<span>원 / 월</span></div>
      <div class="vat">VAT 별도 · 연납 2개월 할인</div>
      <ul><li>해결 2,000건</li><li>문서 1,000페이지</li><li>카카오톡 채널 연동</li><li>주간 리포트</li></ul></div>
    <div class="plan"><div class="nm">SCALE</div><div class="pr">249,000<span>원 / 월</span></div>
      <div class="vat">VAT 별도</div>
      <ul><li>해결 8,000건</li><li>문서 5,000페이지</li><li>다채널 · API · SSO</li><li>전담 온보딩</li></ul></div>
  </div>
  <p style="margin-top:22px;font-size:14px;color:var(--ink2)">
    포함 건수 초과분은 해결당 40원입니다. ERP·CRM 연동 등 기업 맞춤 구축은
    연 {COMPANY["enterprise_from"]:,}원부터이며 별도 상담이 필요합니다.</p>
  <div class="cta" style="margin-top:26px">
    <button class="btn b-pri b-lg" onclick="openChat()">가격 문의하기</button>
    <a class="btn b-out b-lg" href="{CAFE24_URL}" target="_blank" rel="noopener">바로 신청</a>
  </div>
</div></section>

<section><div class="w center">
  <p class="sec-lab">HOW TO START</p>
  <h2>자료만 주시면 됩니다</h2>
  <p class="lede">개발자가 없어도 도입할 수 있습니다. 학습과 검수는 저희가 합니다.</p>
  <div class="steps" style="text-align:left">
    <div class="step"><div class="n">STEP 01</div><h3>자료 전달</h3><p>PDF·엑셀·홈페이지 주소 무엇이든 좋습니다. 정리되지 않아도 괜찮습니다.</p></div>
    <div class="step"><div class="n">STEP 02</div><h3>학습과 검수</h3><p>색인 후 실제 질문으로 정확도를 측정합니다. 기준 미달이면 자료를 보완합니다.</p></div>
    <div class="step"><div class="n">STEP 03</div><h3>설치</h3><p>받으신 스크립트 한 줄을 홈페이지에 붙입니다. 2~5영업일이면 끝납니다.</p></div>
    <div class="step"><div class="n">STEP 04</div><h3>운영</h3><p>답하지 못한 질문 목록을 매주 보내드립니다. 그게 다음에 보완할 자료입니다.</p></div>
  </div>
</div></section>

<section id="faq"><div class="w center">
  <p class="sec-lab">FAQ</p>
  <h2>자주 묻는 질문</h2>
  <div class="faq" style="text-align:left;margin-top:34px">
    <div class="fq"><h3>개발자가 없어도 되나요?</h3><p>네. 자료를 보내주시면 학습과 검수까지 저희가 합니다. 설치가 어려우시면 대행해 드립니다.</p></div>
    <div class="fq"><h3>엉뚱한 답을 하면요?</h3><p>근거를 찾지 못하면 답하지 않고 담당자에게 넘깁니다. 오답보다 연결이 안전하다고 봅니다.</p></div>
    <div class="fq"><h3>카페24 쇼핑몰에도 되나요?</h3><p>가능합니다. 상품 정보를 학습시키면 재고·배송·교환 문의까지 답합니다.</p></div>
    <div class="fq"><h3>가입은 어떻게 하나요?</h3><p>카카오·네이버 간편 로그인 또는 이메일 인증 가입을 지원합니다. 상담창에서 바로 하실 수 있습니다.</p></div>
    <div class="fq"><h3>자료가 유출되지 않나요?</h3><p>고객사별로 저장 공간과 권한을 분리합니다. 요청하시면 삭제 후 확인서를 드립니다.</p></div>
    <div class="fq"><h3>결제와 세금계산서는요?</h3><p>카페24 스토어에서 처리됩니다. 카드·계좌이체가 되고 세금계산서를 발행합니다.</p></div>
  </div>
</div></section>

<section class="band"><div class="w">
  <h2>먼저 물어보세요</h2>
  <p>지금 이 화면의 챗봇이 저희 제품입니다. 가격·설치·분양 조건까지 바로 답해 드립니다.</p>
  <button class="btn b-pri b-lg" onclick="openChat()">AI 상담 시작하기</button>
</div></section>

<section id="contact"><div class="w center">
  <p class="sec-lab">CONTACT</p>
  <h2>사람이 직접 받습니다</h2>
  <p class="lede">계약이나 견적처럼 확답이 필요한 내용은 아래로 연락 주세요.</p>
  <div class="cc" style="text-align:left">
    <div class="b"><div class="k">전화 문의</div><div class="v"><a href="tel:{COMPANY["phone"]}">{COMPANY["phone"]}</a></div><p>{COMPANY["hours"]}</p></div>
    <div class="b"><div class="k">메일 문의</div><div class="v"><a href="mailto:{COMPANY["email"]}">{COMPANY["email"]}</a></div><p>영업일 기준 1일 내 회신</p></div>
    <div class="b"><div class="k">구매</div><div class="v"><a href="{CAFE24_URL}" target="_blank" rel="noopener">카페24 스토어</a></div><p>결제·세금계산서 발행</p></div>
  </div>
</div></section>

<footer><div class="w">
  <div class="top">AI<span style="color:#D68189">노마드</span>챗봇</div>
  <div>기업용 하이브리드 RAG 상담 챗봇 · 전화 {COMPANY["phone"]} · 메일 <a href="mailto:{COMPANY["email"]}">{COMPANY["email"]}</a></div>
  <div style="margin-top:8px">챗봇 답변은 AI가 생성하며 계약의 효력을 갖지 않습니다.</div>
  <!-- 오픈 전 필수: 상호 · 대표자 · 사업자등록번호 · 통신판매업 신고번호 · 주소를 여기에 표기하세요 -->
</div></footer>

<script src="/widget.js" data-tenant="{BSM_TENANT}" data-mode="center"></script>
<script>
function openChat(){{
  if (window.BSMChat) window.BSMChat.open();
  else setTimeout(function(){{ window.BSMChat && window.BSMChat.open(); }}, 400);
}}
</script>
</body></html>''')

# ── firebase.json ────────────────────────────────────────────────
(PUB.parent / "firebase.json").write_text(json.dumps({
    "hosting": {
        "public": "public",
        "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
        "headers": [
            {"source": "/widget.js",
             "headers": [{"key": "Cache-Control", "value": "public,max-age=300"},
                         {"key": "Access-Control-Allow-Origin", "value": "*"}]},
            {"source": "**/*.@(html)",
             "headers": [{"key": "Cache-Control", "value": "public,max-age=600"}]}
        ],
        "rewrites": [{"source": "**", "destination": "/index.html"}]
    }
}, indent=2))

print("생성 완료")
for p in sorted(PUB.iterdir()):
    print(f"  public/{p.name}  ({p.stat().st_size:,} bytes)")
print("  firebase.json")
""")

code(r"""
# Firebase Hosting 배포.
# 로그인은 브라우저 인증이 필요합니다. --no-localhost 옵션이 출력하는 URL을 열어
# 코드를 복사해 붙여넣으면 됩니다.
!npm -q install -g firebase-tools 2>/dev/null | tail -1

print("\n[1] 로그인 — 아래 출력되는 URL을 열어 인증 코드를 붙여넣으세요")
!cd /content && firebase login --no-localhost

print("\n[2] 배포")
!cd /content && firebase deploy --only hosting --project {PROJECT_ID}

print("\\n배포가 끝나면 다음 주소로 접속됩니다:")
print("  https://" + PROJECT_ID + ".web.app")
print("")
print("커스텀 도메인(" + SITE_DOMAIN + ")은 Firebase 콘솔 > Hosting > 커스텀 도메인 추가에서")
print("DNS 레코드를 등록하면 연결됩니다. 인증서는 자동 발급됩니다.")
""")

md("""
## 16. 운영 — 리드 · 대화 로그 · 미응답 질문

**미응답 질문 목록이 이 시스템에서 가장 값진 데이터입니다.**
답하지 못한 질문이 곧 보완할 지식이고, 동시에 다음 블로그·영상 주제가 됩니다.
""")

code(r"""
import pandas as pd

def leads(days=30):
    return bq.query(f'''
      SELECT created_at, company, contact_name, phone, email, homepage, memo, source
      FROM `{DS}.leads`
      WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
      ORDER BY created_at DESC''').to_dataframe()

def unanswered(tenant_id=BSM_TENANT, days=14, limit=30):
    # 근거를 찾지 못한 질문 = 지식 공백
    return bq.query(f'''
      SELECT question, COUNT(*) AS cnt, MAX(created_at) AS last_at,
             ROUND(AVG(top_score), 4) AS avg_score
      FROM `{DS}.chat_logs`
      WHERE tenant_id = '{tenant_id}' AND grounded = FALSE
        AND created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
      GROUP BY question ORDER BY cnt DESC, last_at DESC LIMIT {limit}''').to_dataframe()

def daily(tenant_id=BSM_TENANT, days=14):
    return bq.query(f'''
      SELECT DATE(created_at) AS d, COUNT(*) AS sessions,
             ROUND(AVG(IF(grounded, 1, 0)) * 100, 1) AS grounded_pct,
             ROUND(AVG(latency_ms)) AS avg_ms,
             COUNTIF(action = 'BUY') AS buy,
             COUNTIF(action = 'TRIAL') AS trial,
             COUNTIF(action = 'CONTACT') AS contact
      FROM `{DS}.chat_logs`
      WHERE tenant_id = '{tenant_id}'
        AND created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
      GROUP BY d ORDER BY d DESC''').to_dataframe()

def billing_usage(month=None, tenant_id=None):
    # 과금 기준 집계. 해결 = grounded=TRUE 인 대화.
    # 상담 연결로 넘어간 대화는 세지 않으므로 고객에게 청구되지 않습니다.
    m = month or dt.datetime.now().strftime("%Y-%m")
    where = f"FORMAT_TIMESTAMP('%Y-%m', created_at) = '{m}'"
    if tenant_id:
        where += f" AND tenant_id = '{tenant_id}'"
    return bq.query(f'''
      SELECT tenant_id,
             COUNT(*)                       AS conversations,
             COUNTIF(grounded)              AS resolutions,
             COUNTIF(NOT grounded)          AS handoffs,
             ROUND(COUNTIF(grounded) / COUNT(*) * 100, 1) AS resolution_rate
      FROM `{DS}.chat_logs`
      WHERE {where}
      GROUP BY tenant_id ORDER BY resolutions DESC''').to_dataframe()

def escalations(days=14, status=None):
    # 챗봇이 답하지 못해 담당자에게 넘어간 문의
    w = f"created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)"
    if status:
        w += f" AND status = '{status}'"
    return bq.query(f'''
      SELECT created_at, esc_id, contact_email, question, email_sent, status, summary
      FROM `{DS}.escalations` WHERE {w} ORDER BY created_at DESC''').to_dataframe()

def inquiries(days=30):
    # 회원 로그인 후 접수된 가격·견적 문의
    return bq.query(f'''
      SELECT i.created_at, i.inquiry_id, i.category, i.company_name, i.phone,
             i.contact_email, i.title, i.status, m.provider, m.name
      FROM `{DS}.inquiries` i
      LEFT JOIN `{DS}.members` m USING (member_id)
      WHERE i.created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
      ORDER BY i.created_at DESC''').to_dataframe()

def members_stat(days=30):
    return bq.query(f'''
      SELECT provider, COUNT(*) AS signups, COUNTIF(email != '') AS with_email
      FROM `{DS}.members`
      WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
      GROUP BY provider ORDER BY signups DESC''').to_dataframe()

print("── 담당자 전달 대기 (미회신) ──")
display(escalations(status="NEW"))
print("── 회원 가격·견적 문의 ──")
display(inquiries())
print("── 소셜 가입 현황 ──")
display(members_stat())
print("── 이번 달 과금 기준 (해결 건수) ──")
display(billing_usage())
print("── 최근 지표 ──")
display(daily())
print("── 답하지 못한 질문 (지식 공백) ──")
display(unanswered())
print("── 무료 체험 신청 ──")
display(leads())
""")

md("""
## 17. 고객 개통 — 카페24 주문에서 위젯 발급까지

초기에는 자동화하지 않습니다. 고객 20~30곳까지는 수동 개통이 훨씬 저렴하고 품질도 좋습니다.
아래 함수 하나로 개통이 끝납니다.
""")

code(r"""
def onboard(tenant_id, name, contact_name="", phone="", email="", homepage="",
            urls=None, pdf_paths=None, texts=None):
    # 카페24 주문 확인 후 실행하는 개통 함수입니다.
    print(f"── 개통 시작: {tenant_id} / {name} ──")
    create_tenant(tenant_id, name, plan="BASIC", contact_name=contact_name,
                  phone=phone, email=email, homepage=homepage)
    reset_tenant_knowledge(tenant_id)

    n = 0
    for u in (urls or []):
        n += add_url(tenant_id, u)
    for p in (pdf_paths or []):
        n += add_pdf(tenant_id, p)
    for title, body in (texts or {}).items():
        n += add_text(tenant_id, title, body)

    print(f"\n지식 {n}개 청크 색인 완료")
    print("\n── 고객사에 전달할 설치 코드 ──")
    print(f'<script src="{SITE_DOMAIN}/widget.js" data-tenant="{tenant_id}"></script>')
    print("\n── 개통 검수 ──")
    for q in ["영업시간이 어떻게 되나요?", "환불 규정을 알려주세요", "배송은 얼마나 걸리나요?"]:
        r = answer(q, tenant_id=tenant_id, log=False)
        print(f"  Q. {q}\n  A. {r['answer'][:90]}...  [{'근거O' if r['grounded'] else '근거X'}]")
    return tenant_id

# 사용 예 — 실제 주문이 들어오면 주석을 풀고 값을 채워 실행하세요.
# onboard("SHOP001", "○○몰",
#         contact_name="홍길동", phone="010-0000-0000", email="owner@example.com",
#         homepage="https://example.com",
#         urls=["https://example.com/guide", "https://example.com/faq"],
#         pdf_paths=["/content/이용안내.pdf"])
print("개통 함수 준비 완료")
""")

md("""
## 18. 비용 가드 — 반드시 먼저 설정하세요

가장 흔한 사고는 기능 실패가 아니라 **요금 폭주**입니다. 세 가지를 걸어 둡니다.

1. **예산 알림** — 결제 계정 단위로 임계값을 넘으면 메일이 옵니다.
2. **Cloud Run 최대 인스턴스** — 14단계에서 `--max-instances 3`으로 이미 제한했습니다.
3. **로그 보존 기간** — 기본 30일을 넘기지 않도록 줄입니다. 로깅 비용은 조용히 커집니다.
""")

code(r"""
# 결제 계정 ID 확인
!gcloud billing accounts list

# 아래 BILLING_ACCOUNT를 위 출력의 ACCOUNT_ID로 바꾼 뒤 다시 실행하세요.
BILLING_ACCOUNT = "000000-000000-000000"   # ← 수정 필요

budget_cmd = (
    f"gcloud billing budgets create --billing-account={BILLING_ACCOUNT} "
    f'--display-name="BSM AI 월 예산" --budget-amount=50000KRW '
    f"--threshold-rule=percent=0.5 --threshold-rule=percent=0.8 "
    f"--threshold-rule=percent=1.0 -q"
)

if BILLING_ACCOUNT == "000000-000000-000000":
    print("BILLING_ACCOUNT를 위 목록의 ACCOUNT_ID로 바꾼 뒤 다시 실행하세요.")
    print("예산 알림 없이 운영하지 마세요. 가장 흔한 사고가 요금 폭주입니다.")
else:
    get_ipython().system(budget_cmd)

# 로그 보존 30일로 제한 (로깅 비용은 조용히 커집니다)
!gcloud logging buckets update _Default --location=global --retention-days=30 -q
print("로그 보존 기간 30일로 설정")
""")

md("""
## 19. 오픈 전 점검표

| 항목 | 확인 |
|---|---|
| 골든셋 정답률 85% 이상 | 13단계 |
| 자료에 없는 질문에서 상담 연결로 넘어가는지 | 12단계 마지막 질문 |
| `/health`, `/chat` 응답 정상 | 14단계 |
| 홈페이지 우측 하단 위젯 동작 | 배포 후 브라우저 |
| 카페24에 상품 3종 등록 (이용권 · 개통지원 · 분양구좌) | 카페24 관리자 |
| 홈페이지 구매 버튼이 실제 상품 페이지로 연결 | `CAFE24_URL` 수정 |
| **푸터에 사업자 정보 표기** (상호·대표자·사업자등록번호·통신판매업 신고번호·주소) | `index.html` 주석 위치 |
| 개인정보처리방침·이용약관 페이지 | 별도 작성 필요 |
| 예산 알림 설정 | 18단계 |
| 티스토리·유튜브 CTA를 홈페이지로 연결 (UTM 포함) | 콘텐츠 채널 |

**아직 남은 일이 두 가지 있습니다.** 사업자 정보 표기는 전자상거래법상 의무이므로 오픈 전에 반드시 채우셔야 하고,
개인정보처리방침은 상담 신청 폼에서 개인정보를 받는 이상 필수입니다. 두 가지 모두 이 노트북 밖의 작업입니다.

---

### 이후 운영 리듬

- **매주** — 17단계 `unanswered()`로 지식 공백 확인 → 자료 보완 → 재색인, 그 목록으로 블로그·영상 주제 선정
- **매월** — 13단계 골든셋 재실행으로 품질 회귀 확인, `daily()`로 전환 지표 점검
- **주문 발생 시** — 18단계 `onboard()` 실행 후 설치 코드 전달
""")

nb = {
    "cells": [
        ({"cell_type": "markdown", "metadata": {}, "source": s.splitlines(keepends=True)}
         if t == "markdown" else
         {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
          "source": s.splitlines(keepends=True)})
        for t, s in C
    ],
    "metadata": {
        "colab": {"provenance": [], "toc_visible": True, "name": "BSM_AI_FACTORY_GCP.ipynb"},
        "kernelspec": {"name": "python3", "display_name": "Python 3"},
        "language_info": {"name": "python"},
    },
    "nbformat": 4, "nbformat_minor": 0,
}

out = "/home/user/chatbot/notebooks/BSM_AI_FACTORY_GCP.ipynb"
io.open(out, "w", encoding="utf-8").write(json.dumps(nb, ensure_ascii=False, indent=1))
print("생성:", out, "| 셀 수:", len(C))
