"""11-1 보강본 12쪽: 'Meta Muse — 귀찮은 환불 신청을 대신하는 AI' 사례 (알렉산더 왕 사진 포함).
11쪽(데이터 모델링 개요) 다음에 넣고, 이미 있으면 같은 제목 슬라이드를 지우고 다시 만든다.
python slide_meta_muse.py <in.pptx> <out.pptx> <photo.jpg>
사진: Meta Platforms, Inc. 제공 공식 사진, Wikimedia Commons, CC BY-SA 4.0 (출처 표기 필수)"""
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

src, out, photo = sys.argv[1:4]
prs = Presentation(src)
RGB = lambda h: RGBColor.from_string(h)
TXT, SUB, NAVY, GREEN, ORANGE = RGB('262626'), RGB('5A5A5A'), RGB('1F4E79'), RGB('548235'), RGB('C55A11')
TITLE = '데이터 모델링 사례 · Meta Muse'
OLD_TITLES = {TITLE}

ids = prs.slides._sldIdLst
s = next((sl for sl in prs.slides if sl.shapes.title is not None
          and sl.shapes.title.text_frame.text.strip() in OLD_TITLES), None)
if s is None:                                           # 처음: 11쪽 레이아웃으로 새 슬라이드 → 12쪽 위치
    s = prs.slides.add_slide(prs.slides[10].slide_layout)
    el = ids[-1]; ids.remove(el); ids.insert(11, el)
for sh in list(s.shapes):                               # 다시 만들 때: 제목만 남기고 비움
    if not (sh.is_placeholder and sh.placeholder_format.idx == 0):
        sh._element.getparent().remove(sh._element)
s.shapes.title.text_frame.text = TITLE


def box(x, y, w, h, paras, size=12, color=TXT, bold=False, align=PP_ALIGN.LEFT, anchor=None, font='Malgun Gothic'):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    for m in ('margin_left', 'margin_right', 'margin_top', 'margin_bottom'):
        setattr(tf, m, Inches(0.03))
    if anchor:
        tf.vertical_anchor = anchor
    for i, p in enumerate(paras):
        text, kw = (p, {}) if isinstance(p, str) else p
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = kw.get('align', align); para.space_after = Pt(kw.get('after', 3))
        r = para.add_run(); r.text = text
        r.font.size = Pt(kw.get('size', size)); r.font.bold = kw.get('bold', bold)
        r.font.color.rgb = kw.get('color', color); r.font.name = kw.get('font', font)
    return tb


def shape(kind, x, y, w, h, fill, line=None, lw=1.25):
    c = s.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    c.fill.solid(); c.fill.fore_color.rgb = RGB(fill)
    if line:
        c.line.color.rgb = RGB(line); c.line.width = Pt(lw)
    else:
        c.line.fill.background()
    c.shadow.inherit = False
    return c


def label(x, y, w, h, text, fill, size=10, color='FFFFFF'):
    c = shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h, fill)
    tf = c.text_frame; tf.margin_left = tf.margin_right = Inches(0.03); tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = text; r.font.size = Pt(size); r.font.bold = True; r.font.color.rgb = RGB(color); r.font.name = 'Malgun Gothic'
    return c


box(0.75, 1.55, 11.85, 0.4, [('“귀찮은 환불·환급 신청, AI가 대신 해 드립니다” — Meta Muse가 사람들에게 와닿은 이유',
                              {'size': 15, 'bold': True, 'color': NAVY})])

# ── 왼쪽: 사진 + 인물 한 줄 경력
pic = s.shapes.add_picture(photo, Inches(0.8), Inches(2.1), Inches(1.85), Inches(2.78))
pic.line.color.rgb = RGB('BFBFBF'); pic.line.width = Pt(0.75)
box(0.62, 4.92, 2.2, 0.95, [('Alexandr Wang (汪滔)', {'size': 11, 'bold': True, 'align': PP_ALIGN.CENTER, 'after': 1}),
                            ('Meta 최고 AI 책임자 · MSL 총괄', {'size': 9, 'color': SUB, 'align': PP_ALIGN.CENTER, 'after': 1}),
                            ('Scale AI 창업(2016) → Meta(2025)', {'size': 9, 'color': SUB, 'align': PP_ALIGN.CENTER, 'after': 0}),
                            ('→ Muse 에이전트 출시(2026.09)', {'size': 9, 'color': SUB, 'align': PP_ALIGN.CENTER, 'after': 0})])

# ── 가운데: 환불 신청 시나리오 (대화 + 단계)
shape(MSO_SHAPE.ROUNDED_RECTANGLE, 3.0, 2.1, 4.75, 3.75, 'FCE4D6', 'C55A11').adjustments[0] = 0.05
box(3.2, 2.17, 4.4, 0.35, [('Muse가 대신 해 주는 일 · 예시 시나리오', {'size': 13.5, 'bold': True, 'color': ORANGE})])
bub = shape(MSO_SHAPE.ROUNDED_RECTANGLE, 3.2, 2.58, 4.35, 0.45, 'FFFFFF', 'C55A11', 0.75)
tf = bub.text_frame; tf.vertical_anchor = MSO_ANCHOR.MIDDLE; tf.margin_left = Inches(0.08)
r = tf.paragraphs[0].add_run(); r.text = '사용자 ▸ “지난달 늦게 온 택배, 배송비 환불 좀 받아 줘”'
r.font.size = Pt(11); r.font.bold = True; r.font.color.rgb = TXT; r.font.name = 'Malgun Gothic'
STEPS = [('메일함에서 영수증 찾기 → 주문번호·금액·날짜'),
         ('쇼핑몰 환불 신청 화면을 브라우저로 열기'),
         ('신청서 칸 채우기 → 주문번호 · 사유 · 금액 · 환불 계좌'),
         ('고객센터 채팅으로 요청 → 결과를 사용자에게 보고')]
y = 3.15
for i, t in enumerate(STEPS, 1):
    label(3.2, y + 0.03, 0.34, 0.3, str(i), 'C55A11', 10.5)
    box(3.62, y, 3.95, 0.4, [(t, {'size': 11})], anchor=MSO_ANCHOR.MIDDLE)
    y += 0.47
box(3.2, 5.08, 4.4, 0.7, [('사람이 미루던 ‘복잡하지만 돈이 되는 일’을 끝까지 대신 처리', {'size': 10.5, 'bold': True, 'color': ORANGE, 'after': 1}),
                          ('2026.09 미국 출시 · 무료 / 월 $20 · $100 요금제', {'size': 9.5, 'color': SUB, 'after': 0})])

# ── 오른쪽: 데이터 모델링으로 보면
shape(MSO_SHAPE.ROUNDED_RECTANGLE, 7.95, 2.1, 4.65, 3.75, 'E2F0D9', '548235').adjustments[0] = 0.05
box(8.15, 2.17, 4.3, 0.35, [('대신 하려면 데이터 구조를 알아야 한다', {'size': 13.5, 'bold': True, 'color': GREEN})])
ROWS = [('현실 세계', '영수증 메일 · 쇼핑몰 화면 · 고객센터 대화', False),
        ('개념 세계', 'Customer — Order — RefundRequest (고객·주문·환불요청 객체와 관계)', False),
        ('컴퓨터 세계', "refund_request(order_id FK, reason, amount, status='신청')", True)]
y = 2.65
for i, (k, v, code) in enumerate(ROWS):
    label(8.15, y, 1.25, 0.66, k, '548235', 10.5)
    box(9.5, y, 3.0, 0.66, [(v, {'size': 9.5 if code else 10.5, 'font': 'Courier New' if code else 'Malgun Gothic'})], anchor=MSO_ANCHOR.MIDDLE)
    if i < 2:
        shape(MSO_SHAPE.DOWN_ARROW, 8.65, y + 0.68, 0.25, 0.14, '7F7F7F')
    y += 0.84
box(8.15, 5.18, 4.35, 0.6, [('→ 신청서의 칸 = 테이블의 열, 칸 채우기 = INSERT', {'size': 10.5, 'bold': True, 'color': GREEN, 'after': 1}),
                            ('주문번호(FK)를 정확히 찾아야 환불이 연결됩니다', {'size': 9.5, 'color': SUB, 'after': 0})])

# ── 강의 포인트 (현실 데이터 + 한계)
pt = shape(MSO_SHAPE.ROUNDED_RECTANGLE, 0.75, 5.98, 11.85, 0.5, '0F2A4A')
tf = pt.text_frame; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
r = p.add_run(); r.text = '와닿은 이유: 가장 많이 쓴 일이 ‘잊고 있던 돈 찾기’ — 요금 협상 · 환불 받기 · 안 쓰는 구독 해지 (Forbes, 2026.09)'
r.font.size = Pt(12.5); r.font.bold = True; r.font.color.rgb = RGB('FFFFFF'); r.font.name = 'Malgun Gothic'

box(0.75, 6.53, 11.85, 0.26, [('※ 에이전트(Agent): 사람 대신 여러 단계를 실행하는 AI · MSL: Meta Superintelligence Labs (메타 초지능 연구소) · FK: Foreign Key (외래키) · INSERT: 행 추가 SQL',
                               {'size': 9.5, 'color': RGB('3A445C')})])
box(0.75, 6.8, 10.7, 0.45, [('출처: Axios·PBS(2026.09.08, Muse 출시: 브라우저로 양식 작성·협상), Forbes(2026.09.25, 요금 협상·환불 사례), Bloomberg(2026.04.08, Muse Spark) '
                             '· 절감액 사례는 사용자 게시물로 독립 검증 전', {'size': 8, 'color': SUB, 'after': 0}),
                            ('사진: Meta Platforms, Inc. 제공 (2025), Wikimedia Commons, CC BY-SA 4.0', {'size': 8, 'color': SUB, 'after': 0})])

s.notes_slide.notes_text_frame.text = (
    '【슬라이드 핵심】 Meta Muse는 “사람이 하기 싫은 복잡한 신청”을 대신 끝내 주는 개인 AI 에이전트로 주목받았다. 이를 대신하려면 영수증·신청서 같은 현실 데이터를 객체(주문·환불요청)와 테이블 열로 정확히 이해해야 한다.\n'
    '【강의 설명】 Muse는 2026년 9월 8일 미국에서 18세 이상 대상으로 출시된 Meta의 개인 AI 에이전트로, Muse Spark 모델 위에서 동작한다. '
    '전용 보안 가상 머신에서 브라우저를 열어 양식을 작성하고, 고객센터와 협상하고, 결제까지 대신한다(Axios·PBS). 기본 무료, 월 20달러·100달러 요금제가 있다. '
    'Forbes(2026.09.25)는 사용자들이 가장 많이 쓴 일이 인터넷 요금 협상, 환불 받기, 잊고 있던 구독 해지처럼 “잊고 있던 돈 찾기”라고 보도했다. '
    '복잡해서 미루던 일을 대신해 돈으로 돌려준다는 점이 사람들에게 와닿은 핵심이다. 다만 절감액 사례는 사용자·직원 게시물이 많아 독립 검증 전이고, Amazon은 약관을 이유로 Muse의 주문을 막았다는 보도도 있다. '
    '수업 연결: 예시 시나리오에서 Muse는 메일 속 영수증(현실 세계)을 찾아 Order·RefundRequest 객체(개념 세계)로 이해하고, 신청서 칸을 refund_request(order_id, reason, amount, status) 레코드로 채운다(컴퓨터 세계). '
    '신청서 칸이 테이블의 열, 칸 채우기가 INSERT, 주문번호가 FK라는 점을 짚는다. 이 회사를 이끄는 알렉산더 왕(1997년생, 중국계 이민자 부모)은 2016년 데이터 라벨링 회사 Scale AI를 공동 창업했고, '
    '2025년 6월 Meta가 Scale AI 지분 49%에 143억 달러를 투자하면서 Meta 최고 AI 책임자가 되었다.\n'
    '【연결】 11쪽 데이터 모델링 개요, 13쪽 개념적 모델링, 6·9쪽 데이터의 세 세계\n'
    '【출처】 Axios “Meta debuts Muse, its long-planned personal AI agent”(2026.09.08); PBS NewsHour “Meta launches personal AI agent, Muse”(2026.09.08); '
    'Forbes “AI Agents Are Helping People Recover Money By Negotiating Bills And Chasing Refunds”(2026.09.25); Bloomberg(2026.04.08); Wikipedia “Alexandr Wang”; '
    '사진: Meta Platforms, Inc., Wikimedia Commons, CC BY-SA 4.0')

n9 = prs.slides[8].notes_slide.notes_text_frame
for p in n9.paragraphs:
    for r in p.runs:
        r.text = r.text.replace('37–43쪽 Colab', '38–44쪽 Colab')
prs.save(out)
print('ok, slides =', len(prs.slides))
