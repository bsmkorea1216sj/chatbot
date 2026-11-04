"""CD10-2 Colab 실습 노트북 생성: python colab_nb.py <출력.ipynb>  (접속 셀은 cd10-1/scripts/colab_nb.py의 SETUP 재사용)"""
import json, sys
from pathlib import Path

src = (Path(__file__).resolve().parents[2] / 'cd10-1' / 'scripts' / 'colab_nb.py').read_text(encoding='utf-8')
g = {}
exec(src.split('cells = [')[0], g)
SETUP = g['SETUP'].replace('def connect(name="cd10_1_lab")', 'def connect(name="cd10_2_lab")') + '''

def plan(q):
    cur.execute("EXPLAIN (ANALYZE, BUFFERS) " + q)
    print("\\n".join(r[0] for r in cur.fetchall()))
    print("-" * 70)

conn = connect("cd10_2_lab")
cur = conn.cursor()'''

LAB1 = '''cur.execute(\'\'\'CREATE TABLE IF NOT EXISTS cd10_orders AS
  SELECT i AS order_id, (i % 10000) + 1 AS customer_id, repeat('X', 100) AS memo
  FROM generate_series(1, 100000) g(i)\'\'\')
cur.execute("ANALYZE cd10_orders")
q = "SELECT * FROM cd10_orders WHERE customer_id = 42"

print("① 인덱스 전")
plan(q)
cur.execute("CREATE INDEX IF NOT EXISTS idx_cd10_orders_cust ON cd10_orders (customer_id)")
cur.execute("ANALYZE cd10_orders")
print("② 인덱스 후")
plan(q)'''

LAB2 = '''cur.execute(\'\'\'CREATE TABLE IF NOT EXISTS cd10_customers AS
  SELECT i AS customer_id FROM generate_series(1, 10000) g(i)\'\'\')
cur.execute("ANALYZE cd10_customers")
for cond in ("c.customer_id = 42", "c.customer_id <= 9000"):
    print("조건:", cond)
    plan(f\'\'\'SELECT c.customer_id, o.order_id
             FROM cd10_customers c JOIN cd10_orders o
               ON c.customer_id = o.customer_id
             WHERE {cond}\'\'\')'''

DEEP = '''cur.execute("CREATE INDEX IF NOT EXISTS idx_cd10_orders_id_btree ON cd10_orders (order_id)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_cd10_orders_id_brin ON cd10_orders USING brin (order_id)")
cur.execute(\'\'\'SELECT indexrelid::regclass AS index_name,
                      pg_size_pretty(pg_relation_size(indexrelid)) AS size
               FROM pg_index WHERE indrelid = 'cd10_orders'::regclass
               ORDER BY pg_relation_size(indexrelid) DESC\'\'\')
display(pd.DataFrame(cur.fetchall(), columns=["index", "size"]))'''

CLEAN = '''# 실습용 테이블 정리가 필요할 때만 주석을 풀고 실행
# cur.execute("DROP TABLE IF EXISTS cd10_orders, cd10_customers")
conn.close()
print("연결 종료")'''


def md(t):
    return {"cell_type": "markdown", "metadata": {}, "source": t}


def code(t):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": t}


cells = [
    md("# CD10-2 인덱스·스캔·조인 · Colab 실습\n"
       "**보안 비밀(왼쪽 열쇠)**: `AWS_ACCESS_KEY`, `AWS_SECRET_KEY` (필수), "
       "`DB_PASSWORD`(없으면 입력칸 표시), `DB_HOST`·`DB_PORT`(없으면 RDS 자동 조회) (선택)\n\n"
       "접속 방식은 CD10-1 노트북과 같습니다. 실습 테이블(`cd10_orders` 10만 행, `cd10_customers` 1만 행)은 접속한 DB에 만들어집니다."),
    code("!pip -q install boto3 psycopg2-binary pandas requests"),
    md("## 0 · AWS 인증과 RDS 접속, 실행계획 출력 함수 `plan()`"),
    code(SETUP),
    md("## 실습 1 · 인덱스 전후: Seq Scan → Index Scan\n스캔 노드, Buffers, Execution Time을 전·후로 비교합니다."),
    code(LAB1),
    md("## 실습 2 · 조회 범위에 따른 조인 방식 변화\n고객 1명 → Nested Loop, 9,000명 → Hash Join이 나오는지 확인합니다."),
    code(LAB2),
    md("## 심화 · B-tree와 BRIN 인덱스 크기 비교\n같은 컬럼(order_id)에 두 인덱스를 만들고 크기를 비교합니다."),
    code(DEEP),
    code(CLEAN),
]
nb = {"cells": cells, "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3"}},
      "nbformat": 4, "nbformat_minor": 5}
out = sys.argv[1] if len(sys.argv) > 1 else "CD10-2_Colab_Lab(26).ipynb"
json.dump(nb, open(out, "w"), ensure_ascii=False, indent=1)
print("saved", out)
