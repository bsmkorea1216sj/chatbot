"""노트북 1~14단계를 gcloud 없이 REST 로 수행합니다. 각 단계는 따로, 반복 실행해도 안전합니다."""
import json
import os
import shutil
import subprocess
import sys
import tarfile
import time
from pathlib import Path

import conf
from gcp import ApiError, api, get_or_none, session, wait_lro, whoami

CRM = "https://cloudresourcemanager.googleapis.com/v3"
SU = "https://serviceusage.googleapis.com/v1"
IAM = "https://iam.googleapis.com/v1"
FS = "https://firestore.googleapis.com/v1"
TASKS = "https://cloudtasks.googleapis.com/v2"
SM = "https://secretmanager.googleapis.com/v1"
FB = "https://firebase.googleapis.com/v1beta1"
AR = "https://artifactregistry.googleapis.com/v1"
CB = "https://cloudbuild.googleapis.com/v1"
RUN = "https://run.googleapis.com/v2"
GCS = "https://storage.googleapis.com/storage/v1"
GCS_UP = "https://storage.googleapis.com/upload/storage/v1"

P = conf.PROJECT_ID


def _ok(msg):
    print(f"  OK   {msg}", flush=True)


def _info(msg):
    print(f"       {msg}", flush=True)


# ── 1. 인증 확인 ──────────────────────────────────────────────────────────
def step01_auth():
    email, key_project = whoami()
    _ok(f"인증 주체: {email}")
    if key_project and key_project != P:
        _info(f"경고: 키의 프로젝트({key_project})와 대상 프로젝트({P})가 다릅니다.")
    proj = get_or_none(f"{CRM}/projects/{P}")
    if not proj:
        raise RuntimeError(f"프로젝트 {P} 에 접근할 수 없습니다. 키 권한을 확인하세요.")
    number = proj["name"].split("/")[-1]
    conf.save_state(project_number=number, actor=email)
    _ok(f"프로젝트 {P} (번호 {number}) 접근 확인")
    _ok(f"상태: {proj.get('state')} | 표시명: {proj.get('displayName')}")
    return {"project_number": number, "actor": email}


# ── 2. 설정 점검 ──────────────────────────────────────────────────────────
def step02_config():
    print(f"  프로젝트 {P} | 리전 {conf.REGION} | 모델 {conf.MODEL}")
    print(f"  서비스 {conf.SERVICE} | 큐 {conf.QUEUE} | 가격 버전 {conf.PRICE_VERSION}")
    print(f"  런타임 계정 {conf.RUN_SA}")
    print(f"  호출 계정   {conf.TASKS_SA}")
    print(f"  앱 소스     {conf.APP_SRC}")
    gaps = conf.missing_prices()
    if gaps:
        _info("아직 비어 있는 단가: " + ", ".join(gaps))
        _info("12단계 배포 전까지 환경변수로 채워야 합니다. 비면 앱이 503 으로 실패합니다.")
    else:
        _ok(f"단가 입력 완료 (입력 ${conf.INPUT_USD_PER_MILLION}/M, "
            f"출력 ${conf.OUTPUT_USD_PER_MILLION}/M, {conf.KRW_PER_USD}원/USD, "
            f"검색 상한 {conf.GROUNDING_MAX_MICRO_KRW // 1_000_000}원)")
    if not conf.APP_SRC.exists():
        raise RuntimeError(f"앱 소스가 없습니다: {conf.APP_SRC}")
    _ok(f"앱 소스 파일 {len(list(conf.APP_SRC.glob('*')))}개 확인")
    return {"missing_prices": gaps}


# ── 3. API 활성화 ─────────────────────────────────────────────────────────
def step03_enable_apis():
    number = conf.state().get("project_number") or step01_auth()["project_number"]
    enabled = set()
    page = None
    while True:
        res = api("GET", f"{SU}/projects/{number}/services",
                  params={"filter": "state:ENABLED", "pageSize": 200,
                          **({"pageToken": page} if page else {})})
        enabled |= {s["config"]["name"] for s in res.get("services", [])}
        page = res.get("nextPageToken")
        if not page:
            break
    todo = [a for a in conf.APIS if a not in enabled]
    if not todo:
        _ok(f"필요한 API {len(conf.APIS)}개 모두 이미 활성화됨")
        return {"enabled_now": []}
    _info(f"활성화할 API {len(todo)}개: " + ", ".join(s.split('.')[0] for s in todo))
    op = api("POST", f"{SU}/projects/{number}/services:batchEnable",
             body={"serviceIds": todo})
    wait_lro(op, poll_url=f"{SU}/{op['name']}", label="API 활성화")
    _ok(f"API {len(todo)}개 활성화 완료")
    return {"enabled_now": todo}


# ── 4. Firestore + Cloud Tasks 큐 ─────────────────────────────────────────
def step04_firestore_and_queue():
    out = {}
    db = get_or_none(f"{FS}/projects/{P}/databases/(default)")
    if db:
        _ok(f"Firestore 이미 있음: {db.get('type')} @ {db.get('locationId')}")
        if db.get("type") != "FIRESTORE_NATIVE":
            raise RuntimeError(f"Firestore 유형이 {db.get('type')} 입니다. Native 모드가 필요합니다.")
    else:
        _info(f"Firestore Native 생성 중 ({conf.FS_LOCATION}) — 1~2분 걸립니다.")
        op = api("POST", f"{FS}/projects/{P}/databases",
                 params={"databaseId": "(default)"},
                 body={"locationId": conf.FS_LOCATION, "type": "FIRESTORE_NATIVE",
                       "concurrencyMode": "PESSIMISTIC"})
        wait_lro(op, poll_url=f"{FS}/{op['name']}", label="Firestore 생성")
        _ok("Firestore Native 생성 완료")
    out["firestore"] = "ready"

    qpath = f"projects/{P}/locations/{conf.REGION}/queues/{conf.QUEUE}"
    # 동시 실행과 재시도를 제한해 폭주와 중복 과금을 막습니다.
    wanted = {"rateLimits": {"maxConcurrentDispatches": 5, "maxDispatchesPerSecond": 5.0},
              "retryConfig": {"maxAttempts": 3, "minBackoff": "30s", "maxBackoff": "300s"}}
    q = get_or_none(f"{TASKS}/{qpath}")
    if q:
        _ok(f"큐 이미 있음: {conf.QUEUE} (상태 {q.get('state')})")
        api("PATCH", f"{TASKS}/{qpath}", body=wanted,
            params={"updateMask": "rateLimits.maxConcurrentDispatches,"
                                  "rateLimits.maxDispatchesPerSecond,retryConfig"})
    else:
        api("POST", f"{TASKS}/projects/{P}/locations/{conf.REGION}/queues",
            body={"name": qpath, **wanted})
        _ok(f"큐 생성: {conf.QUEUE}")
    _ok("큐 설정: 동시 5건, 최대 3회 시도, 최소 대기 30초")
    out["queue"] = qpath
    return out


# ── 5. 서비스 계정과 IAM ──────────────────────────────────────────────────
def _ensure_sa(email, display):
    if get_or_none(f"{IAM}/projects/{P}/serviceAccounts/{email}"):
        _ok(f"이미 있음: {email}")
        return False
    api("POST", f"{IAM}/projects/{P}/serviceAccounts",
        body={"accountId": email.split("@")[0], "serviceAccount": {"displayName": display}})
    _ok(f"생성: {email}")
    time.sleep(5)  # IAM 전파 대기
    return True


def _bind_project_roles(pairs):
    """프로젝트 IAM 정책에 (member, role) 여럿을 한 번에 추가합니다. etag 충돌은 재시도합니다."""
    for attempt in range(5):
        policy = api("POST", f"{CRM}/projects/{P}:getIamPolicy",
                     body={"options": {"requestedPolicyVersion": 3}})
        bindings = policy.setdefault("bindings", [])
        added = []
        for member, role in pairs:
            found = next((b for b in bindings
                          if b.get("role") == role and not b.get("condition")), None)
            if found is None:
                bindings.append({"role": role, "members": [member]})
                added.append((member, role))
            elif member not in found.setdefault("members", []):
                found["members"].append(member)
                added.append((member, role))
        if not added:
            return []
        try:
            api("POST", f"{CRM}/projects/{P}:setIamPolicy", body={"policy": policy})
            return added
        except ApiError as exc:
            if exc.status == 409 and attempt < 4:
                time.sleep(2 ** attempt)
                continue
            raise
    return []


def _bind_resource_role(base, resource, member, role):
    policy = api("POST", f"{base}/{resource}:getIamPolicy") or {}
    bindings = policy.setdefault("bindings", [])
    found = next((b for b in bindings if b.get("role") == role), None)
    if found and member in found.get("members", []):
        return False
    if found:
        found["members"].append(member)
    else:
        bindings.append({"role": role, "members": [member]})
    api("POST", f"{base}/{resource}:setIamPolicy", body={"policy": policy})
    return True


def step05_service_accounts():
    _ensure_sa(conf.RUN_SA, "BSM Research Runtime")
    _ensure_sa(conf.TASKS_SA, "BSM Research Tasks Invoker")
    added = _bind_project_roles([(f"serviceAccount:{conf.RUN_SA}", r) for r in conf.RUN_SA_ROLES])
    if added:
        _ok("런타임 계정에 부여: " + ", ".join(r.split('/')[-1] for _, r in added))
    else:
        _ok("런타임 계정 권한 이미 설정됨")
    # Cloud Tasks 작업에 OIDC 토큰을 붙이려면 런타임 계정이 호출 계정을 대신할 수 있어야 합니다.
    changed = _bind_resource_role(f"{IAM}/projects/{P}/serviceAccounts", conf.TASKS_SA,
                                  f"serviceAccount:{conf.RUN_SA}", "roles/iam.serviceAccountUser")
    _ok("런타임 계정 → 호출 계정 serviceAccountUser " + ("부여" if changed else "이미 있음"))
    _info("호출 계정의 run.invoker 는 12단계 배포 후에 붙습니다.")
    return {"run_sa": conf.RUN_SA, "tasks_sa": conf.TASKS_SA}


# ── 6. Secret Manager ─────────────────────────────────────────────────────
def step06_secrets():
    """GEMINI_API_KEY 는 환경변수에서만 읽고 값은 출력하지 않습니다."""
    name = "GEMINI_API_KEY"
    value = os.environ.get("GEMINI_API_KEY", "").strip()
    sec = get_or_none(f"{SM}/projects/{P}/secrets/{name}")
    if not sec:
        api("POST", f"{SM}/projects/{P}/secrets", params={"secretId": name},
            body={"replication": {"automatic": {}}})
        _ok(f"시크릿 생성: {name}")
    else:
        _ok(f"시크릿 이미 있음: {name}")

    versions = api("GET", f"{SM}/projects/{P}/secrets/{name}/versions",
                   params={"filter": "state:ENABLED", "pageSize": 1}).get("versions", [])
    if value:
        import base64
        api("POST", f"{SM}/projects/{P}/secrets/{name}:addSecretVersion",
            body={"payload": {"data": base64.b64encode(value.encode()).decode()}})
        _ok(f"새 버전 저장 완료 (길이 {len(value)}자, 값은 출력하지 않습니다)")
    elif versions:
        _ok("기존 버전을 그대로 사용합니다.")
    else:
        raise RuntimeError(
            "GEMINI_API_KEY 환경변수가 비어 있고 저장된 버전도 없습니다. "
            "환경 시크릿에 GEMINI_API_KEY 를 등록하고 다시 실행하세요. 채팅에 붙여넣지 마세요.")

    changed = _bind_resource_role(f"{SM}/projects/{P}/secrets", name,
                                  f"serviceAccount:{conf.RUN_SA}",
                                  "roles/secretmanager.secretAccessor")
    _ok("런타임 계정 읽기 권한 " + ("부여" if changed else "이미 있음"))
    return {"secret": name}


# ── 7. Firebase 웹 구성 ───────────────────────────────────────────────────
def step07_firebase_config():
    if os.environ.get("FIREBASE_WEB_CONFIG", "").strip():
        cfg = json.loads(os.environ["FIREBASE_WEB_CONFIG"])
        _ok("환경변수로 받은 구성을 사용합니다.")
    else:
        if not get_or_none(f"{FB}/projects/{P}"):
            _info("프로젝트에 Firebase 를 추가합니다.")
            op = api("POST", f"{FB}/projects/{P}:addFirebase", body={})
            wait_lro(op, poll_url=f"{FB}/{op['name']}", label="Firebase 추가")
        apps = api("GET", f"{FB}/projects/{P}/webApps").get("apps", [])
        if apps:
            app = apps[0]
            _ok(f"웹 앱 이미 있음: {app.get('displayName') or app['appId']}")
        else:
            op = api("POST", f"{FB}/projects/{P}/webApps",
                     body={"displayName": "AI 리서치 웹"})
            app = wait_lro(op, poll_url=f"{FB}/{op['name']}", label="웹 앱 생성")
            _ok(f"웹 앱 생성: {app['appId']}")
        cfg = api("GET", f"{FB}/projects/{P}/webApps/{app['appId']}/config")
        cfg.pop("@type", None)
    for key in ("apiKey", "authDomain", "projectId", "appId"):
        if key not in cfg:
            raise RuntimeError(f"웹 구성에 {key} 가 없습니다: {sorted(cfg)}")
    print(f"       apiKey     : {str(cfg['apiKey'])[:10]}...")
    print(f"       authDomain : {cfg['authDomain']}")
    print(f"       projectId  : {cfg['projectId']}")
    conf.save_state(firebase_web_config=json.dumps(cfg, ensure_ascii=False, separators=(",", ":")))
    _info("Firebase 콘솔 > Authentication > Google 공급자를 켜야 로그인이 동작합니다.")
    return {"authDomain": cfg["authDomain"]}


# ── 8. 빌드 사본 준비 ─────────────────────────────────────────────────────
def step08_stage_source():
    dest = conf.BUILD_DIR / "app"
    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(conf.APP_SRC, dest,
                    ignore=shutil.ignore_patterns("PROVENANCE.md", "__pycache__", "*.pyc"))
    files = sorted(p.name for p in dest.iterdir())
    _ok(f"빌드 사본 준비: {dest} ({len(files)}개 파일)")
    for name in files:
        print(f"         - {name}")
    conf.save_state(build_app=str(dest))
    return {"files": files}


# ── 9. 모델 잠금 패치 ─────────────────────────────────────────────────────
OLD_LOCK = """    # Only Gemini 2.5 Flash is allowed here: search is billed per grounded prompt.
    # Reserve the full model input window including grounding/tool tokens.
    if os.getenv('GEMINI_MODEL', 'gemini-2.5-flash') != 'gemini-2.5-flash':
        raise ValueError('Unreviewed model pricing')"""

NEW_LOCK = """    # 검토를 마친 모델만 허용합니다. 모델명과 입력 창은 운영 설정으로 받습니다.
    # 검색은 grounded prompt 단위로 과금되므로 입력 창 전체를 예약합니다.
    model = os.getenv('GEMINI_MODEL', '')
    reviewed = {m.strip() for m in os.getenv('REVIEWED_MODELS', '').split(',') if m.strip()}
    if not model or model not in reviewed:
        raise ValueError('Unreviewed model pricing')"""


def step09_patch_model_lock():
    path = Path(conf.state().get("build_app") or (conf.BUILD_DIR / "app")) / "app.py"
    if not path.exists():
        raise RuntimeError("빌드 사본이 없습니다. 8단계를 먼저 실행하세요.")
    src = path.read_text(encoding="utf-8")
    if "REVIEWED_MODELS" in src:
        _ok("이미 패치되어 있습니다.")
    elif OLD_LOCK in src:
        src = src.replace(OLD_LOCK, NEW_LOCK, 1)
        src = src.replace("    cap = token_cost(1_048_576, output,",
                          "    cap = token_cost(positive_env('MODEL_INPUT_WINDOW'), output,", 1)
        src = src.replace("'output': output, 'model': 'gemini-2.5-flash',",
                          "'output': output, 'model': model,", 1)
        path.write_text(src, encoding="utf-8")
        _ok("패치 적용: 모델 잠금 해제 (2.5 계열은 2026-10-16 종료)")
    else:
        raise RuntimeError("quote() 원문을 찾지 못했습니다. 원본이 바뀌었는지 확인하세요.")
    import ast
    ast.parse(src)
    _ok("패치본 구문 검사 통과")
    for line in src.split("\n"):
        if any(k in line for k in ("REVIEWED_MODELS", "MODEL_INPUT_WINDOW", "'model': model")):
            print(f"         {line.strip()[:100]}")
    return {"patched": str(path)}


# ── 10. 단위 테스트 ───────────────────────────────────────────────────────
def step10_tests():
    appdir = Path(conf.state().get("build_app") or (conf.BUILD_DIR / "app"))
    venv = conf.BUILD_DIR / "venv"
    py = venv / "bin" / "python"
    if not py.exists():
        _info("테스트용 가상환경을 만듭니다. 처음에는 1~2분 걸립니다.")
        subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
        subprocess.run([str(py), "-m", "pip", "install", "-q", "--upgrade", "pip"], check=True)
    r = subprocess.run([str(py), "-m", "pip", "install", "-q",
                        "-r", str(appdir / "requirements.txt"), "httpx"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        _info("의존성 설치 경고: " + r.stderr[-400:])
    r = subprocess.run([str(py), "-m", "unittest", "discover", "-s", str(appdir), "-p", "test_*.py"],
                       capture_output=True, text=True, cwd=str(appdir))
    print((r.stdout or "")[-1500:])
    print((r.stderr or "")[-2500:])
    if r.returncode != 0:
        raise RuntimeError("테스트 실패. 배포하지 마세요.")
    _ok("테스트 통과")
    return {"tests": "passed"}


# ── 11. 무료 체험 예산 시드 ───────────────────────────────────────────────
def step11_seed_trial_pool():
    doc = f"{FS}/projects/{P}/databases/(default)/documents/budgets/trial_pool"
    cur = get_or_none(doc) or {}
    fields = cur.get("fields", {})

    def num(key):
        return int(fields.get(key, {}).get("integerValue", 0) or 0)

    granted = conf.TRIAL_POOL_KRW * 1_000_000  # 마이크로원
    if num("granted"):
        _ok(f"기존 예산: {num('granted') // 1_000_000:,}원 "
            f"| 사용 {num('spent') // 1_000_000:,}원 "
            f"| 예약 {num('reserved') // 1_000_000:,}원")
        if os.environ.get("RESET_TRIAL_POOL") != "1":
            _info("바꾸려면 RESET_TRIAL_POOL=1 로 다시 실행하세요.")
            return {"granted_krw": num("granted") // 1_000_000, "changed": False}
        api("PATCH", doc, params={"updateMask.fieldPaths": "granted"},
            body={"fields": {"granted": {"integerValue": str(granted)}}})
        _ok(f"예산 갱신: {conf.TRIAL_POOL_KRW:,}원")
        return {"granted_krw": conf.TRIAL_POOL_KRW, "changed": True}
    api("PATCH", doc,
        params=[("updateMask.fieldPaths", "granted"), ("updateMask.fieldPaths", "spent"),
                ("updateMask.fieldPaths", "reserved")],
        body={"fields": {"granted": {"integerValue": str(granted)},
                         "spent": {"integerValue": "0"},
                         "reserved": {"integerValue": "0"}}})
    _ok(f"무료 체험 예산 설정: {conf.TRIAL_POOL_KRW:,}원")
    return {"granted_krw": conf.TRIAL_POOL_KRW, "changed": True}


# ── 12. Cloud Run 배포 (gcloud 없이 Cloud Build + Run API) ────────────────
def _ensure_ar_repo():
    base = f"{AR}/projects/{P}/locations/{conf.REGION}/repositories"
    if get_or_none(f"{base}/{conf.AR_REPO}"):
        _ok(f"Artifact Registry 저장소 이미 있음: {conf.AR_REPO}")
        return
    op = api("POST", base, params={"repositoryId": conf.AR_REPO},
             body={"format": "DOCKER", "description": "BSM AI 리서치 컨테이너"})
    wait_lro(op, poll_url=f"{AR}/{op['name']}", label="저장소 생성")
    _ok(f"Artifact Registry 저장소 생성: {conf.AR_REPO}")


def _ensure_bucket():
    bucket = os.environ.get("BUILD_BUCKET", f"{P}-bsm-build")
    if get_or_none(f"{GCS}/b/{bucket}"):
        _ok(f"빌드 버킷 이미 있음: {bucket}")
        return bucket
    api("POST", f"{GCS}/b", params={"project": P},
        body={"name": bucket, "location": conf.REGION.upper(),
              "storageClass": "STANDARD",
              "iamConfiguration": {"uniformBucketLevelAccess": {"enabled": True}},
              "lifecycle": {"rule": [{"action": {"type": "Delete"},
                                      "condition": {"age": 30}}]}})
    _ok(f"빌드 버킷 생성: {bucket} (30일 후 자동 삭제)")
    return bucket


def _upload_source(bucket, appdir):
    tar_path = conf.BUILD_DIR / "source.tar.gz"
    if tar_path.exists():
        tar_path.unlink()
    with tarfile.open(tar_path, "w:gz") as tar:
        for item in sorted(Path(appdir).iterdir()):
            if item.name in ("__pycache__",) or item.suffix == ".pyc":
                continue
            tar.add(item, arcname=item.name)
    obj = f"source/{int(time.time())}.tar.gz"
    with open(tar_path, "rb") as fh:
        resp = session().post(f"{GCS_UP}/b/{bucket}/o",
                              params={"uploadType": "media", "name": obj},
                              data=fh.read(),
                              headers={"Content-Type": "application/gzip"}, timeout=300)
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"소스 업로드 실패 {resp.status_code}: {resp.text[:300]}")
    _ok(f"소스 업로드: gs://{bucket}/{obj} ({tar_path.stat().st_size:,} 바이트)")
    return obj


def _build_image(bucket, obj):
    tag = time.strftime("%Y%m%d-%H%M%S")
    image = f"{conf.REGION}-docker.pkg.dev/{P}/{conf.AR_REPO}/{conf.SERVICE}:{tag}"
    build = {
        "source": {"storageSource": {"bucket": bucket, "object": obj}},
        "steps": [{"name": "gcr.io/cloud-builders/docker",
                   "args": ["build", "-t", image, "."]}],
        "images": [image],
        "timeout": "1200s",
        "options": {"logging": "CLOUD_LOGGING_ONLY", "machineType": "E2_HIGHCPU_8"},
    }
    sa = os.environ.get("CLOUDBUILD_SA", "").strip()
    if sa:
        build["serviceAccount"] = f"projects/{P}/serviceAccounts/{sa}"
    _info("컨테이너 빌드를 시작합니다. 첫 빌드는 3~5분 걸립니다.")
    op = api("POST", f"{CB}/projects/{P}/builds", body=build, timeout=180)
    build_id = (op.get("metadata") or {}).get("build", {}).get("id", "")
    if build_id:
        _info(f"빌드 ID {build_id}")
    done = wait_lro(op, poll_url=f"{CB}/{op['name']}", label="컨테이너 빌드",
                    timeout=1500, interval=15)
    status = done.get("status", "")
    if status != "SUCCESS":
        log = done.get("logUrl", "")
        raise RuntimeError(f"빌드 실패 (status={status}). 로그: {log}")
    _ok(f"빌드 성공: {image}")
    return image


def _service_body(image, envs, web_config):
    env = [{"name": k, "value": str(v)} for k, v in envs.items()]
    env.append({"name": "FIREBASE_WEB_CONFIG", "value": web_config})
    env.append({"name": "GEMINI_API_KEY",
                "valueSource": {"secretKeyRef": {"secret": "GEMINI_API_KEY",
                                                 "version": "latest"}}})
    return {
        "ingress": "INGRESS_TRAFFIC_ALL",
        "launchStage": "GA",
        "template": {
            "serviceAccount": conf.RUN_SA,
            "timeout": "300s",
            "maxInstanceRequestConcurrency": 10,
            "scaling": {"minInstanceCount": 0, "maxInstanceCount": 3},
            "containers": [{
                "image": image,
                "ports": [{"name": "http1", "containerPort": 8080}],
                "resources": {"limits": {"cpu": "1", "memory": "1Gi"},
                              "cpuIdle": True},
                "env": env,
            }],
        },
    }


def step12_deploy():
    gaps = conf.missing_prices()
    if gaps:
        raise RuntimeError("단가가 비어 있습니다: " + ", ".join(gaps)
                           + " — 환경변수로 채우고 다시 실행하세요.")
    web_config = conf.state().get("firebase_web_config", "")
    if not web_config:
        raise RuntimeError("FIREBASE_WEB_CONFIG 가 없습니다. 7단계를 먼저 끝내세요.")
    appdir = Path(conf.state().get("build_app") or (conf.BUILD_DIR / "app"))
    if "REVIEWED_MODELS" not in (appdir / "app.py").read_text(encoding="utf-8"):
        raise RuntimeError("빌드 사본에 패치가 없습니다. 9단계를 먼저 실행하세요.")

    _ensure_ar_repo()
    bucket = _ensure_bucket()
    obj = _upload_source(bucket, appdir)
    image = _build_image(bucket, obj)

    envs = {
        "GOOGLE_CLOUD_PROJECT": P,
        "TASKS_REGION": conf.REGION,
        "TASKS_QUEUE": conf.QUEUE,
        "TASKS_SA": conf.TASKS_SA,
        "GEMINI_MODEL": conf.MODEL,
        "REVIEWED_MODELS": conf.MODEL,
        "MODEL_INPUT_WINDOW": conf.MODEL_INPUT_WINDOW,
        "INPUT_USD_PER_MILLION": conf.INPUT_USD_PER_MILLION,
        "OUTPUT_USD_PER_MILLION": conf.OUTPUT_USD_PER_MILLION,
        "KRW_PER_USD": conf.KRW_PER_USD,
        "GROUNDING_MAX_MICRO_KRW": conf.GROUNDING_MAX_MICRO_KRW,
        "PRICE_VERSION": conf.PRICE_VERSION,
        "PURCHASE_URL": conf.PURCHASE_URL,
        "SERVICE_URL": "https://placeholder.invalid",
    }
    base = f"{RUN}/projects/{P}/locations/{conf.REGION}/services"
    svc_path = f"{base}/{conf.SERVICE}"
    body = _service_body(image, envs, web_config)
    if get_or_none(svc_path):
        _info("기존 서비스를 갱신합니다.")
        op = api("PATCH", svc_path, body=body, timeout=180)
    else:
        _info("새 서비스를 만듭니다.")
        op = api("POST", base, params={"serviceId": conf.SERVICE}, body=body, timeout=180)
    svc = wait_lro(op, poll_url=f"{RUN}/{op['name']}", label="Cloud Run 배포",
                   timeout=900, interval=10)
    url = svc.get("uri") or api("GET", svc_path).get("uri", "")
    if not url:
        raise RuntimeError("서비스 주소를 확인하지 못했습니다.")
    _ok(f"서비스 주소: {url}")

    # 주소가 정해졌으니 OIDC 대상과 호출 권한을 맞춥니다.
    envs["SERVICE_URL"] = url
    op = api("PATCH", svc_path, body=_service_body(image, envs, web_config), timeout=180)
    wait_lro(op, poll_url=f"{RUN}/{op['name']}", label="SERVICE_URL 주입",
             timeout=600, interval=8)
    _ok("SERVICE_URL 주입 완료")

    policy = {"bindings": [
        {"role": "roles/run.invoker",
         "members": ["allUsers", f"serviceAccount:{conf.TASKS_SA}"]}]}
    api("POST", f"{svc_path}:setIamPolicy", body={"policy": policy})
    _ok("공개 접근 + 호출 계정 run.invoker 부여")

    conf.save_state(service_url=url, image=image)
    print()
    _info("Firebase 콘솔에서 두 가지를 하세요.")
    _info("  1. Authentication > 시작하기 > Google 공급자 사용 설정")
    _info(f"  2. Authentication > 설정 > 승인된 도메인에 추가: {url.replace('https://', '')}")
    return {"service_url": url, "image": image}


# ── 13. 스모크 테스트 ─────────────────────────────────────────────────────
def step13_smoke():
    import urllib.error
    import urllib.request
    url = conf.state().get("service_url") or os.environ.get("SERVICE_URL", "")
    if not url:
        raise RuntimeError("서비스 주소가 없습니다. 12단계를 먼저 실행하세요.")

    def get(path, token=None):
        req = urllib.request.Request(url.rstrip("/") + path)
        if token:
            req.add_header("Authorization", "Bearer " + token)
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                return resp.status, resp.read().decode("utf-8")[:400]
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode("utf-8")[:300]
        except Exception as exc:
            return 0, f"{type(exc).__name__}: {exc}"

    checks = []
    s, b = get("/health")
    checks.append(("GET /health", s == 200, s, b))
    s, b = get("/")
    checks.append(("GET / (화면)", s == 200, s, b[:80] + "..."))
    s, cfg_body = get("/api/config")
    checks.append(("GET /api/config", s == 200, s, cfg_body))
    s, b = get("/api/account")
    checks.append(("GET /api/account 무인증 차단", s == 401, s, b))
    s, b = get("/api/account", token="bogus")
    checks.append(("GET /api/account 잘못된 토큰 차단", s == 401, s, b))

    print(f"  {'판정':<6}{'항목':<38}{'상태'}")
    print("  " + "-" * 72)
    passed = 0
    for name, good, status, body in checks:
        passed += good
        print(f"  {'통과' if good else '실패':<6}{name:<38}{status}")
        if not good:
            print(f"         {body}")
    print("  " + "-" * 72)
    print(f"  {passed}/{len(checks)} 통과")

    try:
        cfg = json.loads(cfg_body)
        print(f"\n  결제 연결 상태: {'열림' if cfg.get('payments_connected') else '닫힘 (정상 — 카페24 연동 전)'}")
        print(f"  구매 링크: {cfg.get('purchase_url') or '(미설정)'}")
        fb = cfg.get("firebase") or {}
        print(f"  Firebase authDomain: {fb.get('authDomain') or '(없음)'}")
    except ValueError:
        pass
    print(f"\n  브라우저에서 열어 로그인까지 확인하세요: {url}")
    if passed != len(checks):
        raise RuntimeError(f"스모크 테스트 {len(checks) - passed}건 실패")
    return {"passed": passed, "total": len(checks)}


# ── 14. 원가 측정 ─────────────────────────────────────────────────────────
MEASURE = r'''
import json, os, sys, time
sys.path.insert(0, os.environ["APPDIR"])
from research import generate, AccountedFailure

MODEL = os.environ["GEMINI_MODEL"]
RATES = {k: os.environ[k] for k in
         ("INPUT_USD_PER_MILLION", "OUTPUT_USD_PER_MILLION", "KRW_PER_USD")}
GROUND = int(os.environ["GROUNDING_MAX_MICRO_KRW"])
TOPICS = ["국내 중소기업의 생성형 AI 도입 현황",
          "한국 전자상거래 반품 정책 규제 동향",
          "국내 클라우드 전환 비용 구조",
          "생성형 AI 저작권 분쟁 국내 판례",
          "국내 구독 결제 시장 경쟁 구도"]

def measure(mode, n):
    rows = []
    for i in range(n):
        job = {"request": {"topic": TOPICS[i % len(TOPICS)],
                           "categories": ["공식자료", "논문"]},
               "pricing": {"model": MODEL, "output": 2048 if mode == "basic" else 4096,
                           "rates": RATES, "grounding": GROUND,
                           "cap": 10 ** 15}}   # 측정이므로 상한을 두지 않습니다
        t0 = time.time()
        try:
            cost, output = generate(job)
            rows.append({"ok": True, "cost": cost, "sec": time.time() - t0,
                         "chars": len(output["report"]), "sources": len(output["sources"])})
            print(f"  {mode} {i+1}/{n}  {cost/1_000_000:>7.1f}원  "
                  f"{time.time()-t0:>5.1f}초  출처 {len(output['sources'])}건", flush=True)
        except AccountedFailure as exc:
            rows.append({"ok": False, "cost": exc.cost, "sec": time.time() - t0})
            print(f"  {mode} {i+1}/{n}  실패 (비용 {exc.cost/1_000_000:.1f}원 발생)", flush=True)
        except Exception as exc:
            rows.append({"ok": False, "cost": 0, "sec": time.time() - t0,
                         "err": f"{type(exc).__name__}: {str(exc)[:160]}"})
            print(f"  {mode} {i+1}/{n}  오류: {type(exc).__name__} {str(exc)[:140]}", flush=True)
    return rows

print(f"모델 {MODEL} 로 측정합니다.\n")
res = {"basic": measure("basic", int(os.environ.get("N_BASIC", "3"))),
       "deep": measure("deep", int(os.environ.get("N_DEEP", "2")))}
json.dump(res, open(os.environ["OUT"], "w", encoding="utf-8"), ensure_ascii=False)
'''


def step14_measure_cost():
    appdir = Path(conf.state().get("build_app") or (conf.BUILD_DIR / "app"))
    py = conf.BUILD_DIR / "venv" / "bin" / "python"
    if not py.exists():
        raise RuntimeError("테스트 환경이 없습니다. 10단계를 먼저 실행하세요.")
    gaps = conf.missing_prices()
    if gaps:
        raise RuntimeError("단가가 비어 있습니다: " + ", ".join(gaps))
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        import base64
        ver = get_or_none(f"{SM}/projects/{P}/secrets/GEMINI_API_KEY/versions/latest:access")
        if ver:
            key = base64.b64decode(ver["payload"]["data"]).decode()
    if not key:
        raise RuntimeError("GEMINI_API_KEY 를 읽지 못했습니다. 6단계를 확인하세요.")

    script = conf.BUILD_DIR / "measure.py"
    script.write_text(MEASURE, encoding="utf-8")
    out = conf.BUILD_DIR / "cost.json"
    env = {**os.environ, "APPDIR": str(appdir), "OUT": str(out),
           "GEMINI_API_KEY": key, "GEMINI_MODEL": conf.MODEL,
           "INPUT_USD_PER_MILLION": conf.INPUT_USD_PER_MILLION,
           "OUTPUT_USD_PER_MILLION": conf.OUTPUT_USD_PER_MILLION,
           "KRW_PER_USD": conf.KRW_PER_USD,
           "GROUNDING_MAX_MICRO_KRW": str(conf.GROUNDING_MAX_MICRO_KRW)}
    proc = subprocess.run([str(py), str(script)], env=env, cwd=str(appdir),
                          capture_output=True, text=True, timeout=1800)
    print(proc.stdout[-4000:])
    if proc.returncode != 0:
        print(proc.stderr[-2000:])
        raise RuntimeError("측정 실행 실패")

    res = json.loads(out.read_text(encoding="utf-8"))
    budget = int(conf.MONTHLY_PRICE_KRW * conf.BUDGET_RATIO)
    print("=" * 70)
    summary = {}
    for mode, rows in res.items():
        good = [r for r in rows if r.get("ok")]
        if not good:
            print(f"  {mode:<6} 성공한 측정이 없습니다.")
            continue
        avg = sum(r["cost"] for r in good) / len(good) / 1_000_000
        mx = max(r["cost"] for r in good) / 1_000_000
        sec = sum(r["sec"] for r in good) / len(good)
        summary[mode] = avg
        print(f"  {mode:<6} 평균 {avg:>7.1f}원  최대 {mx:>7.1f}원  "
              f"평균 {sec:>5.1f}초  (성공 {len(good)}/{len(rows)})")
    if summary:
        print("-" * 70)
        print(f"  월 예산 {budget:,}원으로 제공 가능한 횟수")
        for mode, avg in summary.items():
            print(f"    {mode:<6} 약 {int(budget / avg):>4}회")
        if "basic" in summary:
            print(f"\n  무료 3회 원가: 약 {summary['basic'] * 3:,.0f}원")
            print(f"  전환율 10% 가정 시 유료 1명당 획득 원가: 약 {summary['basic'] * 3 * 10:,.0f}원")
        if "basic" in summary and "deep" in summary:
            ratio = summary["deep"] / summary["basic"]
            print(f"\n  심층/기본 원가 비율: {ratio:.1f}배 "
                  f"(현재 크레딧 차감은 5배 — {'타당' if ratio <= 5 else '차감량 상향 필요'})")
    conf.save_state(cost_summary=summary)
    return {"summary": summary, "raw": str(out)}


# ── 15. 기본 도메인 URL 발급 (Firebase Hosting → Cloud Run) ───────────────
FH = "https://firebasehosting.googleapis.com/v1beta1"


def step15_default_domain():
    """Cloud Run 의 긴 기본 주소 대신 {프로젝트}.web.app 기본 도메인으로 열어줍니다.

    사용자 지정 도메인을 사지 않고도 바로 쓸 수 있는 주소입니다.
    Hosting 은 모든 경로를 Cloud Run 서비스로 넘깁니다(rewrite).
    """
    run_url = conf.state().get("service_url")
    if not run_url:
        svc = get_or_none(f"{RUN}/projects/{P}/locations/{conf.REGION}/services/{conf.SERVICE}")
        run_url = (svc or {}).get("uri", "")
    if not run_url:
        raise RuntimeError("Cloud Run 서비스가 없습니다. 12단계를 먼저 실행하세요.")
    _ok(f"Cloud Run 기본 주소: {run_url}")

    sites = api("GET", f"{FH}/projects/{P}/sites").get("sites", [])
    site = next((s for s in sites if s.get("type") == "DEFAULT_SITE"), None) or \
        next(iter(sites), None)
    if site is None:
        _info(f"Hosting 기본 사이트를 만듭니다: {P}")
        api("POST", f"{FH}/projects/{P}/sites", params={"siteId": P}, body={})
        site = api("GET", f"{FH}/projects/{P}/sites/{P}")
    site_name = site["name"]                      # projects/{p}/sites/{site}
    site_id = site_name.split("/")[-1]
    default_url = site.get("defaultUrl") or f"https://{site_id}.web.app"
    _ok(f"Hosting 사이트: {site_id}")

    # 모든 경로를 Cloud Run 으로 넘깁니다. 정적 파일은 올리지 않습니다.
    config = {"rewrites": [{"glob": "**",
                            "run": {"serviceId": conf.SERVICE, "region": conf.REGION}}]}
    try:
        version = api("POST", f"{FH}/{site_name}/versions", body={"config": config})
    except ApiError as exc:
        raise RuntimeError(
            f"Hosting 버전 생성 실패: {exc}\n"
            f"       리전 {conf.REGION} 이 거부되면 Cloud Run 기본 주소({run_url})를 "
            f"그대로 쓰거나 서비스를 지원 리전으로 옮기세요.") from None
    version_name = version["name"]
    api("POST", f"{FH}/{version_name}:populateFiles", body={"files": {}})
    api("PATCH", f"{FH}/{version_name}", params={"updateMask": "status"},
        body={"status": "FINALIZED"})
    api("POST", f"{FH}/{site_name}/releases", params={"versionName": version_name}, body={})
    _ok("Hosting 릴리스 완료 (모든 경로 → Cloud Run)")

    urls = {"default_domain": default_url,
            "alt_domain": f"https://{site_id}.firebaseapp.com",
            "cloud_run": run_url}
    conf.save_state(**urls)
    print()
    print(f"       기본 도메인 : {urls['default_domain']}")
    print(f"       예비 도메인 : {urls['alt_domain']}")
    print(f"       원본(Run)   : {urls['cloud_run']}")
    print()
    _info("Firebase 콘솔 > Authentication > 설정 > 승인된 도메인에 다음을 모두 넣으세요.")
    _info(f"  {site_id}.web.app, {site_id}.firebaseapp.com, "
          f"{run_url.replace('https://', '')}")
    return urls
