"""Google Cloud REST 호출 공통층. gcloud CLI 없이 동작합니다.

인증은 서비스 계정 키만 씁니다. 키는 환경변수로 받고 값은 절대 출력하지 않습니다.
  GCP_SA_KEY                  : 키 JSON 본문 (권장: 환경 시크릿으로 주입)
  GOOGLE_APPLICATION_CREDENTIALS : 키 파일 경로 (대안)
"""
import json
import os
import time

import google.auth
from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account

SCOPE = ["https://www.googleapis.com/auth/cloud-platform"]
_session = None


class ApiError(RuntimeError):
    def __init__(self, status, body, url):
        self.status, self.body, self.url = status, body, url
        msg = body.get("error", {}).get("message", "") if isinstance(body, dict) else str(body)[:300]
        super().__init__(f"HTTP {status} {url.split('googleapis.com')[-1][:80]} :: {msg[:300]}")


def credentials():
    raw = os.environ.get("GCP_SA_KEY", "").strip()
    if raw:
        info = json.loads(raw)
        return service_account.Credentials.from_service_account_info(info, scopes=SCOPE), info
    path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    if path and os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            info = json.load(fh)
        return service_account.Credentials.from_service_account_file(path, scopes=SCOPE), info
    try:
        creds, _ = google.auth.default(scopes=SCOPE)
        return creds, {}
    except Exception as exc:
        raise RuntimeError(
            "구글 인증 정보가 없습니다. 서비스 계정 키 JSON 본문을 환경 시크릿 "
            "GCP_SA_KEY 로 등록하거나, 키 파일 경로를 "
            "GOOGLE_APPLICATION_CREDENTIALS 로 지정하세요. "
            "키를 채팅창에 붙여넣지 마세요."
        ) from exc


def session():
    global _session
    if _session is None:
        creds, _ = credentials()
        _session = AuthorizedSession(creds)
    return _session


def whoami():
    """인증 주체를 확인합니다. 키 본문은 노출하지 않고 이메일만 돌려줍니다."""
    _, info = credentials()
    email = info.get("client_email", "")
    if not email:
        creds, _ = credentials()
        email = getattr(creds, "service_account_email", "") or "(알 수 없음)"
    return email, info.get("project_id", "")


def api(method, url, body=None, params=None, timeout=120, ok=(200, 201, 204), retry=3):
    last = None
    for attempt in range(retry):
        resp = session().request(method, url, params=params,
                                 json=body if body is not None else None, timeout=timeout)
        try:
            parsed = resp.json() if resp.content else {}
        except ValueError:
            parsed = {"raw": resp.text[:500]}
        if resp.status_code in ok:
            return parsed
        last = ApiError(resp.status_code, parsed, url)
        # 429/5xx 와 IAM 전파 지연(400 service account does not exist)만 재시도합니다.
        transient = resp.status_code in (429, 500, 502, 503, 504)
        if not transient or attempt == retry - 1:
            raise last
        time.sleep(2 ** attempt * 2)
    raise last


def get_or_none(url, params=None):
    try:
        return api("GET", url, params=params)
    except ApiError as exc:
        if exc.status in (403, 404):
            return None
        raise


def wait_lro(op, poll_url=None, label="작업", timeout=900, interval=6):
    """표준 LRO 를 완료까지 기다립니다. op 는 operations 응답입니다."""
    if not isinstance(op, dict) or op.get("done"):
        return op
    name = op.get("name")
    if not name:
        return op
    url = poll_url or f"https://{_host_of(name)}/v1/{name}"
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(interval)
        cur = api("GET", url)
        if cur.get("done"):
            if cur.get("error"):
                raise RuntimeError(f"{label} 실패: {json.dumps(cur['error'], ensure_ascii=False)[:400]}")
            return cur.get("response", cur)
        print(f"    {label} 진행 중...", flush=True)
    raise TimeoutError(f"{label} 시간 초과 ({timeout}초)")


def _host_of(name):
    # operations 이름만으로는 호스트를 알 수 없어 호출부가 poll_url 을 주는 것이 원칙입니다.
    raise RuntimeError(f"poll_url 이 필요합니다: {name}")
