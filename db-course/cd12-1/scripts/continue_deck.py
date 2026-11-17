"""12-1 교안: 5번 셀 '삭제' → '마무리(STOP)', 최종 삭제는 12-3 마지막 (continue_chain.py와 짝).
 - 31쪽 Colab 실습 표 5행·첫 줄·노트
 - 34쪽 실습 끝내기 본문·버튼 글자·노트
도형 이름은 Google Slides 저장 때 바뀌므로 텍스트로 찾는다.
python continue_deck.py <in.pptx> <out.pptx>"""
import sys
from pptx import Presentation

src, out = sys.argv[1:3]
prs = Presentation(src)

def set_runs(p, text):
    """첫 run에 새 글자, 나머지 run은 비움 (서식 유지)"""
    p.runs[0].text = text
    for r in p.runs[1:]:
        r.text = ''

def find_slide(key):
    hits = [s for s in prs.slides if any(sh.has_text_frame and key in sh.text_frame.text for sh in s.shapes)]
    assert len(hits) == 1, (key, len(hits))
    return hits[0]

def set_notes(s, old, new):
    tf = s.notes_slide.notes_text_frame
    for p in tf.paragraphs:
        if old in p.text and p.runs:
            set_runs(p, p.text.replace(old, new))

# ── 31쪽 Colab 실습 개요
s31 = find_slide('Colab 실습 | 쇼핑몰 DB에서 웹앱까지')
for sh in s31.shapes:
    if sh.has_text_frame and sh.text_frame.text.startswith('AWS에 실습 RDS를 만들고'):
        set_runs(sh.text_frame.paragraphs[0], 'AWS에 RDS 생성 → 표·검증·웹앱 실습 → STOP으로 중지 (12-2에서 이어서)')
    if sh.has_table:
        for row in sh.table.rows:
            if row.cells[0].text.strip() in ('5. 삭제', '5. 마무리'):
                set_runs(row.cells[0].text_frame.paragraphs[0], '5. 마무리')
                set_runs(row.cells[1].text_frame.paragraphs[0], 'STOP을 입력해 RDS를 중지합니다(데이터 유지 → 12-2에서 이어서). 최종 삭제는 12-3 마지막.')
            if row.cells[0].text.strip() == '2. 표 만들기':
                set_runs(row.cells[1].text_frame.paragraphs[0], '표 5개와 관계(FK)를 shop 스키마에 만들고 ⑤ 출력으로 확인합니다.')
set_notes(s31, '제출 후 5번 셀에서 DELETE를 입력하면 RDS가 삭제되어 요금이 멈춘다.',
          '2번 셀의 표는 고정 스키마 shop에 만들어져 12-2가 이어받는다. 제출 후 5번 셀에서 STOP을 입력하면 RDS가 중지되어(인스턴스 요금 중지, 데이터 유지) 12-2의 1번 셀이 다시 시작한다. 최종 삭제는 12-3 마지막 셀에서 한다.')
set_notes(s31, '표·검증·웹앱으로 실습한 뒤 삭제한다.', '표·검증·웹앱으로 실습한 뒤 중지한다(12-2·12-3에서 이어서, 최종 삭제는 12-3).')

# ── 34쪽 실습 끝내기
s34 = find_slide('실습 끝내기')
body = next(sh for sh in s34.placeholders if sh.placeholder_format.idx == 1)
NEW = {'Colab 5. 삭제 셀을 실행하고 DELETE를 입력합니다.': 'Colab 5. 마무리 셀을 실행하고 STOP을 입력합니다.',
       '웹앱 미리보기를 끄고 AWS의 실습 RDS(cd12-shop-lab)를 삭제합니다.': '웹앱 미리보기를 끄고 RDS(cd12-shop-lab)를 중지합니다. shop 데이터는 남아 12-2에서 이어서 씁니다.',
       'RDS는 켜져 있는 동안 요금이 나오므로 제출 후 바로 삭제합니다. 다음 실습 때 1번 셀이 새로 만듭니다.':
       '중지 중에는 인스턴스 요금이 멈춥니다(7일 뒤 자동 시작). 다음 수업의 1번 셀이 다시 시작하고, 최종 삭제는 12-3 마지막 셀에서 합니다.'}
for p in body.text_frame.paragraphs:
    if p.text.strip() in NEW and p.runs:
        set_runs(p, NEW[p.text.strip()])
for sh in s34.shapes:
    if sh.has_text_frame and sh.text_frame.text.strip() == 'Colab · 5. 삭제':
        set_runs(sh.text_frame.paragraphs[0], 'Colab · 5. 마무리 (STOP)')
tf = s34.notes_slide.notes_text_frame
tf.text = ('【슬라이드 핵심】 제출 후 Colab 5. 마무리 셀에서 STOP을 입력해 RDS를 중지한다. 데이터(shop 스키마)는 남아 12-2·12-3에서 이어서 쓰고, 최종 삭제는 12-3 마지막 셀에서 한다.\n'
           '【강의 설명】 5번 셀은 런타임을 다시 시작했어도 단독으로 실행된다(Colab 보안 비밀의 AWS 키로 다시 인증). 중지 중에는 인스턴스 요금이 멈추고 저장공간 요금만 나온다. '
           'AWS는 중지 7일 뒤 자동으로 다시 시작하므로 수업 간격이 길면 콘솔에서 다시 중지하도록 안내한다. DELETE는 과정을 그만둘 때만 입력한다(이어서 할 데이터도 지워짐).\n'
           '【연결】 https://colab.research.google.com/drive/1URPntHhY0jY96psj9cK0Khrzq3gLb8KX#scrollTo=shop-delete')

prs.save(out)
for s in (s31, s34):
    print('---'); [print(' ', sh.text_frame.text.replace('\n', ' / ')[:150]) for sh in s.shapes if sh.has_text_frame]
    for sh in s.shapes:
        if sh.has_table:
            print('  표5행:', [c.text for c in sh.table.rows[len(sh.table.rows) - 1].cells])
