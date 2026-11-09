"""CD11-3 설계실습 Colab 노트북 생성 (11-2 노트북과 같은 SQLite + HTML 표 방식): python colab_nb.py <출력.ipynb>"""
import json, sys

SETUP = r'''import sqlite3
from html import escape
from IPython.display import HTML, display

def show_table(title, headers, rows, highlight=lambda row: False):
    header = ''.join(f'<th style="padding:7px 12px;background:#102950;color:#fff">{escape(str(v))}</th>' for v in headers)
    body = []
    for row in rows:
        color = '#fff0c2' if highlight(row) else '#f4f8ff'
        cells = ''.join(f'<td style="padding:7px 12px;border-top:1px solid #d7e0ee">{escape(f"{v:,}" if isinstance(v, int) and abs(v) >= 1000 else str(v))}</td>' for v in row)
        body.append(f'<tr style="background:{color}">{cells}</tr>')
    display(HTML(f'<p style="font-weight:700;color:#102950;margin:14px 0 6px">{escape(title)}</p>'
                 f'<table style="border-collapse:collapse;font-size:14px">{header}{"".join(body)}</table>'))

db = sqlite3.connect(':memory:')
db.execute('PRAGMA foreign_keys = ON')
db.executescript("""
CREATE TABLE stores (store_id TEXT PRIMARY KEY, store_name TEXT NOT NULL, biz_no TEXT, phone TEXT, owner TEXT, address TEXT);
CREATE TABLE orders (order_id TEXT PRIMARY KEY, store_id TEXT NOT NULL REFERENCES stores(store_id),
                     wait_no INTEGER, ordered_at TEXT, pos_no TEXT);
CREATE TABLE menu (menu_id TEXT PRIMARY KEY, menu_name TEXT NOT NULL, temp TEXT, unit_price INTEGER NOT NULL);
CREATE TABLE order_items (order_id TEXT REFERENCES orders(order_id), menu_id TEXT REFERENCES menu(menu_id),
                          qty INTEGER NOT NULL, discount INTEGER DEFAULT 0, takeout TEXT,
                          PRIMARY KEY (order_id, menu_id));
CREATE TABLE payments (payment_id TEXT PRIMARY KEY, order_id TEXT NOT NULL REFERENCES orders(order_id),
                       method TEXT, card_company TEXT, approval_no TEXT, amount INTEGER NOT NULL);
""")
# 영수증 1장의 값을 각 테이블에 한 번씩만 저장 (BILL 번호는 가려져 있어 B0001로 가정)
db.execute("INSERT INTO stores VALUES ('S01','강남중앙점(메가MGC커피)','105-87-51367','02-533-0656','김대영','서울 서초구 서초대로77길 35, 1층 102호')")
db.execute("INSERT INTO orders VALUES ('B0001','S01',241,'2025-03-19 08:54','02')")
db.executemany("INSERT INTO menu VALUES (?,?,?,?)", [('M01','아메리카노','HOT',1500), ('M02','아메리카노','ICE',2000)])
db.executemany("INSERT INTO order_items VALUES (?,?,?,?,?)", [('B0001','M01',1,0,'포장'), ('B0001','M02',2,0,'포장')])
db.execute("INSERT INTO payments VALUES ('P01','B0001','카드','카카오뱅크체크','21091497',5500)")
db.commit()

for t, h in [('stores', ('매장ID (PK)', '매장명', '사업자번호', '전화', '대표자', '주소')),
             ('orders', ('주문ID (PK)', '매장ID (FK)', '대기번호', '주문일시', 'POS')),
             ('menu', ('메뉴ID (PK)', '메뉴명', '온도', '단가')),
             ('order_items', ('주문ID (PK/FK)', '메뉴ID (PK/FK)', '수량', '할인', '포장')),
             ('payments', ('결제ID (PK)', '주문ID (FK)', '수단', '카드사', '승인번호', '금액'))]:
    show_table(f'{t} · {db.execute(f"SELECT count(*) FROM {t}").fetchone()[0]}행', h, db.execute(f'SELECT * FROM {t}').fetchall())'''

RECEIPT = r'''def print_receipt(order_id):
    head = db.execute("""SELECT s.store_name, o.wait_no, o.ordered_at FROM orders o
                         JOIN stores s ON s.store_id = o.store_id WHERE o.order_id = ?""", (order_id,)).fetchone()
    lines = db.execute("""SELECT '[' || i.takeout || '](' || m.temp || ')' || m.menu_name, m.unit_price, i.qty,
                                 m.unit_price * i.qty - i.discount
                          FROM order_items i JOIN menu m ON m.menu_id = i.menu_id
                          WHERE i.order_id = ? ORDER BY m.menu_id""", (order_id,)).fetchall()
    total = sum(r[3] for r in lines)
    vat = total // 11                      # 부가세 포함 금액 기준: 부가세 = 합계 ÷ 11
    paid = db.execute("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE order_id = ?", (order_id,)).fetchone()[0]
    print(f"{head[0]} · 대기번호 {head[1]} · {head[2]}")
    show_table('JOIN으로 다시 만든 영수증 상품 줄', ('상품명', '단가', '수량', '금액'), lines)
    show_table('계산한 금액 (저장하지 않고 상품 줄에서 계산)', ('과세물품가액', '부가세', '합계', '받은 금액(결제 표)', '일치'),
               [(total - vat, vat, total, paid, '✅' if paid == total else '❌')])

print_receipt('B0001')'''

UPDATE = r'''# 메뉴 표에서 ICE 아메리카노 단가를 한 번만 바꾸면, 이 메뉴를 쓴 모든 주문 계산에 반영됩니다
db.execute("SAVEPOINT demo")
db.execute("UPDATE menu SET unit_price = 2200 WHERE menu_id = 'M02'")
print("단가 2,000 → 2,200으로 바꾼 뒤 다시 계산")
print_receipt('B0001')
db.execute("ROLLBACK TO demo"); db.execute("RELEASE demo")
print("시연이 끝나 원래 단가(2,000)로 되돌렸습니다.")
# 주의: 실제 영수증은 '판매 당시 단가'를 보존해야 하므로, 현업에서는 order_items에 판매 단가를 함께 저장합니다.'''

FORM = r'''db.executescript("""
CREATE TABLE students (student_id TEXT PRIMARY KEY, name_ko TEXT NOT NULL, name_en TEXT, phone TEXT,
                       birth TEXT, email TEXT, address TEXT, school_year TEXT, school_status TEXT, major TEXT);
CREATE TABLE planners (planner_id TEXT PRIMARY KEY, planner_name TEXT NOT NULL);
CREATE TABLE institutions (inst_id TEXT PRIMARY KEY, inst_name TEXT NOT NULL, country TEXT);
CREATE TABLE fields (field_code TEXT PRIMARY KEY, field_name TEXT NOT NULL);
CREATE TABLE consultations (consult_id TEXT PRIMARY KEY,
                            student_id TEXT NOT NULL REFERENCES students(student_id),
                            planner_id TEXT REFERENCES planners(planner_id),
                            inst_id TEXT REFERENCES institutions(inst_id),
                            consult_date TEXT, hope_major TEXT, visa_type TEXT, depart_ym TEXT, hope_region TEXT,
                            question TEXT, memo TEXT);
CREATE TABLE consult_fields (consult_id TEXT REFERENCES consultations(consult_id),
                             field_code TEXT REFERENCES fields(field_code), PRIMARY KEY (consult_id, field_code));
CREATE TABLE progress (consult_id TEXT REFERENCES consultations(consult_id), step TEXT, done_date TEXT,
                       PRIMARY KEY (consult_id, step));
""")
# 예시 데이터 (가상의 학생 1명, 상담 1건)
db.execute("INSERT INTO students VALUES ('ST01','김하늘','Kim Haneul','010-0000-0000','2005-04-02','sky@example.com','서울','3학년','재학','경영')")
db.execute("INSERT INTO planners VALUES ('PL01','박상담')")
db.execute("INSERT INTO institutions VALUES ('IN01','시드니 어학원','호주')")
db.executemany("INSERT INTO fields VALUES (?,?)", [('F1','어학연수'),('F2','TAFE/칼리지'),('F3','대학(학사)'),('F4','대학(석사)'),('F5','조기유학'),('F6','영주권'),('F7','기타')])
db.execute("INSERT INTO consultations VALUES ('C001','ST01','PL01','IN01','2025-03-20','경영','학생','2025-09','시드니','장학금이 있나요?','어학 6개월 후 학사 진학 희망')")
db.executemany("INSERT INTO consult_fields VALUES (?,?)", [('C001','F1'), ('C001','F3')])     # 체크박스 2개 선택
db.executemany("INSERT INTO progress VALUES (?,?,?)", [('C001','초기상담','2025-03-20'), ('C001','학교신청','2025-03-28')])

row = db.execute("""SELECT s.name_ko, c.consult_date, p.planner_name, i.inst_name, c.visa_type, c.depart_ym,
                           (SELECT group_concat(f.field_name, ', ') FROM consult_fields cf
                              JOIN fields f ON f.field_code = cf.field_code WHERE cf.consult_id = c.consult_id)
                    FROM consultations c JOIN students s ON s.student_id = c.student_id
                    JOIN planners p ON p.planner_id = c.planner_id JOIN institutions i ON i.inst_id = c.inst_id""").fetchall()
show_table('상담 카드 다시 보기 (JOIN)', ('학생', '상담일', '플래너', '교육기관', '비자', '출국', '유학분야(N:M)'), row)
show_table('진행 이력 (단계마다 한 행)', ('상담ID', '단계', '처리일'), db.execute('SELECT * FROM progress').fetchall())'''

INS1 = '''> **결과 읽는 법**
> - 영수증 1장이 **매장 1행 · 주문 1행 · 메뉴 2행 · 주문상세 2행 · 결제 1행**으로 나뉩니다.
> - 주문상세의 기본키는 (주문ID, 메뉴ID) 두 열을 합친 **복합키**입니다. 같은 주문에 같은 메뉴는 한 줄로 기록합니다.'''
INS2 = '''> **결과 읽는 법**
> - 상품 줄: (HOT)아메리카노 1,500 × 1 = 1,500 · (ICE)아메리카노 2,000 × 2 = 4,000
> - 합계 5,500 = 과세물품가액 5,000 + 부가세 500 → **영수증과 같습니다.** 합계·부가세는 저장하지 않고 상품 줄에서 계산했습니다.
> - 결제 표의 5,500과 합계가 같아 '받을 금액 = 받은 금액'이 확인됩니다.'''
INS3 = '''> **결과 읽는 법**
> - 메뉴 표의 단가를 **한 번만** 바꿨는데 합계가 5,500 → 5,900으로 다시 계산됩니다. 이것이 정규화의 장점입니다.
> - 그런데 이미 발행한 영수증 금액이 바뀌면 안 됩니다. 그래서 현업에서는 주문상세에 **판매 당시 단가**를 함께 저장합니다(설계 판단).'''
INS4 = '''> **결과 읽는 법**
> - 체크박스로 2개를 고른 유학분야는 `consult_fields`에 **2행**으로 저장됩니다 (상담 N:M 유학분야).
> - 업무 진행 단계는 열 8개가 아니라 `progress`에 **단계마다 한 행**으로 쌓입니다. 단계가 늘어도 표 구조를 바꿀 필요가 없습니다.'''


def md(t):
    return {"cell_type": "markdown", "metadata": {}, "source": t}


def code(t):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": t}


import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from missions import CHECKS, CELLS

def mission(k):
    head = md(CELLS[k][0]); head['metadata'] = {'id': 'mission_' + k}     # 교안 버튼 링크: #scrollTo=mission_<k>
    return [head, code(CELLS[k][1])]

cells = [
    md("# CD11-3 데이터베이스 설계실습 · 교안과 함께 실행하기\n\n"
       "교안의 각 실습 페이지에 있는 **'Colab 미션 N ▶'** 버튼과 이 노트북의 **🎯 미션 N** 셀이 짝입니다. "
       "교안에서 개념을 보고 → 여기서 따라하기 셀을 실행하고 → 미션 셀의 `____` 빈칸을 채워 실행합니다. "
       "결과가 **✅**이면 통과, **❌**이면 힌트를 보고 다시 시도하세요. **정답은 교안의 '미션 정답' 페이지**에 있습니다.\n\n"
       "| 노트북 | 교안 |\n|---|---|\n| 1. 테이블 저장 · 미션 1·2 | 실습1 ①②, 실습1 정답 (7·8·10쪽) |\n"
       "| 2. JOIN 영수증 · 미션 3 | 실습1 ③ (9쪽) |\n| 3. 단가 수정 · 미션 4 | 검증 (17쪽) |\n"
       "| 4. 상담 카드 · 미션 5 | 실습2 ①②, 실습2 정답 (13~15쪽) |\n| 과제 | 실습 마무리 (18쪽) |\n\n"
       "Colab에 내장된 SQLite를 쓰므로 **AWS 접속이나 비밀번호가 필요 없습니다.** 셀을 위에서부터 실행하세요."),
    md("## 1. 따라하기 · 영수증을 5개 테이블에 저장하기  (교안 실습1 정답 · 10쪽)\n매장·주문·메뉴·주문상세·결제 테이블을 PK·FK와 함께 만들고, 영수증의 값을 한 번씩만 넣습니다."),
    md(INS1), code(SETUP), code(CHECKS),
    *mission('m1'), *mission('m2'),
    md("## 2. 따라하기 · JOIN으로 영수증 다시 만들기  (교안 검증 · 17쪽)\n키로 표를 연결해 상품 줄을 복원하고, 합계·부가세는 저장하지 않고 계산합니다."),
    md(INS2), code(RECEIPT), *mission('m3'),
    md("## 3. 따라하기 · 메뉴 단가를 한 번 바꾸면?  (교안 실습1 ③ · 9쪽)\n정규화된 설계에서는 한 곳만 고치면 됩니다. 시연 뒤 원래 값으로 되돌립니다."),
    md(INS3), code(UPDATE), *mission('m4'),
    md("## 4. 따라하기 · 상담 카드를 테이블로  (교안 실습2 정답 · 15쪽)\n학생·상담·플래너·교육기관을 나누고, 여러 개 고르는 유학분야와 업무 진행 단계는 별도 표로 둡니다."),
    md(INS4), code(FORM), *mission('m5'),
    *mission('hw'),
]
nb = {"cells": cells, "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3"}},
      "nbformat": 4, "nbformat_minor": 5}
out = sys.argv[1] if len(sys.argv) > 1 else "CD11-3_Colab_설계실습.ipynb"
json.dump(nb, open(out, "w"), ensure_ascii=False, indent=1)
print("saved", out)
