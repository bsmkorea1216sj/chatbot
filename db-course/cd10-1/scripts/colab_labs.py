"""기준본 43~47번 Colab 실습 슬라이드를 현재 노트북 코드·실측 결과와 맞춤: python colab_labs.py <in.pptx> <out.pptx>"""
import sys
from pathlib import Path
sys.argv_saved = sys.argv
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pptx import Presentation
from pptx.util import Inches

import importlib.util
spec = importlib.util.spec_from_file_location('h', str(Path(__file__).resolve().parent / 'pgadmin_labs.py'))
src = (Path(__file__).resolve().parent / 'pgadmin_labs.py').read_text(encoding='utf-8').split('# 39 · 세션 관찰')[0]
src = src.replace("prs = Presentation(sys.argv[1])", "prs = None")
h = {}
exec(src, h)
find, set_lines, panel = h['find'], h['set_lines'], h['panel']

prs = Presentation(sys.argv[1])
S = lambda n: prs.slides[n - 1]

# 43 · 준비
s = S(43)
set_lines(find(s, 'pgAdmin에서 본 구조'), ['pgAdmin에서 본 구조를 Python 클라이언트(Colab)로 다시 관찰합니다.'])
set_lines(find(s, 'Colab 왼쪽 열쇠'), ['Colab 왼쪽 열쇠(보안 비밀)에 AWS_ACCESS_KEY·AWS_SECRET_KEY 등록 → 노트북 액세스 허용 → 맨 위 pip 셀 실행'])
set_lines(find(s, 'RDS 보안그룹에서'), ['DB 비밀번호는 실행할 때 입력칸에 입력(DB_PASSWORD 보안 비밀이 있으면 자동). 키·비밀번호를 코드에 쓰지 않습니다.'])
set_lines(find(s, 'Colab의 psycopg2'), ['엔드포인트·포트(5433)는 AWS 키로 자동 조회. psycopg2 = Client Process(libpq), 연결마다 백엔드 생성.'])
set_lines(find(s, '예상 소요'), ['예상 소요 5분 · 노트북: CD10-1_Colab_Lab(26).ipynb (드라이브 강의 자료 폴더)'])

# 44 · 실습 1
s = S(44)
set_lines(find(s, '같은 RDS에 연결을'), ['AWS 키로 RDS를 찾아 접속한 뒤, 연결을 두 번 열고 PID를 비교합니다.'])
code = find(s, 'from google.colab')
code.width = Inches(6.75)
set_lines(code, ['# 0 · 접속: 보안 비밀 AWS_ACCESS_KEY / AWS_SECRET_KEY',
                 'aws = boto3.Session(aws_access_key_id=key, aws_secret_access_key=skey)',
                 "ep = aws.client('rds').describe_db_instances(",
                 "       DBInstanceIdentifier='postgresql-lab-01')['DBInstances'][0]['Endpoint']",
                 '#     → 엔드포인트·포트 자동 조회, 비밀번호는 입력칸',
                 '# 1 · 연결 2개 = 백엔드 2개',
                 "c1, c2 = connect('session_A'), connect('session_B')",
                 'for c in (c1, c2):',
                 "    cur = c.cursor(); cur.execute('SELECT pg_backend_pid()')",
                 '    print(cur.fetchone())'], size=12.5)
panel(s, 8.05, 3.0, 4.35, 3.45, '실행 결과 (Colab 실측)', [
    ('✅ AWS 인증 완료', 'b'), ('DB 엔드포인트: postgresql-lab-01…:5433', 'n'),
    ('세션 A PID 23416 · 세션 B PID 23421', 'b'), ('→ Postmaster가 연결마다 백엔드를 하나씩 생성', 'n'),
    ('접속 DB는 postgres (dvdrental 미설치)', 's')])

# 45 · 실습 2
s = S(45)
code = find(s, 'import pandas as pd')
code.width = Inches(6.75)
set_lines(code, ["for p in ['shared_buffers', 'work_mem', 'wal_buffers', 'max_connections']:",
                 "    cur.execute(f'SHOW {p}'); print(p, '=', cur.fetchone()[0])",
                 '',
                 "cur.execute('''SELECT backend_type, count(*) AS n",
                 "               FROM pg_stat_activity",
                 "               GROUP BY 1 ORDER BY 2 DESC''')",
                 "display(pd.DataFrame(cur.fetchall(), columns=['backend_type', 'n']))"], size=12.5)
panel(s, 8.05, 3.0, 4.35, 3.45, '실행 결과 (Colab 실측)', [
    ('shared_buffers 185MB · work_mem 4MB', 'b'), ('wal_buffers 5.9MB', 'n'),
    ('max_connections 81', 'b'), ('→ 1,000명 직접 접속은 불가 → 커넥션 풀러 필요', 'n'),
    ('walwriter · checkpointer · background writer · autovacuum launcher · archiver', 'b'),
    ('→ 4. Utility Processes 그림과 일치', 'n')])

# 46 · 실습 3
s = S(46)
set_lines(find(s, 'Parser·Analyzer 오류를'), ['Parser·Analyzer 오류를 비교하고, Planner·Executor 결과(실행계획)를 읽습니다.'])
code = find(s, 'c1.autocommit')
code.width = Inches(6.75)
set_lines(code, ["for sql in ['SELEC * FROM film', 'SELECT * FROM filmx']:",
                 '    try: cur.execute(sql)',
                 "    except Exception as e: print(type(e).__name__, '→', str(e).splitlines()[0])",
                 '',
                 '# payment가 없으면 실습 테이블 cd10_lab_payment(20만 행) 자동 생성',
                 "q = 'SELECT sum(amount) FROM cd10_lab_payment WHERE amount >= 3'",
                 'for i in (1, 2):',
                 "    cur.execute('EXPLAIN (ANALYZE, BUFFERS) ' + q)"], size=12.5)
panel(s, 8.05, 3.0, 4.35, 3.45, '실행 결과 (Colab 실측)', [
    ('SyntaxError → Parser 단계', 'b'), ('UndefinedTable → Analyzer 단계', 'b'),
    ('Parallel Seq Scan', 'b'), ('→ 인덱스 없음, Planner가 전체 읽기 선택', 'n'),
    ('추정 82,607행 · 실제 70,144행 · 45ms', 'b'), ('→ 통계가 정확해 계획이 적절 (Executor 결과)', 'n')])
set_lines(find(s, '기대:'), ['확인: 오류 종류로 단계 구분, 실행계획의 노드·rows(추정/실제)·Buffers·Execution Time 기록'])

# 47 · 제출
s = S(47)
set_lines(find(s, 'PID 2개'), ['PID 2개, 설정값 4개, backend_type 표, 실습 3 실행계획, 심화 Sort Method 캡처'])
set_lines(find(s, 'OpenAI · Uber · Notion'), ['max_connections 81을 근거로 RDS Proxy(4번) 또는 OpenAI(16번) 사례와 연결해 설명합니다.'])
set_lines(find(s, "SET work_mem = '64kB'"), ['work_mem을 64kB·4MB·32MB로 바꿔 ORDER BY의 Sort Method(Disk ↔ Memory) 변화를 관찰합니다.'])

add = {
    43: '\n【변경】 노트북 접속 방식이 PG_HOST 보안 비밀 → AWS 키 + RDS 자동 조회로 바뀌어 슬라이드를 맞췄습니다. 포트는 5433입니다.',
    44: '\n【실측】 AWS 인증 완료 → 엔드포인트 postgresql-lab-01:5433 자동 조회 → PID 23416/23421. 슬라이드 코드는 핵심만 줄인 것이고 전체 코드는 노트북 첫 실습 셀에 있습니다.',
    45: '\n【실측】 shared_buffers 189,376kB, work_mem 4MB, wal_buffers 5,912kB, max_connections 81. client backend 4, walwriter·autovacuum launcher·logical replication launcher·background writer·archiver·checkpointer 각 1.',
    46: '\n【실측】 Parallel Seq Scan(작업자 2), shared hit=1280(1·2차 동일), 약 45ms. 새로 만든 테이블이라 1차부터 메모리에 있어 read가 0입니다.',
    47: '\n【심화 기대 결과】 64kB·4MB는 external merge(Disk), 32MB는 quicksort(Memory)로 바뀌는 것이 일반적입니다(20만 행 정렬에 약 6.6MB 이상 필요).',
}
for n, t in add.items():
    tf = S(n).notes_slide.notes_text_frame
    tf.text = (tf.text or '') + t

prs.save(sys.argv[2])
print('saved', sys.argv[2])
