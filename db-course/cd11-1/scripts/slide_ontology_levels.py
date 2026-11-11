"""11-1 보강본 'Palantir Ontology: 현실 업무를 데이터 모델로'(현재 39쪽) 보강:
본문 4줄은 유지(글자 크기만 줄임), 빈 글머리표 제거, Ontology를 개념·논리·물리 3단으로 구분한 표형 행 추가,
본문과 맞지 않던 노트(AWS·Google 비교)를 Palantir 3단 설명으로 교체. 다시 실행하면 추가 도형만 다시 만든다.
python slide_ontology_levels.py <in.pptx> <out.pptx>"""
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

src, out = sys.argv[1:3]
prs = Presentation(src)
RGB = lambda h: RGBColor.from_string(h)
TXT, SUB, NAVY = RGB('262626'), RGB('5A5A5A'), RGB('1F4E79')

s = next(sl for sl in prs.slides if sl.shapes.title is not None
         and sl.shapes.title.text_frame.text.strip().startswith('Palantir Ontology: 현실 업무를 데이터 모델로'))
for sh in list(s.shapes):
    if not sh.is_placeholder:
        sh._element.getparent().remove(sh._element)
body = next(sh for sh in s.placeholders if sh.placeholder_format.idx == 1)
for p in list(body.text_frame.paragraphs):
    if not p.text.strip() or p.text.strip().startswith('Ontology ·'):
        p._p.getparent().remove(p._p)
for p in body.text_frame.paragraphs:
    for r in p.runs:
        r.font.size = Pt(15)
body.top, body.height = Inches(1.45), Inches(1.4)


def box(x, y, w, h, paras, size=10.5, color=TXT, bold=False, anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.LEFT, font='Malgun Gothic', spacing=1):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    for m in ('margin_left', 'margin_right', 'margin_top', 'margin_bottom'):
        setattr(tf, m, Inches(0.05))
    for i, p in enumerate(paras):
        runs = p if isinstance(p, list) else [p]
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = align; para.space_after = Pt(spacing)
        for rr in runs:
            text, kw = (rr, {}) if isinstance(rr, str) else rr
            r = para.add_run(); r.text = text
            r.font.size = Pt(kw.get('size', size)); r.font.bold = kw.get('bold', bold)
            r.font.color.rgb = kw.get('color', color); r.font.name = kw.get('font', font)
    return tb


def shape(kind, x, y, w, h, fill, line=None, lw=1.0):
    c = s.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    c.fill.solid(); c.fill.fore_color.rgb = RGB(fill)
    if line:
        c.line.color.rgb = RGB(line); c.line.width = Pt(lw)
    else:
        c.line.fill.background()
    c.shadow.inherit = False
    return c


X = [0.75, 2.2, 6.45, 10.0]; W = [1.35, 4.15, 3.45, 2.6]
for x, w, h in zip(X, W, ['단계', 'Ontology에서 정하는 것', '예: 고객 주문', '관계형 DB로 옮기면']):
    box(x, 2.88, w, 0.28, [(h, {'bold': True, 'color': SUB, 'size': 10.5})])

ROWS = [
    ('개념', '무엇을 관리하나?', '7030A0', 'F3ECFA',
     ['객체 타입 · 링크 타입 · 액션을 업무 언어로 정의'],
     ['고객 · 주문 · 제품 객체', '고객–주문 링크, ‘주문 취소’ 액션'],
     ['개체 · 관계 · 업무 규칙 (ER 모델)']),
    ('논리', '어떤 구조로?', '1F4E79', 'DEEBF7',
     ['객체마다 기본키 속성과 자료형이 있는 속성', '링크는 외래키, 다대다는 연결 데이터셋'],
     ['주문: order_id(기본키), customer_id,', '주문일시, 상태 · 주문–제품은 연결'],
     ['테이블 · PK · FK', 'N:M 연결 테이블']),
    ('물리', '어떻게 운영하나?', '548235', 'E2F0D9',
     ['원천 데이터셋에서 객체로 동기화 · 색인해 빠르게 조회', '권한으로 누가 보고 어떤 액션을 실행할지 통제'],
     ['주문 데이터셋 → 주문 객체', '상담원은 조회만, 관리자만 취소 실행'],
     ['실제 테이블 · 인덱스', '권한(GRANT)']),
]
y = 3.18
for lvl, q, line, fill, decide, ex, rel in ROWS:
    shape(MSO_SHAPE.ROUNDED_RECTANGLE, 0.75, y, 11.85, 0.86, fill, line, 1.25).adjustments[0] = 0.1
    lab = shape(MSO_SHAPE.ROUNDED_RECTANGLE, 0.85, y + 0.08, 1.25, 0.7, line)
    tf = lab.text_frame; tf.vertical_anchor = MSO_ANCHOR.MIDDLE; tf.margin_left = tf.margin_right = Inches(0.02)
    for i, (t, sz) in enumerate([(lvl, 15), (q, 8.5)]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.alignment = PP_ALIGN.CENTER
        r = p.add_run(); r.text = t; r.font.size = Pt(sz); r.font.bold = True; r.font.color.rgb = RGB('FFFFFF'); r.font.name = 'Malgun Gothic'
    box(2.2, y + 0.03, 4.15, 0.8, [[('• ', {'bold': True, 'color': RGB(line)}), d] for d in decide])
    box(6.45, y + 0.03, 3.45, 0.8, ex, size=10, color=RGB(line))
    rb = shape(MSO_SHAPE.ROUNDED_RECTANGLE, 10.0, y + 0.1, 2.5, 0.66, 'FFFFFF', line, 0.75)
    box(10.0, y + 0.1, 2.5, 0.66, rel, size=10, align=PP_ALIGN.CENTER)
    y += 0.93

bar = shape(MSO_SHAPE.ROUNDED_RECTANGLE, 0.75, 6.0, 11.85, 0.46, '0F2A4A')
tf = bar.text_frame; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
for t, c in [('업무 객체·액션', 'D9C3F0'), ('(개념) → ', 'FFFFFF'), ('키·속성', 'BDD7EE'), ('(논리) → ', 'FFFFFF'),
             ('데이터셋·색인·권한', 'C5E0B4'), ('(물리)을 한 플랫폼에서 연결해 운영합니다', 'FFFFFF')]:
    r = p.add_run(); r.text = t; r.font.size = Pt(12.5); r.font.bold = True; r.font.color.rgb = RGB(c); r.font.name = 'Malgun Gothic'

box(0.75, 6.5, 11.85, 0.26, [('※ Ontology: 조직의 실제 업무 개체와 관계를 표현하는 운영 모델 · Object/Link/Action: 객체/링크/액션 · PK·FK: 기본키·외래키 · GRANT: 권한 부여 SQL',
                              {'size': 9, 'color': RGB('3A445C')})], anchor=MSO_ANCHOR.TOP)
box(0.75, 6.76, 10.6, 0.26, [('출처: Palantir Foundry 문서 — Ontology 개요(Object types · Properties · Link types · Actions), Object permissions',
                              {'size': 8.5, 'color': SUB})], anchor=MSO_ANCHOR.TOP)

s.notes_slide.notes_text_frame.text = (
    '【슬라이드 핵심】 Palantir Ontology는 개념 모델처럼 보이지만 개념(업무 객체·액션) → 논리(키·속성·링크) → 물리(데이터셋·색인·권한)가 한 플랫폼에서 이어진 기업 사례다.\n'
    '【강의 설명】 개념: 업무 담당자 언어로 객체 타입(고객·주문·제품), 링크 타입(고객–주문), 액션(주문 취소)을 정한다. ER 모델의 개체·관계·업무 규칙과 같다. '
    '논리: 각 객체 타입에 기본키 역할의 속성과 자료형이 있는 속성을 두고, 링크는 외래키로, 다대다는 연결 데이터셋으로 정의한다. 관계형의 테이블·PK·FK·연결 테이블에 해당한다. '
    '물리: 객체는 Foundry의 원천 데이터셋에서 동기화되어 빠른 조회를 위해 색인되고, 권한으로 누가 어떤 객체를 보고 어떤 액션을 실행할지 통제한다. 관계형의 실제 테이블·인덱스·GRANT에 해당한다. '
    '“Palantir는 업무 객체와 액션을 먼저 정하고(개념), 키와 속성으로 정의한 뒤(논리), 데이터셋·색인·권한으로 운영한다(물리)”로 정리한다.\n'
    '【연결】 개념·논리·물리 모델링 슬라이드, 29쪽 적용 사례(개념·논리·물리), 9쪽 데이터의 세 세계\n'
    '【출처】 Palantir Foundry 문서: Ontology overview, Object types, Properties, Link types, Action types, Object permissions')
prs.save(out)
print('ok')
