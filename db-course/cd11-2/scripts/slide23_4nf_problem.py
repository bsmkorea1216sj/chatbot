"""11-2 정규화(26) 23쪽(4차 정규화 · 여러 값을 중복 삽입해야 하는 종속성) 설명 보강.
22쪽(Codex: 사원 10 · 기술 2 × 프로젝트 3 = 6행)과 이어지도록 ①→②→③ 흐름으로 정리:
  ① 원래 정보(한 칸에 여러 값) — 기존 '사원기술' 표 유지
  ② 행 수를 줄이려 임의로 짝지음 — 기존 '지원내역' 표 유지, '거짓 짝' 설명으로 문구 교체
  ③ 모든 조합을 저장하면 6행 — 새 상자(22쪽 연결)
  결론 띠: 거짓 짝 아니면 조합 중복 → 두 표로 분리(25~26쪽)
기존 표·화살표는 그대로 두고 라벨·설명 문장만 바꾸며, 추가 도형은 이름 접두어로 관리(다시 실행 시 재생성).
python slide23_4nf_problem.py <in.pptx> <out.pptx>"""
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

src, out = sys.argv[1:3]
prs = Presentation(src)
RGB = lambda h: RGBColor.from_string(h)
P, RED, NAVY, TXT = '555FAB', 'C00000', '102950', '262626'
TAG = 'cd112_4nf23'

s = next(sl for sl in prs.slides if any(sh.has_text_frame and '여러 값을 중복적으로 삽입해야 하는 종속성을 제거' in sh.text_frame.text
                                        for sh in sl.shapes))
for sh in list(s.shapes):
    if sh.name.startswith(TAG):
        sh._element.getparent().remove(sh._element)


def by_start(prefixes):
    return next((sh for sh in s.shapes if sh.has_text_frame and sh.text_frame.text.strip().startswith(prefixes)), None)


def set_text(sh, lines, size=None, color=None, bold=None):
    """첫 문단 서식을 유지하며 문단을 lines로 교체"""
    tf = sh.text_frame
    first = tf.paragraphs[0]
    for p in tf.paragraphs[1:]:
        p._p.getparent().remove(p._p)
    for i, ln in enumerate(lines):
        p = first if i == 0 else tf.add_paragraph()
        runs = ln if isinstance(ln, list) else [ln]
        if i == 0:
            base = p.runs[0] if p.runs else p.add_run()
            for r in p.runs[1:]:
                r._r.getparent().remove(r._r)
        for j, rr in enumerate(runs):
            text, kw = (rr, {}) if isinstance(rr, str) else rr
            r = base if (i == 0 and j == 0) else p.add_run()
            r.text = text
            if size or kw.get('size'):
                r.font.size = Pt(kw.get('size', size))
            c = kw.get('color', color)
            if c:
                r.font.color.rgb = RGB(c)
            b = kw.get('bold', bold)
            if b is not None:
                r.font.bold = b
            r.font.name = 'Arial'


def named(sh, n):
    sh.name = f'{TAG}_{n}'
    return sh


def tb(n, x, y, w, h, lines, size=11, color=TXT, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    t = named(s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)), n)
    tf = t.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    for m in ('margin_left', 'margin_right', 'margin_top', 'margin_bottom'):
        setattr(tf, m, Inches(0.04))
    for i, ln in enumerate(lines):
        runs = ln if isinstance(ln, list) else [ln]
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.alignment = align; p.space_after = Pt(1)
        for rr in runs:
            text, kw = (rr, {}) if isinstance(rr, str) else rr
            r = p.add_run(); r.text = text
            r.font.size = Pt(kw.get('size', size)); r.font.bold = kw.get('bold', bold)
            r.font.color.rgb = RGB(kw.get('color', color)); r.font.name = 'Arial'
    return t


def box(n, x, y, w, h, fill, line=None, lw=1.25):
    b = named(s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h)), n)
    b.fill.solid(); b.fill.fore_color.rgb = RGB(fill)
    if line:
        b.line.color.rgb = RGB(line); b.line.width = Pt(lw)
    else:
        b.line.fill.background()
    b.shadow.inherit = False
    return b


# 기존 두 표: 글자 18→13pt, 행 높이 축소 (내용은 그대로)
for sh in s.shapes:
    if sh.has_table:
        for row in sh.table.rows:
            row.height = Inches(0.3)
            for c in row.cells:
                c.margin_top = c.margin_bottom = Inches(0.02)
                for pp in c.text_frame.paragraphs:
                    for r in pp.runs:
                        r.font.size = Pt(13)
        sh.top = Inches(3.3)

# 표 사이 화살표(기존)를 표 중간 높이로  # arrow_mid
for sh in s.shapes:
    if not sh.has_text_frame or sh.has_table:
        continue
    if sh.shape_type == 1 and not sh.text_frame.text.strip() and abs(sh.left - Inches(5.75)) < Inches(0.2):
        sh.top = Inches(3.62)

# ① ② 라벨 (기존 '사원기술'·'지원내역' 텍스트 상자)
lab1 = by_start(('사원기술', '①'))
lab2 = by_start(('지원내역', '②'))
if lab1 is not None:
    set_text(lab1, [[('① 원래 정보 ', {'bold': True}), ('· 한 칸에 여러 값', {'size': 11})]], size=13, color=P)
    lab1.width = Inches(4.6); lab1.top = Inches(2.62); lab1.left = Inches(0.64)
if lab2 is not None:
    set_text(lab2, [[('② 행 수를 줄이려 임의로 짝지음', {'bold': True})]], size=13, color=P)
    lab2.width = Inches(5.6); lab2.top = Inches(2.62); lab2.left = Inches(6.96)

# 빨간 설명(기존) → ②의 문제를 분명하게
red = by_start(('Modeling이라는 기술', '사원 10의 Modeling'))
if red is not None:
    set_text(red, ['사원 10의 Modeling–SI·OO, DBA–PA 짝 → 실제와 무관한 거짓 의미'], size=10, color=RED)
    red.left, red.top, red.width, red.height = Inches(6.96), Inches(2.9), Inches(5.6), Inches(0.42)
    for p_ in red.text_frame.paragraphs:                 # 원문 run의 자간(spc)·굵게 상속 제거
        for r_ in p_.runs:
            r_._r.get_or_add_rPr().attrib.pop('spc', None); r_.font.bold = False

# 아래 설명(기존 원문) → ③ 상자로 대체: 원문은 ②에 대한 설명이므로 짧게 정리해 유지
low = by_start(('데이터 수를 줄이기 위해', '빈칸을 임의의 값'))
if low is not None:
    set_text(low, [[('②는 ', {'bold': True}), '기술 수와 프로젝트 수가 달라 생기는 빈칸(Null)을 임의의 값으로 채운 결과입니다.']], size=10, color=P)
    low.left, low.top, low.width, low.height = Inches(6.96), Inches(5.2), Inches(5.6), Inches(0.42)

# ③ 모든 조합을 저장하면 (22쪽과 연결)
box('c3', 0.64, 5.68, 11.92, 0.58, 'FFF3D9', 'BF9000', 1)
tb('c3t', 0.75, 5.69, 11.7, 0.56, [
    [('③ 거짓 짝을 피하려면 모든 조합을 저장 ', {'bold': True, 'color': '7F6000'}),
     ('· 사원 10: Modeling×(SI·OO·PA) + DBA×(SI·OO·PA) = ', {}), ('6행', {'bold': True, 'color': RED}),
     ('  → 의미는 정확, 대신 기술 1개 추가에 프로젝트 수만큼 행 추가 (22쪽)', {})]], size=10.5, anchor=MSO_ANCHOR.MIDDLE)

# 결론 띠
bar = box('bar', 0.64, 6.33, 11.92, 0.44, NAVY)
tf = bar.text_frame; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
for t, c in [('독립된 두 목록을 한 표에 넣으면 ', 'FFFFFF'), ('② 거짓 짝', 'FFB4B4'), (' 아니면 ', 'FFFFFF'), ('③ 조합 중복', 'FFE699'),
             (' → 두 표로 분리 (4차 정규화, 25~26쪽)', 'FFFFFF')]:
    r = p.add_run(); r.text = t; r.font.size = Pt(13); r.font.bold = True; r.font.color.rgb = RGB(c); r.font.name = 'Arial'

tb('foot', 0.64, 6.82, 10.6, 0.3, ['※ 다치 종속(MVD: Multivalued Dependency): 사원번호 하나가 기술코드 여러 개와 프로젝트코드 여러 개를 서로 독립적으로 결정 (사원번호 ↠ 기술코드, 사원번호 ↠ 프로젝트코드)'],
   size=9, color='3A445C')

s.notes_slide.notes_text_frame.text = (
    '【슬라이드 핵심】 서로 독립인 두 목록(보유기술, 지원 프로젝트)을 한 표에 펼치는 방법은 둘뿐이다. 행 수를 줄이려 임의로 짝지으면 거짓 의미가 생기고(②), 거짓 짝을 피하려면 모든 조합을 저장해 중복이 생긴다(③). 그래서 4차 정규화로 두 표를 분리한다.\n'
    '【강의 설명】 ① 원래 정보는 사원 10이 Modeling·DBA 두 기술을 보유하고 SI·OO·PA 세 프로젝트를 지원했다는 것뿐이다. 두 목록 사이에는 아무 관계가 없다. '
    '② 한 칸에 한 값(1NF)으로 펼치면서 행 수를 줄이려고 기술 수와 프로젝트 수의 차이로 생기는 빈칸에 임의의 값을 채우면, (10, Modeling, SI)·(10, Modeling, OO)·(10, DBA, PA)처럼 실제와 무관한 짝이 생긴다. '
    '학생에게 “사원 10이 SI 프로젝트에서 DBA 기술을 썼나요?”라고 물으면 표만 보고는 답할 수 없다는 점을 확인시킨다. '
    '③ 거짓 짝을 피하려면 2 × 3 = 6행의 모든 조합을 저장해야 한다(22쪽). 의미는 정확하지만 기술 하나를 추가할 때 프로젝트 수만큼 행을 추가해야 하고, 이것이 다음 쪽의 입력·수정·삭제 이상으로 이어진다. '
    '사원번호 ↠ 기술코드, 사원번호 ↠ 프로젝트코드라는 두 다치 종속이 한 표에 섞인 것이 원인이므로, 25~26쪽처럼 보유기술(사원번호, 기술코드)과 지원프로젝트(사원번호, 프로젝트코드)로 분리한다.\n'
    '【연결】 22쪽 4차 정규화 도입(2×3=6행), 24쪽 이상 현상, 25~26쪽 분리, 27쪽 실제 사용 기술(세 값이 함께 의미를 갖는 경우)\n'
    '【출처】 11-2 정규화 원본 교안')
prs.save(out)
print('ok')
