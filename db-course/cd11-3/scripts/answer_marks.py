"""11-3 미션 페이지의 Colab 버튼 아래에 작은 정답 표시: python answer_marks.py <in.pptx> <out.pptx>"""
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

MARKS = {
    7: '정답 · 대기번호→주문 · 사업자번호→매장 · (ICE)아메리카노→주문상세 · 승인번호→결제 · 부가세→계산값',
    8: '정답 · ① orders  ② menu  ③ order_id, menu_id  ④ orders(order_id)',
    9: '정답 · ① SUM(m.unit_price * i.qty)  ② SUM(m.unit_price * i.qty) / 11',
    10: '정답 · ① orders  ② menu  ③ order_id, menu_id  ④ orders(order_id)',
    14: '정답 · ① F4 (대학(석사))  ② f.field_name',
    15: '정답 · ① F4 (대학(석사))  ② f.field_name',
    17: '정답 · ① 카드 · 3000  ② 현금 · 2500',
    18: '정답 · 과제 입력값 ①~④는 20쪽 (members · point_logs 열 정의와 값)',
}
prs = Presentation(sys.argv[1])
for n, text in MARKS.items():
    s = prs.slides[n - 1]
    if not any(sh.has_text_frame and ('Colab 미션' in sh.text_frame.text or 'Colab 과제' in sh.text_frame.text) for sh in s.shapes):
        print('no badge on', n); continue
    for sh in list(s.shapes):
        if sh.name == '미션 정답 표시' or (sh.has_text_frame and sh.text_frame.text.startswith('정답 · ')):
            sh._element.getparent().remove(sh._element)
    tb = s.shapes.add_textbox(Inches(2.6), Inches(6.8), Inches(9.65), Inches(0.28))
    tb.name = '미션 정답 표시'
    tf = tb.text_frame; tf.word_wrap = True
    tf.margin_top = tf.margin_bottom = Inches(0)
    p = tf.paragraphs[0]; p.alignment = 3          # 오른쪽 정렬 (버튼 아래)
    r = p.add_run(); r.text = text
    r.font.size = Pt(9.5); r.font.name = 'Malgun Gothic'; r.font.color.rgb = RGBColor(0x8A, 0x96, 0xA8)
prs.save(sys.argv[2])
print('marks added:', list(MARKS))
