"""CD12-3 논리적·물리적 모델링 Colab(26) 생성 — 12-1·12-2와 같은 형식, 12장 마지막 차시(최종 삭제).
같은 RDS(cd12-shop-lab)·고정 스키마 shop을 이어서 쓴다.
  1. DB 생성(중지된 RDS 시작) · 🔎① · 2. 논리 스키마(12-2 모델 → 교안 릴레이션 스키마로 정렬) · 3. 무결성 제약 · 과제 ① 제약 예측
  🔎② · 4. Fillfactor · 🔎③ · 5. 인덱스·클러스터링 · 6. 파티셔닝·테이블스페이스 · 과제 ② 파티션 예측 · 7. 물리 설계 적용 · 8. 마무리(최종 삭제)
교안(26) 쪽: 개요 4 · 릴레이션 스키마 12~18 · 무결성 20 · 과제① 21 · 전환 23 · Fillfactor 32·33 · 인덱스 34 · 파티셔닝 35 · 과제② 36
             · 테이블스페이스 37 · 물리 DDL 39~52 · 추가 최적화 54·55 · 실습 끝내기 57
python build_notebook.py <CD12-1 노트북> <CD12-2 노트북> <출력.ipynb>"""
import json, os, sys

src1, src2, out = sys.argv[1:4]
S = lambda c: ''.join(c['source']) if isinstance(c['source'], list) else c['source']
C1 = {c['metadata'].get('id'): S(c) for c in json.load(open(src1))['cells']}
C2 = {c['metadata'].get('id'): S(c) for c in json.load(open(src2))['cells']}
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'cd12-1', 'scripts'))
from continue_chain import FINAL_CELL

CELL1 = C1['shop-db-create-run'].replace('(교안 13·31쪽)', '(교안 4쪽)')
assert 'def ensure_lab_rds' in CELL1 and 'def transaction' in CELL1

# 12-2의 2번 셀에서 '표 준비' 부분(새로 생성 / 12-1 마이그레이션 / 이미 확장)만 가져온다
c2 = C2['m-tables-run']
PREP = c2[c2.index('owned_schemas = '):c2.index('model_schema = MODEL_SCHEMA')]
assert 'MIGRATE_AFTER' in PREP and 'MODEL_DDL' in PREP

GUARD1 = '''if "transaction" not in globals():
    raise SystemExit("⚠️ 먼저 1. DB 생성 셀을 실행하세요. (런타임을 다시 시작했다면 1번 셀부터)")
'''
GUARD2 = GUARD1 + '''if "logical_schema" not in globals():
    raise SystemExit("⚠️ 먼저 2. 논리 스키마 셀을 실행하세요.")
'''

QUIZ_FN = '''def quiz(question, answer, page):
    norm = lambda x: str(x).replace(",", "").replace(" ", "").replace("개", "").replace("번", "").replace(")", "").strip().upper()
    for attempt in range(1, 3):
        if norm(input("🔎 " + question + " ")) == norm(answer):
            print("✅ 맞았습니다! 다음 셀을 실행해 확인하세요."); return True
        print(f"❌ 다시 생각해 보세요 ({attempt}/2)")
    print(f"💡 정답은 교안 {page}쪽 하단에 있습니다. 다음 셀 결과로 확인하세요."); return False
'''
QUIZ1 = ('# 🔎 예측 퀴즈 ① · 다음 셀을 실행하기 전에 맞혀 보세요\n' + QUIZ_FN +
         "quiz('12-2 ERD의 관계 7개(1:1·1:N)를 논리 모델로 옮기면 외래키(FK)는 모두 몇 개가 될까요? (숫자)', 7, 23)\n")
QUIZ2 = ('# 🔎 예측 퀴즈 ② · 다음 셀을 실행하기 전에 맞혀 보세요\n' + QUIZ_FN +
         "quiz('fillfactor 100 표와 80 표에서 같은 행(10%)을 UPDATE하면, 같은 페이지 안에서 끝나는 HOT 업데이트가 더 많은 쪽은? (100 또는 80)', 80, 32)\n")
QUIZ3 = ('# 🔎 예측 퀴즈 ③ · 다음 셀을 실행하기 전에 맞혀 보세요\n' + QUIZ_FN +
         "quiz('주문 30만 건 중 customer_id = 42 (10건)를 찾을 때, 인덱스를 만든 뒤의 실행 계획은? 1) Seq Scan(표 전체 훑기)  2) 인덱스 사용(Index Scan 또는 Bitmap Index Scan)  (번호)', 2, 33)\n")

# ── 2. 논리 스키마: 12-2 개념 모델 → 교안 12~18쪽 릴레이션 스키마의 열 이름·속성으로 정렬
CELL2 = '''# @title 2. 논리 스키마 · 12-2 개념 모델 → 릴레이션 스키마(교안 12~18쪽 열 이름)로 정렬 (교안 12~18·23쪽)
''' + GUARD1 + PREP + r'''
# 교안 12~18쪽 CREATE TABLE의 열 이름·속성에 맞춘다 (데이터는 그대로)
ALIGN = """
ALTER TABLE customers ADD COLUMN password_hash TEXT NOT NULL DEFAULT md5('실습용-비밀번호'),
    ADD COLUMN signup_date TIMESTAMPTZ NOT NULL DEFAULT now(), ADD COLUMN membership TEXT NOT NULL DEFAULT '일반';
ALTER TABLE products RENAME COLUMN name TO product_name;
ALTER TABLE products ADD COLUMN description TEXT, ADD COLUMN image_url TEXT, ADD COLUMN size TEXT, ADD COLUMN color TEXT,
    ADD COLUMN register_date TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE orders RENAME COLUMN status TO order_status;
ALTER TABLE orders ADD COLUMN ship_address TEXT;
UPDATE orders o SET ship_address = COALESCE(c.address, '미입력') FROM customers c WHERE c.customer_id = o.customer_id;
ALTER TABLE orders ALTER COLUMN ship_address SET NOT NULL, ALTER COLUMN ship_address SET DEFAULT '미입력';
ALTER TABLE payments RENAME COLUMN method TO payment_method;
ALTER TABLE payments RENAME COLUMN approval_code TO auth_code;
ALTER TABLE deliveries RENAME COLUMN shipping_date TO start_date;
ALTER TABLE deliveries RENAME COLUMN expected_arrival TO expected_date;
ALTER TABLE deliveries RENAME COLUMN tracking_number TO tracking_no;
ALTER TABLE reviews RENAME COLUMN comment TO review_text;
ALTER TABLE reviews RENAME COLUMN created_at TO review_date;
"""
with transaction(MODEL_SCHEMA) as cur:
    cur.execute("SELECT 1 FROM information_schema.columns WHERE table_schema = %s AND table_name = 'payments' AND column_name = 'payment_method'",
                (MODEL_SCHEMA,))
    aligned = cur.fetchone() is not None
    if not aligned:
        cur.execute(ALIGN)
logical_schema = MODEL_SCHEMA

def relation_schemas(schema):
    """표마다 열 목록 + PK·FK·UQ 표시 (논리 모델 표기)"""
    with transaction(schema) as cur:
        cur.execute("""
            SELECT c.relname AS t, a.attname AS col, a.attnum,
                   EXISTS (SELECT 1 FROM pg_constraint k WHERE k.conrelid = c.oid AND k.contype = 'p' AND a.attnum = ANY(k.conkey)) AS pk,
                   (SELECT string_agg(f.confrelid::regclass::text, ',') FROM pg_constraint f
                     WHERE f.conrelid = c.oid AND f.contype = 'f' AND a.attnum = ANY(f.conkey)) AS fk,
                   EXISTS (SELECT 1 FROM pg_constraint u WHERE u.conrelid = c.oid AND u.contype = 'u' AND u.conkey = ARRAY[a.attnum]) AS uq
            FROM pg_class c JOIN pg_attribute a ON a.attrelid = c.oid
            WHERE c.relnamespace = %s::regnamespace AND c.relkind = 'r' AND a.attnum > 0 AND NOT a.attisdropped
            ORDER BY c.relname, a.attnum""", (schema,))
        rows = cur.fetchall()
        cur.execute("SELECT count(*) AS n FROM pg_constraint WHERE connamespace = %s::regnamespace AND contype = 'f'", (schema,))
        fk_count = cur.fetchone()["n"]
    tables = {}
    for r in rows:
        mark = (" PK" if r["pk"] else "") + (f" FK→{r['fk'].split('.')[-1]}" if r["fk"] else "") + (" UQ" if r["uq"] else "")
        tables.setdefault(r["t"], []).append(r["col"] + mark)
    return tables, fk_count

tables, fk_count = relation_schemas(logical_schema)
with transaction(logical_schema) as cur:
    cur.execute("SELECT (SELECT count(*) FROM orders) AS o, (SELECT count(*) FROM reviews) AS r")
    counts = cur.fetchone()
print(f"⑤ 논리 스키마 준비: {logical_schema} ({how}{' · 이미 정렬됨' if aligned else ' → 교안 열 이름으로 정렬'}) · 주문 {counts['o']}건 · 리뷰 {counts['r']}건")
for t in ENTITY_ORDER:
    print(f"   {t}(" + ", ".join(tables[t]) + ")")
print(f"   외래키(FK) {fk_count}개 = 12-2 ERD의 관계 {fk_count}개 (1:1은 FK 열에 UQ)")
print("→ 다음: 3. 무결성 제약")
'''

CELL3 = '''# @title 3. 무결성 제약 · 표마다 PK·FK·UNIQUE·CHECK·NOT NULL 개수 (교안 20쪽)
''' + GUARD2 + r'''with transaction(logical_schema) as cur:
    cur.execute("""
        SELECT c.relname AS t,
               count(*) FILTER (WHERE k.contype = 'p') AS pk, count(*) FILTER (WHERE k.contype = 'f') AS fk,
               count(*) FILTER (WHERE k.contype = 'u') AS uq, count(*) FILTER (WHERE k.contype = 'c') AS ck,
               (SELECT count(*) FROM pg_attribute a WHERE a.attrelid = c.oid AND a.attnum > 0 AND a.attnotnull AND NOT a.attisdropped) AS nn
        FROM pg_class c LEFT JOIN pg_constraint k ON k.conrelid = c.oid
        WHERE c.relnamespace = %s::regnamespace AND c.relkind = 'r' GROUP BY c.oid, c.relname""", (logical_schema,))
    stats = {r["t"]: r for r in cur.fetchall()}
    cur.execute("""SELECT conrelid::regclass::text AS t, pg_get_constraintdef(oid) AS d FROM pg_constraint
                   WHERE connamespace = %s::regnamespace AND contype = 'c' ORDER BY 1""", (logical_schema,))
    checks = cur.fetchall()
print("표".ljust(15) + "PK  FK  UNIQUE  CHECK  NOT NULL")
for t in ENTITY_ORDER:
    s = stats[t]
    print(f"{t:15}{s['pk']:>2}{s['fk']:>4}{s['uq']:>8}{s['ck']:>7}{s['nn']:>10}")
print("CHECK 예:", " / ".join(r["d"].replace("CHECK ", "") for r in checks[:4]), "…")
print("⑥ 무결성 제약 확인 · 이 제약들이 잘못된 데이터를 실제로 막는지 과제 ①에서 예측해 봅니다.")
print("→ 다음: 과제 ① 무결성 제약 예측")
'''

ASSIGN1 = '''# @title 과제 ① · 이 SQL은 성공할까 실패할까? O(성공) / X(실패) 입력 (교안 21쪽)
''' + GUARD2 + r'''import psycopg2
from contextlib import closing
from psycopg2.extras import RealDictCursor

TESTS = [
    ("이미 있는 이메일로 고객 추가", "INSERT INTO customers(customer_id, name, email) VALUES (9001, '김중복', 'customer1@example.com')"),
    ("같은 고객이 주문 1건 더", "INSERT INTO orders(customer_id, total_amount, ship_address) VALUES (1, 19900, '서울 성동구')"),
    ("평점 6점 리뷰", "INSERT INTO reviews(customer_id, product_id, rating, review_text) VALUES (1, 101, 6, '최고예요')"),
    ("없는 고객(999)의 주문", "INSERT INTO orders(customer_id, total_amount, ship_address) VALUES (999, 1000, '서울')"),
    ("결제된 주문에 결제 1건 더", "INSERT INTO payments(order_id, amount, payment_method) VALUES (%(paid)s, 19900, '카드')"),
    ("상품 재고를 -1로", "UPDATE products SET stock = -1 WHERE product_id = 101"),
    ("평점 5점 리뷰", "INSERT INTO reviews(customer_id, product_id, rating, review_text) VALUES (1, 101, 5, '잘 쓰고 있어요')"),
]
KIND = {"p": "PK", "f": "FK", "u": "UNIQUE", "c": "CHECK"}

def run_tests():
    """모두 한 트랜잭션에서 실행하고 마지막에 ROLLBACK → shop 데이터는 바뀌지 않음"""
    results = []
    with closing(connect_db()) as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SET search_path TO shop, pg_catalog")
        cur.execute("INSERT INTO orders(customer_id, total_amount, ship_address) VALUES (1, 19900, '서울') RETURNING order_id")
        paid = cur.fetchone()["order_id"]
        cur.execute("INSERT INTO payments(order_id, amount, payment_method, status) VALUES (%s, 19900, '카드', '승인')", (paid,))
        for name, stmt in TESTS:
            cur.execute("SAVEPOINT t")
            try:
                cur.execute(stmt, {"paid": paid})
                results.append(("O", ""))
            except psycopg2.Error as e:
                cur.execute("ROLLBACK TO SAVEPOINT t")
                cname = e.diag.constraint_name or ""
                cur.execute("SELECT contype FROM pg_constraint WHERE conname = %s AND connamespace = 'shop'::regnamespace", (cname,))
                row = cur.fetchone()
                results.append(("X", f"{KIND.get(row['contype'], '') if row else ''} {cname}".strip()))
        conn.rollback()
    return results

actual = run_tests()
for i, (name, stmt) in enumerate(TESTS, 1):
    print(f"{i}. {name}\n   {stmt.replace('%(paid)s', '(결제된 주문 번호)')}")
norm = lambda s: {"0": "O", "ㅐ": "O", "ㅇ": "O", "ㅌ": "X", "×": "X"}.get(s.strip().upper(), s.strip().upper())
todo = list(range(len(TESTS)))
for attempt in range(1, 4):
    print()
    wrong = []
    for i in todo:
        guess = norm(input(f"{i + 1}. {TESTS[i][0]} → O(성공) / X(실패): "))
        ok = guess == actual[i][0]
        why = actual[i][1] or "제약 위반 없음"
        print(("   ✅ " if ok else "   ❌ ") + (f"실제 결과 {actual[i][0]} · {why}" if ok else "다시 생각해 보세요 (힌트: 교안 20쪽 무결성 제약)"))
        if not ok:
            wrong.append(i)
    if not wrong:
        print(f"⑦ 과제 ① 통과 · {len(TESTS)}문항 모두 정답 (실행은 모두 ROLLBACK → shop 데이터 그대로)")
        break
    todo = wrong
    if attempt < 3:
        print(f"↻ 틀린 {len(wrong)}개만 다시 입력하세요 ({attempt}/3)")
else:
    print("💡 정답: " + ", ".join(f"{i + 1}={actual[i][0]}" for i in range(len(TESTS))) + " · 교안 21쪽 하단")
print("→ 다음: 4. Fillfactor")
'''

LAB_PREP = r'''LAB = "lab12_3"                               # 성능 실험용 스키마 (7번 셀에서 정리)
with transaction() as cur:
    cur.execute("CREATE SCHEMA IF NOT EXISTS lab12_3")
'''

CELL4 = '''# @title 4. Fillfactor · 페이지에 빈 공간을 남기면 UPDATE가 같은 페이지 안에서 끝난다(HOT) (교안 31·32쪽)
''' + GUARD1 + LAB_PREP + r'''ff_result = {}
for ff in (100, 80):
    table = f"{LAB}.ff{ff}"
    with transaction(LAB) as cur:
        cur.execute(f"DROP TABLE IF EXISTS ff{ff}")
        cur.execute(f"CREATE TABLE ff{ff}(id INTEGER PRIMARY KEY, status TEXT NOT NULL, memo CHAR(200) NOT NULL) WITH (fillfactor = {ff})")
        cur.execute(f"INSERT INTO ff{ff} SELECT g, '주문접수', '메모' FROM generate_series(1, 20000) g")
    with transaction(LAB) as cur:
        cur.execute("SELECT pg_relation_size(%s) / 8192 AS pages", (table,))
        before = cur.fetchone()["pages"]
        cur.execute(f"UPDATE ff{ff} SET status = '결제완료' WHERE id % 10 = 0")      # 자주 바뀌는 10%
        cur.execute("SELECT n_tup_upd AS upd, n_tup_hot_upd AS hot FROM pg_stat_xact_user_tables WHERE relid = %s::regclass", (table,))
        s = cur.fetchone()
    with transaction(LAB) as cur:
        cur.execute("SELECT pg_relation_size(%s) / 8192 AS pages", (table,))
        after = cur.fetchone()["pages"]
    ff_result[ff] = dict(pages=before, after=after, upd=s["upd"], hot=s["hot"])
    print(f"fillfactor {ff:>3} · 처음 {before:,}페이지 · UPDATE {s['upd']:,}행 중 HOT {s['hot']:,}행 ({s['hot'] / s['upd']:.0%}) · 갱신 후 {after:,}페이지")
print("⑧ Fillfactor 확인 · 80은 처음부터 페이지가 더 많지만(20% 비움), UPDATE가 같은 페이지에서 끝나 표가 덜 커진다")
print("   PostgreSQL은 UPDATE 때 새 행 버전을 쓰므로, 같은 페이지에 자리가 있으면 인덱스를 고치지 않는 HOT 업데이트가 된다")
print("→ 다음: 5. 인덱스·클러스터링")
'''

CELL5 = '''# @title 5. 인덱스·클러스터링 · 실행 계획(EXPLAIN)과 읽은 페이지 수 비교 (교안 33쪽)
''' + GUARD1 + LAB_PREP + r'''def plan(cur, query):
    cur.execute("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + query)
    p = cur.fetchone()["QUERY PLAN"][0]
    nodes, stack = [], [p["Plan"]]
    while stack:
        n = stack.pop(); nodes.append(n["Node Type"]); stack.extend(n.get("Plans", []))
    pages = p["Plan"].get("Shared Hit Blocks", 0) + p["Plan"].get("Shared Read Blocks", 0)
    scan = " ← ".join(t for t in nodes if "Scan" in t) or nodes[0]
    return scan, pages, p["Execution Time"]

with transaction(LAB) as cur:
    cur.execute("DROP TABLE IF EXISTS orders_big CASCADE")
    cur.execute("CREATE TABLE orders_big(order_id BIGINT PRIMARY KEY, customer_id INTEGER NOT NULL, order_date DATE NOT NULL, amount INTEGER NOT NULL)")
    cur.execute("""INSERT INTO orders_big                            -- 주문 30만 건 (고객 3만 명, 날짜는 1년에 흩어짐)
                   SELECT g, 1 + (g * 7919) % 30000, DATE '2026-01-01' + ((g * 104729) % 365)::int, 10000 + (g * 31) % 90000
                   FROM generate_series(1::bigint, 300000) g""")
    cur.execute("ANALYZE orders_big")
Q1 = "SELECT * FROM orders_big WHERE customer_id = 42"
with transaction(LAB) as cur:
    before = plan(cur, Q1)
    cur.execute("CREATE INDEX idx_orders_big_customer ON orders_big(customer_id)")
    after = plan(cur, Q1)
index_used = "Index" in after[0]
print(f"① 인덱스  {Q1}")
print(f"   전: {before[0]:<36} · 읽은 페이지 {before[1]:>5,} · {before[2]:7.2f} ms")
print(f"   후: {after[0]:<36} · 읽은 페이지 {after[1]:>5,} · {after[2]:7.2f} ms   (CREATE INDEX idx_orders_big_customer)")

Q2 = "SELECT count(*), sum(amount) FROM orders_big WHERE order_date BETWEEN '2026-03-01' AND '2026-03-07'"
with transaction(LAB) as cur:
    cur.execute("CREATE INDEX idx_order_date ON orders_big(order_date)")
    cur.execute("ANALYZE orders_big")
    cur.execute("SELECT correlation FROM pg_stats WHERE schemaname = %s AND tablename = 'orders_big' AND attname = 'order_date'", (LAB,))
    corr_before = round(cur.fetchone()["correlation"], 2) + 0.0
    c_before = plan(cur, Q2)
with transaction(LAB) as cur:
    cur.execute("CLUSTER orders_big USING idx_order_date")       # 표의 실제 행 순서를 order_date 순으로 재정렬
    cur.execute("ANALYZE orders_big")
    cur.execute("SELECT correlation FROM pg_stats WHERE schemaname = %s AND tablename = 'orders_big' AND attname = 'order_date'", (LAB,))
    corr_after = round(cur.fetchone()["correlation"], 2) + 0.0
    c_after = plan(cur, Q2)
print(f"② 클러스터링  일주일(3/1~3/7) 주문 합계")
print(f"   전: 날짜 정렬도 {corr_before:+.2f} · {c_before[0]:<36} · 읽은 페이지 {c_before[1]:>5,} · {c_before[2]:7.2f} ms")
print(f"   후: 날짜 정렬도 {corr_after:+.2f} · {c_after[0]:<36} · 읽은 페이지 {c_after[1]:>5,} · {c_after[2]:7.2f} ms   (CLUSTER orders_big USING idx_order_date)")
print("⑨ 인덱스·클러스터링 확인 · 인덱스는 찾는 길을, 클러스터링은 행을 모아 읽을 페이지 수를 줄인다")
print("   CLUSTER는 한 번만 정렬한다. 이후 들어오는 행은 다시 흩어지므로 주기적으로 다시 실행해야 한다")
print("→ 다음: 6. 파티셔닝·테이블스페이스")
'''

CELL6 = '''# @title 6. 파티셔닝·테이블스페이스 · 날짜로 나눈 주문 표에서 필요한 파티션만 읽기 (교안 34·36·53·54쪽)
''' + GUARD1 + LAB_PREP + r'''if "orders_big" not in str(globals().get("Q1", "")):
    raise SystemExit("⚠️ 먼저 5. 인덱스·클러스터링 셀을 실행하세요 (주문 30만 건을 만듭니다).")

def partitions_read(cur, where):
    cur.execute("EXPLAIN (FORMAT JSON) SELECT count(*) FROM orders_part WHERE " + where)
    found, stack = set(), [cur.fetchone()["QUERY PLAN"][0]["Plan"]]
    while stack:
        n = stack.pop(); stack.extend(n.get("Plans", []))
        if "Relation Name" in n:
            found.add(n["Relation Name"])
    return sorted(found)

with transaction(LAB) as cur:
    cur.execute("DROP TABLE IF EXISTS orders_part CASCADE")
    cur.execute("""CREATE TABLE orders_part(order_id BIGINT NOT NULL, customer_id INTEGER NOT NULL,
                       order_date DATE NOT NULL, amount INTEGER NOT NULL) PARTITION BY RANGE(order_date)""")
    for m in (1, 2, 3):                                  # 끝 값(TO)은 포함하지 않음 → 다음 달 1일로 적는다
        cur.execute(f"CREATE TABLE orders_2026_0{m} PARTITION OF orders_part FOR VALUES FROM ('2026-0{m}-01') TO ('2026-0{m + 1}-01')")
    cur.execute("INSERT INTO orders_part SELECT * FROM orders_big WHERE order_date < '2026-04-01'")
    cur.execute("ANALYZE orders_part")
    cur.execute("SELECT tableoid::regclass::text AS p, count(*) AS n FROM orders_part GROUP BY 1 ORDER BY 1")
    sizes = cur.fetchall()
    read = partitions_read(cur, "order_date BETWEEN '2026-02-01' AND '2026-02-28'")
    cur.execute("SAVEPOINT s")
    try:
        cur.execute("INSERT INTO orders_part VALUES (999999, 1, '2026-04-01', 1000)")
        out_of_range = "들어감"
    except psycopg2.Error:
        cur.execute("ROLLBACK TO SAVEPOINT s")
        out_of_range = "거부됨 (맞는 파티션 없음)"
    cur.execute("SELECT spcname FROM pg_tablespace ORDER BY 1")
    spaces = [r["spcname"] for r in cur.fetchall()]
print("① 파티션별 행 수:", " · ".join(f"{r['p'].split('.')[-1]} {r['n']:,}" for r in sizes))
print(f"② 2월 한 달 조회 → 읽은 파티션 {len(read)}개: {', '.join(read)} (나머지는 건너뜀 = 파티션 프루닝)")
print(f"③ 4월 1일 주문 넣기 → {out_of_range} · 범위 끝(TO)은 포함되지 않으므로 4월 파티션을 미리 만들어야 한다")
print(f"④ 테이블스페이스: {', '.join(spaces)} · RDS는 저장소(EBS)를 AWS가 관리하므로 디스크 경로(LOCATION)를 나눠 쓰는 효과는 없다")
print("⑩ 파티셔닝 확인")
print("→ 다음: 과제 ② 파티션 예측")
'''

ASSIGN2 = '''# @title 과제 ② · 이 조회는 파티션을 몇 개 읽을까? (교안 35쪽)
''' + GUARD1 + r'''if "partitions_read" not in globals():
    raise SystemExit("⚠️ 먼저 6. 파티셔닝·테이블스페이스 셀을 실행하세요.")
QUESTIONS = [
    ("1월 20일 ~ 3월 9일", "order_date >= '2026-01-20' AND order_date < '2026-03-10'"),
    ("주문번호 5000번", "order_id = 5000"),
    ("3월 1일 하루", "order_date = '2026-03-01'"),
    ("1월 31일 하루", "order_date = '2026-01-31'"),
]
with transaction(LAB) as cur:
    answers = [partitions_read(cur, w) for _, w in QUESTIONS]
todo = list(range(len(QUESTIONS)))
for attempt in range(1, 4):
    wrong = []
    for i in todo:
        name, where = QUESTIONS[i]
        guess = input(f"{name} · WHERE {where} → 읽는 파티션 수 (1~3): ").strip().replace("개", "")
        ok = guess == str(len(answers[i]))
        print(("   ✅ " if ok else "   ❌ ") + (f"{len(answers[i])}개: {', '.join(answers[i])}" if ok else "다시 생각해 보세요 (힌트: 파티션 키는 order_date)"))
        if not ok:
            wrong.append(i)
    if not wrong:
        print(f"⑪ 과제 ② 통과 · 파티션 키(order_date)로 거르지 않으면 모든 파티션을 읽는다")
        break
    todo = wrong
    if attempt < 3:
        print(f"↻ 틀린 {len(wrong)}개만 다시 입력하세요 ({attempt}/3)\n")
else:
    print("💡 정답: " + ", ".join(f"{QUESTIONS[i][0]} {len(answers[i])}개" for i in range(len(QUESTIONS))) + " · 교안 35쪽 하단")
print("→ 다음: 7. 물리 설계 적용")
'''

CELL7 = '''# @title 7. 물리 설계 적용 · 교안 38~51쪽의 인덱스·fillfactor·클러스터를 shop 표에 적용 (교안 38~51쪽)
''' + GUARD2 + r'''PHYSICAL = [
    ("customers", None, "ALTER TABLE customers SET (fillfactor = 90)"),
    ("products", "idx_products_category", "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category)"),
    ("products", "idx_products_name", "CREATE INDEX IF NOT EXISTS idx_products_name ON products(product_name)"),
    ("orders", "idx_orders_customer_date", "CREATE INDEX IF NOT EXISTS idx_orders_customer_date ON orders(customer_id, order_date)"),
    ("order_details", "idx_order_details_product", "CREATE INDEX IF NOT EXISTS idx_order_details_product ON order_details(product_id)"),
    ("payments", "idx_payments_method", "CREATE INDEX IF NOT EXISTS idx_payments_method ON payments(payment_method)"),
    ("deliveries", "idx_deliveries_status", "CREATE INDEX IF NOT EXISTS idx_deliveries_status ON deliveries(delivery_status)"),
    ("reviews", "idx_reviews_product", "CREATE INDEX IF NOT EXISTS idx_reviews_product ON reviews(product_id)"),
]
with transaction(logical_schema) as cur:
    for t in ENTITY_ORDER:
        cur.execute(f"ALTER TABLE {t} SET (fillfactor = 90)")         # 교안 38~51쪽 WITH (fillfactor = 90)
    for _, _, stmt in PHYSICAL[1:]:
        cur.execute(stmt)
    # 교안 39쪽 CREATE UNIQUE INDEX idx_customers_email: 이미 UNIQUE 제약이 같은 인덱스(customers_email_key)를 만들어 둠
    cur.execute("CLUSTER customers USING customers_email_key")
    cur.execute("ANALYZE")
    cur.execute("""SELECT tablename AS t, string_agg(indexname, ', ' ORDER BY indexname) AS idx
                   FROM pg_indexes WHERE schemaname = %s GROUP BY 1""", (logical_schema,))
    idx = {r["t"]: r["idx"] for r in cur.fetchall()}
    cur.execute("""SELECT relname AS t, reloptions FROM pg_class
                   WHERE relnamespace = %s::regnamespace AND relkind = 'r'""", (logical_schema,))
    opts = {r["t"]: r["reloptions"] for r in cur.fetchall()}
for t in ENTITY_ORDER:
    print(f"   {t:14} {', '.join(opts[t] or [])} · 인덱스: {idx.get(t, '')}")
with transaction() as cur:
    cur.execute("DROP SCHEMA IF EXISTS lab12_3 CASCADE")             # 4~6번 실험용 표 정리
print("⑫ 물리 설계 적용 완료 · PK·UNIQUE는 인덱스를 자동으로 만든다(이메일은 따로 만들지 않음) · 실험용 lab12_3 정리")
print("→ 다음: 제출 후 8. 마무리(최종 삭제)")
'''

# ── 8. 마무리: 12장 마지막 → 기본은 DELETE(최종 삭제)
CELL8 = (FINAL_CELL.replace('__PAGE__', '57')
         .replace('# @title 5. 마무리 · RDS 중지 (다음 수업에서 이어서) · 최종 삭제는 12-3 마지막 (교안 57쪽)',
                  '# @title 8. 마무리 · 12장 실습 끝 · AWS의 실습 RDS 최종 삭제 (교안 57쪽)')
         .replace('print(f"RDS {instance}가 없습니다. 다음 수업의 1번 셀이 새로 만듭니다.")',
                  'print(f"RDS {instance}가 없습니다. 이미 삭제됐습니다.")')
         .replace('answer = input(f"다음 수업까지 RDS {instance}를 중지하려면 STOP, 과정을 그만두고 완전히 지우려면 DELETE (그대로 두려면 Enter): ").strip().upper()',
                  'answer = input(f"12장 실습이 모두 끝났습니다. RDS {instance}를 완전히 지우려면 DELETE (나중에 다시 보려면 STOP, 그대로 두려면 Enter): ").strip().upper()')
         .replace('print(f"RDS {instance} 삭제 요청 완료 · 이어서 할 데이터도 함께 지워집니다. 다음 수업의 1번 셀이 새로 만듭니다.")',
                  'print(f"RDS {instance} 최종 삭제 요청 완료 · 5~10분 뒤 사라지며 요금이 멈춥니다. 12-1~12-3 실습 데이터(shop)도 함께 지워집니다.")\n'
                  '            print("   보안 그룹 cd12-shop-lab-sg는 요금이 없어 남겨 둡니다(원하면 EC2 콘솔에서 삭제).")')
         .replace('print("   ※ AWS는 중지 7일 뒤 자동으로 다시 시작하므로, 수업 간격이 길면 콘솔에서 다시 중지하세요. 최종 삭제는 12-3 마지막 셀.")',
                  'print("   ※ AWS는 중지 7일 뒤 자동으로 다시 시작합니다. 다 봤으면 이 셀에서 DELETE로 지우세요.")')
         .replace('print("그대로 둡니다. 켜져 있는 동안 요금이 나오므로 수업이 끝나면 STOP으로 중지하세요.")',
                  'print("그대로 둡니다. 켜져 있는 동안 요금이 나오므로 끝나면 이 셀에서 DELETE로 지우세요.")'))
assert '최종 삭제 요청 완료' in CELL8 and '12장 실습이 모두 끝났습니다' in CELL8 and '8. 마무리' in CELL8


def md(cid, text):
    return {'cell_type': 'markdown', 'metadata': {'id': cid}, 'source': text}


def code(cid, text):
    return {'cell_type': 'code', 'metadata': {'id': cid}, 'execution_count': None, 'outputs': [], 'source': text}


INTRO = '''# CD12-3 · 논리적·물리적 모델링을 AWS RDS에서 확인하기

**12-1 → 12-2에서 이어서** 진행하는 12장 마지막 실습입니다. 1번 셀이 중지해 둔 RDS를 다시 시작하고, 2번 셀이 12-2의 `shop` 표 7개를 교안의 릴레이션 스키마(열 이름)로 정렬합니다(앞 차시를 건너뛰었으면 처음부터 만듭니다). 4~6번 셀은 주문 30만 건으로 fillfactor·인덱스·클러스터링·파티셔닝의 효과를 직접 재고, 7번 셀이 물리 설계를 `shop`에 적용합니다. **마지막 8번 셀에서 RDS를 최종 삭제**합니다. 🔎 예측 퀴즈 3개(정답: 교안 23·32·33쪽 하단)와 과제 2개가 중간에 있습니다.

| 셀 | 하는 일 | 교안 |
|---|---|---|
| 1. DB 생성 | 중지된 RDS 다시 시작(없으면 새로 생성) → TLS 연결 확인 | 4쪽 |
| 2. 논리 스키마 | 12-2 표 7개 → 릴레이션 스키마(열 이름·PK·FK·UQ)로 정렬 · 🔎퀴즈 ① | 12~18·23쪽 |
| 3. 무결성 제약 | 표마다 PK·FK·UNIQUE·CHECK·NOT NULL 개수 | 20쪽 |
| **과제 ①** | SQL 7개가 성공(O)/실패(X)할지 예측 → 실제 실행(ROLLBACK)으로 채점 | 21쪽 |
| 4. Fillfactor | fillfactor 100 vs 80, UPDATE의 HOT 비율·페이지 수 · 🔎퀴즈 ② | 31·32쪽 |
| 5. 인덱스·클러스터링 | 30만 건에서 EXPLAIN 실행 계획·읽은 페이지 비교 · 🔎퀴즈 ③ | 33쪽 |
| 6. 파티셔닝·테이블스페이스 | 월별 파티션, 필요한 파티션만 읽기, RDS의 테이블스페이스 | 34·36·53·54쪽 |
| **과제 ②** | 조회마다 읽는 파티션 수 예측 → EXPLAIN으로 채점 | 35쪽 |
| 7. 물리 설계 적용 | 교안의 인덱스·fillfactor·클러스터를 shop에 적용 | 38~51쪽 |
| 8. 마무리 | **DELETE → RDS 최종 삭제** (12장 끝) | 57쪽 |

**준비물 · Colab 보안 비밀** (왼쪽 열쇠 아이콘 → 각 항목 **노트북 액세스** 켜기): `AWS_ACCESS_KEY`, `AWS_SECRET_KEY`, `DB_PASSWORD`(12-1에서 정한 RDS 관리자 비밀번호) · 임시 키면 `AWS_SESSION_TOKEN` · `AWS_REGION` 선택(기본 ap-northeast-2)'''

GUIDE1 = next(S(c) for c in json.load(open(src1))['cells'] if c['metadata'].get('id') == 'shop-db-create').replace('(교안 13·31쪽)', '(교안 4쪽)')
cells = [
    md('l-intro', INTRO),
    md('l-db-create', GUIDE1), code('l-db-create-run', CELL1),
    md('l-schema', '## 2. 논리 스키마 (교안 12~18·23쪽)\n\n개념 모델(12-2)의 엔티티·관계를 **릴레이션 스키마**로 옮깁니다. 12-2의 `shop` 표 7개를 데이터는 그대로 둔 채 교안 12~18쪽 CREATE TABLE의 열 이름에 맞춥니다(예: `name` → `product_name`, `method` → `payment_method`, `password_hash`·`ship_address` 추가). 출력의 `PK`·`FK→표`·`UQ` 표시를 교안과 비교하세요.'),
    code('l-quiz1', QUIZ1),
    code('l-schema-run', CELL2),
    md('l-integrity', '## 3. 무결성 제약 (교안 20쪽)\n\n기본키·외래키(참조 무결성), UNIQUE(중복 방지), CHECK(값의 범위), NOT NULL이 표마다 몇 개 걸려 있는지 확인합니다.'),
    code('l-integrity-run', CELL3),
    md('l-assign1', '## 과제 ① 무결성 제약 예측 (교안 21쪽)\n\nSQL 7개가 **성공(O)할지 실패(X)할지** 예측해 입력합니다. 셀이 실제로 실행해 어떤 제약이 막았는지 보여 주고, 틀린 것만 다시 입력합니다(최대 3번). 모든 실행은 마지막에 ROLLBACK하므로 `shop` 데이터는 바뀌지 않습니다. **정답은 교안 21쪽 하단**.'),
    code('l-assign1-run', ASSIGN1),
    md('l-fillfactor', '## 4. Fillfactor (교안 31·32쪽)\n\n같은 2만 행을 `fillfactor = 100`과 `80`인 표에 넣고, 자주 바뀌는 10%의 행을 UPDATE합니다. 빈 공간이 있으면 새 행 버전이 같은 페이지에 들어가 인덱스를 고치지 않는 **HOT 업데이트**가 됩니다.'),
    code('l-quiz2', QUIZ2),
    code('l-fillfactor-run', CELL4),
    md('l-index', '## 5. 인덱스·클러스터링 (교안 33쪽)\n\n주문 30만 건을 만들어 `EXPLAIN (ANALYZE, BUFFERS)`로 실행 계획·읽은 페이지 수·시간을 비교합니다. ① 고객 1명의 주문: 인덱스 전/후 ② 일주일 주문 합계: `CLUSTER` 전/후(행이 날짜순으로 모이면 읽을 페이지가 줄어듦).'),
    code('l-quiz3', QUIZ3),
    code('l-index-run', CELL5),
    md('l-partition', '## 6. 파티셔닝·테이블스페이스 (교안 34·36·53·54쪽)\n\n주문을 월별(1~3월) **RANGE 파티션**으로 나누고, 2월만 조회하면 2월 파티션만 읽는 것(파티션 프루닝)을 확인합니다. 범위의 끝 값(`TO`)은 포함되지 않는다는 점, RDS에서 테이블스페이스가 어떻게 보이는지도 확인합니다.'),
    code('l-partition-run', CELL6),
    md('l-assign2', '## 과제 ② 파티션 수 예측 (교안 35쪽)\n\n조회 4개가 파티션(1~3월)을 **몇 개 읽을지** 입력합니다. 셀이 EXPLAIN 실행 계획으로 채점합니다. **정답은 교안 35쪽 하단**.'),
    code('l-assign2-run', ASSIGN2),
    md('l-physical', '## 7. 물리 설계 적용 (교안 38~51쪽)\n\n교안의 물리 설계(표마다 `fillfactor = 90`, 조회용 인덱스 7개, 이메일 인덱스 기준 `CLUSTER`)를 `shop` 표에 실제로 적용하고, 4~6번 실험용 `lab12_3` 스키마를 정리합니다.'),
    code('l-physical-run', CELL7),
    md('l-submit', '## 제출\n\n과제 ①·② 결과(⑦·⑪)와 5번 셀(인덱스·클러스터링 전/후) 결과를 캡처해 제출합니다. 출력에는 키·비밀번호가 표시되지 않습니다. 제출 후 **8번 셀에서 DELETE**로 RDS를 최종 삭제하세요.'),
    md('l-delete', '## 8. 마무리 · RDS 최종 삭제 (교안 57쪽)\n\n12장(12-1~12-3) 실습이 모두 끝났습니다. `DELETE`를 입력하면 AWS의 실습 RDS `cd12-shop-lab`이 **최종 삭제**되어 요금이 멈춥니다(스냅샷 없음, `shop` 데이터도 함께 삭제). 나중에 다시 볼 계획이면 `STOP`(중지)을 입력하되, AWS는 7일 뒤 자동으로 다시 시작하므로 끝나면 꼭 DELETE 하세요. 런타임을 다시 시작했어도 이 셀만 실행하면 됩니다.'),
    code('l-delete-run', CELL8),
]
nb = {'cells': cells, 'metadata': {'kernelspec': {'name': 'python3', 'display_name': 'Python 3'}, 'language_info': {'name': 'python'}},
      'nbformat': 4, 'nbformat_minor': 5}
for c in cells:
    if c['cell_type'] == 'code':
        compile(c['source'], c['metadata']['id'], 'exec')
json.dump(nb, open(out, 'w'), ensure_ascii=False, indent=1)
print('ok ·', [c['metadata']['id'] for c in cells])
