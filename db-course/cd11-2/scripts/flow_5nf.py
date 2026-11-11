"""11-2 정규화(26) 5차 정규화(28~30쪽)를 4차 정규화(22~25쪽)와 같은 패턴으로 정리.
예시: 27쪽(Codex) 지원내역 = 사원 10·20의 '프로젝트별 실제 사용 기술' 6행.
  두 열씩 세 표(사원–프로젝트, 사원–기술, 프로젝트–기술)로 나눈 뒤 JOIN → 7행, 원본에 없던 (10, PA, DBA)가 생김
  → 27쪽 'PA의 DBA 경험자' 조회에 사원 10이 잘못 끼는 문제와 같은 원인 → 지원내역은 나누지 않는다(이미 5NF)
 - 28쪽(숨김 유지) ① 세 표로 나눠 보기 / 29쪽(숨김 유지) ② JOIN 결과와 판단 / 30쪽(보이는 쪽) 한 장 요약
 - 디자인: 24·25쪽과 같은 제목 자리·머리글(placeholder 복제), 표, 파랑·노랑·빨강 카드, 맑은 고딕
python flow_5nf.py <in.pptx> <out.pptx>"""
import sys, copy
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

src, out = sys.argv[1:3]
prs = Presentation(src)
RGB = lambda h: RGBColor.from_string(h)
NAVY, NAVY2, FONT, GRAY = '172B45', '0F3154', '맑은 고딕', '5A5A5A'
BLUE, YELLOW, PINK, RED = 'E2EFFA', 'FFF0BF', 'FCE5E4', 'C00000'

# ── 데이터와 검증
R = [('10', 'SI', 'Modeling'), ('10', 'SI', 'DBA'), ('10', 'PA', 'Modeling'), ('10', 'OO', 'DBA'), ('20', 'PA', 'DBA'), ('20', 'PA', 'XML')]
SP = sorted({(e, p) for e, p, k in R}); SK = sorted({(e, k) for e, p, k in R}); PK = sorted({(p, k) for e, p, k in R})
J = sorted({(e, p, k) for e, p in SP for e2, k in SK if e == e2 and (p, k) in PK}, key=lambda r: (r[0], ['SI', 'PA', 'OO'].index(r[1]), r[2]))
EXTRA = [j for j in J if j not in R]
assert len(J) == 7 and EXTRA == [('10', 'PA', 'DBA')], (J, EXTRA)


def txt(sl):
    return ' '.join(sh.text_frame.text for sh in sl.shapes if sh.has_text_frame)


def tagged(sl, tag):
    return any(sh.name.startswith(tag) for sh in sl.shapes)


S = list(prs.slides)
ref = next(sl for sl in S if '4차 정규화 | 두 표로 분리하면 이상이 사라진다' in txt(sl) or '4차 정규화 | 한 표에 두 목록을 담을 때 생기는 이상' in txt(sl))
s28 = next(sl for sl in S if '5차 정규화 ① | 무손실 분해를 확인하는 법' in txt(sl) or tagged(sl, 'cd112_5nf28'))
s29 = next(sl for sl in S if '5차 정규화 ② | 반례와 5NF 판단 기준' in txt(sl) or tagged(sl, 'cd112_5nf29'))
s30 = next(sl for sl in S if '5차 정규화 | 지원내역을 표로 분해해 보기' in txt(sl) or tagged(sl, 'cd112_5nf30'))


class Page:
    def __init__(self, sl, tag, header):
        self.s, self.tag = sl, tag
        for sh in list(sl.shapes):
            sh._element.getparent().remove(sh._element)
        for ph in ref.placeholders:                     # 24·25쪽 제목·머리글 자리 복제
            sl.shapes._spTree.append(copy.deepcopy(ph._element))
        p = {x.placeholder_format.idx: x for x in sl.placeholders}
        hp = p[1].text_frame.paragraphs[0]
        hp.runs[0].text = header
        for r in hp.runs[1:]:
            r.text = ''
        for extra in p[1].text_frame.paragraphs[1:]:
            extra._p.getparent().remove(extra._p)

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

    def table(self, n, x, y, header, rows, colw, rh=0.3, size=11.5, hl=None):
        gf = self.named(self.s.shapes.add_table(len(rows) + 1, len(header), Inches(x), Inches(y), Inches(sum(colw)), Inches(rh * (len(rows) + 1))), n)
        t = gf.table
        for j, cw in enumerate(colw):
            t.columns[j].width = Inches(cw)
        for i, row in enumerate([header] + list(rows)):
            t.rows[i].height = Inches(rh)
            for j, v in enumerate(row):
                c = t.cell(i, j); c.text = v; c.vertical_anchor = MSO_ANCHOR.MIDDLE
                c.margin_top = c.margin_bottom = Inches(0.01)
                fill = NAVY if i == 0 else ((hl or {}).get(tuple(row)) or ('FFFFFF' if i % 2 else 'EEF3F9'))
                c.fill.solid(); c.fill.fore_color.rgb = RGB(fill)
                p = c.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
                r = p.runs[0]; r.font.size = Pt(size); r.font.name = FONT; r.font.bold = (i == 0) or (hl and tuple(row) in hl)
                r.font.color.rgb = RGB('FFFFFF' if i == 0 else (RED if hl and tuple(row) in hl else '262626'))
        return gf

    def card(self, n, x, y, w, h, fill, lines, head_size=15, size=11.5):
        c = self.named(self.s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h)), n)
        c.fill.solid(); c.fill.fore_color.rgb = RGB(fill); c.line.fill.background(); c.shadow.inherit = False
        tf = c.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        for m in ('margin_left', 'margin_right'):
            setattr(tf, m, Inches(0.12))
        for k, ln in enumerate(lines):
            p = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
            p.alignment = PP_ALIGN.CENTER if k == 0 else PP_ALIGN.LEFT; p.space_after = Pt(2)
            runs = ln if isinstance(ln, list) else [ln]
            for rr in runs:
                t, kw = (rr, {}) if isinstance(rr, str) else rr
                r = p.add_run(); r.text = t; r.font.name = FONT
                r.font.size = Pt(kw.get('size', head_size if k == 0 else size)); r.font.bold = kw.get('bold', k == 0)
                r.font.color.rgb = RGB(kw.get('color', NAVY))
        return c

    def arrow(self, n, x, y, w=0.4, h=0.32, kind=MSO_SHAPE.RIGHT_ARROW):
        a = self.named(self.s.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h)), n)
        a.fill.solid(); a.fill.fore_color.rgb = RGB('7F7F7F'); a.line.fill.background(); a.shadow.inherit = False

    def foot(self, text, y=6.66):
        self.tb('foot', 1.05, y, 10.4, 0.28, [text], size=9.5, color='3A445C')

    def notes(self, text):
        self.s.notes_slide.notes_text_frame.text = text


HDR = ('사원번호', '프로젝트코드', '기술코드')
ORIG = '지원내역 · 실제 사용 6행 (27쪽)'
FOOT = '※ 5NF: Fifth Normal Form (제5정규형) · 무손실 분해: 나눈 표를 JOIN하면 원본이 그대로 복원 · JD: Join Dependency (조인 종속)'

# ───────── 28쪽 ① 세 표로 나눠 보기
p = Page(s28, 'cd112_5nf28', '5차 정규화 ① | 지원내역을 두 열씩 세 표로 나눠 보기')
p.tb('l0', 1.05, 2.2, 4.6, 0.4, [(ORIG, {'bold': True, 'size': 15})])
p.table('t0', 1.05, 2.62, HDR, R, (1.4, 1.6, 1.52), rh=0.34, size=12)
p.arrow('a0', 5.75, 3.6)
for i, (lab, hdr, rows, x) in enumerate([('사원–프로젝트 · 4행', ('사원', '프로젝트'), SP, 6.3),
                                          ('사원–기술 · 4행', ('사원', '기술'), SK, 8.33),
                                          ('프로젝트–기술 · 6행', ('프로젝트', '기술'), PK, 10.36)]):
    p.tb(f'l{i+1}', x, 2.2, 2.0, 0.4, [(lab, {'bold': True, 'size': 12})])
    p.table(f't{i+1}', x, 2.62, hdr, rows, (0.95, 0.98), rh=0.3, size=11)
p.card('q', 1.05, 5.25, 11.23, 0.72, YELLOW, [[('질문 · ', {'bold': True, 'size': 14}),
                                                ('세 표를 다시 JOIN하면 원본 6행이 그대로 나올까? → 다음 쪽', {'bold': False, 'size': 14})]])
p.tb('bottom', 1.05, 6.05, 11.23, 0.5, [[('각 표는 원본에서 두 열을 골라 중복을 지운 것 ', {'bold': True}),
                                         ('(4차 정규화처럼 사원번호 하나로는 나눌 수 없는, 세 값이 함께 하나의 사실인 표)', {})]], size=12.5, color=NAVY2)
p.foot(FOOT)
p.notes('【슬라이드 핵심】 27쪽 지원내역(사원·프로젝트·기술 = 프로젝트별 실제 사용 기술)을 두 열씩 세 표로 나눠 본다. 나눈 표를 다시 JOIN했을 때 원본이 그대로 나오면 나눌 수 있고, 아니면 나누면 안 된다.\n'
        '【강의 설명】 사원–프로젝트는 4행, 사원–기술은 4행, 프로젝트–기술은 6행이다. 각 표는 원본에서 두 열만 골라 중복을 지운 것이다. '
        '4차 정규화(25쪽)에서는 사원번호 하나가 두 목록을 독립적으로 결정해 두 표로 나눌 수 있었다. 여기서는 “사원 10이 PA에서 Modeling을 썼다”처럼 세 값이 함께 하나의 사실이다. '
        '학생에게 세 표를 다시 JOIN하면 몇 행이 나올지 예상하게 하고 다음 쪽에서 확인한다.\n'
        '【연결】 27쪽 4차 정규화 응용(실제 사용 기술), 29쪽 JOIN 결과, 30쪽 요약\n'
        '【출처】 11-2 정규화 교안 27~30쪽 사원·기술·프로젝트 예제 재구성')

# ───────── 29쪽 ② JOIN 결과와 판단
p = Page(s29, 'cd112_5nf29', '5차 정규화 ② | 다시 JOIN하면 원본에 없던 행이 생긴다')
p.tb('l0', 1.05, 2.2, 4.8, 0.4, [[('세 표 JOIN 결과 · 7행', {'bold': True, 'size': 15}), ('  (원본 6행 + 1행)', {'size': 11, 'color': GRAY})]])
p.table('t0', 1.05, 2.62, HDR, J, (1.4, 1.6, 1.52), rh=0.34, size=12, hl={EXTRA[0]: PINK})
p.card('c1', 6.02, 2.31, 6.26, 1.09, BLUE, ['어떻게 생겼나',
                                            '사원–프로젝트 (10, PA) + 사원–기술 (10, DBA)',
                                            '+ 프로젝트–기술 (PA, DBA) ← 사원 20의 기록 → (10, PA, DBA)'], size=11)
p.card('c2', 6.02, 3.52, 6.26, 1.09, YELLOW, ['무슨 문제인가',
                                              '사원 10은 PA에서 DBA를 쓴 적이 없다 (원본은 Modeling)',
                                              '→ 27쪽 ‘PA의 DBA 경험자’ 조회에 사원 10이 잘못 포함'], size=11)
p.card('c3', 6.02, 4.73, 6.26, 1.09, PINK, ['판단',
                                            '가짜 행이 한 번이라도 생기면 손실 분해 → 나누면 안 된다',
                                            '→ 지원내역(사원, 프로젝트, 기술)을 한 표로 유지 = 5NF'], size=11)
p.tb('bottom', 1.05, 6.02, 11.23, 0.55, [[('5NF 판단 기준 · ', {'bold': True}),
                                          ('업무 규칙상 모든 유효한 데이터에서 JOIN이 원본과 같을 때(조인 종속)만 나눈다. 예제 한 번 맞는 것으로는 부족하다.', {})]],
   size=12.5, color=NAVY2)
p.foot(FOOT)
p.notes('【슬라이드 핵심】 28쪽의 세 표를 JOIN하면 7행이 나오고, 원본에 없던 (10, PA, DBA)가 생긴다. 이런 분해는 정보를 잃는(가짜 정보를 만드는) 손실 분해이므로, 지원내역은 세 값을 한 행에 함께 둔 채 유지한다. 이 상태가 5NF다.\n'
        '【강의 설명】 사원–프로젝트의 (10, PA), 사원–기술의 (10, DBA), 그리고 사원 20의 기록에서 나온 프로젝트–기술 (PA, DBA)가 연결되어 (10, PA, DBA)가 만들어진다. '
        '원본에서 사원 10이 PA에서 쓴 기술은 Modeling뿐이다. 27쪽에서 “PA 프로젝트의 DBA 경험자”를 찾을 때 사원 10이 잘못 끼는 문제와 같은 원인이다. '
        '5NF는 비자명한 조인 종속이 모두 후보키에서 나올 때 성립한다. 실무에서는 “업무 규칙상 세 표로 나눠도 항상 원본이 복원되는가?”를 묻고, 한 번이라도 가짜 행이 생기면 나누지 않는다. '
        '예제 한 번 결과가 맞았다고 조인 종속이 성립하는 것은 아니라는 점도 짚는다.\n'
        '【연결】 28쪽 세 표로 나누기, 27쪽 PA의 DBA 경험자 조회, 30쪽 요약, 이후 Colab 실습(4NF → 5NF)\n'
        '【출처】 11-2 정규화 교안 27~30쪽 사원·기술·프로젝트 예제 재구성')

# ───────── 30쪽 (보이는 쪽) 한 장 요약
p = Page(s30, 'cd112_5nf30', '5차 정규화 | 지원내역을 세 표로 나누면 가짜 행이 생긴다')
p.tb('l0', 1.05, 2.2, 4.6, 0.4, [(ORIG, {'bold': True, 'size': 15})])
p.table('t0', 1.05, 2.62, HDR, R, (1.3, 1.5, 1.42), rh=0.32, size=11.5)
mid = p.card('mid', 5.42, 2.95, 1.75, 1.6, 'EEF3F9', [('두 열씩', {'size': 12}), ('세 표로 나눈 뒤', {'size': 11, 'bold': False}),
                                                     ('다시 JOIN', {'size': 11, 'bold': False})])
p.arrow('a0', 5.08, 3.6, 0.3, 0.3); p.arrow('a1', 7.2, 3.6, 0.3, 0.3)
for para in mid.text_frame.paragraphs:
    para.alignment = PP_ALIGN.CENTER
p.tb('l1', 7.55, 2.2, 4.8, 0.4, [[('JOIN 결과 · 7행', {'bold': True, 'size': 15}), ('  빨간 행은 원본에 없음', {'size': 11, 'color': RED})]])
p.table('t1', 7.55, 2.62, HDR, J, (1.3, 1.5, 1.42), rh=0.32, size=11.5, hl={EXTRA[0]: PINK})
p.card('c1', 1.05, 5.3, 3.62, 0.95, BLUE, ['어떻게?', '(10, PA) + (10, DBA) + 사원 20의 (PA, DBA)'], head_size=13, size=10.5)
p.card('c2', 4.85, 5.3, 3.62, 0.95, YELLOW, ['문제 (27쪽)', '사원 10이 PA에서 DBA를 쓴 것처럼 보임'], head_size=13, size=10.5)
p.card('c3', 8.65, 5.3, 3.62, 0.95, PINK, ['결론', '나누지 않고 한 표로 유지 = 5NF'], head_size=13, size=10.5)
p.tb('bottom', 1.05, 6.3, 11.23, 0.35, [[('JOIN해도 원본이 그대로 복원될 때만 나눈다', {'bold': True}),
                                         (' · 세 값이 함께 하나의 사실이면 한 표가 정답', {})]], size=12.5, color=NAVY2)
p.foot(FOOT, y=6.7)
p.notes('【슬라이드 핵심】 지원내역(사원·프로젝트·기술)을 두 열씩 세 표로 나눴다가 다시 JOIN하면 원본 6행이 아니라 7행이 나오고, 원본에 없던 (10, PA, DBA)가 생긴다. 그래서 이 표는 나누지 않는다. 이미 5NF다.\n'
        '【강의 설명】 27쪽의 실제 사용 기록 6행을 그대로 쓴다. 사원–프로젝트·사원–기술·프로젝트–기술 세 표로 나누면(자세한 표는 28쪽) 각 표만 보면 틀린 곳이 없다. '
        '그러나 세 표를 JOIN하면 사원 10의 (10, PA)·(10, DBA)와 사원 20에게서 나온 (PA, DBA)가 연결되어 (10, PA, DBA)가 만들어진다. '
        '27쪽의 “PA의 DBA 경험자” 조회에서 사원 10이 잘못 끼는 문제와 같다. 4차 정규화(25쪽)는 JOIN하면 원본 6행이 그대로 복원되어 나눌 수 있었지만, 여기서는 복원되지 않으므로 나누면 안 된다. '
        '5NF는 “JOIN해도 항상 원본이 복원되는 경우에만 나눈다(조인 종속)”는 기준이며, 세 값이 함께 하나의 사실이면 한 표로 두는 것이 정답이다. 28·29쪽은 이 과정을 두 장으로 자세히 보여 준다(현재 숨김).\n'
        '【연결】 25쪽 4차 정규화(무손실 분해 성공), 27쪽 응용, 28·29쪽 상세(숨김), 31쪽 Colab 실습\n'
        '【출처】 11-2 정규화 교안 27~30쪽 사원·기술·프로젝트 예제 재구성')

prs.save(out)
print('ok · JOIN', len(J), '행, 가짜 행', EXTRA)
