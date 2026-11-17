"""CD12-3 논리적·물리적 모델링 교안(26) — 12-1·12-2와 같은 형식(실습 쪽마다 Colab 셀 버튼, 개요·과제·실습 끝내기 쪽).
원본(18OCGd8-ZLmTlUzHJKIXYw_dlUFSt1C5y)은 그대로 두고 새 (26) 파일을 만든다. 12장 마지막 차시 → 실습 끝내기 = RDS 최종 삭제.
 새 쪽(원본 55장 → 59장): 4 Colab 실습 개요 · 21 과제 ① 무결성 제약 예측 · 35 과제 ② 파티션 수 예측 · 57 실습 끝내기(최종 삭제)
 🔎 퀴즈 정답 표시: 23 · 32 · 33쪽
 본문 오류 수정: 12쪽 phone VARCHAR(11)→(20) · 18쪽 '2.6 Reviews'→'2.7' · 31쪽 fillfactor 효과(페이지 분할 → HOT 업데이트)
                 · 34쪽 파티션 끝 값 '2024-12-31'→'2025-01-01'(TO는 미포함) · 39쪽 클러스터 주석(PK → 이메일 인덱스)
python build_deck.py <원본.pptx> <출력.pptx> <노트북ID>"""
import sys
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
O = list(prs.slides)                       # 원본 쪽 번호로 참조 (O[n-1])
assert len(O) == 55, len(O)


def txt(sl):
    return ' '.join(sh.text_frame.text for sh in sl.shapes if sh.has_text_frame) + ' '.join(
        c.text for sh in sl.shapes if sh.has_table for r in sh.table.rows for c in r.cells)


def orig(n, key):
    s = O[n - 1]
    assert key in txt(s), (n, key)
    return s


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


def button(sl, label, anchor, x=0.98, y=6.62, w=4.9, h=0.48, size=12.5):
    url = f'{NB}#scrollTo={anchor}' if anchor else NB
    b = sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    b.fill.solid(); b.fill.fore_color.rgb = RGB('EAF2FB'); b.line.color.rgb = RGB(NAVY); b.line.width = Pt(1)
    b.shadow.inherit = False
    tf = b.text_frame; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = f'Colab · {label}'; r.font.size = Pt(size); r.font.bold = True
    r.font.color.rgb = RGB(NAVY); r.font.name = FONT
    r.hyperlink.address = url
    b.click_action.hyperlink.address = url
    return b


def small_button(sl, label, anchor):
    """원본 본문이 아래까지 차는 쪽: 오른쪽 아래 작은 버튼"""
    return button(sl, label, anchor, x=7.75, y=7.0, w=3.6, h=0.38, size=11)          # 오른쪽 아래 학교 로고(11.6in~) 피함


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
    s = prs.slides.add_slide(orig(6, '1. 논리적 모델링의 개요').slide_layout)
    el = ids[-1]; ids.remove(el)
    pos = [i for i, e in enumerate(ids) if prs.part.related_part(e.rId) is after.part][0]
    ids.insert(pos + 1, el)
    for ph in list(s.placeholders):
        if ph.placeholder_format.idx != 0:
            ph._element.getparent().remove(ph._element)
    s.shapes.title.text_frame.text = title
    return s


def replace_in(sl, old, new):
    """문단 단위 바꾸기(첫 run 서식 유지)"""
    hit = 0
    for sh in sl.shapes:
        if not sh.has_text_frame:
            continue
        for p in sh.text_frame.paragraphs:
            if old in p.text and p.runs:
                p.runs[0].text = p.text.replace(old, new)
                for r in p.runs[1:]:
                    r.text = ''
                hit += 1
    assert hit, old
    return hit


def quiz_mark(s, text, x=1.0, y=7.05, w=6.6):
    tb(s, x, y, w, 0.28, [(text, {'size': 9.5, 'color': '8A96A8'})], align=PP_ALIGN.RIGHT)


# ── 원본 쪽 참조
s_goal = orig(3, '논리적 모델링 단계에서 수행되는 핵심 절차')
s_ent, s_ie = orig(8, '주요 엔티티 및 속성 식별(review)'), orig(10, 'ER-Diagram(IE 표기법)(review)')
s_rel = [orig(n, '릴레이션 스키마 예시') for n in range(11, 18)]
s_int = orig(19, '유일성 및 체크 제약')
s_tr1, s_tr2 = orig(21, '외래키 제약으로 반영'), orig(22, '비즈니스 룰 통합')
s_pov1, s_pov2 = orig(27, '저장 매개변수'), orig(28, '파티셔닝 및 클러스터링 적용')
s_ff1, s_ff2 = orig(29, 'Fillfactor'), orig(30, 'Fillfactor = 80')
s_idx, s_part, s_ts = orig(31, 'CLUSTER orders USING'), orig(32, 'PARTITION BY RANGE'), orig(33, 'CREATE TABLESPACE')
s_phys = [orig(n, '2. 주요 릴레이션 스키마') for n in range(35, 49)]
s_opt1, s_opt2 = orig(50, '테이블스페이스 설정'), orig(51, 'VACUUM 및 ANALYZE')
s_sum = orig(54, '논리적 모델링 단계에서는 개념적 모델링의 산출물')

# ── 본문 오류 수정 (노트에 【수정】으로 기록)
replace_in(s_rel[0], 'VARCHAR(11)', 'VARCHAR(20)')
append_note(s_rel[0], '【수정】 phone VARCHAR(11)은 예시 010-1234-5678(13자)이 들어가지 않아 VARCHAR(20)으로 고쳤다(물리 모델 38쪽과 같게).')
replace_in(s_rel[6], '2.6 Reviews', '2.7 Reviews')
replace_in(s_ff1, '여유 공간을 두어 페이지 분할 방지', '여유 공간을 두어 같은 페이지 안에서 갱신(HOT 업데이트)')
replace_in(s_ff1, '페이지 분할(TOAST/HEAP 분할)을 방지하고 성능 저하를 완화', 'UPDATE한 행을 다른 페이지로 옮겨 쓰며 인덱스까지 고치는 일을 줄여 성능 저하를 완화')
append_note(s_ff1, '【수정】 PostgreSQL 표(heap)는 B-tree처럼 페이지를 분할하지 않는다. UPDATE는 새 행 버전을 쓰는데, 같은 페이지에 빈 자리가 있으면 인덱스를 고치지 않는 HOT 업데이트가 된다. fillfactor는 이 빈 자리를 남겨 두는 설정이다(Colab 4번 셀에서 100 vs 80 측정). 【출처】 https://www.postgresql.org/docs/current/storage-hot.html')
replace_in(s_part, "('2024-12-31')", "('2025-01-01')")
append_note(s_part, "【수정】 RANGE 파티션의 TO 값은 포함되지 않으므로 TO ('2024-12-31')이면 12월 31일 주문이 들어갈 곳이 없다 → TO ('2025-01-01'). Colab 6번 셀에서 범위 밖 날짜가 거부되는 것을 확인한다. 【출처】 https://www.postgresql.org/docs/current/ddl-partitioning.html")
replace_in(s_phys[1], '클러스터링 적용: 향후 데이터 조회 성능 개선을 위해 primary key 인덱스 기준 클러스터링 가능', '클러스터링 적용: 이메일 순 조회가 잦다면 이메일 인덱스 기준으로 행 순서를 정렬')
append_note(s_phys[1], '【수정】 주석은 PK 인덱스 기준이라 했지만 아래 명령은 이메일 인덱스 기준이라 주석을 맞췄다. 논리 모델의 UNIQUE 제약은 이미 같은 인덱스를 자동으로 만들므로, Colab 7번 셀은 idx_customers_email을 따로 만들지 않고 customers_email_key로 CLUSTER한다.')

# ── 새 쪽 A: Colab 실습 개요 (학습목표 다음 → 4쪽)
A = new_slide(s_goal, 'Colab 실습 | 논리·물리 모델 확인')
tb(A, 0.98, 1.5, 11.4, 0.4, [('12-2의 RDS·shop을 이어받아 → 릴레이션 스키마·제약·성능 설계 확인 → 최종 삭제', {'size': 15, 'bold': True})])
tb(A, 0.98, 1.92, 11.4, 0.3, [[('실습 노트북  ', {'size': 11, 'color': GRAY}), (NB, {'size': 11, 'color': '1155CC', 'link': NB})]])
table(A, 0.98, 2.28, [2.5, 6.9, 2.0], [
    ('셀', '하는 일', '교안'),
    ('1. DB 생성', '중지된 RDS 다시 시작(없으면 새로 생성) → ④ 연결 확인', '이 쪽'),
    ('2. 논리 스키마', '🔎퀴즈 ① → 12-2 표 7개를 교안 릴레이션 스키마로 정렬', '12~18·23쪽'),
    ('3. 무결성 제약', '표마다 PK·FK·UNIQUE·CHECK·NOT NULL', '20쪽'),
    ('과제 ①', 'SQL 7개 성공(O)/실패(X) 예측 → 실제 실행으로 채점', '21쪽'),
    ('4. Fillfactor', '🔎퀴즈 ② → 100 vs 80, HOT 업데이트 비율', '31·32쪽'),
    ('5. 인덱스·클러스터링', '🔎퀴즈 ③ → 주문 30만 건 EXPLAIN 전/후', '33쪽'),
    ('6. 파티셔닝', '월별 RANGE 파티션 · 테이블스페이스', '34·36쪽'),
    ('과제 ②', '조회마다 읽는 파티션 수 예측 → EXPLAIN으로 채점', '35쪽'),
    ('7. 물리 설계 적용', '인덱스 7개·fillfactor 90·CLUSTER를 shop에', '38~51쪽'),
    ('8. 마무리', 'DELETE → RDS 최종 삭제 (12장 끝)', '57쪽'),
], size=11, rh=0.33, hl={4: 'FFF3D9', 8: 'FFF3D9', 10: 'FDE2E2'})
foot(A, '※ RDS: Relational Database Service · PK/FK: Primary/Foreign Key (기본키/외래키) · HOT: Heap-Only Tuple (같은 페이지 안 갱신) · EXPLAIN: 실행 계획 보기', y=6.0)
button(A, '1. DB 생성', 'l-db-create'); button(A, '노트북 처음부터 열기', None, x=6.05)
add_notes(A, '【슬라이드 핵심】 12-1·12-2와 같은 RDS(cd12-shop-lab)와 shop 스키마를 이어받아, 논리 모델(릴레이션 스키마·무결성 제약)과 물리 모델(fillfactor·인덱스·클러스터링·파티셔닝)을 실제로 확인하고 마지막에 RDS를 최종 삭제한다.\n'
             '【강의 설명】 1번 셀은 12-2에서 STOP으로 중지한 RDS를 다시 시작한다(없으면 새로 생성, 5~15분). 2번 셀은 12-2의 표 7개를 데이터는 그대로 둔 채 교안 12~18쪽 열 이름(product_name, payment_method 등)에 맞춘다. 앞 차시를 건너뛴 학생도 처음부터 만들어 진행할 수 있다. '
             '노란 줄이 중간 과제 2개, 🔎는 실행 전에 결과를 맞히는 예측 퀴즈(정답 23·32·33쪽 하단)다. 4~6번은 실험용 스키마 lab12_3에서 주문 30만 건으로 측정하고 7번에서 정리한다. 마지막 8번 셀에서 DELETE를 입력해 RDS를 지운다.\n'
             f'【연결】 {NB}\n【출처】 Colab 노트북(직접 작성, 로컬 PostgreSQL 16 TLS 환경에서 전 셀 검증)')

# ── 버튼·퀴즈 정답: 기존 쪽
for s in [s_ent, s_ie] + s_rel + [s_tr1]:
    small_button(s, '2. 논리 스키마', 'l-schema'); append_note(s, f'【Colab】 2. 논리 스키마 셀: {NB}#scrollTo=l-schema')
for s in (s_int, s_tr2):
    small_button(s, '3. 무결성 제약', 'l-integrity'); append_note(s, f'【Colab】 3. 무결성 제약 셀: {NB}#scrollTo=l-integrity')
for s, label, anchor in [(s_pov1, '4. Fillfactor', 'l-fillfactor'), (s_ff1, '4. Fillfactor', 'l-fillfactor'), (s_ff2, '4. Fillfactor', 'l-fillfactor'),
                         (s_idx, '5. 인덱스·클러스터링', 'l-index'),
                         (s_ts, '6. 파티셔닝·테이블스페이스', 'l-partition'), (s_opt1, '6. 파티셔닝·테이블스페이스', 'l-partition'),
                         (s_opt2, '6. 파티셔닝·테이블스페이스', 'l-partition'), (s_pov2, '7. 물리 설계 적용', 'l-physical')] + \
                        [(s, '7. 물리 설계 적용', 'l-physical') for s in s_phys]:
    small_button(s, label, anchor); append_note(s, f'【Colab】 {label} 셀: {NB}#scrollTo={anchor}')

b = button(s_part, '6. 파티셔닝', 'l-partition', x=8.4, y=4.25, w=3.6, h=0.38, size=11)     # 코드가 바닥까지 → 장점 오른쪽 빈 곳
append_note(s_part, f'【Colab】 6. 파티셔닝 셀: {NB}#scrollTo=l-partition')
quiz_mark(s_tr1, '🔎퀴즈 ① 정답 · FK 7개 (관계 하나 = FK 하나, 1:1은 FK 열에 UNIQUE)')
append_note(s_tr1, '【🔎퀴즈 ①】 12-2 ERD의 관계 7개는 외래키 7개가 된다(고객–주문, 주문–주문상세, 상품–주문상세, 주문–결제, 주문–배송, 고객–리뷰, 상품–리뷰). 1:1은 FK 열에 UNIQUE를 더해 표현한다. Colab 2번 셀이 실제 FK 개수를 출력한다.')
quiz_mark(s_ff2, '🔎퀴즈 ② 정답 · 80 (빈 공간 20% → UPDATE가 같은 페이지에서 끝남 = HOT)')
append_note(s_ff2, '【🔎퀴즈 ②】 Colab 4번 셀 측정(2만 행 중 10% UPDATE): fillfactor 100은 HOT 0%이고 표가 커지며, 80은 HOT 100%이고 표 크기가 그대로다. 대신 80은 처음부터 페이지가 약 25% 많다(공간과 갱신 성능의 맞바꿈). 【출처】 https://www.postgresql.org/docs/current/storage-hot.html')
quiz_mark(s_idx, '🔎퀴즈 ③ 정답 · 2) 인덱스 사용 (읽은 페이지 1,911 → 13)')
append_note(s_idx, '【🔎퀴즈 ③】 주문 30만 건에서 고객 1명(10건) 조회: 인덱스 전 Seq Scan으로 1,911페이지, 후 Bitmap Index Scan으로 13페이지(로컬 측정, RDS에서도 비슷). 일주일 합계는 CLUSTER 전 1,269페이지 → 후 46페이지(날짜 정렬도 0 → 1). CLUSTER는 한 번만 정렬하므로 이후 들어오는 행은 다시 흩어진다. 【출처】 https://www.postgresql.org/docs/current/sql-cluster.html')
append_note(s_ts, '【RDS】 Amazon RDS for PostgreSQL은 호환을 위해 테이블스페이스를 지원하지만 모든 저장소가 하나의 볼륨에 있어 디스크를 나눠 I/O를 분산하는 효과는 없다. Colab 6번 셀은 pg_tablespace 목록만 보여 준다. 【출처】 https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html (Tablespaces for RDS for PostgreSQL)')
append_note(s_part, '【Colab】 6번 셀은 orders_part를 2026년 1~3월 파티션으로 나누고, 2월 조회가 2월 파티션 하나만 읽는 것(파티션 프루닝)을 EXPLAIN으로 보여 준다.')

# ── 새 쪽 B: 과제 ① 무결성 제약 예측 (무결성 제약 쪽 다음 → 21쪽)
B = new_slide(s_int, '과제 ① | 이 SQL은 성공할까? 실패할까?')
tb(B, 0.98, 1.5, 11.4, 0.45, [('앞 쪽의 제약을 보고 O(성공)/X(실패)를 Colab에 입력하면, 실제로 실행해 어떤 제약이 막았는지 보여 줍니다.', {'size': 14, 'bold': True})])
table(B, 0.98, 2.05, [0.5, 3.2, 6.6, 1.0], [
    ('#', '상황', 'SQL (shop 스키마)', 'O / X'),
    ('1', '이미 있는 이메일로 고객 추가', "INSERT INTO customers(customer_id, name, email) VALUES (9001, '김중복', 'customer1@example.com')", '?'),
    ('2', '같은 고객이 주문 1건 더', "INSERT INTO orders(customer_id, total_amount, ship_address) VALUES (1, 19900, '서울 성동구')", '?'),
    ('3', '평점 6점 리뷰', "INSERT INTO reviews(customer_id, product_id, rating, …) VALUES (1, 101, 6, …)", '?'),
    ('4', '없는 고객(999)의 주문', "INSERT INTO orders(customer_id, …) VALUES (999, 1000, '서울')", '?'),
    ('5', '결제된 주문에 결제 1건 더', "INSERT INTO payments(order_id, amount, payment_method) VALUES (결제된 주문, …)", '?'),
    ('6', '상품 재고를 -1로', 'UPDATE products SET stock = -1 WHERE product_id = 101', '?'),
    ('7', '평점 5점 리뷰', "INSERT INTO reviews(customer_id, product_id, rating, …) VALUES (1, 101, 5, …)", '?'),
], size=10.5, rh=0.42)
tb(B, 0.98, 5.5, 11.4, 0.4, [('힌트 · 실패는 모두 PK·FK·UNIQUE·CHECK 중 하나가 막습니다. 실행은 마지막에 ROLLBACK → 데이터는 그대로', {'size': 12, 'color': '7F6000', 'bold': True})])
tb(B, 5.3, 6.95, 6.0, 0.28, [('정답 · X, O, X, X, X, X, O', {'size': 9.5, 'color': '8A96A8'})], align=PP_ALIGN.RIGHT)
foot(B, '※ UNIQUE: 중복 금지 · CHECK: 값의 범위 제한 · FK: Foreign Key (외래키) · PK: Primary Key (기본키) · ROLLBACK: 트랜잭션 되돌리기 · O/X: 성공/실패', y=6.22)
button(B, '과제 ① 무결성 제약 예측', 'l-assign1')
add_notes(B, '【슬라이드 핵심】 논리 모델의 무결성 제약(PK·FK·UNIQUE·CHECK)은 잘못된 데이터를 DB가 직접 거부하게 만든다. 과제 ①은 SQL 7개의 성공/실패를 예측하고 Colab이 실제로 실행해 채점한다.\n'
             '【강의 설명】 정답: 1 X(UNIQUE customers_email_key), 2 O, 3 X(CHECK rating 1~5), 4 X(FK orders → customers), 5 X(UNIQUE payments.order_id = 1:1 관계), 6 X(CHECK stock >= 0), 7 O. '
             '5번은 12-2 과제 ①의 “주문–결제 1:1”이 물리적으로 UNIQUE로 구현된 결과다. 모든 실행은 한 트랜잭션에서 SAVEPOINT로 하나씩 시험하고 마지막에 ROLLBACK하므로 shop 데이터는 바뀌지 않는다. 틀린 문항만 다시 입력한다(최대 3번).\n'
             f'【연결】 {NB}#scrollTo=l-assign1 · 정답은 이 쪽 오른쪽 아래 작은 글씨\n【출처】 https://www.postgresql.org/docs/current/ddl-constraints.html')

# ── 새 쪽 C: 과제 ② 파티션 수 예측 (Partitioning 쪽 다음 → 35쪽)
C = new_slide(s_part, '과제 ② | 이 조회는 파티션을 몇 개 읽을까?')
tb(C, 0.98, 1.5, 11.4, 0.45, [('Colab 6번 셀의 orders_part는 order_date로 3개(1·2·3월) 파티션입니다. 조회마다 읽는 파티션 수(1~3)를 입력하세요.', {'size': 14, 'bold': True})])
table(C, 0.98, 2.1, [3.4, 6.4, 1.6], [
    ('파티션', '범위 (FROM 포함 · TO 미포함)', '행 수(약)'),
    ('orders_2026_01', "FROM ('2026-01-01') TO ('2026-02-01')", '25,000'),
    ('orders_2026_02', "FROM ('2026-02-01') TO ('2026-03-01')", '23,000'),
    ('orders_2026_03', "FROM ('2026-03-01') TO ('2026-04-01')", '25,000'),
], size=11.5, rh=0.38)
table(C, 0.98, 3.85, [3.4, 6.4, 1.6], [
    ('조회', 'WHERE', '읽는 파티션 수'),
    ('1월 20일 ~ 3월 9일', "order_date >= '2026-01-20' AND order_date < '2026-03-10'", '?'),
    ('주문번호 5000번', 'order_id = 5000', '?'),
    ('3월 1일 하루', "order_date = '2026-03-01'", '?'),
    ('1월 31일 하루', "order_date = '2026-01-31'", '?'),
], size=11.5, rh=0.38, hl={1: 'FFF3D9', 2: 'FFF3D9', 3: 'FFF3D9', 4: 'FFF3D9'})
tb(C, 5.3, 6.95, 6.0, 0.28, [('정답 · 3, 3, 1, 1 (파티션 키가 아닌 조건은 모든 파티션을 읽음)', {'size': 9.5, 'color': '8A96A8'})], align=PP_ALIGN.RIGHT)
foot(C, '※ 파티션 프루닝(Partition Pruning): 조건에 맞지 않는 파티션을 읽지 않고 건너뜀 · RANGE: 값의 구간으로 나눔 · EXPLAIN: 실행 계획 보기', y=6.22)
button(C, '과제 ② 파티션 수 예측', 'l-assign2')
add_notes(C, '【슬라이드 핵심】 파티셔닝의 이점은 조건이 파티션 키(order_date)를 거를 때만 생긴다. 과제 ②는 조회 4개가 읽는 파티션 수를 예측하고 Colab이 EXPLAIN 실행 계획으로 채점한다.\n'
             '【강의 설명】 정답: ① 1/20~3/9는 세 달에 걸치므로 3개 ② order_id는 파티션 키가 아니므로 모든 파티션 3개 ③ 3월 1일은 3월 파티션의 FROM(포함) 값이므로 1개 ④ 1월 31일은 2월 파티션의 FROM 값(2-01) 전날이므로 1월 파티션 1개. '
             '경계 값(TO 미포함)을 헷갈리지 않는지가 핵심이다. 주문번호로 자주 찾는다면 order_id 인덱스가 필요하다.\n'
             f'【연결】 {NB}#scrollTo=l-assign2 · 정답은 이 쪽 오른쪽 아래 작은 글씨\n【출처】 https://www.postgresql.org/docs/current/ddl-partitioning.html')

# ── 새 쪽 D: 실습 끝내기 (summary 앞 → 57쪽)
D = new_slide(orig(53, '4. 마무리'), '실습 끝내기 | AWS RDS 최종 삭제 (12장 끝)')
tb(D, 0.98, 1.6, 11.4, 2.6, [
    [('1. ', {'bold': True}), '제출: 과제 ①·② 결과(⑦·⑪)와 5번 셀 인덱스·클러스터링 전/후 결과를 캡처합니다.'],
    [('2. ', {'bold': True}), 'Colab 8. 마무리 셀을 실행하고 DELETE를 입력합니다.'],
    [('3. ', {'bold': True}), 'AWS의 실습 RDS(cd12-shop-lab)가 스냅샷 없이 삭제되어 요금이 멈춥니다. 12-1~12-3의 shop 데이터도 함께 지워집니다.'],
    [('4. ', {'bold': True}), '런타임을 다시 시작했어도 이 셀만 실행하면 됩니다. 5~10분 뒤 RDS 콘솔에서 사라진 것을 확인하세요.'],
], size=18)
foot(D, '※ RDS: Relational Database Service · STOP(중지)은 7일 뒤 자동으로 다시 시작되므로 12장이 끝나면 DELETE로 지웁니다 · 보안 그룹은 요금이 없어 남겨 둡니다', y=6.0)
button(D, '8. 마무리 (DELETE)', 'l-delete')
add_notes(D, '【슬라이드 핵심】 12장 실습(12-1 쇼핑몰 DB → 12-2 개념 모델 → 12-3 논리·물리 모델)이 끝났으므로 Colab 8번 셀에서 DELETE로 RDS를 최종 삭제한다.\n'
             '【강의 설명】 8번 셀은 보안 비밀의 AWS 키로 다시 인증하므로 런타임이 초기화돼도 단독 실행된다. DELETE는 최종 스냅샷과 자동 백업 없이 삭제하므로 되돌릴 수 없다. 나중에 다시 볼 학생은 STOP을 입력할 수 있지만, AWS는 중지 7일 뒤 자동으로 다시 시작해 요금이 나오므로 끝나면 꼭 DELETE 하도록 안내한다.\n'
             f'【연결】 {NB}#scrollTo=l-delete\n【출처】 https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_StopInstance.html')

prs.save(out)
pages = {i + 1: (s.shapes.title.text_frame.text.strip() if s.shapes.title is not None else '')[:30] for i, s in enumerate(prs.slides)}
print('ok · slides', len(prs.slides))
for k in (4, 12, 18, 20, 21, 23, 33, 34, 35, 36, 37, 39, 52, 57, 58):
    print(f'  {k:2}쪽 {pages[k]}')
