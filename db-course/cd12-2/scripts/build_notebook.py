"""CD12-2 개념적 모델링 Colab(26) 생성 — 12-1과 같은 형식(Colab 보안 비밀 → AWS RDS 생성 → 실습 → 삭제, 셀 = 교안 실습 단계).
1번(DB 생성)·5번(삭제) 셀은 실제 AWS에서 동작이 확인된 12-1 노트북의 셀을 그대로 가져온다.
  1. DB 생성 · 2. 표 만들기(엔티티 7개) · 과제 ① 관계 차수 · 3. 주문 트랜잭션(롤백 포함) · 4. CRUD 측정 · 과제 ② 주문취소 CRUD 예측 · 5. 삭제
교안(26) 쪽: 개요 4 · 엔티티 8 · 관계/ERD 11~13 · 과제① 14 · 트랜잭션 16~18 · CRUD 19(과제②)·20(정답) · 실습 끝내기 29
python build_notebook.py <CD12-1 노트북.ipynb> <출력.ipynb>"""
import json, sys

src12_1, out = sys.argv[1:3]
nb1 = json.load(open(src12_1))
S = lambda c: ''.join(c['source']) if isinstance(c['source'], list) else c['source']
C1 = {c['metadata'].get('id'): S(c) for c in nb1['cells']}
CELL1 = (C1['shop-db-create-run']
         .replace('(교안 13·31쪽)', '(교안 4쪽)')
         .replace('print("→ 다음: 2. 표 만들기")', 'print("→ 다음: 2. 표 만들기")'))
sys.path.insert(0, __import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)), '..', '..', 'cd12-1', 'scripts'))
from continue_chain import FINAL_CELL, FINAL_MD
CELL5 = FINAL_CELL.replace('__PAGE__', '29')
assert 'def ensure_lab_rds' in CELL1

GUARD1 = '''if "transaction" not in globals():
    raise SystemExit("⚠️ 먼저 1. DB 생성 셀을 실행하세요. (런타임을 다시 시작했다면 1번 셀부터)")
'''
GUARD2 = GUARD1 + '''if "model_schema" not in globals():
    raise SystemExit("⚠️ 먼저 2. 표 만들기 셀을 실행하세요.")
'''
GUARD3 = GUARD2 + '''if "create_order" not in globals():
    raise SystemExit("⚠️ 먼저 3. 주문 트랜잭션 셀을 실행하세요.")
'''

CELL2 = '''# @title 2. 12-1 DB 이어받기 · 표 5개 → 개념 모델 7개로 확장 (교안 8·11~13쪽)
''' + GUARD1 + r'''owned_schemas = globals().get("owned_schemas", set())
ENTITY_ORDER = ["customers", "orders", "order_details", "payments", "deliveries", "products", "reviews"]

MODEL_DDL = """
CREATE TABLE customers(customer_id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
    phone TEXT, address TEXT, points INTEGER NOT NULL DEFAULT 0 CHECK(points >= 0));
CREATE TABLE products(product_id INTEGER PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL,
    price INTEGER NOT NULL CHECK(price >= 0), stock INTEGER NOT NULL CHECK(stock >= 0));
CREATE TABLE orders(order_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    order_date TIMESTAMPTZ NOT NULL DEFAULT now(),
    status TEXT NOT NULL DEFAULT '주문접수' CHECK(status IN ('주문접수', '결제완료', '배송중', '취소')),
    total_amount INTEGER NOT NULL CHECK(total_amount >= 0));
CREATE TABLE order_details(order_id BIGINT NOT NULL REFERENCES orders(order_id),
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    quantity INTEGER NOT NULL CHECK(quantity > 0), unit_price INTEGER NOT NULL CHECK(unit_price >= 0),
    PRIMARY KEY(order_id, product_id));
CREATE TABLE payments(payment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id BIGINT NOT NULL UNIQUE REFERENCES orders(order_id),
    payment_date TIMESTAMPTZ, amount INTEGER NOT NULL CHECK(amount >= 0), method TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT '대기' CHECK(status IN ('대기', '승인', '환불')), approval_code TEXT UNIQUE);
CREATE TABLE deliveries(delivery_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id BIGINT NOT NULL UNIQUE REFERENCES orders(order_id),
    shipping_date DATE, expected_arrival DATE,
    delivery_status TEXT NOT NULL DEFAULT '준비' CHECK(delivery_status IN ('준비', '배송중', '배송완료')),
    tracking_number TEXT);
CREATE TABLE reviews(review_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5), comment TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now());
INSERT INTO customers VALUES (1, '실습 고객', 'customer1@example.com', NULL, NULL, 0),
                             (2, '이도윤', 'doyun@example.com', '010-0000-0002', '부산 해운대구', 0);
INSERT INTO products VALUES (101, '무선 마우스', '주변기기', 19900, 1), (102, '접이식 키보드', '주변기기', 32900, 5),
                            (103, '노트북 거치대', '주변기기', 24900, 3),
                            (201, '린넨 셔츠', '의류', 39000, 5), (202, '와이드 팬츠', '의류', 45000, 3),
                            (203, '캔버스 백', '잡화', 29000, 1);
"""

# 12-1의 shop 스키마(표 5개)를 개념 모델(표 7개)로 확장하는 변경 — 주문 데이터는 그대로 이어짐
MIGRATE = """
ALTER TABLE customers RENAME COLUMN id TO customer_id;
ALTER TABLE customers ADD COLUMN email TEXT, ADD COLUMN phone TEXT, ADD COLUMN address TEXT,
    ADD COLUMN points INTEGER NOT NULL DEFAULT 0 CHECK(points >= 0);
UPDATE customers SET email = 'customer' || customer_id || '@example.com' WHERE email IS NULL;
ALTER TABLE customers ALTER COLUMN email SET NOT NULL, ADD CONSTRAINT customers_email_key UNIQUE (email);
ALTER TABLE products RENAME COLUMN id TO product_id;
ALTER TABLE products ADD COLUMN category TEXT NOT NULL DEFAULT '주변기기';
ALTER TABLE orders RENAME COLUMN id TO order_id;
ALTER TABLE orders RENAME COLUMN created_at TO order_date;
ALTER TABLE orders ADD COLUMN status TEXT NOT NULL DEFAULT '주문접수'
        CHECK(status IN ('주문접수', '결제완료', '배송중', '취소')),
    ADD COLUMN total_amount INTEGER NOT NULL DEFAULT 0 CHECK(total_amount >= 0);
ALTER TABLE order_items RENAME TO order_details;
UPDATE orders o SET total_amount = t.s, status = '결제완료'
  FROM (SELECT order_id, sum(quantity * unit_price)::int AS s FROM order_details GROUP BY order_id) t
 WHERE t.order_id = o.order_id;
ALTER TABLE shipments RENAME TO deliveries;
ALTER TABLE deliveries RENAME COLUMN status TO delivery_status;
"""
MIGRATE_AFTER = """
UPDATE deliveries SET delivery_status = CASE delivery_status WHEN '준비 중' THEN '준비' WHEN '배송 중' THEN '배송중'
                                       WHEN '배송 완료' THEN '배송완료' ELSE delivery_status END;
ALTER TABLE deliveries ADD CONSTRAINT deliveries_status_check CHECK(delivery_status IN ('준비', '배송중', '배송완료')),
    ALTER COLUMN delivery_status SET DEFAULT '준비',
    ADD COLUMN delivery_id BIGINT GENERATED ALWAYS AS IDENTITY,
    ADD COLUMN shipping_date DATE, ADD COLUMN expected_arrival DATE, ADD COLUMN tracking_number TEXT;
ALTER TABLE deliveries ADD PRIMARY KEY (delivery_id), ADD CONSTRAINT deliveries_order_id_key UNIQUE (order_id);
CREATE TABLE payments(payment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id BIGINT NOT NULL UNIQUE REFERENCES orders(order_id),
    payment_date TIMESTAMPTZ, amount INTEGER NOT NULL CHECK(amount >= 0), method TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT '대기' CHECK(status IN ('대기', '승인', '환불')), approval_code TEXT UNIQUE);
INSERT INTO payments(order_id, payment_date, amount, method, status, approval_code)
    SELECT order_id, order_date, total_amount, '카드', '승인', 'AP' || lpad(order_id::text, 6, '0') FROM orders;
CREATE TABLE reviews(review_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5), comment TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now());
INSERT INTO customers(customer_id, name, email, phone, address) VALUES
    (2, '이도윤', 'doyun@example.com', '010-0000-0002', '부산 해운대구') ON CONFLICT DO NOTHING;
INSERT INTO products(product_id, name, category, price, stock) VALUES
    (201, '린넨 셔츠', '의류', 39000, 5), (202, '와이드 팬츠', '의류', 45000, 3), (203, '캔버스 백', '잡화', 29000, 1)
    ON CONFLICT (product_id) DO NOTHING;
"""

def new_model_schema():
    name = "cd12_2_" + uuid4().hex[:12]
    with transaction() as cur:
        cur.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(name)))
        cur.execute(sql.SQL("SET LOCAL search_path TO {}, pg_catalog").format(sql.Identifier(name)))
        cur.execute(MODEL_DDL)
    owned_schemas.add(name)
    return name

def drop_lab_schema(name):
    with transaction() as cur:
        cur.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(name)))
    owned_schemas.discard(name)

def relationships(schema):
    """FK 하나당 관계 1개. FK 열에 UNIQUE(또는 PK 전체)가 걸려 있으면 1:1, 아니면 1:N"""
    with transaction() as cur:
        cur.execute("""
            SELECT c.conrelid::regclass::text AS child, c.confrelid::regclass::text AS parent,
                   (SELECT string_agg(a.attname, ',') FROM pg_attribute a
                     WHERE a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey)) AS fk,
                   EXISTS (SELECT 1 FROM pg_constraint u WHERE u.conrelid = c.conrelid AND u.contype IN ('u', 'p')
                            AND u.conkey::int[] @> c.conkey::int[] AND c.conkey::int[] @> u.conkey::int[]) AS one_to_one
            FROM pg_constraint c WHERE c.contype = 'f' AND c.connamespace = %s::regnamespace""", (schema,))
        rows = cur.fetchall()
    return {(r["parent"].split(".")[-1], r["child"].split(".")[-1]): ("1:1" if r["one_to_one"] else "1:N", r["fk"]) for r in rows}

MODEL_SCHEMA = "shop"                        # 12-1에서 만든 고정 스키마 (12-3에서도 이어서 사용)
with transaction() as cur:
    cur.execute("SELECT to_regclass(%s) IS NOT NULL AS shop, to_regclass(%s) IS NOT NULL AS extended",
                (MODEL_SCHEMA + ".products", MODEL_SCHEMA + ".payments"))
    state = cur.fetchone()
if state["extended"]:
    how = "이미 확장됨 · 그대로 사용"
elif state["shop"]:
    with transaction(MODEL_SCHEMA) as cur:
        cur.execute(MIGRATE)
        cur.execute("""SELECT conname FROM pg_constraint WHERE conrelid = 'deliveries'::regclass AND contype IN ('c', 'p')""")
        for row in cur.fetchall():          # 12-1 배송 표의 상태 CHECK·PK(order_id)를 풀고 개념 모델 제약으로 교체
            cur.execute(sql.SQL("ALTER TABLE deliveries DROP CONSTRAINT {}").format(sql.Identifier(row["conname"])))
        cur.execute(MIGRATE_AFTER)
    how = "12-1 데이터 이어받아 확장"
else:
    with transaction() as cur:
        cur.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(MODEL_SCHEMA)))
        cur.execute(sql.SQL("SET LOCAL search_path TO {}, pg_catalog").format(sql.Identifier(MODEL_SCHEMA)))
        cur.execute(MODEL_DDL)
    how = "12-1 데이터 없음 · 새로 생성"
model_schema = MODEL_SCHEMA
with transaction(model_schema) as cur:
    cur.execute("SELECT (SELECT count(*) FROM orders) AS o, (SELECT count(*) FROM payments) AS p")
    counts = cur.fetchone()
    cur.execute("""SELECT table_name, string_agg(column_name, ', ' ORDER BY ordinal_position) AS cols
                   FROM information_schema.columns WHERE table_schema = %s GROUP BY table_name""", (model_schema,))
    cols = {r["table_name"]: r["cols"] for r in cur.fetchall()}
print(f"⑤ 개념 모델 표 7개 준비: {model_schema} ({how}) · 주문 {counts['o']}건 · 결제 {counts['p']}건")
for t in ENTITY_ORDER:
    print(f"   {t:13} ({cols[t]})")
print("   관계(FK)는 과제 ①에서 직접 맞혀 봅니다.")
print("→ 다음: 과제 ① 관계 차수")
'''

ASSIGN1 = '''# @title 과제 ① · 관계 차수 맞히기 — 입력칸에 1:1 또는 1:N (교안 14쪽)
''' + GUARD2 + r'''QUESTIONS = [("고객", "주문", "customers", "orders"), ("주문", "주문상세", "orders", "order_details"),
             ("상품", "주문상세", "products", "order_details"), ("주문", "결제", "orders", "payments"),
             ("주문", "배송", "orders", "deliveries"), ("고객", "리뷰", "customers", "reviews"),
             ("상품", "리뷰", "products", "reviews")]
truth = relationships(model_schema)
norm = lambda s: s.strip().upper().replace(" ", "").replace("：", ":").replace(";", ":").replace("ㅜ", "N").replace("ㅡ", "N").replace("M", "N")   # 한글 자판(ㅜ=n)·쌍점 실수 허용

def assignment1(tries=3):
    todo = list(QUESTIONS)
    for attempt in range(1, tries + 1):
        wrong = []
        for a, b, pa, ch in todo:
            ans = norm(input(f"{a} – {b} 관계의 차수 (1:1 또는 1:N): "))
            ok = ans == truth[(pa, ch)][0]
            print(("   ✅ " if ok else "   ❌ ") + f"{a}–{b}")
            if not ok:
                wrong.append((a, b, pa, ch))
        if not wrong:
            print("⑥ 과제 ① 통과 · 7개 관계 모두 정답 (FK 열에 UNIQUE가 있으면 1:1)")
            return True
        todo = wrong
        if attempt < tries:
            print(f"↻ 틀린 {len(wrong)}개만 다시 입력하세요 ({attempt}/{tries}) · 힌트: FK 열이 UNIQUE인지 보세요\n")
    print("💡 정답과 근거는 교안 14쪽 하단과 13쪽 ERD에 있습니다.")
    return False

assignment1()
print("→ 다음: 3. 주문 트랜잭션")
'''

CELL3 = '''# @title 3. 주문 트랜잭션 · 주문생성 → 결제승인 → 배송처리 → 리뷰작성, 실패하면 전체 롤백 (교안 16~18쪽)
''' + GUARD2 + r'''from contextlib import contextmanager

class OutOfStock(Exception):
    pass

def create_order(cur, customer_id, items, method="카드"):
    cur.execute("SELECT name FROM customers WHERE customer_id = %s", (customer_id,))
    if cur.fetchone() is None:
        raise ValueError("고객이 없습니다.")
    priced = []
    for product_id, qty in items:
        cur.execute("SELECT price FROM products WHERE product_id = %s", (product_id,))      # 재고 차감은 결제 승인 때
        priced.append((product_id, qty, cur.fetchone()["price"]))
    total = sum(q * p for _, q, p in priced)
    cur.execute("INSERT INTO orders(customer_id, total_amount) VALUES (%s, %s) RETURNING order_id", (customer_id, total))
    order_id = cur.fetchone()["order_id"]
    for product_id, qty, price in priced:
        cur.execute("INSERT INTO order_details VALUES (%s, %s, %s, %s)", (order_id, product_id, qty, price))
    cur.execute("INSERT INTO payments(order_id, amount, method) VALUES (%s, %s, %s)", (order_id, total, method))
    cur.execute("INSERT INTO deliveries(order_id) VALUES (%s)", (order_id,))
    return order_id

def approve_payment(cur, order_id):
    cur.execute("""SELECT c.name, o.status FROM orders o JOIN customers c USING (customer_id)
                   WHERE o.order_id = %s""", (order_id,))
    if cur.fetchone()["status"] != "주문접수":
        raise ValueError("주문접수 상태만 결제할 수 있습니다.")
    cur.execute("SELECT product_id, quantity FROM order_details WHERE order_id = %s ORDER BY product_id", (order_id,))
    for item in cur.fetchall():
        cur.execute("UPDATE products SET stock = stock - %s WHERE product_id = %s AND stock >= %s RETURNING stock",
                    (item["quantity"], item["product_id"], item["quantity"]))
        if cur.fetchone() is None:
            raise OutOfStock(f"상품 {item['product_id']} 재고 부족")
    cur.execute("""UPDATE payments SET status = '승인', payment_date = now(), approval_code = %s
                   WHERE order_id = %s""", (f"AP{order_id:06d}", order_id))
    cur.execute("UPDATE orders SET status = '결제완료' WHERE order_id = %s", (order_id,))

def ship_order(cur, order_id):
    cur.execute("""SELECT c.name, c.address, o.status, p.status AS paid FROM orders o
                   JOIN customers c USING (customer_id) JOIN payments p USING (order_id) WHERE o.order_id = %s""", (order_id,))
    head = cur.fetchone()
    if head["paid"] != "승인":
        raise ValueError("결제 승인된 주문만 배송합니다.")
    cur.execute("""SELECT pr.name FROM order_details d JOIN products pr USING (product_id)
                   WHERE d.order_id = %s""", (order_id,))            # 송장에 넣을 상품명
    cur.fetchall()
    cur.execute("""UPDATE deliveries SET delivery_status = '배송중', shipping_date = CURRENT_DATE,
                   expected_arrival = CURRENT_DATE + 2, tracking_number = %s WHERE order_id = %s""",
                (f"TRK{order_id:08d}", order_id))

def write_review(cur, customer_id, product_id, rating, comment):
    cur.execute("SELECT name FROM customers WHERE customer_id = %s", (customer_id,))
    cur.fetchone()
    cur.execute("SELECT name FROM products WHERE product_id = %s", (product_id,))
    cur.fetchone()
    cur.execute("INSERT INTO reviews(customer_id, product_id, rating, comment) VALUES (%s, %s, %s, %s)",
                (customer_id, product_id, rating, comment))

def cancel_order(cur, order_id):
    cur.execute("UPDATE orders SET status = '취소' WHERE order_id = %s AND status IN ('주문접수', '결제완료') RETURNING order_id",
                (order_id,))
    if cur.fetchone() is None:
        raise ValueError("배송 전 주문만 취소할 수 있습니다.")
    cur.execute("SELECT product_id, quantity FROM order_details WHERE order_id = %s", (order_id,))
    for item in cur.fetchall():
        cur.execute("UPDATE products SET stock = stock + %s WHERE product_id = %s", (item["quantity"], item["product_id"]))
    cur.execute("UPDATE payments SET status = '환불' WHERE order_id = %s", (order_id,))
    cur.execute("DELETE FROM deliveries WHERE order_id = %s", (order_id,))

def run(schema, fn, *args):
    with transaction(schema) as cur:          # 함수 안에서 오류가 나면 이 트랜잭션 전체가 ROLLBACK
        return fn(cur, *args)

def snapshot(schema, order_id):
    with transaction(schema) as cur:
        cur.execute("""SELECT o.status, p.status AS pay, d.delivery_status AS ship
                       FROM orders o JOIN payments p USING (order_id) LEFT JOIN deliveries d USING (order_id)
                       WHERE o.order_id = %s""", (order_id,))
        s = cur.fetchone()
        cur.execute("SELECT product_id, stock FROM products WHERE product_id >= 201 ORDER BY product_id")
        stock = {r["product_id"]: r["stock"] for r in cur.fetchall()}
    return f"주문 {s['status']} · 결제 {s['pay']} · 배송 {s['ship']} · 재고 {stock}"

with transaction(model_schema) as cur:      # 시연용 상품 재고를 처음 값으로 (다시 실행해도 같은 결과)
    cur.execute("UPDATE products p SET stock = v.s FROM (VALUES (201, 5), (202, 3), (203, 1)) v(id, s) WHERE p.product_id = v.id")
o1 = run(model_schema, create_order, 1, [(201, 2), (203, 1)])
print("주문생성  →", snapshot(model_schema, o1))
run(model_schema, approve_payment, o1)
print("결제승인  →", snapshot(model_schema, o1))
run(model_schema, ship_order, o1)
print("배송처리  →", snapshot(model_schema, o1))
run(model_schema, write_review, 1, 203, 5, "가볍고 튼튼해요")
print("리뷰작성  → 리뷰 1건 저장")

o2 = run(model_schema, create_order, 2, [(202, 1), (203, 1)])     # 캔버스 백은 이미 품절(재고 0)
try:
    run(model_schema, approve_payment, o2)
except OutOfStock as error:
    print(f"결제승인 실패({error}) → ROLLBACK:", snapshot(model_schema, o2))
    print("   와이드 팬츠 재고 3 그대로 = 앞에서 차감한 행까지 함께 취소됨 (원자성)")
print("⑦ 주문 트랜잭션 확인 완료 · 정상 흐름 4단계와 실패 시 전체 롤백")
print("→ 다음: 4. CRUD 측정")
'''

QUIZ_FN = '''def quiz(question, answer, page):
    norm = lambda x: str(x).replace(",", "").replace(" ", "").replace("개", "").replace("행", "").strip()
    for attempt in range(1, 3):
        if norm(input("🔎 " + question + " ")) == norm(answer):
            print("✅ 맞았습니다! 다음 셀을 실행해 확인하세요."); return True
        print(f"❌ 다시 생각해 보세요 ({attempt}/2)")
    print(f"💡 정답은 교안 {page}쪽 하단에 있습니다. 다음 셀 결과로 확인하세요."); return False
'''
QUIZ1 = '# 🔎 예측 퀴즈 ① · 다음 셀을 실행하기 전에 맞혀 보세요\n' + QUIZ_FN + "quiz('12-1의 표 5개를 개념 모델로 확장하면 표는 모두 몇 개가 될까요? (숫자)', 7, 8)\n"
QUIZ2 = '# 🔎 예측 퀴즈 ② · 다음 셀을 실행하기 전에 맞혀 보세요\n' + QUIZ_FN + "quiz('와이드 팬츠(재고 3)와 품절된 캔버스 백을 함께 주문해 결제승인이 실패하면, 와이드 팬츠 재고는 몇 개일까요? (숫자)', 3, 16)\n"
QUIZ3 = '# 🔎 예측 퀴즈 ③ · 다음 셀을 실행하기 전에 맞혀 보세요\n' + QUIZ_FN + "quiz('주문생성 트랜잭션에서 C(생성)가 일어나는 표는 몇 개일까요? (숫자)', 4, 18)\n"

CELL4 = '''# @title 4. CRUD 측정 · 트랜잭션마다 실제로 어떤 표를 만들고·읽고·고치고·지웠는지 (교안 19·20쪽)
''' + GUARD3 + r'''CRUD_COLS = [("Customers", "customers"), ("Orders", "orders"), ("Order Details", "order_details"),
             ("Payments", "payments"), ("Delivery", "deliveries"), ("Products", "products"), ("Review", "reviews")]

def measure(schema, fn, *args):
    """같은 트랜잭션 안에서 pg_stat_xact_user_tables(이번 트랜잭션 통계)로 C/R/U/D를 판정"""
    with transaction(schema) as cur:
        fn(cur, *args)
        cur.execute("""SELECT relname, seq_scan + COALESCE(idx_scan, 0) AS reads,
                              n_tup_ins AS c, n_tup_upd AS u, n_tup_del AS d
                       FROM pg_stat_xact_user_tables WHERE schemaname = %s""", (schema,))
        stats = {r["relname"]: r for r in cur.fetchall()}
    row = {}
    for _, table in CRUD_COLS:
        s = stats.get(table)
        letters = "".join(k.upper() for k in ("c", "u", "d") if s and s[k] > 0)
        row[table] = letters or ("R" if s and s["reads"] > 0 else "")
    return row

def show_matrix(rows):
    header = "트랜잭션".ljust(8) + "".join(name[:9].center(11) for name, _ in CRUD_COLS)
    print(header)
    for label, row in rows:
        print(label.ljust(8) + "".join((row[t] or "·").center(11) for _, t in CRUD_COLS))

crud_schema = new_model_schema()                  # 측정은 깨끗한 별도 스키마에서
try:
    rows = [("주문생성", measure(crud_schema, create_order, 1, [(101, 1)]))]
    with transaction(crud_schema) as cur:
        cur.execute("SELECT max(order_id) AS o FROM orders"); o = cur.fetchone()["o"]
    rows.append(("결제승인", measure(crud_schema, approve_payment, o)))
    rows.append(("배송처리", measure(crud_schema, ship_order, o)))
    rows.append(("리뷰작성", measure(crud_schema, write_review, 1, 101, 4, "좋아요")))
finally:
    drop_lab_schema(crud_schema)
crud_measured = dict(rows)
show_matrix(rows)
print("⑧ CRUD 측정 완료 · 교안 20쪽 정답과 비교 (· = 사용 안 함)")
print("   읽기(R)에는 외래키 확인으로 부모 표를 읽는 것도 포함됩니다.")
print("→ 다음: 과제 ② 주문취소 CRUD 예측")
'''

ASSIGN2 = '''# @title 과제 ② · ‘주문취소’ 행의 CRUD를 예측해 입력 → 실제 측정과 비교 (교안 19쪽, 정답 20쪽)
''' + GUARD3 + r'''if "measure" not in globals():
    raise SystemExit("⚠️ 먼저 4. CRUD 측정 셀을 실행하세요.")
print("주문취소: 주문 상태를 '취소'로 바꾸고, 주문상세를 읽어 재고를 되돌리고, 결제를 '환불'로 바꾸고, 배송 준비 행을 지웁니다.")
print("각 표에 C·R·U·D 중 하나를 입력하세요. 쓰지 않는 표는 - 를 입력합니다.\n")
guess = {}
for name, table in CRUD_COLS:
    v = input(f"주문취소 · {name}: ").strip().upper().replace("-", "").replace(" ", "")
    v = "".join({"ㅊ": "C", "ㄱ": "R", "ㅕ": "U", "ㅇ": "D"}.get(ch, ch) for ch in v)   # 한글 자판 상태로 입력해도 인정
    guess[table] = v

cancel_schema = new_model_schema()
try:
    with transaction(cancel_schema) as cur:
        o = create_order(cur, 1, [(101, 1)])
        approve_payment(cur, o)
    actual = measure(cancel_schema, cancel_order, o)
finally:
    drop_lab_schema(cancel_schema)

score = 0
for name, table in CRUD_COLS:
    ok = guess[table] == actual[table]
    score += ok
    print(("   ✅ " if ok else "   ❌ ") + f"{name}: 내 답 {guess[table] or '-'}" + ("" if ok else " (교안 20쪽 주문취소 행과 비교)"))
print(f"⑨ 과제 ② {score}/7 정답" + (" · 통과" if score == 7 else " · 틀린 칸은 교안 20쪽 정답과 노트 설명을 확인하세요"))
show_matrix(list(crud_measured.items()) + [("주문취소", actual)])
'''


def md(cid, text):
    return {'cell_type': 'markdown', 'metadata': {'id': cid}, 'source': text}


def code(cid, text):
    return {'cell_type': 'code', 'metadata': {'id': cid}, 'execution_count': None, 'outputs': [], 'source': text}


INTRO = '''# CD12-2 · 개념적 모델링을 AWS RDS에서 확인하기

**12-1에서 이어서** 진행합니다. 1번 셀이 12-1의 RDS를 다시 시작(중지돼 있으면)하고, 2번 셀이 12-1의 `shop` 데이터를 이어받아 개념 모델로 확장합니다. 12-1을 건너뛰었으면 처음부터 만듭니다. 실습이 끝나면 5번 셀로 **중지**하고 12-3에서 이어서 씁니다(**최종 삭제는 12-3**). 🔎 예측 퀴즈 3개로 결과를 먼저 맞혀 보세요(정답: 교안 8·16·18쪽 하단). 교안 각 페이지의 **Colab 버튼**이 아래 셀로 바로 이동합니다.

| 셀 | 하는 일 | 교안 |
|---|---|---|
| 1. DB 생성 | AWS 인증 → 실습 RDS 생성(없을 때만) → TLS 연결 확인 | 4쪽 |
| 2. 12-1 DB 이어받기 | 12-1 표 5개 → 엔티티 7개(고객·상품·주문·주문상세·결제·배송·리뷰)로 확장 | 8·11~13쪽 |
| **과제 ①** | 관계 차수(1:1 / 1:N) 맞히기 → 실제 FK·UNIQUE로 채점 | 14쪽 |
| 3. 주문 트랜잭션 | 주문생성 → 결제승인 → 배송처리 → 리뷰작성, 재고 부족 시 전체 롤백 | 16~18쪽 |
| 4. CRUD 측정 | 트랜잭션마다 실제 C·R·U·D를 측정해 매트릭스로 | 19·20쪽 |
| **과제 ②** | ‘주문취소’ 행 CRUD 예측 → 측정과 비교 | 19쪽 (정답 20쪽) |
| 5. 마무리 | RDS 중지(STOP) → 12-3에서 이어서 · 최종 삭제는 12-3 | 29쪽 |

**준비물 · Colab 보안 비밀** (왼쪽 열쇠 아이콘 → 각 항목 **노트북 액세스** 켜기): `AWS_ACCESS_KEY`, `AWS_SECRET_KEY`, `DB_PASSWORD`(새 RDS 관리자 비밀번호, 8자 이상) · 임시 키면 `AWS_SESSION_TOKEN` · `AWS_REGION` 선택(기본 ap-northeast-2)'''

GUIDE1 = C1 and next(S(c) for c in nb1['cells'] if c['metadata'].get('id') == 'shop-db-create').replace('(교안 13·31쪽)', '(교안 4쪽)')
cells = [
    md('m-intro', INTRO),
    md('m-db-create', GUIDE1), code('m-db-create-run', CELL1),
    md('m-tables', '## 2. 12-1 DB 이어받기 · 개념 모델로 확장 (교안 8·11~13쪽)\n\n12-1에서 만든 `shop` 스키마(표 5개, 웹앱 주문 포함)를 그대로 이어받아 개념 모델의 엔티티 7개로 확장합니다: 열 이름 정리(id → customer_id 등), `order_items` → `order_details`, `shipments` → `deliveries`, `payments`(기존 주문마다 결제 기록)·`reviews` 추가. 12-1을 하지 않았다면 처음부터 7개 표를 만듭니다. 출력의 열 목록을 교안 8쪽 속성 표와 비교하세요.'),
    code('m-quiz1', QUIZ1),
    code('m-tables-run', CELL2),
    md('m-assign1', '## 과제 ① 관계 차수 맞히기 (교안 14쪽)\n\n13쪽 ERD를 보고 7개 관계의 차수를 `1:1` 또는 `1:N`으로 입력합니다. 실제 RDS에 만든 제약조건(FK 열에 UNIQUE가 있으면 1:1)으로 바로 채점하고, 틀린 것만 다시 입력합니다(최대 3번). **정답은 교안 14쪽 하단**에 있습니다.'),
    code('m-assign1-run', ASSIGN1),
    md('m-transaction', '## 3. 주문 트랜잭션 (교안 16~18쪽)\n\n주문생성(주문·주문상세·결제 대기·배송 준비 INSERT) → 결제승인(재고 차감·결제 승인·주문 상태 UPDATE) → 배송처리 → 리뷰작성을 차례로 실행합니다. 이어서 **품절 상품이 섞인 주문의 결제승인이 실패하면, 앞에서 차감한 재고까지 전체가 롤백**되는 것(원자성)을 확인합니다.'),
    code('m-quiz2', QUIZ2),
    code('m-transaction-run', CELL3),
    md('m-crud', '## 4. CRUD 측정 (교안 19·20쪽)\n\n각 트랜잭션을 실행하는 같은 트랜잭션 안에서 PostgreSQL 통계(`pg_stat_xact_user_tables`)를 읽어, 표마다 **C(생성)·R(읽기)·U(수정)·D(삭제)**를 실제로 판정합니다. 결과를 교안 20쪽 CRUD 매트릭스와 비교하세요.'),
    code('m-quiz3', QUIZ3),
    code('m-crud-run', CELL4),
    md('m-assign2', '## 과제 ② ‘주문취소’ CRUD 예측 (교안 19쪽, 정답 20쪽)\n\n교안 19쪽 빈 매트릭스를 채운 뒤, 새 트랜잭션 **주문취소**의 7칸을 예측해 입력합니다. 셀이 실제로 주문취소를 실행해 측정한 결과와 칸마다 비교합니다.'),
    code('m-assign2-run', ASSIGN2),
    md('m-submit', '## 제출\n\n과제 ①·② 결과 화면(⑥·⑨)과 4번 셀의 CRUD 매트릭스를 캡처해 제출합니다. 출력에는 키·비밀번호가 표시되지 않습니다. 제출 후 **5번 셀에서 STOP**으로 RDS를 중지하세요(12-3에서 이어서 사용, 최종 삭제는 12-3).'),
    md('m-delete', FINAL_MD.replace('__PAGE__', '29')),
    code('m-delete-run', CELL5),
]
nb = {'cells': cells, 'metadata': {'kernelspec': {'name': 'python3', 'display_name': 'Python 3'}, 'language_info': {'name': 'python'}},
      'nbformat': 4, 'nbformat_minor': 5}
json.dump(nb, open(out, 'w'), ensure_ascii=False, indent=1)
print('ok ·', [c['metadata']['id'] for c in cells])
