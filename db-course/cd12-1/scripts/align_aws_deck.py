"""Align CD12-1 slide content, text sizes and links with the AWS Colab lab."""
import argparse
import json
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_SHAPE_TYPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

BASE = "https://colab.research.google.com/drive/1URPntHhY0jY96psj9cK0Khrzq3gLb8KX"
BLUE = RGBColor.from_string("103858")
PALE = RGBColor.from_string("E6F5FF")
PAGES = {
    6: [("실습 소개 열기", "CD12-1 · AWS 쇼핑몰 DB와 웹앱", None)],
    18: [("실행 검증 셀", "4. 실행 전 확인", "shop-check")],
    21: [("웹앱 코드 셀", "3. 웹앱 화면과 요청 연결", "shop-app")],
    23: [("DB 생성 셀", "1. 쇼핑몰 DB 생성", "shop-db")],
    24: [(None, "1. 쇼핑몰 DB 생성", "shop-db")],
    26: [(None, "3. 웹앱 화면과 요청 연결", "shop-app")],
    28: [(None, "2. 주문·취소 처리", "shop-order")],
    29: [(None, "2. 주문·취소 처리", "shop-order")],
    30: [("검증 셀 열기", "4. 실행 전 확인", "shop-check")],
    31: [("DB 생성부터 실행", "0. AWS RDS 준비와 연결", "shop-aws-guide"),
         ("웹앱 미리보기 셀", "5. 실제 웹앱 화면 열기", "shop-run")],
    33: [("제출 항목 확인", "제출", "shop-submit")],
    34: [(None, "6. 실습 데이터와 AWS 자원 정리", "shop-clean-guide")],
}
MAIN_PANELS = {6, 18, 21, 26, 30, 31}
TABLE_PAGES = {6, 7, 8, 9, 10, 17, 18, 20, 21, 23, 24, 26, 28, 30, 31}


def source_text(cell):
    return "".join(cell["source"])


def validate_notebook(notebook):
    cells = json.loads(notebook.read_text(encoding="utf-8"))["cells"]
    ids = {c["metadata"]["id"]: i for i, c in enumerate(cells) if "id" in c["metadata"]}
    for _, heading, anchor in (row for rows in PAGES.values() for row in rows):
        if anchor is None:
            assert source_text(cells[0]).splitlines()[0].lstrip("# ") == heading
            continue
        c = cells[ids[anchor]]
        assert c.get("id", anchor) == anchor
        section = c if c["cell_type"] == "markdown" else cells[ids[anchor] - 1]
        assert source_text(section).splitlines()[0].lstrip("# ") == heading


def set_minimum(frame, point):
    for paragraph in frame.paragraphs:
        for run in paragraph.runs:
            if run.text.strip() and run.font.size is not None and run.font.size.pt < point:
                run.font.size = Pt(point)


def create_button(slide, label, address, existing=None, x=0.98, y=6.66, width=5.25):
    shape = existing
    if shape is None:
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                       Inches(x), Inches(y), Inches(width), Inches(0.53))
    shape.fill.solid()
    shape.fill.fore_color.rgb = PALE
    shape.line.color.rgb = BLUE
    shape.height = Inches(0.53)
    frame = shape.text_frame
    frame.clear()
    frame.margin_top = Pt(0)
    frame.margin_bottom = Pt(0)
    frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = frame.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = label
    run.hyperlink.address = address
    run.font.name = "맑은 고딕"
    run.font.size = Pt(16)
    run.font.bold = True
    run.font.underline = False
    run.font.color.rgb = BLUE
    shape.click_action.hyperlink.address = address
    return shape


BODY = {
    13: ("AWS 실습 범위", "상품 목록 · 수량 주문 · 주문과 배송 상태 조회 · 주문 취소",
         "Colab이 웹 화면을 띄우고 AWS RDS PostgreSQL이 데이터를 저장합니다.",
         "실습 고객과 상품만 사용합니다. 결제와 실제 배송 연동은 후속 범위입니다."),
    25: ("PostgreSQL의 무결성 제약", "기본키는 상품·주문을 식별하고 외래키는 연결된 주문을 검증합니다.",
         "CHECK로 재고·가격은 0 이상, 수량은 1 이상으로 제한합니다.",
         "주문을 삭제하면 주문항목과 배송 행은 ON DELETE CASCADE로 함께 삭제됩니다."),
    29: ("ACID · 원자성, 일관성, 격리성, 지속성", "예약할 수 있을 때만 재고를 차감하고, 주문·배송 기록을 함께 저장합니다.",
         "준비 중 주문을 잠그고 재고를 복구한 뒤 주문을 삭제합니다.",
         "예약이나 취소 처리 중 오류가 나면 같은 트랜잭션의 변경을 되돌립니다."),
    33: ("제출 화면 · 상품 재고 1개 → 주문·배송 준비 중 → 품절",
         "주문 취소 및 삭제를 누르고 상품 화면에서 재고가 1개로 돌아왔는지 확인합니다.",
         "자동 검증 결과와 함께 제출하세요."),
    34: ("실습 끝내기", "Colab 6단계에서 정리 함수를 정의하고 cleanup_lab(“DELETE LAB”)을 실행합니다.",
         "현재 런타임에서 만든 스키마와 표만 삭제합니다. 웹앱 미리보기도 종료됩니다.",
         "별도로 만든 전용 RDS 인스턴스는 스냅샷 보존 여부를 확인한 뒤 AWS 콘솔에서 삭제합니다."),
}

ROW_UPDATES = {
    6: {4: ("④ 구현·검증", "AWS RDS PostgreSQL에 표 5개를 만들고 Colab에서 웹앱을 엽니다.")},
    18: {4: ("가격·취소 검증", "기존 주문 단가는 유지됩니다. 준비 중 주문을 삭제하면 재고가 복구됩니다.")},
    21: {4: ("주문 취소", "POST /orders/cancel → 재고 복구 → 주문·주문항목·배송 행 삭제")},
    28: {4: ("취소·실패 처리", "배송 준비 중에는 재고를 복구하고 주문을 삭제합니다. 오류가 나면 롤백합니다.")},
    30: {4: ("취소·검증", "주문·배송 기록 삭제, 재고 1개 복구, 중복 취소 차단을 확인합니다.")},
    31: {1: ("0. AWS 준비 → 1. DB 생성", "RDS 접속 정보를 등록하고 PostgreSQL에 실습 표 5개를 생성합니다."),
         2: ("2. 주문·취소 처리", "재고 차감과 주문을 저장합니다. 취소하면 주문을 삭제하고 재고를 돌려놓습니다."),
         3: ("3. 웹앱 구현 → 4. 검증", "상품·주문·배송 화면을 만들고 품절과 취소를 테스트합니다."),
         4: ("5. 실제 화면 → 6. 정리", "Colab에서 주문·취소를 체험하고 끝나면 실습 스키마를 정리합니다.")},
}
NOTES = {
    6: "쿠팡 공개 주문·배송 흐름을 참고합니다. 화면은 Colab, 저장은 AWS RDS PostgreSQL입니다.",
    18: "정상 주문, 품절, 주문 당시 단가 보존, 취소 후 재고 복구를 자동 검증합니다.",
    21: "GET 요청은 조회합니다. 주문과 취소 POST 요청은 연결된 데이터를 트랜잭션에서 함께 바꿉니다.",
    25: "배송 준비 상태인 주문만 앱에서 취소할 수 있습니다. 연결된 주문항목·배송 행은 외래키의 연쇄 삭제로 정리됩니다.",
    28: "주문과 취소의 재고 갱신, 주문 저장 또는 삭제는 각 트랜잭션에서 함께 처리합니다.",
    29: "주문 취소는 주문과 배송 행을 잠그고 준비 중인지 다시 읽은 후 재고를 복구합니다. 이미 취소된 주문이면 아무 행도 바꾸지 않습니다.",
    30: "Colab 검증 셀은 별도 PostgreSQL 스키마를 만들고 검증 후 정리합니다. 미리보기의 주문 이력은 영향받지 않습니다.",
    31: "연결 준비 → 표 생성 → 주문·취소 → 웹앱 → 검증 → 실제 화면 → 정리 순서입니다. Colab에서 실제 화면이 표시됩니다.",
    33: "실행 결과를 캡처해 제출합니다.",
    34: "공유 RDS 자체는 계속 사용합니다. 종료 정리 셀은 이번 런타임에서 만든 스키마와 표를 정리합니다.",
}


def rewrite(shape, lines):
    frame = shape.text_frame
    for paragraph in list(frame.paragraphs)[len(lines):]:
        paragraph._p.getparent().remove(paragraph._p)
    for i, line in enumerate(lines):
        p = frame.paragraphs[i] if i < len(frame.paragraphs) else frame.add_paragraph()
        p.text = line
        for run in p.runs:
            run.font.name = "맑은 고딕"
            run.font.color.rgb = BLUE
            run.font.size = Pt(23)


def update_case(slide, page):
    if page in BODY:
        content = [s for s in slide.shapes if s.is_placeholder and s.has_text_frame][-1]
        rewrite(content, BODY[page])
    for row, (label, explanation) in ROW_UPDATES.get(page, {}).items():
        table = next(sh.table for sh in slide.shapes if sh.has_table)
        for j, value in enumerate((label, explanation)):
            t = table.cell(row, j)
            t.text = value
            for paragraph in t.text_frame.paragraphs:
                for run in paragraph.runs:
                    run.font.name = "맑은 고딕"
                    run.font.size = Pt(18)
                    run.font.color.rgb = BLUE
                    run.font.bold = j == 0
    extra = {
        6: ("실습 완성 기준", "완성 기준 · 주문·배송 조회, 품절 확인, 취소 후 재고 복구."),
        30: ("Colab의 자동 검증", "자동 검증은 별도 PostgreSQL 스키마에서 실행합니다."),
        31: ("제출 ·", "제출 · 재고 1개 → 배송 준비 중 → 품절 → 취소·재고 복구."),
    }
    if page in extra:
        prefix, text = extra[page]
        shape, = [sh for sh in slide.shapes if sh.has_text_frame and sh.text.startswith(prefix)]
        shape.text_frame.paragraphs[0].runs[0].text = text
    if page in NOTES:
        ref = PAGES[page][0][2] if page in PAGES else None
        address = BASE + "#scrollTo=" + ref if ref else BASE
        slide.notes_slide.notes_text_frame.text = (
            "【슬라이드 핵심】\n" + NOTES[page] + "\n【연결】\n" + address
        )


def update(source, notebook, output):
    validate_notebook(notebook)
    deck = Presentation(source)
    intended = {}
    for page, slide in enumerate(deck.slides, 1):
        update_case(slide, page)
        buttons = {}
        for shape in list(slide.shapes):
            if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
                continue
            if shape.has_table and page in TABLE_PAGES:
                for cell in shape.table.iter_cells():
                    set_minimum(cell.text_frame, 18 if page in MAIN_PANELS | {23, 24, 28} else 17)
            if not shape.has_text_frame or not shape.text.strip():
                continue
            text = shape.text
            target = shape.click_action.hyperlink.address
            if target and target.startswith(BASE):
                buttons[text.removeprefix("Colab · ")] = shape
                continue
            if page == 26 and text.startswith("쿠팡 뉴스룸") and target:
                shape.top = Inches(6.66)
                create_button(slide, text, target, shape)
            if text.startswith("실습 노트북 "):
                set_minimum(shape.text_frame, 16)
            elif text.startswith("※") or text.startswith("출처"):
                set_minimum(shape.text_frame, 12)
            elif page in MAIN_PANELS and not shape.is_placeholder and not target:
                set_minimum(shape.text_frame, 20 if shape.top < Inches(3) else 19)
            elif page in (12, 13, 25, 29, 33, 34) and shape.is_placeholder:
                set_minimum(shape.text_frame, 23)
        if page == 6:
            notes = slide.notes_slide.notes_text_frame
            for paragraph in notes.paragraphs:
                for run in paragraph.runs:
                    run.text = run.text.replace(BASE + "#scrollTo=shop-intro", BASE)
        if page == 31:
            lead, = [sh for sh in slide.shapes if sh.has_text_frame and sh.text.startswith("아래 링크에서")]
            lead.text_frame.paragraphs[0].runs[0].text = "노트북에서 AWS 연결부터 실행한 뒤 실제 웹앱에서 주문과 취소를 실습합니다."
        if page not in PAGES:
            if buttons:
                raise ValueError(f"Unmapped Colab buttons on page {page}: {list(buttons)}")
            continue
        intended[page] = []
        for index, (old, heading, anchor) in enumerate(PAGES[page]):
            address = f"{BASE}#scrollTo={anchor}" if anchor else BASE
            label = "Colab · " + (heading if anchor else "실습 노트북 처음부터 열기")
            existing = buttons.pop(old) if old else None
            if existing is not None and existing.top >= Inches(6.7):
                existing.top = Inches(6.67)
            create_button(slide, label, address, existing,
                          x=6.05 if page == 26 or index else 0.98,
                          y=5.65 if page == 29 else 6.66)
            intended[page].append((label, address))
        assert not buttons, (page, buttons)
    deck.save(output)
    result = Presentation(output)
    assert len(result.slides) == len(deck.slides)
    for page, expected in intended.items():
        for label, address in expected:
            shape, = [s for s in result.slides[page - 1].shapes if s.has_text_frame and s.text == label]
            assert shape.click_action.hyperlink.address == address
            assert shape.text_frame.paragraphs[0].runs[0].hyperlink.address == address
    assert not any("SQLite" in sh.text for slide in result.slides for sh in slide.shapes if sh.has_text_frame)
    print(f"{sum(map(len, intended.values()))} buttons mapped to verified Colab sections")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    p.add_argument("notebook", type=Path)
    p.add_argument("output", type=Path)
    a = p.parse_args()
    if a.source.resolve() == a.output.resolve():
        p.error("Use distinct input and output paths.")
    update(a.source, a.notebook, a.output)
