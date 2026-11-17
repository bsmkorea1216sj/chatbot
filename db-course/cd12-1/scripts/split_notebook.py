"""CD12-1 Colab을 '1 DB 생성 → 2 표 만들기 → 3 자동 검증 → 4 웹앱 실행 → 5 삭제' 셀로 나누고 교안 쪽과 1:1로 맞춘다.
- PostgreSQL(RDS)이 없는 초기 상태 기준, 접근은 Colab 보안 비밀만으로:
  AWS_ACCESS_KEY·AWS_SECRET_KEY(+AWS_SESSION_TOKEN)·DB_PASSWORD → 1번 셀이 AWS에 실습 RDS를 만들고(없을 때만) 보안 그룹(내 Colab IP)까지 준비,
  DB_PASSWORD(관리자 비밀번호)로 TLS(verify-full) 접속. 실습 후 5번 셀이 RDS를 삭제(DELETE 입력, 1번 셀 없이도 실행 가능)
  (강사 공용 RDS를 쓰면 보안 비밀 DB_HOST·DB_PORT·DB_NAME·DB_USER 등록 → 생성·삭제 건너뜀)
- 각 셀은 앞 셀을 안 돌렸으면 NameError 대신 '몇 번 셀부터 실행하세요' 안내로 멈춤
- 기존 실행 셀의 주문·취소·웹앱·자동 검증 코드는 그대로 잘라 옮김(CA 자동 다운로드, verify-full 유지)
python split_notebook.py <기존.ipynb(한 셀 버전)> <출력.ipynb>"""
import json, sys

src, out = sys.argv[1:3]
nb = json.load(open(src))
S = lambda c: ''.join(c['source']) if isinstance(c['source'], list) else c['source']
old = {c['metadata'].get('id'): c for c in nb['cells']}
RUN = S(old['shop-run'])


def cut(start, end=None, include_end=False):
    i = RUN.index(start)
    if end is None:
        return RUN[i:].rstrip() + '\n'
    j = RUN.index(end, i)
    if include_end:
        j = RUN.index('\n', j) + 1
    return RUN[i:j].rstrip() + '\n'


SCHEMA_FUNCS = cut('owned_schemas = globals().get', 'if "shop_schema" not in globals()')
SHOP_FUNCS = cut('class SoldOut(ValueError):', 'from urllib.request import urlopen, Request')
VERIFY = cut('from urllib.request import urlopen, Request', 'print("통과', include_end=True).replace(
    'print("통과 · 상품 조회 / 주문·배송 / 품절 / 단가 보존 / 삭제·재고 복구 / 중복 취소 차단")',
    'print("⑥ 통과 · 상품 조회 / 주문·배송 / 품절 / 단가 보존 / 삭제·재고 복구 / 중복 취소 차단 (검증용 스키마는 삭제됨)")')
PREVIEW = cut('from google.colab import output').replace(
    'output.serve_kernel_port_as_iframe(preview_server.server_port, height=660)',
    'print("⑦ 웹앱 열림 · 아래 화면에서 무선 마우스를 주문해 보세요")\noutput.serve_kernel_port_as_iframe(preview_server.server_port, height=660)')
for piece in (SCHEMA_FUNCS, SHOP_FUNCS, VERIFY, PREVIEW):
    assert 'setting(' not in piece

GUARD1 = '''if "transaction" not in globals():
    raise SystemExit("⚠️ 먼저 1. DB 생성 셀을 실행하세요. (런타임을 다시 시작했다면 1번 셀부터)")
'''
GUARD2 = GUARD1 + '''if "shop_schema" not in globals() or "make_app" not in globals():
    raise SystemExit("⚠️ 먼저 2. 표 만들기 셀을 실행하세요.")
'''

CELL1 = r'''# @title 1. DB 생성 · AWS에 실습 RDS PostgreSQL을 만들고(없을 때만) 연결 확인 (교안 13·31쪽)
import sys, subprocess, json, time
from pathlib import Path
from uuid import uuid4
from contextlib import contextmanager, closing

for module, package in (("psycopg2", "psycopg2-binary"), ("boto3", "boto3")):
    try:
        __import__(module)
    except ModuleNotFoundError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", package])
import psycopg2, boto3
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from botocore.exceptions import BotoCoreError, ClientError
from google.colab import userdata

_SECRET_TIMEOUT = getattr(userdata, "TimeoutException", ())

def setting(name, optional=False):
    try:
        value = userdata.get(name)
    except userdata.SecretNotFoundError:
        value = None
    except userdata.NotebookAccessError:
        raise ValueError(f"Colab 보안 비밀 {name}의 '노트북 액세스'를 켜세요 (왼쪽 열쇠 아이콘 → {name} 스위치). 켠 뒤 탭을 새로고침하고 1번 셀을 다시 실행합니다.") from None
    except _SECRET_TIMEOUT:
        raise TimeoutError("보안 비밀 접근 허용 창에 응답하지 않아 시간이 초과됐습니다. 탭을 새로고침하고 1번 셀을 다시 실행한 뒤 '허용'을 누르세요.") from None
    if not value or not value.strip():
        if optional:
            return None
        raise ValueError(f"Colab 보안 비밀에 {name}을(를) 등록하세요.")
    return value.strip()

# ① AWS 인증
session = boto3.Session(
    aws_access_key_id=setting("AWS_ACCESS_KEY"),
    aws_secret_access_key=setting("AWS_SECRET_KEY"),
    aws_session_token=setting("AWS_SESSION_TOKEN", optional=True),
    region_name=setting("AWS_REGION", optional=True) or "ap-northeast-2",
)
try:
    me = session.client("sts").get_caller_identity()
except ClientError as error:
    code = error.response.get("Error", {}).get("Code", "")
    hint = {
        "ExpiredToken": "임시 자격 증명이 만료됐습니다. AWS_ACCESS_KEY·AWS_SECRET_KEY·AWS_SESSION_TOKEN을 새 값으로 바꾸세요.",
        "InvalidClientTokenId": "AWS_ACCESS_KEY가 올바르지 않거나, 임시 키인데 AWS_SESSION_TOKEN이 빠졌습니다.",
        "SignatureDoesNotMatch": "AWS_SECRET_KEY가 AWS_ACCESS_KEY와 짝이 맞지 않습니다.",
    }.get(code, "보안 비밀, 리전, 임시 자격 증명의 세션 토큰과 만료 여부를 확인하세요.")
    raise RuntimeError(f"AWS 인증에 실패했습니다 ({code or '오류'}). {hint}") from None
except BotoCoreError:
    raise RuntimeError("AWS 인증 서버에 닿지 못했습니다. AWS_REGION 값과 Colab 인터넷 연결을 확인하세요.") from None
rds = session.client("rds")
print("① AWS 인증 확인 · 리전", session.region_name)

# ② RDS 준비 (없으면 새로 만든다)
LAB_INSTANCE = setting("DB_INSTANCE_ID", optional=True) or "cd12-shop-lab"
LAB_DB, LAB_ADMIN, LAB_SG = "shoplab", "shop_admin", "cd12-shop-lab-sg"
DB_PASSWORD = setting("DB_PASSWORD")                 # RDS 관리자 비밀번호 (8자 이상, 처음 만들 때 이 값으로 생성)
shared_host = setting("DB_HOST", optional=True)          # 강사 공용 RDS를 쓸 때만 등록

def find_instance():
    try:
        return rds.describe_db_instances(DBInstanceIdentifier=LAB_INSTANCE)["DBInstances"][0]
    except rds.exceptions.DBInstanceNotFoundFault:
        return None

def wait_available(label):
    t0 = time.time()
    while True:
        db = find_instance()
        if db and db["DBInstanceStatus"] == "available" and db.get("Endpoint"):
            return db
        sec = int(time.time() - t0)
        print(f"   {label} · {sec // 60}분 {sec % 60:02d}초 · 상태 {db['DBInstanceStatus'] if db else '없음'}", flush=True)
        time.sleep(30)

def lab_security_group(port):
    from urllib.request import urlopen
    ec2 = session.client("ec2")
    vpcs = ec2.describe_vpcs(Filters=[{"Name": "isDefault", "Values": ["true"]}])["Vpcs"]
    if not vpcs:
        raise RuntimeError("이 리전에 기본 VPC가 없습니다. VPC 콘솔에서 '기본 VPC 생성' 후 다시 실행하세요.")
    vpc = vpcs[0]["VpcId"]
    found = ec2.describe_security_groups(Filters=[{"Name": "group-name", "Values": [LAB_SG]},
                                                 {"Name": "vpc-id", "Values": [vpc]}])["SecurityGroups"]
    sg = found[0]["GroupId"] if found else ec2.create_security_group(
        GroupName=LAB_SG, Description="CD12 Colab shopping lab", VpcId=vpc)["GroupId"]
    with urlopen("https://checkip.amazonaws.com", timeout=10) as response:
        ip = response.read().decode().strip()
    try:
        ec2.authorize_security_group_ingress(GroupId=sg, IpPermissions=[{
            "IpProtocol": "tcp", "FromPort": port, "ToPort": port,
            "IpRanges": [{"CidrIp": f"{ip}/32", "Description": "CD12 Colab runtime"}]}])
    except ClientError as error:
        if error.response.get("Error", {}).get("Code") != "InvalidPermission.Duplicate":
            raise
    return sg, ip

def ensure_lab_rds():
    db = find_instance()
    if db is None:
        print(f"   RDS {LAB_INSTANCE} 없음 → AWS에 새로 만듭니다 (보통 5~15분)")
        if len(DB_PASSWORD) < 8:
            raise ValueError("보안 비밀 DB_PASSWORD는 8자 이상이어야 합니다.")
        sg, ip = lab_security_group(5432)
        rds.create_db_instance(
            DBInstanceIdentifier=LAB_INSTANCE, Engine="postgres", DBInstanceClass="db.t4g.micro",
            AllocatedStorage=20, StorageType="gp3", MasterUsername=LAB_ADMIN, MasterUserPassword=DB_PASSWORD,
            DBName=LAB_DB, Port=5432, VpcSecurityGroupIds=[sg], PubliclyAccessible=True, MultiAZ=False,
            BackupRetentionPeriod=0, StorageEncrypted=True, DeletionProtection=False,
            Tags=[{"Key": "course", "Value": "cd12-shop-lab"}])
        return wait_available("생성 중"), "새로 생성", ip
    if db["DBInstanceStatus"] == "stopped":
        rds.start_db_instance(DBInstanceIdentifier=LAB_INSTANCE)
    if db["DBInstanceStatus"] != "available":
        db = wait_available("시작 중")
    sg, ip = lab_security_group(db["Endpoint"]["Port"])
    attached = [g["VpcSecurityGroupId"] for g in db["VpcSecurityGroups"]]
    if sg not in attached:
        rds.modify_db_instance(DBInstanceIdentifier=LAB_INSTANCE, VpcSecurityGroupIds=attached + [sg], ApplyImmediately=True)
        time.sleep(20)
        db = wait_available("보안 그룹 연결 중")
    return db, "기존 인스턴스 사용", ip

if shared_host:
    lab_db = None
    print("② RDS 준비 · 보안 비밀 DB_HOST의 공용 RDS 사용")
else:
    lab_db, how, ip = ensure_lab_rds()
    print(f"② RDS 준비 · {LAB_INSTANCE} ({how}) · 내 Colab IP {ip} 허용")

# ③ AWS 공식 RDS 인증서
def download_rds_ca():
    import ssl
    from urllib.request import urlopen
    from urllib.error import URLError
    ca = Path("/content/cd12-rds-global-bundle.pem")
    temp = ca.with_suffix(".tmp")
    try:
        with urlopen("https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem", timeout=20) as response:
            data = response.read(2_000_001)
        if len(data) > 2_000_000:
            raise ValueError("CA bundle too large")
        temp.write_bytes(data)
        ssl.create_default_context(cafile=str(temp))
        temp.replace(ca)
    except (URLError, OSError, ValueError):
        raise RuntimeError("AWS 공식 RDS 인증서를 받지 못했습니다. Colab 인터넷 연결을 확인하고 1번 셀을 다시 실행하세요.") from None
    finally:
        temp.unlink(missing_ok=True)
    return ca

ca = download_rds_ca()
print("③ RDS 인증서 준비 · AWS 공식 CA 번들")

# ④ 보안 비밀 DB_PASSWORD로 TLS 접속 (verify-full)
if lab_db:
    endpoint = lab_db["Endpoint"]
    db_config = dict(host=endpoint["Address"], port=int(endpoint["Port"]), dbname=LAB_DB, user=lab_db["MasterUsername"],
                     sslmode="verify-full", sslrootcert=str(ca), connect_timeout=8, application_name="cd12_shopping_lab")
else:
    db_config = dict(host=shared_host, port=int(setting("DB_PORT")), dbname=setting("DB_NAME"), user=setting("DB_USER"),
                     sslmode="verify-full", sslrootcert=str(ca), connect_timeout=8, application_name="cd12_shopping_lab")

def rds_hint(message):
    m = message.lower()
    if "could not translate host name" in m or "name or service not known" in m:
        return "DB 주소를 찾지 못했습니다. RDS 엔드포인트를 확인하세요."
    if any(k in m for k in ("timeout", "timed out", "could not connect", "connection refused", "no route")):
        return "네트워크 시간 초과: 런타임이 바뀌어 Colab IP가 달라졌을 수 있습니다. 1번 셀을 다시 실행하세요(보안 그룹 자동 갱신)."
    if "password authentication failed" in m:
        return "비밀번호 불일치: 보안 비밀 DB_PASSWORD가 RDS를 처음 만들 때의 값과 다릅니다. 원래 값으로 바꾸거나 5번 셀로 RDS를 지운 뒤 다시 만드세요."
    if "certificate" in m or "ssl" in m:
        return "TLS 확인 실패: 별칭이 아닌 RDS 엔드포인트를 쓰고, 1번 셀을 다시 실행해 인증서를 다시 받으세요."
    if "does not exist" in m:
        return "DB 이름 또는 사용자가 RDS에 없습니다."
    return "엔드포인트, 네트워크, DB_PASSWORD를 확인하세요."

def connect_db():
    try:
        return psycopg2.connect(**db_config, password=DB_PASSWORD)
    except psycopg2.OperationalError as error:
        raise RuntimeError("RDS 연결에 실패했습니다 · " + rds_hint(str(error))) from None

@contextmanager
def transaction(schema=None):
    with closing(connect_db()) as conn, conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if schema is not None:
                cur.execute(sql.SQL("SET LOCAL search_path TO {}, pg_catalog").format(sql.Identifier(schema)))
            yield cur

with transaction() as cur:
    cur.execute("SELECT current_database() AS db, ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid()")
    connected = cur.fetchone()
    assert connected["ssl"], "TLS 연결이어야 합니다."
print("④ 연결 확인:", connected["db"], "· AWS RDS에 TLS로 접속 (인증서·호스트 확인 완료)")
print("→ 다음: 2. 표 만들기")
'''

CELL2 = '# @title 2. 표 만들기 · 고객·상품·주문·주문항목·배송 5개 표와 관계 (교안 23~25쪽)\n' + GUARD1 + SCHEMA_FUNCS + '''
if "shop_schema" not in globals() or shop_schema not in owned_schemas:
    shop_schema = new_lab_schema()
with transaction(shop_schema) as cur:
    cur.execute("SELECT id, name, price, stock FROM products ORDER BY id")
    products_now = cur.fetchall()
    cur.execute("""
        SELECT con.conrelid::regclass::text AS child, a.attname AS fk, con.confrelid::regclass::text AS parent
        FROM pg_constraint con JOIN pg_attribute a ON a.attrelid = con.conrelid AND a.attnum = ANY(con.conkey)
        WHERE con.contype = 'f' AND con.connamespace = %s::regnamespace ORDER BY 1, 2""", (shop_schema,))
    relations = cur.fetchall()
print("⑤ 실습 스키마 준비:", shop_schema)
print("   상품:", ", ".join(f"{r['name']} {r['price']:,}원 · 재고 {r['stock']}" for r in products_now))
for r in relations:
    print(f"   관계(FK): {r['child'].split('.')[-1]}.{r['fk']} → {r['parent'].split('.')[-1]}")

# 주문·취소·조회와 웹앱 기능 정의 (3·4번 셀에서 사용)
''' + SHOP_FUNCS + 'print("→ 다음: 3. 자동 검증")\n'

CELL3 = '# @title 3. 자동 검증 · 마지막 마우스 1개 주문 → 품절 → 취소·재고 복구 (교안 18·28~30쪽)\n' + GUARD2 + VERIFY + 'print("→ 다음: 4. 웹앱 실행")\n'
CELL4 = '# @title 4. 웹앱 실행 · 직접 주문·취소하고 제출 화면 캡처 (교안 21·26·31·33쪽)\n' + GUARD2 + PREVIEW
CELL5 = r'''# @title 5. 삭제 · 실습이 끝나면 AWS의 실습 RDS를 삭제 (교안 34쪽)
# 런타임을 다시 시작했어도 이 셀만 실행하면 됩니다 (Colab 보안 비밀의 AWS 키 사용).
import boto3
from google.colab import userdata

def _secret(name, default=None):
    try:
        value = userdata.get(name)
    except Exception:
        value = None
    return value.strip() if value and value.strip() else default

stop = globals().get("stop_preview")
if stop is not None:
    stop()                                                # 웹앱 미리보기 종료

if _secret("DB_HOST"):
    print("공용 RDS(DB_HOST)를 쓰는 중이라 삭제하지 않습니다. 실습 스키마는 강사가 정리합니다.")
else:
    instance = _secret("DB_INSTANCE_ID", "cd12-shop-lab")
    rds = boto3.Session(aws_access_key_id=_secret("AWS_ACCESS_KEY"), aws_secret_access_key=_secret("AWS_SECRET_KEY"),
                        aws_session_token=_secret("AWS_SESSION_TOKEN"),
                        region_name=_secret("AWS_REGION", "ap-northeast-2")).client("rds")
    try:
        status = rds.describe_db_instances(DBInstanceIdentifier=instance)["DBInstances"][0]["DBInstanceStatus"]
    except rds.exceptions.DBInstanceNotFoundFault:
        status = None
    if status is None:
        print(f"RDS {instance}가 없습니다. 이미 삭제됐습니다.")
    elif status == "deleting":
        print(f"RDS {instance} 삭제가 진행 중입니다.")
    elif input(f"실습을 마치고 AWS의 RDS {instance}를 삭제하려면 DELETE 입력: ").strip() == "DELETE":
        rds.delete_db_instance(DBInstanceIdentifier=instance, SkipFinalSnapshot=True, DeleteAutomatedBackups=True)
        print(f"RDS {instance} 삭제 요청 완료 · 5~10분 뒤 사라집니다 (요금 중지). 다음 실습 때 1번 셀이 새로 만듭니다.")
    else:
        print("취소했습니다. RDS가 켜져 있는 동안 요금이 나오므로 실습이 끝나면 꼭 삭제하세요.")
'''



def md(cid, text):
    return {'cell_type': 'markdown', 'metadata': {'id': cid}, 'source': text}


def code(cid, text):
    return {'cell_type': 'code', 'metadata': {'id': cid}, 'execution_count': None, 'outputs': [], 'source': text}


INTRO = '''# CD12-1 · 미니 쇼핑몰 DB 실습 (AWS RDS)

PostgreSQL이 **없는 상태에서 시작**합니다. 1번 셀이 **AWS에 실습용 RDS**를 만들고, 실습이 끝나면 5번 셀이 **삭제**합니다. 교안 각 페이지의 **Colab 버튼**이 아래 셀로 바로 이동합니다.

| 셀 | 하는 일 | 교안 |
|---|---|---|
| 1. DB 생성 | AWS 인증 → 실습 RDS 생성(없을 때만, 5~15분) → TLS 연결 확인 | 13·31쪽 |
| 2. 표 만들기 | 표 5개와 관계(FK) 생성 | 23~25쪽 |
| 3. 자동 검증 | 마지막 마우스 1개 주문 → 품절 → 취소·재고 복구 | 18·28~30쪽 |
| 4. 웹앱 실행 | 화면에서 직접 주문·취소, 제출 캡처 | 21·26·31·33쪽 |
| 5. 삭제 | AWS의 실습 RDS 삭제 (요금 중지) | 34쪽 |

**준비물 · Colab 보안 비밀** (왼쪽 열쇠 아이콘 → 새 보안 비밀 추가 → 각 항목 **노트북 액세스** 켜기)

| 이름 | 값 |
|---|---|
| `AWS_ACCESS_KEY` | AWS 액세스 키 ID |
| `AWS_SECRET_KEY` | AWS 비밀 액세스 키 |
| `DB_PASSWORD` | 새 RDS 관리자 비밀번호로 쓸 값 (8자 이상, 직접 정함) |
| `AWS_SESSION_TOKEN` | 임시 자격 증명일 때만 |
| `AWS_REGION` | 선택 (기본 ap-northeast-2) |'''



GUIDE1 = '''## 1. DB 생성 (교안 13·31쪽)

- 처음 실행하면 AWS에 실습 RDS PostgreSQL `cd12-shop-lab`(db.t4g.micro, 공개 접근, 암호화)을 만듭니다. 관리자 비밀번호는 보안 비밀 `DB_PASSWORD` 값입니다. **5~15분** 걸리며 진행 상태가 30초마다 표시됩니다.
- 자동으로: 실습 보안 그룹(**지금 Colab IP만 허용**, 다시 실행할 때 갱신) · AWS 공식 RDS 인증서(TLS `verify-full`).
- 이미 있으면 새로 만들지 않고 그대로 씁니다(중지 상태면 시작).
- AWS 키에 필요한 권한: RDS 생성·조회·수정·시작·삭제, EC2 기본 VPC·보안 그룹 조회/생성/인바운드 추가.

| 출력 | 뜻 |
|---|---|
| ① AWS 인증 확인 | 보안 비밀의 AWS 키로 인증 성공 |
| ② RDS 준비 | 실습 RDS 확인 · 없으면 생성 · 내 Colab IP 허용 |
| ③ RDS 인증서 준비 | AWS 공식 CA 번들 내려받기 |
| ④ **연결 확인** | `DB_PASSWORD`로 **AWS RDS에 TLS 접속 성공** |

| 문제 | 해결 |
|---|---|
| 보안 비밀 · '노트북 액세스' / 시간 초과 | 열쇠 아이콘에서 노트북 액세스 켜기 → 탭 새로고침 → 1번 셀 다시 실행 |
| ExpiredToken / InvalidClientTokenId | 임시 키 만료 또는 `AWS_SESSION_TOKEN` 누락 → 새 값 등록 |
| 네트워크 시간 초과 | 런타임이 바뀌어 IP가 달라짐 → 1번 셀 다시 실행 |
| 비밀번호 불일치 | `DB_PASSWORD`를 RDS를 만들 때의 값으로 되돌리거나, 5번 셀로 삭제 후 다시 생성 |'''



GUIDE2 = '''## 2. 표 만들기 (교안 23~25쪽)

내 런타임 전용 스키마에 customers · products · orders · order_items · shipments 5개 표를 만들고, ⑤ 출력에서 상품과 **관계(FK)**를 확인합니다. 교안 24쪽 ERD와 같은지 비교하세요.'''
GUIDE3 = '''## 3. 자동 검증 (교안 18·28~30쪽)

별도 검증용 스키마에서 마지막 마우스 1개 주문 → 재주문 품절(409) → 단가 보존 → 취소·재고 복구 → 중복 취소 차단을 확인합니다. **⑥ 통과**가 나오면 성공이고, 검증용 스키마는 자동으로 지워집니다.'''
GUIDE4 = '''## 4. 웹앱 실행 (교안 21·26·31·33쪽)

아래 웹앱에서 무선 마우스 주문 → 주문·배송 조회(배송 준비 중) → 재주문 시 품절 → 주문 취소 및 삭제 → 재고 1개 복구를 직접 확인합니다.'''
SUBMIT = '''## 제출 (교안 33쪽)

웹앱의 주문·품절·취소 화면과 ④ 연결 확인 · ⑥ 통과 출력을 캡처해 제출합니다. 출력에는 키·비밀번호가 표시되지 않습니다. 제출 후 **5번 셀로 RDS를 삭제**하세요.'''
GUIDE5 = '''## 5. 삭제 (교안 34쪽)

제출이 끝나면 실행합니다. `DELETE`를 입력하면 웹앱을 끄고 **AWS의 실습 RDS를 삭제**합니다(요금 중지, 5~10분 소요). 런타임을 다시 시작했어도 이 셀만 실행하면 됩니다. 다음 실습 때는 1번 셀이 새로 만듭니다.'''



nb['cells'] = [md('shop-intro', INTRO),
               md('shop-db-create', GUIDE1), code('shop-db-create-run', CELL1),
               md('shop-tables', GUIDE2), code('shop-tables-run', CELL2),
               md('shop-verify', GUIDE3), code('shop-verify-run', CELL3),
               md('shop-webapp', GUIDE4), code('shop-webapp-run', CELL4),
               md('shop-submit', SUBMIT),
               md('shop-delete', GUIDE5), code('shop-delete-run', CELL5)]
json.dump(nb, open(out, 'w'), ensure_ascii=False, indent=1)
print('ok ·', [c['metadata']['id'] for c in nb['cells']])
