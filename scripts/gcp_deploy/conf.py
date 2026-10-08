"""노트북 2단계와 같은 설정. 단가만 환경변수로 받습니다."""
import datetime as dt
import os
from pathlib import Path

PROJECT_ID = os.environ.get("GCP_PROJECT", "aichat-507914")
REGION = os.environ.get("GCP_REGION", "asia-northeast3")
FS_LOCATION = os.environ.get("GCP_FS_LOCATION", "asia-northeast3")
SERVICE = os.environ.get("GCP_SERVICE", "bsm-research")
QUEUE = os.environ.get("GCP_QUEUE", "research-jobs")
AR_REPO = os.environ.get("GCP_AR_REPO", "bsm")

RUN_SA = f"bsm-research-run@{PROJECT_ID}.iam.gserviceaccount.com"
TASKS_SA = f"bsm-research-tasks@{PROJECT_ID}.iam.gserviceaccount.com"

MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
MODEL_INPUT_WINDOW = int(os.environ.get("MODEL_INPUT_WINDOW", "1048576"))

# 반드시 채워야 하는 값. 비면 12단계가 중단됩니다.
INPUT_USD_PER_MILLION = os.environ.get("INPUT_USD_PER_MILLION", "").strip()
OUTPUT_USD_PER_MILLION = os.environ.get("OUTPUT_USD_PER_MILLION", "").strip()
KRW_PER_USD = os.environ.get("KRW_PER_USD", "").strip()
GROUNDING_MAX_MICRO_KRW = int(os.environ.get("GROUNDING_MAX_MICRO_KRW", "0") or 0)
PRICE_VERSION = os.environ.get("PRICE_VERSION") or dt.date.today().strftime("%Y%m%d") + "-1"

PURCHASE_URL = os.environ.get("PURCHASE_URL", "https://bsmshop.cafe24.com")
TRIAL_POOL_KRW = int(os.environ.get("TRIAL_POOL_KRW", "50000"))

MONTHLY_PRICE_KRW = 22_000
BUDGET_RATIO = 0.5  # 서버 내부 운영 정책. 고객 안내에는 쓰지 않습니다.

REPO_ROOT = Path(__file__).resolve().parents[2]
APP_SRC = Path(os.environ.get("APP_SRC", REPO_ROOT / "services" / "research-api"))
BUILD_DIR = Path(os.environ.get("BUILD_DIR", "/tmp/bsm_build"))
STATE_FILE = Path(os.environ.get("STATE_FILE", BUILD_DIR / "state.json"))

APIS = [
    "run.googleapis.com", "cloudbuild.googleapis.com", "artifactregistry.googleapis.com",
    "firestore.googleapis.com", "cloudtasks.googleapis.com", "secretmanager.googleapis.com",
    "identitytoolkit.googleapis.com", "firebase.googleapis.com", "iam.googleapis.com",
    "generativelanguage.googleapis.com", "storage.googleapis.com",
    "cloudresourcemanager.googleapis.com", "serviceusage.googleapis.com",
    "firebasehosting.googleapis.com",
]

RUN_SA_ROLES = ["roles/datastore.user", "roles/cloudtasks.enqueuer",
                "roles/secretmanager.secretAccessor", "roles/firebaseauth.viewer"]


def missing_prices():
    gaps = [n for n, v in (("INPUT_USD_PER_MILLION", INPUT_USD_PER_MILLION),
                           ("OUTPUT_USD_PER_MILLION", OUTPUT_USD_PER_MILLION),
                           ("KRW_PER_USD", KRW_PER_USD)) if not v]
    if GROUNDING_MAX_MICRO_KRW <= 0:
        gaps.append("GROUNDING_MAX_MICRO_KRW")
    return gaps


def state():
    import json
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {}


def save_state(**kv):
    import json
    cur = state()
    cur.update(kv)
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(cur, ensure_ascii=False, indent=2), encoding="utf-8")
    return cur
