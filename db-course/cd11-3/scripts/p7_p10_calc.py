"""7·10쪽에 '계산값은 저장 안 함 · 예외(판매 당시 단가)' 표기, 실습1 정답 5개 유지: python p7_p10_calc.py <in> <out>"""
import sys, copy
from pptx import Presentation
prs = Presentation(sys.argv[1])
s7, s10 = prs.slides[6], prs.slides[9]


def by_text(s, start):
    return next(sh for sh in s.shapes if sh.has_text_frame and sh.text_frame.text.startswith(start))


def add_para(sh, text):  # 마지막 문단 서식 복제
    last = sh.text_frame.paragraphs[-1]._p
    new = copy.deepcopy(last); last.addnext(new)
    p = sh.text_frame.paragraphs[-1]
    p.runs[0].text = text
    for r in p.runs[1:]:
        r.text = ''


# 7쪽 표: 합계 영역 → 계산값 (저장 안 함)
tbl = next(sh for sh in s7.shapes if sh.has_table).table
cell = next(r.cells[2] for r in tbl.rows if r.cells[0].text.startswith('합계'))
cell.text_frame.paragraphs[0].runs[0].text = '계산값 (저장 안 함)'
add_para(by_text(s7, '같은 대상의 값끼리'), '합계·부가세는 계산값이라 표로 만들지 않음 → 실습1 정답 5개 테이블 (회원·포인트는 과제)')

# 10쪽: 리드 + 오른쪽 아래 메모에 예외
lead = by_text(s10, '영수증 1장이 5개')
lead.text_frame.paragraphs[0].runs[0].text = '영수증 1장이 5개 테이블의 행으로 나뉩니다. 합계·부가세는 저장하지 않고 계산, 회원·포인트는 📝 과제'
for r in lead.text_frame.paragraphs[0].runs[1:]:
    r.text = ''
add_para(by_text(s10, 'BILL 번호는'), '예외 · 판매 당시 단가는 주문상세에 함께 저장 (9쪽)')
prs.save(sys.argv[2]); print('ok')

# 노트: 본문과 일치하도록 【강의 설명】 끝에 한 문장 추가
prs = Presentation(sys.argv[2])
ADD = {7: ' 합계·부가세는 계산값이라 표로 만들지 않으므로 실습1 정답은 5개 테이블이고, 회원·포인트는 과제에서 추가합니다.',
       10: ' 합계·부가세는 저장하지 않고 주문상세×메뉴 단가로 계산합니다. 예외로 현업에서는 이미 발행한 영수증 금액을 지키기 위해 판매 당시 단가를 주문상세에 함께 저장합니다(9쪽).'}
for n, add in ADD.items():
    tf = prs.slides[n - 1].notes_slide.notes_text_frame
    p = next((p for p in tf.paragraphs if p.runs and '【강의 설명】' in ''.join(r.text for r in p.runs)), None)
    if p is not None and add.strip() not in tf.text:
        p.runs[-1].text += add
prs.save(sys.argv[2]); print('notes ok')
