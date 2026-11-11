"""Explain the applied 4NF example on slide 27 of the 11-2 deck.

Usage: python slide27_4nf_applied.py <source.pptx> <output.pptx>
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
from pptx.util import Inches, Pt

SLIDE_INDEX = 26
REL_ID = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
ACTUAL_EXPERIENCE = """SELECT DISTINCT employee_id FROM assignments
WHERE project_code = 'PA' AND skill_code = 'DBA'
ORDER BY employee_id;"""


def find_shape(slide, prefix):
    matches = [s for s in slide.shapes if s.has_text_frame and s.text.startswith(prefix)]
    if len(matches) != 1:
        raise ValueError(f'Expected one slide 27 shape starting with {prefix!r}.')
    return matches[0]


def set_text(shape, value, *, size=None):
    run = shape.text_frame.paragraphs[0].runs[0]
    run.text = value
    if size is not None:
        run.font.size = Pt(size)


def check_example(rows):
    # Populate separate lists for this demonstration from known usage records.
    with sqlite3.connect(':memory:') as connection:
        connection.execute('CREATE TABLE assignments (employee_id INTEGER, skill_code TEXT, project_code TEXT)')
        connection.executemany('INSERT INTO assignments VALUES (?, ?, ?)', rows)
        inferred = connection.execute("""
            WITH held_skills AS (SELECT DISTINCT employee_id, skill_code FROM assignments),
                 projects AS (SELECT DISTINCT employee_id, project_code FROM assignments)
            SELECT held_skills.employee_id FROM held_skills JOIN projects USING (employee_id)
            WHERE skill_code = 'DBA' AND project_code = 'PA' ORDER BY held_skills.employee_id
        """).fetchall()
        actual = connection.execute(ACTUAL_EXPERIENCE).fetchall()
    if inferred != [(10,), (20,)] or actual != [(20,)]:
        raise ValueError(f'Example has changed: inferred={inferred}, actual={actual}')


def related_part(archive, part, *, rel_id=None, suffix=None):
    directory, name = posixpath.split(part)
    rels = etree.fromstring(archive.read(posixpath.join(directory, '_rels', name + '.rels')))
    match, = [rel for rel in rels if (rel.get('Id') == rel_id if rel_id else rel.get('Type').endswith(suffix))]
    return posixpath.normpath(posixpath.join(directory, match.get('Target')))


def update(source, output):
    deck = Presentation(source)
    slide = deck.slides[SLIDE_INDEX]
    body = find_shape(slide, '4차 정규화의 응용 | 보유 기술과 실제 사용 기술')
    text = (
        '4차 정규화 응용 | PA 프로젝트의 DBA 경험자 찾기',
        '문제 | DBA 보유와 PA 참여만 보고 고르면, 사원 10도 경험자로 분류된다.',
        '개선 | 보유기술은 따로 저장하고, 지원내역에는 프로젝트에서 실제 쓴 기술만 기록한다.',
        '조회 | 지원내역에서 프로젝트 PA와 기술 DBA를 함께 조건으로 검색한다.',
    )
    for paragraph, line in zip(body.text_frame.paragraphs, text, strict=True):
        paragraph.runs[0].text = line

    caption = find_shape(slide, '지원내역 표 · 실제 사용 조합')
    set_text(caption, '지원내역 · 프로젝트별 실제 사용 기록')
    footer = find_shape(slide, '보유기술과 지원내역은 각각 기록한다.')
    footer.left = Inches(0.52)
    footer.width = Inches(7.20)
    set_text(footer, '보유기술 변경은 별도 표에서 관리  ·  FK: Foreign Key (외래키)', size=12)
    result = slide.shapes.add_textbox(Inches(7.03), Inches(6.79), Inches(5.6), Inches(0.40))
    run = result.text_frame.paragraphs[0].add_run()
    run.text = '결과  |  PA의 DBA 경험이 확인된 사람은 사원 20'
    run.font.name = '맑은 고딕'
    run.font.bold = True
    run.font.size = Pt(16)
    run.font.color.rgb = RGBColor.from_string('155C4E')

    table, = [shape.table for shape in slide.shapes if shape.has_table]
    records = []
    highlights = {('10', 'MODELING', 'PA'): 'FFF0B4', ('20', 'DBA', 'PA'): 'CDEFE4'}
    for row in list(table.rows)[1:]:
        values = tuple(cell.text for cell in row.cells)
        records.append(values)
        if values in highlights:
            for cell in row.cells:
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor.from_string(highlights[values])
    check_example(records)

    notes = slide.notes_slide.notes_text_frame
    if notes is None or not notes.text.startswith('【슬라이드 핵심】'):
        raise ValueError('Review the existing speaker notes before applying this script.')
    notes.text = '''【슬라이드 핵심】
PA 프로젝트에서 실제로 DBA 기술을 사용한 사람을 찾는 수업용 예제다. 보유기술, 프로젝트 참여, 프로젝트별 기술 사용은 서로 다른 사실이다.
【강의 설명】
사원 10은 DBA 기술을 보유하고 PA에 참여했다. 두 목록을 사원번호만으로 조인해 PA·DBA 조합을 만들면 사원 10과 20이 모두 조회된다. 그러나 노란 행에서 보듯 이 표의 사원 10은 PA에서 MODELING을 사용했다. DBA는 SI와 OO에서 사용했다.
독립적으로 관리하는 보유기술은 보유기술(사원번호, 기술코드)에 저장한다. 실제 사용은 지원내역(사원번호, 프로젝트코드, 기술코드)에 한 행으로 기록한다. PA와 DBA를 동시에 만족하는 지원내역을 조회하면 초록색 행의 사원 20만 확인된다. 기술을 새로 취득하더라도 보유기술에만 등록하므로 허위 프로젝트 이력이 추가되지 않는다.
【연결】
25~26쪽의 제4정규형 분리는 독립 목록의 중복을 줄인다. 이 페이지의 실제 사용 기록은 세 값이 함께 하나의 사실을 이루므로 세 값의 관계를 유지한다. 28~30쪽에서 두 열씩 분해했다가 조인할 때 원본에 없던 행이 생기는지 확인한다.
검증용 SQL (영문 테이블·열 이름):\n''' + ACTUAL_EXPERIENCE + '''
【출처】
11-2 정규화 교안 25~30쪽 및 27쪽의 기존 지원내역 데이터. 두 조회 결과를 SQLite에서 검증.'''

    with ZipFile(source) as archive, ZipFile(output, 'w') as result_zip:
        presentation = 'ppt/presentation.xml'
        order = etree.fromstring(archive.read(presentation)).xpath('//*[local-name()="sldId"]')
        part = related_part(archive, presentation, rel_id=order[SLIDE_INDEX].get(REL_ID))
        notes_part = related_part(archive, part, suffix='/notesSlide')
        updates = {part: slide._element, notes_part: slide.notes_slide._element}
        for entry in archive.infolist():
            xml = updates.get(entry.filename)
            payload = (etree.tostring(xml, encoding='UTF-8', xml_declaration=True, standalone=True)
                       if xml is not None else archive.read(entry))
            result_zip.writestr(entry, payload)

    with ZipFile(source) as archive, ZipFile(output) as result_zip:
        assert result_zip.testzip() is None
        assert {name for name in archive.namelist() if archive.read(name) != result_zip.read(name)} == set(updates)
    verified = Presentation(output)
    assert len(verified.slides) == len(deck.slides)
    find_shape(verified.slides[SLIDE_INDEX], '결과  |  PA의 DBA 경험')
    print('27쪽·발표자 노트 반영 및 조회 결과 검증 완료')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve():
        parser.error('Use distinct input and output paths.')
    update(args.source, args.output)
