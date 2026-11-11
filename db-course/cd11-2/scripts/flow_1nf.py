"""11-2 정규화(26) 1차 정규화(9~12쪽)를 4차·5차와 같은 패턴(문제 → 이상 → 펼침 → 해결)으로 정리. 같은 주문 데이터(AB345~CB231) 사용.
 - 9쪽: 머리글 '1차 정규화 | …' 형식 통일(원본 표·다이어그램 유지)
 - 10쪽: 글로만 된 이상 설명 → 24쪽 디자인(표 + 입력·수정·삭제 색상 카드), 원문 예시 그대로(마우스 재고 9,702→15,000, CB231 스피커)
 - 11쪽: 머리글 통일, 표 오타 정정(CB231 주문수량 800→80, AD347 우선순위 1→3: 9·13쪽과 일치)
 - 12쪽: 다른 예시(주문 101) → 같은 데이터로 '주문 + 주문목록 분리' 해결 페이지(25쪽 디자인), 남은 이상은 13쪽 2차 정규화로 연결
python flow_1nf.py <in.pptx> <out.pptx>"""
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

src, out = sys.argv[1:3]
prs = Presentation(src)
RGB = lambda h: RGBColor.from_string(h)
NAVY, NAVY2, FONT, GRAY, RED = '172B45', '0F3154', '맑은 고딕', '5A5A5A', 'C00000'
BLUE, YELLOW, PINK = 'E2EFFA', 'FFF0BF', 'FCE5E4'

ORDERS = [('AB345', '10.01', '4520'), ('CA210', '10.02', '3280'), ('CB230', '10.03', '2341'), ('AD347', '10.04', '2341'), ('CB231', '10.05', '8320')]
ITEMS = [('AB345', '1001', '모니터', '1990', '150'), ('AB345', '1007', '마우스', '9702', '300'), ('CA210', '1007', '마우스', '9702', '120'),
         ('CB230', '1007', '마우스', '9702', '690'), ('AD347', '1001', '모니터', '1990', '600'), ('CB231', '1201', '스피커', '2108', '80')]


def txt(sl):
    return ' '.join(sh.text_frame.text for sh in sl.shapes if sh.has_text_frame)


def body(sl):
    return next(sh for sh in sl.placeholders if sh.placeholder_format.idx == 1)


def set_header(sl, text, keep_rest=True):
    b = body(sl)
    p0 = b.text_frame.paragraphs[0]
    if p0.runs:
        p0.runs[0].text = text
        for r in p0.runs[1:]:
            r.text = ''
    else:
        p0.add_run().text = text
    if not keep_rest:
        for p in b.text_frame.paragraphs[1:]:
            p._p.getparent().remove(p._p)
    return b


S = list(prs.slides)
s9 = next(sl for sl in S if '1차 정규화 – Remove Repeating Group' in txt(sl))
s10 = next(sl for sl in S if ('1. 입력 이상' in txt(sl) and '마우스의 재고수량' in txt(sl)) or any(sh.name.startswith('cd112_1nf10') for sh in sl.shapes))
s11 = next(sl for sl in S if '정규화(Normalization) – 1차 정규화' in txt(sl))
s12 = next(sl for sl in S if '1차 정규화 전 → 후' in txt(sl) or any(sh.name.startswith('cd112_1nf12') for sh in sl.shapes))


class Page:
    def __init__(self, sl, tag):
        self.s, self.tag = sl, tag
        for sh in list(sl.shapes):
            if sh.name.startswith(tag) or not sh.is_placeholder:
                sh._element.getparent().remove(sh._element)

    def named(self, sh, n):
        sh.name = f'{self.tag}_{n}'
        return sh

    def tb(self, n, x, y, w, h, lines, size=12, color=NAVY, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
        t = self.named(self.s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)), n)
        tf = t.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
        for m in ('margin_left', 'margin_right', 'margin_top', 'margin_bottom'):
            setattr(tf, m, Inches(0.04))
        for i, ln in enumerate(lines):
            runs = ln if isinstance(ln, list) else [ln]
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.alignment = align; p.space_after = Pt(2)
            for rr in runs:
                text, kw = (rr, {}) if isinstance(rr, str) else rr
                r = p.add_run(); r.text = text
                r.font.size = Pt(kw.get('size', size)); r.font.bold = kw.get('bold', bold)
                r.font.color.rgb = RGB(kw.get('color', color)); r.font.name = FONT
        return t

    def table(self, n, x, y, header, rows, colw, rh=0.32, size=11.5, fills=None):
        gf = self.named(self.s.shapes.add_table(len(rows) + 1, len(header), Inches(x), Inches(y), Inches(sum(colw)), Inches(rh * (len(rows) + 1))), n)
        t = gf.table
        for j, cw in enumerate(colw):
            t.columns[j].width = Inches(cw)
        for i, row in enumerate([header] + list(rows)):
            t.rows[i].height = Inches(rh)
            for j, v in enumerate(row):
                c = t.cell(i, j); c.text = v; c.vertical_anchor = MSO_ANCHOR.MIDDLE
                c.margin_top = c.margin_bottom = Inches(0.01); c.margin_left = c.margin_right = Inches(0.03)
                f = (fills or {}).get(i - 1) if i else None
                c.fill.solid(); c.fill.fore_color.rgb = RGB(NAVY if i == 0 else (f or ('FFFFFF' if i % 2 else 'EEF3F9')))
                p = c.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
                r = p.runs[0]; r.font.size = Pt(size); r.font.name = FONT; r.font.bold = (i == 0)
                r.font.color.rgb = RGB('FFFFFF' if i == 0 else '262626')
        return gf

    def card(self, n, x, y, w, h, fill, lines, head=16, size=12):
        c = self.named(self.s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h)), n)
        c.fill.solid(); c.fill.fore_color.rgb = RGB(fill); c.line.fill.background(); c.shadow.inherit = False
        tf = c.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf.margin_left = tf.margin_right = Inches(0.12)
        for k, ln in enumerate(lines):
            p = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
            p.alignment = PP_ALIGN.CENTER if k == 0 else PP_ALIGN.LEFT; p.space_after = Pt(2)
            r = p.add_run(); r.text = ln; r.font.name = FONT; r.font.color.rgb = RGB(NAVY)
            r.font.size = Pt(head if k == 0 else size); r.font.bold = (k == 0)
        return c

    def foot(self, text, y=6.66):
        self.tb('foot', 1.05, y, 10.4, 0.28, [text], size=9.5, color='3A445C')


IHDR = ('주문번호', '제품번호', '제품명', '재고수량', '주문수량')

# ── 9쪽: 머리글 통일
set_header(s9, '1차 정규화 | 한 주문 칸에 제품이 반복된다 (반복 그룹)')
for sh in s9.shapes:                                     # 세로로 깨지던 라벨 정리
    if sh.has_text_frame and sh.text_frame.text.strip() == '테이블':
        sh.width = Inches(0.8)
    if sh.has_text_frame and sh.text_frame.text.strip() == '반복적인 노출':
        sh.top = Inches(6.2)

# ── 10쪽: 이상 현상 (24쪽 디자인)
p = Page(s10, 'cd112_1nf10')
b = set_header(s10, '1차 정규화 | 반복 그룹을 그대로 두면 생기는 이상', keep_rest=False)
b.height = Inches(0.6)
p.tb('l0', 1.05, 2.2, 5.6, 0.4, [[('주문 + 주문한 제품 · 6행', {'bold': True, 'size': 16}), ('  (9쪽 표의 제품 부분)', {'size': 11, 'color': GRAY})]])
p.table('t0', 1.05, 2.62, IHDR, ITEMS, (1.05, 1.0, 0.95, 1.0, 1.0), rh=0.4, size=12, fills={1: YELLOW, 2: YELLOW, 3: YELLOW, 5: PINK})
p.card('c1', 6.3, 2.31, 5.98, 1.09, BLUE, ['입력 이상', '한 주문의 제품이 늘어나면', '→ 제품 칸(열)이나 행을 계속 덧붙여야 함'])
p.card('c2', 6.3, 3.52, 5.98, 1.09, YELLOW, ['수정 이상', '마우스 재고 9,702 → 15,000으로 변경', '→ 노란색 3행을 모두 고쳐야 하고, 하나라도 빠지면 재고 불일치'])
p.card('c3', 6.3, 4.73, 5.98, 1.09, PINK, ['삭제 이상', 'CB231 주문을 삭제하면', '→ 빨간 행과 함께 스피커(1201) 제품 정보도 사라짐'])
p.tb('bottom', 1.05, 6.02, 11.23, 0.5, [[('원인: ', {'bold': True}), ('한 주문 안에 제품 정보가 반복되도록 비정규화된 설계 → 정규화로 중복을 없앤다', {})]], size=14, color=NAVY2)
p.foot('※ 반복 그룹(Repeating Group): 한 행(한 주문) 안에 같은 종류의 값(제품)이 여러 번 나타나는 것')
s10.notes_slide.notes_text_frame.text = (
    '【슬라이드 핵심】 9쪽처럼 한 주문 칸에 여러 제품이 반복되는 표는 입력·수정·삭제 이상을 일으킨다.\n'
    '【강의 설명】 표는 9쪽 주문 표에서 제품 부분만 뽑은 것이다. 파란 입력 카드: 한 주문에 제품이 늘어날 때마다 제품 칸이나 행을 계속 덧붙여야 한다. '
    '노란 수정 카드: 마우스 재고를 9,702에서 15,000으로 바꾸려면 마우스가 들어 있는 노란 3행을 모두 고쳐야 하고, 하나라도 빠지면 재고가 서로 달라진다. '
    '빨간 삭제 카드: CB231 주문을 지우면 그 주문에만 있던 스피커(1201)의 제품명·재고 정보까지 사라진다. 원인은 한 주문 안에 제품 정보를 반복해 넣은 비정규화 설계다.\n'
    '【연결】 9쪽 반복 그룹, 11쪽 한 행씩 펼친 표, 12쪽 주문목록 분리(해결), 13쪽 2차 정규화\n'
    '【출처】 11-2 정규화 원본 교안')

# ── 11쪽: 머리글 통일 + 표 오타 정정(9·13쪽과 일치)
set_header(s11, '1차 정규화 | 반복 그룹을 한 행씩 펼친 결과')
for sh in s11.shapes:
    if sh.has_table:
        t = sh.table
        hdr = [c.text.replace('\n', ' ') for c in t.rows[0].cells]
        for row in list(t.rows)[1:]:
            cells = [c.text for c in row.cells]
            def fix(col, old, new):
                j = next(i for i, h in enumerate(hdr) if h.replace(' ', '') == col)
                c = row.cells[j]
                if c.text == old:
                    r = c.text_frame.paragraphs[0].runs
                    r[0].text = new
                    for x in r[1:]:
                        x.text = ''
            if cells[0] == 'CB231':
                fix('주문수량', '800', '80')
            if cells[0] == 'AD347':
                fix('우선순위', '1', '3')

# ── 12쪽: 해결 (25쪽 디자인)
p = Page(s12, 'cd112_1nf12')
b = set_header(s12, '1차 정규화 | 반복 그룹을 주문목록으로 분리', keep_rest=False)
p.tb('l1', 1.05, 2.15, 5.0, 0.38, [[('주문 · 5행', {'bold': True, 'size': 15}), ('  PK 주문번호 (사업자번호·우선순위·수출여부 생략)', {'size': 10, 'color': GRAY})]])
p.table('t1', 1.05, 2.53, ('주문번호', '주문일자', '고객번호'), ORDERS, (1.6, 1.45, 1.45), rh=0.27, size=11)
p.tb('l2', 1.05, 4.2, 5.0, 0.38, [[('주문목록 · 6행', {'bold': True, 'size': 15}), ('  PK (주문번호, 제품번호) · 주문번호 FK', {'size': 10, 'color': GRAY})]])
p.table('t2', 1.05, 4.58, IHDR, ITEMS, (1.0, 0.95, 0.85, 0.85, 0.85), rh=0.235, size=10, fills={1: YELLOW, 2: YELLOW, 3: YELLOW})
p.card('c1', 6.3, 2.31, 5.98, 1.09, BLUE, ['입력 → 해결', '제품이 늘어나도 주문목록에 1행씩 추가', '→ 주문 표의 칸을 늘릴 필요 없음 (한 칸에 한 값)'])
p.card('c2', 6.3, 3.52, 5.98, 1.09, YELLOW, ['수정 → 아직 남음', '마우스 재고는 주문목록 노란 3행에 여전히 반복', '→ 제품명·재고수량은 제품번호에만 종속 → 13쪽 2차 정규화'])
p.card('c3', 6.3, 4.73, 5.98, 1.09, PINK, ['삭제 → 아직 남음', 'CB231 주문목록을 지우면 스피커 정보도 사라짐', '→ 제품을 별도 표로 분리하면 해결 (13쪽)'])
p.tb('bottom', 6.3, 5.95, 5.98, 0.62, [[('1NF = 한 칸에 한 값, 반복 그룹은 별도 표로', {'bold': True}),
                                         (' · 주문번호로 두 표를 JOIN하면 11쪽 표가 그대로 복원', {})]], size=12, color=NAVY2)
p.foot('※ PK: Primary Key (기본키) · FK: Foreign Key (외래키) · 1NF: First Normal Form (제1정규형) · JOIN: 키로 두 표의 행을 연결', y=6.75)
s12.notes_slide.notes_text_frame.text = (
    '【슬라이드 핵심】 반복 그룹(한 주문의 여러 제품)을 주문목록 표로 분리하면 1NF가 된다. 입력 이상은 해결되지만, 제품번호에만 종속된 제품명·재고수량 때문에 수정·삭제 이상이 남아 2차 정규화로 이어진다.\n'
    '【강의 설명】 9~11쪽과 같은 데이터를 쓴다. 주문 표는 주문번호를 기본키로 주문 단위 정보(주문일자·고객번호 등)를 한 번만 저장한다. '
    '주문목록 표는 (주문번호, 제품번호) 복합키로 제품마다 한 행을 두고, 주문번호는 주문 표를 가리키는 외래키다. 파란 카드: 제품이 늘어나도 주문목록에 행만 추가하면 된다. '
    '노란 카드: 그러나 마우스의 제품명·재고수량은 여전히 주문목록의 3행에 반복되어 재고를 바꾸려면 3행을 고쳐야 한다. 빨간 카드: CB231의 주문목록 행을 지우면 스피커 정보도 사라진다. '
    '두 문제 모두 제품명·재고수량이 주문번호가 아니라 제품번호에만 종속되기 때문이며(부분 종속), 13쪽 2차 정규화에서 해결한다. 두 표를 주문번호로 JOIN하면 11쪽의 펼친 표가 그대로 복원된다.\n'
    '【연결】 10쪽 이상 현상, 11쪽 펼친 표, 13쪽 2차 정규화(부분 종속 분리)\n'
    '【출처】 11-2 정규화 원본 교안 9~13쪽 주문 예제 재구성')
prs.save(out)
print('ok')
