"""CD11-3 미션 정답: 각 미션 셀의 input() 입력칸에 순서대로 넣을 값. 교안 '미션 정답' 페이지와 자동 시험에 사용."""
INPUTS = {
    'm1': ['주문', '매장', '주문상세', '결제', '계산값'],
    'm2': ['orders', 'menu', 'order_id, menu_id', 'orders(order_id)'],
    'm3': ['SUM(m.unit_price * i.qty)', 'SUM(m.unit_price * i.qty) / 11'],
    'm4': ['카드', '3000', '현금', '2500'],
    'm5': ['F4', 'f.field_name'],
    'hw': ['member_id TEXT PRIMARY KEY, card_no TEXT, points INTEGER',
           'order_id TEXT REFERENCES orders(order_id), member_id TEXT REFERENCES members(member_id), earned INTEGER, PRIMARY KEY (order_id, member_id)',
           "'CJ5505', '010****5505', 384",
           "'B0001', 'CJ5505', 28"],
}
WRONG = {   # 학생이 흔히 낼 오답 (시험용)
    'm1': ['주문', '주문', '메뉴', '결제', '주문'],
    'm2': ['order_items', 'menu', 'order_id', 'orders(order_id)'],
    'm3': ['SUM(m.unit_price)', 'SUM(m.unit_price)'],
    'm4': ['payment_method', '삼천', '현금', '2500'],
    'm5': ['석사', 'f.field_code'],
    'hw': ['member_id TEXT', 'order_id TEXT', "'CJ5505'", "'B0001'"],
}
