"""Build the Part 1 (26) teaching edition from the original 30-slide PPTX."""
import argparse
import sqlite3
from copy import deepcopy
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR
from pptx.util import Inches, Pt

SHOPIFY = 'https://help.shopify.com/en/manual/inventory-and-locations/fundamentals/inventory-states'
POSTGRES = 'https://www.postgresql.org/docs/current/transaction-iso.html'
RDS = 'https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/ssl-certificate-rotation-postgresql.html'
RESERVE = 'UPDATE lab_stock SET available = available - 1 WHERE sku = 1001 AND available >= 1 RETURNING available'
CELL = f'''# Colab 사전 준비: psycopg2가 없으면 %pip install -q psycopg2-binary
# Colab 보안 비밀: DB_HOST, DB_PORT, DB_USER
# AWS 공식 RDS CA 번들을 Colab에 /content/global-bundle.pem으로 업로드
from getpass import getpass
from pathlib import Path
from google.colab import userdata
import psycopg2
from contextlib import closing

ca = Path("/content/global-bundle.pem")
if not ca.is_file():
    raise FileNotFoundError("RDS CA 번들을 /content/global-bundle.pem에 업로드하세요.")
with closing(psycopg2.connect(
    host=userdata.get("DB_HOST").strip(), port=int(userdata.get("DB_PORT").strip()),
    user=userdata.get("DB_USER").strip(), password=getpass("DB 비밀번호: "),
    dbname="dvdrental", sslmode="verify-full", sslrootcert=str(ca), connect_timeout=10,
)) as db:
    with db:
        with db.cursor() as cur:
            cur.execute("CREATE TEMP TABLE lab_stock(sku integer PRIMARY KEY, available integer NOT NULL CHECK(available >= 0))")
            cur.execute("INSERT INTO lab_stock VALUES (1001, 1), (1002, 1)")
    with db:
        with db.cursor() as cur:
            cur.execute("{RESERVE}")
            print("예약 1:", cur.fetchall())
            cur.execute("{RESERVE}")
            print("예약 2:", cur.fetchall())
            cur.execute("SAVEPOINT checkout")
            cur.execute("{RESERVE.replace('1001', '1002')}")
            cur.execute("ROLLBACK TO SAVEPOINT checkout")
            cur.execute("SELECT available FROM lab_stock WHERE sku = 1002")
            print("롤백 후:", cur.fetchone()[0])
'''
NAVY = '103858'
INK = '13314A'
PALE = 'E8F2FB'


def note(slide, core, details, link, source='12-1 원본 교안 및 수업용 쇼핑몰 예제'):
    slide.notes_slide.notes_text_frame.text = '\n'.join((
        '【슬라이드 핵심】', core, '【강의 설명】', details,
        '【연결】', link, '【출처】', source,
    ))


def set_run(run, size, color, bold=False):
    run.font.name = '맑은 고딕'
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor.from_string(color)


def text_box(slide, box, lines, size, bold=False):
    shape = slide.shapes.add_textbox(*(Inches(v) for v in box))
    frame = shape.text_frame
    frame.word_wrap = True
    for i, line in enumerate(lines):
        p = frame.paragraphs[0] if i == 0 else frame.add_paragraph()
        set_run(p.add_run(), size, INK, bold)
        p.runs[-1].text = line
    return shape


def case_slide(deck, reference, title, lead, rows, end, footer):
    slide = deck.slides.add_slide(reference.slide_layout)
    slide.shapes.title.text = title
    for shape in list(slide.placeholders):
        if shape != slide.shapes.title and not shape.text:
            shape._element.getparent().remove(shape._element)
    text_box(slide, (0.98, 1.55, 11.45, 0.65), (lead,), 20, True)
    table = slide.shapes.add_table(len(rows) + 1, 2, Inches(1.05), Inches(2.30),
                                   Inches(11.1), Inches(3.04)).table
    table.columns[0].width = Inches(2.77)
    table.columns[1].width = Inches(8.33)
    for i, values in enumerate([('확인 항목', '쇼핑몰 시나리오'), *rows]):
        if i == 0:
            table.rows[i].height = Inches(0.44)
        else:
            table.rows[i].height = Inches(2.6 / len(rows))
        for j, value in enumerate(values):
            cell = table.cell(i, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor.from_string(NAVY if i == 0 else (PALE if i % 2 else 'F5F9FC'))
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.margin_left = Inches(0.14)
            p = cell.text_frame.paragraphs[0]
            run = p.add_run()
            run.text = value
            set_run(run, 17 if len(rows) < 5 else 15, 'FFFFFF' if i == 0 else INK, i == 0 or j == 0)
    text_box(slide, (0.98, 5.56, 11.4, 0.65), (end,), 18, True)
    text_box(slide, (0.98, 6.41, 11.5, 0.63), footer, 10)
    return slide


def first_table(slide):
    return next(shape.table for shape in slide.shapes if shape.has_table)


def replace_body(slide, lines):
    boxes = [shape for shape in slide.shapes if shape.is_placeholder and shape.has_text_frame]
    frame = boxes[-1].text_frame
    for para in list(frame.paragraphs)[len(lines):]:
        para._p.getparent().remove(para._p)
    for i, line in enumerate(lines):
        para = frame.paragraphs[i] if i < len(frame.paragraphs) else frame.add_paragraph()
        para.text = line
        para.font.size = Pt(22)


def test_example():
    # Validate outcome and rollback locally. The live RDS exercise uses PostgreSQL.
    with sqlite3.connect(':memory:') as db:
        db.execute('CREATE TABLE lab_stock(sku INTEGER PRIMARY KEY, available INTEGER CHECK(available >= 0))')
        db.execute('INSERT INTO lab_stock VALUES (1001, 1), (1002, 1)')
        assert db.execute(RESERVE).fetchall() == [(0,)]
        assert db.execute(RESERVE).fetchall() == []
        db.execute('SAVEPOINT checkout')
        assert db.execute(RESERVE.replace('1001', '1002')).fetchall() == [(0,)]
        db.execute('ROLLBACK TO SAVEPOINT checkout')
        assert db.execute('SELECT available FROM lab_stock ORDER BY sku').fetchall() == [(0,), (1,)]


def build(source, output):
    test_example()
    deck = Presentation(source)
    original = list(deck.slides)
    if len(original) != 30 or '무결성' not in original[21].shapes.title.text:
        raise ValueError('Expected the 30-page CD12-1 Part 1 original.')
    ref = original[19]
    added = {}

    added[5] = case_slide(deck, ref, '설계 흐름 | 마지막 재고 1개를 어떻게 팔까?',
        '상황 · 고객 A와 B가 같은 상품의 마지막 1개를 동시에 주문한다.',
        [('① 요구 분석', '성공한 주문은 1건이어야 한다. 실패한 요청에는 품절 결과를 반환한다.'),
         ('② 개념 모델', '고객·주문·주문항목·상품과 재고 예약의 관계를 그린다.'),
         ('③ 논리 모델', '주문항목에 수량과 판매 당시 단가를 두고 주문·상품 키를 연결한다.'),
         ('④ 물리 모델', '재고가 충분할 때만 조건부 갱신하고, 재고와 주문 변경을 함께 기록한다.')],
        '검증 기준 · 성공 1건, 품절 1건, 최종 판매 가능 재고 0개.',
        ('수업용 가상 쇼핑몰 사례',))
    note(added[5], '같은 업무 상황을 설계 단계별 산출물로 바꿉니다.',
         '두 요청이 재고 1개를 읽더라도 성공은 한 건만 허용합니다. 분석에서는 기대 결과를, 설계에서는 데이터와 변경 규칙을 정합니다.',
         '요구 수집에서 성공 판정 기준을 명시합니다.')

    added[16] = case_slide(deck, ref, '요구사항 | 재고 1개를 두 고객이 주문하면',
        '고객·운영팀·결제 대행사의 요구를 검증할 수 있는 조건으로 바꾼다.',
        [('고객 · 품절 안내', '재고 예약에 실패한 주문에는 결제 요청을 시작하지 않고 품절을 알려 준다.'),
         ('운영팀 · 재고 신뢰성', '재고 1개에 주문 2건이 경합하면 예약 1건만 승인하고 재고는 0개가 된다.'),
         ('결제 대행사 · 재통지', '같은 승인 통지가 다시 도착해도 결제 성공 처리와 재고 확정은 1회만 한다.'),
         ('검증 증거', '주문별 상태, 재고 변화, 외부 결제 이벤트 ID로 결과를 대조한다.')],
        '명세서에 입력 조건, 기대 결과, 확인할 데이터를 함께 적는다.',
        ('※ ID: Identifier (식별자)',))
    note(added[16], '요구사항을 관찰할 수 있는 입출력 조건으로 적습니다.',
         '결제 통지 중복은 외부 이벤트 ID를 고유하게 기록해 처리합니다. 벤치마크 목표는 트래픽 가정을 확인한 후 별도로 정합니다.',
         '다음 업무 영역 분할에서 어떤 시스템이 어떤 정보를 소유하는지 찾습니다.')

    added[18] = case_slide(deck, ref, '업무 영역 | 주문·재고·결제·배송',
        '고객 주문 → 주문·재고 → 외부 결제 → 배송의 흐름을 따라간다.',
        [('주문·재고', '주문항목 저장과 재고 예약을 한 데이터베이스 트랜잭션으로 처리한다.'),
         ('결제 대행사', '예약 성공 후 외부 결제를 요청한다. 승인 통지는 이벤트 ID로 중복 제거한다.'),
         ('배송', '결제 승인 확인 후 배송을 만든다. 운송장 번호와 상태를 배송 영역에서 관리한다.'),
         ('실패·시간 초과', '결제 실패나 예약 만료 시 예약 해제 절차를 별도로 실행한다.')],
        '외부 결제와 로컬 재고 변경은 각각 결과를 기록하고 상태로 연결한다.',
        ('※ ID: Identifier (식별자)',))
    note(added[18], '업무 영역과 외부 연동 지점에서 교환할 데이터를 구분합니다.',
         '데이터베이스 트랜잭션 안에서 외부 결제 응답을 기다리면 락이 길어질 수 있습니다. 승인 후 내부 반영이 실패하면 같은 이벤트를 재처리하거나 정산 대조를 수행합니다.',
         '다음 데이터 요구 분석에서 주문항목·결제 이벤트·재고 상태에 필요한 속성을 찾습니다.')

    added[22] = case_slide(deck, ref, 'Shopify 사례 | 판매 가능한 재고는?',
        'Shopify는 판매 가능, 주문에 배정, 판매 불가 등 재고 상태를 구분한다.',
        [('Available · 판매 가능', '새 고객에게 판매할 수 있는 재고다.'),
         ('Committed · 배정', '주문에 배정돼 새 주문에 판매할 수 없는 재고다.'),
         ('수업 모델', '판매 가능 수량(available)과 예약·확정 상태를 구분해 중복 판매를 검증한다.'),
         ('관계와 검증', '주문과 상품은 주문항목으로 연결하고, 예약 가능 수량이 0 미만이 되는지 검사한다.')],
        '남은 재고의 의미를 먼저 합의하면 화면의 품절 상태와 처리 규칙이 일치한다.',
        ('출처  Shopify Help Center · Understanding inventory states',))
    note(added[22], '판매 가능 재고와 주문에 배정된 재고는 서로 다른 상태입니다.',
         'Shopify 공식 문서가 설명한 상태 개념을 소개합니다. 수업 모델의 스키마와 예약 트랜잭션은 별도로 설계한 간소화 예입니다.',
         '다음 장에서 판매 가능 재고 1개를 갱신할 때 처리 경계를 확인합니다.', SHOPIFY)

    added[25] = case_slide(deck, ref, '트랜잭션 설계 | 재고 확인과 차감을 한 문장으로',
        '두 요청이 먼저 재고를 읽으면 둘 다 1개가 남았다고 판단할 수 있다.',
        [('문제', '조회와 차감 사이에 다른 주문도 같은 재고를 볼 수 있다.'),
         ('해결', 'UPDATE에 available ≥ 요청 수량 조건을 넣고 갱신된 행을 반환한다.'),
         ('판정', '갱신 1행이면 예약 성공, 0행이면 품절로 처리한다.'),
         ('검증', '주문 저장이 실패하면 같은 DB 트랜잭션의 재고 차감도 롤백한다.')],
        '재고 행 1개에서 시작하면 첫 예약 성공 후 판매 가능 수량은 0개다.',
        ('※ SQL: Structured Query Language (구조화 질의어) · DB: Database (데이터베이스)',
         '출처  PostgreSQL 문서 · Transaction Isolation'),)
    note(added[25], '조건부 갱신으로 재고 확인과 차감을 한 문장으로 처리합니다.',
         RESERVE + '\nPostgreSQL의 READ COMMITTED에서 같은 행의 선행 갱신을 기다린 후 검색 조건을 새 버전에 다시 적용합니다. 예약과 주문 저장은 하나의 데이터베이스 트랜잭션에 넣습니다.',
         '이어지는 Colab 실습에서 조건부 갱신과 롤백 결과를 확인합니다.', POSTGRES)

    lab = case_slide(deck, ref, 'Colab 실습 | 재고 차감과 롤백 결과 확인',
        '발표자 노트의 Python 셀을 Colab으로 옮겨 PostgreSQL에서 실행한다.',
        [('준비', 'AWS RDS PostgreSQL의 dvdrental에 연결한다. 연결 정보는 보안 비밀로 읽는다.'),
         ('초기화', '임시 재고 표에 상품 1001·1002를 각각 재고 1개로 넣는다.'),
         ('조건부 예약', '같은 예약을 두 번 순차 실행한다. 첫 결과 [(0,)], 두 번째 결과 []를 확인한다.'),
         ('롤백', '상품 1002의 예약을 취소한다. 롤백 후 재고가 1개로 돌아오는지 확인한다.')],
        '실습 확장 · 동시성은 세션 2개로 같은 행을 갱신해 별도로 확인한다.',
        ('※ AWS: Amazon Web Services · RDS: Relational Database Service · CA: Certificate Authority',
         '출처  AWS RDS 문서 · PostgreSQL 서버 인증서 검증'))
    note(lab, '순차 예약 결과와 롤백 결과를 확인합니다.',
         '실행 전 실습용 서버 접속과 AWS RDS 인증서 번들을 준비합니다. 아래 셀은 연결 종료 시 삭제되는 임시 표를 사용합니다.\n\n' + CELL,
         '첫 결과와 둘째 결과가 다른 이유를 말하고, 다음 시간에는 두 세션의 경합을 확인합니다.', RDS)

    # Keep the original tables and update the specific rows that conflict with the example.
    entities = first_table(original[19])
    entities.cell(3, 1).text = '주문ID, 고객ID, 주문일시, 주문 상태, 총금액, 배송 주소'
    entities._tbl.append(deepcopy(entities.rows[len(entities.rows) - 1]._tr))
    entities.cell(len(entities.rows)-1, 0).text = 'Order_Items (주문항목)'
    entities.cell(len(entities.rows)-1, 1).text = '주문ID, 상품ID, 수량, 판매 당시 단가'
    for row in entities.rows:
        row.height = Inches(0.46)
    for cell in entities.rows[len(entities.rows) - 1].cells:
        for paragraph in cell.text_frame.paragraphs:
            for run in paragraph.runs:
                set_run(run, 14, INK, cell == entities.cell(len(entities.rows) - 1, 0))
    for shape in original[17].shapes:
        if shape.has_text_frame and shape.text.startswith('업무 영역 분할도는 추후'):
            shape.text_frame.paragraphs[0].text = '다음 쪽에서는 주문·재고·결제·배송 사이에서 오가는 데이터를 확인합니다.'
    text_box(original[24], (1.05, 6.5, 11.2, 0.38),
             ('※ ACID: Atomicity, Consistency, Isolation, Durability · DB: Database',), 11)
    table = first_table(original[20])
    table.cell(2, 1).text = 'N:M 관계. 주문항목으로 연결하며 상품 수량과 판매 당시 단가를 기록합니다.'
    table.cell(3, 1).text = '1:N 관계. 주문 1건에 결제 재시도 기록이 여러 건 생길 수 있습니다.'
    table.cell(4, 1).text = '이 실습에서는 분할 배송 없이 주문당 배송 0~1건을 가정합니다.'
    table = first_table(original[23])
    table.cell(1, 1).text = '주문과 재고 예약을 함께 기록 → DB 커밋 → 외부 결제 요청 → 승인 후 배송 준비'
    table.cell(2, 1).text = '취소 요청 → 외부 환불 결과 확인 → 환불 상태 및 재고 복구를 업무 규칙에 따라 반영. 실패는 재처리·대조.'
    replace_body(original[24], ('ACID · 원자성, 일관성, 격리성, 지속성',
        '동시 주문 · 재고가 충분할 때만 갱신하고 영향을 받은 행 수로 성공을 판단합니다.',
        'DB 변경 실패 · 같은 트랜잭션의 주문과 재고 변경을 롤백합니다.',
        '외부 결제 실패 · 예약 해제, 재시도 또는 정산 대조로 처리합니다.'))

    note(original[19], '주문과 주문항목을 분리합니다.',
         '한 주문에 여러 상품을 담기 위해 주문항목을 둡니다. 판매 당시 단가와 현재 상품 가격은 다르게 저장합니다.',
         '다음 장에서 주문–상품과 주문–결제의 관계를 비교합니다.')
    note(original[20], '업무 규칙에 따라 관계의 개수를 정합니다.',
         '결제 재시도를 보존하고 배송은 수업 범위에서 0~1건으로 제한합니다. 결제 승인 정책과 분할 배송 여부에 따라 모델이 달라집니다.',
         '무결성 제약으로 이 관계를 검증합니다.')
    note(original[23], '주문 예약과 외부 결제·환불의 처리 경계를 구분합니다.',
         '로컬 데이터베이스 롤백으로 외부 결제를 되돌릴 수 없습니다. 외부 통지는 중복 처리하지 않고 승인·환불 불일치는 재처리 또는 대조합니다.',
         '동시 주문 시 재고가 음수가 되지 않는 절차를 살펴봅니다.')
    note(original[24], '동시성 제어와 오류 복구 규칙을 적용합니다.',
         '조건부 갱신 결과 0행을 재고 부족으로 해석합니다. 외부 호출은 로컬 데이터베이스 커밋과 별개의 단계로 관리합니다.',
         '다음 사례와 실습으로 확인합니다.', POSTGRES)

    ids = deck.slides._sldIdLst
    mapping = {slide.slide_id: item for slide, item in zip(deck.slides, list(ids), strict=True)}
    ordered = []
    for i, slide in enumerate(original, 1):
        ordered.append(mapping[slide.slide_id])
        if i in added:
            ordered.append(mapping[added[i].slide_id])
        if i == 25:
            ordered.append(mapping[lab.slide_id])
    ids[:] = ordered
    deck.save(output)
    result = Presentation(output)
    assert len(result.slides) == 36
    assert result.slides[34].notes_slide.notes_text_frame.text == original[28].notes_slide.notes_text_frame.text
    assert [s.slide_id for s in result.slides if s.slide_id in {o.slide_id for o in original}] == [o.slide_id for o in original]
    assert [s.shapes.title.text.split(' | ')[0] for s in result.slides if s.slide_id == lab.slide_id] == ['Colab 실습']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve():
        parser.error('Use separate paths for the original and the teaching edition.')
    build(args.source, args.output)
