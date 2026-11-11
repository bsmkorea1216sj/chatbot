"""11-1 보강본 '적용 사례 | 주문·결제 데이터…' 슬라이드 보강: 세 회사 사례를 개념·논리·물리 단계로 구분해 설명.
  개념 = Palantir Ontology(업무 객체·관계·액션), 논리 = Google Cloud Knowledge Catalog(필드 정의·의미·소유권 문서화),
  물리 = AWS DynamoDB(조회 패턴에 맞춘 키·저장 배치). 각 단계를 관계형 DB로 옮기면 어떤 모습인지 함께 제시.
  제목 자리·강의자가 둔 장식(학습내용 태그 등)은 유지하고 본문 카드·토론·출처만 다시 만든다.
  덤: '의미 객체 모델 vs ER 모델' 슬라이드의 '(19쪽)' 참조 제거(강의자가 도서관 예제 슬라이드를 삭제함).
python slide_case_levels.py <in.pptx> <out.pptx>"""
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

def _txt(sl):
    return ' '.join(sh.text_frame.text for sh in sl.shapes if sh.has_text_frame)
# 대상: '적용 사례 | 주문·결제…' 제목 + Palantir/AWS/Google 카드가 있는 슬라이드 (같은 이름 '적용 사례' 슬라이드가 또 있으므로 내용으로 찾음)
s = next(sl for sl in prs.slides if '적용 사례 |' in _txt(sl) and 'Palantir' in _txt(sl)
         and ('Knowledge Catalog' in _txt(sl) or '개념·논리·물리' in _txt(sl)))
title_sh = next(sh for sh in s.shapes if sh.is_placeholder and sh.has_text_frame and sh.text_frame.text.strip().startswith('적용 사례'))
KEEP = ('학습내용', 'Cloud Database')
for sh in list(s.shapes):
    if sh.is_placeholder:
        continue
    t = sh.text_frame.text.strip() if sh.has_text_frame else ''
    if t in KEEP or (not t and sh.top < Inches(1.6)):      # 강의자 장식(태그·파란 막대·밑줄) 유지
        continue
    sh._element.getparent().remove(sh._element)
tp = title_sh.text_frame
tp.paragraphs[0].runs[0].text = '적용 사례 | 주문·결제의 개념·논리·물리'
for r in tp.paragraphs[0].runs[1:]:
    r.text = ''
for p in tp.paragraphs[1:]:
    p._p.getparent().remove(p._p)
tp.paragraphs[0].runs[0].font.size = Pt(30)


def box(x, y, w, h, paras, size=11, color=TXT, bold=False, anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.LEFT, font='Malgun Gothic', spacing=2):
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


box(0.75, 1.55, 11.85, 0.38, [('같은 ‘주문·결제’ 데이터도 단계마다 묻는 질문이 다릅니다 — 세 회사 도구가 각 단계를 대표합니다', {'bold': True, 'color': NAVY, 'size': 14})])

# 열 머리글
X = [0.75, 2.2, 4.75, 9.0]; W = [1.35, 2.45, 4.15, 3.6]
for x, w, h in zip(X, W, ['단계', '회사 · 도구', '이 단계에서 정하는 것 (사례)', '관계형 DB로 옮기면']):
    box(x, 2.0, w, 0.3, [(h, {'bold': True, 'color': SUB, 'size': 10.5})])

ROWS = [
    ('개념', '무엇을 관리하나?', '7030A0', 'F3ECFA',
     [('Palantir', {'bold': True, 'size': 13}), ], 'Ontology · 업무 객체와 액션',
     ['고객 → 주문 → 결제를 객체와 링크로 연결', '상담원은 조회, 권한 있는 담당자만 ‘환불 승인’ 액션 실행'],
     ['개체: Customer · Order · Payment', '관계: 고객 1:N 주문 1:N 결제', '규칙: 환불은 승인 권한자만'], False),
    ('논리', '어떤 구조·의미로?', '1F4E79', 'DEEBF7',
     [('Google Cloud', {'bold': True, 'size': 13})], 'Knowledge Catalog · 정의와 소유권',
     ['결제 데이터의 필드 정의(금액·상태·승인번호)와 갱신 주기 문서화', '소유팀(정산팀)을 정하고 분석팀은 접근 요청'],
     ['payments(payment_id PK,', '  order_id FK, amount,', "  status CHECK ('승인','환불'))"], True),
    ('물리', '어떻게 빨리 읽나?', '548235', 'E2F0D9',
     [('AWS', {'bold': True, 'size': 13})], 'DynamoDB · 조회 패턴과 키',
     ['자주 하는 조회: 고객별 최근 주문', 'PK = 고객ID, SK = 주문시각#주문ID → 최신순으로 바로 읽기'],
     ['CREATE INDEX idx_orders_recent', '  ON orders(customer_id,', '            ordered_at DESC);'], True),
]
y = 2.33
for lvl, q, line, fill, vendor, tool, decide, rel, code in ROWS:
    shape(MSO_SHAPE.ROUNDED_RECTANGLE, 0.75, y, 11.85, 1.0, fill, line, 1.25).adjustments[0] = 0.08
    lab = shape(MSO_SHAPE.ROUNDED_RECTANGLE, 0.85, y + 0.1, 1.25, 0.8, line)
    tf = lab.text_frame; tf.vertical_anchor = MSO_ANCHOR.MIDDLE; tf.margin_left = tf.margin_right = Inches(0.02)
    for i, (t, sz) in enumerate([(lvl, 16), (q, 8.5)]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.alignment = PP_ALIGN.CENTER
        r = p.add_run(); r.text = t; r.font.size = Pt(sz); r.font.bold = True; r.font.color.rgb = RGB('FFFFFF'); r.font.name = 'Malgun Gothic'
    box(2.2, y + 0.05, 2.45, 0.9, [vendor, [(tool, {'size': 10, 'color': RGB(line), 'bold': True})]])
    box(4.75, y + 0.05, 4.15, 0.9, [[('• ', {'color': RGB(line), 'bold': True}), d] for d in decide], size=10.5)
    rb = shape(MSO_SHAPE.ROUNDED_RECTANGLE, 9.0, y + 0.1, 3.5, 0.8, 'FFFFFF', line, 0.75)
    box(9.05, y + 0.1, 3.4, 0.8, [(t, {'font': 'Courier New' if code else 'Malgun Gothic', 'size': 9 if code else 10}) for t in rel], spacing=0)
    y += 1.08

d = shape(MSO_SHAPE.ROUNDED_RECTANGLE, 0.75, 5.62, 11.85, 0.72, '0F2A4A')
tf = d.text_frame; tf.vertical_anchor = MSO_ANCHOR.MIDDLE; tf.word_wrap = True
for i, runs in enumerate([[('토론 | 결제 이력이 보이지 않는다면 어느 단계부터 확인할까?', {'size': 12.5})],
                          [('개념', {'color': RGB('D9C3F0')}), ': 고객–주문–결제 연결이 빠졌나?   ',
                           ('논리', {'color': RGB('BDD7EE')}), ': order_id·상태 값 정의가 맞나?   ',
                           ('물리', {'color': RGB('C5E0B4')}), ': 조회 키·인덱스·접근 권한이 맞나?']]):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.alignment = PP_ALIGN.CENTER
    for rr in runs:
        t, kw = (rr, {}) if isinstance(rr, str) else rr
        r = p.add_run(); r.text = t; r.font.size = Pt(kw.get('size', 11)); r.font.bold = True
        r.font.color.rgb = kw.get('color', RGB('FFFFFF')); r.font.name = 'Malgun Gothic'

box(0.75, 6.4, 11.85, 0.28, [('※ PK: Partition Key (파티션 키, 관계형의 Primary Key) · SK: Sort Key (정렬 키) · FK: Foreign Key (외래키) · Ontology: 업무 객체·관계·액션 모델', {'size': 9, 'color': RGB('3A445C')})], anchor=MSO_ANCHOR.TOP)
box(0.75, 6.7, 10.6, 0.26, [('수업용 가상 시나리오 · 참고 문서: Palantir Ontology / Google Cloud Knowledge Catalog / AWS DynamoDB Query·Sort Key', {'size': 8.5, 'color': SUB})], anchor=MSO_ANCHOR.TOP)

s.notes_slide.notes_text_frame.text = (
    '【슬라이드 핵심】 같은 주문·결제 데이터도 개념(무엇을 관리하나) → 논리(어떤 구조·의미로) → 물리(어떻게 빨리 읽나) 단계마다 결정하는 것이 다르다. 세 회사 도구가 각 단계를 대표한다.\n'
    '【강의 설명】 개념 단계 – Palantir Ontology: 고객·주문·결제를 업무 객체로, 그 사이를 링크로 연결하고 ‘환불 승인’ 같은 액션과 실행 권한까지 정의한다. ER 모델의 개체·관계·업무 규칙에 해당한다. '
    '논리 단계 – Google Cloud Knowledge Catalog: 결제 데이터의 필드(금액·상태·승인번호)가 무슨 뜻인지, 얼마나 자주 갱신되는지, 누가 소유하는지를 문서화한다. 관계형으로 옮기면 payments 테이블의 열·PK·FK·CHECK 정의와 데이터 사전이다. '
    '물리 단계 – AWS DynamoDB: 가장 자주 하는 조회(고객별 최근 주문)에 맞춰 파티션 키=고객ID, 정렬 키=주문시각#주문ID로 저장 배치를 정해 최신순으로 바로 읽는다. 관계형에서는 (customer_id, ordered_at DESC) 인덱스가 같은 역할을 한다. '
    '토론에서는 결제 이력이 안 보일 때 개념(연결 누락) → 논리(키·값 정의 불일치) → 물리(조회 키·인덱스·권한) 순으로 점검하게 한다.\n'
    '【연결】 개념적·논리적·물리적 모델링 슬라이드, 의미 객체 모델 vs ER 모델, 이후 데이터베이스 구축 6단계\n'
    '【출처】 Palantir Ontology 문서, Google Cloud Knowledge Catalog 문서, AWS DynamoDB 개발자 안내서(Partition key·Sort key·Query). 수업용 가상 시나리오')

# 의미 객체 모델 슬라이드의 '(19쪽)' 참조 정리
som = next((sl for sl in prs.slides if sl.shapes.title is not None and sl.shapes.title.text_frame.text.strip() == '의미 객체 모델 vs ER 모델'), None)
if som is not None:
    for sh in som.shapes:
        if sh.has_text_frame:
            for p in sh.text_frame.paragraphs:
                for r in p.runs:
                    r.text = r.text.replace('‘동네 도서관 대출’(19쪽)을', '‘동네 도서관 대출’을')
    for p in som.notes_slide.notes_text_frame.paragraphs:
        for r in p.runs:
            r.text = (r.text.replace('이 그림은 members·books·loans 세 테이블로 그대로 바뀐다(19·20쪽).', '이 그림은 members·books·loans 세 테이블로 그대로 바뀐다.')
                      .replace('26쪽 개념적 데이터 모델의 종류, 19·20쪽 도서관 대출 예제, 다음 쪽 Hulu 사례(ER 관점)', '앞 쪽 개념적 데이터 모델의 종류, 다음 쪽 Hulu 사례(ER 관점)'))
prs.save(out)
print('ok')
