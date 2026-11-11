"""11-2 정규화(26) 16쪽(3차 정규화) 보강: 13쪽(2차 정규화)처럼 결과 ER 다이어그램을 추가해 이해를 돕는다.
- 오른쪽: 3차 정규화 결과 — 고객(고객번호 PK; 사업자번호·우선순위·수출여부) 1 ─< 주문(주문번호 PK; 주문일자·고객번호 FK)
  13쪽과 같은 스타일(555FAB 테두리·채운 속성 상자·노란 강조 상자·까마귀발 표기)
- 표 아래: 종속 사슬 주문번호 → 고객번호 → 사업자번호·우선순위·수출여부 (이행 종속)
- 기존 표·화살표·설명 문장 유지, 'Transitive Dependency 1' 라벨만 다이어그램 아래로 이동, 약어 주석·노트 추가
python slide16_3nf_diagram.py <in.pptx> <out.pptx>   (다시 실행하면 추가 도형만 새로 만듦)"""
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

src, out = sys.argv[1:3]
prs = Presentation(src)
RGB = lambda h: RGBColor.from_string(h)
P, YEL, WHITE = '555FAB', 'FFE858', 'FFFFFF'
TAG = 'cd112_3nf'                                         # 추가 도형 이름 접두어

s = next(sl for sl in prs.slides if any(sh.has_text_frame and sh.text_frame.text.startswith('3차 정규화 – Remove Transitive')
                                        for sh in sl.shapes))
for sh in list(s.shapes):
    if sh.name.startswith(TAG):
        sh._element.getparent().remove(sh._element)


def named(sh, n):
    sh.name = f'{TAG}_{n}'
    return sh


def tb(n, x, y, w, h, lines, size=11, color=P, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    t = named(s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)), n)
    tf = t.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    for m in ('margin_left', 'margin_right', 'margin_top', 'margin_bottom'):
        setattr(tf, m, Inches(0.03))
    for i, ln in enumerate(lines):
        runs = ln if isinstance(ln, list) else [ln]
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.alignment = align
        for rr in runs:
            text, kw = (rr, {}) if isinstance(rr, str) else rr
            r = p.add_run(); r.text = text
            r.font.size = Pt(kw.get('size', size)); r.font.bold = kw.get('bold', bold)
            r.font.color.rgb = RGB(kw.get('color', color)); r.font.name = 'Arial'
    return t


def rect(n, x, y, w, h, fill=None, line=P, lw=1.5, lines=(), color=P, size=10.5, align=PP_ALIGN.LEFT, kind=MSO_SHAPE.RECTANGLE):
    r = named(s.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h)), n)
    if fill:
        r.fill.solid(); r.fill.fore_color.rgb = RGB(fill)
    else:
        r.fill.background()
    if line:
        r.line.color.rgb = RGB(line); r.line.width = Pt(lw)
    else:
        r.line.fill.background()
    r.shadow.inherit = False
    tf = r.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.TOP
    tf.margin_left = Inches(0.08); tf.margin_top = Inches(0.04); tf.margin_bottom = Inches(0.02)
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.alignment = align
        q = p.add_run(); q.text = ln; q.font.size = Pt(size); q.font.color.rgb = RGB(color); q.font.name = 'Arial'
    return r


def line(n, x1, y1, x2, y2, w=1.5):
    c = named(s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2)), n)
    c.line.color.rgb = RGB(P); c.line.width = Pt(w)
    return c


# ── 오른쪽: 3차 정규화 결과 ER 다이어그램 (13쪽 스타일)
tb('title', 9.15, 3.92, 4.0, 0.62, ['3차 정규화 결과:', '고객번호에 종속된 속성을 ‘고객’으로 분리'], size=13, align=PP_ALIGN.CENTER)


def entity(key, x, y, name, pk, attrs, w=1.55):
    rect(f'{key}_tab', x, y, 0.62, 0.3, WHITE, lines=[name], size=10.5)
    rect(f'{key}_pk', x, y + 0.33, w, 0.33, WHITE, lines=[pk], size=10.5)
    rect(f'{key}_at', x, y + 0.66, w, 0.22 * len(attrs) + 0.14, P, line=P, lines=attrs, color=WHITE, size=10)


EY = 4.62
entity('cust', 9.25, EY, '고객', '고객번호', ['사업자번호', '우선순위', '수출여부'])
entity('ord', 11.55, EY, '주문', '주문번호', ['주문일자', '고객번호(FK)'])
# 관계: 고객 1 ─< 주문 N  (13쪽과 같은 까마귀발 표기)
yy = EY + 0.33 + 0.165
line('rel', 10.8, yy, 11.55, yy)
line('one1', 10.95, yy - 0.12, 10.95, yy + 0.12)
line('one2', 11.03, yy - 0.12, 11.03, yy + 0.12)
for dy in (-0.11, 0, 0.11):
    line(f'crow{dy}', 11.36, yy, 11.55, yy + dy)
line('crowbar', 11.3, yy - 0.12, 11.3, yy + 0.12)
tb('one', 10.75, yy - 0.42, 0.4, 0.25, ['1'], size=10, bold=True)
tb('many', 11.28, yy - 0.42, 0.4, 0.25, ['N'], size=10, bold=True)
# 노란 강조: 분리된 속성 (13쪽 노란 상자와 같은 의미)
hl = rect('hl', 9.2, EY + 0.3, 1.65, 1.35, None, line=YEL, lw=4.5)

# 강의자 라벨 'Transitive Dependency 1'을 다이어그램 아래로
lab = next((sh for sh in s.shapes if sh.has_text_frame and sh.text_frame.text.strip().startswith('Transitive Dependency')), None)
if lab is not None:
    lab.left, lab.top = Inches(9.3), Inches(6.38)

# ── 표 아래: 종속 사슬 (주식별자 → 결정자 → 이행 종속 속성)
CY = 6.08
chain = [('주문번호', '주식별자', 1.25), ('고객번호', '비식별자 · 결정자', 1.25), ('사업자번호 · 우선순위 · 수출여부', '이행 종속 속성', 3.1)]
x = 1.41
for i, (k, sub, w) in enumerate(chain):
    fill = WHITE if i == 0 else (YEL if i == 1 else P)
    rect(f'ch{i}', x, CY, w, 0.36, fill, lines=[k], color=WHITE if i == 2 else P, size=11, align=PP_ALIGN.CENTER,
         kind=MSO_SHAPE.ROUNDED_RECTANGLE).text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    tb(f'chs{i}', x, CY + 0.37, w, 0.25, [sub], size=9, color='5A5A5A', align=PP_ALIGN.CENTER)
    if i < 2:
        a = rect(f'arr{i}', x + w + 0.08, CY + 0.08, 0.32, 0.2, P, line=None, kind=MSO_SHAPE.RIGHT_ARROW)
    x += w + 0.48

tb('foot', 1.0, 6.98, 10.4, 0.25, ['※ FK: Foreign Key (외래키) · 결정자: 다른 속성 값을 결정하는 속성 · 이행 종속: A→B, B→C 이면 A→C 로 간접 종속'],
   size=9, color='3A445C')

s.notes_slide.notes_text_frame.text = (
    '【슬라이드 핵심】 3차 정규화는 주식별자가 아닌 속성(고객번호)이 다른 속성을 결정하는 이행 종속을 없애, 그 속성들을 별도 엔터티(고객)로 분리하는 것이다.\n'
    '【강의 설명】 주문 표에서 사업자번호·우선순위·수출여부는 주문번호가 아니라 고객번호에 따라 정해진다(AD347·CB230은 같은 고객 2341이라 값이 같다). '
    '즉 주문번호 → 고객번호 → 사업자번호처럼 간접(이행) 종속이다. 이대로 두면 고객 정보가 주문마다 반복되고, 고객의 우선순위를 바꾸려면 여러 주문 행을 고쳐야 한다(갱신 이상). '
    '그래서 오른쪽 다이어그램처럼 고객(고객번호 PK, 사업자번호·우선순위·수출여부)을 분리하고, 주문에는 고객번호를 외래키로 남긴다. 고객 1명이 여러 주문을 하므로 고객 1 : N 주문이다. '
    '13쪽 2차 정규화(제품번호에만 종속된 속성을 분리)와 같은 방식으로, 노란 상자가 분리된 속성이다.\n'
    '【연결】 13쪽 2차 정규화 다이어그램, 이후 BCNF·반정규화\n'
    '【출처】 11-2 정규화 원본 교안')
prs.save(out)
print('ok')
