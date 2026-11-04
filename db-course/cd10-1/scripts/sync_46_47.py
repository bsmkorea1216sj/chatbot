"""기준본 46번(Colab 실습 3)·47번 노트를 현재 노트북(표·트리 출력)과 맞춤: python sync_46_47.py <in.pptx> <out.pptx>"""
import sys
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches

src = (Path(__file__).resolve().parent / 'pgadmin_labs.py').read_text(encoding='utf-8').split('# 39 · 세션 관찰')[0]
h = {}
exec(src.replace("prs = Presentation(sys.argv[1])", "prs = None"), h)
find, set_lines, panel = h['find'], h['set_lines'], h['panel']

prs = Presentation(sys.argv[1])
s = prs.slides[45]

set_lines(find(s, 'Parser·Analyzer 오류를'), ['오류 표 → 실행계획 트리 → 1·2차 비교 표 순서로 SQL 5단계를 확인합니다.'])
code = find(s, "for sql in ['SELEC")
set_lines(code, ['# ① 오류 2개 → 멈춘 단계 표',
                 "for sql, stage in [('SELEC * FROM film', 'Parser'),",
                 "                   ('SELECT * FROM filmx', 'Analyzer')]:",
                 '    try: cur.execute(sql)',
                 '    except Exception as e: rows.append([sql, type(e).__name__, stage])',
                 '# ② 실습 테이블 cd10_lab_payment(20만 행): 없으면 자동 생성',
                 '# ③ 같은 SELECT 두 번 → 실행계획을 JSON으로 받아 트리·표로 정리',
                 "cur.execute('EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) ' + q)",
                 'plan = cur.fetchone()[0][0]',
                 'display(pd.DataFrame(summary, columns=[...]))   # 1·2차 비교 표'], size=12.5)
for sh in list(s.shapes):
    if sh.name == '결과 예시 패널':
        sh._element.getparent().remove(sh._element)
panel(s, 8.05, 3.0, 4.35, 3.45, '실행 결과 (Colab 실측)', [
    ('① SyntaxError → Parser · UndefinedTable → Analyzer', 'b'),
    ('② 트리(아래→위): Parallel Seq Scan → Partial Aggregate → Gather → Finalize Aggregate', 'n'),
    ('③ 1·2차 비교 표', 'b'),
    ('추정 82,607행 · 실제 70,144행 · hit 1,280 · read 0 · 약 45ms', 'n'),
    ('계획 단계 read 1 → 0 (1차만 디스크, 2차부터 메모리)', 'b')])
set_lines(find(s, '확인:'), ['확인: ① 멈춘 단계 ② 트리를 아래에서 위로 ③ 1·2차 표의 hit·read·실행시간 비교'])
tf = s.notes_slide.notes_text_frame
tf.text = (tf.text or '') + '\n【변경】 노트북 출력이 실행계획 원문 → 오류 표·실행계획 트리·1·2차 비교 표(FORMAT JSON)로 바뀌어 슬라이드를 맞췄습니다. 실습 3 셀은 접속이 없으면 스스로 접속합니다.'

n47 = prs.slides[46].notes_slide.notes_text_frame
t = n47.text
for a, b in [('심화(work_mem 64kB와 Sort Method)', '심화(work_mem 64kB·4MB·32MB와 Sort Method)'),
             ('심화 정답: Sort Method가 quicksort(Memory) → external merge(Disk)로 바뀜 = Local Memory 부족(슬라이드 16).',
              '심화 정답: work_mem이 작으면 external merge(Disk), 충분하면 quicksort(Memory) = Local Memory 크기 문제(슬라이드 19).')]:
    assert a in t, a
    t = t.replace(a, b)
n47.text = t

prs.save(sys.argv[2])
print('saved', sys.argv[2])
