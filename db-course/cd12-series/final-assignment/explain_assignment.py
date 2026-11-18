# @title 과제 ③ 검증 · 완성한 주문 조회의 실행 계획 보기
if not callable(globals().get("order_query")):
    raise RuntimeError("먼저 과제 ③ 웹앱 셀을 실행하세요.")
query = order_query(1)
if query is None:
    print("TODO 2를 완성하고 웹앱 셀을 다시 실행한 뒤 검증하세요.")
else:
    for (line,) in read_rows(query, plan=True):
        print(line)
    print("고객 번호와 주문일 조건에 idx_orders_customer_date가 어떻게 도움이 되는지 설명하세요.")
