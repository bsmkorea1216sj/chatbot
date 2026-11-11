"""Align slides 31–41 of CD11-2 with the linked Colab notebook.

Usage: python sync_colab_slides_31_41.py <source.pptx> <colab.ipynb> <output.pptx>
Dependencies: python-pptx, lxml.
"""
import argparse
import json
import posixpath
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Inches, Pt

COLAB = 'https://colab.research.google.com/drive/1xsUDOtX0SNHjjNqfqaqdGvKn3XL5StCO'
OFFICE_REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
REL_ID = f'{{{OFFICE_REL}}}id'
GLOSSARY = '※ NF: Normal Form (정규형) · JOIN: 공통 열로 두 표의 행 연결'
KEYS = 'PK: Primary Key (기본키) · FK: Foreign Key (외래키)'

PAGES = {
    31: ('Colab 실습 |', 'h7a4lykA-omG', 'Colab에서 첫 코드 셀 열기', (
        '준비 · 1차 정규화 코드 셀에서 SQLite 메모리 DB와 실습 데이터를 만듭니다.',
        '실행 순서 · 1NF → 2NF → 3NF → 4NF → 5NF. 같은 런타임에서 위에서부터 실행합니다.',
        '확인 순서 · 먼저 결과를 예측한 뒤, 출력 표와 JOIN 결과를 비교합니다.',
    ), '첫 셀을 다시 실행하면 메모리 DB가 초기화됩니다. 런타임을 다시 시작했다면 첫 셀부터 순서대로 실행합니다.'),
    32: ('원본 A |', '4kLYaXW8-omF', 'Colab · 1차 정규화 예측 질문 열기', (
        '원본 orders_raw · 주문 101(민지)은 마우스 2개, 키보드 1개를 담고 있습니다.',
        '주문 102(민지)는 마우스 1개를 담고 있습니다. 원본은 주문당 한 행입니다.',
        '예측 · 두 주문의 상품 목록을 한 상품씩 펼치면 결과는 몇 행일까요?',
    ), '노트북의 1NF 설명 셀을 읽고, 답을 예상한 뒤 다음 쪽에서 코드 셀을 실행합니다.'),
    33: ('1NF |', 'h7a4lykA-omG', 'Colab · 1차 정규화 코드 실행', (
        '실행 · 상품 목록을 펼쳐 flat에 저장합니다. 복합 PK는 (order_id, product_id)입니다.',
        '출력 · 주문·상품·수량은 (101, 10, 2), (101, 20, 1), (102, 10, 1)입니다.',
        '확인 · 상품마다 한 행이 되어 총 3행입니다. 고객명과 상품명은 여전히 반복됩니다.',
    ), 'Colab 출력 flat에는 주문 ID, 상품 ID, 고객 ID, 고객명, 상품명, 수량의 여섯 열이 있습니다. 본문의 세 값은 그중 비교할 열입니다.'),
    34: ('2NF |', 'kVksBdgL-omN', 'Colab · 2차 정규화 코드 실행', (
        'products · 상품ID가 상품명을 결정합니다. 상품 표 2행을 확인합니다.',
        'orders_2nf · 주문ID가 고객ID·고객명을 결정합니다. 주문 표 2행을 확인합니다.',
        'order_items · 수량은 주문ID와 상품ID 모두에 의존합니다. 주문상세는 3행입니다.',
    ), 'products의 PK는 product_id, orders_2nf의 PK는 order_id, order_items의 복합 PK는 (order_id, product_id)입니다. 이 셀에서 order_items.product_id만 FK로 선언되며 주문 FK는 다음 셀의 order_items_3nf에 선언됩니다.'),
    35: ('3NF |', 'LNY9jLBB-omU', 'Colab · 3차 정규화와 JOIN 검증', (
        '분리 · 주문ID → 고객ID → 고객명. customers 1행과 orders 2행을 확인합니다.',
        '검증 · order_items_3nf를 주문·고객·상품과 JOIN하면 flat의 3행이 복원됩니다.',
        '수정 · products의 상품 10을 무선 마우스로 한 번 바꾸면 주문 101·102에 반영됩니다.',
    ), 'orders.customer_id는 customers를 참조합니다. order_items_3nf의 order_id와 product_id는 각각 orders와 products를 참조합니다. 출력에서 변경된 상품명이 두 행에 표시되는지 확인합니다.'),
    36: ('원본 B |', 'EdVWHCrS-omX', 'Colab · 4차 정규화 예측 질문 열기', (
        'E01의 보유기술은 SQL과 Python, 참여 프로젝트는 P01과 P02입니다.',
        '업무 규칙 · 기술 보유와 프로젝트 참여는 서로 독립적으로 관리합니다.',
        '예측 · 기술 2개와 프로젝트 2개를 한 표에 펼치면 몇 행이 될까요?',
    ), '이 노트북의 E01 사례는 27쪽 실제 사용 기록과 업무 규칙이 다릅니다. 네 조합이 특정 프로젝트에서 해당 기술을 썼다는 뜻은 아닙니다.'),
    37: ('4NF |', 'wTF9RT0N-omZ', 'Colab · 4차 정규화 코드 실행', (
        '원본 employee_flat · 기술 2개 × 프로젝트 2개로 총 4행을 출력합니다.',
        '분리 · employee_skill 2행, employee_project 2행을 각각 확인합니다.',
        '검증 · 두 표를 employee로 JOIN하면 원본 4행이 복원됩니다.',
    ), '분리한 표의 복합 PK는 각각 (employee, skill), (employee, project)입니다. 코드는 JOIN 결과의 행 집합과 원본 행 집합이 같은지 확인합니다.'),
    38: ('원본 C |', 'bC0fAalP-omg', 'Colab · 5차 정규화 예측 질문 열기', (
        '사례 A 원본 3행 · (E01, P02, SQL), (E01, P01, Python), (E02, P01, SQL)',
        '두 열씩 추출 · 사원–프로젝트, 사원–기술, 프로젝트–기술의 세 표를 만듭니다.',
        '예측 · 세 표를 JOIN하면 원본에 없는 (E01, P01, SQL)이 생길까요?',
    ), '27쪽의 실제 사용 기록과 같은 유형입니다. 이 페이지에서는 노트북의 E01·E02 데이터를 사용합니다.'),
    39: ('5NF |', 'Uw7ZTEsE-omi', 'Colab · 5차 정규화 사례 A·B 실행', (
        '사례 A · 원본 3행 → JOIN 4행. (E01, P01, SQL)이 새로 생겨 무손실 분해가 아닙니다.',
        '사례 B · 세 쌍이 모두 유효하면 조합을 허용합니다. 원본 4행과 JOIN 4행이 일치합니다.',
        '판단 · 한 데이터셋의 일치만으로 조인 종속을 증명할 수 없습니다.',
    ), '추가 행을 만든 세 쌍은 (E01, P01), (E01, SQL), (P01, SQL)입니다. 사례 B 셀은 별도 업무 규칙에 따라 그 행을 원본에 추가합니다. 조인 종속은 해당 규칙을 만족하는 모든 유효 데이터에 적용되어야 합니다.'),
    40: ('제출 과제 |', 'Y6euVPNi-omj', 'Colab · 제출 체크리스트 열기', (
        '1~3NF · 1NF 3행, 2NF·3NF의 PK·FK, 3NF JOIN 및 상품명 수정 결과',
        '4NF · 독립 목록에서 4개 조합이 생긴 이유와 분리 후 각 표의 행 수',
        '5NF · 사례 A에서 추가된 행과 이를 만든 세 쌍, 사례 B의 업무 규칙',
    ), '노트북의 제출 항목 네 개를 확인합니다. 교안 첫 줄에는 노트북의 첫 두 제출 항목이 함께 들어 있습니다.'),
    41: ('Summary |', 'Y6euVPNi-omj', 'Colab · 제출 항목 다시 확인', None,
         'Summary의 BCNF는 이론 복습 항목입니다. 연결된 노트북의 실행 셀은 1NF, 2NF, 3NF, 4NF, 5NF 순서입니다.'),
}


def part_path(archive, part, *, rel_id=None, suffix=None):
    rels = etree.fromstring(archive.read(rels_path(part)))
    match, = [rel for rel in rels if (rel.get('Id') == rel_id if rel_id else rel.get('Type').endswith(suffix))]
    return posixpath.normpath(posixpath.join(posixpath.dirname(part), match.get('Target')))


def rels_path(part):
    directory, name = posixpath.split(part)
    return posixpath.join(directory, '_rels', name + '.rels')


def set_text(shape, text):
    first, *remaining = shape.text_frame.paragraphs[0].runs
    first.text = text
    for run in remaining:
        run._r.getparent().remove(run._r)


def add_button(slide, y, label):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                   *(Inches(v) for v in (1.05, y, 5.70, 0.62)))
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor.from_string('143D65')
    shape.line.fill.background()
    shape.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    run = shape.text_frame.paragraphs[0].add_run()
    run.text = label
    run.font.name = '맑은 고딕'
    run.font.bold = True
    run.font.size = Pt(16)
    run.font.color.rgb = RGBColor.from_string('FFFFFF')
    return shape


def add_glossary(slide, page):
    y = 6.45 if page == 41 else 5.55
    shape = slide.shapes.add_textbox(Inches(1.05), Inches(y), Inches(11.15), Inches(0.32))
    run = shape.text_frame.paragraphs[0].add_run()
    run.text = GLOSSARY
    if page in (33, 34, 35, 37, 40):
        run.text += ' · ' + KEYS
    if page == 41:
        run.text += ' · BCNF: Boyce–Codd Normal Form (보이스–코드 정규형)'
    run.font.name = '맑은 고딕'
    run.font.size = Pt(11)
    run.font.color.rgb = RGBColor.from_string('274766')


def link_button(button, relationships, url):
    existing_ids = {element.get('Id') for element in relationships}
    next_id = next(f'rId{n}' for n in range(1, len(existing_ids) + 2) if f'rId{n}' not in existing_ids)
    namespace = etree.QName(relationships).namespace
    relationship = etree.SubElement(relationships, f'{{{namespace}}}Relationship')
    relationship.attrib.update({'Id': next_id, 'Type': f'{OFFICE_REL}/hyperlink', 'Target': url, 'TargetMode': 'External'})
    for link in button._element.xpath('.//a:hlinkClick'):
        link.set(REL_ID, next_id)
    properties, = button._element.xpath('./p:nvSpPr/p:cNvPr')
    if not properties.xpath('./a:hlinkClick'):
        link = OxmlElement('a:hlinkClick')
        link.set(REL_ID, next_id)
        properties.insert(0, link)


def sync(source, notebook, output):
    cells = json.loads(notebook.read_text(encoding='utf-8'))['cells']
    anchors = {cell.get('id') or cell.get('metadata', {}).get('id') for cell in cells}
    if not {step[1] for step in PAGES.values()} <= anchors:
        raise ValueError('Some Colab cell anchors are missing from this notebook.')
    deck = Presentation(source)
    presentation = 'ppt/presentation.xml'
    changes = {}
    with ZipFile(source) as archive:
        order = etree.fromstring(archive.read(presentation)).xpath('//*[local-name()="sldId"]')
        reference_part = part_path(archive, presentation, rel_id=order[33].get(REL_ID))
        reference_rels = etree.fromstring(archive.read(rels_path(reference_part)))
        layout, = [rel for rel in reference_rels if rel.get('Type').endswith('/slideLayout')]
        for page, (title, anchor, label, lines, details) in PAGES.items():
            slide = deck.slides[page - 1]
            shapes = [shape for shape in slide.shapes if shape.has_text_frame and shape.text.strip()]
            if not shapes or not shapes[0].text.startswith(title):
                raise ValueError(f'Unexpected title on page {page}.')
            if lines:
                for shape, line in zip(shapes[1:4], lines, strict=True):
                    set_text(shape, line)
            if page == 31:
                button = shapes[4]
                set_text(button, label)
            else:
                button = add_button(slide, 5.72 if page == 41 else 4.78, label)
            add_glossary(slide, page)
            url = f'{COLAB}#scrollTo={anchor}'
            part = part_path(archive, presentation, rel_id=order[page - 1].get(REL_ID))
            notes_part = part_path(archive, part, suffix='/notesSlide')
            rel_path = rels_path(part)
            relationships = etree.fromstring(archive.read(rel_path))
            if page in (35, 36, 37):
                page_layout, = [rel for rel in relationships if rel.get('Type').endswith('/slideLayout')]
                page_layout.set('Target', layout.get('Target'))
            link_button(button, relationships, url)
            notes = slide.notes_slide.notes_text_frame
            if notes is None:
                raise ValueError(f'Speaker notes placeholder missing on page {page}.')
            if lines:
                notes.text = '\n'.join((
                    '【슬라이드 핵심】', *lines, '【강의 설명】', details,
                    '【연결】', f'{label}\n{url}', '【출처】', 'CD11-2_Colab_정규화.ipynb',
                ))
            else:
                notes.text += f'\n\n【연결】\n{details}\n{url}'
            changes.update({part: slide._element, notes_part: slide.notes_slide._element, rel_path: relationships})

        with ZipFile(output, 'w') as result:
            for entry in archive.infolist():
                xml = changes.get(entry.filename)
                data = (etree.tostring(xml, encoding='UTF-8', xml_declaration=True, standalone=True)
                        if xml is not None else archive.read(entry))
                result.writestr(entry, data)

    with ZipFile(source) as archive, ZipFile(output) as result:
        assert result.testzip() is None
        assert {name for name in archive.namelist() if archive.read(name) != result.read(name)} == set(changes)
    verified = Presentation(output)
    assert len(verified.slides) == len(deck.slides)
    for page, (_, anchor, label, _, _) in PAGES.items():
        button, = [sh for sh in verified.slides[page - 1].shapes if sh.has_text_frame and sh.text == label]
        assert button.click_action.hyperlink.address == f'{COLAB}#scrollTo={anchor}'
    print('31–41쪽 본문·노트와 Colab 바로가기 11개 검증 완료')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('notebook', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve():
        parser.error('Use distinct input and output paths.')
    sync(args.source, args.notebook, args.output)
