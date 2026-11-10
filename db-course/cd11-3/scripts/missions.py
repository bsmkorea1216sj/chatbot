"""CD11-3 Colab 미션 셀 원고. 확인 함수는 힌트만 주고 정답은 교안 '미션 정답' 페이지에만 둔다."""

CHECKS = r'''#@title ✅ 미션 확인 도우미 — 코드는 보지 않아도 됩니다. 실행(▶)만 하세요 { display-mode: "form" }
# 미션 확인 함수 (정답은 교안의 '미션 정답' 페이지와 각 페이지 하단에 있습니다)
import sqlite3
HELPER_V = 2   # 도우미 버전 (미션 셀이 확인)
def _ok(cond, good, hint):
    print(('✅ ' + good) if cond else ('❌ ' + hint))
    return cond

def check_m1(ans):
    key = {'대기번호 241': '주문', '사업자번호 105-87-51367': '매장', '(ICE)아메리카노 2,000×2': '주문상세',
           '승인번호 21091497': '결제', '부가세 500': '계산값'}
    wrong = [k for k in key if ans.get(k, '').strip() != key[k]]
    return _ok(not wrong, '미션 1 통과: 5개 모두 맞았습니다.', f'{len(key) - len(wrong)}/5 정답 · 다시 볼 항목: {", ".join(wrong)}  (힌트: 교안 실습1 ① 표)')

def check_m2(sql):
    t = sqlite3.connect(':memory:'); t.execute('PRAGMA foreign_keys = ON')
    t.executescript("""CREATE TABLE stores (store_id TEXT PRIMARY KEY);
                       CREATE TABLE orders (order_id TEXT PRIMARY KEY, store_id TEXT REFERENCES stores(store_id));
                       CREATE TABLE menu (menu_id TEXT PRIMARY KEY, unit_price INTEGER);""")
    try:
        t.executescript(sql)
    except Exception as e:
        return _ok(False, '', f'SQL 오류: {e}  (입력한 표·열 이름을 확인하세요)')
    pk = sorted(r[1] for r in t.execute('PRAGMA table_info(order_items)') if r[5])
    fk_items = sorted((r[2], r[3]) for r in t.execute('PRAGMA foreign_key_list(order_items)'))
    fk_pay = sorted((r[2], r[3], r[4]) for r in t.execute('PRAGMA foreign_key_list(payments)'))
    a = _ok(pk == ['menu_id', 'order_id'], 'order_items 복합 PK 정답', 'order_items의 PK는 두 열을 함께 써야 합니다 (힌트: 교안 실습1 ②)')
    b = _ok([x[0] for x in fk_items] == ['menu', 'orders'], 'order_items의 FK 두 개 정답', 'order_items는 어느 두 표를 가리켜야 할까요?')
    c = _ok(fk_pay == [('orders', 'order_id', 'order_id')], 'payments의 FK 정답', 'payments는 어느 표의 어느 열을 가리켜야 할까요?')
    return a and b and c

def check_m3(sql):
    try:
        r = db.execute(sql).fetchone()
    except Exception as e:
        return _ok(False, '', f'SQL 오류: {e}')
    return _ok(tuple(r) == (5500, 500), f'미션 3 통과: 합계 {r[0]:,} · 부가세 {r[1]:,} (영수증과 일치)',
        f'결과 {tuple(r)} · 기대값은 영수증의 합계·부가세입니다 (힌트: 단가×수량, 부가세 = 합계 ÷ 11)')

def check_m4():
    n, s = db.execute("SELECT count(*), COALESCE(SUM(amount), 0) FROM payments WHERE order_id = 'B0001'").fetchone()
    methods = sorted(r[0] for r in db.execute("SELECT method FROM payments WHERE order_id = 'B0001'"))
    return _ok(n == 2 and s == 5500 and methods == ['카드', '현금'], f'미션 5 통과: 결제 {n}행 · 합계 {s:,}원 = 주문 합계',
        f'지금 결제 {n}행 · 합계 {s:,}원 · 수단 {methods} (힌트: 카드 3,000 + 현금 2,500 두 행)')

def check_m5(sql):
    fields = sorted(r[0] for r in db.execute("""SELECT f.field_name FROM consult_fields cf
                    JOIN fields f ON f.field_code = cf.field_code WHERE cf.consult_id = 'C001'"""))
    a = _ok(len(fields) == 3 and '대학(석사)' in fields, '대학(석사) 추가 정답 (C001 유학분야 3개)', f'C001 유학분야: {fields} (힌트: consult_fields에 한 행 추가)')
    try:
        rows = dict(db.execute(sql).fetchall())
    except Exception as e:
        return _ok(False, '', f'SQL 오류: {e}')
    return _ok(a and rows.get('대학(석사)') == 1 and rows.get('어학연수') == 1, f'GROUP BY 결과 정답: {rows}', f'결과 {rows} (힌트: 분야명별 상담 수)')

def check_hw():
    try:
        pk = sorted(r[1] for r in db.execute('PRAGMA table_info(point_logs)') if r[5])
        fks = sorted(r[2] for r in db.execute('PRAGMA foreign_key_list(point_logs)'))
        pts = db.execute("SELECT points FROM members WHERE member_id = 'CJ5505'").fetchone()
        earned = db.execute("SELECT earned FROM point_logs WHERE order_id = 'B0001'").fetchone()
    except Exception as e:
        return _ok(False, '', f'아직 표가 없습니다: {e}')
    a = _ok(pk == ['member_id', 'order_id'], 'point_logs 복합 PK 정답', 'point_logs의 PK는? (힌트: 주문과 회원)')
    b = _ok(fks == ['members', 'orders'], 'point_logs FK 정답', 'point_logs는 어느 두 표를 가리켜야 할까요?')
    return a and b and _ok(pts == (384,) and earned == (28,), '영수증 값 입력 정답 (가용 384 · 적립 28)', f'가용 포인트 {pts} · 적립 {earned} (힌트: 영수증 제휴카드 영역)')

def quiz(question, answer, page):
    # 예측 퀴즈: 입력하고 바로 확인 (정답은 교안 해당 쪽 하단)
    norm = lambda x: str(x).replace(',', '').replace(' ', '').replace('원', '').replace('개', '').replace('행', '').strip()
    for attempt in range(1, 3):
        if norm(input('🔎 ' + question + ' ')) == norm(answer):
            print('✅ 맞았습니다! 아래 결과로 확인하세요.'); return True
        print(f'❌ 다시 생각해 보세요 ({attempt}/2)')
    print(f'💡 정답은 교안 {page}쪽 하단에 있습니다. 아래 결과를 보고 확인하세요.'); return False

def retry(fn, tries=3, page=''):
    # 미션: 틀리면 셀을 다시 실행하지 않고 그 자리에서 다시 입력
    if fn.__name__ in ('mission3', 'mission4', 'mission5', 'homework') and 'db' not in globals():
        print('⚠️ 아직 실습 DB가 없습니다. 이 미션 위의 따라하기 셀부터 차례로 실행(▶)한 뒤 이 셀을 다시 실행하세요.')
        return False
    for attempt in range(1, tries + 1):
        try:
            ok = fn()
        except NameError as e:
            print(f'⚠️ 아직 준비되지 않은 값이 있습니다 ({e}).\n   이 미션 위의 따라하기 셀부터 차례로 실행(▶)한 뒤 이 셀을 다시 실행하세요.')
            return False
        if ok:
            return True
        if attempt < tries:
            print(f'↻ 다시 입력하세요 ({attempt}/{tries})\n')
    print(f'💡 {tries}번 모두 통과하지 못했습니다. 교안 {page}쪽을 다시 보고 셀을 다시 실행하세요.')
    return False

print('✅ 준비 완료: 미션 셀을 실행하면 입력칸이 나오고, 바로 결과를 확인합니다.')'''

GUARD = r"""if globals().get('HELPER_V') != 2:   # 맨 위 ✅ 도우미 셀을 안 돌렸거나 옛 버전이면 자동으로 준비
    try:
        from google.colab import _message
        exec(next(''.join(c['source']) for c in _message.blocking_request('get_ipynb')['ipynb']['cells'] if ''.join(c['source']).startswith('#@title ✅')))
    except Exception:
        print('⚠️ 맨 위 ✅ 미션 확인 도우미 셀을 먼저 실행(▶)하세요.'); raise SystemExit
"""

M1 = r'''# 🎯 미션 1 · 실행하면 입력칸이 나옵니다. 각 영수증 값이 어느 개체인지 입력하세요 (틀리면 바로 다시 입력)
# 보기: 매장 / 주문 / 주문상세 / 메뉴 / 결제 / 계산값
items = ['대기번호 241', '사업자번호 105-87-51367', '(ICE)아메리카노 2,000×2', '승인번호 21091497', '부가세 500']
def mission1():
    return check_m1({k: input(f"'{k}' → 어느 개체? (매장/주문/주문상세/메뉴/결제/계산값): ").strip() for k in items})
retry(mission1, page=7)'''

M2 = r'''# 🎯 미션 2 · 입력칸 4개에 표 이름·열 이름만 입력하세요 (따옴표 없이, 틀리면 바로 다시 입력)
def mission2():
    t1 = input('① order_items.order_id 가 가리킬 표 이름: ').strip()
    t2 = input('② order_items.menu_id 가 가리킬 표 이름: ').strip()
    pk = input('③ order_items 의 기본키(PK) 열 2개 (쉼표로 구분): ').strip()
    fk = input("④ payments.order_id 가 가리킬 '표(열)' 예: 표이름(열이름): ").strip()
    sql = f"""CREATE TABLE order_items (order_id TEXT REFERENCES {t1}(order_id), menu_id TEXT REFERENCES {t2}(menu_id),
                                qty INTEGER NOT NULL, PRIMARY KEY ({pk}));
CREATE TABLE payments (payment_id TEXT PRIMARY KEY, order_id TEXT NOT NULL REFERENCES {fk}, method TEXT, amount INTEGER NOT NULL);"""
    print(sql)
    return check_m2(sql)
retry(mission2, page=8)'''

M3 = r'''# 🎯 미션 3 · 합계와 부가세를 구하는 식을 입력하세요 (틀리면 바로 다시 입력)
# 사용할 수 있는 열: m.unit_price(단가), i.qty(수량) · 함수: SUM( )
def mission3():
    total_expr = input('① 합계(total)를 구하는 식: ').strip()
    vat_expr   = input('② 부가세(vat)를 구하는 식: ').strip()
    sql = f"""SELECT {total_expr} AS total, {vat_expr} AS vat
FROM order_items i JOIN menu m ON m.menu_id = i.menu_id WHERE i.order_id = 'B0001'"""
    print(sql)
    return check_m3(sql)
retry(mission3, page=9)'''

M4 = r'''# 🎯 미션 5 · 손님이 나눠 낸 결제를 저장합니다 (교안 17쪽 '검증' 토론)
# 수단은 글자(예: 카드), 금액은 숫자만 입력하세요. 확인 후 원래 결제로 자동 복원
def mission4():
    m1, a1 = input('① 첫 번째 결제 수단: ').strip(), input('① 첫 번째 결제 금액(숫자): ').strip()
    m2, a2 = input('② 두 번째 결제 수단: ').strip(), input('② 두 번째 결제 금액(숫자): ').strip()
    db.execute("SAVEPOINT m4")
    try:
        db.execute("DELETE FROM payments WHERE order_id = 'B0001'")
        db.execute("INSERT INTO payments VALUES ('P02', 'B0001', ?, '카카오뱅크체크', '21091498', ?)", (m1, int(a1)))
        db.execute("INSERT INTO payments VALUES ('P03', 'B0001', ?, NULL, NULL, ?)", (m2, int(a2)))
        return check_m4()
    except ValueError:
        print('❌ 금액은 숫자만 입력하세요 (예: 3000)'); return False
    finally:
        db.execute("ROLLBACK TO m4"); db.execute("RELEASE m4")
retry(mission4, page=17)'''

M5 = r'''# 🎯 미션 4 · 상담 C001에 '대학(석사)'를 추가하고, 유학분야별 상담 수를 세세요 (틀리면 바로 다시 입력)
print('유학분야 코드표:', db.execute('SELECT field_code, field_name FROM fields').fetchall())
def mission5():
    code_in = input("① '대학(석사)'의 분야코드: ").strip()
    group_in = input('② 분야명별로 묶을 열 (GROUP BY 뒤에 올 열): ').strip()
    db.execute("SAVEPOINT m5")
    try:
        db.execute("INSERT OR IGNORE INTO consult_fields VALUES ('C001', ?)", (code_in,))
    except sqlite3.IntegrityError:
        print(f"❌ '{code_in}'은(는) 코드표에 없는 분야코드입니다. 위 코드표에서 찾아 입력하세요")
    ok = check_m5(f"""SELECT f.field_name, COUNT(*) FROM consult_fields cf
                      JOIN fields f ON f.field_code = cf.field_code GROUP BY {group_in}""")
    if not ok:
        db.execute("ROLLBACK TO m5")          # 틀린 입력은 데이터에 남기지 않음
    db.execute("RELEASE m5")
    return ok
retry(mission5, page=14)'''

HW = r'''# 📝 과제 · 영수증의 제휴카드(CJ ONE) 영역을 테이블로 확장하세요 (틀리면 바로 다시 입력)
#   - members: 회원ID(PK), 카드번호(마스킹), 가용 포인트
#   - point_logs: 주문ID·회원ID(복합 PK, 각각 FK), 적립 포인트
#   - 영수증 값: 회원 CJ5505 · 카드 010****5505 · 가용 384 · 주문 B0001 적립 28
# 괄호 ( ) 안에 들어갈 내용만 한 줄로 입력하세요
def homework():
    cols_m  = input('① members 열 정의  예: member_id TEXT PRIMARY KEY, ... : ').strip()
    cols_pl = input('② point_logs 열 정의 (FK·복합 PK 포함): ').strip()
    vals_m  = input("③ members 에 넣을 값  예: 'CJ5505', ... : ").strip()
    vals_pl = input('④ point_logs 에 넣을 값: ').strip()
    sql = f"""DROP TABLE IF EXISTS point_logs; DROP TABLE IF EXISTS members;
CREATE TABLE members ({cols_m});
CREATE TABLE point_logs ({cols_pl});
INSERT INTO members VALUES ({vals_m});
INSERT INTO point_logs VALUES ({vals_pl});"""
    print(sql)
    try:
        db.executescript(sql)
    except Exception as e:
        print('❌ SQL 오류:', e); return False
    return check_hw()
retry(homework, page=20)'''

# 예측 퀴즈: 따라하기 셀 바로 앞에서 결과를 먼저 예측하고 바로 확인
Q1 = r"""# 🔎 예측 퀴즈 · 아래 따라하기 셀을 실행하기 전에 결과를 먼저 맞혀 보세요
quiz('회원·포인트(📝 과제)를 빼면, 영수증 1장은 몇 개의 테이블에 저장될까요? (숫자)', 5, 10)"""
Q2 = r"""# 🔎 예측 퀴즈 · 아래 따라하기 셀을 실행하기 전에 결과를 먼저 맞혀 보세요
quiz('주문 B0001의 합계는 얼마일까요? (숫자)', 5500, 17)"""
Q3 = r"""# 🔎 예측 퀴즈 · 아래 따라하기 셀을 실행하기 전에 결과를 먼저 맞혀 보세요
quiz('ICE 아메리카노 단가를 2,200원으로 바꾸면 합계는 얼마가 될까요? (숫자)', 5900, 9)"""
Q4 = r"""# 🔎 예측 퀴즈 · 아래 따라하기 셀을 실행하기 전에 결과를 먼저 맞혀 보세요
quiz('유학분야를 2개 고른 상담 1건은 consult_fields에 몇 행으로 저장될까요? (숫자)', 2, 14)"""

# (미션 번호, 마크다운 제목, 코드)
def _g(src):  # 머리 주석 1줄 뒤에 GUARD 삽입
    head, rest = src.split('\n', 1)
    return head + '\n' + GUARD + rest
M1, M2, M3, M4, M5, HW, Q1, Q2, Q3, Q4 = map(_g, (M1, M2, M3, M4, M5, HW, Q1, Q2, Q3, Q4))

CELLS = {
    'm1': ('## 🎯 미션 1 · 영수증 값 → 개체 분류  (교안 실습1 ① · 7쪽)\n셀을 실행하면 나오는 입력칸에 답을 입력하세요. 결과가 ✅이면 통과입니다.', M1),
    'm2': ('## 🎯 미션 2 · PK·FK 정하기  (교안 실습1 ② · 8쪽 / 정답 표 10쪽)\n셀을 실행하면 나오는 입력칸 4개에 표 이름·열 이름을 입력하세요.', M2),
    'm3': ('## 🎯 미션 3 · 합계·부가세를 계산으로 구하기  (교안 실습1 ③ · 9쪽)\n합계 = Σ(단가 × 수량), 부가세 = 합계 ÷ 11', M3),
    'm4': ('## 🎯 미션 4 · 다중 선택과 GROUP BY  (교안 실습2 ② · 14쪽 / 정답 15쪽)', M5),
    'm5': ('## 🎯 미션 5 · 나눠 낸 결제 저장하기  (교안 검증 · 17쪽 토론)\n입력칸에 결제 수단과 금액을 넣으세요. 확인 후 자동으로 원래 결제로 되돌립니다.', M4),
    'hw': ('## 📝 과제 · 회원·포인트 테이블로 확장  (교안 실습 마무리 · 18쪽)\n제출: 이 셀의 SQL과 ✅ 결과 화면 캡처. 정답은 교안 \'미션 정답\' 페이지에서 확인합니다.', HW),
}
