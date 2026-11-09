"""11-3 교안 ↔ Colab 미션 연결: 미션 버튼, Colab·마무리 페이지 갱신, 미션 정답 2장, 약어 주석 보강.
python deck_missions.py <build.py 결과 pptx> <출력 pptx>"""
import copy, sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

NAVY, BLUE, TXT = RGBColor(0x10, 0x29, 0x50), RGBColor(0x21, 0x56, 0x9A), RGBColor(0x1A, 0x23, 0x32)
YEL, SKY, WHITE = RGBColor(0xFF, 0xF3, 0xD9), RGBColor(0xED, 0xF4, 0xFD), RGBColor(0xFF, 0xFF, 0xFF)
FONT, MONO = 'Malgun Gothic', 'Courier New'
NB = 'https://colab.research.google.com/drive/1mJEtXxBEUK9THq9pVF607BVqO_vDO5Qg'
A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'

prs = Presentation(sys.argv[1])
S = lambda n: prs.slides[n - 1]
LAYOUT = next(l for l in prs.slide_layouts if l.name == '제목 및 내용')


def run(p, text, size, bold=False, color=TXT, font=FONT, link=None):
    r = p.add_run(); r.text = text
    r.font.size = Pt(size); r.font.bold = bold; r.font.name = font; r.font.color.rgb = color
    if link:
        r.hyperlink.address = link
    return r


def textbox(s, x, y, w, h, lines, size=16, bold=True, color=BLUE):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf = tb.text_frame; tf.word_wrap = True
    for i, ln in enumerate(lines if isinstance(lines, list) else [lines]):
        run(tf.paragraphs[0] if i == 0 else tf.add_paragraph(), ln, size, bold, color)
    return tb


def card(s, x, y, w, h, title, lines, fill=SKY, tsize=15, bsize=12, mono=False):
    b = s.shapes.add_shape(1, Inches(x), Inches(y), Inches(w), Inches(h))
    b.fill.solid(); b.fill.fore_color.rgb = fill; b.line.fill.background(); b.shadow.inherit = False
    tf = b.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.TOP
    tf.margin_left = tf.margin_right = Inches(0.15); tf.margin_top = Inches(0.08)
    tf.paragraphs[0].alignment = 1
    run(tf.paragraphs[0], title, tsize, True, NAVY)
    for ln in lines:
        p = tf.add_paragraph(); p.space_before = Pt(2); p.alignment = 1
        run(p, ln, bsize, False, TXT, MONO if mono and not ln.startswith('→') else FONT)
    return b


def table(s, x, y, widths, rows, size=12, rh=0.34):
    t = s.shapes.add_table(len(rows), len(widths), Inches(x), Inches(y), Inches(sum(widths)), Inches(rh * len(rows))).table
    for j, w in enumerate(widths):
        t.columns[j].width = Inches(w)
    for i, row in enumerate(rows):
        t.rows[i].height = Inches(rh)
        for j, v in enumerate(row):
            c = t.cell(i, j); c.fill.solid(); c.fill.fore_color.rgb = NAVY if i == 0 else SKY
            c.margin_left = c.margin_right = Inches(0.08); c.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = c.text_frame.paragraphs[0]; p.text = ''
            run(p, str(v), size, i == 0, WHITE if i == 0 else TXT)


def badge(s, label, anchor):
    b = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(9.15), Inches(6.36), Inches(3.1), Inches(0.42))
    b.name = 'Colab 미션 버튼'
    b.fill.solid(); b.fill.fore_color.rgb = NAVY; b.line.fill.background(); b.shadow.inherit = False
    tf = b.text_frame; tf.margin_top = tf.margin_bottom = Inches(0.02); tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = 2
    run(p, label, 12.5, True, WHITE, link=f'{NB}#scrollTo={anchor}')
    b.click_action.hyperlink.address = f'{NB}#scrollTo={anchor}'


def footnote(s, lines, dark=False):
    h = 0.17 * len(lines) + 0.05
    tb = textbox(s, 0.95, 7.5 - h - 0.12, 10.8, h, ['※ ' + x for x in lines], 10.5, False,
                 RGBColor(0xDD, 0xE6, 0xF5) if dark else RGBColor(0x3A, 0x44, 0x5C))
    tb.name = '약어 주석'


def has_fn(s):
    return any(sh.has_text_frame and sh.text_frame.text.lstrip().startswith('※') for sh in s.shapes)


def set_card_body(s, title_start, body):
    for sh in s.shapes:
        if sh.has_text_frame and sh.text_frame.text.startswith(title_start):
            ps = sh.text_frame.paragraphs
            ps[1].runs[0].text = body
            for r in ps[1].runs[1:]:
                r.text = ''
            return
    raise KeyError(title_start)


# 1) 실습 페이지 ↔ Colab 미션 버튼
for n, label, anchor in [(7, '🎯 Colab 미션 1 실행 ▶', 'mission_m1'), (8, '🎯 Colab 미션 2 실행 ▶', 'mission_m2'),
                         (9, '🎯 Colab 미션 3 실행 ▶', 'mission_m3'), (10, '🎯 Colab 미션 2 결과 비교 ▶', 'mission_m2'),
                         (14, '🎯 Colab 미션 5 실행 ▶', 'mission_m5'), (15, '🎯 Colab 미션 5 결과 비교 ▶', 'mission_m5'),
                         (17, '🎯 Colab 미션 4 실행 ▶', 'mission_m4'), (18, '📝 Colab 과제 실행 ▶', 'mission_hw')]:
    badge(S(n), label, anchor)

# 2) Colab 페이지(16): 따라하기 + 미션 구조로
s16 = S(16)
for sh in s16.shapes:
    if sh.has_text_frame and sh.text_frame.text.startswith('Colab에 내장된 SQLite'):
        sh.text_frame.paragraphs[0].runs[0].text = '교안의 🎯 버튼 ↔ 노트북의 🎯 미션 셀이 짝입니다. 빈칸을 채워 실행하면 ✅/❌로 바로 확인합니다.'
set_card_body(s16, '① 테이블 만들기', '따라하기 1 → 미션 1 (영수증 값 → 개체) · 미션 2 (PK·FK 빈칸 채우기)  ↔ 교안 7·8·10쪽')
set_card_body(s16, '② JOIN 출력', '따라하기 2 → 미션 3 (합계·부가세를 계산으로 구하기)  ↔ 교안 9쪽')
set_card_body(s16, '③ 수정 비교', '따라하기 3 → 미션 4 (카드+현금 나눠 낸 결제 저장)  ↔ 교안 17쪽')
set_card_body(s16, '④ 상담 카드', '따라하기 4 → 미션 5 (다중 선택 + GROUP BY) → 📝 과제 (회원·포인트 확장)  ↔ 교안 14·15·18쪽')

# 3) 실습 마무리(18): 제출물
set_card_body(S(18), '제출', '미션 1~5의 ✅ 결과 화면 + 📝 과제(회원·포인트 확장) SQL과 ✅ 화면 캡처')

# 4) 미션 정답 2장 (마무리 다음, SUMMARY 앞)
def new_slide(title, lead):
    s = prs.slides.add_slide(LAYOUT)
    for ph in list(s.placeholders):
        ph._element.getparent().remove(ph._element)
    textbox(s, 1.25, 0.72, 11.3, 0.64, title, 28, True, NAVY)
    textbox(s, 0.95, 1.42, 11.45, 0.57, lead, 16, True, BLUE)
    return s


a1 = new_slide('미션 정답 ① | 실습1 · 미션 1·2·3', 'Colab에서 ❌가 나오면 이 페이지와 비교하세요. 표 이름보다 키(PK·FK)가 맞는지가 중요합니다.')
textbox(a1, 1.05, 2.0, 4.6, 0.4, '미션 1 · 영수증 값 → 개체', 15, True, NAVY)
table(a1, 1.05, 2.42, [3.05, 1.55], [('영수증 값', '개체'), ('대기번호 241', '주문'), ('사업자번호 105-87-51367', '매장'),
      ('(ICE)아메리카노 2,000×2', '주문상세'), ('승인번호 21091497', '결제'), ('부가세 500', '계산값')], 12, 0.36)
card(a1, 5.95, 2.0, 6.3, 2.2, '미션 2 · PK·FK 빈칸', ['order_id TEXT REFERENCES orders(order_id),', 'menu_id  TEXT REFERENCES menu(menu_id),',
     'PRIMARY KEY (order_id, menu_id)', 'payments: order_id ... REFERENCES orders(order_id)',
     '→ 주문상세는 두 키를 합친 복합 PK, 결제는 주문을 가리킨다'], SKY, 15, 12, True)
card(a1, 5.95, 4.35, 6.3, 1.45, '미션 3 · 계산으로 구하기', ['SUM(m.unit_price * i.qty)       AS total', 'SUM(m.unit_price * i.qty) / 11  AS vat',
     '→ 합계 5,500 · 부가세 500 (영수증과 일치)'], YEL, 15, 12, True)
a1.notes_slide.notes_text_frame.text = (
    "【슬라이드 핵심】 미션 1·2·3 정답.\n【강의 설명】 미션 1에서 '부가세'를 주문으로 답해도 이해한 것이지만, 저장하지 않고 계산하는 값이라는 점을 짚어 줍니다. "
    "미션 2의 핵심은 order_items의 PK가 한 열이 아니라 (order_id, menu_id) 두 열이라는 것입니다. 미션 3에서 SQLite의 정수 나눗셈이라 5500/11 = 500이 됩니다.")

a2 = new_slide('미션 정답 ② | 검증·실습2·과제 · 미션 4·5·과제', '결제는 여러 행, 다중 선택은 연결 표, 확장은 새 표와 FK로 해결합니다.')
card(a2, 1.05, 2.0, 5.45, 1.75, '미션 4 · 나눠 낸 결제', ["('P02','B0001','카드', ..., 3000)", "('P03','B0001','현금', NULL, NULL, 2500)",
     '→ 결제 2행 · 합계 5,500 = 주문 합계'], SKY, 15, 12, True)
card(a2, 6.8, 2.0, 5.45, 1.75, '미션 5 · 다중 선택 + GROUP BY', ["INSERT ... VALUES ('C001', 'F4')", 'GROUP BY f.field_name',
     '→ 어학연수 1 · 대학(학사) 1 · 대학(석사) 1'], SKY, 15, 12, True)
card(a2, 1.05, 3.9, 11.2, 1.85, '📝 과제 · 회원·포인트 확장', [
     'CREATE TABLE members (member_id TEXT PRIMARY KEY, card_no TEXT, points INTEGER);',
     'CREATE TABLE point_logs (order_id TEXT REFERENCES orders(order_id), member_id TEXT REFERENCES members(member_id),',
     '                         earned INTEGER, PRIMARY KEY (order_id, member_id));',
     "INSERT INTO members VALUES ('CJ5505','010****5505',384);  INSERT INTO point_logs VALUES ('B0001','CJ5505',28);"], YEL, 15, 11, True)
textbox(a2, 1.05, 5.9, 11.2, 0.45, '채점 기준 · 모든 표에 PK가 있는가 · FK가 올바른 표를 가리키는가 · 같은 값이 한 곳에만 저장되는가', 14, True, NAVY)
a2.notes_slide.notes_text_frame.text = (
    "【슬라이드 핵심】 미션 4·5와 과제 정답.\n【강의 설명】 미션 4는 결제를 주문의 열이 아니라 별도 표(주문 1:N 결제)로 둔 설계 덕분에 가능합니다. "
    "미션 5는 체크박스 다중 선택을 연결 표로 둔 덕분에 GROUP BY로 바로 셉니다. 과제는 회원 1:N 포인트적립, 주문 1:N 포인트적립 구조이며, "
    "열 이름이 달라도 PK·FK 구조가 같으면 정답으로 인정합니다.")

sld = prs.slides._sldIdLst
ids = list(sld)
new = ids[-2:]
for el in new:
    sld.remove(el)
for k, el in enumerate(new):
    sld.insert(18 + k, el)                 # 18번(실습 마무리) 다음 → 19·20번

# 5) 약어 주석 보강 (이미 '※'가 있는 페이지는 건너뜀) — 정답 2장 삽입 후 번호 기준
FN = {
    9: ['Σ(시그마): 모두 더한다는 기호 · 부가세(VAT): Value Added Tax, 판매가에 포함된 10% 세금'],
    10: ['PK: Primary Key (기본키) · FK: Foreign Key (외래키)'],
    13: ['PK: Primary Key (기본키) · 1:N: 일대다 관계 (학생 1명이 상담 여러 번)'],
    17: ['JOIN: 키로 두 표의 행을 연결하는 SQL 연산 · 부가세(VAT): Value Added Tax'],
    18: ['1NF·2NF·3NF: 제1·2·3정규형 (11-2에서 학습) · N:M: 다대다 관계'],
    19: ['DDL: Data Definition Language (CREATE TABLE처럼 구조를 정의하는 SQL) · PK·FK: 기본키·외래키'],
    20: ['GROUP BY: 같은 값끼리 묶어 집계 · NULL: 값이 없음 (현금 결제는 카드사·승인번호가 없음)'],
}
for n, lines in FN.items():
    if not has_fn(S(n)):
        footnote(S(n), lines)
if not has_fn(S(21)):
    footnote(S(21), ['1:N: 일대다 관계 · N:M: 다대다 관계 (연결 표로 표현)'], dark=True)

prs.save(sys.argv[2])
print('saved', sys.argv[2], len(prs.slides), 'slides')
