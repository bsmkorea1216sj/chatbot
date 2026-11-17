"""CD12-1 교안 보강 (2026-11-17 진행 기록 기준)
 - 24쪽 '4.2 엔티티 간 관계 명시': 관계 표를 왼쪽으로 줄이고 오른쪽에 실습 표 5개 ERD(1:N·1:1, PK/FK) 추가, 약어 주석·노트 보강
다시 실행해도 추가 도형은 이름 접두어로 새로 만든다.
python deck_erd_runcheck.py <in.pptx> <out.pptx>"""
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

src, out = sys.argv[1:3]
prs = Presentation(src)
RGB = lambda h: RGBColor.from_string(h)
NAVY, FILL, LINE, GRAY = '1F4E79', 'EDF4FD', '5B7DB1', '5A5A5A'
TAG = 'cd121_erd'


def txt(sl):
    return ' '.join(sh.text_frame.text for sh in sl.shapes if sh.has_text_frame)


s24 = next(sl for sl in prs.slides if '4.2. 엔티티 간 관계 명시' in txt(sl))

# ── 24쪽
for sh in list(s24.shapes):
    if sh.name.startswith(TAG):
        sh._element.getparent().remove(sh._element)
tbl_sh = next(sh for sh in s24.shapes if sh.has_table)
t = tbl_sh.table
t.columns[0].width, t.columns[1].width = Inches(1.45), Inches(5.15)
tbl_sh.left, tbl_sh.top = Inches(0.98), Inches(2.35)
for row in t.rows:
    row.height = Inches(0.42)
    for c in row.cells:
        c.margin_top = c.margin_bottom = Inches(0.03)
        for p in c.text_frame.paragraphs:
            for r in p.runs:
                r.font.size = Pt(12.5)


def named(sh, n):
    sh.name = f'{TAG}_{n}'
    return sh


def tb(n, x, y, w, h, text, size=10, color=GRAY, bold=False, align=PP_ALIGN.LEFT):
    b = named(s24.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)), n)
    tf = b.text_frame; tf.word_wrap = True
    for m in ('margin_left', 'margin_right', 'margin_top', 'margin_bottom'):
        setattr(tf, m, Inches(0.02))
    p = tf.paragraphs[0]; p.alignment = align
    r = p.add_run(); r.text = text; r.font.size = Pt(size); r.font.bold = bold; r.font.color.rgb = RGB(color); r.font.name = 'Malgun Gothic'
    return b


def entity(key, x, y, name, lines, w=1.38):
    h = named(s24.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(0.3)), key + '_h')
    h.fill.solid(); h.fill.fore_color.rgb = RGB(NAVY); h.line.color.rgb = RGB(NAVY); h.shadow.inherit = False
    tf = h.text_frame; tf.margin_top = tf.margin_bottom = Inches(0); tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = name; r.font.size = Pt(11); r.font.bold = True; r.font.color.rgb = RGB('FFFFFF'); r.font.name = 'Consolas'
    bh = 0.2 * len(lines) + 0.1
    b = named(s24.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y + 0.3), Inches(w), Inches(bh)), key + '_b')
    b.fill.solid(); b.fill.fore_color.rgb = RGB(FILL); b.line.color.rgb = RGB(NAVY); b.shadow.inherit = False
    tf = b.text_frame; tf.margin_left = Inches(0.06); tf.margin_top = Inches(0.04); tf.margin_bottom = Inches(0.02); tf.vertical_anchor = MSO_ANCHOR.TOP
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        r = p.add_run(); r.text = ln; r.font.size = Pt(9.5); r.font.color.rgb = RGB('262626'); r.font.name = 'Malgun Gothic'
        r.font.bold = ln.startswith('PK')
    return y + 0.3 + bh


def line(n, x1, y1, x2, y2):
    c = named(s24.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2)), n)
    c.line.color.rgb = RGB(LINE); c.line.width = Pt(1.5)


tb('title', 7.95, 2.18, 4.8, 0.3, '실습 표 5개 ERD · Colab 2. 표 만들기 셀이 이대로 생성', size=11, color=NAVY, bold=True)
X1, X2, X3, W = 7.95, 9.72, 11.49, 1.38
Y1, Y2 = 2.6, 4.3
entity('cust', X1, Y1, 'customers', ['PK id', 'name'])
entity('ord', X2, Y1, 'orders', ['PK id', 'FK customer_id', 'created_at'])
entity('ship', X3, Y1, 'shipments', ['PK·FK order_id', 'status'])
entity('prod', X1, Y2, 'products', ['PK id', 'price, stock'])
entity('item', X2, Y2, 'order_items', ['PK·FK order_id', 'PK·FK product_id', 'quantity, unit_price'])
ym = Y1 + 0.15
line('l_co', X1 + W, ym, X2, ym); tb('l_co1', X1 + W + 0.02, ym - 0.24, 0.2, 0.2, '1', 9.5, NAVY, True); tb('l_coN', X2 - 0.18, ym - 0.24, 0.2, 0.2, 'N', 9.5, NAVY, True)
line('l_os', X2 + W, ym, X3, ym); tb('l_os1', X2 + W + 0.02, ym - 0.24, 0.2, 0.2, '1', 9.5, NAVY, True); tb('l_os2', X3 - 0.18, ym - 0.24, 0.2, 0.2, '1', 9.5, NAVY, True)
xm = X2 + W / 2
line('l_oi', xm, Y1 + 1.0, xm, Y2); tb('l_oi1', xm + 0.05, Y1 + 1.0, 0.2, 0.2, '1', 9.5, NAVY, True); tb('l_oiN', xm + 0.05, Y2 - 0.22, 0.2, 0.2, 'N', 9.5, NAVY, True)
yp = Y2 + 0.15
line('l_pi', X1 + W, yp, X2, yp); tb('l_pi1', X1 + W + 0.02, yp - 0.24, 0.2, 0.2, '1', 9.5, NAVY, True); tb('l_piN', X2 - 0.18, yp - 0.24, 0.2, 0.2, 'N', 9.5, NAVY, True)
tb('cap', X3 - 0.05, Y2 + 0.05, 1.5, 1.0, '주문–상품 N:M은 order_items가 연결 (복합 PK)', size=9.5, color=GRAY)
tb('foot', 0.98, 6.1, 11.5, 0.3, '※ PK: Primary Key (기본키) · FK: Foreign Key (외래키) · 1:N 일대다 · 1:1 일대일 · N:M 다대다 · ERD: Entity-Relationship Diagram (개체-관계 다이어그램)',
   size=9.5, color='3A445C')

n24 = s24.notes_slide.notes_text_frame
if '【ERD】' not in n24.text:
    n24.add_paragraph().text = ('【ERD】 오른쪽 그림은 Colab 2. 표 만들기 셀이 만드는 표 5개다(⑤ 출력의 관계(FK) 4줄과 같다). customers 1:N orders, orders 1:1 shipments(주문번호가 기본키이자 외래키), '
                                'orders 1:N order_items N:1 products. 주문과 상품의 다대다 관계를 order_items가 (order_id, product_id) 복합 기본키로 연결하고, '
                                'unit_price에 주문 당시 가격을 복사해 나중에 상품 가격이 바뀌어도 과거 합계가 유지된다(자동 검증의 “단가 보존”).')

prs.save(out)
print('ok')
