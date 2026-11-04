"""CD10-1 노트북 실습 3·심화·인사이트 셀 원고 (요약 표 중심). colab_patch.py와 colab_nb.py에서 사용."""

LAB3 = '''import pandas as pd
if "connect" not in globals():
    raise RuntimeError("먼저 맨 위 pip 셀과 '실습 1' 셀(AWS 인증·DB 접속)을 실행하세요.")
if "c1" not in globals() or c1.closed:
    c1 = connect("cd10_1_session_A")      # 런타임이 다시 시작됐으면 자동 재연결
c1.autocommit = True; cur = c1.cursor()

def walk(p, d=0):
    yield d, p
    for ch in p.get("Plans", []):
        yield from walk(ch, d + 1)

def name(n):
    pre = n.get("Partial Mode", "") if n.get("Partial Mode") not in (None, "Simple") else ""
    pre = (pre + " ") if pre else ("Parallel " if n.get("Parallel Aware") else "")
    return pre + n["Node Type"]

# ① 일부러 오류 내기: SQL 처리 몇 단계에서 멈추나?
rows = []
for sql, stage in [("SELEC * FROM film", "1단계 Parser (문법 검사)"),
                   ("SELECT * FROM filmx", "2단계 Analyzer (의미 검사)")]:
    try:
        cur.execute(sql)
    except Exception as e:
        rows.append([sql, type(e).__name__, stage, str(e).splitlines()[0]])
display(pd.DataFrame(rows, columns=["SQL", "오류", "멈춘 단계", "메시지"]))

# ② 실습 테이블: payment가 없으면 20만 행 테이블을 한 번만 생성
cur.execute("SELECT to_regclass('payment')")
T = "payment"
if cur.fetchone()[0] is None:
    T = "cd10_lab_payment"
    cur.execute(f"""CREATE TABLE IF NOT EXISTS {T} AS
        SELECT g AS payment_id,
               round((random() * 10)::numeric, 2) AS amount,
               now() - g * interval '1 minute' AS payment_date
        FROM generate_series(1, 200000) AS g""")
    cur.execute(f"ANALYZE {T}")

# ③ 같은 SELECT를 두 번: Planner의 선택(계획)과 Executor의 결과(실제)
q = f"SELECT sum(amount) FROM {T} WHERE amount >= 3"
summary = []
for i in (1, 2):
    cur.execute("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + q)
    res = cur.fetchone()[0][0]
    plan = res["Plan"]
    if i == 1:
        print(f"[실행계획 트리] 테이블 {T} · 아래(들여쓰기 깊은 쪽)부터 실행해 위로 올라옵니다")
        for d, n in walk(plan):
            rel = f" on {n['Relation Name']}" if "Relation Name" in n else ""
            print("    " * d + f"└ {name(n)}{rel}  (추정 {n['Plan Rows']:,}행 · 실제 {n['Actual Rows']:,}행)")
    scan = next(n for _, n in walk(plan) if "Scan" in n["Node Type"])
    summary.append([f"{i}차", name(scan),
                    f"{scan['Plan Rows']:,}", f"{scan['Actual Rows']:,}",
                    plan.get("Shared Hit Blocks", 0), plan.get("Shared Read Blocks", 0),
                    res.get("Planning", {}).get("Shared Read Blocks", 0),
                    round(res["Execution Time"], 1)])
display(pd.DataFrame(summary, columns=["실행", "스캔 방식(Planner 선택)", "추정 행(작업자당)", "실제 행(작업자당)",
                                       "shared hit(메모리)", "shared read(새로 읽음)", "계획 단계 read", "실행시간(ms)"]))'''

DEEP = '''if "T" not in globals():
    raise RuntimeError("먼저 '실습 3' 셀을 실행하세요. (실습 테이블과 실행계획 함수를 준비합니다)")
rows = []
for wm in ("64kB", "4MB", "32MB"):
    cur.execute(f"SET work_mem = '{wm}'")
    cur.execute(f"EXPLAIN (ANALYZE, FORMAT JSON) SELECT * FROM {T} ORDER BY amount, payment_date")
    sort = next(n for _, n in walk(cur.fetchone()[0][0]["Plan"]) if n["Node Type"] == "Sort")
    where = "메모리" if sort.get("Sort Space Type") == "Memory" else "디스크"
    rows.append([wm, sort.get("Sort Method"), f"{sort.get('Sort Space Used', 0):,}kB", where])
cur.execute("RESET work_mem")
display(pd.DataFrame(rows, columns=["work_mem", "정렬 방식", "사용 공간", "정렬 위치"]))'''

INSIGHT3 = '''> **결과 인사이트 · 읽는 순서**
>
> **① 오류 표 → 몇 단계에서 멈췄나**
> | SQL | 오류 | 멈춘 단계 |
> |---|---|---|
> | `SELEC * FROM film` | SyntaxError | 1단계 **Parser** (문법이 틀림) |
> | `SELECT * FROM filmx` | UndefinedTable | 2단계 **Analyzer** (문법은 맞지만 테이블이 없음) |
>
> **② 실행계획 트리 → 아래에서 위로 읽기**
> `Parallel Seq Scan`(전체를 2개 작업자가 나눠 읽기) → `Partial Aggregate`(각자 합계) → `Gather`(모으기) → `Finalize Aggregate`(최종 합계)
> → `amount`에 인덱스가 없어서 **Planner**가 전체 읽기를 골랐습니다.
>
> **③ 1차·2차 비교 표 (실측)**
> | 항목 | 1차 | 2차 | 의미 |
> |---|---|---|---|
> | 추정 행 / 실제 행 (작업자당) | 82,607 / 70,144 | 같음 | 통계가 실제와 비슷 → 계획이 적절 |
> | shared hit / read | 1,280 / 0 | 1,280 / 0 | 테이블(약 10MB)이 이미 메모리(Shared Buffer)에 있음 |
> | 계획 단계 read | **1** | **0** | 1차에 시스템 정보를 디스크에서 1번 읽고, 2차부터 메모리에서 읽음 → **read → hit 변화** |
> | 실행시간 | 약 45ms | 약 45ms | **Executor**가 실제로 실행한 시간 |
>
> - 테이블 본문은 방금 만들어서 1차부터 메모리에 있었기 때문에 1·2차 차이가 없습니다. 처음 읽는 큰 테이블이면 1차에 read가 많고 2차에 hit로 바뀝니다.'''
