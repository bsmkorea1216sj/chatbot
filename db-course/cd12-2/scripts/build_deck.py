"""CD12-2 개념적 모델링 교안(26) — 12-1과 같은 형식: 실습 쪽마다 Colab 셀 버튼, Colab 개요·실습 끝내기 쪽, 중간 과제 2개.
원본(1jnWHgGIYul_DyVYea4P3Qc0ZsiJcs7tG)은 그대로 두고 새 (26) 파일을 만든다.
 새 쪽: 4 Colab 실습 개요 · 14 과제 ① 관계 차수 · 29 실습 끝내기(RDS 삭제)
 수정: 버튼(8·11·12·13·16·17·18·19·20·23·24) · 18쪽 재고 차감 시점(결제 승인, 20쪽 CRUD와 일치) ·
       19쪽 과제 ②(주문취소 행 추가) · 20쪽 정답(주문취소 행, 측정 결과 Order Details R 두 칸 노란색) · 약어 주석·노트
python build_deck.py <원본.pptx> <출력.pptx> <노트북ID>"""
import sys, copy
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

src, out, NBID = sys.argv[1:4]
NB = f'https://colab.research.google.com/drive/{NBID}'
prs = Presentation(src)
RGB = lambda h: RGBColor.from_string(h)
NAVY, FILL, FONT, GRAY = '1F4E79', 'EDF4FD', 'Malgun Gothic', '5A5A5A'
ids = prs.slides._sldIdLst


def txt(sl):
    return ' '.join(sh.text_frame.text for sh in sl.shapes if sh.has_text_frame) + ' '.join(
        c.text for sh in sl.shapes if sh.has_table for r in sh.table.rows for c in r.cells)


def find(key):
    return next(s for s in prs.slides if key in txt(s))


def tb(sl, x, y, w, h, lines, size=12, color=NAVY, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    t = sl.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = t.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    for m in ('margin_left', 'margin_right', 'margin_top', 'margin_bottom'):
        setattr(tf, m, Inches(0.04))
    for i, ln in enumerate(lines):
        runs = ln if isinstance(ln, list) else [ln]
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.alignment = align; p.space_after = Pt(3)
        for rr in runs:
            text, kw = (rr, {}) if isinstance(rr, str) else rr
            r = p.add_run(); r.text = text
            r.font.size = Pt(kw.get('size', size)); r.font.bold = kw.get('bold', bold)
            r.font.color.rgb = RGB(kw.get('color', color)); r.font.name = FONT
            if kw.get('link'):
                r.hyperlink.address = kw['link']
    return t


def button(sl, label, anchor, x=0.98, y=6.62, w=4.9):
    url = f'{NB}#scrollTo={anchor}' if anchor else NB
    b = sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(0.48))
    b.fill.solid(); b.fill.fore_color.rgb = RGB('EAF2FB'); b.line.color.rgb = RGB(NAVY); b.line.width = Pt(1)
    b.shadow.inherit = False
    tf = b.text_frame; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = f'Colab · {label}'; r.font.size = Pt(12.5); r.font.bold = True
    r.font.color.rgb = RGB(NAVY); r.font.name = FONT
    r.hyperlink.address = url
    b.click_action.hyperlink.address = url
    return b


def table(sl, x, y, colw, rows, size=12, rh=0.4, hl=None):
    gf = sl.shapes.add_table(len(rows), len(colw), Inches(x), Inches(y), Inches(sum(colw)), Inches(rh * len(rows)))
    t = gf.table
    for j, w in enumerate(colw):
        t.columns[j].width = Inches(w)
    for i, row in enumerate(rows):
        t.rows[i].height = Inches(rh)
        for j, v in enumerate(row):
            c = t.cell(i, j); c.text = v; c.vertical_anchor = MSO_ANCHOR.MIDDLE
            c.margin_top = c.margin_bottom = Inches(0.03)
            c.fill.solid(); c.fill.fore_color.rgb = RGB(NAVY if i == 0 else ((hl or {}).get(i) or (FILL if i % 2 else 'FFFFFF')))
            r = c.text_frame.paragraphs[0].runs[0]
            r.font.size = Pt(size); r.font.name = FONT; r.font.bold = (i == 0 or j == 0)
            r.font.color.rgb = RGB('FFFFFF' if i == 0 else '262626')
    return gf


def foot(sl, text, y=6.22):
    tb(sl, 0.98, y, 11.4, 0.3, [(text, {'size': 9.5, 'color': '3A445C'})])


def add_notes(sl, text):
    sl.notes_slide.notes_text_frame.text = text


def append_note(sl, text):
    tf = sl.notes_slide.notes_text_frame
    if text[:10] not in tf.text:
        tf.add_paragraph().text = text


def new_slide(after, title):
    """원본 '제목 및 내용' 레이아웃으로 새 쪽을 만들고 after 다음에 둔다(본문 자리는 지움)."""
    layout = find('1. 개념적 모델링의 목표 분석 단계').slide_layout
    s = prs.slides.add_slide(layout)
    el = ids[-1]; ids.remove(el)
    pos = list(prs.slides).index(after) if False else [i for i, e in enumerate(ids) if prs.part.related_part(e.rId) is after.part][0]
    ids.insert(pos + 1, el)
    for ph in list(s.placeholders):
        if ph.placeholder_format.idx != 0:
            ph._element.getparent().remove(ph._element)
    s.shapes.title.text_frame.text = title
    return s


# ── 기준 쪽(원본 텍스트로 찾기)
s_goal = find('도출된 요구사항을 기반으로 주요 엔티티와 속성을 정의')
s_ent = next(s for s in prs.slides if s.shapes.title is not None and s.shapes.title.text_frame.text.strip() == '2. 주요 엔티티 및 속성 식별'
             and any(sh.has_table for sh in s.shapes))      # 같은 제목의 구역 표지(7쪽) 제외
s_rel_text = find('ER 다이어그램은 위 엔티티와 관계를 시각적으로 표현함')
s_rel_list = find('관계 (다이아몬드)')
s_chen = find('ER-Diagram(피터 첸 표기법)')
s_ie = next(s for s in prs.slides if s.shapes.title is not None and s.shapes.title.text_frame.text.strip() == 'ER-Diagram(IE 표기법)')
s_tx1 = find('4.1 주문 생성 및 처리 트랜잭션')
s_tx2 = find('4.2 기타 트랜잭션')
s_flow = find('4.3 처리 흐름')
crud = [s for s in prs.slides if '4.4 CRUD 매트릭스' in txt(s)]
s_crud_blank, s_crud_ans = crud[0], crud[1]
s_ent_rev = find('2. 주요 엔티티 및 속성 식별(review)')
s_ie_rev = find('ER-Diagram(IE 표기법)(review)')
s_conc = [s for s in prs.slides if '6. 결론 및 향후 발전' in txt(s) and '이와 같이 개념적 모델링은' in txt(s)][0]

# ── 새 쪽 A: Colab 실습 개요 (학습목표 다음)
A = new_slide(s_goal, 'Colab 실습 | 개념 모델을 AWS RDS에서 확인')
tb(A, 0.98, 1.5, 11.4, 0.4, [('Colab 보안 비밀만으로 AWS에 실습 RDS를 만들고 → 표·과제·트랜잭션·CRUD를 확인한 뒤 → 삭제합니다.', {'size': 15, 'bold': True})])
tb(A, 0.98, 1.92, 11.4, 0.3, [[('실습 노트북  ', {'size': 11, 'color': GRAY}), (NB, {'size': 11, 'color': '1155CC', 'link': NB})]])
table(A, 0.98, 2.3, [2.1, 7.0, 2.3], [
    ('셀', '하는 일', '교안'),
    ('1. DB 생성', '보안 비밀(AWS 키·DB_PASSWORD)로 AWS에 RDS 생성(없을 때만) → ④ 연결 확인', '이 쪽'),
    ('2. 표 만들기', '엔티티 7개를 IE 표기법 그대로 표로 만들기', '8·11~13쪽'),
    ('과제 ①', '관계 차수(1:1 / 1:N) 입력 → 실제 FK·UNIQUE로 채점', '14쪽'),
    ('3. 주문 트랜잭션', '주문생성 → 결제승인 → 배송처리 → 리뷰작성, 재고 부족 시 전체 롤백', '16~18쪽'),
    ('4. CRUD 측정', '트랜잭션마다 실제 C·R·U·D를 측정해 매트릭스로', '19·20쪽'),
    ('과제 ②', '‘주문취소’ 행 CRUD 예측 → 측정과 비교', '19쪽 (정답 20쪽)'),
    ('5. 삭제', 'DELETE 입력 → AWS의 실습 RDS 삭제 (요금 중지)', '29쪽'),
], size=11.5, rh=0.42, hl={3: 'FFF3D9', 6: 'FFF3D9'})
foot(A, '※ 보안 비밀: AWS_ACCESS_KEY · AWS_SECRET_KEY · DB_PASSWORD (각 항목 ‘노트북 액세스’ 켜기) · RDS: Relational Database Service · CRUD: Create·Read·Update·Delete', y=5.82)
button(A, '1. DB 생성', 'm-db-create'); button(A, '노트북 처음부터 열기', None, x=6.05)
add_notes(A, '【슬라이드 핵심】 12-1과 같은 방식으로, Colab 보안 비밀만으로 AWS에 실습 RDS를 만들고 개념 모델을 실제 표·제약조건·트랜잭션으로 확인한 뒤 삭제한다. 각 쪽의 Colab 버튼이 해당 셀로 이동한다.\n'
             '【강의 설명】 학생은 열쇠 아이콘에 AWS_ACCESS_KEY, AWS_SECRET_KEY, DB_PASSWORD를 등록하고 노트북 액세스를 켠다. 1번 셀은 RDS가 없으면 만들고(5~15분), 있으면 그대로 쓴다(12-1과 같은 RDS). '
             '노란 줄 두 개가 중간 과제다: 과제 ①은 ERD를 본 뒤 관계 차수를, 과제 ②는 CRUD 매트릭스를 배운 뒤 주문취소 행을 예측한다. 실습이 끝나면 29쪽 안내대로 5번 셀로 RDS를 삭제한다.\n'
             f'【연결】 {NB}')

# ── 버튼: 기존 쪽
LOW_RIGHT = dict(x=6.35, y=6.98, w=4.7)                   # 본문·ERD가 아래까지 차는 쪽
for s, label, anchor in [(s_ent, '2. 표 만들기', 'm-tables'), (s_rel_text, '2. 표 만들기', 'm-tables'),
                         (s_rel_list, '2. 표 만들기', 'm-tables'), (s_chen, '2. 표 만들기', 'm-tables'),
                         (s_ie, '2. 표 만들기', 'm-tables'), (s_tx1, '3. 주문 트랜잭션', 'm-transaction'),
                         (s_tx2, '3. 주문 트랜잭션', 'm-transaction'), (s_flow, '3. 주문 트랜잭션', 'm-transaction'),
                         (s_crud_blank, '과제 ② 주문취소 CRUD 예측', 'm-assign2'), (s_crud_ans, '4. CRUD 측정', 'm-crud'),
                         (s_ent_rev, '2. 표 만들기', 'm-tables'), (s_ie_rev, '2. 표 만들기', 'm-tables')]:
    if s in (s_ie, s_ie_rev):                              # ERD가 바닥까지 → 상자들 오른쪽 빈 곳
        b = button(s, label, anchor, x=8.35, y=6.98, w=3.2); b.height = Inches(0.4)
    elif s in (s_ent, s_rel_text, s_ent_rev):
        b = button(s, label, anchor, **LOW_RIGHT); b.height = Inches(0.4)
    else:
        button(s, label, anchor)
    append_note(s, f'【Colab】 {label} 셀: {NB}#scrollTo={anchor}')

foot(s_tx1, '※ ACID: Atomicity·Consistency·Isolation·Durability (원자성·일관성·고립성·지속성) · Colab 3번 셀에서 재고 부족 시 전체 롤백을 확인', y=6.22)

# 18쪽(처리 흐름): 재고 차감 시점을 20쪽 CRUD와 맞춤
for sh in s_flow.shapes:
    if sh.has_text_frame:
        for p in sh.text_frame.paragraphs:
            if '재고 차감' in p.text and p.runs:
                p.runs[0].text = 'Product 테이블에서 가격·재고 확인(READ) → 재고 차감(UPDATE)은 결제 승인 때'
                for r in p.runs[1:]:
                    r.text = ''
append_note(s_flow, '【수정】 재고 차감 시점을 20쪽 CRUD 매트릭스(결제승인 Products U)와 맞췄다: 주문생성 때는 가격·재고를 읽기만(R) 하고, 결제 승인 때 차감한다. Colab 3번 셀이 같은 순서로 실행된다.')

# ── 새 쪽 B: 과제 ① 관계 차수 (IE ERD 다음)
B = new_slide(s_ie, '과제 ① | 관계 차수 맞히기')
tb(B, 0.98, 1.5, 11.4, 0.45, [('앞 쪽 ERD를 보고 Colab 입력칸에 1:1 또는 1:N을 넣으면, 실제 RDS의 제약조건(FK·UNIQUE)으로 바로 채점합니다.', {'size': 14.5, 'bold': True})])
table(B, 0.98, 2.1, [2.6, 6.1, 1.6], [
    ('관계', '근거가 되는 표·열', '차수'),
    ('고객 – 주문', 'orders.customer_id (FK)', '?'),
    ('주문 – 주문상세', 'order_details.order_id (FK, PK의 일부)', '?'),
    ('상품 – 주문상세', 'order_details.product_id (FK, PK의 일부)', '?'),
    ('주문 – 결제', 'payments.order_id (FK + UNIQUE)', '?'),
    ('주문 – 배송', 'deliveries.order_id (FK + UNIQUE)', '?'),
    ('고객 – 리뷰', 'reviews.customer_id (FK)', '?'),
    ('상품 – 리뷰', 'reviews.product_id (FK)', '?'),
], size=12, rh=0.42)
tb(B, 0.98, 5.6, 11.4, 0.4, [('힌트 · FK 열에 UNIQUE가 걸려 있으면 부모 1행당 자식이 최대 1행 → 1:1', {'size': 12, 'color': '7F6000', 'bold': True})])
tb(B, 6.0, 6.95, 6.3, 0.28, [('정답 · 1:N, 1:N, 1:N, 1:1, 1:1, 1:N, 1:N', {'size': 9.5, 'color': '8A96A8'})], align=PP_ALIGN.RIGHT)
foot(B, '※ ERD: Entity-Relationship Diagram · IE: Information Engineering 표기법 · FK: Foreign Key (외래키) · UNIQUE: 중복 금지 제약 · 1:1 일대일 · 1:N 일대다', y=6.22)
button(B, '과제 ① 관계 차수', 'm-assign1')
add_notes(B, '【슬라이드 핵심】 개념 모델의 관계 차수는 물리 모델에서 FK와 UNIQUE 제약으로 표현된다. 과제 ①은 ERD를 보고 차수를 예측하고, Colab이 실제 RDS의 제약조건으로 채점한다.\n'
             '【강의 설명】 고객–주문, 주문–주문상세, 상품–주문상세, 고객–리뷰, 상품–리뷰는 1:N이다. 주문–결제는 모든 주문에 결제 기록이 1건(필수 1:1), 주문–배송은 0..1(선택적 1:1)이며 두 경우 모두 자식 표의 order_id에 UNIQUE를 둔다. '
             '주문상세의 order_id는 (order_id, product_id) 복합 PK의 일부일 뿐 단독으로 UNIQUE가 아니므로 1:N이다. 틀린 관계만 다시 입력하게 되어 있다(최대 3번).\n'
             f'【연결】 {NB}#scrollTo=m-assign1 · 정답은 이 쪽 오른쪽 아래 작은 글씨')

# ── 19쪽(빈 CRUD): 과제 ② — 주문취소 행 추가
def add_row(tbl, values, fill=None):
    tr = copy.deepcopy(tbl._tbl.tr_lst[-1]); tbl._tbl.append(tr)
    row = tbl.rows[len(tbl.rows) - 1]
    for c, v in zip(row.cells, values):
        runs = c.text_frame.paragraphs[0].runs
        if runs:
            runs[0].text = v
            for r in runs[1:]:
                r.text = ''
        else:
            c.text_frame.paragraphs[0].add_run().text = v
        if fill:
            c.fill.solid(); c.fill.fore_color.rgb = RGB(fill)
    return row

tbl_blank = next(sh for sh in s_crud_blank.shapes if sh.has_table).table
add_row(tbl_blank, ['주문취소'] + [''] * 7, 'FFF3D9')
for i, row in enumerate(tbl_blank.rows):
    row.height = Inches(0.5 if i == 0 else 0.4)
tb(s_crud_blank, 5.9, 6.12, 6.4, 0.4, [('과제 ② · 빈칸을 채운 뒤, 노란 ‘주문취소’ 행을 Colab에 입력하세요 (정답 다음 쪽)', {'size': 11.5, 'bold': True, 'color': '7F6000'})], align=PP_ALIGN.RIGHT)
append_note(s_crud_blank, '【과제 ②】 학생은 먼저 4개 트랜잭션 행을 채운 뒤, 새 트랜잭션 ‘주문취소’(주문 상태 취소, 주문상세를 읽어 재고 복구, 결제 환불, 배송 준비 행 삭제)의 7칸을 Colab에 입력한다. Colab이 실제로 주문취소를 실행해 측정한 C·R·U·D와 칸마다 비교한다.')

# ── 20쪽(정답): 측정 결과 반영 + 주문취소 행
tbl_ans = next(sh for sh in s_crud_ans.shapes if sh.has_table).table
hdr = [c.text.replace('\x0b', ' ').replace('\n', ' ').strip() for c in tbl_ans.rows[0].cells]
od = next(i for i, h in enumerate(hdr) if h.replace(' ', '') == 'OrderDetails')
for row in list(tbl_ans.rows)[1:]:
    if row.cells[0].text.strip() in ('결제승인', '배송처리'):
        c = row.cells[od]
        runs = c.text_frame.paragraphs[0].runs
        if runs:
            runs[0].text = 'R'
        else:
            r = c.text_frame.paragraphs[0].add_run(); r.text = 'R'
        c.fill.solid(); c.fill.fore_color.rgb = RGB('FFE699')
add_row(tbl_ans, ['주문취소', '', 'U', 'R', 'U', 'D', 'U', ''], 'FFF3D9')
foot(s_crud_ans, '※ 노란 칸: Colab 4번 셀 측정 결과 반영(재고를 줄이거나 상품명을 읽으려면 주문상세를 거침) · 주문취소 = 과제 ② 정답 · CRUD: Create·Read·Update·Delete', y=6.0)
append_note(s_crud_ans, '【측정 반영】 Colab 4번 셀은 트랜잭션 안에서 pg_stat_xact_user_tables로 실제 C·R·U·D를 측정한다. 원본 정답과 다른 칸은 결제승인·배송처리의 Order Details(R) 두 칸이다. '
                        '결제 승인 때 재고를 줄이려면 주문상세의 수량을, 배송 때 송장에 상품명을 넣으려면 주문상세를 거쳐 상품을 읽어야 하기 때문이다. 주문취소 행(과제 ② 정답): Orders U, Order Details R, Payments U, Delivery D, Products U.')

# ── 새 쪽 C: 실습 끝내기 (결론 둘째 쪽 다음 = summary 앞)
C = new_slide(s_conc, '실습 끝내기 | AWS RDS 삭제')
tb(C, 0.98, 1.6, 11.4, 2.6, [
    [('1. ', {'bold': True}), '제출: 과제 ①·② 결과(⑥·⑨)와 4번 셀 CRUD 매트릭스를 캡처합니다.'],
    [('2. ', {'bold': True}), 'Colab 5. 삭제 셀을 실행하고 DELETE를 입력합니다.'],
    [('3. ', {'bold': True}), 'AWS의 실습 RDS(cd12-shop-lab)가 삭제되어 요금이 멈춥니다. 런타임을 다시 시작했어도 이 셀만 실행하면 됩니다.'],
    [('4. ', {'bold': True}), '다음 실습 때는 1번 셀이 RDS를 새로 만듭니다 (5~15분).'],
], size=16)
foot(C, '※ RDS는 켜져 있는 동안 요금이 나옵니다. 수업 끝에 반드시 삭제하세요.', y=6.0)
button(C, '5. 삭제', 'm-delete')
add_notes(C, '【슬라이드 핵심】 실습이 끝나면 Colab 5번 셀로 AWS 실습 RDS를 삭제한다.\n'
             '【강의 설명】 5번 셀은 보안 비밀의 AWS 키로 다시 인증하므로 런타임이 초기화돼도 단독 실행된다. DELETE를 입력하면 최종 스냅샷 없이 삭제하며 5~10분 뒤 사라진다. 이미 없으면 “이미 삭제됐습니다”를 출력한다.\n'
             f'【연결】 {NB}#scrollTo=m-delete')

prs.save(out)
pages = {i + 1: (s.shapes.title.text_frame.text.strip() if s.shapes.title is not None else '')[:28] for i, s in enumerate(prs.slides)}
print('ok · slides', len(prs.slides))
for k in (4, 8, 11, 12, 13, 14, 16, 17, 18, 19, 20, 23, 24, 29, 30):
    print(f'  {k:2}쪽 {pages[k]}')
