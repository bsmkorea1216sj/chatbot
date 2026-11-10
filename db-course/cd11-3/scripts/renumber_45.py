"""교안 순서(실습2 14·15쪽 → 검증 17쪽)에 맞춰 미션 4↔5 번호 교체: python renumber_45.py <in.pptx> <out.pptx>
상담 카드(다중 선택) = 미션 4, 나눠 낸 결제 = 미션 5. 노트북(colab_nb.py)도 같은 순서."""
import sys
from pptx import Presentation

prs = Presentation(sys.argv[1])
S = lambda n: prs.slides[n - 1]
log = []


def runs(sh):
    return [r for p in sh.text_frame.paragraphs for r in p.runs]


def relink(sh, old, new):
    try:
        if sh.click_action.hyperlink.address and old in sh.click_action.hyperlink.address:
            sh.click_action.hyperlink.address = sh.click_action.hyperlink.address.replace(old, new)
    except Exception:
        pass
    for r in runs(sh):
        if r.hyperlink.address and old in r.hyperlink.address:
            r.hyperlink.address = r.hyperlink.address.replace(old, new)


def badge(n, old_no, new_no):
    for sh in S(n).shapes:
        if sh.has_text_frame and f'Colab 미션 {old_no}' in sh.text_frame.text:
            for r in runs(sh):
                r.text = r.text.replace(f'미션 {old_no}', f'미션 {new_no}')
            relink(sh, f'mission_m{old_no}', f'mission_m{new_no}')
            log.append(f'{n}쪽 버튼 {old_no}→{new_no}')


def by_text(n, start):
    return next(sh for sh in S(n).shapes if sh.has_text_frame and sh.text_frame.text.startswith(start))


def set_runs(sh, texts):  # 문단별 첫 run만 바꿔 서식 유지
    for p, t in zip(sh.text_frame.paragraphs, texts):
        p.runs[0].text = t
        for r in p.runs[1:]:
            r.text = ''


badge(14, 5, 4); badge(15, 5, 4); badge(17, 4, 5)

# 16쪽 안내: ③ 상담 카드 → 미션 4, ④ 수정 비교 → 미션 5 → 과제 (위치도 교체)
a, b = by_text(16, '③ 수정 비교'), by_text(16, '④ 상담 카드')
a.top, b.top = b.top, a.top
set_runs(b, ['③ 상담 카드', '따라하기 3 → 미션 4 (다중 선택 + GROUP BY)  ↔ 교안 14·15쪽'])
set_runs(a, ['④ 수정 비교', '따라하기 4 → 미션 5 (카드+현금 나눠 낸 결제 저장) → 📝 과제 (회원·포인트 확장)  ↔ 교안 17·18쪽'])
log.append('16쪽 ③④ 교체')

# 20쪽 미션 정답 ②: 왼쪽 미션 4(상담) · 오른쪽 미션 5(결제)
set_runs(by_text(20, '미션 정답 ②'), ['미션 정답 ② | 실습2·검증·과제 · 미션 4·5·과제'])
set_runs(by_text(20, '결제는 여러 행'), ['다중 선택은 연결 표, 결제는 여러 행, 확장은 새 표와 FK로 해결합니다.'])
pay, form = by_text(20, '미션 4 · 결제'), by_text(20, '미션 5 · 입력값')
pay.left, form.left = form.left, pay.left
pay.text_frame.paragraphs[0].runs[0].text = '미션 5 · 결제 입력값'
form.text_frame.paragraphs[0].runs[0].text = '미션 4 · 상담 입력값'
nt = S(20).notes_slide.notes_text_frame
for p in nt.paragraphs:
    for r in p.runs:
        r.text = r.text.replace('미션 4는', '#A#').replace('미션 5는', '미션 4는').replace('#A#', '미션 5는')
log.append('20쪽 카드·노트 교체')

prs.save(sys.argv[2])
print(log)
