"""Update slide 24 and its notes in the 11-2 normalization deck.

Usage: python slide24_4nf_anomalies.py <source.pptx> <output.pptx>
Dependencies: python-pptx, lxml.
"""
import argparse
import posixpath
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

SLIDE_INDEX = 23
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
                                  *(Inches(v) for v in (6.02, y, 6.26, 1.09)))
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor.from_string(fill)
    shape.line.fill.background()
    frame = shape.text_frame
    frame.word_wrap = True
    frame.margin_left = Inches(0.20)
    frame.margin_right = Inches(0.20)
    frame.margin_top = Inches(0.07)
    add_text(frame, (title, action, result), size=14, heading_size=17)


def add_example_table(slide):
    text_box(slide, 1.05, 2.22, 4.55, 0.42, ('사원 10의 전체 조합 · 6행',), heading_size=18)
    rows = [('사원번호', '기술코드', '프로젝트코드')]
    rows += [('10', tech, project) for project in ('SI', 'OO', 'PA') for tech in ('Modeling', 'DBA')]
    shape = slide.shapes.add_table(len(rows), len(rows[0]), *(Inches(v) for v in (1.05, 2.69, 4.52, 3.12)))
    table = shape.table
    for col, width in zip(table.columns, (1.20, 1.50, 1.82)):
        col.width = Inches(width)
    for row_index, row in enumerate(rows):
        for col_index, value in enumerate(row):
            cell = table.cell(row_index, col_index)
            fill = NAVY if row_index == 0 else {'SI': YELLOW, 'PA': RED}.get(row[2], WHITE)
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor.from_string(fill)
            cell.margin_left = cell.margin_right = Inches(0.04)
            cell.margin_top = cell.margin_bottom = Inches(0.02)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            add_text(cell.text_frame, (value,), size=15, heading_size=15 if row_index == 0 else None,
                     color=WHITE if row_index == 0 else INK)
            cell.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER


def related_part(archive, part, *, rel_id=None, suffix=None):
    directory, name = posixpath.split(part)
    rels = etree.fromstring(archive.read(posixpath.join(directory, '_rels', name + '.rels')))
    match, = [rel for rel in rels if (rel.get('Id') == rel_id if rel_id else rel.get('Type').endswith(suffix))]
    return posixpath.normpath(posixpath.join(directory, match.get('Target')))


def update(source, output):
    deck = Presentation(source)
    slide = deck.slides[SLIDE_INDEX]
    bodies = [shape for shape in slide.shapes if shape.has_text_frame
              and all(term in shape.text for term in ('입력 이상', '수정 이상', '삭제 이상'))]
    if len(bodies) != 1:
        raise ValueError('Expected the original three-anomaly explanation on slide 24.')
    body = bodies[0]
    heading, *old_paragraphs = body.text_frame.paragraphs
    heading.runs[0].text = '4차 정규화 | 한 표에 두 목록을 담을 때 생기는 이상'
    heading.runs[0].font.size = Pt(23)
    for paragraph in old_paragraphs:
        paragraph._p.getparent().remove(paragraph._p)
    body.height = Inches(0.59)

    add_example_table(slide)
    add_card(slide, 2.31, BLUE, '입력 이상', '새 프로젝트 P04 한 건을 등록',
             '→ Modeling·DBA와 조합해 2행을 입력')
    add_card(slide, 3.52, YELLOW, '수정 이상', '프로젝트 코드 SI를 SI2로 정정',
             '→ 노란색 2행을 모두 수정해야 일치')
    add_card(slide, 4.73, RED, '삭제 이상', 'PA가 마지막 프로젝트인 상태에서 PA를 삭제',
             '→ 빨간색 2행과 함께 보유기술 기록도 사라짐')
    text_box(slide, 1.05, 6.10, 11.1, 0.50, (
        '보유기술과 지원프로젝트를 두 표로 나누면 각 목록을 독립적으로 변경할 수 있습니다.',
    ), heading_size=17, color=NAVY)

    notes = slide.notes_slide.notes_text_frame
    if notes is None or notes.text.strip():
        raise ValueError('Review the existing speaker notes before replacing them.')
    notes.text = '''【슬라이드 핵심】
독립적인 두 목록을 한 표에 넣으면 하나의 업무 사실을 입력·수정·삭제할 때 관계없는 행까지 영향을 받는다.
【강의 설명】
22쪽과 같은 사원 10의 기술 2개와 프로젝트 3개를 모든 조합으로 펼쳐 6행을 보여준다. 파란 입력 카드는 새 프로젝트 P04를 추가하는 상황이다. 프로젝트 참여는 한 건이지만 기술별 2행을 추가해야 한다. 노란 수정 카드는 SI 코드의 정정이다. 두 행 중 하나만 바꾸면 SI와 SI2가 동시에 남는다.
빨간 삭제 카드는 SI와 OO가 이미 제거되어 PA만 남은 시점을 가정한다. PA에 해당하는 마지막 두 행을 삭제하면 Modeling과 DBA를 보유한다는 정보도 이 표에서 사라진다. 반대로 마지막 기술만 남았을 때 그 기술을 삭제하면 프로젝트 기록이 사라지는 것도 같은 구조의 문제다.
【연결】
25~26쪽의 분리 설계에서는 보유기술과 지원프로젝트를 독립적으로 변경한다. 27쪽의 프로젝트별 실제 기술 사용은 세 값이 함께 하나의 사실을 이룬다.
【출처】
11-2 정규화 교안 22~27쪽 사원·기술·프로젝트 예제 재구성.'''

    with ZipFile(source) as archive, ZipFile(output, 'w') as result:
        presentation = 'ppt/presentation.xml'
        order = etree.fromstring(archive.read(presentation)).xpath('//*[local-name()="sldId"]')
        part = related_part(archive, presentation, rel_id=order[SLIDE_INDEX].get(REL_ID))
        notes_part = related_part(archive, part, suffix='/notesSlide')
        updates = {part: slide._element, notes_part: slide.notes_slide._element}
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
    table, = [shape.table for shape in verified.slides[SLIDE_INDEX].shapes if shape.has_table]
    assert len(table.rows) == 7
    print('24쪽과 발표자 노트 반영 완료')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve():
        parser.error('Use distinct input and output paths.')
    update(args.source, args.output)
