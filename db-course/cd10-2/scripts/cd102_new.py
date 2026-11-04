# (템플릿 원본 번호, 삽입 위치(원본 번호 뒤), 텍스트, 노트)
# 템플릿 4·30: [tag,title,sub,label1,body1,label2,body2,label3,body3,footer] / 템플릿 28: [tag,title,sub,code_lines,footer]
NEW = [
(4, 9, ["현업 사례 · 인덱스 비용", "GitLab: 인덱스를 추가하기 전에 확인하는 것",
  "조회가 느리다고 인덱스부터 만들면 무엇이 문제일까?",
  "공개 사례", "GitLab은 공개 개발 문서에서 인덱스는 공짜가 아니며(저장 공간·쓰기 비용·유지 작업), 실제 쿼리와 실행계획으로 필요성을 확인한 뒤 추가하도록 안내합니다.",
  "교안 연결", "인덱스는 읽기를 빠르게 하지만 INSERT·UPDATE·DELETE마다 함께 갱신되어 쓰기와 공간 비용이 늘어납니다.",
  "토론", "이미 (last_name, first_name) 복합 인덱스가 있는데 last_name 단일 인덱스를 또 만들면 어떨까요?",
  "출처: GitLab Docs · Adding database indexes (docs.gitlab.com)"],
 "【슬라이드 핵심】 GitLab의 인덱스 추가 원칙: 인덱스는 비용이 있으므로 실제 쿼리·실행계획으로 필요성을 확인 후 추가.\n"
 "【강의 설명】 앞 슬라이드(장단점)의 '적합하지 않은 인덱스는 오히려 느려질 수 있음'을 실제 기업 개발 가이드로 확인합니다. 인덱스가 많을수록 INSERT·UPDATE 때 함께 고쳐야 할 구조가 늘고(앞 Uber 사례와 같은 원리), 디스크와 메모리(shared_buffers)도 차지합니다.\n"
 "토론 정답: 복합 인덱스 (last_name, first_name)은 맨 앞 컬럼 last_name 단독 조건에도 쓰일 수 있으므로 last_name 단일 인덱스는 대부분 중복입니다 → 쓰기 비용만 늘어남.\n"
 "【연결】 Uber 사례, Index Only Scan(복합 인덱스), Colab 실습 1(인덱스 전후 비교).\n"
 "【출처】 GitLab Docs, Adding database indexes (수업 전 원문 문구 확인 권장)"),
(4, 22, ["핵심 개념 · JOIN", "조인 방식 3가지: Planner는 무엇을 고를까?",
  "같은 JOIN이라도 데이터 양에 따라 실행 방법이 바뀝니다.",
  "Nested Loop", "바깥 테이블 한 행마다 안쪽 테이블을 반복해서 찾습니다. 결과가 적고 안쪽에 인덱스가 있을 때 유리합니다. (예: 고객 1명의 주문)",
  "Hash Join", "작은 쪽으로 해시 테이블(메모리, work_mem)을 만들고 큰 쪽을 훑으며 짝을 찾습니다. 대량의 등가 조인(=)에 유리합니다.",
  "Merge Join", "양쪽을 조인 키 순서로 정렬(또는 인덱스 순서 이용)한 뒤 지퍼처럼 맞춥니다. 둘 다 크고 이미 정렬돼 있을 때 유리합니다.",
  "실습 3·Colab 2: 고객 1명 → 9,000명으로 범위를 넓히면 Nested Loop가 Hash Join으로 바뀌는지 확인합니다."],
 "【슬라이드 핵심】 조인 실행 방식 3가지(Nested Loop, Hash Join, Merge Join)와 각각 유리한 상황.\n"
 "【강의 설명】 스캔 방식(Sequential·Index·Bitmap·Index Only)이 '테이블 하나를 어떻게 읽나'라면, 조인 방식은 '두 테이블을 어떻게 짝짓나'입니다. Planner는 예상 행 수(통계)로 비용을 계산해 고릅니다(10-1 Planner 단원).\n"
 "비유: Nested Loop = 손님 한 명씩 명부에서 찾아보기, Hash Join = 명부를 이름표 상자로 분류해 두고 한 번에 맞추기, Merge Join = 가나다순으로 정렬된 두 명단을 나란히 놓고 맞추기.\n"
 "【연결】 학생 실습 3(조회 범위가 달라질 때의 조인), Colab 실습 2.\n"
 "【출처】 https://www.postgresql.org/docs/17/planner-optimizer.html"),
(28, 30, ["Colab 실습 · 1", "인덱스 전후: Seq Scan → Index Scan",
  "접속 셀은 CD10-1과 같습니다. 노트북에서 순서대로 실행합니다.",
  ["cur.execute('''CREATE TABLE IF NOT EXISTS cd10_orders AS",
   "  SELECT i AS order_id, (i % 10000) + 1 AS customer_id, repeat('X', 100) AS memo",
   "  FROM generate_series(1, 100000) g(i)''')",
   "q = 'SELECT * FROM cd10_orders WHERE customer_id = 42'",
   "plan(q)                                   # 인덱스 전",
   "cur.execute('CREATE INDEX IF NOT EXISTS idx_cd10_orders_cust ON cd10_orders (customer_id)')",
   "cur.execute('ANALYZE cd10_orders')",
   "plan(q)                                   # 인덱스 후"],
  "기록: 스캔 노드(Seq Scan → Bitmap/Index Scan), Buffers, Execution Time을 전·후로 비교합니다."],
 "【슬라이드 핵심】 같은 조회를 인덱스 전·후로 실행해 스캔 노드·버퍼·실행시간 비교.\n"
 "【강의 설명】 인덱스 전에는 10만 행 전체를 읽는 Seq Scan, 인덱스 후에는 해당 고객 10행만 찾는 Bitmap Heap Scan(또는 Index Scan)이 나옵니다. customer_id=42인 주문이 테이블 곳곳에 흩어져 있어 Bitmap 방식이 자주 선택됩니다(Bitmap Index Scan 슬라이드). plan()은 노트북에 정의된 EXPLAIN (ANALYZE, BUFFERS) 출력 함수입니다.\n"
 "【연결】 스캔 방식 슬라이드, 인덱스 추가 전후 비교 항목, 학생 실습 2(pgAdmin)와 같은 내용을 Colab으로 재현.\n"
 "【자료】 CD10-2_Colab_Lab(26).ipynb"),
(28, 30, ["Colab 실습 · 2", "조회 범위에 따른 조인 방식 변화",
  "고객 1명과 9,000명을 조회할 때 Planner가 고르는 조인 방식을 비교합니다.",
  ["cur.execute('''CREATE TABLE IF NOT EXISTS cd10_customers AS",
   "  SELECT i AS customer_id FROM generate_series(1, 10000) g(i)''')",
   "cur.execute('ANALYZE cd10_customers')",
   "for cond in ('c.customer_id = 42', 'c.customer_id <= 9000'):",
   "    plan(f'''SELECT c.customer_id, o.order_id",
   "             FROM cd10_customers c JOIN cd10_orders o",
   "               ON c.customer_id = o.customer_id",
   "             WHERE {cond}''')"],
  "기대: 1명 → Nested Loop, 9,000명 → Hash Join (데이터 양에 따라 Planner가 방식을 바꿈)."],
 "【슬라이드 핵심】 조인 조건의 범위(1명 vs 9,000명)에 따라 Nested Loop ↔ Hash Join이 바뀌는 것을 관찰.\n"
 "【강의 설명】 1명이면 주문 인덱스로 10행만 찾으면 되므로 Nested Loop, 9,000명이면 주문 9만 건을 읽어야 하므로 인덱스를 9만 번 타는 것보다 Hash Join + Seq Scan이 쌉니다. '인덱스가 있어도 안 쓰는 것이 정답일 수 있다'가 핵심입니다(학생 실습 제출의 해석 질문과 같은 답).\n"
 "【연결】 조인 방식 3가지 슬라이드, 학생 실습 3."),
(30, 30, ["Colab 실습 · 제출", "실행계획으로 인덱스·조인 선택 설명하기",
  "관찰한 실행계획을 근거로 Planner의 선택을 설명합니다.",
  "비교", "인덱스 전·후의 스캔 노드, Buffers, Execution Time과 1명·9,000명 조회의 조인 노드를 표로 정리합니다.",
  "해석", "9,000명 조회에서 인덱스가 있는데도 Hash Join과 Seq Scan을 고른 이유를 비용(cost) 관점에서 설명합니다.",
  "심화", "같은 컬럼에 B-tree와 BRIN 인덱스를 만들고 pg_relation_size로 크기를 비교해 봅니다.",
  "노트북: CD10-2_Colab_Lab(26).ipynb · 판단 기준: 관찰값 → 스캔/조인 방식 → 선택 이유"],
 "【슬라이드 핵심】 Colab 결과로 인덱스·조인 선택 이유를 설명하는 제출 과제.\n"
 "【강의 설명】 해석 정답 방향: 결과가 전체의 90%면 인덱스로 한 행씩 찾는 비용(랜덤 접근)이 전체를 순서대로 읽는 비용보다 큽니다. 심화 기대 결과: BRIN은 블록 범위의 최소·최대값만 저장해 B-tree보다 훨씬 작습니다(BRIN 슬라이드). 단, customer_id처럼 값이 흩어진 컬럼에서는 BRIN 효과가 작고, 시간순으로 쌓이는 컬럼(order_id, 날짜)에서 효과가 큽니다.\n"
 "【연결】 BRIN 인덱스, 스캔 방식 비교표, 학생 실습 제출."),
]
