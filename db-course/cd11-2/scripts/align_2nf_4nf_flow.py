"""Align the 2NF and 4NF sections of the CD11-2 normalization deck.

Usage: python align_2nf_4nf_flow.py <source.pptx> <output.pptx>
Dependencies: python-pptx, lxml.
"""
import argparse
import posixpath
import sqlite3
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

REL_ID = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
NAVY = '0F3154'
INK = '172B45'
BLUE = 'E2EFFA'
YELLOW = 'FFF0BF'
RED = 'FCE5E4'
WHITE = 'FFFFFF'


def add_text(frame, lines, *, size=16, heading_size=None, color=INK):
    for i, line in enumerate(lines):
        paragraph = frame.paragraphs[0] if i == 0 else frame.add_paragraph()
        paragraph.space_after = Pt(4 if i == 0 and heading_size else 0)
        run = paragraph.add_run()
        run.text = line
        run.font.name = '맑은 고딕'
        run.font.size = Pt(heading_size if i == 0 and heading_size else size)
        run.font.bold = i == 0 and heading_size is not None
        run.font.color.rgb = RGBColor.from_string(color)


def text_box(slide, x, y, width, height, lines, **text_style):
    frame = slide.shapes.add_textbox(*(Inches(v) for v in (x, y, width, height))).text_frame
    frame.word_wrap = True
    add_text(frame, lines, **text_style)


def add_card(slide, y, fill, title, action, result):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                  *(Inches(v) for v in (6.57, y, 5.70, 1.07)))
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor.from_string(fill)
    shape.line.fill.background()
    frame = shape.text_frame
    frame.word_wrap = True
    frame.margin_left = Inches(0.20)
    frame.margin_right = Inches(0.20)
    frame.margin_top = Inches(0.07)
    add_text(frame, (title, action, result), size=13, heading_size=16)


def add_table(slide, y, headers, rows, widths, *, height, color_key=None, font=14):
    shape = slide.shapes.add_table(
        len(rows) + 1, len(headers), Inches(1.05), Inches(y), Inches(sum(widths)), Inches(height)
    )
    table = shape.table
    for col, width in zip(table.columns, widths, strict=True):
        col.width = Inches(width)
    for row_index, row in enumerate([headers, *rows]):
        for col_index, value in enumerate(row):
            cell = table.cell(row_index, col_index)
            fill = NAVY if row_index == 0 else (color_key or {}).get(row[1], WHITE)
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor.from_string(fill)
            cell.margin_left = cell.margin_right = Inches(0.04)
            cell.margin_top = cell.margin_bottom = Inches(0.02)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            add_text(cell.text_frame, (str(value),), size=font,
                     heading_size=font if row_index == 0 else None,
                     color=WHITE if row_index == 0 else INK)
            cell.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER


def title_text(shape, text):
    paragraph = shape.text_frame.paragraphs[0]
    first, *other = paragraph.runs
    first.text = text
    for run in other:
        run._r.getparent().remove(run._r)


def find(slide, prefix):
    matches = [s for s in slide.shapes if s.has_text_frame and s.text.startswith(prefix)]
    if len(matches) != 1:
        raise ValueError(f'Expected one shape starting with {prefix!r}')
    return matches[0]


def read_table(table):
    return [tuple(cell.text.strip() for cell in row.cells) for row in table.rows]


def order_example(slide):
    tables = [read_table(sh.table) for sh in slide.shapes if sh.has_table]
    detail, = [rows for rows in tables if len(rows[0]) == 5]
    orders, = [rows for rows in tables if len(rows[0]) == 6]
    return detail[1:], orders


def verify_decompositions(detail, products, items, holds, projects, combinations):
    with sqlite3.connect(':memory:') as db:
        db.executescript("""
            CREATE TABLE products (product TEXT PRIMARY KEY, name TEXT, stock TEXT);
            CREATE TABLE items (order_id TEXT, product TEXT REFERENCES products(product), qty TEXT,
                                PRIMARY KEY (order_id, product));
            CREATE TABLE holds (employee TEXT, skill TEXT, PRIMARY KEY (employee, skill));
            CREATE TABLE projects (employee TEXT, project TEXT, PRIMARY KEY (employee, project));
        """)
        db.executemany('INSERT INTO products VALUES (?, ?, ?)', products)
        db.executemany('INSERT INTO items VALUES (?, ?, ?)', items)
        restored = db.execute('SELECT order_id, product, name, stock, qty FROM items JOIN products USING(product)').fetchall()
        db.executemany('INSERT INTO holds VALUES (?, ?)', holds)
        db.executemany('INSERT INTO projects VALUES (?, ?)', projects)
        recombined = db.execute('SELECT employee, skill, project FROM holds JOIN projects USING(employee)').fetchall()
    assert len(detail) == 6 and len(products) == 3 and sorted(restored) == sorted(detail)
    assert len(combinations) == 6 and sorted(recombined) == sorted(combinations)


def table_title(slide, y, text):
    text_box(slide, 1.05, y, 5.43, 0.33, (text,), heading_size=15, color=NAVY)


def format_2nf(slide, page, detail, products, items, orders):
    header = find(slide, '정규화의 이해')
    body, = [sh for sh in slide.shapes if sh.is_placeholder and sh.has_text_frame and sh.text.startswith('2차 정규화')]
    for shape in list(slide.shapes):
        if shape.shape_id not in (header.shape_id, body.shape_id):
            shape._element.getparent().remove(shape._element)
    title_text(header, '정규화 이해')
    topics = {
        13: '2차 정규화 ① | 문제 찾기 · 제품 정보가 왜 반복될까?',
        14: '2차 정규화 ② | 입력·수정·삭제 이상',
        15: '2차 정규화 ③ | 제품 분리·검증',
    }
    title_text(body, topics[page])
    for paragraph in list(body.text_frame.paragraphs)[1:]:
        paragraph._p.getparent().remove(paragraph._p)
    body.text_frame.paragraphs[0].runs[0].font.size = Pt(23)
    body.height = Inches(0.6)

    if page in (13, 14):
        table_title(slide, 2.22, '분리 전 주문목록 · 6행')
        add_table(slide, 2.63, ('주문번호', '제품번호', '제품명', '재고', '주문수량'),
                  detail, (1.10, 1.0, 1.13, 0.9, 1.18), height=3.12,
                  color_key={'1007': YELLOW, '1201': RED} if page == 14 else {'1007': YELLOW})
    else:
        table_title(slide, 2.12, '제품 · 3행  |  PK 제품번호')
        add_table(slide, 2.48, ('제품번호', '제품명', '재고'), products,
                  (1.70, 1.91, 1.70), height=1.16, font=13)
        table_title(slide, 3.72, '주문목록 · 6행  |  PK (주문번호, 제품번호)')
        add_table(slide, 4.08, ('주문번호', '제품번호', '주문수량'), items,
                  (1.70, 1.91, 1.70), height=1.97, font=13)

    cases = {
        13: (
            ('복합 기본키', '한 주문의 여러 제품을 구분합니다.', '(주문번호, 제품번호)로 한 행을 식별'),
            ('부분 종속', '제품번호 1007만 알면 제품명과 재고를 알 수 있습니다.', '→ 마우스·9,702가 여러 주문에 반복'),
            ('전체 키에 종속', '1007의 주문수량은 주문마다 다릅니다.', '→ 수량에는 주문번호와 제품번호가 모두 필요'),
        ),
        14: (
            ('입력 이상', '아직 주문이 없는 새 제품 1300을 등록', '→ 주문번호가 없으면 주문목록에 저장할 수 없음'),
            ('수정 이상', '마우스(1007) 재고를 9,702 → 15,000으로 변경', '→ 노란색 3행을 모두 수정해야 일치'),
            ('삭제 이상', '스피커(1201)의 유일한 주문 CB231을 취소', '→ 빨간색 주문행과 함께 스피커 정보도 사라짐'),
        ),
        15: (
            ('입력 해결', '새 제품 1300을 등록', '→ 주문 없이 제품 표에 1행 추가'),
            ('수정 해결', '마우스(1007) 재고를 15,000으로 변경', '→ 제품 표 1행만 수정'),
            ('삭제 해결', 'CB231의 스피커 주문행을 삭제', '→ 제품 표의 스피커(1201)는 그대로 유지'),
        ),
    }
    fills = (BLUE, YELLOW, BLUE) if page == 13 else (BLUE, YELLOW, RED)
    for y, fill, card in zip((2.31, 3.52, 4.73), fills, cases[page], strict=True):
        add_card(slide, y, fill, *card)
    conclusion = {
        13: '부분 종속 · 복합키의 일부인 제품번호만으로 제품명과 재고가 결정됩니다.',
        14: '제품 정보와 주문 사실을 한 표에 담아 제품을 독립적으로 관리하기 어렵습니다.',
        15: '제품번호로 제품과 주문목록을 JOIN하면, 변경 전 주문목록 6행을 복원합니다.',
    }
    text_box(slide, 1.05, 6.15, 11.15, 0.37, (conclusion[page],), heading_size=16, color=NAVY)
    if page == 15:
        foot = ('주문 표 유지 · 주문번호 PK, 주문일자와 고객 관련 열. 주문목록의 주문번호·제품번호는 각각 FK입니다.',
                '※ PK: Primary Key (기본키) · FK: Foreign Key (외래키) · JOIN: 키로 두 표의 행 연결')
        text_box(slide, 1.05, 6.57, 11.35, 0.57, foot, size=11)

    notes = slide.notes_slide.notes_text_frame
    if notes is None or notes.text.strip():
        raise ValueError(f'Review any existing speaker notes on page {page}.')
    note_text = {
        13: (
            '주문목록의 복합 기본키는 (주문번호, 제품번호)입니다. 제품번호만으로 제품명·재고를 결정하는 부분 종속이 있습니다.',
            '1007의 제품명·재고는 AB345, CA210, CB230에 반복되지만 주문수량은 300, 120, 690으로 다릅니다. 주문일자와 고객 관련 열은 이미 별도의 주문 표에 있습니다. 제2정규형에서는 비주요 속성이 후보키의 진부분집합에 함수적으로 종속되는 경우를 제거합니다.',
            '14쪽에서 반복된 값으로 인해 생기는 세 가지 이상을 확인합니다.',
        ),
        14: (
            '제품 등록·재고 수정·주문 삭제를 원본 주문목록에서 각각 시도합니다.',
            '주문 없이 제품 1300을 등록할 자리가 없습니다. 1007 재고를 바꾸려면 노란색 3행을 바꿔야 하며 하나만 수정하면 값이 불일치합니다. CB231의 유일한 1201 행을 지우면 스피커의 제품명과 재고도 사라집니다.',
            '15쪽에서 같은 세 동작을 분리된 표에서 다시 확인합니다.',
        ),
        15: (
            '제품명·재고는 제품 표, 주문수량은 주문목록에 둡니다. 주문 표는 별도로 유지됩니다.',
            '제품은 제품번호로 유일하게 식별해 3행, 주문목록은 (주문번호, 제품번호)로 식별해 6행입니다. 제품번호로 연결하면 변경 전 주문목록 6행이 모두 복원됩니다. 기존 주문 표의 예제 행은 다음과 같습니다.\n'
            + '\n'.join(' | '.join(value.replace('\n', ' ') for value in row) for row in orders),
            '16쪽부터는 유지된 주문 표 안에서 고객번호가 결정하는 속성을 찾아 3차 정규화로 분리합니다.',
        ),
    }
    core, explanation, link = note_text[page]
    notes.text = '\n'.join(('【슬라이드 핵심】', core, '【강의 설명】', explanation,
                             '【연결】', link, '【출처】', '11-2 정규화 교안 기존 13~15쪽 예제.'))


def format_4nf(slide, page):
    titles = {
        22: '4차 정규화 ① | 문제 찾기 · 독립된 두 목록의 조합',
        23: '4차 정규화 ① | 문제 찾기 · 임의 짝과 전체 조합',
        24: '4차 정규화 ② | 입력·수정·삭제 이상',
        25: '4차 정규화 ③ | 분리·검증 · 보유기술과 참여 프로젝트',
        26: '4차 정규화 ③ | 보충 · 분리한 표의 키 연결',
        27: '4차 정규화 ④ | 응용 · 사원 10의 DBA 사용 이력',
    }
    prefix = '4차 정규화'
    title_text(find(slide, prefix), titles[page])
    if page == 22:
        title_text(find(slide, '사원번호가 두 목록을'), '다치 종속 · 한 사원의 기술 목록과 프로젝트 목록은 서로 독립적으로 관리합니다.')
    if page == 26:
        shape = find(slide, '27쪽으로 연결')
        run = shape.text_frame.paragraphs[1].runs[0]
        run.text = '사원 10이 PA에서 DBA를 사용했는지는 27쪽의 실제 지원내역에서 확인합니다.'


def related_part(archive, part, *, rel_id=None, suffix=None):
    directory, name = posixpath.split(part)
    rels = etree.fromstring(archive.read(posixpath.join(directory, '_rels', name + '.rels')))
    match, = [rel for rel in rels if (rel.get('Id') == rel_id if rel_id else rel.get('Type').endswith(suffix))]
    return posixpath.normpath(posixpath.join(directory, match.get('Target')))


def update(source, output):
    deck = Presentation(source)
    detail, orders = order_example(deck.slides[12])
    products = list(dict.fromkeys((product, name, stock) for _, product, name, stock, _ in detail))
    items = [(order, product, qty) for order, product, _, _, qty in detail]
    combined, = [read_table(sh.table)[1:] for sh in deck.slides[23].shapes if sh.has_table]
    holds, projects = [read_table(sh.table)[1:] for sh in deck.slides[24].shapes if sh.has_table]
    verify_decompositions(detail, products, items, holds, projects, combined)
    pages = (13, 14, 15, 22, 23, 24, 25, 26, 27)

    with ZipFile(source) as archive, ZipFile(output, 'w') as result:
        presentation = 'ppt/presentation.xml'
        order = etree.fromstring(archive.read(presentation)).xpath('//*[local-name()="sldId"]')
        updates = {}
        for page in pages:
            slide = deck.slides[page - 1]
            part = related_part(archive, presentation, rel_id=order[page - 1].get(REL_ID))
            if page <= 15:
                format_2nf(slide, page, detail, products, items, orders)
                notes_part = related_part(archive, part, suffix='/notesSlide')
                updates[notes_part] = slide.notes_slide._element
            else:
                format_4nf(slide, page)
            updates[part] = slide._element
        for entry in archive.infolist():
            xml = updates.get(entry.filename)
            payload = (etree.tostring(xml, encoding='UTF-8', xml_declaration=True, standalone=True)
                       if xml is not None else archive.read(entry))
            result.writestr(entry, payload)

    with ZipFile(source) as archive, ZipFile(output) as result:
        assert result.testzip() is None
        assert {name for name in archive.namelist() if archive.read(name) != result.read(name)} == set(updates)
    verified = Presentation(output)
    assert len(verified.slides) == len(deck.slides)
    assert verified.slides[25]._element.get('show') == '0'
    assert [len(sh.table.rows) for sh in verified.slides[14].shapes if sh.has_table] == [4, 7]
    print('13–15쪽·22–27쪽 수정 및 두 예제의 JOIN 6행 복원 검증 완료')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve():
        parser.error('Use distinct input and output paths.')
    update(args.source, args.output)
