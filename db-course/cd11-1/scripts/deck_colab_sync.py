"""11-1 보강본 교안을 Colab(CD11-1_Colab_Lab) 흐름과 맞춤.
- 정리(summary) 슬라이드를 Colab 실습 뒤·Q&A 앞으로 이동 → Colab 도입 42 · 준비 43 · 실습1 44 · 실습2 45 · 실습3 46 · 정리 47 · Q&A 48
- 한 칸씩 밀려 있던 노트 바로잡기: Palantir AIP+Azure / AWS·Google 설계 관점 / 정리
- Colab 슬라이드 코드·설명을 노트북 수정(status·attempted_at·amount>0·복합 인덱스)에 맞춤
python deck_colab_sync.py <in.pptx> <out.pptx>"""
import sys
from pptx import Presentation
from pptx.util import Pt

src, out = sys.argv[1:3]
prs = Presentation(src)
ids = prs.slides._sldIdLst


def title(sl):
    return sl.shapes.title.text_frame.text.strip() if sl.shapes.title is not None else ''


def find(pred):
    return next(sl for sl in prs.slides if pred(sl))


def alltext(sl):
    return ' '.join(sh.text_frame.text for sh in sl.shapes if sh.has_text_frame)


def rep(sl, old, new):
    hit = False
    for sh in sl.shapes:
        if not sh.has_text_frame:
            continue
        for p in sh.text_frame.paragraphs:
            if old in p.text and p.runs:
                full = p.text.replace(old, new)
                p.runs[0].text = full
                for r in p.runs[1:]:
                    r.text = ''
                hit = True
    if not hit and new not in alltext(sl):
        print('  ! not found:', old[:40])


# 1) 정리 슬라이드 이동 (Q&A 바로 앞)
summary = find(lambda sl: sl.slide_layout.name == 'summary' and '데이터가 속한 세계' in alltext(sl))
qa = find(lambda sl: title(sl).startswith('Q&A') or 'Q&A | 주문·결제' in alltext(sl))
el = next(e for e in ids if prs.part.related_part(e.rId) is summary.part)
ids.remove(el)
qa_idx = next(i for i, e in enumerate(ids) if prs.part.related_part(e.rId) is qa.part)
ids.insert(qa_idx, el)

# 2) 노트 바로잡기
azure = find(lambda sl: title(sl).startswith('Palantir AIP + Microsoft Azure'))
azure.notes_slide.notes_text_frame.text = (
    '【슬라이드 핵심】 민감한 업무 데이터는 모델 단계에서부터 민감도·역할·승인 경로·감사 로그를 정의해야 한다. Palantir와 Microsoft의 보안 클라우드 협력이 그 기업 사례다.\n'
    '【강의 설명】 Palantir는 Foundry·Gotham·AIP를 Microsoft Azure Government/Secret 등 보안 클라우드 환경에 배포하고, Azure OpenAI 모델을 AIP와 연계해 물류·계약·우선순위 판단 같은 업무 흐름에 적용한다고 발표했다(2024.08.08). '
    '설계 관점에서 보면 “누가 어떤 데이터를 보고, 어떤 액션을 승인할 수 있는가”를 개념 모델(역할·액션)에서 정하고, 논리 모델(권한 테이블·감사 로그)과 물리 구현(접근 제어·암호화·로그 보관)으로 내려간다. '
    '앞 쪽 결제 실패와 재시도 사례의 ‘환불 승인은 담당자만’ 규칙과 연결해 설명한다.\n'
    '【연결】 38쪽 적용 사례(결제 실패와 재시도), 39쪽 Palantir Ontology, 37쪽 설계 고려사항(보안)\n'
    '【출처】 Microsoft·Palantir 협력 발표(2024.08.08, Azure Government/Secret·Azure OpenAI 연계)')

aws = find(lambda sl: title(sl).startswith('연관 빅테크 사례: AWS·Google'))
aws.notes_slide.notes_text_frame.text = (
    '【슬라이드 핵심】 AWS는 접근 패턴 중심, Google은 데이터 제품·거버넌스 중심, Palantir는 업무 객체·액션 중심으로 설계 관점이 다르다.\n'
    '【강의 설명】 관계형 모델링은 개체와 관계를 정규화해 테이블로 바꾸는 방식이다. DynamoDB는 먼저 조회 패턴을 정의하고 PK/SK를 설계한다. '
    'Google Knowledge Catalog는 도메인, 존, 자산, 데이터 제품으로 조직 차원의 데이터 거버넌스를 구성한다. 이 세 관점을 비교하면 설계 목적에 따라 모델링 출발점이 달라진다는 점을 이해할 수 있다. '
    'Colab 실습 마지막의 기업 사례 비교표(29쪽 개념·논리·물리 형식)로 이어진다.\n'
    '【연결】 29쪽 적용 사례(개념·논리·물리), 46쪽 Colab 기업 사례 비교\n'
    '【출처】 AWS DynamoDB Data Modeling Foundations: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/data-modeling-foundations.html ; '
    'Google Cloud Knowledge Catalog data mesh quickstart: https://docs.cloud.google.com/knowledge-catalog/docs/build-a-data-mesh-quickstart')

summary.notes_slide.notes_text_frame.text = (
    '【슬라이드 핵심】 11-1 전체 요약: 데이터 세계, 모델링 단계(개념·논리·물리), 기업 사례, 설계 고려사항, Colab 실습 결과.\n'
    '【강의 설명】 학생들에게 “현실의 주문·결제 업무를 어떻게 DB 테이블과 제약조건으로 바꿀 것인가?”를 다시 묻는다. '
    'Colab에서 확인한 것—결제 시도를 별도 행으로 남기고(실패도 기록), FK·CHECK·UNIQUE로 잘못된 입력을 막고, 롤백으로 일관성을 지키며, 복합 인덱스로 조회 경로가 SCAN에서 SEARCH로 바뀐 것—을 설계 기준(무결성·일관성·효율성)과 연결해 정리한다. '
    'Palantir 사례는 추상 모델이 실제 운영 의사결정과 보안 통제까지 연결될 수 있음을 보여준다.\n'
    '【연결】 42–46쪽 Colab 실습, 29·39쪽 개념·논리·물리 사례, 37쪽 설계 고려사항\n'
    '【출처】 11-1 원본 교안 및 Palantir/AWS/Google 공식 문서')

# 3) Colab 슬라이드 코드·설명을 노트북에 맞춤
prep = find(lambda sl: title(sl).startswith('Colab 준비'))
rep(prep, 'db = sqlite3.connect(":memory:")', 'db = sqlite3.connect(":memory:", cached_statements=0)')
rep(prep, '런타임을 다시 시작하면 첫 코드 셀부터 실행합니다.', '런타임을 다시 시작하면 준비 셀부터 다시 실행합니다.')

lab1 = find(lambda sl: title(sl).startswith('Colab 실습 1'))
rep(lab1, '조회값으로 (1,)을 전달하면 결제 ID 1과 10이 나옵니다.',
    '조회값으로 (1,)을 전달하면 결제 ID 1(failed)과 10(approved)이 나옵니다. 승인 합계 1,200원 = 주문 금액')

lab2 = find(lambda sl: title(sl).startswith('Colab 실습 2'))
rep(lab2, 'db.execute(insert, (3, 1, "demo-rollback", 300))', 'db.execute(insert, (3, 1, "demo-rollback", 300, "approved", t))')
rep(lab2, 'db.execute(insert, (4, 999, "demo-missing-order", 300))', 'db.execute(insert, (4, 999, "demo-missing-order", 300, "approved", t))')

lab3 = find(lambda sl: title(sl).startswith('Colab 실습 3'))
rep(lab3, 'EXPLAIN QUERY PLAN SELECT amount FROM payments WHERE order_id = ?',
    'EXPLAIN QUERY PLAN SELECT amount, status FROM payments WHERE order_id = ? ORDER BY attempted_at DESC')
rep(lab3, 'CREATE INDEX IF NOT EXISTS payments_order_idx ON payments(order_id)',
    'CREATE INDEX payments_order_time_idx ON payments(order_id, attempted_at DESC)')
for sh in lab3.shapes:                              # 코드 3줄은 13pt로 (강의자 그림과 겹치지 않게 한 줄씩)
    if sh.has_text_frame:
        for p in sh.text_frame.paragraphs:
            if p.text.startswith(('SELECT payment_id', 'EXPLAIN QUERY PLAN', 'CREATE INDEX')):
                for r in p.runs:
                    r.font.size = Pt(13)

prs.save(out)
order = [i + 1 for i, sl in enumerate(prs.slides) if sl is summary or sl is qa]
print('ok · 정리/Q&A 위치:', order, '· 슬라이드 수', len(prs.slides))
