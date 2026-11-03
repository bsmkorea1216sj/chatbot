"""기준본 PPTX의 각 페이지 하단에 약어·용어 주석 추가: python footnotes.py <in.pptx> <out.pptx>
규칙: AGENTS.md 교안 제작 규칙 8. 이미 '※'로 시작하는 주석이 있는 페이지는 건너뜀."""
import sys
from pptx import Presentation
from pptx.util import Pt, Emu
from pptx.dml.color import RGBColor

G = {
    'SQL': 'SQL: Structured Query Language (구조적 질의 언어)',
    'DB': 'DB: Database (데이터베이스)',
    'AWS': 'AWS: Amazon Web Services (아마존 클라우드 서비스)',
    'RDS': 'RDS: Relational Database Service (AWS 관리형 관계형 DB 서비스)',
    'OS': 'OS: Operating System (운영체제)',
    'WAL': 'WAL: Write-Ahead Log (선행 기록 로그)',
    'SYS': 'SYS logger: System Logger (에러·경고를 기록하는 시스템 로그 프로세스)',
    'PITR': 'PITR: Point-In-Time Recovery (특정 시점 복구)',
    'VACUUM': 'VACUUM: 죽은 행(옛 행 버전)을 정리해 공간을 재사용하게 하는 명령 (Autovacuum: 이를 자동 실행하는 프로세스)',
    'XID': '트랜잭션 ID(XID): 트랜잭션마다 붙는 번호, 약 21억 개를 다 쓰기 전에 VACUUM으로 재사용해야 함(wraparound 방지)',
    'SHARD': '샤딩(Sharding): 큰 DB를 여러 DB(샤드)로 나눠 저장하는 방식',
    'PID': 'PID: Process ID (프로세스 번호)',
    'PGB': 'PgBouncer: PostgreSQL용 오픈소스 커넥션 풀러 (Skype에서 시작)',
    'PROXY': 'RDS Proxy: AWS 관리형 커넥션 풀러 · pinning: 세션 상태 때문에 연결이 한 클라이언트에 고정되는 현상',
    'PM': 'Postmaster: PostgreSQL 메인 서버 프로세스 (접속 수락·백엔드 생성)',
    'BE': 'Backend: 연결마다 생성되어 SQL을 실행하는 서버 프로세스',
    'EXPLAIN': 'EXPLAIN: 실행 계획을 보여 주는 명령 · ANALYZE: 실제로 실행해 시간을 측정(단독 사용 시 통계 갱신)',
    'BUFFERS': 'BUFFERS: EXPLAIN 옵션, 메모리에서 읽은 페이지(shared hit)와 새로 읽은 페이지(read) 수 표시',
    'SB': 'shared_buffers: 공유 메모리 캐시 크기 · work_mem: 정렬·해시 연산 1회당 쓰는 지역 메모리',
    'WM': 'work_mem: 정렬·해시 연산 1회당 쓰는 지역 메모리 크기',
    'FORK': 'fork: 실행 중인 프로세스를 복제해 새 프로세스를 만드는 OS 기능',
    'LIBPQ': 'libpq: PostgreSQL 공식 C 클라이언트 라이브러리 (psycopg2도 내부적으로 사용)',
    'ANALYZE': 'ANALYZE: 테이블 통계 갱신 명령 · EXPLAIN ANALYZE: 실행 계획 + 실제 실행 시간 표시',
}

# 페이지: (주석 키, 배치)  배치 = 'row'(사례 템플릿: 출처 줄 위) / 'foot'(하단) / 'code'(코드 슬라이드: 출처 줄 아래)
PLAN = {
    3: (['SQL', 'EXPLAIN'], 'foot'),
    4: ([['AWS', 'DB'], 'RDS', 'PROXY'], 'row'),
    10: (['OS', 'SYS'], 'topleft'),
    14: (['PM', 'BE'], 'foot'),
    16: (['PGB'], 'row'),
    17: (['OS', 'WAL'], 'foot'),
    19: (['OS', 'WAL', 'WM'], 'foot'),
    21: (['WAL', 'PITR', 'SYS'], 'foot'),
    22: (['WAL', 'PITR'], 'foot'),
    26: (['VACUUM', 'XID', 'SHARD'], 'row'),
    33: (['EXPLAIN'], 'foot'),
    35: (['ANALYZE'], 'row'),
    36: (['EXPLAIN'], 'foot'),
    38: (['WAL', 'VACUUM'], 'foot'),
    39: (['PID'], 'row'),
    40: (['PID', 'SB'], 'code'),
    41: (['EXPLAIN', 'BUFFERS'], 'code'),
    42: (['PID'], 'row'),
    43: (['RDS', 'LIBPQ'], 'row'),
    44: ([['PID', 'FORK'], 'PM'], 'code'),
    45: (['SB'], 'code'),
    46: (['EXPLAIN', 'BUFFERS'], 'code'),
    47: (['PID', 'WM'], 'row'),
}
TOP = {'row': 5600000, 'foot': 6330000, 'code': 6500000}
DARK = {3, 38}


def add(slide, keys, mode, size=10.5):
    lines = ['   '.join('※ ' + G[x] for x in k) if isinstance(k, list) else '※ ' + G[k] for k in keys]
    left, width = 914400, 9900000
    if mode == 'row' and len(lines) > 2:
        size = 9.5
    if mode == 'topleft':
        left, top, width, h = 274320, 720000, 3200000, 420000
    elif mode == 'row':
        top, h = TOP[mode], 440000
    elif mode == 'code':
        top, h = TOP[mode], 358000
    else:
        h = 140000 * len(lines) + 60000
        top = 6858000 - h - 60000
    tb = slide.shapes.add_textbox(Emu(left), Emu(top), Emu(width), Emu(h))
    tb.name = '약어 주석'
    tf = tb.text_frame
    tf.word_wrap = True
    for m in ('margin_top', 'margin_bottom'):
        setattr(tf, m, Emu(0))
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        r = p.add_run()
        r.text = ln
        r.font.size = Pt(size)
        r.font.name = 'NanumGothic'
        r.font.color.rgb = RGBColor(0xDD, 0xE6, 0xF5) if slide_no(slide) in DARK else RGBColor(0x3A, 0x44, 0x5C)


def slide_no(slide):
    return list(prs.slides).index(slide) + 1


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
