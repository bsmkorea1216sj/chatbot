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
ALL_DBA_EXPERIENCE = """SELECT DISTINCT employee_id FROM assignments
WHERE skill_code = 'DBA'
ORDER BY employee_id;"""
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
        any_project = connection.execute(ALL_DBA_EXPERIENCE).fetchall()
        actual = connection.execute(ACTUAL_EXPERIENCE).fetchall()
    if inferred != [(10,), (20,)] or any_project != [(10,), (20,)] or actual != [(20,)]:
        raise ValueError(f'Example has changed: inferred={inferred}, any_project={any_project}, PA={actual}')


def related_part(archive, part, *, rel_id=None, suffix=None):
    directory, name = posixpath.split(part)
    rels = etree.fromstring(archive.read(posixpath.join(directory, '_rels', name + '.rels')))
    match, = [rel for rel in rels if (rel.get('Id') == rel_id if rel_id else rel.get('Type').endswith(suffix))]
    return posixpath.normpath(posixpath.join(directory, match.get('Target')))


def update(source, output):
    deck = Presentation(source)
    slide = deck.slides[SLIDE_INDEX]
    body = find_shape(slide, '4차 정규화 응용 | PA 프로젝트의 DBA 경험자 찾기')
    text = (
        '4차 정규화 응용 | 사원 10의 DBA가 두 번 나오는 이유',
        '실제 이력 | 사원 10은 SI와 OO에서 각각 DBA를 사용했다. 두 행 모두 유효하다.',
        '저장 구조 | 보유기술에는 (10, DBA) 한 번, 지원내역에는 SI·OO의 DBA 이력을 각각 저장한다.',
        'PA에서의 사용 | 사원 10은 MODELING을 썼다. PA에서 DBA를 쓴 기록은 사원 20에게 있다.',
    )
    for paragraph, line in zip(body.text_frame.paragraphs, text, strict=True):
        first, *remaining = paragraph.runs
        first.text = line
        for run in remaining:
            run._r.getparent().remove(run._r)

    footer = find_shape(slide, '보유기술 변경은 별도 표에서 관리')
    set_text(footer, 'DBA 경험자(프로젝트 무관)  |  사원 10, 20', size=16)
    result = find_shape(slide, '결과  |  PA의 DBA 경험')
    set_text(result, 'PA에서 DBA를 쓴 경험자  |  사원 20')
    glossary = slide.shapes.add_textbox(Inches(0.55), Inches(7.13), Inches(5.5), Inches(0.24))
    run = glossary.text_frame.paragraphs[0].add_run()
    run.text = '※ FK: Foreign Key (외래키)'
    run.font.name = '맑은 고딕'
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor.from_string('27385B')

    table, = [shape.table for shape in slide.shapes if shape.has_table]
    records = []
    highlights = {
        ('10', 'DBA', 'SI'): 'FFF0B4',
        ('10', 'DBA', 'OO'): 'FFF0B4',
        ('10', 'MODELING', 'PA'): 'E3EBF4',
        ('20', 'DBA', 'PA'): 'CDEFE4',
    }
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
    notes.text = (
        """【슬라이드 핵심】
사원 10이 DBA를 SI와 OO에서 각각 사용했다는 두 행은 서로 다른 사실이다. 보유기술과 프로젝트별 실제 사용 기록을 구분하면 질문에 맞는 답을 얻는다.
【강의 설명】
보유기술은 사원번호와 기술코드로 한 행을 식별하므로 (10, DBA)는 한 번 저장한다. 지원내역은 사원번호·프로젝트코드·기술코드로 식별하므로 (10, SI, DBA)와 (10, OO, DBA)는 모두 저장한다. 노란색은 이 두 사용 이력이다. 파란색 행은 사원 10이 PA에서 MODELING을 사용한 기록이고, 초록색은 사원 20이 PA에서 DBA를 사용한 기록이다.
DBA 사용 경험만 묻는다면 기술코드 DBA로 거르고 사원번호를 중복 없이 조회한다. 결과는 사원 10과 20이다. PA에서 DBA를 사용했는지 묻는다면 프로젝트 PA 조건을 함께 적용해 사원 20만 조회한다. 보유기술과 PA 참여를 사원번호로만 합치면 사원 10도 PA의 DBA 사용 경험자로 잘못 분류된다.
【연결】
25쪽에서는 독립 목록을 나누는 제4정규형을 적용했다. 여기서는 실제 사용을 뜻하는 세 값의 연결을 보존한다. 28~30쪽의 무손실 분해 실습에서 이 연결을 잃으면 어떤 행이 추가되는지 확인한다.
확인용 SQL (DBA 경험자 전체, PA의 DBA 경험자 순서)
"""
        + ALL_DBA_EXPERIENCE + '\n' + ACTUAL_EXPERIENCE
        + """
【출처】
11-2 정규화 교안 25~30쪽 및 27쪽의 기존 지원내역 데이터. 두 조회 결과를 SQLite에서 검증."""
    )

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
    find_shape(verified.slides[SLIDE_INDEX], 'PA에서 DBA를 쓴 경험자')
    print('27쪽·발표자 노트 반영 및 조회 결과 검증 완료')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve():
        parser.error('Use distinct input and output paths.')
    update(args.source, args.output)
