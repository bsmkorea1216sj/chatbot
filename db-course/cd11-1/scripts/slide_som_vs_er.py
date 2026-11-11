"""11-1 보강본: 26쪽(개념적 데이터 모델 정의·종류, 강의자 이미지) 다음에 '의미 객체 모델 vs ER 모델' 비교 1장 추가.
같은 도서관 대출 예제(19쪽)를 ER 다이어그램과 의미 객체 다이어그램으로 나란히 그리고, 아래에 비교 표.
python slide_som_vs_er.py <in.pptx> <out.pptx>   (같은 제목 슬라이드가 있으면 그 자리에서 다시 만듦)"""
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

src, out = sys.argv[1:3]
prs = Presentation(src)
RGB = lambda h: RGBColor.from_string(h)
TXT, SUB, NAVY, GREEN, PURPLE = RGB('262626'), RGB('5A5A5A'), RGB('1F4E79'), RGB('548235'), RGB('7030A0')
TITLE = '의미 객체 모델 vs ER 모델'
ids = prs.slides._sldIdLst

s = next((sl for sl in prs.slides if sl.shapes.title is not None and sl.shapes.title.text_frame.text.strip() == TITLE), None)
if s is None:
    # 'Hulu 사례' 개념적 데이터 모델 슬라이드(현재 27쪽) 바로 앞 = 26쪽 다음
    hulu = next(i for i, sl in enumerate(prs.slides) if sl.shapes.title is not None
                and sl.shapes.title.text_frame.text.strip() == '개념적 데이터 모델'
                and any(sh.has_text_frame and 'Hulu' in sh.text_frame.text for sh in sl.shapes))
    s = prs.slides.add_slide(prs.slides[hulu].slide_layout)
    el = ids[-1]; ids.remove(el); ids.insert(hulu, el)
for sh in list(s.shapes):
    if not (sh.is_placeholder and sh.placeholder_format.idx == 0):
        sh._element.getparent().remove(sh._element)
s.shapes.title.text_frame.text = TITLE


def text(sh, t, size=10, color=TXT, bold=False, align=PP_ALIGN.CENTER, underline=False, font='Malgun Gothic'):
    tf = sh.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    for m in ('margin_left', 'margin_right', 'margin_top', 'margin_bottom'):
        setattr(tf, m, Inches(0.02))
    p = tf.paragraphs[0]; p.alignment = align
    r = p.add_run(); r.text = t
    r.font.size = Pt(size); r.font.bold = bold; r.font.color.rgb = color; r.font.name = font; r.font.underline = underline
    return sh


def shape(kind, x, y, w, h, fill='FFFFFF', line=None, lw=1.25, dash=False):
    c = s.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill:
        c.fill.solid(); c.fill.fore_color.rgb = RGB(fill)
    else:
        c.fill.background()
    if line:
        c.line.color.rgb = RGB(line); c.line.width = Pt(lw)
        if dash:
            from pptx.enum.dml import MSO_LINE
            c.line.dash_style = MSO_LINE.DASH
    else:
        c.line.fill.background()
    c.shadow.inherit = False
    return c


def tbox(x, y, w, h, t, **kw):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    return text(tb, t, **kw)


def line(x1, y1, x2, y2, color='7F7F7F', w=1.0):
    c = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb = RGB(color); c.line.width = Pt(w)
    return c


tbox(0.75, 1.47, 11.85, 0.38, '같은 ‘동네 도서관 대출’(19쪽)을 두 가지 개념적 데이터 모델로 그려 보면', size=14.5, color=NAVY, bold=True, align=PP_ALIGN.LEFT)

# ── 왼쪽: ER 모델 (Chen 표기: □ 개체, ◇ 관계, ○ 속성)
shape(MSO_SHAPE.ROUNDED_RECTANGLE, 0.75, 1.92, 5.75, 2.62, 'F7FAFE', '1F4E79', 1.25).adjustments[0] = 0.04
tbox(0.9, 1.97, 5.4, 0.3, 'ER 모델 (Chen, 1976) · 개체 □ · 관계 ◇ · 속성 ○', size=11.5, color=NAVY, bold=True, align=PP_ALIGN.LEFT)
EY = 3.35                                                # 개체·관계 중심선
ent = {'회원': (1.0, 1.2), '도서': (5.05, 1.2)}
for name, (x, w) in ent.items():
    line(x + w / 2, EY, x + w / 2, EY - 0.62)
for name, (x, w) in ent.items():
    pass
# 속성 타원 (먼저 선, 나중에 도형)
ATT = [('회원번호', 0.85, True, 1.6), ('이름', 1.9, False, 1.6),            # 위: 개체 속성
       ('ISBN', 4.45, True, 5.65), ('제목', 5.5, False, 5.65)]
for t, ax, key, anchor_x in ATT:
    line(ax + 0.47, 2.72, anchor_x, EY - 0.25)
RATT = [('대출일', 2.25), ('반납예정일', 3.62)]                              # 아래: 관계 속성
for t, ax in RATT:
    line(ax + 0.47, 3.82, 3.42, EY + 0.3)
line(2.2, EY, 2.82, EY); line(4.02, EY, 5.05, EY)
for t, ax, key, _ in ATT:
    text(shape(MSO_SHAPE.OVAL, ax, 2.38, 0.95, 0.36, 'FFFFFF', '1F4E79', 1), t, size=9, underline=key)
for t, ax in RATT:
    text(shape(MSO_SHAPE.OVAL, ax, 3.78, 0.95, 0.34, 'FFFFFF', 'C55A11', 1), t, size=8.5 if len(t) > 4 else 9)
for name, (x, w) in ent.items():
    text(shape(MSO_SHAPE.RECTANGLE, x, EY - 0.25, w, 0.5, 'DEEBF7', '1F4E79', 1.5), name, size=12, color=NAVY, bold=True)
text(shape(MSO_SHAPE.DIAMOND, 2.82, EY - 0.32, 1.2, 0.64, 'FCE4D6', 'C55A11', 1.5), '대출', size=11, color=RGB('C55A11'), bold=True)
tbox(2.3, EY - 0.33, 0.4, 0.25, 'N', size=11, color=RGB('C55A11'), bold=True)
tbox(4.3, EY - 0.33, 0.4, 0.25, 'M', size=11, color=RGB('C55A11'), bold=True)
tbox(0.9, 4.18, 5.45, 0.3, '대출 = 관계(◇), 대출일·반납예정일 = 관계의 속성 · 키는 밑줄 → 테이블 3개로', size=9.5, color=SUB, align=PP_ALIGN.LEFT)

# ── 오른쪽: 의미 객체 모델 (Kroenke 표기: 객체 상자 안에 속성, 개수는 최소.최대)
shape(MSO_SHAPE.ROUNDED_RECTANGLE, 6.75, 1.92, 5.85, 2.62, 'FBF8FE', '7030A0', 1.25).adjustments[0] = 0.04
tbox(6.9, 1.97, 5.6, 0.3, '의미 객체 모델 (Kroenke, 1988) · 객체 상자 안에 속성', size=11.5, color=PURPLE, bold=True, align=PP_ALIGN.LEFT)


def sem_object(x, y, w, h, name, rows):
    shape(MSO_SHAPE.RECTANGLE, x, y, w, h, 'FFFFFF', '7030A0', 1.5)
    text(shape(MSO_SHAPE.RECTANGLE, x, y, w, 0.3, 'E4D5F2', '7030A0', 1.5), name, size=11, color=PURPLE, bold=True)
    yy = y + 0.36
    for kind, label, card in rows:
        if kind == 'attr':
            tbox(x + 0.08, yy, w - 0.6, 0.22, label, size=9.5, align=PP_ALIGN.LEFT, bold=label.startswith('ID'))
            tbox(x + w - 0.55, yy, 0.48, 0.22, card, size=9, color=SUB, align=PP_ALIGN.RIGHT)
            yy += 0.24
        elif kind == 'group':                       # 그룹 속성: 안쪽 사각형
            gx, gw, gh = x + 0.08, w - 0.16, 0.24 * len(label[1]) + 0.32
            shape(MSO_SHAPE.RECTANGLE, gx, yy, gw, gh, 'F7F2FC', 'A27BC9', 1)
            tbox(gx + 0.05, yy + 0.02, gw - 0.6, 0.22, label[0], size=9.5, bold=True, color=PURPLE, align=PP_ALIGN.LEFT)
            tbox(gx + gw - 0.52, yy + 0.02, 0.46, 0.22, card, size=9, color=SUB, align=PP_ALIGN.RIGHT)
            iy = yy + 0.27
            for sub_kind, sl, sc in label[1]:
                if sub_kind == 'obj':
                    text(shape(MSO_SHAPE.RECTANGLE, gx + 0.08, iy, gw - 0.7, 0.21, 'E4D5F2', '7030A0', 0.75), sl, size=9, color=PURPLE, bold=True)
                else:
                    tbox(gx + 0.08, iy, gw - 0.7, 0.21, sl, size=9.5, align=PP_ALIGN.LEFT)
                tbox(gx + gw - 0.52, iy, 0.46, 0.21, sc, size=9, color=SUB, align=PP_ALIGN.RIGHT)
                iy += 0.24
            yy += gh + 0.04
        elif kind == 'obj':                         # 객체 속성: 다른 객체를 품는다
            text(shape(MSO_SHAPE.RECTANGLE, x + 0.08, yy, w - 0.7, 0.22, 'E4D5F2', '7030A0', 0.75), label, size=9, color=PURPLE, bold=True)
            tbox(x + w - 0.55, yy, 0.48, 0.22, card, size=9, color=SUB, align=PP_ALIGN.RIGHT)
            yy += 0.26


sem_object(6.95, 2.32, 2.75, 2.08, '회원', [
    ('attr', 'ID 회원번호', '1.1'), ('attr', '이름', '1.1'),
    ('group', ('대출 기록', [('attr', '대출일', '1.1'), ('attr', '반납예정일', '1.1'), ('obj', '도서', '1.1')]), '0.N')])
sem_object(9.95, 2.32, 2.45, 1.45, '도서', [
    ('attr', 'ID ISBN', '1.1'), ('attr', '제목', '1.1'), ('attr', '저자', '1.N'), ('obj', '회원', '0.N')])
tbox(9.95, 3.8, 2.55, 0.7, '회원 카드 한 장 = 객체 하나. 관계는 상대 객체를 속성으로 품는다(양쪽에 짝으로)', size=9.5, color=SUB, align=PP_ALIGN.LEFT)

# ── 비교 표
ROWS = [('구분', 'ER 모델', '의미 객체 모델'),
        ('출발점', '업무에서 개체·관계를 찾아 추상화', '사용자가 보는 양식·보고서 (회원 카드, 대출 화면)'),
        ('관계 표현', '관계(◇)를 따로 그림 · 1:N, N:M 표기', '상대 객체를 속성으로 포함 · 양쪽 객체에 짝으로 표시'),
        ('속성 · 식별자', '단순·복합·다중값 속성, 키는 밑줄', '단순·그룹·객체 속성, 개수는 최소.최대(1.1, 0.N), ID 표시'),
        ('장점', '표준처럼 널리 쓰이고 테이블 변환이 쉬움', '업무 담당자가 자기 양식과 같아 이해하기 쉬움'),
        ('한계', '업무 담당자에게는 추상적', '지원 도구·표준이 적고, 같은 관계가 두 번 그려짐')]
tbl = s.shapes.add_table(len(ROWS), 3, Inches(0.75), Inches(4.63), Inches(11.85), Inches(0.27 * len(ROWS))).table
for j, w in enumerate((1.55, 4.8, 5.5)):
    tbl.columns[j].width = Inches(w)
for i, row in enumerate(ROWS):
    tbl.rows[i].height = Inches(0.27)
    for j, t in enumerate(row):
        c = tbl.cell(i, j); c.text = t
        c.margin_top = c.margin_bottom = Inches(0.02); c.vertical_anchor = MSO_ANCHOR.MIDDLE
        c.fill.solid()
        c.fill.fore_color.rgb = RGB('102950' if i == 0 else ('EDF4FD' if j == 1 else ('F7F2FC' if j == 2 else 'F2F2F2')))
        r = c.text_frame.paragraphs[0].runs[0]
        r.font.size = Pt(10); r.font.name = 'Malgun Gothic'; r.font.bold = (i == 0 or j == 0)
        r.font.color.rgb = RGB('FFFFFF') if i == 0 else TXT

tb = s.shapes.add_textbox(Inches(0.75), Inches(6.32), Inches(11.85), Inches(0.26))
text(tb, '※ ER: Entity-Relationship (개체-관계) · ID: Identifier (식별자) · 1.1 / 0.N / 1.N: 최소.최대 개수 (반드시 1개 / 0개 이상 / 1개 이상) · N:M: 다대다 관계',
     size=9.5, color=RGB('3A445C'), align=PP_ALIGN.LEFT)
tb = s.shapes.add_textbox(Inches(0.75), Inches(6.6), Inches(10.6), Inches(0.26))
text(tb, '출처: P. Chen, “The Entity-Relationship Model—Toward a Unified View of Data”, ACM TODS (1976); D. Kroenke·D. Auer, Database Processing — 의미 객체 모델(1988년 3판에서 처음 소개)',
     size=8.5, color=SUB, align=PP_ALIGN.LEFT)

s.notes_slide.notes_text_frame.text = (
    '【슬라이드 핵심】 같은 업무(도서관 대출)도 ER 모델은 개체·관계·속성을 따로 그리고, 의미 객체 모델은 사용자가 보는 양식 하나를 객체 하나로 묶어 그 안에 속성과 다른 객체를 품는다.\n'
    '【강의 설명】 ER 모델(Peter Chen, 1976)에서는 회원·도서를 개체(사각형)로, 대출을 관계(마름모)로 그리고, 대출일·반납예정일을 관계의 속성(타원)으로 붙인다. 회원과 도서는 N:M이며 키 속성은 밑줄로 표시한다. '
    '이 그림은 members·books·loans 세 테이블로 그대로 바뀐다(19·20쪽). '
    '의미 객체 모델(David Kroenke, 1988)은 사용자가 실제로 보는 양식(회원 카드)에서 출발한다. 회원 객체 안에 이름 같은 단순 속성, 대출 기록 같은 그룹 속성, 그리고 도서라는 객체 속성이 들어간다. '
    '각 속성 옆의 1.1, 0.N, 1.N은 최소.최대 개수다(이름은 반드시 1개, 대출 기록은 0개 이상, 저자는 1명 이상). 관계는 회원 객체 안의 도서, 도서 객체 안의 회원처럼 양쪽에 짝으로 나타난다. '
    '업무 담당자와 이야기할 때는 의미 객체 모델이, DB 테이블로 옮길 때는 ER 모델이 편하다는 점을 비교한다.\n'
    '【연결】 26쪽 개념적 데이터 모델의 종류, 19·20쪽 도서관 대출 예제, 다음 쪽 Hulu 사례(ER 관점)\n'
    '【출처】 P. Chen, “The Entity-Relationship Model—Toward a Unified View of Data”, ACM Transactions on Database Systems 1(1), 1976; '
    'D. Kroenke·D. Auer, Database Processing, 부록 “The Semantic Object Model”(1988년 3판에서 처음 소개)')

prs.save(out)
print('ok, slides =', len(prs.slides), '| new at', [i + 1 for i, sl in enumerate(prs.slides) if sl.shapes.title is not None and sl.shapes.title.text_frame.text.strip() == TITLE])
