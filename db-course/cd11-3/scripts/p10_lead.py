"""10쪽 리드 문구에 '회원·포인트는 과제' 명시 (7쪽 개체 6개와 10쪽 테이블 5개 차이 설명): python p10_lead.py <in> <out>"""
import sys
from pptx import Presentation
prs = Presentation(sys.argv[1])
sh = next(s for s in prs.slides[9].shapes if s.has_text_frame and s.text_frame.text.startswith('영수증 1장이 5개 테이블'))
r = sh.text_frame.paragraphs[0].runs
r[0].text = '영수증 1장이 5개 테이블의 행으로 나뉩니다. (7쪽의 회원·포인트는 📝 과제에서 표 2개로 추가)'
for x in r[1:]:
    x.text = ''
prs.save(sys.argv[2]); print('ok')
