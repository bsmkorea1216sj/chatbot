"""Google Cloud REST 호출 공통층. gcloud CLI 없이 동작합니다.

인증은 아래 순서로 찾습니다. 어느 경우에도 값을 출력하지 않습니다.
  1. GCP_ACCESS_TOKEN  : 단기 액세스 토큰 (권장). 키 파일을 만들지 않습니다.
                         유효기간 약 1시간. Cloud Shell 에서
                         `gcloud auth print-access-token` 으로 발급합니다.
  2. GCP_SA_KEY        : 서비스 계정 키 JSON 본문 (키를 내려받는 방식)
  3. GOOGLE_APPLICATION_CREDENTIALS : 키 파일 경로
  4. 애플리케이션 기본 자격증명
"""
import json
import os
import time

import google.auth
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials as TokenCredentials

SCOPE = ["https://www.googleapis.com/auth/cloud-platform"]
_session = None


TOKEN_EXPIRED = RuntimeError(
    "액세스 토큰이 만료되었거나 범위가 부족합니다(유효기간 약 1시간). Cloud Shell 에서 "
    "`gcloud auth print-access-token` 을 다시 실행해 환경 시크릿 GCP_ACCESS_TOKEN 을 "
    "갱신한 뒤, 멈춘 단계부터 다시 실행하세요.")


class ApiError(RuntimeError):
    def __init__(self, status, body, url):
        self.status, self.body, self.url = status, body, url
        msg = body.get("error", {}).get("message", "") if isinstance(body, dict) else str(body)[:300]
        super().__init__(f"HTTP {status} {url.split('googleapis.com')[-1][:80]} :: {msg[:300]}")


def credentials():
    token = os.environ.get("GCP_ACCESS_TOKEN", "").strip()
    if token:
        # 키 파일을 만들지 않는 경로입니다. 토큰만으로는 주체를 알 수 없어
        # 1단계에서 tokeninfo 로 확인합니다.
        return TokenCredentials(token=token), {"auth": "access_token"}
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
            "구글 인증 정보가 없습니다. 키 파일을 만들지 않는 방법으로는 "
            "Cloud Shell 에서 `gcloud auth print-access-token` 으로 받은 값을 "
            "환경 시크릿 GCP_ACCESS_TOKEN 으로 등록하세요(유효기간 약 1시간). "
            "서비스 계정 키를 쓰려면 JSON 본문을 GCP_SA_KEY 로 등록하세요. "
            "어느 경우든 채팅창에 붙여넣지 마세요."
        ) from exc


def session():
    global _session
    if _session is None:
        creds, info = credentials()
        _session = AuthorizedSession(creds)
        if info.get("auth") == "access_token":
            # 사용자 계정 토큰은 할당량 프로젝트가 없으면 일부 API 가 거부합니다.
            quota = os.environ.get("GCP_QUOTA_PROJECT") or os.environ.get("GCP_PROJECT", "")
            if quota:
                _session.headers["x-goog-user-project"] = quota
    return _session


def whoami():
    """인증 주체를 확인합니다. 키나 토큰 값은 노출하지 않고 이메일만 돌려줍니다."""
    creds, info = credentials()
    if info.get("auth") == "access_token":
        # tokeninfo 는 토큰 자체를 질의 문자열로 보내므로 직접 호출하지 않고,
        # 권한이 필요 없는 userinfo 로 주체만 확인합니다.
        # 주체 표시는 참고용입니다. 토큰에 userinfo 범위가 없으면 조회만 실패하고
        # 실제 권한 확인은 1단계의 프로젝트 조회가 담당합니다.
        try:
            me = api("GET", "https://www.googleapis.com/oauth2/v3/userinfo", retry=1)
            return me.get("email") or "(토큰 주체 미표시)", ""
        except Exception:
            return "(토큰 주체 미표시 — 권한은 프로젝트 조회로 확인합니다)", ""
    email = info.get("client_email", "")
    if not email:
        email = getattr(creds, "service_account_email", "") or "(알 수 없음)"
    return email, info.get("project_id", "")


def api(method, url, body=None, params=None, timeout=120, ok=(200, 201, 204), retry=3):
    last = None
    for attempt in range(retry):
        try:
            resp = session().request(method, url, params=params,
                                     json=body if body is not None else None, timeout=timeout)
        except RefreshError:
            # 단기 토큰은 갱신할 수 없습니다. 만료되면 여기로 떨어집니다.
            raise TOKEN_EXPIRED from None
        try:
            parsed = resp.json() if resp.content else {}
        except ValueError:
            parsed = {"raw": resp.text[:500]}
        if resp.status_code in ok:
            return parsed
        if resp.status_code == 401 and os.environ.get("GCP_ACCESS_TOKEN"):
            raise TOKEN_EXPIRED
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
