"""기준본 39~42번 pgAdmin 실습 4장만 보기 쉽게 수정: python pgadmin_labs.py <in.pptx> <out.pptx>"""
import copy, sys
from pptx import Presentation
from pptx.util import Pt, Emu, Inches
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR

A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
prs = Presentation(sys.argv[1])
S = lambda n: prs.slides[n - 1]


def find(slide, start):
    for sh in slide.shapes:
        if sh.has_text_frame and sh.text_frame.text.strip().startswith(start):
            return sh
    raise KeyError(start)


def set_lines(shape, lines, size=None):
    tf = shape.text_frame
    first = tf.paragraphs[0]
    for p in tf.paragraphs[1:]:
        p._p.getparent().remove(p._p)
    for r in first.runs[1:]:
        r._r.getparent().remove(r._r)
    tmpl = copy.deepcopy(first._p)
    first.runs[0].text = lines[0]
    prev = first._p
    for ln in lines[1:]:
        np_ = copy.deepcopy(tmpl)
        prev.addnext(np_)
        prev = np_
        np_.findall(A + 'r')[0].find(A + 't').text = ln if ln else ' '
    if size:
        for p in tf.paragraphs:
            for r in p.runs:
                r.font.size = Pt(size)


def panel(slide, x, y, w, h, title, items):
    b = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    b.name = '결과 예시 패널'
    b.adjustments[0] = 0.06
    b.fill.solid(); b.fill.fore_color.rgb = RGBColor(0xEE, 0xF4, 0xFF)
    b.line.color.rgb = RGBColor(0xA8, 0xC4, 0xF8); b.line.width = Pt(1.25)
    b.shadow.inherit = False
    tf = b.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.TOP
    tf.margin_left = tf.margin_right = Inches(0.15)
    tf.margin_top = Inches(0.12)
    for i, (txt, kind) in enumerate([(title, 'h')] + items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(5)
        r = p.add_run(); r.text = txt
        r.font.name = 'NanumGothic'
        r.font.size = Pt({'h': 15, 'b': 13.5, 'n': 13.5, 's': 11.5}[kind])
        r.font.bold = kind in ('h', 'b')
        r.font.color.rgb = {'h': RGBColor(0x1A, 0x56, 0xDB), 'b': RGBColor(0x1A, 0x23, 0x32),
                            'n': RGBColor(0x1A, 0x23, 0x32), 's': RGBColor(0x5A, 0x67, 0x80)}[kind]


# 39 · 세션 관찰
s = S(39)
set_lines(find(s, '같은 RDS에'), ['pgAdmin에서 Query Tool 창을 2개 열어 "연결 1개 = 백엔드 1개"를 확인합니다.'])
set_lines(find(s, '기존 실습 RDS'), ['① 실습 RDS 서버 연결 → ② postgres DB 선택 → ③ Tools ▸ Query Tool을 두 번 열어 창 A·창 B 준비'])
set_lines(find(s, '같은 창에서 다시'), ['창 A에서 두 번 조회하면 PID가 같을까요? 창 A와 창 B의 PID는? → 예측을 먼저 적고 실행'])
set_lines(find(s, '두 창의 PID'), ['창 A·B의 PID, DB 이름, shared_buffers, work_mem을 제출 표에 적습니다.'])
set_lines(find(s, '예상 소요'), ['예상 소요 5분 · 창 A ─▶ 백엔드 ①, 창 B ─▶ 백엔드 ② (Postmaster가 연결마다 생성)'])

# 40 · PID와 메모리
s = S(40)
set_lines(find(s, '두 창에서'), ['①은 창 A·B 각각, ②③은 한 창에서 실행합니다.'])
code = find(s, 'SELECT pg_backend_pid')
code.width = Inches(6.55)
set_lines(code, ['-- ① 창 A, 창 B에서 각각 실행', 'SELECT pg_backend_pid() AS pid,', '       current_database() AS db;',
                 '-- ② 메모리 설정', 'SHOW shared_buffers;', 'SHOW work_mem;',
                 '-- ③ 지금 떠 있는 프로세스 종류', 'SELECT backend_type, count(*)', 'FROM pg_stat_activity',
                 'GROUP BY backend_type;'], size=15)
panel(s, 7.85, 3.0, 4.55, 3.45, '결과 예시 (우리 RDS 실측)', [
    ('① PID: 창 A 23416 · 창 B 23421', 'b'), ('→ 창마다 다른 백엔드 프로세스', 'n'),
    ('② shared_buffers 185MB · work_mem 4MB', 'b'), ('→ 공유 메모리 / 연산별 지역 메모리', 'n'),
    ('③ walwriter · checkpointer · background writer · autovacuum launcher · archiver', 'b'),
    ('숫자는 실행할 때마다 다를 수 있습니다.', 's')])
set_lines(find(s, '비교:'), ['비교: 같은 창은 PID 유지, 다른 창은 PID가 다름 → 2. Server Processes / 4. Utility Processes 확인'])

# 41 · 반복 조회와 버퍼 캐시
s = S(41)
set_lines(find(s, 'dvdrental의 payment'), ['실습용 결제 테이블(20만 행)을 만들고 같은 SELECT를 두 번 실행합니다.'])
code = find(s, 'EXPLAIN (ANALYZE, BUFFERS)')
code.width = Inches(6.55)
set_lines(code, ['-- ① 실습 테이블 준비 (한 번만)', 'CREATE TABLE IF NOT EXISTS cd10_lab_payment AS',
                 'SELECT g AS payment_id,', '       round((random()*10)::numeric, 2) AS amount,',
                 "       now() - g * interval '1 minute' AS payment_date",
                 'FROM generate_series(1, 200000) g;', 'ANALYZE cd10_lab_payment;',
                 '-- ② 같은 문장을 두 번 실행', 'EXPLAIN (ANALYZE, BUFFERS)',
                 'SELECT sum(amount) FROM cd10_lab_payment', 'WHERE amount >= 3;'], size=13.5)
panel(s, 7.85, 3.0, 4.55, 3.45, '결과 예시 (우리 RDS 실측)', [
    ('Parallel Seq Scan', 'b'), ('→ 인덱스가 없어 전체를 나눠 읽음 (Planner 선택)', 'n'),
    ('Buffers: shared hit=1280', 'b'), ('→ 1,280페이지 모두 메모리(Shared Buffer)에서 읽음', 'n'),
    ('Execution Time ≈ 45ms', 'b'),
    ('방금 만든 테이블은 이미 메모리에 있어 1·2차 모두 hit. 처음 읽는 큰 테이블은 1차 read → 2차 hit', 's')])
set_lines(find(s, '기록:'), ['기록: 노드 이름, shared hit / read, Execution Time을 1차·2차로 비교합니다.'])

# 42 · 제출
s = S(42)
set_lines(find(s, '수강신청 서비스의'), ['"수강신청 DB가 느리다"는 보고를 받았다고 가정하고, 오늘 관찰한 값으로 설명합니다.'])
set_lines(find(s, '두 세션의 PID'), ['표 1장: 창 A·B의 PID │ shared_buffers·work_mem │ 1·2차 실행계획(노드, hit/read, 시간)'])
set_lines(find(s, '버퍼의 read가'), ['shared read는 항상 "디스크에서 읽음"일까요? (힌트: Shared Buffer 밖에는 OS 캐시도 있음)'])
set_lines(find(s, '동시 접속 급증과'), ['연결 수 문제(pg_stat_activity)인지, 느린 SQL(EXPLAIN ANALYZE)인지 어떻게 구분할까요?'])

# 노트 보강
add = {
    39: '\n【실습 순서】 Tools ▸ Query Tool을 두 번 열면 서버 입장에서는 연결 2개 → 백엔드 프로세스 2개입니다. 예측을 먼저 적게 해야 결과가 기억에 남습니다.',
    40: '\n【결과 예시】 Colab 실측: PID 23416/23421, shared_buffers 185MB, work_mem 4MB, max_connections 81, 백그라운드 프로세스 walwriter·checkpointer·background writer·autovacuum launcher·archiver. pgAdmin에서 나오는 PID 숫자는 다르지만 "창마다 다르다"는 점은 같습니다.',
    41: '\n【변경】 RDS에 dvdrental이 없어 payment 대신 실습 테이블 cd10_lab_payment를 만듭니다(Colab 실습 3과 같은 테이블, IF NOT EXISTS라 두 번 만들어지지 않음). 결과 예시는 Colab 실측값입니다. 1·2차 차이를 꼭 보여 주려면 RDS 재부팅 직후나 처음 읽는 큰 테이블로 실행합니다.',
    42: '\n【정답 방향】 해석: shared read는 "Shared Buffer에 없어서 가져옴"이고, OS 캐시에서 왔을 수도 있어 물리 디스크 읽기와 같지 않습니다. 응용: 연결 급증은 pg_stat_activity의 연결 수·대기 상태로, 느린 SQL은 EXPLAIN ANALYZE의 실행시간·노드로 구분합니다(4번 RDS Proxy 사례와 같은 결론).',
}
for n, t in add.items():
    tf = S(n).notes_slide.notes_text_frame
    tf.text = (tf.text or '') + t

prs.save(sys.argv[2])
print('saved', sys.argv[2])
