# @title 과제 ③ · 여성 액세서리몰 웹앱 만들기 (교안 57쪽)
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from urllib.parse import parse_qs, urlsplit
from google.colab import output

if not callable(globals().get("transaction")) or globals().get("logical_schema") != "shop":
    raise RuntimeError("먼저 1번과 2번 셀을 실행하고 7번에서 물리 설계를 적용하세요.")

# TODO 1: category와 keyword 필터를 파라미터로 적용하세요.
def product_query(category, keyword=""):
    return """
        SELECT product_name, category, price, stock
        FROM products ORDER BY product_id LIMIT 30
    """, ()

# TODO 2: orders와 order_details를 order_id로, products를 product_id로 조인하세요.
# customer_id를 %s로 필터링하고, 최신 주문부터 정렬하세요. 현재 판매가 대신 unit_price를 표시하세요.
# 표시 순서: 주문번호, 주문일, 상태, 상품명, 수량, 주문 당시 단가.
def order_query(customer_id):
    return None

def read_rows(query, *, plan=False):
    statement, params = query
    with transaction("shop") as cur:
        cur.execute("SET TRANSACTION READ ONLY")
        if plan:
            cur.execute("EXPLAIN (ANALYZE, BUFFERS) " + statement, params)
        else:
            cur.execute(statement, params)
        return [tuple(row.values()) for row in cur.fetchall()]

def table(headers, rows):
    if not rows:
        return "<p>조회 결과가 없습니다.</p>"
    title = "".join(f"<th>{escape(str(value))}</th>" for value in headers)
    body = "".join("<tr>" + "".join(f"<td>{escape(str(value))}</td>" for value in row) + "</tr>" for row in rows)
    return f"<table><thead><tr>{title}</tr></thead><tbody>{body}</tbody></table>"

HERO_IMAGE = ""

def product_cards(rows):
    if not rows:
        return "<p>조건에 맞는 상품이 없습니다.</p>"
    cards = []
    for name, category, price, stock in rows:
        color = {"귀걸이": "pearl", "목걸이": "silver", "헤어핀": "rose"}.get(category, "rose")
        indication = f"재고 {int(stock)}개" if stock else "품절"
        cards.append(f"""<article class="card">
<div class="tile {color}">{escape(str(category))}</div>
<h3>{escape(str(name))}</h3><strong>{int(price):,}원</strong><small>{indication}</small>
</article>""")
    return '<div class="grid">' + "".join(cards) + '</div>'

def render_shop(category, customer_id, keyword=""):
    products = product_cards(read_rows(product_query(category, keyword)))
    orders = "<p>TODO 2를 완성하면 주문 내역이 표시됩니다.</p>"
    query = order_query(customer_id)
    if query is not None:
        orders = table(("주문번호", "주문일", "상태", "상품명", "수량", "주문 당시 단가"), read_rows(query))
    categories = ("전체", "귀걸이", "목걸이", "헤어핀", "팔찌", "반지", "브로치")
    chips = "".join(
        f'<button type="submit" name="category" value="{label}" class="chip{" active" if label == category else ""}">{label}</button>'
        for label in categories
    )
    hero_style = f' style="--hero:url({HERO_IMAGE})"' if HERO_IMAGE else ""
    return f"""<!doctype html><html lang="ko"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>로지아 액세서리</title>
<style>
* {{ box-sizing:border-box; }}
body {{ font: 15px system-ui,sans-serif; background:#fbf8f6; color:#32232a; margin:0; }}
header {{ border-bottom:1px solid #e8dde0; background:white; }}
.bar {{ display:flex; justify-content:space-between; align-items:center; max-width:1040px; margin:auto; padding:15px 22px; }}
.logo {{ letter-spacing:.25em; font:600 24px Georgia,serif; color:#662e44; }}
.bar a {{ color:#662e44; text-decoration:none; }}
main {{ max-width:1040px; margin:auto; padding:22px; }}
.hero {{ background-image:linear-gradient(90deg,#f1e1e7 5%,#f1e1e7d9 32%,#e4cbd528 100%), var(--hero, linear-gradient(135deg,#f1e1e7,#c193aa)); background-size:cover; background-position:center; border-radius:14px; padding:34px 32px; }}
h1 {{ color:#512539; font-size:clamp(25px,5vw,43px); margin:6px 0 12px; }}
.eyebrow {{ letter-spacing:.18em; font:small-caps 14px Georgia,serif; color:#662e44; }}
section {{ margin:26px 0; overflow-x:auto; }}
form {{ display:flex; flex-wrap:wrap; align-items:center; gap:8px; margin-top:16px; }}
input,button {{ padding:9px 13px; font:inherit; border:1px solid #d8c4ca; border-radius:20px; background:#fff; color:#32232a; }}
button {{ cursor:pointer; }}
button.primary,.chip.active {{ background:#662e44; border-color:#662e44; color:white; }}
nav {{ display:flex; flex-wrap:wrap; gap:8px; margin:12px 0 18px; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; }}
.card {{ background:white; border:1px solid #ecdee3; border-radius:12px; overflow:hidden; padding-bottom:12px; }}
.tile {{ min-height:84px; display:grid; place-items:center; color:#542d3c; background:linear-gradient(145deg,#f7efe8,#ebd5d8); }}
.tile.silver {{ background:linear-gradient(145deg,#f2f2f4,#d9dce3); }}
.tile.rose {{ background:linear-gradient(145deg,#f7e8ef,#edd1df); }}
.card h3,.card strong,.card small {{ display:block; margin:9px 12px 0; }}
.card small {{ color:#694f5b; }}
table {{ border-collapse:collapse; min-width:565px; width:100%; background:white; }}
td,th {{ padding:9px; border-bottom:1px solid #e9e0e3; text-align:left; }}
</style>
<header><div class="bar"><span class="logo">ROSIA</span><a href="#orders">주문 조회</a></div></header>
<main><div class="hero"{hero_style}><span class="eyebrow">Everyday Accessories</span>
<h1>로지아 액세서리</h1><p>진주 귀걸이부터 리본 헤어핀까지</p></div>
<form method="get" id="catalog">
  <label>상품명 <input name="keyword" value="{escape(keyword, quote=True)}" maxlength="40" placeholder="상품명을 입력하세요"></label>
  <input type="hidden" name="customer" value="{customer_id}">
  <button type="submit" class="primary" name="category" value="{escape(category, quote=True)}">검색</button>
  <nav aria-label="카테고리">{chips}</nav>
</form>
<section><h2>상품·재고</h2>{products}</section>
<section id="orders"><h2>주문 내역</h2>
<form method="get" action="#orders">
  <input type="hidden" name="category" value="{escape(category, quote=True)}">
  <input type="hidden" name="keyword" value="{escape(keyword, quote=True)}">
  <label>실습 고객 번호 <input name="customer" value="{customer_id}" type="number" min="1" max="2147483647"></label>
  <button class="primary">조회</button>
</form>{orders}</section></main></html>"""

class ShopPreview(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_GET(self):
        args = parse_qs(urlsplit(self.path).query)
        try:
            category = args.get("category", ["전체"])[0][:40]
            customer = int(args.get("customer", ["1"])[0])
            if not 1 <= customer <= 2147483647:
                raise ValueError
        except ValueError:
            self.send_error(400, "Check customer number")
            return
        try:
            keyword = args.get("keyword", [""])[0][:40]
            body = render_shop(category, customer, keyword).encode("utf-8")
        except Exception:
            self.send_error(500, "Check the SQL in Colab")
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

old_stop = globals().get("stop_preview")
if callable(old_stop):
    old_stop()
preview_server = ThreadingHTTPServer(("127.0.0.1", 0), ShopPreview)
Thread(target=preview_server.serve_forever, daemon=True).start()

def stop_preview(server=preview_server):
    server.shutdown()
    server.server_close()

output.serve_kernel_port_as_iframe(preview_server.server_port, height=680)
