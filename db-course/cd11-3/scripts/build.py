"""CD11-3 설계실습 보강 (11-2 정규화 패턴: '주제 | 부제' 제목, 남색 머리글 표, 노랑/파랑 카드): python build.py <원본.pptx> <출력.pptx>"""
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN

NAVY, BLUE, TXT = RGBColor(0x10, 0x29, 0x50), RGBColor(0x21, 0x56, 0x9A), RGBColor(0x1A, 0x23, 0x32)
YEL, SKY, HL = RGBColor(0xFF, 0xF3, 0xD9), RGBColor(0xED, 0xF4, 0xFD), RGBColor(0xFF, 0xF0, 0xC2)
FONT = 'Malgun Gothic'
NB_URL = 'https://colab.research.google.com/drive/1mJEtXxBEUK9THq9pVF607BVqO_vDO5Qg'

prs = Presentation(sys.argv[1])
orig = list(prs.slides)
LAYOUT = next(l for l in prs.slide_layouts if l.name == '제목 및 내용')


def run(p, text, size, bold=False, color=TXT, link=None):
    r = p.add_run(); r.text = text
    r.font.size = Pt(size); r.font.bold = bold; r.font.name = FONT; r.font.color.rgb = color
    if link:
        r.hyperlink.address = link
    return r


def textbox(s, x, y, w, h, lines, size=16, bold=True, color=BLUE):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    for i, ln in enumerate(lines if isinstance(lines, list) else [lines]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        run(p, ln, size, bold, color)
    return tb


def new_slide(title, lead):
    s = prs.slides.add_slide(LAYOUT)
    for ph in list(s.placeholders):
        ph._element.getparent().remove(ph._element)
    textbox(s, 1.25, 0.72, 11.3, 0.64, title, 28, True, NAVY)
    textbox(s, 0.95, 1.42, 11.45, 0.57, lead, 16, True, BLUE)
    return s


def table(s, x, y, widths, rows, size=13, rh=0.38, label=None):
    if label:
        textbox(s, x, y - 0.42, sum(widths), 0.4, label, 15, True, NAVY)
    t = s.shapes.add_table(len(rows), len(widths), Inches(x), Inches(y), Inches(sum(widths)), Inches(rh * len(rows))).table
    for j, w in enumerate(widths):
        t.columns[j].width = Inches(w)
    for i, row in enumerate(rows):
        t.rows[i].height = Inches(rh)
        for j, v in enumerate(row):
            c = t.cell(i, j); c.fill.solid(); c.fill.fore_color.rgb = NAVY if i == 0 else SKY
            c.margin_left = c.margin_right = Inches(0.08); c.margin_top = c.margin_bottom = Inches(0.03)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = c.text_frame; tf.word_wrap = True
            p = tf.paragraphs[0]; p.text = ''
            run(p, str(v), size, i == 0, RGBColor(0xFF, 0xFF, 0xFF) if i == 0 else TXT)
    return t


def card(s, x, y, w, h, title, lines, fill=SKY, tsize=16, bsize=13):
    b = s.shapes.add_shape(1, Inches(x), Inches(y), Inches(w), Inches(h))
    b.fill.solid(); b.fill.fore_color.rgb = fill; b.line.fill.background(); b.shadow.inherit = False
    tf = b.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.TOP
    tf.margin_left = tf.margin_right = Inches(0.15); tf.margin_top = Inches(0.1)
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.LEFT; run(p, title, tsize, True, NAVY)
    for ln in lines:
        p = tf.add_paragraph(); p.alignment = PP_ALIGN.LEFT; p.space_before = Pt(3)
        run(p, ln, bsize, False, TXT)
    return b


def footnote(s, lines):
    h = 0.17 * len(lines) + 0.05
    textbox(s, 0.95, 7.5 - h - 0.12, 10.8, h, ['※ ' + x for x in lines], 10.5, False, RGBColor(0x3A, 0x44, 0x5C))


def note(s, text):
    s.notes_slide.notes_text_frame.text = text


NEW_AFTER = {6: [], 8: []}

# ── 실습1 ① 영수증 영역 → 개체
s = new_slide('실습1 ① | 영수증에서 데이터 항목 찾기', "영수증의 각 영역을 '무엇에 대한 정보인가'로 묶으면 개체가 보입니다.")
table(s, 1.05, 2.05, [2.0, 6.7, 2.5], [
    ('영수증 영역', '적힌 값 (예)', '개체'),
    ('상단 매장 정보', '강남중앙점 · 105-87-51367 · 02-533-0656 · 김대영 · 서초대로77길 35', '매장'),
    ('주문 머리글', '대기번호 241 · 2025-03-19 08:54 · POS 02 · BILL 번호', '주문'),
    ('상품 줄', '[포장](HOT)아메리카노 1,500×1 · [포장](ICE)아메리카노 2,000×2', '주문상세 · 메뉴'),
    ('합계 영역', '과세물품가액 5,000 · 부가세 500 · 합계 5,500', '주문 (계산 값)'),
    ('결제 영역', '카드결제 5,500 · 카카오뱅크체크 · 승인번호 21091497', '결제'),
    ('제휴·멤버십', 'CJ ONE 010****5505 · 적립 28 · 가용 384 · 스탬프 3', '회원 · 포인트'),
], size=13, rh=0.44)
textbox(s, 1.05, 5.4, 11.2, 0.5, '같은 대상의 값끼리 묶고, 여러 번 반복되는 줄(상품 줄)은 별도 개체로 나눕니다.', 15, True, NAVY)
footnote(s, ['POS: Point Of Sale (판매 시점 관리 단말) · 부가세(VAT): Value Added Tax, 판매가에 포함된 10% 세금'])
note(s, "【슬라이드 핵심】 영수증을 영역별로 나눠 '무엇에 대한 값인가'로 개체를 찾는다: 매장·주문·주문상세·메뉴·결제·회원(포인트).\n"
        "【강의 설명】 학생에게 영수증에 형광펜으로 영역을 표시하게 한 뒤 표를 채우게 합니다. 핵심 질문은 '이 값은 무엇이 바뀌면 함께 바뀌는가?'입니다. 매장 정보는 주문이 바뀌어도 그대로이고, 상품 줄은 한 주문에 여러 번 나타나므로 따로 나눕니다. 합계 영역은 상품 줄에서 계산되는 값이라 ③에서 다룹니다.\n"
        "【연결】 11-1 개체·속성·관계, 11-2 1NF(반복 그룹 분리).")
NEW_AFTER[6].append(s)

# ── 실습1 ② 개체·PK·FK
s = new_slide('실습1 ② | 개체와 관계 정하기 (PK·FK)', '개체마다 한 행을 구별하는 키(PK)를 정하고, 다른 개체를 가리키는 키(FK)로 연결합니다.')
cards = [('매장 · Stores', ['PK 매장ID', '매장명 · 사업자번호 · 전화 · 대표자 · 주소']),
         ('주문 · Orders', ['PK 주문ID (BILL)', '대기번호 · 주문일시 · POS번호', 'FK 매장ID → 매장']),
         ('메뉴 · Menu', ['PK 메뉴ID', '메뉴명 · 온도(HOT/ICE) · 단가']),
         ('주문상세 · Order_Items', ['PK (주문ID, 메뉴ID)', '수량 · 할인 · 포장 여부', 'FK 주문ID → 주문, 메뉴ID → 메뉴']),
         ('결제 · Payments', ['PK 결제ID', '결제수단 · 카드사 · 승인번호 · 금액', 'FK 주문ID → 주문']),
         ('회원 · 포인트 (확장)', ['PK 회원ID', '가용 포인트 · 스탬프', '적립: (주문ID, 회원ID, 적립금액)'])]
for k, (t, ls) in enumerate(cards):
    card(s, 1.05 + (k % 3) * 3.75, 2.05 + (k // 3) * 1.75, 3.55, 1.6, t, ls, SKY, 15, 12.5)
textbox(s, 1.05, 5.65, 11.2, 0.45, '매장 1:N 주문  |  주문 1:N 주문상세  |  메뉴 1:N 주문상세  |  주문 1:N 결제  |  회원 1:N 포인트적립', 14, True, NAVY)
footnote(s, ['PK: Primary Key (기본키, 행을 구별하는 값) · FK: Foreign Key (외래키, 다른 표의 PK를 가리키는 값)'])
note(s, "【슬라이드 핵심】 영수증에서 6개 개체를 도출하고 PK·FK와 1:N 관계를 정한다.\n"
        "【강의 설명】 주문상세는 '어느 주문의 어느 메뉴인가'를 둘 다 알아야 한 줄이 정해지므로 복합키(주문ID, 메뉴ID)를 씁니다. 결제를 주문과 따로 두는 이유는 카드+현금처럼 한 주문을 여러 번 나눠 결제할 수 있기 때문입니다(주문 1:N 결제). 회원·포인트는 시간이 남으면 확장 과제로 다룹니다.\n"
        "【연결】 11-2 2NF(복합키 일부에만 종속되는 속성 분리), Colab 실습 1.")
NEW_AFTER[6].append(s)

# ── 실습1 ③ 저장 vs 계산
s = new_slide('실습1 ③ | 저장할 값 vs 계산할 값', '영수증의 합계·부가세는 상품 줄에서 계산되는 값입니다. 그대로 저장하면 어긋날 수 있습니다.')
card(s, 1.05, 2.15, 5.45, 2.6, '영수증 그대로 저장', ['주문 표에 합계 5,500 · 부가세 500 · 받을금액 5,500을 함께 저장',
     '상품 줄을 고치면 합계도 따로 고쳐야 하고, 하나라도 빠지면 금액이 서로 어긋납니다 (수정 이상).'], YEL, 18, 13.5)
card(s, 6.8, 2.15, 5.45, 2.6, '설계 후 · 상품 줄에서 계산', ['합계 = Σ(단가 × 수량 − 할인) = 1,500 + 4,000 = 5,500',
     '부가세 = 합계 ÷ 11 = 500 · 과세물품가액 = 5,000', '받은 금액은 결제 표에 결제 건별로 저장'], SKY, 18, 13.5)
textbox(s, 1.05, 5.05, 11.2, 0.8, ['예외 · 이미 발행한 영수증 금액은 바뀌면 안 되므로, 현업에서는 주문상세에 판매 당시 단가를 함께 저장합니다.',
                                   'Colab 실습 3에서 메뉴 단가를 바꾸면 합계가 5,900으로 다시 계산되는 문제를 직접 확인합니다.'], 14, True, NAVY)
note(s, "【슬라이드 핵심】 계산할 수 있는 값(합계·부가세)은 원칙적으로 저장하지 않고 상세 행에서 계산한다. 단, 발행 당시 금액은 보존해야 한다.\n"
        "【강의 설명】 '받을 금액'과 '받은 금액'은 다른 개념입니다. 받을 금액은 주문에서 계산하고, 받은 금액은 결제 표의 합입니다. 둘이 같아야 정상 거래입니다. Colab 실습 3 결과: 단가 2,000→2,200 변경 시 계산 합계 5,900 ≠ 결제 5,500 → 그래서 order_items에 판매 단가 스냅샷을 둡니다.\n"
        "【연결】 11-2 수정 이상, Colab 실습 2·3.")
NEW_AFTER[6].append(s)

# ── 실습1 정답
s = new_slide('실습1 정답 | 커피전문점 영수증 테이블 설계', '영수증 1장이 5개 테이블의 행으로 나뉩니다.')
table(s, 1.05, 2.45, [1.45, 1.35, 2.3], [('매장ID (PK)', '매장명', '사업자번호'), ('S01', '강남중앙점', '105-87-51367')], 12, 0.34, 'Stores · 매장')
table(s, 1.05, 3.75, [1.45, 1.35, 1.0, 1.75], [('주문ID (PK)', '매장ID (FK)', '대기번호', '주문일시'), ('B0001', 'S01', '241', '03-19 08:54')], 12, 0.34, 'Orders · 주문')
table(s, 1.05, 5.05, [1.25, 1.3, 0.8, 1.0, 1.35], [('결제ID (PK)', '주문ID (FK)', '수단', '금액', '승인번호'), ('P01', 'B0001', '카드', '5,500', '21091497')], 12, 0.34, 'Payments · 결제')
table(s, 7.15, 2.45, [1.4, 2.4, 1.1], [('메뉴ID (PK)', '메뉴명', '단가'), ('M01', '아메리카노 (HOT)', '1,500'), ('M02', '아메리카노 (ICE)', '2,000')], 12, 0.34, 'Menu · 메뉴')
table(s, 7.15, 4.1, [1.45, 1.45, 0.8, 1.2], [('주문ID (PK/FK)', '메뉴ID (PK/FK)', '수량', '포장'), ('B0001', 'M01', '1', '포장'), ('B0001', 'M02', '2', '포장')], 12, 0.34, 'Order_Items · 주문상세')
textbox(s, 7.15, 5.45, 5.1, 0.7, ['BILL 번호는 가려져 있어 B0001로 가정', '회원·포인트는 확장 과제'], 12.5, True, BLUE)
note(s, "【슬라이드 핵심】 실습1 정답: 매장 1 · 주문 1 · 메뉴 2 · 주문상세 2 · 결제 1행.\n"
        "【강의 설명】 학생 답과 비교할 때 표 이름보다 'PK·FK가 맞는가', '반복되는 값이 한 곳에만 있는가'를 기준으로 채점합니다. HOT/ICE를 메뉴 2개로 볼지, 메뉴 1개 + 옵션(온도)으로 볼지는 둘 다 정답이 될 수 있습니다(가격이 달라 메뉴 2개가 단순).\n"
        "【연결】 Colab 실습 1 출력 표와 같습니다.")
NEW_AFTER[6].append(s)

# ── 실습2 ① 상담 카드 칸 → 개체
s = new_slide('실습2 ① | 상담 카드 칸을 개체로 나누기', '한 장의 상담 카드에는 사람, 상담, 담당자, 진행 상황이 섞여 있습니다.')
table(s, 1.05, 2.05, [3.6, 5.3, 2.3], [
    ('상담 카드 칸', '속성', '개체'),
    ('이름(한글·영문) · 연락처 · 생년월일 · 이메일 · 주소', '학생ID, 이름, 영문명, 연락처, 생년월일, 이메일, 주소', '학생'),
    ('학력 (학년 · 재학/휴학/졸업 · 전공)', '학년, 학적 상태, 전공', '학생'),
    ('유학분야 · 희망전공 · 비자종류 · 출국시기 · 희망지역', '상담ID, 희망전공, 비자종류, 출국시기, 희망지역', '상담'),
    ('질문사항 · 상담내용 · 날짜', '질문, 상담내용, 상담일', '상담'),
    ('교육기관 · 교육플래너', '기관ID·기관명 / 플래너ID·이름', '교육기관 · 플래너'),
    ('업무 진행 (초기상담 ~ 완료)', '단계, 처리일', '진행이력'),
], size=12.5, rh=0.46)
textbox(s, 1.05, 5.5, 11.2, 0.5, '한 학생은 여러 번 상담받을 수 있으므로 학생과 상담은 따로 둡니다 (학생 1:N 상담).', 15, True, NAVY)
note(s, "【슬라이드 핵심】 상담 카드 칸을 학생·상담·교육기관·플래너·진행이력 개체로 나눈다.\n"
        "【강의 설명】 '이 카드가 두 번째 상담이라면 어떤 칸을 다시 적어야 하나?'라고 물어보면 학생 정보(이름·연락처)와 상담 정보(희망전공·질문)가 자연스럽게 나뉩니다. 학력은 학생 속성으로 두되, 여러 학력을 관리해야 하면 학력 표로 분리할 수 있습니다.\n"
        "【연결】 실습1 ①과 같은 방법.")
NEW_AFTER[8].append(s)

# ── 실습2 ② 체크박스·진행 단계
s = new_slide('실습2 ② | 체크박스와 진행 단계는 왜 따로 둘까?', '여러 개를 고를 수 있는 칸을 한 칸에 넣으면 11-2에서 배운 1NF 위반이 됩니다.')
card(s, 1.05, 2.15, 5.45, 2.75, '분해 전 · 상담 표에 그대로', ["유학분야 = '어학연수, 대학(학사)'  → 한 칸에 여러 값",
     '업무 진행 8단계를 열로: 초기상담일, 학교신청일, 오퍼레터일, … 완료일',
     '단계가 하나 늘면 표 구조(열)를 바꿔야 합니다.'], YEL, 18, 13.5)
card(s, 6.8, 2.15, 5.45, 2.75, '분해 후 · 별도 표로 분리', ['상담_유학분야 (상담ID, 분야코드) → 상담 N:M 유학분야',
     '진행이력 (상담ID, 단계, 처리일) → 상담 1:N 진행이력',
     '단계가 늘면 행만 추가합니다.'], SKY, 18, 13.5)
textbox(s, 1.05, 5.2, 11.2, 0.6, '비자종류처럼 하나만 고르는 칸은 상담 표의 코드 열로 둡니다.', 15, True, NAVY)
footnote(s, ['1NF: First Normal Form (제1정규형, 한 칸에 한 값) · N:M: 다대다 관계 (연결 표로 표현)'])
note(s, "【슬라이드 핵심】 다중 선택(체크박스)은 연결 표(N:M), 단계별 날짜는 이력 표(1:N)로 분리한다.\n"
        "【강의 설명】 '유학분야로 어학연수를 고른 학생 수'를 세려면 한 칸에 쉼표로 넣은 설계에서는 문자열 검색을 해야 하지만, 연결 표에서는 GROUP BY로 바로 셉니다. 진행 단계를 열로 두면 단계 추가가 표 변경(ALTER TABLE)이 되지만, 행으로 두면 데이터 추가로 끝납니다.\n"
        "【연결】 11-2 1NF, Colab 실습 4.")
NEW_AFTER[8].append(s)

# ── 실습2 정답
s = new_slide('실습2 정답 | 유학원 상담 관리 테이블 설계', '학생·상담·플래너·교육기관을 키로 연결하고, 여러 값은 연결 표로 나눕니다.')
cards = [('학생 · Students', ['PK 학생ID', '이름 · 영문명 · 연락처 · 생년월일', '이메일 · 주소 · 학력']),
         ('상담 · Consultations', ['PK 상담ID', '상담일 · 희망전공 · 비자종류 · 출국시기', 'FK 학생ID · 플래너ID · 기관ID']),
         ('플래너 · Planners', ['PK 플래너ID', '이름 · 연락처']),
         ('교육기관 · Institutions', ['PK 기관ID', '기관명 · 국가']),
         ('상담_유학분야 (연결 표)', ['PK (상담ID, 분야코드)', 'FK 상담ID → 상담', 'FK 분야코드 → 유학분야']),
         ('진행이력 · Progress', ['PK (상담ID, 단계)', '처리일 · 메모', 'FK 상담ID → 상담'])]
for k, (t, ls) in enumerate(cards):
    card(s, 1.05 + (k % 3) * 3.75, 2.05 + (k // 3) * 1.75, 3.55, 1.6, t, ls, SKY, 15, 12.5)
textbox(s, 1.05, 5.65, 11.2, 0.45, '학생 1:N 상담  |  플래너 1:N 상담  |  기관 1:N 상담  |  상담 N:M 유학분야  |  상담 1:N 진행이력', 14, True, NAVY)
footnote(s, ['PK: Primary Key (기본키) · FK: Foreign Key (외래키) · N:M: 다대다 관계'])
note(s, "【슬라이드 핵심】 실습2 정답: 학생·상담·플래너·교육기관 + 연결 표(상담_유학분야) + 이력 표(진행이력).\n"
        "【강의 설명】 유학분야 코드 표(어학연수·TAFE/칼리지·학사·석사·조기유학·영주권·기타)를 따로 두면 오타 없이 같은 값을 씁니다. 학생 답에서 상담 표에 학생 이름이 들어 있다면 2NF·3NF 관점에서 왜 빼야 하는지 물어봅니다.\n"
        "【연결】 Colab 실습 4 출력(상담 카드 JOIN, 진행 이력).")
NEW_AFTER[8].append(s)

# ── Colab
s = new_slide('Colab | 영수증을 테이블로 저장하고 다시 출력하기', 'Colab에 내장된 SQLite로 실행합니다. AWS 접속이나 비밀번호가 필요 없습니다.')
steps = [('① 테이블 만들기', '매장·주문·메뉴·주문상세·결제 5개 테이블을 PK·FK와 함께 만들고 영수증 값을 한 번씩만 넣습니다.'),
         ('② JOIN 출력', '키로 연결해 상품 줄을 복원하고, 합계 5,500·부가세 500을 저장하지 않고 계산합니다.'),
         ('③ 수정 비교', '메뉴 표에서 ICE 단가를 한 번 바꾸면 합계가 다시 계산됩니다. 결제 금액과 어긋나는 이유를 봅니다.'),
         ('④ 상담 카드', '학생·상담·연결 표·진행이력을 만들고 JOIN으로 상담 카드를 다시 봅니다.')]
for k, (t, d) in enumerate(steps):
    card(s, 1.05, 2.05 + k * 0.82, 11.2, 0.72, t, [d], SKY, 14, 12.5)
tb = s.shapes.add_textbox(Inches(1.05), Inches(5.45), Inches(11.2), Inches(0.45))
run(tb.text_frame.paragraphs[0], 'CD11-3 설계실습 노트북 열기 ▶', 16, True, BLUE, NB_URL)
footnote(s, ['SQLite: 파일 하나로 동작하는 가벼운 관계형 DB (Colab에 내장) · JOIN: 키로 두 표의 행을 연결하는 SQL 연산'])
note(s, "【슬라이드 핵심】 실습1·2 설계를 SQLite 테이블로 만들고 JOIN으로 원래 문서를 다시 만들어 검증한다.\n"
        "【강의 설명】 11-2 정규화 노트북과 같은 방식입니다. ①②④는 그대로 실행하면 되고, ③은 시연 뒤 자동으로 원래 단가로 되돌립니다. 노트북: CD11-3_Colab_설계실습.ipynb (강의 자료 폴더).\n"
        "【자료】 " + NB_URL)
NEW_AFTER[8].append(s)

# ── 검증
s = new_slide('검증 | JOIN으로 영수증 다시 만들기', '주문상세 → 메뉴, 주문 → 매장을 연결하면 영수증의 상품 줄이 그대로 복원됩니다.')
table(s, 1.05, 2.05, [4.2, 2.0, 1.6, 2.0], [('상품명', '단가', '수량', '금액'),
      ('[포장](HOT)아메리카노', '1,500', '1', '1,500'), ('[포장](ICE)아메리카노', '2,000', '2', '4,000'),
      ('합계 (계산)', '', '', '5,500')], 14, 0.42)
card(s, 1.05, 4.0, 5.45, 1.35, '계산 결과', ['과세물품가액 5,000 + 부가세 500 = 합계 5,500', '부가세 = 합계 ÷ 11'], YEL, 17, 13.5)
card(s, 6.8, 4.0, 5.45, 1.35, '결제 표와 비교', ['카드 5,500 = 합계 5,500', '받을 금액과 받은 금액이 일치합니다 ✅'], SKY, 17, 13.5)
textbox(s, 1.05, 5.6, 11.2, 0.6, '토론 · 손님이 카드 3,000원 + 현금 2,500원으로 나눠 냈다면 결제 표는 몇 행이 될까요?', 15, True, BLUE)
note(s, "【슬라이드 핵심】 Colab 실습 2 실측 결과: JOIN으로 복원한 상품 줄과 계산한 합계·부가세가 영수증과 일치.\n"
        "【강의 설명】 토론 정답: 결제 표 2행(카드 3,000 / 현금 2,500), 둘의 합 5,500이 주문 합계와 같아야 합니다. 그래서 결제를 주문 표의 열이 아니라 별도 표(주문 1:N 결제)로 둡니다.\n"
        "【연결】 실습1 ②(주문 1:N 결제), 실습1 ③(계산 값).")
NEW_AFTER[8].append(s)

# ── 실습 마무리
s = new_slide('실습 마무리 | 어떤 개체를 왜 나눴나요?', '실습1·2의 설계 결과를 근거와 함께 제출합니다.')
for k, (t, d) in enumerate([('제출', '영수증·상담 카드 각각의 개체 목록, PK·FK, 관계(1:N·N:M), Colab JOIN 결과 캡처'),
                            ('토론', "영수증의 '합계'는 저장할까 계산할까? 상담 카드의 진행 단계는 열로 둘까 행으로 둘까?"),
                            ('비교', '11-2 정규화 기준(1NF·2NF·3NF)으로 내 설계의 표를 하나씩 점검합니다.')]):
    card(s, 1.05, 2.15 + k * 1.1, 11.2, 0.95, t, [d], SKY, 16, 13.5)
textbox(s, 1.05, 5.55, 11.2, 0.5, 'Summary에서 개체·속성·관계를 도출하는 순서를 다시 확인합니다.', 15, True, NAVY)
note(s, "【슬라이드 핵심】 제출물과 토론 질문.\n"
        "【강의 설명】 정답 방향: 합계는 계산이 원칙이지만 발행 금액은 보존(스냅샷), 진행 단계는 행(이력 표)으로 둡니다. 채점 기준은 '반복되는 값이 한 곳에만 있는가, 다중 값이 한 칸에 없는가, 모든 표에 PK가 있는가'입니다.")
NEW_AFTER[8].append(s)

# ── 원본 페이지 노트 (기존 노트 없을 때만)
ORIG_NOTES = {
    5: "【슬라이드 핵심】 커피전문점 영수증에서 entity(개체)·attribute(속성)·relation(관계)을 찾는다.\n【강의 설명】 다음 장들(실습1 ①~정답)에서 영역 표 → 개체·키 → 계산 값 → 테이블 순서로 풀어 갑니다.",
    6: "【슬라이드 핵심】 영수증을 위·아래 두 부분으로 나눠 보기: 매장·주문·상품 줄·합계 / 결제·제휴·멤버십.\n【강의 설명】 학생이 각 영역에 이름표(매장, 주문, 결제…)를 붙이게 한 뒤 실습1 ①로 넘어갑니다.",
    8: "【슬라이드 핵심】 유학원 상담 카드에서 개체·속성·관계를 찾는다.\n【강의 설명】 체크박스(유학분야·비자종류)와 오른쪽 '업무 진행' 칸이 설계 포인트입니다(실습2 ②).",
}
for n, t in ORIG_NOTES.items():
    tf = orig[n - 1].notes_slide.notes_text_frame
    if not tf.text.strip():
        tf.text = t
footnote(orig[4], ['entity: 개체 (데이터로 관리할 대상) · attribute: 속성 (개체의 특성) · relation: 관계 (개체 사이의 연결)'])
footnote(orig[7], ['TAFE: Technical and Further Education (호주 직업교육기관) · COE: Confirmation of Enrolment (입학 허가 확인서)'])

# ── SUMMARY 보강 (기존 문장 유지, 핵심 2줄 추가)
import copy as _copy
for sh in orig[8].shapes:
    if sh.has_text_frame and '실생활에서' in sh.text_frame.text:
        last = sh.text_frame.paragraphs[-1]._p
        for line in ['영수증: 매장·주문·메뉴·주문상세·결제로 분해하고, 합계·부가세는 상품 줄에서 계산한다.',
                     '상담 카드: 여러 개 고르는 칸은 연결 표(N:M), 진행 단계는 이력 표(1:N)로 나눈다.']:
            np_ = _copy.deepcopy(last); last.addnext(np_); last = np_
            rs = np_.findall('{http://schemas.openxmlformats.org/drawingml/2006/main}r')
            rs[0].find('{http://schemas.openxmlformats.org/drawingml/2006/main}t').text = line
            for r in rs[1:]:
                np_.remove(r)
        break

# ── 배치
sld = prs.slides._sldIdLst
all_ids = list(sld)
ids, tail = all_ids[:len(orig)], all_ids[len(orig):]
order = {i + 1: [ids[i]] for i in range(len(ids))}
k = 0
for after in (6, 8):
    for _ in NEW_AFTER[after]:
        order[after].append(tail[k]); k += 1
for el in list(sld):
    sld.remove(el)
for n in sorted(order):
    for el in order[n]:
        sld.append(el)
prs.save(sys.argv[2])
print('saved', sys.argv[2], len(prs.slides), 'slides')
