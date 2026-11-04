"""CD10-2 기준본(37장) 전체 약어·용어 주석 보강: python footnotes2.py <in.pptx> <out.pptx>
이미 '※' 주석이 있는 페이지는 건너뜀. 배치: row(사례·제출 템플릿) / code(코드 실습) / foot(일반 하단)"""
import sys
from pptx import Presentation
from pptx.util import Pt, Emu
from pptx.dml.color import RGBColor

G = {
    'ID': 'ID: Identifier (식별자, 각 행을 구분하는 고유 번호)',
    'FACT': 'Fact Table: 주문·매출처럼 측정값(사실)을 담는 중심 테이블',
    'GITLAB': 'GitLab: 소스코드 관리·협업 플랫폼 기업 (GitHub와 비슷한 서비스)',
    'DML': 'INSERT·UPDATE·DELETE: 데이터를 추가·수정·삭제하는 SQL 명령 (인덱스도 함께 갱신됨)',
    'BT': 'B-tree: Balanced Tree (균형 트리)', 'BETWEEN': 'BETWEEN: 범위 조건 연산자 (예: 가격 BETWEEN 1000 AND 5000)',
    'HASH': 'Hash(해시): 값을 고정된 번호로 바꿔 저장 위치를 바로 찾는 방식',
    'BRIN': 'BRIN: Block Range Index (블록 범위 인덱스)',
    'PGIDX': 'pg_indexes: 테이블별 인덱스 목록을 보여 주는 PostgreSQL 시스템 뷰',
    'COST': 'cost: Planner의 예상 비용, 단위 없는 상대 점수 (페이지 1개를 순서대로 읽기 = 1)',
    'SEL': '선택도(Selectivity): 조건을 만족하는 행의 비율 (낮다 = 결과 행이 많다)',
    'PG13': "PG-13: 영화 등급 'Parents Strongly Cautioned' (13세 미만은 보호자 지도 권고)",
    'VIS': '가시성(Visibility): 그 행이 지금 트랜잭션에서 보이는지 여부 (VACUUM이 가시성 정보를 갱신)',
    'HEAP': 'Heap: 테이블의 실제 행이 저장된 영역 · Bitmap Heap Scan: 표시된 페이지만 골라 읽는 방식',
    'JOIN': 'JOIN: 두 테이블을 조건(ON)으로 연결하는 SQL 연산 · work_mem: 해시·정렬에 쓰는 메모리',
    'TEMP': 'TEMP TABLE: 현재 연결(창)에서만 보이는 임시 테이블 · ANALYZE: 통계 갱신',
    'EXPB': 'EXPLAIN (ANALYZE, BUFFERS): 실제로 실행하고 읽은 페이지 수(Buffers)까지 표시',
    'ON': 'JOIN … ON: ON 뒤의 조건으로 두 테이블의 행을 짝지음',
    'HF': 'Heap Fetches: Index Only Scan에서 가시성 확인을 위해 테이블을 읽은 횟수',
    'JSON': 'FORMAT JSON: 실행계획을 데이터(JSON)로 받아 표로 정리 · DataFrame: pandas의 표 형식 데이터',
    'DF': 'DataFrame: pandas의 표 형식 데이터 (display로 표 출력)',
}
PLAN = {
    8: ([['ID'], 'FACT'], 'foot'),
    10: (['GITLAB', 'DML'], 'row'),
    11: (['BT', 'BETWEEN'], 'under:CREATE INDEX idx_customer_last_name'),
    12: (['HASH', 'ID'], 'foot'),
    15: (['BRIN'], 'foot'),
    16: (['PGIDX'], 'foot'),
    18: (['COST'], 'foot'),
    19: (['SEL'], 'under:인덱스가 없는 상태'),
    21: (['PG13'], 'foot'),
    22: (['VIS'], 'foot'),
    23: (['HEAP'], 'foot'),
    25: (['JOIN'], 'row'),
    30: (['TEMP'], 'code'),
    31: (['EXPB'], 'code'),
    32: (['ON'], 'code'),
    33: (['HF'], 'row'),
    34: (['JSON'], 'code'),
    35: (['DF'], 'code'),
}


def add(slide, keys, mode):
    lines = ['   '.join('※ ' + G[x] for x in k) if isinstance(k, list) else '※ ' + G[k] for k in keys]
    left, width = 914400, 9900000
    if mode.startswith('under:'):
        box = next(sh for sh in slide.shapes if sh.has_text_frame and mode[6:] in sh.text_frame.text)
        left, width, top, h = box.left, box.width, box.top + box.height + 120000, 700000
    elif mode == 'row':
        top, h = 5600000, 440000
    elif mode == 'code':
        top, h = 6500000, 340000
    else:
        h = 150000 * len(lines) + 60000
        top = 6858000 - h - 60000
    tb = slide.shapes.add_textbox(Emu(left), Emu(top), Emu(width), Emu(h))
    tb.name = '약어 주석'
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_top = tf.margin_bottom = Emu(0)
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        r = p.add_run(); r.text = ln
        r.font.size = Pt(10.5); r.font.name = 'NanumGothic'; r.font.color.rgb = RGBColor(0x3A, 0x44, 0x5C)


prs = Presentation(sys.argv[1])
done = []
for n, (keys, mode) in PLAN.items():
    s = prs.slides[n - 1]
    if any(sh.has_text_frame and sh.text_frame.text.lstrip().startswith('※') for sh in s.shapes):
        continue
    add(s, keys, mode)
    done.append(n)
prs.save(sys.argv[2])
print('footnotes added:', done)
