"""11-1 보강본: 11쪽(데이터 모델링 개요) 다음에 'Meta Muse와 알렉산더 왕(Alexandr Wang)' 사례 슬라이드 추가 (사진 포함).
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
TXT, SUB, NAVY = RGB('262626'), RGB('5A5A5A'), RGB('1F4E79')
TITLE = '데이터 모델링 사례 · Meta Muse'

# 이미 추가돼 있으면 그 슬라이드를 다시 만든다(중복 방지)
ids = prs.slides._sldIdLst
for i, sl in enumerate(prs.slides):
    if sl.shapes.title is not None and sl.shapes.title.text_frame.text.strip() == TITLE:
        prs.part.drop_rel(ids[i].rId); ids.remove(ids[i]); break

base = prs.slides[10]                                   # 11쪽: 데이터 모델링 개요 (원본 템플릿)
s = prs.slides.add_slide(base.slide_layout)
el = ids[-1]; ids.remove(el); ids.insert(11, el)        # 12쪽 위치로
for ph in list(s.placeholders):
    if ph.placeholder_format.idx != 0:
        ph._element.getparent().remove(ph._element)
s.shapes.title.text_frame.text = TITLE


def box(x, y, w, h, paras, size=12, color=TXT, bold=False, align=PP_ALIGN.LEFT, anchor=None):
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
        r.font.color.rgb = kw.get('color', color); r.font.name = 'Malgun Gothic'
    return tb


def card(x, y, w, h, fill, line):
    c = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    c.adjustments[0] = 0.06
    c.fill.solid(); c.fill.fore_color.rgb = RGB(fill)
    c.line.color.rgb = RGB(line); c.line.width = Pt(1.25); c.shadow.inherit = False
    return c


box(0.75, 1.55, 11.85, 0.4, [('알렉산더 왕과 Meta Muse — AI 모델도 현실 데이터 → 라벨 체계(개념) → 학습 데이터셋(물리)에서 시작합니다.',
                              {'size': 14.5, 'bold': True, 'color': NAVY})])

# 사진 + 이름
pic = s.shapes.add_picture(photo, Inches(0.8), Inches(2.1), Inches(2.0), Inches(3.0))
pic.line.color.rgb = RGB('BFBFBF'); pic.line.width = Pt(0.75)
box(0.7, 5.12, 2.2, 0.55, [('Alexandr Wang (汪滔)', {'size': 11.5, 'bold': True, 'align': PP_ALIGN.CENTER, 'after': 0}),
                           ('Meta 최고 AI 책임자 · MSL 총괄', {'size': 9.5, 'color': SUB, 'align': PP_ALIGN.CENTER, 'after': 0})])

# 가운데: 인물·사건 타임라인
card(3.1, 2.1, 4.35, 3.55, 'DEEBF7', '1F4E79')
box(3.3, 2.2, 4.0, 0.4, [('누가 · 무엇을 만들었나', {'size': 15, 'bold': True, 'color': NAVY})])
TL = [('1997', '미국 로스앨러모스 출생, 중국계 이민자 부모(물리학자)'),
      ('2016', 'MIT를 그만두고 Scale AI 공동 창업 — AI 학습용 데이터 라벨링 회사'),
      ('2025.06', 'Meta가 Scale AI 지분 49%에 143억 달러 투자 → Meta 최고 AI 책임자, MSL 총괄'),
      ('2026.04', 'MSL 첫 모델 Muse Spark 공개 — 텍스트·이미지·음성을 함께 다루는 멀티모달, 비공개 모델')]
y = 2.68
for yr, txt in TL:
    tag = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(3.3), Inches(y + 0.02), Inches(0.82), Inches(0.3))
    tag.fill.solid(); tag.fill.fore_color.rgb = NAVY; tag.line.fill.background(); tag.shadow.inherit = False
    tf = tag.text_frame; tf.margin_left = tf.margin_right = Inches(0.02); tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = yr; r.font.size = Pt(10); r.font.bold = True; r.font.color.rgb = RGB('FFFFFF'); r.font.name = 'Malgun Gothic'
    box(4.2, y, 3.15, 0.7, [(txt, {'size': 11})])
    y += 0.72

# 오른쪽: 데이터 모델링으로 보면
card(7.7, 2.1, 4.9, 3.55, 'E2F0D9', '548235')
box(7.9, 2.2, 4.6, 0.4, [('데이터 모델링으로 보면', {'size': 15, 'bold': True, 'color': RGB('548235')})])
ROWS = [('현실 세계', '사진·문서·음성·주행 영상 같은 원천 데이터'),
        ('개념적 모델링', '라벨 체계 정의: 객체 클래스(자동차·보행자)·속성·관계'),
        ('논리·물리 모델링', '라벨 레코드(item_id, label, 위치, 검수자, 버전)로 학습 데이터셋 저장')]
y = 2.7
for i, (k, v) in enumerate(ROWS):
    lab = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(7.9), Inches(y), Inches(1.45), Inches(0.62))
    lab.fill.solid(); lab.fill.fore_color.rgb = RGB('548235'); lab.line.fill.background(); lab.shadow.inherit = False
    tf = lab.text_frame; tf.margin_left = tf.margin_right = Inches(0.03); tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = k; r.font.size = Pt(10.5); r.font.bold = True; r.font.color.rgb = RGB('FFFFFF'); r.font.name = 'Malgun Gothic'
    box(9.45, y, 3.05, 0.62, [(v, {'size': 10.5})], anchor=MSO_ANCHOR.MIDDLE)
    if i < 2:
        a = s.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, Inches(8.5), Inches(y + 0.64), Inches(0.25), Inches(0.14))
        a.fill.solid(); a.fill.fore_color.rgb = RGB('7F7F7F'); a.line.fill.background(); a.shadow.inherit = False
    y += 0.8
box(7.9, 5.1, 4.6, 0.45, [('→ Muse 같은 모델의 품질은 이 데이터 구조의 품질에 달려 있습니다.', {'size': 10.5, 'bold': True, 'color': RGB('548235')})])

# 강의 포인트
pt = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.75), Inches(5.82), Inches(11.85), Inches(0.5))
pt.fill.solid(); pt.fill.fore_color.rgb = RGB('0F2A4A'); pt.line.fill.background(); pt.shadow.inherit = False
tf = pt.text_frame; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
r = p.add_run(); r.text = '강의 포인트: Meta가 모델이 아니라 ‘데이터 회사’에 143억 달러를 투자한 이유 — 잘 정의된 데이터 구조가 AI 경쟁력입니다.'
r.font.size = Pt(12.5); r.font.bold = True; r.font.color.rgb = RGB('FFFFFF'); r.font.name = 'Malgun Gothic'

# 약어 주석 + 출처(사진 저작권 표기 포함)
box(0.75, 6.38, 11.85, 0.28, [('※ MSL: Meta Superintelligence Labs (메타 초지능 연구소) · 라벨링: 데이터에 정답 이름표를 붙이는 작업 · 멀티모달: 여러 형태 데이터를 함께 처리', {'size': 10, 'color': RGB('3A445C')})])
box(0.75, 6.68, 10.6, 0.5, [('출처: Bloomberg·Fortune(2026.04.08, Muse Spark 공개), Meta의 Scale AI 투자 보도(2025.06, 지분 49%·143억 달러), Wikipedia “Alexandr Wang”', {'size': 8.5, 'color': SUB, 'after': 0}),
                            ('사진: Meta Platforms, Inc. 제공 (2025), Wikimedia Commons, CC BY-SA 4.0', {'size': 8.5, 'color': SUB, 'after': 0})])

s.notes_slide.notes_text_frame.text = (
    '【슬라이드 핵심】 AI 모델 경쟁의 출발점도 데이터 모델링이다. Meta는 데이터 라벨링 회사 Scale AI에 투자하고 창업자 알렉산더 왕에게 초지능 연구소(MSL)를 맡겨 첫 모델 Muse Spark를 내놓았다.\n'
    '【강의 설명】 알렉산더 왕(Alexandr Wang, 汪滔)은 1997년 미국 뉴멕시코주 로스앨러모스에서 중국계 이민자 물리학자 부모에게서 태어났다. '
    'MIT를 그만두고 2016년 Scale AI를 공동 창업했고, 이 회사는 AI 학습에 쓰이는 데이터에 라벨(정답 이름표)을 붙이고 모델을 평가하는 일을 한다. '
    '2025년 6월 Meta는 Scale AI 지분 49%에 143억 달러를 투자했고, 왕은 Meta 최고 AI 책임자로 MSL을 이끈다. 2026년 4월 MSL의 첫 모델 Muse Spark가 공개됐다(멀티모달, 비공개 모델). '
    '데이터 모델링 관점에서 보면, 라벨링은 현실 데이터(사진·영상·문서)를 어떤 객체 클래스와 속성으로 표현할지 정하는 개념적 모델링이고, '
    '그 결과를 item_id·label·위치·검수자·버전 같은 레코드로 저장하는 것이 논리·물리 모델링이다. 잘 정의된 데이터 구조가 모델 품질을 좌우한다는 점을 강조한다.\n'
    '【연결】 11쪽 데이터 모델링 개요(개념·논리·물리), 13쪽 개념적 모델링, 6·9쪽 데이터의 세 세계\n'
    '【출처】 Bloomberg “Meta Debuts First AI Model From New Superintelligence Group”(2026.04.08); Fortune “Meta unveils Muse Spark”(2026.04.08); '
    'Wikipedia “Alexandr Wang”; 사진: Meta Platforms, Inc., Wikimedia Commons “Alexandr Wang, Chief A.I. Officer, Meta.jpg”, CC BY-SA 4.0')

# 9쪽 노트의 Colab 쪽 번호(슬라이드 1장 추가로 한 칸 뒤로)
n9 = prs.slides[8].notes_slide.notes_text_frame
for p in n9.paragraphs:
    for r in p.runs:
        r.text = r.text.replace('37–43쪽 Colab', '38–44쪽 Colab')
prs.save(out)
print('ok, slides =', len(prs.slides))
