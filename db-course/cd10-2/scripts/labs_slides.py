"""CD10-2 29~35번 실습 슬라이드를 단계 안내 + 예상 결과 패널로 정리, 노트북과 일치: python labs_slides.py <in.pptx> <out.pptx>"""
import sys
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches

_src = (Path(__file__).resolve().parents[2] / 'cd10-1' / 'scripts' / 'pgadmin_labs.py').read_text(encoding='utf-8')
_h = {}
exec(_src.split('# 39 · 세션 관찰')[0].replace("prs = Presentation(sys.argv[1])", "prs = None"), _h)
find, set_lines, panel = _h['find'], _h['set_lines'], _h['panel']

prs = Presentation(sys.argv[1])
S = lambda n: prs.slides[n - 1]
TITLE = '예상 결과 (실행 후 실측값으로 확인)'


def narrow(slide, start, lines, size):
    code = find(slide, start)
    code.width = Inches(6.75)
    set_lines(code, lines, size=size)


# 29 · pgAdmin 실습 1
s = S(29)
set_lines(find(s, '같은 pgAdmin Query Tool'), ['① 한 창에서 아래 코드 실행 → ② 실습 2·3도 같은 창에서 이어서 진행'])
narrow(s, 'DROP TABLE IF EXISTS', ['-- 이전 실습 테이블 정리', 'DROP TABLE IF EXISTS pg_temp.cd10_orders;',
       'DROP TABLE IF EXISTS pg_temp.cd10_customers;', '-- 고객 1만 명', 'CREATE TEMP TABLE cd10_customers AS',
       'SELECT i AS customer_id FROM generate_series(1, 10000) g(i);', '-- 주문 10만 건 (고객당 10건)',
       'CREATE TEMP TABLE cd10_orders AS', 'SELECT i AS order_id, (i % 10000) + 1 AS customer_id,',
       "       repeat('X', 100) AS memo FROM generate_series(1, 100000) g(i);",
       'ANALYZE cd10_customers;  ANALYZE cd10_orders;'], 12.5)
panel(s, 8.05, 3.0, 4.35, 3.45, TITLE, [
    ('고객 10,000행 · 주문 100,000행', 'b'), ('→ customer_id 1~10000이 반복, 고객당 주문 10건', 'n'),
    ('TEMP 테이블', 'b'), ('→ 이 창(연결)에서만 보이고, 창을 닫으면 사라짐', 'n'),
    ('ANALYZE', 'b'), ('→ 통계를 만들어 Planner가 행 수를 정확히 예측', 'n')])

# 30 · pgAdmin 실습 2
s = S(30)
set_lines(find(s, '1번 SELECT를'), ['① 인덱스 전 SELECT 실행·기록 → ② 인덱스 생성 → ③ 같은 SELECT 다시 실행·비교'])
narrow(s, '-- 1. 인덱스', ['-- ①·③ 인덱스 전·후에 각각 실행', 'EXPLAIN (ANALYZE, BUFFERS)',
       'SELECT * FROM cd10_orders WHERE customer_id = 42;', '', '-- ② 첫 실행계획을 기록한 다음 실행',
       'CREATE INDEX idx_cd10_orders_customer', '    ON cd10_orders (customer_id);', 'ANALYZE cd10_orders;'], 14)
panel(s, 8.05, 3.0, 4.35, 3.45, TITLE, [
    ('① 인덱스 전: Seq Scan on cd10_orders', 'b'), ('→ 10만 행을 모두 읽고 10행 반환', 'n'),
    ('③ 인덱스 후: Bitmap Heap Scan ← Bitmap Index Scan', 'b'), ('→ 그 고객의 페이지만 골라 읽음', 'n'),
    ('local read·hit 수와 실행시간이 크게 줄어듦', 'b'), ('TEMP 테이블은 Buffers가 local로 표시됩니다.', 's')])
set_lines(find(s, '결과는 모두'), ['기록: 결과는 둘 다 10행. 스캔 노드, local buffers, Execution Time을 전·후로 비교합니다.'])

# 31 · pgAdmin 실습 3
s = S(31)
set_lines(find(s, '먼저 고객 1명'), ['① 고객 1명(= 42)으로 실행 → ② 마지막 줄을 <= 9000으로 바꿔 다시 실행'])
code = find(s, 'EXPLAIN (ANALYZE')
code.width = Inches(6.75)
panel(s, 8.05, 3.0, 4.35, 3.45, TITLE, [
    ('고객 1명 → Nested Loop', 'b'), ('→ 한 명씩 인덱스로 주문을 찾아 짝짓기', 'n'),
    ('고객 9,000명 → Hash Join', 'b'), ('→ 양쪽을 한 번에 읽어(Seq Scan) 해시로 짝짓기', 'n'),
    ('인덱스가 있어도 안 쓰는 것이 더 쌀 수 있음', 'b'), ('Planner는 예상 행 수로 비용을 계산합니다.', 's')])

# 32 · pgAdmin 제출
s = S(32)
set_lines(find(s, '인덱스 전·후의 반환'), ['표 1장: 인덱스 전·후(스캔 노드, 읽은 페이지, 시간) │ 1명·9,000명(조인 방식, 테이블별 스캔)'])
set_lines(find(s, '인덱스가 있어도 전체의'), ['9,000명은 주문의 90%: 인덱스로 9천 번 찾기 vs 한 번에 읽기, 어느 쪽이 쌀까요?'])
set_lines(find(s, 'Index Only Scan의 Heap'), ['Index Only Scan의 Heap Fetches가 0이 아니면? (힌트: VACUUM과 가시성 정보)'])

# 33 · Colab 실습 1
s = S(33)
set_lines(find(s, '접속 셀은'), ['인덱스 전·후 실행계획을 트리와 비교 표로 확인합니다. (셀이 접속까지 자동으로 함)'])
narrow(s, "cur.execute('''CREATE TABLE IF NOT EXISTS cd10_orders", [
    "q = 'SELECT * FROM cd10_orders WHERE customer_id = 42'",
    "drop_idx = 'DROP INDEX IF EXISTS idx_cd10_orders_cust'",
    "make_idx = 'CREATE INDEX ... ON cd10_orders (customer_id)'",
    "for label, ddl in [('① 인덱스 전', drop_idx), ('② 인덱스 후', make_idx)]:",
    "    cur.execute(ddl); cur.execute('ANALYZE cd10_orders')",
    '    res = explain(q)          # EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)',
    '    show_tree(res, label)     # 실행계획 트리 출력',
    '    rows.append([label, 스캔 방식, 결과 행, 읽은 페이지, 실행시간])',
    'display(pd.DataFrame(rows, ...))   # 전·후 비교 표'], 12.5)
panel(s, 8.05, 3.0, 4.35, 3.45, TITLE, [
    ('① 인덱스 전: Seq Scan', 'b'), ('→ 테이블 전체 페이지를 읽음', 'n'),
    ('② 인덱스 후: Bitmap Heap Scan ← Bitmap Index Scan', 'b'), ('→ 수십 페이지 이하만 읽음', 'n'),
    ('결과 행은 둘 다 10행', 'b'), ('같은 결과, 다른 실행 방법 = Planner의 선택', 's')])
set_lines(find(s, '기록:'), ['기록: 비교 표의 스캔 방식·읽은 페이지 수·실행시간을 전·후로 비교합니다.'])

# 34 · Colab 실습 2
s = S(34)
narrow(s, "cur.execute('''CREATE TABLE IF NOT EXISTS cd10_customers", [
    "for label, cond in [('고객 1명', 'c.customer_id = 42'),",
    "                    ('고객 9,000명', 'c.customer_id <= 9000')]:",
    "    res = explain(f'''SELECT c.customer_id, o.order_id",
    '                      FROM cd10_customers c JOIN cd10_orders o',
    '                        ON c.customer_id = o.customer_id',
    "                      WHERE {cond}''')",
    '    show_tree(res, label)',
    '    rows.append([label, 조인 방식, 테이블별 스캔, 결과 행, 실행시간])',
    'display(pd.DataFrame(rows, ...))   # 조인 방식 비교 표'], 12.5)
panel(s, 8.05, 3.0, 4.35, 3.45, TITLE, [
    ('고객 1명 → Nested Loop', 'b'), ('→ 결과가 적어 인덱스로 하나씩 찾기', 'n'),
    ('고객 9,000명 → Hash Join', 'b'), ('→ 양쪽 Seq Scan 후 해시로 한 번에 짝짓기', 'n'),
    ('예상 행 수가 방식을 바꾼다', 'b'), ('조인 방식 3가지 슬라이드와 연결', 's')])
set_lines(find(s, '기대:'), ['확인: 비교 표의 조인 방식과 테이블별 스캔이 범위에 따라 어떻게 바뀌는지 기록합니다.'])

# 35 · Colab 제출
s = S(35)
set_lines(find(s, '같은 컬럼에 B-tree'), ['심화 셀의 표에서 B-tree와 BRIN 크기를 "테이블 대비 %"로 비교하고 이유를 설명합니다.'])

notes = {
    29: '【변경】 단계 안내와 예상 결과 패널 추가. 예상 결과는 아직 실측 전입니다.',
    30: '【예상 결과】 인덱스 전 Seq Scan, 후 Bitmap Heap Scan ← Bitmap Index Scan. TEMP 테이블이라 Buffers는 local hit/read로 나옵니다.',
    31: '【예상 결과】 = 42 → Nested Loop, <= 9000 → Hash Join (양쪽 Seq Scan). 정확한 노드는 PostgreSQL 버전·통계에 따라 다를 수 있습니다.',
    33: '【변경】 노트북 실습 1이 트리와 전·후 비교 표로 출력되도록 바뀌어 코드를 맞췄습니다. 셀이 접속까지 스스로 하고, 인덱스를 먼저 지운 뒤 비교하므로 여러 번 실행해도 같은 비교가 됩니다.',
    34: '【변경】 노트북 실습 2가 조인 방식 비교 표로 출력됩니다(조회 범위, 조인 방식, 테이블별 스캔, 결과 행, 실행시간).',
    35: '【변경】 심화 셀은 테이블·B-tree·BRIN 크기와 테이블 대비 %를 표로 보여 줍니다.',
}
for n, t in notes.items():
    tf = S(n).notes_slide.notes_text_frame
    tf.text = (tf.text or '') + '\n' + t

prs.save(sys.argv[2])
print('saved', sys.argv[2])
