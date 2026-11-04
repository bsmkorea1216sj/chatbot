"""CD10-1 Colab 실습 노트북 생성: python colab_nb.py <출력경로.ipynb>
접속 방식은 CD9-3 노트북과 동일 (AWS_ACCESS_KEY/AWS_SECRET_KEY 보안비밀 + DB 비밀번호 getpass + RDS SSL)."""
import json, sys


def md(t):
    return {"cell_type": "markdown", "metadata": {}, "source": t}


def code(t):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": t}


SETUP = '''from google.colab import userdata
from getpass import getpass
from pathlib import Path
from botocore.config import Config
import boto3, psycopg2, requests
import pandas as pd
from IPython.display import display

def secret(*names, default=None):
    for n in names:
        try:
            v = userdata.get(n)
            if v and v.strip():
                return v.strip()
        except Exception:
            pass
    return default

key = secret("AWS_ACCESS_KEY", "AWS_ACCESS_KEY_ID")
skey = secret("AWS_SECRET_KEY", "AWS_SECRET_ACCESS_KEY")
if not key or not skey:
    raise ValueError("AWS_ACCESS_KEY와 AWS_SECRET_KEY 보안비밀 접근을 허용하세요.")
api = Config(connect_timeout=5, read_timeout=10, retries={"total_max_attempts": 1})
aws = boto3.Session(aws_access_key_id=key, aws_secret_access_key=skey,
                    region_name=secret("AWS_REGION", "AWS_DEFAULT_REGION", default="ap-northeast-2"))
aws.client("sts", config=api).get_caller_identity()
print("✅ AWS 인증 완료", flush=True)

# 엔드포인트·포트: 보안비밀 → RDS 조회 → 기존 실습(CD9-3) 값 순서로 사용
INSTANCE_ID = secret("DB_INSTANCE_ID", default="postgresql-lab-01")
host, port = secret("DB_HOST"), secret("DB_PORT")
if not host or not port:
    try:
        ep = aws.client("rds", config=api).describe_db_instances(
            DBInstanceIdentifier=INSTANCE_ID)["DBInstances"][0]["Endpoint"]
        host, port = host or ep["Address"], port or ep["Port"]
    except Exception as e:
        print("RDS 조회 실패, 기존 실습 값 사용:", type(e).__name__)
host = host or "postgresql-lab-01.cf4icu2qu8n0.ap-northeast-2.rds.amazonaws.com"
port = int(port or 5433)
user = secret("DB_USER", "DB_USERNAME", default="postgres")
print(f"DB 엔드포인트: {host}:{port}", flush=True)

password = secret("DB_PASSWORD") or getpass("DB 비밀번호: ")
if not password:
    raise ValueError("DB 비밀번호가 비어 있습니다.")

r = requests.get("https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem", timeout=(5, 15))
r.raise_for_status()
ca = Path("/content/rds-global-bundle.pem")
ca.write_bytes(r.content)

cfg = dict(host=host, port=port, user=user, password=password,
           sslmode="verify-full", sslrootcert=str(ca), connect_timeout=10,
           options="-c statement_timeout=30000 -c lock_timeout=5000")

dbname = secret("DB_NAME", default="dvdrental")
try:
    psycopg2.connect(**cfg, dbname=dbname).close()
except psycopg2.OperationalError as e:
    if "does not exist" not in str(e):
        raise
    print(f"⚠️ {dbname} DB가 없어 postgres로 접속합니다. (실습 3·심화는 dvdrental 필요)")
    dbname = "postgres"
cfg["dbname"] = dbname

def connect(name="cd10_1_lab"):
    c = psycopg2.connect(**cfg, application_name=name)
    c.autocommit = True
    return c

print(f"✅ DB 연결 완료 ({dbname}). 다음 실습 셀을 실행하세요.", flush=True)'''

LAB1 = '''c1, c2 = connect("cd10_1_session_A"), connect("cd10_1_session_B")
for name, c in (("세션 A", c1), ("세션 B", c2)):
    with c.cursor() as cur:
        cur.execute("SELECT pg_backend_pid()")
        print(name, "백엔드 PID =", cur.fetchone()[0])'''

LAB2 = '''with c1.cursor() as cur:
    for p in ["shared_buffers", "work_mem", "wal_buffers", "max_connections"]:
        cur.execute(f"SHOW {p}")
        print(f"{p:16} = {cur.fetchone()[0]}")
    cur.execute("""SELECT backend_type, count(*) AS n
                   FROM pg_stat_activity GROUP BY 1 ORDER BY 2 DESC""")
    display(pd.DataFrame(cur.fetchall(), columns=["backend_type", "n"]))'''

LAB3 = '''import pandas as pd
if "connect" not in globals():
    raise RuntimeError("먼저 맨 위 pip 셀과 '실습 1' 셀(AWS 인증·DB 접속)을 실행하세요.")
if "c1" not in globals() or c1.closed:
    c1 = connect("cd10_1_session_A")      # 런타임이 다시 시작됐으면 자동 재연결
c1.autocommit = True; cur = c1.cursor()

def walk(p, d=0):
    yield d, p
    for ch in p.get("Plans", []):
        yield from walk(ch, d + 1)

def name(n):
    pre = n.get("Partial Mode", "") if n.get("Partial Mode") not in (None, "Simple") else ""
    pre = (pre + " ") if pre else ("Parallel " if n.get("Parallel Aware") else "")
    return pre + n["Node Type"]

# ① 일부러 오류 내기: SQL 처리 몇 단계에서 멈추나?
rows = []
for sql, stage in [("SELEC * FROM film", "1단계 Parser (문법 검사)"),
                   ("SELECT * FROM filmx", "2단계 Analyzer (의미 검사)")]:
    try:
        cur.execute(sql)
    except Exception as e:
        rows.append([sql, type(e).__name__, stage, str(e).splitlines()[0]])
display(pd.DataFrame(rows, columns=["SQL", "오류", "멈춘 단계", "메시지"]))

# ② 실습 테이블: payment가 없으면 20만 행 테이블을 한 번만 생성
cur.execute("SELECT to_regclass('payment')")
T = "payment"
if cur.fetchone()[0] is None:
    T = "cd10_lab_payment"
    cur.execute(f"""CREATE TABLE IF NOT EXISTS {T} AS
        SELECT g AS payment_id,
               round((random() * 10)::numeric, 2) AS amount,
               now() - g * interval '1 minute' AS payment_date
        FROM generate_series(1, 200000) AS g""")
    cur.execute(f"ANALYZE {T}")

# ③ 같은 SELECT를 두 번: Planner의 선택(계획)과 Executor의 결과(실제)
q = f"SELECT sum(amount) FROM {T} WHERE amount >= 3"
summary = []
for i in (1, 2):
    cur.execute("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + q)
    res = cur.fetchone()[0][0]
    plan = res["Plan"]
    if i == 1:
        print(f"[실행계획 트리] 테이블 {T} · 아래(들여쓰기 깊은 쪽)부터 실행해 위로 올라옵니다")
        for d, n in walk(plan):
            rel = f" on {n['Relation Name']}" if "Relation Name" in n else ""
            print("    " * d + f"└ {name(n)}{rel}  (추정 {n['Plan Rows']:,}행 · 실제 {n['Actual Rows']:,}행)")
    scan = next(n for _, n in walk(plan) if "Scan" in n["Node Type"])
    summary.append([f"{i}차", name(scan),
                    f"{scan['Plan Rows']:,}", f"{scan['Actual Rows']:,}",
                    plan.get("Shared Hit Blocks", 0), plan.get("Shared Read Blocks", 0),
                    res.get("Planning", {}).get("Shared Read Blocks", 0),
                    round(res["Execution Time"], 1)])
display(pd.DataFrame(summary, columns=["실행", "스캔 방식(Planner 선택)", "추정 행(작업자당)", "실제 행(작업자당)",
                                       "shared hit(메모리)", "shared read(새로 읽음)", "계획 단계 read", "실행시간(ms)"]))'''

DEEP = '''if "T" not in globals():
    raise RuntimeError("먼저 '실습 3' 셀을 실행하세요. (실습 테이블과 실행계획 함수를 준비합니다)")
rows = []
for wm in ("64kB", "4MB", "32MB"):
    cur.execute(f"SET work_mem = '{wm}'")
    cur.execute(f"EXPLAIN (ANALYZE, FORMAT JSON) SELECT * FROM {T} ORDER BY amount, payment_date")
    sort = next(n for _, n in walk(cur.fetchone()[0][0]["Plan"]) if n["Node Type"] == "Sort")
    where = "메모리" if sort.get("Sort Space Type") == "Memory" else "디스크"
    rows.append([wm, sort.get("Sort Method"), f"{sort.get('Sort Space Used', 0):,}kB", where])
cur.execute("RESET work_mem")
display(pd.DataFrame(rows, columns=["work_mem", "정렬 방식", "사용 공간", "정렬 위치"]))'''

cells = [
    md("# CD10-1 PostgreSQL Architecture · Colab 실습\n"
       "**보안 비밀(왼쪽 열쇠)**: `AWS_ACCESS_KEY`, `AWS_SECRET_KEY` (필수), "
       "`DB_PASSWORD`(없으면 입력칸 표시), `DB_HOST`·`DB_PORT`(없으면 RDS 자동 조회) (선택)\n\n"
       "엔드포인트·포트는 AWS 키로 자동 조회합니다 (기존 실습: postgresql-lab-01, 포트 5433)."),
    code("!pip -q install boto3 psycopg2-binary pandas requests"),
    md("## 0 · AWS 인증과 RDS 접속 확인"),
    code(SETUP),
    md("## 실습 1 · 연결 2개 = 백엔드 프로세스 2개 (Client / Server Process)"),
    code(LAB1),
    md("## 실습 2 · 메모리 설정과 Utility 프로세스 관찰 (System Memory / Utility)"),
    code(LAB2),
    md("## 실습 3 · SQL 5단계를 오류와 실행계획으로 관찰 (Parser → Executor)"),
    code(LAB3),
    md("## 심화 · work_mem과 Sort Method (Local Memory)"),
    code(DEEP),
    code("c1.close(); c2.close()\nprint('연결 종료')"),
]
nb = {"cells": cells, "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3"}},
      "nbformat": 4, "nbformat_minor": 5}
out = sys.argv[1] if len(sys.argv) > 1 else "CD10-1_Colab_Lab(26).ipynb"
json.dump(nb, open(out, "w"), ensure_ascii=False, separators=(",", ":"))
print("saved", out)
