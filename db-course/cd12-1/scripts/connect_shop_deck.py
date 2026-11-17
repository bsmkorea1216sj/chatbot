"""Connect the 36-slide CD12-1 deck with the mini shop Colab notebook."""
import argparse
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

COUPANG = "https://news.coupang.com/archives/61370/"
COLAB_DOC = "https://github.com/googlecolab/colabtools/blob/main/google/colab/output/_util.py"
NAVY = RGBColor.from_string("103858")


def write(shape, lines, size=None):
    frame = shape.text_frame
    for paragraph in list(frame.paragraphs)[len(lines):]:
        paragraph._p.getparent().remove(paragraph._p)
    for i, line in enumerate(lines):
        paragraph = frame.paragraphs[i] if i < len(frame.paragraphs) else frame.add_paragraph()
        paragraph.text = line
        if size is not None:
            for run in paragraph.runs:
                run.font.name = "맑은 고딕"
                run.font.size = Pt(size)
                run.font.color.rgb = NAVY


def notes(slide, core, detail, next_step, source):
    slide.notes_slide.notes_text_frame.text = "\n".join((
        "【슬라이드 핵심】", core, "【강의 설명】", detail,
        "【연결】", next_step, "【출처】", source,
    ))


def table(slide):
    return next(shape.table for shape in slide.shapes if shape.has_table)


def edit_rows(slide, rows):
    t = table(slide)
    for i, row in enumerate(rows, 1):
        for j, value in enumerate(row):
            cell = t.cell(i, j)
            cell.text = value
            for p in cell.text_frame.paragraphs:
                for run in p.runs:
                    run.font.name = "맑은 고딕"
                    run.font.size = Pt(15)
                    run.font.color.rgb = NAVY


def button(slide, label, url, x=0.98, y=6.77, width=4.9):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y),
                                   Inches(width), Inches(0.40))
    shape.fill.solid()
    shape.fill.fore_color.rgb = NAVY
    shape.line.fill.background()
    shape.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = shape.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = label
    run.font.name = "맑은 고딕"
    run.font.size = Pt(13)
    run.font.bold = True
    run.font.color.rgb = RGBColor(255, 255, 255)
    shape.click_action.hyperlink.address = url


def body(slide, lines):
    boxes = [s for s in slide.shapes if s.is_placeholder and s.has_text_frame]
    write(boxes[-1], lines, 21)


def panel(slide, title, lead, rows, end, footer, link=None):
    slide.shapes.title.text = title
    lead_box, ending, source = [s for s in slide.shapes if not s.is_placeholder and s.has_text_frame]
    write(lead_box, [lead], 20)
    write(ending, [end], 17)
    source.top = Inches(6.18)
    source.height = Inches(0.52)
    write(source, footer, 10)
    edit_rows(slide, rows)
    if link:
        button(slide, *link)


def build(source, output, notebook_id):
    deck = Presentation(source)
    if len(deck.slides) != 36 or not deck.slides[30].shapes.title.text.startswith("Colab 실습"):
        raise ValueError("Expected the current CD12-1 (26) deck.")
    s = {i: slide for i, slide in enumerate(deck.slides, 1)}
    colab = f"https://colab.research.google.com/drive/{notebook_id}"
    def jump(anchor):
        return colab + "#scrollTo=" + anchor

    for shape in s[2].shapes:
        if shape.has_text_frame and "시나리오 기반 설계 실습" in shape.text:
            for p in shape.text_frame.paragraphs:
                for r in p.runs:
                    r.text = r.text.replace("시나리오 기반 설계 실습", "미니 쇼핑몰 DB 설계와 웹앱 실습")
    panel(s[6], "설계 흐름 | 미니 쇼핑몰 만들기",
          "목표 · 상품을 고르고 주문한 뒤 배송 상태까지 확인하는 웹앱을 만든다.",
          [("① 요구 분석", "상품 목록, 주문 생성, 주문·배송 조회를 실습 범위로 정한다."),
           ("② 개념 모델", "고객·상품·주문·주문항목·배송의 관계를 찾는다."),
           ("③ 논리 모델", "기본키·외래키를 정하고 주문 시점의 단가를 주문항목에 남긴다."),
           ("④ 구현·검증", "SQLite에 표를 만들고 웹 화면에서 주문과 품절 처리까지 확인한다.")],
          "실습 완성 기준 · 주문 1건, 재고 0개, 배송 준비 중.",
          ["※ DB: Database (데이터베이스)"], ("Colab · 실습 소개 열기", jump("shop-intro")))
    notes(s[6], "하나의 쇼핑몰 시나리오를 설계와 구현에서 이어 씁니다.",
          "쿠팡의 공개 주문·배송 조회 화면을 사용자 경험 사례로 참고합니다. 수업용 모델은 SQLite와 Python으로 독립 구현했습니다.",
          jump("shop-intro"), COUPANG)

    body(s[12], ["프로젝트 목표", "가상 쇼핑몰의 상품 목록을 만들고 주문과 배송 상태를 같은 웹앱에서 확인한다.",
                 "고객 화면에서는 가격과 잔여 재고를 보고 수량을 선택한다.",
                 "주문 완료 후 주문번호, 판매 당시 단가, 배송 준비 상태를 확인한다."])
    body(s[13], ["이번 실습 범위", "상품 목록 · 실습 고객 1명 · 상품별 수량 주문 · 주문 및 배송 조회",
                 "가상 데이터만 사용한다. 실제 결제, 로그인, 배송사 연동은 후속 범위다.",
                 "DB는 SQLite, 화면과 요청 처리는 Python 표준 라이브러리로 구현한다."])

    panel(s[18], "요구사항 | 학생이 직접 확인할 네 가지",
          "마우스 1개를 담아 주문하면 주문 기록과 재고가 함께 바뀌어야 한다.",
          [("상품 조회", "상품명, 가격, 판매 가능 수량이 나온다. 무선 마우스는 재고 1개다."),
           ("주문 성공", "수량 1개를 주문하면 주문항목과 배송 준비 상태가 생긴다."),
           ("품절 처리", "재고 0개 상태에서 다시 요청하면 HTTP 409를 반환하고 주문이 늘지 않는다."),
           ("가격 보존", "상품 가격을 고쳐도 기존 주문은 주문 당시 단가 19,900원을 보여 준다.")],
          "검증 기준은 입력과 기대 결과를 함께 기록한다.",
          ["※ HTTP: Hypertext Transfer Protocol (웹 요청·응답 규약)"],
          ("Colab · 실행 검증 셀", jump("shop-check")))
    notes(s[18], "정상 주문과 품절 요청을 각각 검증합니다.",
          "태블릿·휴대폰에서도 같은 화면 흐름을 사용합니다. 가격을 폼에서 받지 않고 상품 표의 가격을 주문항목에 복사합니다.",
          jump("shop-check"), "수업용 예제 · 자동 검증 셀")

    panel(s[21], "업무 영역 | 상품 화면에서 배송 조회까지",
          "웹 요청 하나가 어떤 업무와 어떤 표를 연결하는지 따라간다.",
          [("상품 목록", "GET / → products 조회 → 가격과 재고 표시"),
           ("주문 생성", "POST /orders → 재고 조건 확인 → 주문·주문항목·배송 행 생성"),
           ("주문·배송 조회", "GET /orders → 주문·주문항목·상품·배송을 조인해 상태와 합계 표시"),
           ("품절 처리", "재고 갱신 0행 → 주문 생성 중단 → 품절 응답")],
          "배송 준비 상태는 실습용 데이터로 주문 시 함께 기록한다.",
          ["※ GET·POST: 웹 조회·전송 요청 메서드"], ("Colab · 웹앱 코드 셀", jump("shop-app")))
    notes(s[21], "화면 요청을 데이터베이스 읽기와 쓰기에 대응시킵니다.",
          "실습에서는 배송 라벨이나 결제 승인 같은 외부 호출 없이 배송 준비 행을 생성합니다. 상품 조회와 주문 내역 조회는 읽기, 주문 실행은 쓰기입니다.",
          jump("shop-app"), "수업용 예제 · 웹앱 코드 셀")

    t = table(s[23])
    data = [("customers", "id, name · 실습 고객"),
            ("products", "id, name, price, stock · 현재 판매가와 재고"),
            ("orders", "id, customer_id, created_at · 주문 헤더"),
            ("order_items", "order_id, product_id, quantity, unit_price · 판매 당시 단가"),
            ("shipments", "order_id, status · 준비 중/배송 중/배송 완료"),
            ("후속 확장 · 결제", "결제 시도와 승인 식별자를 관리"),
            ("후속 확장 · 리뷰", "고객·상품을 연결하고 평점과 내용을 기록")]
    edit_rows(s[23], data)
    button(s[23], "Colab · DB 생성 셀", jump("shop-db"), y=6.37)
    notes(s[23], "실습에서 사용하는 다섯 표를 확인합니다.",
          "주문과 상품은 주문항목에서 연결합니다. 주문항목은 수량과 판매 당시 단가를 함께 보존합니다.",
          jump("shop-db"), "수업용 예제 · DB 생성 셀")
    edit_rows(s[24], [("고객 → 주문", "1:N · orders.customer_id가 customers.id를 참조"),
                      ("주문 → 주문항목", "1:N · order_items.order_id가 orders.id를 참조"),
                      ("상품 → 주문항목", "1:N · order_items.product_id가 products.id를 참조"),
                      ("주문 → 배송", "1:1 · shipments.order_id는 기본키이자 주문 외래키"),
                      ("주문항목 → 단가", "unit_price에 주문 시점의 가격을 복사해 과거 합계를 보존")])
    notes(s[24], "주문항목이 주문과 상품의 다대다 관계를 연결합니다.",
          "주문항목의 복합 기본키로 같은 주문에 같은 상품이 두 번 기록되는 것을 막습니다. 이 웹앱은 주문 버튼 한 번에 상품 한 종류를 저장합니다.",
          jump("shop-db"), "수업용 예제 · DB 생성 셀")
    body(s[25], ["실습 DB의 무결성 제약", "기본키 · 상품과 주문을 고유하게 식별한다.",
                 "외래키 · 주문항목과 배송은 존재하는 주문만 참조한다.",
                 "CHECK · 재고와 가격은 0 이상, 수량은 1 이상으로 제한한다."])
    panel(s[26], "쿠팡 사례 | 주문목록에서 배송조회까지",
          "마이쿠팡의 주문목록에서 상품을 선택해 배송 현황을 확인하는 흐름을 참고한다.",
          [("공개 고객 경험", "마이쿠팡 → 주문목록/배송조회 → 상품 선택 → 배송조회"),
           ("화면으로 옮기기", "미니 쇼핑몰에서는 상품 목록과 주문·배송 조회 화면을 만든다."),
           ("데이터로 옮기기", "주문번호를 기준으로 주문항목·상품·배송 상태를 연결한다."),
           ("수업용 단순화", "주문 생성 시 배송 준비 행을 넣고, 조회 화면에서 상태를 표시한다.")],
          "공개 고객 경험을 참고한 독립 실습 설계다.",
          ["출처  쿠팡 뉴스룸 · 자주 묻는 질문 · 배송 문의"],
          ("쿠팡 뉴스룸 · 배송조회 사례", COUPANG))
    notes(s[26], "공개 화면 흐름을 설계 요구로 바꾸어 봅니다.",
          "쿠팡의 주문목록과 배송조회 경로는 공식 공개 사례입니다. 실습의 테이블, 코드, 상태 전이 범위는 수업용으로 설계했습니다.",
          jump("shop-app"), COUPANG)

    edit_rows(s[28], [("상품 목록", "products에서 상품명·가격·재고 조회"),
                      ("주문 생성", "재고 확인·차감, 주문·주문항목·배송 기록을 한 트랜잭션으로 처리"),
                      ("주문·배송 조회", "orders, order_items, products, shipments를 키로 조인해 내역 표시"),
                      ("실패 처리", "품절이면 주문을 생성하지 않고 오류 응답. 예외 발생 시 롤백.")])
    notes(s[28], "조회와 변경의 실행 경계를 확인합니다.",
          "상품 목록과 배송 조회는 읽기입니다. 주문 생성은 재고와 주문 데이터를 함께 바꾸는 작업입니다.",
          jump("shop-order"), "수업용 예제 · 주문 로직 셀")
    body(s[29], ["ACID · 원자성, 일관성, 격리성, 지속성",
                 "재고가 충분할 때만 차감하고, 바뀐 행이 1개일 때 주문을 진행한다.",
                 "재고·주문·배송 준비 상태를 함께 저장한다. 오류가 나면 같은 변경을 되돌린다.",
                 "SQLite는 BEGIN IMMEDIATE로 쓰기 트랜잭션을 시작한다."])
    notes(s[29], "재고 차감과 주문 저장은 하나의 트랜잭션입니다.",
          "이 교육용 웹 서버의 테스트는 순차 요청으로 검증합니다. SQLite는 쓰기 트랜잭션을 직렬화하며, 동시 요청 비교는 후속 실습에서 다룹니다.",
          jump("shop-order"), "수업용 예제 · 주문 로직 셀")
    panel(s[30], "트랜잭션 | 마지막 마우스 1개 주문",
          "상품 101의 재고는 1개, 가격은 19,900원에서 시작한다.",
          [("첫 요청", "조건부 UPDATE가 1행을 바꾼다. 주문·주문항목·배송 행을 함께 저장한다."),
           ("두 번째 요청", "차감 가능한 행이 0개다. HTTP 409 품절 응답을 반환한다."),
           ("DB에서 확인", "재고 0개, 주문 1건, 배송 준비 중, 주문 당시 단가 19,900원."),
           ("추가 검증", "상품 가격을 21,900원으로 바꿔도 기존 주문 단가 19,900원은 유지된다.")],
          "Colab의 자동 검증은 복제 데이터베이스에서 요청을 보낸다.",
          ["※ DB: Database · HTTP: Hypertext Transfer Protocol"],
          ("Colab · 검증 셀 열기", jump("shop-check")))
    notes(s[30], "품절과 가격 이력 보존을 자동 검증합니다.",
          "첫 주문 이후 같은 요청을 다시 보내 409를 확인합니다. 존재하지 않는 주문에 주문항목을 넣지 못하는 외래키 제약도 확인합니다.",
          jump("shop-check"), "수업용 예제 · HTTP 검증 셀")
    panel(s[31], "Colab 실습 | 쇼핑몰 DB에서 웹앱까지",
          "아래 링크에서 코드 셀을 위에서부터 실행하고 미리보기에서 직접 주문한다.",
          [("① DB 생성", "SQLite에 고객 1명과 상품 3개를 넣고 표 5개를 생성한다."),
           ("② 주문 로직", "재고 조건 갱신과 주문·배송 기록을 연결한다."),
           ("③ 웹앱 구현", "상품 목록, 주문 요청, 주문·배송 조회 화면을 만든다."),
           ("④ 검증 → ⑤ 미리보기", "자동 검증을 실행한다. 웹앱에서 주문한 뒤 배송 준비 중과 품절을 확인한다.")],
          "제출 · 상품 재고 1개 → 주문·배송 준비 중 → 품절 화면.",
          ["※ DB: Database (데이터베이스)"],
          ("Colab · DB 생성부터 실행", jump("shop-db")))
    button(s[31], "Colab · 웹앱 미리보기 셀", jump("shop-run"), x=6.05)
    notes(s[31], "교안의 데이터 모델을 코드와 웹 화면으로 연결합니다.",
          "미리보기는 현재 Colab 런타임에서 실행합니다. 위쪽 셀을 먼저 실행하고 미리보기 셀을 클릭합니다. 초기화가 필요하면 DB 생성 셀과 미리보기 셀을 다시 실행합니다.",
          jump("shop-submit"), COLAB_DOC)
    body(s[33], ["완성 확인 · 상품 목록에서 재고와 가격을 확인한다.",
                 "무선 마우스 1개를 주문하고 주문번호와 배송 준비 상태를 확인한다.",
                 "상품 화면으로 돌아가 품절을 확인하고 자동 검증 결과를 함께 제출한다."])
    button(s[33], "Colab · 제출 항목 확인", jump("shop-submit"), y=6.37)
    body(s[34], ["후속 설계 · 같은 키 구조를 PostgreSQL로 옮긴다.",
                 "두 세션을 사용해 마지막 재고의 동시 주문을 비교한다.",
                 "실제 결제·배송 연동에는 승인 통지 중복과 실패 복구 규칙을 추가한다."])

    deck.save(output)
    result = Presentation(output)
    assert len(result.slides) == 36
    assert result.slides[34].shapes[0].text == s[35].shapes[0].text
    urls = [sh.click_action.hyperlink.address for slide in result.slides for sh in slide.shapes
            if sh.click_action.hyperlink.address]
    assert set(jump(a) for a in ("shop-intro", "shop-db", "shop-app", "shop-check", "shop-run", "shop-submit")) <= set(urls)
    print("36 pages; Summary and Colab links verified")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("notebook_id")
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve():
        parser.error("Use distinct input and output paths.")
    build(args.source, args.output, args.notebook_id)
