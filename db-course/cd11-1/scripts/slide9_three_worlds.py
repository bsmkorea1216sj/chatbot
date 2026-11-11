"""11-1 보강본 9쪽(본문 사례 연결 1 · 데이터의 세 세계) 보강: 원본 템플릿 제목 자리 사용, 6쪽과 같은 3단 카드 + 아이콘,
현실(주문·결제 사건) → 개념(Palantir Ontology 객체·링크·액션) → 컴퓨터(PostgreSQL 테이블·제약조건) 예시, 약어 주석·노트.
python slide9_three_worlds.py <in.pptx> <out.pptx> <icon_dir: real.png concept.png computer.png>"""
import sys, os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

src, out, icons = sys.argv[1:4]
prs = Presentation(src)
s = prs.slides[8]
RGB = lambda h: RGBColor.from_string(h)
TXT, SUB = RGB('262626'), RGB('5A5A5A')

# 1) AI가 덧붙였던 중복 장식(학습내용 태그·파란 막대·밑줄·Cloud Database)·임시 제목·빈 카드 제거 → 레이아웃 기본 장식 사용
title_txt = '본문 사례 연결 1 · 데이터의 세 세계'
point = None
for sh in list(s.shapes):
    t = sh.text_frame.text.strip() if sh.has_text_frame else ''
    if sh.is_placeholder:
        continue
    if t.startswith('강의 포인트'):
        point = sh; continue
    if t.startswith('출처'):
        continue
    sh._element.getparent().remove(sh._element)

# 2) 제목: 원본 교안과 같은 제목 자리(placeholder idx 0)
ph = {p.placeholder_format.idx: p for p in s.placeholders}
ph[0].text_frame.text = title_txt


def box(x, y, w, h, paras, size=12, color=TXT, bold=False, align=PP_ALIGN.LEFT, font='Malgun Gothic'):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    for m in ('margin_left', 'margin_right', 'margin_top', 'margin_bottom'):
        setattr(tf, m, Inches(0.02))
    for i, p in enumerate(paras):
        text, kw = (p, {}) if isinstance(p, str) else p
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = align; para.space_after = Pt(3)
        r = para.add_run(); r.text = text
        r.font.size = Pt(kw.get('size', size)); r.font.bold = kw.get('bold', bold)
        r.font.color.rgb = kw.get('color', color); r.font.name = kw.get('font', font)
    return tb


# 3) 리드 문장
box(0.75, 1.55, 11.85, 0.4, [('같은 ‘커피 주문·결제’ 업무가 세 세계에서 어떻게 바뀌는지 따라갑니다. (6쪽 반도체 사례와 같은 흐름)',
                              {'size': 15, 'bold': True, 'color': RGB('1F4E79')})])

# 4) 3단 카드 + 아이콘 + 화살표
CARDS = [
    ('real', '1  현실 세계', 'Real World', 'FCE4D6', 'C55A11', '업무에서 실제로 일어나는 사건',
     ['• 고객 김민지가 아메리카노 2잔 주문', '• 카드 결제 승인 → 다음 날 환불 요청', '• 잔액 부족으로 결제 실패 후 재시도'], False),
    ('concept', '2  개념 세계', 'Palantir Ontology', 'DEEBF7', '1F4E79', '업무 의미로 정의한 객체·링크',
     ['• Object: Customer · Order · Payment', '• Property: 주문일시 · 금액 · 상태', '• Link: Customer 1:N Order 1:N Payment',
      '• Action: 결제 승인 · 환불 처리'], False),
    ('computer', '3  컴퓨터 세계', 'PostgreSQL', 'E2F0D9', '548235', 'DBMS가 저장·검증하는 테이블',
     ['customers (customer_id PK)', 'orders (order_id PK, customer_id FK)', 'payments (payment_id PK,',
      '  order_id FK, status CHECK,', '  approval_no UNIQUE)'], True),
]
X, Y, W, H = [0.75, 4.85, 8.95], 2.1, 3.65, 3.05
SAME = ['B0001 · 08:54 · 5,500원 · 카드',
        'Order B0001 → Payment P01',
        "('P01','B0001','승인',5500)"]
for x, (key, head, sub, fill, line, lead, items, code), same in zip(X, CARDS, SAME):
    card = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(Y), Inches(W), Inches(H))
    card.adjustments[0] = 0.08
    card.fill.solid(); card.fill.fore_color.rgb = RGB(fill)
    card.line.color.rgb = RGB(line); card.line.width = Pt(1.5)
    card.shadow.inherit = False
    s.shapes.add_picture(os.path.join(icons, key + '.png'), Inches(x + 0.22), Inches(Y + 0.2), Inches(0.55), Inches(0.55))
    box(x + 0.9, Y + 0.13, W - 1.0, 0.7, [(head, {'size': 17, 'bold': True, 'color': RGB(line)}),
                                          (sub, {'size': 11, 'bold': True, 'color': SUB})])
    body = [(lead, {'size': 12.5, 'bold': True})]
    body += [(t, {'size': 10.5 if code else 11.5, 'font': 'Courier New' if code else 'Malgun Gothic'}) for t in items]
    box(x + 0.22, Y + 0.95, W - 0.4, H - 1.5, body)
    strip = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x + 0.15), Inches(Y + H - 0.55), Inches(W - 0.3), Inches(0.42))
    strip.fill.solid(); strip.fill.fore_color.rgb = RGB('FFFFFF'); strip.line.color.rgb = RGB(line); strip.line.width = Pt(0.75)
    strip.shadow.inherit = False
    tf = strip.text_frame; tf.margin_left = tf.margin_right = Inches(0.06); tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    rr = tf.paragraphs[0].add_run(); rr.text = '같은 주문 ▸ ' + same
    rr.font.size = Pt(9.5); rr.font.color.rgb = RGB(line); rr.font.bold = True
    rr.font.name = 'Courier New' if code else 'Malgun Gothic'
for ax in (4.43, 8.53):
    a = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(ax), Inches(Y + H / 2 - 0.16), Inches(0.38), Inches(0.32))
    a.fill.solid(); a.fill.fore_color.rgb = RGB('7F7F7F'); a.line.fill.background(); a.shadow.inherit = False

# 5) 강의 포인트(기존 문구 유지) 위치 정리
if point is not None:
    point.left, point.top, point.width, point.height = Inches(0.75), Inches(5.38), Inches(11.85), Inches(0.62)

# 6) 약어 주석(출처 위) + 출처
box(0.75, 6.2, 11.85, 0.28, [('※ PK: Primary Key (기본키) · FK: Foreign Key (외래키) · CHECK: 허용 값을 제한하는 제약조건 · '
                              'UNIQUE: 중복을 막는 제약조건 · 1:N: 일대다 관계', {'size': 10.5, 'color': RGB('3A445C')})])
srcbox = next(sh for sh in s.shapes if sh.has_text_frame and sh.text_frame.text.strip().startswith('출처'))
srcbox.left, srcbox.top, srcbox.width, srcbox.height = Inches(0.75), Inches(6.55), Inches(10.6), Inches(0.28)
r = srcbox.text_frame.paragraphs[0].runs
r[0].text = '출처: Palantir Ontology 문서 — Object·Property·Link·Action 개념 / PostgreSQL 공식 문서 — Constraints (PRIMARY KEY·FOREIGN KEY·CHECK·UNIQUE)'
r[0].font.size = Pt(9.5)
for x in r[1:]:
    x.text = ''

s.notes_slide.notes_text_frame.text = (
    '【슬라이드 핵심】 같은 주문·결제 업무가 현실 세계(사건) → 개념 세계(Palantir Ontology 객체·속성·링크·액션) → 컴퓨터 세계(PostgreSQL 테이블·PK/FK·CHECK·UNIQUE)로 바뀐다.\n'
    '【강의 설명】 현실 세계에서는 “김민지가 아메리카노 2잔을 주문하고 카드로 결제했다가 환불을 요청했다” 같은 사건이 일어난다. '
    '개념 세계에서는 이를 Customer·Order·Payment 객체와 주문일시·금액·상태 같은 속성, Customer 1:N Order 1:N Payment 링크, 결제 승인·환불 같은 액션으로 정의한다. '
    '컴퓨터 세계에서는 객체를 테이블로, 링크를 외래키로, 업무 규칙을 CHECK(상태 값 제한)·UNIQUE(승인번호 중복 금지) 제약조건으로 구현한다. '
    '6쪽 반도체 사례(웨이퍼·로트·소재 → 객체 → 레코드)와 같은 흐름임을 짚는다.\n'
    '【연결】 5–7쪽 데이터의 구분, 6쪽 Palantir 반도체 사례, 37–43쪽 Colab 주문·결제 실습\n'
    '【출처】 Palantir Ontology 문서(Object·Property·Link·Action), PostgreSQL 공식 문서 Constraints')

prs.save(out)
print('ok')
