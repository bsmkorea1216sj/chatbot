"""AWS 키로 RDS PostgreSQL 생성(없을 때만) + dvdrental 복원 Colab 노트북 생성: python rds_setup_nb.py <출력.ipynb>"""
import json, sys

DVD_FILE_ID = '19-M54qUc9xZpw6lRPJ7iM_CAeoL-dbDq'   # 강의 자료 폴더 dvdrental/dvdrental.tar

SETUP = '''from google.colab import userdata
from getpass import getpass
from botocore.config import Config
import boto3, requests, time

def secret(*names, default=None):
    for n in names:
        try:
            v = userdata.get(n)
            if v and v.strip():
                return v.strip()
        except Exception:
            pass
    return default

# ── 설정값 (필요하면 여기만 바꾸기) ──
INSTANCE_ID = secret("DB_INSTANCE_ID", default="postgresql-lab-01")
REGION      = secret("AWS_REGION", "AWS_DEFAULT_REGION", default="ap-northeast-2")
DB_USER     = secret("DB_USER", "DB_USERNAME", default="postgres")
DB_CLASS    = "db.t4g.micro"      # 실습용 소형 (프리 티어 대상 여부는 계정마다 다름)
STORAGE_GB  = 20
NEW_PORT    = 5432                # 새로 만들 때 포트 (기존 실습 RDS는 5433)

aws = boto3.Session(aws_access_key_id=secret("AWS_ACCESS_KEY", "AWS_ACCESS_KEY_ID"),
                    aws_secret_access_key=secret("AWS_SECRET_KEY", "AWS_SECRET_ACCESS_KEY"),
                    region_name=REGION)
who = aws.client("sts").get_caller_identity()
print("✅ AWS 인증 완료 · 계정", who["Account"], "· 리전", REGION)
rds, ec2 = aws.client("rds"), aws.client("ec2")

def find_instance():
    try:
        return rds.describe_db_instances(DBInstanceIdentifier=INSTANCE_ID)["DBInstances"][0]
    except rds.exceptions.DBInstanceNotFoundFault:
        return None

db = find_instance()
print("기존 RDS:", f"{INSTANCE_ID} 있음 ({db['DBInstanceStatus']}) → 새로 만들지 않고 사용" if db else f"{INSTANCE_ID} 없음 → 다음 셀에서 생성")'''

CREATE = '''if db:
    print(f"건너뜀: {INSTANCE_ID}가 이미 있습니다. 기존 설정은 바꾸지 않습니다.")
else:
    password = secret("DB_PASSWORD") or getpass("새 DB 마스터 비밀번호 (8자 이상): ")
    assert len(password) >= 8, "비밀번호는 8자 이상이어야 합니다."

    # 1) 보안 그룹: 기본 VPC에 실습용 그룹을 만들고 지금 Colab의 공인 IP만 허용
    vpc = ec2.describe_vpcs(Filters=[{"Name": "isDefault", "Values": ["true"]}])["Vpcs"][0]["VpcId"]
    sgs = ec2.describe_security_groups(Filters=[{"Name": "group-name", "Values": ["cd10-colab-sg"]},
                                               {"Name": "vpc-id", "Values": [vpc]}])["SecurityGroups"]
    sg = sgs[0]["GroupId"] if sgs else ec2.create_security_group(
        GroupName="cd10-colab-sg", Description="CD10 Colab lab access", VpcId=vpc)["GroupId"]
    my_ip = requests.get("https://checkip.amazonaws.com", timeout=10).text.strip()
    try:
        ec2.authorize_security_group_ingress(GroupId=sg, IpPermissions=[{
            "IpProtocol": "tcp", "FromPort": NEW_PORT, "ToPort": NEW_PORT,
            "IpRanges": [{"CidrIp": f"{my_ip}/32", "Description": "Colab"}]}])
    except ec2.exceptions.ClientError as e:
        if "Duplicate" not in str(e):
            raise
    print(f"보안 그룹 {sg}: {my_ip}/32 → 포트 {NEW_PORT} 허용")

    # 2) RDS PostgreSQL 생성
    rds.create_db_instance(
        DBInstanceIdentifier=INSTANCE_ID, Engine="postgres", DBInstanceClass=DB_CLASS,
        AllocatedStorage=STORAGE_GB, StorageType="gp3", MasterUsername=DB_USER,
        MasterUserPassword=password, Port=NEW_PORT, VpcSecurityGroupIds=[sg],
        PubliclyAccessible=True, MultiAZ=False, BackupRetentionPeriod=1,
        StorageEncrypted=True, DeletionProtection=False, DBName="postgres")
    print("생성 요청 완료. 사용 가능해질 때까지 보통 5~15분 걸립니다...")
    t0 = time.time()
    while (db := find_instance())["DBInstanceStatus"] != "available":
        print(f"  {int(time.time() - t0)}초 · 상태: {db['DBInstanceStatus']}", flush=True)
        time.sleep(30)
    print("✅ 생성 완료")

ep = db["Endpoint"]
print("엔드포인트:", ep["Address"], "· 포트:", ep["Port"])'''

RESTORE = '''# dvdrental 데이터베이스 만들기 + 강의 자료 폴더의 dvdrental.tar 복원 (이미 있으면 건너뜀)
!apt-get -qq install -y postgresql-client > /dev/null
import os, io, subprocess, psycopg2
from pathlib import Path
from google.colab import auth
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

host, port = db["Endpoint"]["Address"], db["Endpoint"]["Port"]
password = secret("DB_PASSWORD") or (password if "password" in globals() else getpass("DB 비밀번호: "))
ca = Path("/content/rds-global-bundle.pem")
ca.write_bytes(requests.get("https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem", timeout=15).content)
cfg = dict(host=host, port=port, user=DB_USER, password=password, sslmode="verify-full",
           sslrootcert=str(ca), connect_timeout=10)

c = psycopg2.connect(**cfg, dbname="postgres"); c.autocommit = True
cur = c.cursor()
cur.execute("SELECT 1 FROM pg_database WHERE datname = 'dvdrental'")
exists = cur.fetchone() is not None
if not exists:
    cur.execute("CREATE DATABASE dvdrental")
c.close()

d = psycopg2.connect(**cfg, dbname="dvdrental"); cur = d.cursor()
cur.execute("SELECT to_regclass('public.payment')")
if cur.fetchone()[0]:
    print("건너뜀: dvdrental이 이미 복원되어 있습니다.")
else:
    auth.authenticate_user()                       # 강의자 구글 계정으로 드라이브 파일 받기
    req = build("drive", "v3").files().get_media(fileId="__DVD_FILE_ID__")
    buf = io.FileIO("/content/dvdrental.tar", "wb"); dl = MediaIoBaseDownload(buf, req)
    while not dl.next_chunk()[1]:
        pass
    buf.close()
    env = dict(os.environ, PGPASSWORD=password, PGSSLMODE="require")
    r = subprocess.run(["pg_restore", "-h", host, "-p", str(port), "-U", DB_USER, "-d", "dvdrental",
                        "--no-owner", "--no-privileges", "/content/dvdrental.tar"],
                       env=env, capture_output=True, text=True)
    print("pg_restore 완료" + (f" (경고 {r.stderr.count(chr(10))}줄)" if r.stderr else ""))

for t in ("film", "customer", "rental", "payment"):
    cur.execute(f"SELECT count(*) FROM {t}")
    print(f"  {t:9} {cur.fetchone()[0]:>6,}행")
d.close()
print("✅ dvdrental 준비 완료 → 10-1·10-2 실습에서 DB_NAME=dvdrental로 사용 가능")'''

DELETE = '''# ⚠️ 실습이 끝나 RDS를 지울 때만 실행 (요금 방지). 되돌릴 수 없습니다.
answer = input(f"{INSTANCE_ID}를 삭제하려면 인스턴스 이름을 그대로 입력: ")
if answer == INSTANCE_ID:
    rds.delete_db_instance(DBInstanceIdentifier=INSTANCE_ID, SkipFinalSnapshot=True,
                           DeleteAutomatedBackups=True)
    print("삭제 요청 완료 (몇 분 뒤 사라집니다)")
else:
    print("취소했습니다.")'''


def md(t):
    return {"cell_type": "markdown", "metadata": {}, "source": t}


def code(t):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": t}


cells = [
    md("# CD10 실습 DB 준비 · AWS 키로 RDS PostgreSQL 생성 + dvdrental 복원\n"
       "**보안 비밀**: `AWS_ACCESS_KEY`, `AWS_SECRET_KEY` (필수) · `DB_PASSWORD`, `DB_INSTANCE_ID`(기본 postgresql-lab-01) (선택)\n\n"
       "1. **설정·확인**: 같은 이름의 RDS가 **이미 있으면 새로 만들지 않고** 그대로 씁니다 (기존 설정 변경 없음).\n"
       "2. **생성**: 없을 때만 소형 인스턴스(db.t4g.micro, 20GB gp3)를 만들고, 보안 그룹은 **지금 Colab IP만** 허용합니다.\n"
       "3. **dvdrental 복원**: 강의 자료 폴더의 `dvdrental.tar`를 받아 복원합니다 (구글 계정 허용 창이 한 번 뜹니다).\n"
       "4. **삭제**: 실습이 끝나면 요금 방지를 위해 지웁니다.\n\n"
       "> 💰 RDS는 켜져 있는 동안 요금이 나옵니다. 프리 티어 적용 여부는 계정마다 다르니 AWS 콘솔에서 확인하세요.\n"
       "> 🔒 Colab IP는 실행할 때마다 바뀔 수 있습니다. 접속이 안 되면 2번 셀을 다시 실행해 현재 IP를 추가하세요."),
    code("!pip -q install boto3 psycopg2-binary requests google-api-python-client"),
    md("## 1 · AWS 인증과 기존 RDS 확인"), code(SETUP),
    md("## 2 · RDS 생성 (없을 때만) · 보안 그룹은 현재 Colab IP만 허용"), code(CREATE),
    md("## 3 · dvdrental DB 만들기 + 복원 (이미 있으면 건너뜀)"), code(RESTORE.replace("__DVD_FILE_ID__", DVD_FILE_ID)),
    md("## 4 · (실습 종료 후) RDS 삭제"), code(DELETE),
]
nb = {"cells": cells, "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3"}},
      "nbformat": 4, "nbformat_minor": 5}
out = sys.argv[1] if len(sys.argv) > 1 else "CD10_RDS_DB생성(26).ipynb"
json.dump(nb, open(out, "w"), ensure_ascii=False, indent=1)
print("saved", out)
