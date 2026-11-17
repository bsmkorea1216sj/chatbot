"""Upgrade the CD12-1 shopping lab to RDS PostgreSQL and add deletion workflows."""
import argparse
import json
from pathlib import Path
from textwrap import dedent

AWS_GUIDE = """
## 0. AWS RDS 준비와 연결

1. AWS 콘솔 → RDS → 데이터베이스에서 실습용 PostgreSQL 인스턴스를 선택합니다. 없다면 PostgreSQL을 선택해 실습용 인스턴스를 만들고 상태가 **사용 가능**이 될 때까지 기다립니다. 과금 설정은 생성 화면에서 확인하세요.
2. RDS의 **연결 및 보안**에서 엔드포인트와 포트를 확인합니다. VPC 보안 그룹은 접속할 실습 런타임의 IP만 허용합니다. 일반 호스팅 Colab에서 바로 연결할 때는 해당 런타임에서 접근 가능한 RDS 엔드포인트가 필요합니다. 비공개 RDS는 VPC에 접근할 수 있는 Colab 로컬 런타임 등 승인된 연결 경로를 사용합니다.
3. Colab의 열쇠 메뉴에 `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`를 등록하고 노트북 접근을 허용합니다. DB 이름을 따로 만들지 않았다면 일반적으로 `postgres`를 사용합니다. 로그인 역할에는 실습 DB의 CONNECT·CREATE 권한이 필요합니다. 비밀번호는 코드 셀이 실행될 때 직접 입력합니다.
4. [AWS 공식 RDS CA 번들](https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem)을 내려받아 Colab 파일 패널의 `/content/global-bundle.pem`에 올립니다. 연결은 인증서와 엔드포인트를 검증합니다.

[AWS RDS PostgreSQL 접속 안내](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_ConnectToPostgreSQLInstance.html)
"""

AWS = '''
import sys
import subprocess
import os
from pathlib import Path
from getpass import getpass
from uuid import uuid4
from contextlib import contextmanager, closing

try:
    import psycopg2
except ModuleNotFoundError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "psycopg2-binary"])
    import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor

try:
    from google.colab import userdata
except ModuleNotFoundError:
    userdata = None

def setting(name):
    value = userdata.get(name) if userdata is not None else os.environ.get(name)
    if not value or not value.strip():
        raise ValueError(f"{name} 값을 등록하세요.")
    return value.strip()

ca = Path("/content/global-bundle.pem")
if not ca.is_file():
    raise FileNotFoundError("AWS 공식 CA 번들을 /content/global-bundle.pem에 먼저 올리세요.")

db_config = dict(host=setting("DB_HOST"), port=int(setting("DB_PORT")),
                 dbname=setting("DB_NAME"), user=setting("DB_USER"),
                 password=getpass("RDS PostgreSQL 비밀번호: "),
                 sslmode="verify-full", sslrootcert=str(ca), connect_timeout=8,
                 application_name="cd12_shopping_lab")

@contextmanager
def transaction(schema=None):
    with closing(psycopg2.connect(**db_config)) as conn, conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if schema is not None:
                cur.execute(sql.SQL("SET LOCAL search_path TO {}, pg_catalog").format(sql.Identifier(schema)))
            yield cur

with transaction() as cur:
    cur.execute("SELECT current_database() AS db, ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid()")
    connected = cur.fetchone()
    assert connected["ssl"], "TLS 연결이어야 합니다."
    print("연결 확인:", connected["db"], "· TLS 인증서 및 호스트 확인")
'''

DB = '''
owned_schemas = globals().get("owned_schemas", set())

def new_lab_schema():
    name = "cd12_shop_" + uuid4().hex[:16]
    with transaction() as cur:
        cur.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(name)))
        cur.execute(sql.SQL("SET LOCAL search_path TO {}, pg_catalog").format(sql.Identifier(name)))
        cur.execute("""
        CREATE TABLE customers(id INTEGER PRIMARY KEY, name TEXT NOT NULL);
        CREATE TABLE products(id INTEGER PRIMARY KEY, name TEXT NOT NULL,
            price INTEGER NOT NULL CHECK(price >= 0), stock INTEGER NOT NULL CHECK(stock >= 0));
        CREATE TABLE orders(id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            customer_id INTEGER NOT NULL REFERENCES customers(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE order_items(order_id BIGINT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
            product_id INTEGER NOT NULL REFERENCES products(id), quantity INTEGER NOT NULL CHECK(quantity > 0),
            unit_price INTEGER NOT NULL CHECK(unit_price >= 0), PRIMARY KEY(order_id, product_id));
        CREATE TABLE shipments(order_id BIGINT PRIMARY KEY REFERENCES orders(id) ON DELETE CASCADE,
            status TEXT NOT NULL CHECK(status IN ('준비 중', '배송 중', '배송 완료')));
        INSERT INTO customers VALUES (1, '실습 고객');
        INSERT INTO products VALUES (101, '무선 마우스', 19900, 1),
            (102, '접이식 키보드', 32900, 5), (103, '노트북 거치대', 24900, 3);
        """)
    owned_schemas.add(name)
    return name

def drop_lab_schema(name):
    if name not in owned_schemas:
        raise ValueError("현재 런타임에서 만든 실습 스키마만 삭제할 수 있습니다.")
    with transaction(name) as cur:
        tables = [sql.Identifier(name, table) for table in
                  ("shipments", "order_items", "orders", "products", "customers")]
        cur.execute(sql.SQL("DROP TABLE {}").format(sql.SQL(", ").join(tables)))
        cur.execute(sql.SQL("DROP SCHEMA {} RESTRICT").format(sql.Identifier(name)))
    owned_schemas.remove(name)

if "shop_schema" not in globals() or shop_schema not in owned_schemas:
    shop_schema = new_lab_schema()
with transaction(shop_schema) as cur:
    cur.execute("SELECT id, name, price, stock FROM products ORDER BY id")
    print(shop_schema, [dict(row) for row in cur.fetchall()])
'''

ORDER = '''
class SoldOut(ValueError):
    pass

def place_order(schema, product_id, quantity):
    if not 1 <= quantity <= 2_147_483_647 or not 1 <= product_id <= 2_147_483_647:
        raise ValueError("상품과 수량을 확인하세요.")
    with transaction(schema) as cur:
        cur.execute("UPDATE products SET stock = stock - %s WHERE id = %s AND stock >= %s RETURNING price",
                    (quantity, product_id, quantity))
        product = cur.fetchone()
        if product is None:
            raise SoldOut("재고가 부족하거나 상품이 없습니다.")
        cur.execute("INSERT INTO orders(customer_id) VALUES (1) RETURNING id")
        order_id = cur.fetchone()["id"]
        cur.execute("INSERT INTO order_items VALUES (%s, %s, %s, %s)",
                    (order_id, product_id, quantity, product["price"]))
        cur.execute("INSERT INTO shipments VALUES (%s, '준비 중')", (order_id,))
    return order_id

def cancel_order(schema, order_id):
    if not 1 <= order_id <= 9_223_372_036_854_775_807:
        return False
    with transaction(schema) as cur:
        cur.execute("""
            SELECT s.status FROM orders o JOIN shipments s ON s.order_id = o.id
            WHERE o.id = %s AND o.customer_id = 1 FOR UPDATE OF o, s
        """, (order_id,))
        shipment = cur.fetchone()
        if shipment is None or shipment["status"] != "준비 중":
            return False
        cur.execute("""
            UPDATE products p SET stock = p.stock + i.quantity
            FROM order_items i WHERE i.product_id = p.id AND i.order_id = %s
        """, (order_id,))
        cur.execute("DELETE FROM orders WHERE id = %s AND customer_id = 1", (order_id,))
    return True

def order_history(cur):
    cur.execute("""
       SELECT o.id, p.name, i.quantity, i.unit_price, i.quantity::bigint * i.unit_price AS total,
              s.status
       FROM orders o JOIN order_items i ON i.order_id = o.id
       JOIN products p ON p.id = i.product_id JOIN shipments s ON s.order_id = o.id
       WHERE o.customer_id = 1 ORDER BY o.id DESC
    """)
    return cur.fetchall()
'''

CANCEL_ROUTE = '''
        if method == "POST" and route == "/orders/cancel":
            try:
                size = int(environ.get("CONTENT_LENGTH") or 0)
                if not 0 < size <= 1024:
                    raise ValueError()
                fields = parse_qs(environ["wsgi.input"].read(size).decode("utf-8"), max_num_fields=4)
                order_id = int(fields["order_id"][0])
            except (KeyError, ValueError):
                return send("400 Bad Request", layout("취소 실패", "<p>주문번호를 확인하세요.</p>"))
            if not cancel_order(schema, order_id):
                return send("409 Conflict", layout("취소 불가", "<p>준비 중인 주문만 취소할 수 있습니다.</p>"))
            return send("303 See Other", "", (("Location", "../orders"),))
'''

CANCEL_FORM = '''<form method="post" action="orders/cancel">
        <input type="hidden" name="order_id" value="{order_id}">
        <button>주문 취소 및 삭제</button></form>'''

TEST = '''
from urllib.request import urlopen, Request
from urllib.error import HTTPError

def expect_status(url, body, code):
    try:
        with urlopen(Request(url, data=body), timeout=15) as response:
            assert response.status == code
            return response.read().decode()
    except HTTPError as error:
        with error:
            assert error.code == code, error.code

test_schema = new_lab_schema()
try:
    with make_server("127.0.0.1", 0, make_app(test_schema)) as test_server:
        thread = Thread(target=test_server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{test_server.server_port}/"
        try:
            with urlopen(base, timeout=15) as response:
                assert "무선 마우스" in response.read().decode()
            payload = b"product=101&quantity=1"
            assert "준비 중" in expect_status(base + "orders", payload, 200)
            expect_status(base + "orders", payload, 409)
            with transaction(test_schema) as cur:
                cur.execute("UPDATE products SET price=21900 WHERE id=101")
                rows = order_history(cur)
                assert len(rows) == 1 and rows[0]["unit_price"] == 19900
                order_id = rows[0]["id"]
            cancel_payload = f"order_id={order_id}".encode()
            assert "주문이 없습니다" in expect_status(base + "orders/cancel", cancel_payload, 200)
            expect_status(base + "orders/cancel", cancel_payload, 409)
            with transaction(test_schema) as cur:
                cur.execute("SELECT stock FROM products WHERE id=101")
                assert cur.fetchone()["stock"] == 1
                for table in ("orders", "order_items", "shipments"):
                    cur.execute(sql.SQL("SELECT count(*) AS n FROM {}").format(sql.Identifier(table)))
                    assert cur.fetchone()["n"] == 0
        finally:
            test_server.shutdown()
            thread.join(timeout=10)
finally:
    drop_lab_schema(test_schema)

print("통과 · 상품 조회 / 주문·배송 / 품절 / 단가 보존 / 삭제·재고 복구 / 중복 취소 차단")
'''

RUN = '''
from google.colab import output

def stop_preview():
    server = globals().pop("preview_server", None)
    if server is not None:
        server.shutdown()
        server.server_close()

stop_preview()
preview_server = make_server("127.0.0.1", 0, make_app(shop_schema))
Thread(target=preview_server.serve_forever, daemon=True).start()
output.serve_kernel_port_as_iframe(preview_server.server_port, height=660)
'''

CLEAN = '''
def cleanup_lab(confirm):
    if confirm != "DELETE LAB":
        print("취소했습니다. 저장된 자료는 그대로입니다.")
        return
    stop = globals().get("stop_preview")
    if stop is not None:
        stop()
    for name in sorted(owned_schemas):
        drop_lab_schema(name)
        print("실습 스키마 정리:", name)

# 기본값에서는 실행되지 않습니다. 실습 종료 시 아래 호출을 별도 셀에 복사해 실행하세요.
# cleanup_lab("DELETE LAB")
'''


def set_source(cell, code):
    cell["source"] = dedent(code).strip().splitlines(keepends=True)
    if cell["cell_type"] == "code":
        cell.update(execution_count=None, outputs=[])
        compile("".join(cell["source"]), cell["metadata"]["id"], "exec")


def new_cell(kind, anchor, source):
    cell = {"cell_type": kind, "id": anchor, "metadata": {"id": anchor}}
    set_source(cell, source)
    return cell


def build(source, output):
    notebook = json.loads(source.read_text(encoding="utf-8"))
    c = {cell["metadata"]["id"]: cell for cell in notebook["cells"]}
    app = "".join(c["shop-app"]["source"])
    app = app.replace("def make_app(path):", "def make_app(schema):")
    app = app.replace("with closing(connect(path)) as db:\n                products = db.execute(\"SELECT * FROM products ORDER BY id\").fetchall()",
                      "with transaction(schema) as cur:\n                cur.execute(\"SELECT * FROM products ORDER BY id\")\n                products = cur.fetchall()")
    app = app.replace("with closing(connect(path)) as db:\n                rows = order_history(db)",
                      "with transaction(schema) as cur:\n                rows = order_history(cur)")
    app = app.replace("place_order(path,", "place_order(schema,")
    app = app.replace("href=\"./\"", "href=\"{root}\"").replace('href="orders"', 'href="{root}orders"')
    app = app.replace("def layout(title, content):", 'def layout(title, content, root="./"):')
    app = app.replace("        if method == \"GET\" and route == \"\":", '        if method == "GET" and route == "/orders/cancel":\n            return send("303 See Other", "", (("Location", "../orders"),))\n        if method == "GET" and route == "":')
    app = app.replace('<p class="status">배송 상태 · {escape(r[\'status\'])}</p></article>', '<p class="status">배송 상태 · {escape(r[\'status\'])}</p>{cancel_form(r)}</article>')
    index = app.index("def make_app")
    app = app[:index] + 'def cancel_form(order):\n    if order["status"] != "준비 중":\n        return ""\n    return ' + repr(CANCEL_FORM) + '.format(order_id=order["id"])\n\n' + app[index:]
    app = app.replace('        return send("404 Not Found",', CANCEL_ROUTE + '        return send("404 Not Found",')
    app = app.replace('layout("취소 실패", "<p>주문번호를 확인하세요.</p>")','layout("취소 실패", "<p>주문번호를 확인하세요.</p>", "../")')
    app = app.replace('layout("취소 불가", "<p>준비 중인 주문만 취소할 수 있습니다.</p>")','layout("취소 불가", "<p>준비 중인 주문만 취소할 수 있습니다.</p>", "../")')
    assert "connect(path)" not in app and "cancel_form(r)" in app and 'route == "/orders/cancel"' in app
    contents = {
        "shop-intro": """# CD12-1 · AWS 쇼핑몰 DB와 웹앱
[쿠팡 공개 주문·배송 조회](https://news.coupang.com/archives/61370/) 흐름을 바탕으로 상품 → 주문 → 배송 조회 → 주문 취소를 실습합니다.
웹 화면은 Colab에 표시되고 데이터는 AWS RDS PostgreSQL에 저장됩니다. 0~5를 순서대로 실행하고 실습이 끝나면 6의 정리 셀을 확인하세요.""",
        "shop-db-guide": """## 1. 쇼핑몰 DB 생성
RDS에 이 런타임 전용 스키마와 표 5개를 만듭니다. 같은 런타임에서 다시 실행하면 이미 생성된 스키마를 재사용합니다. 주문항목은 주문 시 단가를 보존합니다.""",
        "shop-db": DB,
        "shop-order-guide": """## 2. 주문·취소 처리
주문은 조건부 재고 차감, 주문·주문항목·배송 생성까지 한 트랜잭션입니다. 배송 준비 중인 주문을 취소하면 재고를 되돌리고 주문·연결 내역을 삭제합니다. 실패 시 함께 롤백됩니다.""",
        "shop-order": ORDER,
        "shop-app-guide": """## 3. 웹앱 화면과 요청 연결
GET / 상품 목록, POST /orders 주문, GET /orders 주문·배송 조회, POST /orders/cancel 주문 취소. 가격은 RDS에서 읽습니다.""",
        "shop-app": app,
        "shop-check-guide": """## 4. 실행 전 확인
별도 시험 스키마에서 상품 조회, 마지막 상품 주문, 품절, 단가 보존, 주문 취소 후 삭제와 재고 복구, 재취소 차단을 검사합니다. 시험 스키마는 테스트 후 정리합니다.""",
        "shop-check": TEST,
        "shop-run-guide": """## 5. 실제 웹앱 화면 열기
아래 셀을 실행하면 상품 목록이 셀 출력에 표시됩니다. 무선 마우스를 주문하고 주문·배송에서 준비 중을 확인하세요. **주문 취소 및 삭제**를 누른 뒤 상품 목록에 재고가 돌아왔는지 확인합니다.""",
        "shop-run": RUN,
        "shop-submit": """## 제출
상품 목록 → 주문·배송 준비 중 → 품절 → 주문 취소·재고 복구를 확인하고 자동 검증 결과를 함께 제출합니다. 판매 단가가 보존되는 이유를 한 문장으로 쓰세요.""",
    }
    for anchor, content in contents.items():
        set_source(c[anchor], content)
    notebook["cells"][1:1] = [new_cell("markdown", "shop-aws-guide", AWS_GUIDE),
                              new_cell("code", "shop-aws", AWS)]
    notebook["cells"].extend((
        new_cell("markdown", "shop-clean-guide", """## 6. 실습 데이터와 AWS 자원 정리
아래 셀로 함수를 정의한 뒤 별도 셀에서 `cleanup_lab("DELETE LAB")`를 실행하면 현재 런타임에서 만든 실습 스키마만 삭제됩니다. 같은 런타임에서 진행하세요.
이 실습을 위해 따로 만든 **전용 RDS 인스턴스**가 더 필요 없으면 AWS RDS 콘솔에서 해당 인스턴스와 스냅샷 보존 여부를 확인한 뒤 삭제합니다. 공유 RDS는 계속 사용하고 실습 스키마만 정리하세요."""),
        new_cell("code", "shop-clean", CLEAN),
    ))
    output.write_text(json.dumps(notebook, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    build(args.source, args.output)
