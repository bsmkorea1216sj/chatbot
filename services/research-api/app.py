"""Cloud Run API/worker. No credentials are embedded; fail closed if unconfigured."""
import hashlib, json, os
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Literal
import firebase_admin
from firebase_admin import auth
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from google.cloud import firestore, tasks_v2
from google.oauth2 import id_token
from google.auth.transport.requests import Request
from pydantic import BaseModel, Field
from billing import Balance, reserve, settle, token_cost

app = FastAPI()
ALLOWED = {'논문', '공식자료', '블로그'}

@lru_cache
def db():
    return firestore.Client(project=os.environ['GOOGLE_CLOUD_PROJECT'])

@lru_cache
def firebase_app():
    return firebase_admin.initialize_app(options={
        'projectId': os.environ['GOOGLE_CLOUD_PROJECT']})

def user(authorization: str = Header(default='')):
    if not authorization.startswith('Bearer '):
        raise HTTPException(401, 'GOOGLE_LOGIN_REQUIRED')
    try:
        claims = auth.verify_id_token(authorization[7:], app=firebase_app(),
                                     check_revoked=True)
        if not claims.get('email_verified') or claims.get('firebase', {}).get(
                'sign_in_provider') != 'google.com':
            raise ValueError('Google sign-in required')
        return claims['uid']
    except Exception:
        raise HTTPException(401, 'INVALID_LOGIN') from None

class ResearchRequest(BaseModel):
    request_id: str = Field(pattern=r'^[a-zA-Z0-9_-]{16,80}$')
    topic: str = Field(min_length=2, max_length=600)
    categories: list[str] = Field(min_length=1, max_length=3)
    mode: Literal['basic', 'deep'] = 'basic'

def positive_env(name):
    n = int(os.environ[name])
    if n <= 0: raise ValueError(f'Invalid {name}')
    return n

def quote(mode):
    # Only Gemini 2.5 Flash is allowed here: search is billed per grounded prompt.
    # Reserve the full model input window including grounding/tool tokens.
    if os.getenv('GEMINI_MODEL', 'gemini-2.5-flash') != 'gemini-2.5-flash':
        raise ValueError('Unreviewed model pricing')
    output = 2048 if mode == 'basic' else 4096
    rates = {k: os.environ[k] for k in ('INPUT_USD_PER_MILLION',
             'OUTPUT_USD_PER_MILLION', 'KRW_PER_USD')}
    cap = token_cost(1_048_576, output, rates['INPUT_USD_PER_MILLION'],
                     rates['OUTPUT_USD_PER_MILLION'], rates['KRW_PER_USD'])
    grounding = positive_env('GROUNDING_MAX_MICRO_KRW')
    return {'cap': cap + grounding, 'grounding': grounding,
            'rates': rates, 'output': output, 'model': 'gemini-2.5-flash',
            'price_version': os.environ['PRICE_VERSION']}

def balance(data):
    return Balance(data.get('granted', 0), data.get('spent', 0),
                   data.get('reserved', 0))

def balance_fields(b):
    return {'granted': b.granted, 'spent': b.spent, 'reserved': b.reserved}

@app.get('/')
def home(): return FileResponse(Path(__file__).with_name('index.html'))

@app.get('/health')
def health(): return {'status': 'ok'}

@app.get('/api/config')
def config():
    return {'firebase': json.loads(os.getenv('FIREBASE_WEB_CONFIG', '{}')),
            'purchase_url': os.getenv('PURCHASE_URL', ''),
            'payments_connected': False}

@app.get('/api/account')
def account(uid=Depends(user)):
    data = db().collection('accounts').document(uid).get().to_dict() or {}
    # No raw expense or 50% budget fields returned to the browser.
    return {'free_remaining': max(0, 3-data.get('free_used', 0)
                                   -data.get('free_pending', 0)),
            'paid': data.get('expires_at', 0) > datetime.now().timestamp(),
            'credits_remaining': max(0, data.get('credits', 0)
                                       -data.get('credits_reserved', 0))}

def enqueue(job_id):
    project = os.environ['GOOGLE_CLOUD_PROJECT']
    region = os.environ['TASKS_REGION']
    service_url = os.environ['SERVICE_URL'].rstrip('/')
    client = tasks_v2.CloudTasksClient()
    parent = client.queue_path(project, region, os.environ['TASKS_QUEUE'])
    task = tasks_v2.Task(name=client.task_path(project, region,
                        os.environ['TASKS_QUEUE'], job_id),
        http_request=tasks_v2.HttpRequest(http_method=tasks_v2.HttpMethod.POST,
          url=service_url+'/internal/work', headers={'Content-Type':'application/json'},
          body=json.dumps({'job_id':job_id}).encode(),
          oidc_token=tasks_v2.OidcToken(service_account_email=os.environ['TASKS_SA'],
                                      audience=service_url)))
    from google.api_core.exceptions import AlreadyExists
    try: client.create_task(parent=parent, task=task)
    except AlreadyExists: pass

@app.post('/api/research', status_code=202)
def research(body: ResearchRequest, uid=Depends(user)):
    if not set(body.categories) <= ALLOWED or len(set(body.categories)) != len(body.categories):
        raise HTTPException(422, 'INVALID_SOURCE_TYPES')
    try: pricing = quote(body.mode)
    except (KeyError, ValueError):
        raise HTTPException(503, '가격 설정 검증이 필요합니다.') from None
    payload = body.model_dump(exclude={'request_id'})
    fingerprint = hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    key = hashlib.sha256((uid+'|'+body.request_id).encode()).hexdigest()
    jref = db().collection('jobs').document(key)
    aref = db().collection('accounts').document(uid)
    pref = db().collection('budgets').document('trial_pool')
    @firestore.transactional
    def book(tx):
        prior = jref.get(transaction=tx)
        a = aref.get(transaction=tx).to_dict() or {}
        p = pref.get(transaction=tx).to_dict() or {}
        if prior.exists:
            if prior.to_dict()['fingerprint'] != fingerprint:
                raise HTTPException(409, 'REQUEST_ID_REUSED')
            return
        if a.get('active_job'):
            raise HTTPException(409, '진행 중인 리서치가 있습니다.')
        if a.get('cost_review_required') or p.get('cost_review_required'):
            raise HTTPException(503, '비용 설정 확인이 필요합니다.')
        free = body.mode == 'basic' and a.get('free_used',0)+a.get('free_pending',0)<3
        credits = 1 if body.mode == 'basic' else 5
        if not free:
            if a.get('expires_at',0) <= datetime.now().timestamp():
                raise HTTPException(402, 'PAID_ACCESS_REQUIRED')
            if a.get('credits',0)-a.get('credits_reserved',0)<credits:
                raise HTTPException(402, 'TOP_UP_REQUIRED')
        try: reserved = reserve(balance(p if free else a), pricing['cap'])
        except PermissionError:
            raise HTTPException(402 if not free else 503,
                                'TOP_UP_REQUIRED' if not free else '무료 체험이 일시 중단되었습니다.')
        if free:
            tx.set(pref,balance_fields(reserved),merge=True)
            a['free_pending'] = a.get('free_pending',0)+1
        else:
            a.update(balance_fields(reserved))
            a['credits_reserved'] = a.get('credits_reserved',0)+credits
        a['active_job'] = key
        tx.set(aref,a,merge=True)
        tx.create(jref, {'uid':uid, 'fingerprint':fingerprint, 'request':payload,
                        'pricing':pricing,'free':free,'credits':credits,
                        'status':'QUEUED','created_at':firestore.SERVER_TIMESTAMP})
    book(db().transaction())
    try: enqueue(key)
    except Exception:
        # Ambiguous enqueue failures retain reservation. Same request ID retries safely.
        raise HTTPException(503, '접수 상태 확인이 필요합니다. 같은 요청으로 다시 시도하세요.') from None
    return {'job_id':key}

@app.get('/api/research/{key}')
def result(key: str, uid=Depends(user)):
    if len(key)!=64: raise HTTPException(404)
    data = db().collection('jobs').document(key).get().to_dict()
    if not data or data['uid']!=uid: raise HTTPException(404)
    return {k:data.get(k) for k in ('status','report','sources','search_html','message')}

class WorkRequest(BaseModel):
    job_id: str = Field(pattern=r'^[a-f0-9]{64}$')

@app.post('/internal/work')
def work(body: WorkRequest, authorization: str = Header(default='')):
    try:
        if not authorization.startswith('Bearer '): raise ValueError()
        claims = id_token.verify_oauth2_token(authorization[7:], Request(),
                                             os.environ['SERVICE_URL'].rstrip('/'))
        if claims.get('email') != os.environ['TASKS_SA'] or not claims.get('email_verified'):
            raise ValueError()
    except Exception: raise HTTPException(401) from None
    jref = db().collection('jobs').document(body.job_id)
    @firestore.transactional
    def claim(tx):
        data = jref.get(transaction=tx).to_dict()
        if not data or data['status']!='QUEUED': return None
        tx.update(jref, {'status':'RUNNING','started_at':firestore.SERVER_TIMESTAMP})
        return data
    job = claim(db().transaction())
    if job is None: return {'status':'already_claimed'}
    from research import generate, AccountedFailure
    # A timeout may still incur provider cost. No automatic repeat model call.
    actual = job['pricing']['cap']
    status, output = 'REVIEW_REQUIRED', {'message':'작업 확인이 필요합니다.'}
    try:
        actual, output = generate(job)
        status = 'SUCCESS'
    except AccountedFailure as failure:
        actual = failure.cost
    except Exception:
        pass  # Sensitive provider errors must not enter customer responses/logs.
    aref = db().collection('accounts').document(job['uid'])
    pref = db().collection('budgets').document('trial_pool')
    @firestore.transactional
    def finish(tx):
        latest = jref.get(transaction=tx).to_dict()
        a = aref.get(transaction=tx).to_dict() or {}
        p = pref.get(transaction=tx).to_dict() or {}
        if latest['status']!='RUNNING': return
        target = p if job['free'] else a
        target.update(balance_fields(settle(balance(target),job['pricing']['cap'],actual)))
        if actual > job['pricing']['cap']:
            target['cost_review_required'] = True
        if job['free']:
            a['free_pending'] = max(0,a.get('free_pending',0)-1)
            a['free_used'] = a.get('free_used',0)+(status=='SUCCESS')
            tx.set(pref,target,merge=True)
        else:
            a['credits_reserved'] = max(0,a.get('credits_reserved',0)-job['credits'])
            if status=='SUCCESS': a['credits']=a.get('credits',0)-job['credits']
        a['active_job']=None
        tx.set(aref,a,merge=True)
        tx.update(jref,dict(status=status,actual_cost=actual,**output,
                           finished_at=firestore.SERVER_TIMESTAMP))
    finish(db().transaction())
    return {'status':status}
