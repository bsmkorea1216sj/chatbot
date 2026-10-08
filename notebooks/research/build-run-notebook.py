import json, io
C = []
def md(s): C.append(("markdown", s.strip("\n")))
def code(s): C.append(("code", s.strip("\n")))

md(r"""
# BSM AI 리서치 · 실행 노트북 v1.0

`BSM_AI_Research_GCP_v0_3.ipynb` 의 앱 코드를 **실제 GCP에 올리고 검증**하는 노트북입니다.
원본 노트북은 코드를 런타임에 펼치고 단위 테스트까지만 합니다. 이 노트북은 그다음을 합니다.

```
인증 → API 활성화 → Firestore·Cloud Tasks·서비스계정 → 시크릿 → 앱 전개
     → 모델/단가 패치 → 테스트 → Cloud Run 배포 → 스모크 테스트 → 원가 측정
```

**먼저 읽어 주세요.**

1. **Gemini 2.5 Flash는 2026-10-16에 종료됩니다.** 원본 `app.py` 의 `quote()` 는 이 모델만 허용하도록
   하드코딩돼 있어 그대로 두면 곧 멈춥니다. 9단계에서 검토 완료 모델 목록 방식으로 바꿉니다.
2. **단가는 제가 채우지 않습니다.** 모델 요금과 환율은 2단계에서 직접 입력하세요.
   값이 비어 있으면 앱이 `503 가격 설정 검증이 필요합니다` 로 실패하도록 설계돼 있습니다.
3. **비용이 발생합니다.** 15단계 원가 측정은 실제 Gemini 호출입니다. 횟수를 확인하고 실행하세요.
4. Firebase 콘솔에서 **Authentication → Google 공급자**를 먼저 켜야 로그인이 동작합니다.
""")

md("## 1. 인증")

code(r"""
import os, re, json, time, base64, subprocess, datetime as dt

def _sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

def _token_works():
    try:
        import google.auth
        from google.auth.transport.requests import Request
        creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        creds.refresh(Request())
        return bool(creds.token)
    except Exception:
        return False

def _colab_auth(reset=False):
    try:
        from google.colab import auth
    except ImportError:
        return False
    if reset:
        _sh("gcloud auth revoke --all -q")
        _sh("rm -f ~/.config/gcloud/application_default_credentials.json")
    try:
        auth.authenticate_user(); return True
    except Exception as e:
        print("  인증 실패:", type(e).__name__, str(e)[:160]); return False

def _key_auth():
    # 브라우저 인증이 401/400 으로 막힐 때 쓰는 우회 경로입니다.
    print("\n서비스 계정 키(JSON)를 업로드하세요. 콘솔 > IAM > 서비스 계정 > 키 추가 > JSON")
    try:
        from google.colab import files
        up = files.upload()
        if not up: return False
        path = "/content/" + list(up.keys())[0]
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path
        _sh(f"gcloud auth activate-service-account --key-file={path} -q")
        return True
    except Exception as e:
        print("  키 인증 실패:", type(e).__name__, str(e)[:160]); return False

print("구글 인증을 시작합니다.")
if not (_colab_auth() and _token_works()):
    print("재시도합니다. 계정 선택 화면이 뜨면 GCP 프로젝트 소유 계정을 고르세요.")
    if not (_colab_auth(reset=True) and _token_works()):
        _key_auth()

if not _token_works():
    raise RuntimeError("구글 인증 실패. 시크릿 창에서 계정 하나만 로그인한 뒤 다시 실행하거나, "
                       "서비스 계정 키로 진행하세요.")

acct = _sh("gcloud auth list --filter=status:ACTIVE --format='value(account)'").stdout.strip()
print("인증 완료:", acct or "(서비스 계정)")
""")

md("""
## 2. 설정

`MODEL`, 단가, 환율은 반드시 직접 채우세요. 비워 두면 뒤 단계에서 멈춥니다.
단가는 [Vertex AI 가격](https://cloud.google.com/vertex-ai/generative-ai/pricing)에서 선택한 모델의
100만 토큰당 USD 를 그대로 옮기면 됩니다.
""")

code(r"""
# ─── 프로젝트 ──────────────────────────────────────────────────────
PROJECT_ID   = "aichat-507914"
REGION       = "asia-northeast3"          # Cloud Run · Cloud Tasks
FS_LOCATION  = "asia-northeast3"          # Firestore
SERVICE      = "bsm-research"
QUEUE        = "research-jobs"
SOURCE_NB_ID = "1suGjY7tdhlEubNDB-pK38LVl3w5r2ixS"   # 원본 노트북 Drive 파일 ID

# ─── 모델과 단가 (반드시 확인 후 입력) ─────────────────────────────
MODEL               = "gemini-3.8-flash"  # 2.5 계열은 2026-10-16 종료
MODEL_INPUT_WINDOW  = 1_048_576           # 최악의 경우 예약에 쓰는 입력 토큰 수
INPUT_USD_PER_MILLION  = ""               # 예: "0.30"
OUTPUT_USD_PER_MILLION = ""               # 예: "2.50"
KRW_PER_USD            = ""               # 예: "1380"
GROUNDING_MAX_MICRO_KRW = 0               # 검색 1회 최대 비용(마이크로원). 예: 60_000_000 == 60원
PRICE_VERSION          = dt.date.today().strftime("%Y%m%d") + "-1"

# ─── 상품 ─────────────────────────────────────────────────────────
PURCHASE_URL = "https://bsmshop.cafe24.com"   # 카페24 상품 페이지. 미등록이면 그대로 두세요
TRIAL_POOL_KRW = 50_000                        # 무료 체험 전체 예산(원)

# ─── 파생값 ───────────────────────────────────────────────────────
RUN_SA   = f"bsm-research-run@{PROJECT_ID}.iam.gserviceaccount.com"
TASKS_SA = f"bsm-research-tasks@{PROJECT_ID}.iam.gserviceaccount.com"
APP_DIR  = "/content/bsm_gcp_research"

os.environ["GOOGLE_CLOUD_PROJECT"] = PROJECT_ID
os.environ["GOOGLE_CLOUD_QUOTA_PROJECT"] = PROJECT_ID
_sh(f"gcloud config set project {PROJECT_ID} -q")

missing = [n for n, v in [("INPUT_USD_PER_MILLION", INPUT_USD_PER_MILLION),
                          ("OUTPUT_USD_PER_MILLION", OUTPUT_USD_PER_MILLION),
                          ("KRW_PER_USD", KRW_PER_USD)] if not str(v).strip()]
if GROUNDING_MAX_MICRO_KRW <= 0:
    missing.append("GROUNDING_MAX_MICRO_KRW")

proj = _sh(f"gcloud projects describe {PROJECT_ID} --format='value(projectId)'").stdout.strip()
if proj != PROJECT_ID:
    raise RuntimeError(f"프로젝트 {PROJECT_ID} 에 접근할 수 없습니다. 권한을 확인하세요.")

print("프로젝트:", PROJECT_ID, "| 리전:", REGION, "| 모델:", MODEL)
print("가격 버전:", PRICE_VERSION)
if missing:
    print("\n아직 비어 있는 값:", ", ".join(missing))
    print("13단계 배포 전까지는 반드시 채워야 합니다. 비면 앱이 503 으로 실패합니다.")
else:
    print("단가 입력 완료.")
""")

md("## 3. API 활성화")

code(r"""
APIS = ["run.googleapis.com", "cloudbuild.googleapis.com", "artifactregistry.googleapis.com",
        "firestore.googleapis.com", "cloudtasks.googleapis.com", "secretmanager.googleapis.com",
        "identitytoolkit.googleapis.com", "firebase.googleapis.com", "iam.googleapis.com",
        "generativelanguage.googleapis.com"]
r = _sh("gcloud services enable " + " ".join(APIS) + " -q")
print("API 활성화 완료" if r.returncode == 0 else "실패:\n" + r.stderr[-800:])
""")

md("""
## 4. Firestore 와 Cloud Tasks

Firestore 는 프로젝트당 하나의 기본 데이터베이스만 만들 수 있습니다. 이미 있으면 그대로 씁니다.
""")

code(r"""
r = _sh(f"gcloud firestore databases describe --database='(default)' --format='value(type)'")
if r.returncode == 0 and r.stdout.strip():
    print("Firestore 이미 있음:", r.stdout.strip())
else:
    r = _sh(f"gcloud firestore databases create --location={FS_LOCATION} "
            f"--type=firestore-native -q")
    print("Firestore 생성" if r.returncode == 0 else "Firestore 생성 실패:\n" + r.stderr[-600:])

r = _sh(f"gcloud tasks queues describe {QUEUE} --location={REGION} --format='value(name)'")
if r.returncode == 0 and r.stdout.strip():
    print("큐 이미 있음:", r.stdout.strip().split('/')[-1])
else:
    r = _sh(f"gcloud tasks queues create {QUEUE} --location={REGION} -q")
    print("큐 생성" if r.returncode == 0 else "큐 생성 실패:\n" + r.stderr[-600:])

# 동시 실행과 재시도를 제한해 폭주와 중복 과금을 막습니다.
_sh(f"gcloud tasks queues update {QUEUE} --location={REGION} "
    f"--max-concurrent-dispatches=5 --max-attempts=3 --min-backoff=30s -q")
print("큐 설정: 동시 5건, 최대 3회 시도")
""")

md("""
## 5. 서비스 계정과 권한

두 개를 씁니다. 하나는 Cloud Run 이 실행될 때 쓰는 계정, 다른 하나는 Cloud Tasks 가
작업을 호출할 때 쓰는 계정입니다. `app.py` 의 `/internal/work` 는 호출자가 후자인지 확인합니다.
""")

code(r"""
def ensure_sa(email, display):
    name = email.split("@")[0]
    if _sh(f"gcloud iam service-accounts describe {email}").returncode != 0:
        _sh(f"gcloud iam service-accounts create {name} --display-name='{display}' -q")
        print("생성:", email); time.sleep(5)
    else:
        print("이미 있음:", email)

def bind(member, role):
    _sh(f"gcloud projects add-iam-policy-binding {PROJECT_ID} "
        f"--member=serviceAccount:{member} --role={role} -q --condition=None")

ensure_sa(RUN_SA, "BSM Research Runtime")
ensure_sa(TASKS_SA, "BSM Research Tasks Invoker")

for role in ["roles/datastore.user", "roles/cloudtasks.enqueuer",
             "roles/secretmanager.secretAccessor", "roles/firebaseauth.viewer"]:
    bind(RUN_SA, role)
# Cloud Tasks 작업에 OIDC 토큰을 붙이려면 런타임 계정이 호출 계정을 대신할 수 있어야 합니다.
_sh(f"gcloud iam service-accounts add-iam-policy-binding {TASKS_SA} "
    f"--member=serviceAccount:{RUN_SA} --role=roles/iam.serviceAccountUser -q")

print("\n런타임 계정 권한: Firestore, Cloud Tasks 등록, 시크릿 읽기")
print("호출 계정은 13단계 배포 후 run.invoker 를 받습니다.")
""")

md("""
## 6. Gemini API 키

Secret Manager 에 저장합니다. 입력값은 화면에 표시되지 않고 노트북에도 남지 않습니다.
키는 [Google AI Studio](https://aistudio.google.com/apikey) 에서 발급합니다.
""")

code(r"""
from getpass import getpass

def put_secret(name, value):
    if not value:
        print(f"  {name}: 건너뜀"); return
    _sh(f"gcloud secrets create {name} --replication-policy=automatic -q")
    r = subprocess.run(["gcloud", "secrets", "versions", "add", name, "--data-file=-"],
                       input=value.encode(), capture_output=True)
    print(f"  {name}: {'저장됨' if r.returncode == 0 else '실패'}")

exists = _sh("gcloud secrets describe GEMINI_API_KEY --format='value(name)'").returncode == 0
if exists:
    print("GEMINI_API_KEY 이미 있습니다. 새 값을 넣으려면 아래에 입력하고, 그대로 쓰려면 엔터만 누르세요.")
put_secret("GEMINI_API_KEY", getpass("Gemini API 키: "))

_sh(f"gcloud secrets add-iam-policy-binding GEMINI_API_KEY "
    f"--member=serviceAccount:{RUN_SA} --role=roles/secretmanager.secretAccessor -q")
print("런타임 계정에 읽기 권한 부여")
""")

md("""
## 7. Firebase 웹 설정

브라우저가 구글 로그인을 하려면 웹 앱 설정이 필요합니다. `app.py` 는 이 값을
`FIREBASE_WEB_CONFIG` 환경변수로 받아 `/api/config` 로 내려줍니다.

Firebase 콘솔에서 먼저 두 가지를 확인하세요.
**Authentication → 시작하기 → Google 공급자 사용 설정**, 그리고 **설정 → 승인된 도메인**에
Cloud Run 주소(13단계 출력)를 추가합니다.
""")

code(r"""
FIREBASE_WEB_CONFIG = ""   # 직접 붙여넣으려면 여기에 JSON 문자열을 넣으세요

if not FIREBASE_WEB_CONFIG:
    _sh("npm -q install -g firebase-tools")
    r = _sh(f"firebase apps:sdkconfig WEB --project {PROJECT_ID} --json --non-interactive")
    try:
        FIREBASE_WEB_CONFIG = json.dumps(json.loads(r.stdout)["result"]["sdkConfig"],
                                         ensure_ascii=False, separators=(",", ":"))
    except Exception:
        FIREBASE_WEB_CONFIG = ""

if FIREBASE_WEB_CONFIG:
    cfg = json.loads(FIREBASE_WEB_CONFIG)
    print("apiKey     :", str(cfg.get("apiKey", ""))[:10] + "...")
    print("authDomain :", cfg.get("authDomain"))
    print("projectId  :", cfg.get("projectId"))
else:
    print("자동 조회 실패. Firebase 콘솔 > 프로젝트 설정 > 내 앱 > 웹 앱에서 구성 객체를 복사해")
    print("위 FIREBASE_WEB_CONFIG 에 JSON 한 줄로 붙여넣고 이 셀을 다시 실행하세요.")
    print("웹 앱이 없으면 콘솔에서 '앱 추가 > 웹'으로 하나 만드세요.")
""")

md("""
## 8. 원본 노트북에서 앱 코드 가져오기

코드를 두 곳에 복사해 두면 반드시 어긋납니다. 원본 노트북을 Drive 에서 직접 읽어
`FILES` 사전만 꺼내 씁니다. 원본을 고치면 이 셀을 다시 돌리는 것으로 끝납니다.
""")

code(r"""
import ast
from pathlib import Path
import google.auth
from google.auth.transport.requests import AuthorizedSession

def fetch_source_notebook(file_id):
    try:
        creds, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/drive.readonly"])
        s = AuthorizedSession(creds)
        r = s.get(f"https://www.googleapis.com/drive/v3/files/{file_id}",
                  params={"alt": "media"}, timeout=60)
        if r.status_code == 200:
            return r.text
        print("Drive 조회 실패:", r.status_code, r.text[:200])
    except Exception as e:
        print("Drive 조회 예외:", type(e).__name__, str(e)[:160])
    print("\n원본 .ipynb 를 직접 업로드하세요.")
    from google.colab import files
    up = files.upload()
    return list(up.values())[0].decode("utf-8") if up else ""

raw = fetch_source_notebook(SOURCE_NB_ID)
if not raw:
    raise RuntimeError("원본 노트북을 가져오지 못했습니다.")

nb = json.loads(raw)
src = next(("".join(c["source"]) for c in nb["cells"]
            if c["cell_type"] == "code" and "FILES" in "".join(c["source"])), "")
j = src.index("{", src.index("FILES"))
depth, k = 0, j
while k < len(src):
    if src[k] == "{": depth += 1
    elif src[k] == "}":
        depth -= 1
        if depth == 0: break
    k += 1
FILES = ast.literal_eval(src[j:k+1])      # 코드 실행 없이 파싱

target = Path(APP_DIR); target.mkdir(parents=True, exist_ok=True)
for name, content in FILES.items():
    (target / name).write_text(content, encoding="utf-8")
print(f"앱 전개 완료: {APP_DIR}  ({len(FILES)}개 파일)")
for name in sorted(FILES): print("  -", name)
""")

md("""
## 9. 모델 잠금 해제

원본 `app.py` 의 `quote()` 는 `gemini-2.5-flash` 만 허용합니다. 다른 모델을 넣으면
`Unreviewed model pricing` 으로 막힙니다. 2.5 계열이 **2026-10-16에 종료**되므로
모델 이름을 운영 설정으로 받되, 검토를 마친 목록에 있는 것만 통과시키도록 바꿉니다.

실패를 닫아 두는 성질은 그대로입니다. `REVIEWED_MODELS` 에 없는 모델은 여전히 거부됩니다.
""")

code(r"""
from pathlib import Path

p = Path(APP_DIR) / "app.py"
s = p.read_text(encoding="utf-8")

OLD = '''    # Only Gemini 2.5 Flash is allowed here: search is billed per grounded prompt.
    # Reserve the full model input window including grounding/tool tokens.
    if os.getenv('GEMINI_MODEL', 'gemini-2.5-flash') != 'gemini-2.5-flash':
        raise ValueError('Unreviewed model pricing')'''

NEW = '''    # 검토를 마친 모델만 허용합니다. 모델명과 입력 창은 운영 설정으로 받습니다.
    # 검색은 grounded prompt 단위로 과금되므로 입력 창 전체를 예약합니다.
    model = os.getenv('GEMINI_MODEL', '')
    reviewed = {m.strip() for m in os.getenv('REVIEWED_MODELS', '').split(',') if m.strip()}
    if not model or model not in reviewed:
        raise ValueError('Unreviewed model pricing')'''

if OLD in s:
    s = s.replace(OLD, NEW, 1)
    s = s.replace("    cap = token_cost(1_048_576, output,",
                  "    cap = token_cost(positive_env('MODEL_INPUT_WINDOW'), output,", 1)
    s = s.replace("'output': output, 'model': 'gemini-2.5-flash',",
                  "'output': output, 'model': model,", 1)
    p.write_text(s, encoding="utf-8")
    print("패치 적용: 모델 잠금 해제")
elif "REVIEWED_MODELS" in s:
    print("이미 패치되어 있습니다.")
else:
    raise RuntimeError("quote() 원문을 찾지 못했습니다. 원본이 바뀌었는지 확인하세요.")

for line in s.split("\n"):
    if "REVIEWED_MODELS" in line or "MODEL_INPUT_WINDOW" in line or "'model': model" in line:
        print("  ", line.strip()[:100])
""")

md("## 10. 단위 테스트")

code(r"""
import sys
r = subprocess.run([sys.executable, "-m", "pip", "install", "-q",
                    "-r", f"{APP_DIR}/requirements.txt", "httpx"],
                   capture_output=True, text=True)
if r.returncode != 0:
    print("설치 경고:", r.stderr[-500:])

r = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", APP_DIR, "-p", "test_*.py"],
                   capture_output=True, text=True)
print(r.stdout[-2000:] or "")
print(r.stderr[-3000:] or "")
if r.returncode != 0:
    raise RuntimeError("테스트 실패. 배포하지 마세요.")
print("테스트 통과")
""")

md("""
## 11. 무료 체험 예산 시드

`budgets/trial_pool` 문서의 `granted` 가 무료 실행 전체의 상한입니다.
이 값이 바닥나면 무료 실행이 멈춥니다. 유료 사용자는 영향을 받지 않습니다.
""")

code(r"""
from google.cloud import firestore

fs = firestore.Client(project=PROJECT_ID)
ref = fs.collection("budgets").document("trial_pool")
cur = ref.get().to_dict() or {}
granted = TRIAL_POOL_KRW * 1_000_000        # 마이크로원

if cur.get("granted"):
    print("기존 예산:", f"{cur['granted']//1_000_000:,}원",
          "| 사용:", f"{cur.get('spent',0)//1_000_000:,}원",
          "| 예약:", f"{cur.get('reserved',0)//1_000_000:,}원")
    print("바꾸려면 아래 줄의 주석을 푸세요.")
    # ref.set({"granted": granted}, merge=True); print("예산 갱신:", f"{TRIAL_POOL_KRW:,}원")
else:
    ref.set({"granted": granted, "spent": 0, "reserved": 0}, merge=True)
    print("무료 체험 예산 설정:", f"{TRIAL_POOL_KRW:,}원")
""")

md("""
## 12. 배포

두 번에 나눠 올립니다. `SERVICE_URL` 은 Cloud Tasks 가 쓰는 OIDC 대상(audience)이라
주소가 정해진 뒤에 다시 넣어야 합니다.
""")

code(r"""
if missing:
    raise RuntimeError("단가가 비어 있습니다: " + ", ".join(missing) + " — 2단계를 채우고 다시 실행하세요.")
if not FIREBASE_WEB_CONFIG:
    raise RuntimeError("FIREBASE_WEB_CONFIG 가 비어 있습니다. 7단계를 먼저 끝내세요.")

ENVS = {
    "GOOGLE_CLOUD_PROJECT": PROJECT_ID,
    "TASKS_REGION": REGION,
    "TASKS_QUEUE": QUEUE,
    "TASKS_SA": TASKS_SA,
    "GEMINI_MODEL": MODEL,
    "REVIEWED_MODELS": MODEL,
    "MODEL_INPUT_WINDOW": str(MODEL_INPUT_WINDOW),
    "INPUT_USD_PER_MILLION": str(INPUT_USD_PER_MILLION),
    "OUTPUT_USD_PER_MILLION": str(OUTPUT_USD_PER_MILLION),
    "KRW_PER_USD": str(KRW_PER_USD),
    "GROUNDING_MAX_MICRO_KRW": str(GROUNDING_MAX_MICRO_KRW),
    "PRICE_VERSION": PRICE_VERSION,
    "PURCHASE_URL": PURCHASE_URL,
    "SERVICE_URL": "https://placeholder.invalid",
}
# FIREBASE_WEB_CONFIG 는 쉼표가 들어 있어 --set-env-vars 로 넘기면 깨집니다. 파일로 전달합니다.
env_yaml = "/content/env.yaml"
with open(env_yaml, "w", encoding="utf-8") as f:
    for k, v in ENVS.items():
        f.write(f"{k}: {json.dumps(str(v), ensure_ascii=False)}\n")
    f.write("FIREBASE_WEB_CONFIG: " + json.dumps(FIREBASE_WEB_CONFIG, ensure_ascii=False) + "\n")

print("배포를 시작합니다. 첫 배포는 3~5분 걸립니다.\n")
r = _sh(f"gcloud run deploy {SERVICE} --source {APP_DIR} --region {REGION} "
        f"--service-account {RUN_SA} --allow-unauthenticated "
        f"--memory 1Gi --cpu 1 --min-instances 0 --max-instances 3 "
        f"--concurrency 10 --timeout 300 "
        f"--env-vars-file {env_yaml} "
        f"--set-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest -q")
print(r.stdout[-1500:] or "")
if r.returncode != 0:
    print("[오류]", r.stderr[-2500:]); raise RuntimeError("배포 실패")

SERVICE_URL = _sh(f"gcloud run services describe {SERVICE} --region {REGION} "
                  f"--format='value(status.url)'").stdout.strip()
print("\n서비스 주소:", SERVICE_URL)

# 주소가 정해졌으니 OIDC 대상과 호출 권한을 맞춥니다.
_sh(f"gcloud run services update {SERVICE} --region {REGION} "
    f"--update-env-vars SERVICE_URL={SERVICE_URL} -q")
_sh(f"gcloud run services add-iam-policy-binding {SERVICE} --region {REGION} "
    f"--member=serviceAccount:{TASKS_SA} --role=roles/run.invoker -q")
print("SERVICE_URL 주입과 호출 권한 부여 완료")

print("\n다음 두 가지를 Firebase 콘솔에서 하세요.")
print("  1. Authentication > 시작하기 > Google 공급자 사용 설정")
print("  2. Authentication > 설정 > 승인된 도메인에 추가:", SERVICE_URL.replace("https://", ""))
""")

md("## 13. 스모크 테스트")

code(r"""
import urllib.request, urllib.error

def get(path, token=None):
    req = urllib.request.Request(SERVICE_URL + path)
    if token: req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, resp.read().decode("utf-8")[:400]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")[:300]
    except Exception as e:
        return 0, f"{type(e).__name__}: {e}"

checks = []
s, b = get("/health");      checks.append(("GET /health", s == 200, s, b))
s, b = get("/");            checks.append(("GET / (화면)", s == 200, s, b[:80] + "..."))
s, b = get("/api/config");  checks.append(("GET /api/config", s == 200, s, b))
s, b = get("/api/account"); checks.append(("GET /api/account 무인증 차단", s == 401, s, b))
s, b = get("/api/account", token="bogus")
checks.append(("GET /api/account 잘못된 토큰 차단", s == 401, s, b))

print(f"{'판정':<5}{'항목':<36}{'상태'}")
print("-" * 76)
ok = 0
for name, passed, status, body in checks:
    ok += passed
    print(f"{'통과' if passed else '실패':<5}{name:<36}{status}")
    if not passed: print(f"      {body}")
print("-" * 76)
print(f"{ok}/{len(checks)} 통과")

cfg = json.loads(get("/api/config")[1])
print("\n결제 연결 상태:", "열림" if cfg.get("payments_connected") else "닫힘 (정상 — 카페24 연동 전)")
print("구매 링크:", cfg.get("purchase_url") or "(미설정)")
print("\n브라우저에서 열어 로그인까지 확인하세요:", SERVICE_URL)
""")

md("""
## 14. 원가 측정

지금 가장 급한 작업입니다. 크레딧 제공량과 무료 횟수는 이 숫자에서 나옵니다.

**실제 Gemini 호출이 발생해 비용이 듭니다.** `N_BASIC`, `N_DEEP` 를 확인하고 실행하세요.
기본 3회·심층 2회면 보통 수백 원 수준이지만, 모델과 검색량에 따라 달라집니다.
""")

code(r"""
N_BASIC = 3        # 기본 모드 측정 횟수
N_DEEP  = 2        # 심층 모드 측정 횟수

TOPICS = ["국내 중소기업의 생성형 AI 도입 현황",
          "한국 전자상거래 반품 정책 규제 동향",
          "국내 클라우드 전환 비용 구조",
          "생성형 AI 저작권 분쟁 국내 판례",
          "국내 구독 결제 시장 경쟁 구도"]

api_key = _sh("gcloud secrets versions access latest --secret=GEMINI_API_KEY").stdout.strip()
if not api_key:
    raise RuntimeError("GEMINI_API_KEY 를 읽지 못했습니다. 6단계를 확인하세요.")

sys.path.insert(0, APP_DIR)
os.environ["GEMINI_API_KEY"] = api_key
import importlib, billing
importlib.reload(billing)
from research import generate, AccountedFailure

def measure(mode, n):
    out_tokens = 2048 if mode == "basic" else 4096
    rows = []
    for i in range(n):
        job = {"request": {"topic": TOPICS[i % len(TOPICS)], "categories": ["공식자료", "논문"]},
               "pricing": {"model": MODEL, "output": out_tokens,
                           "rates": {"INPUT_USD_PER_MILLION": str(INPUT_USD_PER_MILLION),
                                     "OUTPUT_USD_PER_MILLION": str(OUTPUT_USD_PER_MILLION),
                                     "KRW_PER_USD": str(KRW_PER_USD)},
                           "grounding": GROUNDING_MAX_MICRO_KRW,
                           "cap": 10**15}}   # 측정이므로 상한을 두지 않습니다
        t0 = time.time()
        try:
            cost, output = generate(job)
            rows.append({"ok": True, "cost": cost, "sec": time.time()-t0,
                         "chars": len(output["report"]), "sources": len(output["sources"])})
            print(f"  {mode} {i+1}/{n}  {cost/1_000_000:>7.1f}원  {time.time()-t0:>5.1f}초  "
                  f"출처 {len(output['sources'])}건")
        except AccountedFailure as e:
            rows.append({"ok": False, "cost": e.cost, "sec": time.time()-t0})
            print(f"  {mode} {i+1}/{n}  실패 (비용 {e.cost/1_000_000:.1f}원은 발생)")
        except Exception as e:
            print(f"  {mode} {i+1}/{n}  오류: {type(e).__name__} {str(e)[:120]}")
    return rows

print(f"모델 {MODEL} 로 측정합니다.\n")
res = {"basic": measure("basic", N_BASIC), "deep": measure("deep", N_DEEP)}

print("\n" + "=" * 70)
BUDGET = 11_000          # 월 22,000원의 50%
summary = {}
for mode, rows in res.items():
    good = [r for r in rows if r["ok"]]
    if not good:
        print(f"{mode:<6} 성공한 측정이 없습니다."); continue
    avg = sum(r["cost"] for r in good) / len(good) / 1_000_000
    mx  = max(r["cost"] for r in good) / 1_000_000
    sec = sum(r["sec"] for r in good) / len(good)
    summary[mode] = avg
    print(f"{mode:<6} 평균 {avg:>7.1f}원  최대 {mx:>7.1f}원  평균 {sec:>5.1f}초  "
          f"(성공 {len(good)}/{len(rows)})")

if summary:
    print("-" * 70)
    print("월 예산 11,000원으로 제공 가능한 횟수")
    for mode, avg in summary.items():
        print(f"  {mode:<6} 약 {int(BUDGET/avg):>4}회")
    if "basic" in summary:
        print(f"\n무료 3회 원가: 약 {summary['basic']*3:,.0f}원")
        print(f"전환율 10% 가정 시 유료 1명당 획득 원가: 약 {summary['basic']*3*10:,.0f}원")
    print("\n이 숫자로 크레딧 차감량(기본 1 / 심층 5)이 맞는지 다시 보세요.")
    if "basic" in summary and "deep" in summary:
        print(f"실측 비율: 심층 / 기본 = {summary['deep']/summary['basic']:.1f}배")
""")

md("""
## 15. 다음 단계

| 항목 | 상태 | 할 일 |
|---|---|---|
| Firebase Google 로그인 | 콘솔 작업 | Authentication 에서 공급자 켜고 승인된 도메인 추가 |
| 크레딧 제공량 확정 | 14단계 결과 필요 | 실측 평균으로 기본 1 / 심층 5 비율 재검토 |
| 카페24 상품 등록 | 미착수 | 월 22,000원 이용권과 추가 충전을 판매 대기로 등록 |
| 카페24 OAuth · 웹훅 | 미착수 | 개발자 앱 등록, 주문 조회 권한 승인, 웹훅 연결 |
| 결제 확인 → 권한 부여 | 미구현 | `app.py` 에 주문 검증과 크레딧 적립 경로 추가 |
| 예산 알림 | 미설정 | 결제 계정에 월 예산과 임계값 알림 설정 |
| 사업자 정보 표기 | 미작성 | 상호·대표자·사업자등록번호·통신판매업 신고번호 |

`payments_connected` 가 `false` 인 동안에는 구매 버튼이 닫혀 있어 유료 전환이 불가능합니다.
무료 3회까지만 동작하는 상태가 정상입니다.
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
        "colab": {"provenance": [], "toc_visible": True, "name": "BSM_AI_Research_RUN_v1.ipynb"},
        "kernelspec": {"name": "python3", "display_name": "Python 3"},
        "language_info": {"name": "python"},
    },
    "nbformat": 4, "nbformat_minor": 0,
}
out = "/home/user/chatbot/notebooks/research/BSM_AI_Research_RUN_v1.ipynb"
io.open(out, "w", encoding="utf-8").write(json.dumps(nb, ensure_ascii=False, indent=1))
print("생성:", out, "| 셀:", len(C))
