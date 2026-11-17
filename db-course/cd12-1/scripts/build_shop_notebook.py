"""Generate the CD12-1 shop notebook using only Python's standard library."""
import argparse
import json
from pathlib import Path

DB = '''
import sqlite3, tempfile
from pathlib import Path
from contextlib import closing

lab_dir = tempfile.TemporaryDirectory(prefix="cd12-shop-")
db_path = Path(lab_dir.name) / "shop.sqlite3"

def connect(path):
    db = sqlite3.connect(path, timeout=5)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db

with closing(connect(db_path)) as db, db:
    db.executescript("""
    CREATE TABLE customers(id INTEGER PRIMARY KEY, name TEXT NOT NULL);
    CREATE TABLE products(id INTEGER PRIMARY KEY, name TEXT NOT NULL,
        price INTEGER NOT NULL CHECK(price >= 0), stock INTEGER NOT NULL CHECK(stock >= 0));
    CREATE TABLE orders(id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL REFERENCES customers(id),
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE order_items(order_id INTEGER NOT NULL REFERENCES orders(id),
        product_id INTEGER NOT NULL REFERENCES products(id), quantity INTEGER NOT NULL CHECK(quantity > 0),
        unit_price INTEGER NOT NULL CHECK(unit_price >= 0), PRIMARY KEY(order_id, product_id));
    CREATE TABLE shipments(order_id INTEGER PRIMARY KEY REFERENCES orders(id),
        status TEXT NOT NULL CHECK(status IN ('준비 중', '배송 중', '배송 완료')));
    INSERT INTO customers VALUES (1, '실습 고객');
    INSERT INTO products VALUES (101, '무선 마우스', 19900, 1),
        (102, '접이식 키보드', 32900, 5), (103, '노트북 거치대', 24900, 3);
    """)
    for row in db.execute("SELECT * FROM products ORDER BY id"):
        print(tuple(row))
'''

ORDERS = '''
class SoldOut(ValueError):
    pass

def place_order(path, product_id, quantity):
    if quantity < 1:
        raise ValueError("수량은 1 이상이어야 합니다.")
    with closing(connect(path)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        product = db.execute("SELECT price FROM products WHERE id = ?", (product_id,)).fetchone()
        if product is None:
            raise ValueError("상품을 찾을 수 없습니다.")
        changed = db.execute(
            "UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?",
            (quantity, product_id, quantity),
        ).rowcount
        if changed != 1:
            raise SoldOut("재고가 부족합니다.")
        order_id = db.execute("INSERT INTO orders(customer_id) VALUES (1)").lastrowid
        db.execute("INSERT INTO order_items VALUES (?, ?, ?, ?)",
                   (order_id, product_id, quantity, product["price"]))
        db.execute("INSERT INTO shipments VALUES (?, '준비 중')", (order_id,))
        return order_id

def order_history(db):
    return db.execute("""
       SELECT o.id, p.name, i.quantity, i.unit_price, i.quantity * i.unit_price AS total,
              s.status
       FROM orders o JOIN order_items i ON i.order_id = o.id
       JOIN products p ON p.id = i.product_id JOIN shipments s ON s.order_id = o.id
       WHERE o.customer_id = 1 ORDER BY o.id DESC
    """).fetchall()
'''

APP = '''
from html import escape
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server
from threading import Thread

STYLE = """
:root{font-family:system-ui,sans-serif;background:#f1f5f9;color:#182945}
body{margin:0} main{margin:auto;max-width:940px;padding:36px 20px}
header{display:flex;align-items:center;justify-content:space-between;gap:12px}
nav{display:flex;gap:14px} a{color:#174aaa}
h1{font-size:2rem;margin:10px 0 6px} h2{font-size:1.2rem;margin:0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px}
article{background:white;border:1px solid #dbe4ef;border-radius:14px;padding:17px;margin:12px 0}
.price{font-weight:750;font-size:1.25rem} input{width:55px;padding:6px}
button{background:#174aaa;color:white;border:0;border-radius:7px;padding:8px 12px;font:inherit;cursor:pointer}
button:disabled{background:#687789;cursor:default} .status{color:#26564d;font-weight:700}
"""

def layout(title, content):
    return f"""<!doctype html><html lang="ko"><meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1"><title>{title}</title>
    <style>{STYLE}</style><body><main><header><strong>미니 쇼핑몰</strong>
    <nav><a href="./">상품</a><a href="orders">주문·배송</a></nav></header>
    <h1>{title}</h1><p>클라우드 데이터베이스 · 수업용 예시</p>{content}</main></body></html>"""

def make_app(path):
    def app(environ, start_response):
        def send(status, html, headers=()):
            data = html.encode("utf-8")
            start_response(status, [("Content-Type", "text/html; charset=utf-8"),
                                    ("Content-Length", str(len(data))), *headers])
            return [data]

        route = environ.get("PATH_INFO", "/").rstrip("/")
        method = environ["REQUEST_METHOD"]
        if method == "GET" and route == "":
            with closing(connect(path)) as db:
                products = db.execute("SELECT * FROM products ORDER BY id").fetchall()
            cards = []
            for p in products:
                button = '<button disabled>품절</button>' if not p["stock"] else '<button>주문하기</button>'
                cards.append(f"""<article><h2>{escape(p['name'])}</h2>
                    <p class="price">{p['price']:,}원</p><p>판매 가능 {p['stock']}개</p>
                    <form method="post" action="orders"><input type="hidden" name="product" value="{p['id']}">
                    <label>수량 <input name="quantity" type="number" min="1" value="1" required></label>
                    {button}</form></article>""")
            return send("200 OK", layout("상품 목록", '<div class="grid">' + "".join(cards) + "</div>"))
        if method == "GET" and route == "/orders":
            with closing(connect(path)) as db:
                rows = order_history(db)
            cards = [
                f"""<article><h2>주문 #{r['id']} · {escape(r['name'])}</h2>
                <p>{r['quantity']}개 × {r['unit_price']:,}원 · 합계 {r['total']:,}원</p>
                <p class="status">배송 상태 · {escape(r['status'])}</p></article>"""
                for r in rows
            ]
            return send("200 OK", layout("주문·배송 조회", "".join(cards) or "<p>주문이 없습니다.</p>"))
        if method == "POST" and route == "/orders":
            try:
                size = int(environ.get("CONTENT_LENGTH") or 0)
                if not 0 < size <= 1024:
                    raise ValueError()
                fields = parse_qs(environ["wsgi.input"].read(size).decode("utf-8"), max_num_fields=4)
                place_order(path, int(fields["product"][0]), int(fields["quantity"][0]))
            except SoldOut as exc:
                return send("409 Conflict", layout("주문 실패", f"<p>{escape(str(exc))}</p>"))
            except (KeyError, ValueError):
                return send("400 Bad Request", layout("주문 실패", "<p>상품과 수량을 확인하세요.</p>"))
            return send("303 See Other", "", (("Location", "orders"),))
        return send("404 Not Found", layout("페이지를 찾을 수 없습니다", ""))
    return app
'''

TEST = '''
from urllib.request import urlopen, Request
from urllib.error import HTTPError

with tempfile.TemporaryDirectory(prefix="cd12-check-") as test_dir:
    test_path = Path(test_dir) / "test.sqlite3"
    with closing(connect(db_path)) as src, closing(connect(test_path)) as dst:
        src.backup(dst)
    # Use a fresh fixture even if the interactive preview has already been used.
    with closing(connect(test_path)) as db, db:
        db.executescript("DELETE FROM shipments; DELETE FROM order_items; DELETE FROM orders;"
                         "UPDATE products SET stock=1, price=19900 WHERE id=101;")
    with make_server("127.0.0.1", 0, make_app(test_path)) as test_server:
        thread = Thread(target=test_server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{test_server.server_port}/"
        try:
            with urlopen(base, timeout=5) as response:
                assert "무선 마우스" in response.read().decode()
            request = Request(base + "orders", data=b"product=101&quantity=1")
            with urlopen(request, timeout=5) as response:
                assert "준비 중" in response.read().decode()
            try:
                urlopen(request, timeout=5)
            except HTTPError as error:
                assert error.code == 409
                error.close()
            else:
                raise AssertionError("두 번째 주문이 품절이어야 합니다.")
            with closing(connect(test_path)) as db, db:
                db.execute("UPDATE products SET price=21900 WHERE id=101")
                assert db.execute("SELECT stock FROM products WHERE id=101").fetchone()[0] == 0
                rows = order_history(db)
                assert len(rows) == 1 and rows[0]["unit_price"] == 19900
                try:
                    db.execute("INSERT INTO order_items VALUES (999, 101, 1, 19900)")
                except sqlite3.IntegrityError:
                    pass
                else:
                    raise AssertionError("존재하지 않는 주문을 참조할 수 없어야 합니다.")
        finally:
            test_server.shutdown()
            thread.join(timeout=5)
print("통과 · 상품 조회 / 주문·배송 조회 / 품절 409 / 주문 1건 / 단가 보존 / 외래키")
'''

RUN = '''
from google.colab import output

if "preview_server" in globals():
    preview_server.shutdown()
    preview_server.server_close()
preview_server = make_server("127.0.0.1", 0, make_app(db_path))
Thread(target=preview_server.serve_forever, daemon=True).start()
output.serve_kernel_port_as_iframe(preview_server.server_port, height=640)
'''


def cell(kind, id_, content):
    value = {"cell_type": kind, "id": id_, "metadata": {"id": id_},
             "source": content.strip().splitlines(keepends=True)}
    if kind == "code":
        value.update(execution_count=None, outputs=[])
    return value


def build(path):
    cells = [
        cell("markdown", "shop-intro", """# CD12-1 · 미니 쇼핑몰 DB와 웹앱
쿠팡의 공개 고객 경험인 상품 선택 → 주문 → 주문·배송조회 흐름을 수업용 쇼핑몰로 실습합니다.
[쿠팡 뉴스룸 · 배송조회 안내](https://news.coupang.com/archives/61370/)
수업용 데이터와 독립 구현을 사용합니다. 결제와 로그인은 범위에서 제외합니다. 코드 셀을 위에서부터 실행하세요."""),
        cell("markdown", "shop-db-guide", """## 1. 쇼핑몰 DB 생성
고객 → 주문 → 주문항목 ← 상품, 주문 → 배송으로 키를 연결합니다. 주문항목에는 판매 당시 단가를 보존합니다. 이 셀을 다시 실행하면 새 임시 DB로 실습을 시작합니다."""),
        cell("code", "shop-db", DB),
        cell("markdown", "shop-order-guide", """## 2. 주문 처리와 조회
재고가 충분할 때만 차감합니다. 주문, 주문항목, 배송 준비 상태는 같은 트랜잭션에 기록합니다. 재고가 부족하면 주문을 만들기 전에 종료합니다. 예외가 발생하면 변경이 롤백됩니다."""),
        cell("code", "shop-order", ORDERS),
        cell("markdown", "shop-app-guide", """## 3. 웹앱 화면과 요청 연결
상품 목록은 GET /, 주문은 POST /orders, 주문·배송 조회는 GET /orders입니다. 폼에는 상품 ID와 수량을 넣고, 가격은 서버가 DB에서 읽습니다."""),
        cell("code", "shop-app", APP),
        cell("markdown", "shop-check-guide", """## 4. 실행 전 확인
격리한 복제 DB에서 실제 HTTP 요청을 실행합니다. 마우스 1개를 주문한 뒤 같은 요청을 다시 보내면 품절 응답(409)이어야 합니다."""),
        cell("code", "shop-check", TEST),
        cell("markdown", "shop-run-guide", """## 5. 화면에서 주문하기
다음 셀의 미리보기에서 마우스를 주문하고 **주문·배송**에서 배송 준비 중을 확인하세요. 상품 화면으로 돌아가면 품절입니다. 다시 시작하려면 DB 생성 셀을 실행한 뒤 미리보기를 다시 실행하세요."""),
        cell("code", "shop-run", RUN),
        cell("markdown", "shop-submit", """## 제출
상품 화면에서 재고 1개, 주문·배송 화면에서 판매 단가와 준비 중 상태, 상품 화면에서 품절을 순서대로 확인합니다. 자동 검증 셀의 통과 결과와 함께 제출하세요. 주문항목에 가격을 복사하는 이유를 한 문장으로 적으세요.
후속 실습에서는 동일한 키 관계를 PostgreSQL로 옮기고, 두 세션의 재고 갱신 동작을 비교합니다."""),
    ]
    notebook = {"cells": cells, "metadata": {"colab": {"provenance": []},
                 "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                 "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
    path.write_text(json.dumps(notebook, ensure_ascii=False, indent=2) + "\n", encoding="utf8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    build(parser.parse_args().output)
