"""11-2 정규화(26) 4차 정규화 흐름 정리 (22~25쪽, 24쪽 Codex 예시 기준: 사원 10 · Modeling·DBA × SI·OO·PA).
보이는 흐름: 22 도입(독립 목록) → 23 한 표로 펼치는 두 방법 → 24 이상 현상 → 25 두 표로 분리해 해결 → 27 응용(실제 사용 기술)
 - 23쪽: 머리글을 22·24쪽과 같은 '4차 정규화 | …' 형식으로, 결론 띠 쪽 번호 25쪽
 - 25쪽: E01 예시(22쪽과 중복) → 사원 10 예시의 '해결' 페이지로 재구성(24쪽 디자인: 표 + 입력·수정·삭제 색상 카드)
         원래 제목 자리(템플릿 제목·머리글)는 24쪽 placeholder를 복제해 통일
 - 22·24쪽 노트의 '25~26쪽'(26쪽은 강의자가 숨김) → '25쪽'
python flow_4nf.py <in.pptx> <out.pptx>"""
import sys, copy
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

src, out = sys.argv[1:3]
prs = Presentation(src)
RGB = lambda h: RGBColor.from_string(h)
NAVY, NAVY2, FONT = '172B45', '0F3154', '맑은 고딕'
TAG = 'cd112_4nf25'


def txt(sl):
    return ' '.join(sh.text_frame.text for sh in sl.shapes if sh.has_text_frame)


S = list(prs.slides)
s22 = next(sl for sl in S if '4차 정규화 | 독립적인 두 목록을 나누는 이유' in txt(sl))
s23 = next(sl for sl in S if '여러 값을 중복적으로 삽입해야 하는 종속성을 제거' in txt(sl))
s24 = next(sl for sl in S if '4차 정규화 | 한 표에 두 목록을 담을 때 생기는 이상' in txt(sl))
s25 = next(sl for sl in S if ('4차 정규화 ① | 독립적인 두 목록을 나누는 이유' in txt(sl)) or any(sh.name.startswith(TAG) for sh in sl.shapes))


def notes_replace(sl, pairs):
    for p in sl.notes_slide.notes_text_frame.paragraphs:
        for r in p.runs:
            for a, b in pairs:
                r.text = r.text.replace(a, b)


# ── 22·24쪽 노트 쪽 번호
notes_replace(s22, [('23~24쪽에서는 독립 목록을 한 표에 섞을 때 발생하는 문제를, 25~26쪽에서는 분리와 키 연결을 확인한다.',
                     '23쪽에서는 한 표로 펼치는 두 방법(거짓 짝·모든 조합)을, 24쪽에서는 이상 현상을, 25쪽에서는 두 표로 분리한 해결을 확인한다.'),
                    ('25~26쪽', '25쪽')])
notes_replace(s24, [('25~26쪽의 분리 설계', '25쪽의 분리 설계'), ('25~26쪽', '25쪽')])

# ── 23쪽 머리글·결론 띠
body23 = next(sh for sh in s23.placeholders if sh.placeholder_format.idx == 1)
p0 = body23.text_frame.paragraphs[0]
if p0.runs:
    p0.runs[0].text = '4차 정규화 | 두 목록을 한 표로 펼치는 두 가지 방법'
    for r in p0.runs[1:]:
        r.text = ''
for sh in s23.shapes:
    if sh.has_text_frame:
        for p in sh.text_frame.paragraphs:
            for r in p.runs:
                r.text = r.text.replace('(4차 정규화, 25~26쪽)', '(4차 정규화, 25쪽)')
notes_replace(s23, [('25~26쪽처럼', '25쪽처럼'), ('24쪽 이상 현상, 25~26쪽 분리', '24쪽 이상 현상, 25쪽 분리')])

# ── 25쪽 재구성
for sh in list(s25.shapes):
    sh._element.getparent().remove(sh._element)
for src_sh in s24.placeholders:                          # 24쪽 제목·머리글 placeholder 복제 → 같은 디자인
    s25.shapes._spTree.append(copy.deepcopy(src_sh._element))
ph = {p.placeholder_format.idx: p for p in s25.placeholders}
hdr = ph[1].text_frame.paragraphs[0]
hdr.runs[0].text = '4차 정규화 | 두 표로 분리하면 이상이 사라진다'
for r in hdr.runs[1:]:
    r.text = ''


def named(sh, n):
    sh.name = f'{TAG}_{n}'
    return sh


def tb(n, x, y, w, h, lines, size=12, color=NAVY, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    t = named(s25.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)), n)
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


def table(n, x, y, w, rows, colw):
    gf = named(s25.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y), Inches(w), Inches(0.36 * len(rows))), n)
    t = gf.table
    for j, cw in enumerate(colw):
        t.columns[j].width = Inches(cw)
    for i, row in enumerate(rows):
        t.rows[i].height = Inches(0.36)
        for j, v in enumerate(row):
            c = t.cell(i, j); c.text = v; c.vertical_anchor = MSO_ANCHOR.MIDDLE
            c.fill.solid(); c.fill.fore_color.rgb = RGB(NAVY if i == 0 else ('FFFFFF' if i % 2 else 'EEF3F9'))
            p = c.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
            r = p.runs[0]; r.font.size = Pt(13); r.font.name = FONT; r.font.bold = (i == 0)
            r.font.color.rgb = RGB('FFFFFF' if i == 0 else '262626')
    return gf


tb('l1', 1.05, 2.2, 4.6, 0.4, [[('보유기술 · 2행', {'bold': True, 'size': 16}), ('   PK (사원번호, 기술코드)', {'size': 11, 'color': '5A5A5A'})]])
table('t1', 1.05, 2.62, 4.52, [('사원번호', '기술코드'), ('10', 'Modeling'), ('10', 'DBA')], (2.0, 2.52))
tb('l2', 1.05, 3.85, 4.6, 0.4, [[('지원프로젝트 · 3행', {'bold': True, 'size': 16}), ('   PK (사원번호, 프로젝트코드)', {'size': 11, 'color': '5A5A5A'})]])
table('t2', 1.05, 4.27, 4.52, [('사원번호', '프로젝트코드'), ('10', 'SI'), ('10', 'OO'), ('10', 'PA')], (2.0, 2.52))

CARDS = [('E2EFFA', '입력 → 해결', '새 프로젝트 P04 등록', '→ 지원프로젝트에 1행만 추가 (기술과 조합 불필요)'),
         ('FFF0BF', '수정 → 해결', '프로젝트 코드 SI를 SI2로 정정', '→ 지원프로젝트의 1행만 수정'),
         ('FCE5E4', '삭제 → 해결', '마지막 프로젝트 PA를 삭제', '→ 보유기술(Modeling·DBA)은 그대로 남음')]
y = 2.31
for i, (fill, head, a, b) in enumerate(CARDS):
    c = named(s25.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.02), Inches(y), Inches(6.26), Inches(1.09)), f'card{i}')
    c.fill.solid(); c.fill.fore_color.rgb = RGB(fill); c.line.fill.background(); c.shadow.inherit = False
    tf = c.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    for k, (t, sz, bd) in enumerate([(head, 17, True), (a, 12.5, False), (b, 12.5, False)]):
        p = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.CENTER if k == 0 else PP_ALIGN.LEFT
        r = p.add_run(); r.text = t; r.font.size = Pt(sz); r.font.bold = bd; r.font.color.rgb = RGB(NAVY); r.font.name = FONT
    y += 1.21

tb('bottom', 1.05, 6.02, 11.23, 0.55, [[('사원번호 ↠ 기술코드, 사원번호 ↠ 프로젝트코드', {'bold': True}),
                                       ('를 각각의 표로 분리 = 4차 정규화 · 두 표를 사원번호로 JOIN하면 24쪽의 6행이 그대로 복원됩니다', {})]],
   size=13, color=NAVY2)
tb('foot', 1.05, 6.62, 10.4, 0.28, ['※ PK: Primary Key (기본키) · JOIN: 키로 두 표의 행을 연결 · ↠: 다치 종속(MVD: Multivalued Dependency)'],
   size=9.5, color='3A445C')

s25.notes_slide.notes_text_frame.text = (
    '【슬라이드 핵심】 24쪽의 이상 현상은 서로 독립인 두 목록을 한 표에 넣었기 때문이다. 보유기술(사원번호, 기술코드)과 지원프로젝트(사원번호, 프로젝트코드)로 나누면 입력·수정·삭제 이상이 모두 사라진다. 이것이 4차 정규화다.\n'
    '【강의 설명】 24쪽과 같은 사원 10을 그대로 쓴다. 보유기술 표는 2행(Modeling, DBA), 지원프로젝트 표는 3행(SI, OO, PA)이다. '
    '파란 카드: 새 프로젝트 P04는 지원프로젝트에 1행만 넣으면 된다(24쪽에서는 기술 수만큼 2행). '
    '노란 카드: SI를 SI2로 바꾸는 일은 1행 수정으로 끝나 불일치가 생기지 않는다. '
    '빨간 카드: 마지막 프로젝트 PA를 지워도 보유기술 표의 Modeling·DBA는 남는다. '
    '각 표의 기본키는 (사원번호, 기술코드), (사원번호, 프로젝트코드)인 복합키다. 두 표를 사원번호로 JOIN하면 24쪽의 6개 조합이 정확히 다시 만들어지므로 정보 손실이 없다(무손실 분해). '
    '마지막으로 “그런데 사원 10이 PA 프로젝트에서 실제로 어떤 기술을 썼는지는 어디에 기록할까?”라고 물어 27쪽 응용(세 값이 함께 의미를 갖는 지원내역)으로 넘어간다.\n'
    '【연결】 22쪽 도입, 23쪽 한 표로 펼치는 두 방법, 24쪽 이상 현상, 27쪽 4차 정규화의 응용\n'
    '【출처】 11-2 정규화 교안 22~27쪽 사원·기술·프로젝트 예제 재구성')
prs.save(out)
print('ok')
