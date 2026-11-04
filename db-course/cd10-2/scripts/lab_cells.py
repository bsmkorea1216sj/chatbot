"""CD10-2 노트북 실습 셀 원고 (요약 표 중심, 각 셀이 접속까지 스스로 함). colab_nb.py에서 사용."""
import textwrap
from pathlib import Path

_src = (Path(__file__).resolve().parents[2] / 'cd10-1' / 'scripts' / 'colab_nb.py').read_text(encoding='utf-8')
_g = {}
exec(_src.split('cells = [')[0], _g)
_SETUP_CORE = _g['SETUP'].split('\nc = connect(')[0].replace('def connect(name="cd10_1_lab")', 'def connect(name="cd10_2_lab")')

HELPERS = '''def walk(p, d=0):
    yield d, p
    for ch in p.get("Plans", []):
        yield from walk(ch, d + 1)

def name(n):
    pm = n.get("Partial Mode")
    pre = (pm + " ") if pm and pm != "Simple" else ("Parallel " if n.get("Parallel Aware") else "")
    return pre + n["Node Type"]

def explain(q):
    cur.execute("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + q)
    return cur.fetchone()[0][0]

def show_tree(res, title):
    print(f"[{title}] 실행계획 트리 · 아래(들여쓰기 깊은 쪽)부터 실행해 위로 올라옵니다")
    for d, n in walk(res["Plan"]):
        rel = f" on {n['Relation Name']}" if "Relation Name" in n else ""
        print("    " * d + f"└ {name(n)}{rel}  (추정 {n['Plan Rows']:,}행 · 실제 {n['Actual Rows']:,}행)")
    print()

def blocks(res, kind):
    p = res["Plan"]
    return p.get(f"Shared {kind} Blocks", 0) + p.get(f"Local {kind} Blocks", 0)'''

ENSURE = ('# ── 접속이 없으면 이 셀에서 바로 접속 (앞 셀을 건너뛰어도 됨) ──\n'
          'if "connect" not in globals():\n' + textwrap.indent(_SETUP_CORE, '    ') + '\n'
          'if "conn" not in globals() or conn.closed:\n    conn = connect("cd10_2_lab")\n'
          'cur = conn.cursor()\n'
          'import pandas as pd\n' + HELPERS + '\n'
          '# ───────────────────────────────────────────────\n')

ORDERS = '''cur.execute(\'\'\'CREATE TABLE IF NOT EXISTS cd10_orders AS
  SELECT i AS order_id, (i % 10000) + 1 AS customer_id, repeat('X', 100) AS memo
  FROM generate_series(1, 100000) g(i)\'\'\')
cur.execute("ANALYZE cd10_orders")'''

LAB1 = ENSURE + ORDERS + '''

# 같은 조회를 인덱스 전·후로 실행 (전 단계에서 인덱스를 지워 다시 실행해도 같은 비교가 됨)
q = "SELECT * FROM cd10_orders WHERE customer_id = 42"
rows = []
for label, ddl in [("① 인덱스 전", "DROP INDEX IF EXISTS idx_cd10_orders_cust"),
                   ("② 인덱스 후", "CREATE INDEX IF NOT EXISTS idx_cd10_orders_cust ON cd10_orders (customer_id)")]:
    cur.execute(ddl)
    cur.execute("ANALYZE cd10_orders")
    res = explain(q)
    show_tree(res, label)
    scans = " ← ".join(name(n) for _, n in walk(res["Plan"]) if "Scan" in n["Node Type"])
    rows.append([label, scans, res["Plan"]["Actual Rows"], blocks(res, "Hit") + blocks(res, "Read"),
                 round(res["Execution Time"], 2)])
display(pd.DataFrame(rows, columns=["구분", "스캔 방식(Planner 선택)", "결과 행", "읽은 페이지 수", "실행시간(ms)"]))'''

LAB2 = ENSURE + ORDERS + '''
cur.execute(\'\'\'CREATE TABLE IF NOT EXISTS cd10_customers AS
  SELECT i AS customer_id FROM generate_series(1, 10000) g(i)\'\'\')
cur.execute("CREATE INDEX IF NOT EXISTS idx_cd10_orders_cust ON cd10_orders (customer_id)")
cur.execute("ANALYZE cd10_customers")

rows = []
for label, cond in [("고객 1명", "c.customer_id = 42"), ("고객 9,000명", "c.customer_id <= 9000")]:
    res = explain(f\'\'\'SELECT c.customer_id, o.order_id
                       FROM cd10_customers c JOIN cd10_orders o ON c.customer_id = o.customer_id
                       WHERE {cond}\'\'\')
    show_tree(res, label)
    join = next((name(n) for _, n in walk(res["Plan"]) if "Join" in n["Node Type"] or n["Node Type"] == "Nested Loop"), "-")
    scans = ", ".join(f"{n['Relation Name']}: {name(n)}" for _, n in walk(res["Plan"]) if "Relation Name" in n)
    rows.append([label, join, scans, f"{res['Plan']['Actual Rows']:,}", round(res["Execution Time"], 2)])
display(pd.DataFrame(rows, columns=["조회 범위", "조인 방식(Planner 선택)", "테이블별 스캔", "결과 행", "실행시간(ms)"]))'''

DEEP = ENSURE + ORDERS + '''
cur.execute("CREATE INDEX IF NOT EXISTS idx_cd10_orders_id_btree ON cd10_orders (order_id)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_cd10_orders_id_brin ON cd10_orders USING brin (order_id)")
cur.execute(\'\'\'SELECT c.relname,
                      CASE WHEN c.relkind = 'r' THEN '테이블' ELSE am.amname END,
                      pg_size_pretty(pg_relation_size(c.oid)), pg_relation_size(c.oid)
               FROM pg_class c LEFT JOIN pg_am am ON am.oid = c.relam
               WHERE c.relname IN ('cd10_orders', 'idx_cd10_orders_id_btree', 'idx_cd10_orders_id_brin')
               ORDER BY 4 DESC\'\'\')
df = pd.DataFrame(cur.fetchall(), columns=["이름", "종류", "크기", "bytes"])
df["테이블 대비"] = (df["bytes"] / df["bytes"].max() * 100).round(2).astype(str) + "%"
display(df.drop(columns="bytes"))'''

INS1 = '''> **결과 읽는 법 (예상 · 실행 후 실측값으로 확인)**
> | 구분 | 스캔 방식 | 읽은 페이지 | 의미 |
> |---|---|---|---|
> | ① 인덱스 전 | Seq Scan (또는 Parallel Seq Scan) | 테이블 전체(수천 페이지) | 10행을 찾으려고 10만 행을 모두 읽음 |
> | ② 인덱스 후 | Bitmap Heap Scan ← Bitmap Index Scan | 수십 페이지 이하 | 인덱스로 위치를 찾고 그 페이지만 읽음 |
>
> - customer_id=42인 주문 10건이 테이블 곳곳에 흩어져 있어, 한 행씩 오가는 Index Scan보다 위치를 모아 읽는 **Bitmap** 방식이 자주 선택됩니다.
> - 결과 행은 둘 다 10행 → **같은 결과를 내는 다른 실행 방법**을 Planner가 고른 것입니다.'''

INS2 = '''> **결과 읽는 법 (예상 · 실행 후 실측값으로 확인)**
> | 조회 범위 | 조인 방식 | 테이블별 스캔 | 이유 |
> |---|---|---|---|
> | 고객 1명 | **Nested Loop** | customers: Index/Seq Scan, orders: Bitmap/Index Scan | 결과가 적어 한 명씩 인덱스로 찾는 것이 싸다 |
> | 고객 9,000명 | **Hash Join** | 양쪽 Seq Scan | 주문 9만 건을 인덱스로 9천 번 찾는 것보다 한 번에 읽어 짝짓는 것이 싸다 |
>
> - 인덱스가 있어도 **안 쓰는 것이 정답**일 수 있습니다. Planner는 예상 행 수로 비용을 계산해 방식을 바꿉니다.'''

INS3 = '''> **결과 읽는 법 (예상 · 실행 후 실측값으로 확인)**
> - B-tree는 모든 행의 값과 위치를 저장해 테이블의 수십 % 크기가 되고, BRIN은 블록 범위의 최소·최대값만 저장해 **수십 KB 수준**으로 매우 작습니다.
> - order_id처럼 **저장 순서대로 커지는 값**에서 BRIN이 잘 맞습니다. customer_id처럼 값이 흩어진 컬럼에서는 BRIN 효과가 작습니다.'''
