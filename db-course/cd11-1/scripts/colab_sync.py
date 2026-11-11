"""CD11-1_Colab_Lab(26).ipynb 를 교안(11-1 보강본) 흐름에 맞게 수정.
- 첫 셀 쪽 번호: 교안 42~46쪽 (도입 42 · 준비 43 · 실습1 44 · 실습2 45 · 실습3 46)
- 준비 셀 분리(교안 '준비' 슬라이드와 1:1), 실습1 셀 ID(UuenQc24FOvc) 유지
- payments: status('failed'/'approved')·attempted_at 추가, amount > 0 (교안 38쪽 '0보다 커야', 실패 기록은 남김)
- 실습3 인덱스: (order_id, attempted_at DESC) 복합 인덱스 (교안 38쪽 물리 설계)
- 기업 사례: AWS 문제는 29쪽 예시와 다른 조회 패턴임을 명시, 29쪽 표 형식으로 제출
python colab_sync.py <in.ipynb> <out.ipynb>"""
import json, sys

src, out = sys.argv[1:3]
nb = json.load(open(src))
C = {c['metadata'].get('id'): c for c in nb['cells']}


def md(cid, text):
    return {'cell_type': 'markdown', 'metadata': {'id': cid}, 'source': text}


def code(cid, text):
    return {'cell_type': 'code', 'metadata': {'id': cid}, 'source': text, 'outputs': [], 'execution_count': None}


INTRO = """# CD11-1 주문·결제 데이터베이스 설계 실습

교안 **42~46쪽**의 흐름대로 **준비 → 관계 설계 → 제약과 롤백 → 안전한 조회와 실행계획 → 기업 사례 비교**를 실습합니다.

| 노트북 | 교안 |
|---|---|
| 준비 · 실습 환경 열기 | 43쪽 Colab 준비 |
| 실습 1 · 개체와 관계를 테이블로 | 44쪽 (설계 근거: 38쪽 결제 실패와 재시도) |
| 실습 2 · 잘못된 입력과 롤백 | 45쪽 |
| 실습 3 · 안전한 조회와 실행계획 · 기업 사례 비교 | 46쪽 (비교 기준: 29쪽 개념·논리·물리) |

Google Colab에서 노트북을 열고 위에서부터 실행하세요. SQLite 메모리 DB와 가상 데이터를 사용합니다. 런타임을 다시 시작했다면 **준비 셀부터** 다시 실행하세요. 카드번호는 저장하지 않고 결제 참조값만 사용합니다."""

PREP_MD = """## 준비 · 실습 환경 열기 (교안 43쪽)

메모리 DB를 만들고 외래키 검사를 켭니다. 확인값 `(1,)`은 검사가 켜졌다는 뜻입니다."""

PREP = """import sqlite3

db = sqlite3.connect(":memory:", cached_statements=0)   # 실행계획 비교가 매번 새로 계산되도록 캐시 끔
db.execute("PRAGMA foreign_keys = ON")
assert db.execute("PRAGMA foreign_keys").fetchone() == (1,)
print("외래키 검사:", db.execute("PRAGMA foreign_keys").fetchone())"""

LAB1_MD = """## 실습 1 · 개체와 관계를 테이블로 옮기기 (교안 44쪽)

결제에 실패해 다시 시도하면 주문을 새로 만들어야 할까요? 주문은 그대로 두고 **결제 시도**를 별도 행으로 기록합니다(교안 38쪽).

- 고객 1명 → 주문 여러 건
- 주문 1건 → 결제 시도 여러 건 (실패 시도도 `status='failed'`로 남김)
- 주문 1건 → 작업 기록 여러 건

기본키(PK)는 각 행을 구분합니다. 외래키(FK)는 다른 테이블의 행을 가리킵니다. 결제 금액은 **0보다 커야** 합니다. 아래 셀에서 주문 1번의 결제 시도 두 건(실패 → 승인)을 확인하고, **승인된 결제 합계 = 주문 금액**인지 봅니다."""

LAB1 = """db.executescript(\"\"\"
DROP TABLE IF EXISTS action_log; DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS orders;     DROP TABLE IF EXISTS customers;
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    status TEXT NOT NULL,
    total_amount INTEGER NOT NULL CHECK (total_amount >= 0)
);
CREATE TABLE payments (
    payment_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(order_id),
    payment_ref TEXT NOT NULL UNIQUE,
    amount INTEGER NOT NULL CHECK (amount > 0),
    status TEXT NOT NULL CHECK (status IN ('failed', 'approved')),
    attempted_at TEXT NOT NULL
);
CREATE TABLE action_log (
    action_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(order_id),
    actor TEXT NOT NULL,
    action_type TEXT NOT NULL,
    note TEXT
);

INSERT INTO customers VALUES (1, '실습 고객');
INSERT INTO orders VALUES (1, 1, 'paid', 1200);
INSERT INTO payments VALUES (1, 1, 'demo-pay-01', 1200, 'failed', '2026-03-02 10:00');
INSERT INTO payments VALUES (10, 1, 'demo-pay-retry', 1200, 'approved', '2026-03-02 10:03');
INSERT INTO action_log VALUES (1, 1, 'payment_service', 'payment_failed', '첫 번째 시도');
INSERT INTO action_log VALUES (2, 1, 'payment_service', 'payment_approved', '재시도 승인');
\"\"\")

rows = db.execute(\"\"\"
    SELECT payment_id, payment_ref, status FROM payments
    WHERE order_id = ? ORDER BY payment_id
\"\"\", (1,)).fetchall()
assert len(rows) == 2
print("주문 1번의 결제 시도:", rows)
approved = db.execute(
    "SELECT SUM(amount) FROM payments WHERE order_id = ? AND status = 'approved'", (1,)
).fetchone()[0]
total = db.execute("SELECT total_amount FROM orders WHERE order_id = ?", (1,)).fetchone()[0]
assert approved == total
print(f"승인 합계 {approved:,}원 = 주문 금액 {total:,}원 (실패 시도는 기록만 남음)")
print("주문 1번의 작업 기록:", db.execute(
    "SELECT action_type FROM action_log WHERE order_id = ? ORDER BY action_id", (1,)
).fetchall())"""

LAB2_MD = """## 실습 2 · 잘못된 입력과 롤백 확인하기 (교안 45쪽)

없는 주문에 결제를 연결하면 **FK**, 0 이하 금액을 넣으면 **CHECK**, 결제 참조값을 재사용하면 **UNIQUE**가 막습니다.

마지막에는 정상 삽입과 실패하는 삽입을 한 트랜잭션에 넣습니다. 오류가 난 뒤 롤백하고, 앞서 정상적으로 삽입한 행도 사라졌는지 조회합니다."""

LAB2 = """insert = "INSERT INTO payments VALUES (?, ?, ?, ?, ?, ?)"
t = '2026-03-02 11:00'
tests = [
    ("FOREIGN KEY", (2, 999, "demo-fk", 1200, "approved", t)),
    ("CHECK", (2, 1, "demo-amount", -1, "approved", t)),
    ("UNIQUE", (2, 1, "demo-pay-01", 1200, "approved", t)),
]
for expected, row in tests:
    try:
        with db:
            db.execute(insert, row)
    except sqlite3.IntegrityError as error:
        assert expected in str(error), str(error)
        print(error)
    else:
        raise AssertionError(f"{expected} 제약 시험 실패")

try:
    with db:
        db.execute(insert, (3, 1, "demo-rollback", 300, "approved", t))
        db.execute(insert, (4, 999, "demo-missing-order", 300, "approved", t))
except sqlite3.IntegrityError as error:
    assert "FOREIGN KEY" in str(error)
else:
    raise AssertionError("롤백 시험 실패")
assert db.execute("SELECT COUNT(*) FROM payments WHERE payment_id = 3").fetchone() == (0,)
print("롤백 확인: 결제 3번이 남아 있지 않습니다.")"""

LAB3_MD = """## 실습 3 · 안전하게 조회하고 실행계획 비교하기 (교안 46쪽)

1. `WHERE payment_ref = ?`에 정상 참조값과 SQL 조건식처럼 보이는 문자열을 각각 바인딩합니다. 결과가 각각 1건, 0건인지 확인합니다.
2. **주문별 최근 결제 시도**를 조회하는 쿼리에 `EXPLAIN QUERY PLAN`을 실행합니다. 교안 38쪽 물리 설계의 `(order_id, attempted_at DESC)` 복합 인덱스 전후로 `SCAN`과 `SEARCH`를 비교합니다. 실행계획은 DB가 행을 찾는 방법을 보여줍니다."""

LAB3 = """query = "SELECT payment_id FROM payments WHERE payment_ref = ?"
for value, expected in [("demo-pay-01", [(1,)]), ("' OR 1=1 --", [])]:
    result = db.execute(query, (value,)).fetchall()
    assert result == expected
    print(repr(value), result)

plan = "EXPLAIN QUERY PLAN SELECT amount, status FROM payments WHERE order_id = ? ORDER BY attempted_at DESC"
db.execute("DROP INDEX IF EXISTS payments_order_time_idx")
before = db.execute(plan, (1,)).fetchall()
db.execute("CREATE INDEX payments_order_time_idx ON payments(order_id, attempted_at DESC)")
after = db.execute(plan, (1,)).fetchall()
print("인덱스 전:", [r[-1] for r in before])
print("인덱스 후:", [r[-1] for r in after])
assert "SCAN" in before[0][-1] and "SEARCH" in after[0][-1]"""

CASE_MD = """## 기업 사례 비교와 제출 (교안 46쪽 · 비교 기준 29쪽)

같은 주문·결제 문제를 세 가지 관점으로 설명하세요. 교안 29쪽처럼 **개념 · 논리 · 물리** 단계로 나눠 표에 정리합니다.

| 단계 · 관점 | 작성할 내용 |
| --- | --- |
| 개념 · Palantir | 고객·주문·결제 시도 객체의 관계와 결제 승인·실패 작업을 ERD와 설명으로 표현 |
| 논리 · Google Cloud | 결제 데이터 제품의 필드 정의(금액·상태·시도 시각), 소유자, 이용 부서, 접근 권한을 정의 |
| 물리 · AWS | “**주문 번호로 결제 시도 목록을 최신순으로 조회한다**”는 조회 패턴에 맞춰 파티션 키와 정렬 키를 제안 (29쪽 예시 ‘고객별 최근 주문’과 **다른** 조회 패턴입니다) |

**제출물**은 ERD, 실행한 SQL, 제약 오류 3종과 롤백 결과, 안전한 조회 결과와 실행계획 전후 비교, 기업 사례 비교표(29쪽 형식)입니다.

[Python sqlite3](https://docs.python.org/3/library/sqlite3.html) · [SQLite 외래키](https://www.sqlite.org/foreignkeys.html) · [SQLite 실행계획](https://www.sqlite.org/eqp.html)"""

cells = [md('C95pLu0zFOva', INTRO),
         md('prep_md_cd111', PREP_MD), code('prep_cd111', PREP),
         md('hxmh7PBiFOvb', LAB1_MD), code('UuenQc24FOvc', LAB1),
         md('ypneRNZyFOvd', LAB2_MD), code('lcMAL2vHFOvd', LAB2),
         md('i58fGN_qFOve', LAB3_MD), code('HeAPqFCXFOve', LAB3),
         md('j7zp2hbpFOve', CASE_MD)]
for c in cells:                                     # 기존 셀 메타데이터(기타 키) 유지
    old = C.get(c['metadata']['id'])
    if old:
        meta = dict(old['metadata']); meta.update(c['metadata']); c['metadata'] = meta
nb['cells'] = cells
json.dump(nb, open(out, 'w'), ensure_ascii=False, indent=1)
print('cells:', [c['metadata']['id'] for c in cells])
