import copy
A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'


def para_set(p, text):
    rs = p.runs
    rs[0].text = text
    for r in rs[1:]:
        r._r.getparent().remove(r._r)


def find_para(slide, start):
    for sh in slide.shapes:
        if sh.has_text_frame:
            for p in sh.text_frame.paragraphs:
                if p.text.strip().startswith(start):
                    return sh, p
    raise KeyError(start)


def replace(slide, start, text):
    para_set(find_para(slide, start)[1], text)


def add_after(slide, start, text):
    _, p = find_para(slide, start)
    np_ = copy.deepcopy(p._p)
    p._p.addnext(np_)
    rs = np_.findall(A + 'r')
    rs[0].find(A + 't').text = text
    for r in rs[1:]:
        np_.remove(r)


def apply(s):  # s: list of slides, 1-based via s[n-1]
    S = lambda n: s[n - 1]
    add_after(S(3), 'SQL구문 수행시', '현업 사례와 pgAdmin·Colab 실습으로 구조를 직접 관찰한다.')
    add_after(S(3), 'PostgreSQL의 구조를 이해하여', 'EXPLAIN·pg_stat_activity로 프로세스와 실행계획을 확인한다.')

    replace(S(4), '수강신청 시작 직후', '수강신청 시작 직후, 1,000명(수업용 가정)이 동시에 접속한다면?')
    replace(S(4), 'AWS RDS Proxy는', 'RDS Proxy는 DB 연결을 풀에 두고 재사용합니다. 단, SET·임시 테이블 등 세션 상태를 바꾸면 연결이 고정(pinning)되어 재사용 효과가 줄어듭니다.')
    replace(S(4), 'PostgreSQL에 직접 연결하면', '직접 연결하면 연결 1개마다 백엔드 프로세스 1개가 생깁니다(→ 2. Server Processes). Proxy는 이 프로세스 수를 줄여 줍니다.')
    replace(S(4), 'AWS 공식 문서', 'AWS 공식 문서 · How RDS Proxy works (연결 풀링과 pinning)')

    for n in (14, 15, 16):
        replace(S(n), '3. System Processes', '3. System Memory')

    replace(S(18), 'Stats Collector', 'Stats Collector: DB 사용 통계를 수집해 모니터링에 제공 (PG15부터 공유 메모리 방식으로 통합).')
    add_after(S(19), 'WAL은 삽입', 'RDS의 자동 백업·특정 시점 복구(PITR)·읽기 복제본도 WAL을 기반으로 동작함.')

    replace(S(26), '이 과정에서 테이블과 컬럼의', '파서는 문법만 검사하며, 테이블·컬럼 존재 여부 같은 의미 검사는 다음 분석기 단계에서 수행함. (예: SELEC * FROM film → syntax error)')
    add_after(S(27), '이 과정에서 의미 분석은', '예: SELECT * FROM filmx → relation "filmx" does not exist (의미 오류)')
    add_after(S(30), '플래너는 다양한', 'EXPLAIN 출력의 cost=시작비용..총비용 값이 플래너가 예측한 비용임.')
    add_after(S(33), '계획에 명시된', 'EXPLAIN ANALYZE는 계획(추정)과 실행 결과(실제 시간·행 수)를 함께 보여 줌.')
    add_after(S(35), 'SQL 문은 5 단계', '현업에서는 연결 폭증(Proxy·풀러), WAL·VACUUM 비용, 통계 기반 실행계획을 함께 점검한다.')
