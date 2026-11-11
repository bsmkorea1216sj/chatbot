"""Update only slide 22 and its notes in the 11-2 normalization deck.

Usage: python slide22_4nf_intro.py <source.pptx> <output.pptx>
Dependencies: python-pptx, lxml.
"""
import argparse
import posixpath
from copy import deepcopy
from pathlib import Path
from zipfile import ZipFile

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

SLIDE_INDEX = 21
OFFICE_REL_ID = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'


def find_shape(slide, prefix):
    matches = [
        shape for shape in slide.shapes
        if shape.has_text_frame and shape.text.startswith(prefix)
    ]
    if len(matches) != 1:
        raise ValueError(f'Expected one shape starting with {prefix!r}; found {len(matches)}')
    return matches[0]


def copy_card(slide, original, left, top, width, height, lines):
    card_xml = deepcopy(original._element)
    properties, = card_xml.xpath('./p:nvSpPr/p:cNvPr')
    shape_id = max(int(node.get('id')) for node in slide._element.xpath('.//p:cNvPr')) + 1
    properties.set('id', str(shape_id))
    properties.set('name', f'4NF example {shape_id}')
    slide.shapes._spTree.insert_element_before(card_xml, 'p:extLst')
    card = slide.shapes[-1]
    card.left, card.top, card.width, card.height = (Inches(value) for value in (left, top, width, height))
    for i, paragraph in enumerate(card.text_frame.paragraphs):
        if i >= len(lines):
            paragraph._p.getparent().remove(paragraph._p)
            continue
        paragraph.runs[0].text = lines[i]
    return card


def resolve_part(archive, part, *, rel_id=None, type_suffix=None):
    directory, name = posixpath.split(part)
    rels = etree.fromstring(archive.read(posixpath.join(directory, '_rels', name + '.rels')))
    match, = [
        rel for rel in rels
        if (rel.get('Id') == rel_id if rel_id else rel.get('Type').endswith(type_suffix))
    ]
    return posixpath.normpath(posixpath.join(directory, match.get('Target')))


def update(source, output):
    deck = Presentation(source)
    slide = deck.slides[SLIDE_INDEX]
    body = find_shape(slide, '4차 정규화\n')
    heading, description, blank, example = body.text_frame.paragraphs
    heading.runs[0].text = '4차 정규화 | 독립적인 두 목록을 나누는 이유'
    heading.runs[0].font.size = Pt(24)
    description.runs[0].text = '한 사원에게 '
    description.runs[1].text = '보유기술과 지원 프로젝트가 각각 여러 개'
    description.runs[2].text = ' 있고 두 목록은 서로 독립적입니다.'
    for run in description.runs:
        run.font.size = Pt(19)
    example.runs[0].text = '사원 10  |  보유기술 2개: Modeling, DBA  ·  지원 프로젝트 3개: SI, OO, PA'
    example.runs[0].font.size = Pt(18)
    blank._p.getparent().remove(blank._p)
    example.space_before = Pt(10)
    body.height = Inches(1.65)

    original_card = find_shape(deck.slides[24], '분리 전 · 사원·기술·프로젝트')
    copy_card(slide, original_card, 1.05, 3.12, 5.43, 2.12, (
        '한 표에 저장하면 · 6행',
        'Modeling × SI·OO·PA → 3행',
        'DBA × SI·OO·PA → 3행',
        '기술 하나를 추가할 때 프로젝트 수만큼 반복',
    ))
    copy_card(slide, original_card, 6.75, 3.12, 5.45, 2.12, (
        '두 표로 분리하면 · 2행 + 3행',
        '보유기술(사원번호, 기술코드) → 2행',
        '지원프로젝트(사원번호, 프로젝트코드) → 3행',
        '기술 하나를 추가할 때 보유기술에 1행만 추가',
    ))
    takeaway = find_shape(deck.slides[24], '기술을 추가할 때는')
    lower = copy_card(slide, takeaway, 1.05, 5.57, 11.15, 0.65, (
        '사원번호가 두 목록을 각각 결정하는 관계를 다치 종속이라고 합니다.',
    ))
    lower.text_frame.paragraphs[0].runs[0].font.size = Pt(17)
    foot = slide.shapes.add_textbox(Inches(1.05), Inches(6.47), Inches(10.8), Inches(0.34))
    run = foot.text_frame.paragraphs[0].add_run()
    run.text = '※ 4NF: Fourth Normal Form (제4정규형) · MVD: Multivalued Dependency (다치 종속)'
    run.font.size = Pt(12)
    run.font.color.rgb = RGBColor.from_string('27385B')

    notes = slide.notes_slide.notes_text_frame
    if notes is None:
        raise ValueError('Expected a speaker notes placeholder')
    if notes.text.strip():
        raise ValueError('Slide 22 now contains notes. Review them before applying this script.')
    notes.text = '''【슬라이드 핵심】
같은 사원에 대해 독립적으로 여러 값을 갖는 보유기술과 지원 프로젝트를 한 표에 넣으면 모든 조합을 반복하게 된다. 제4정규형은 이런 비자명한 다치 종속으로 인한 중복을 다룬다.
【강의 설명】
사원 10의 보유기술은 Modeling과 DBA이고, 지원 프로젝트는 SI, OO, PA라고 하자. 두 목록이 서로 독립이면 (10, Modeling, SI)와 (10, DBA, OO)가 있을 때 기술과 프로젝트를 바꿔 조합한 (10, Modeling, OO), (10, DBA, SI)도 같은 두 목록에서 유도된다. 한 표에 완전한 조합을 저장하면 2 × 3 = 6행이다. 각 조합은 프로젝트에서 해당 기술을 실제로 사용했다는 뜻을 갖지 않는다.
보유기술과 지원프로젝트를 따로 저장하면 기술 추가는 보유기술 한 행만 필요하다. 사원번호 ↠ 기술코드와 사원번호 ↠ 프로젝트코드로 이 예의 다치 종속을 나타낸다. 제4정규형은 모든 비자명한 다치 종속에서 결정자가 슈퍼키일 것을 요구한다.
【연결】
23~24쪽에서는 독립 목록을 한 표에 섞을 때 발생하는 문제를, 25~26쪽에서는 분리와 키 연결을 확인한다. 27쪽에서는 실제 프로젝트 사용 기술처럼 세 값이 함께 의미를 갖는 경우를 비교한다.
【출처】
11-2 정규화 교안 22~27쪽의 사원·기술·프로젝트 예제 재구성.'''

    with ZipFile(source) as archive, ZipFile(output, 'w') as result:
        presentation = 'ppt/presentation.xml'
        slide_ids = etree.fromstring(archive.read(presentation)).xpath('//*[local-name()="sldId"]')
        part = resolve_part(archive, presentation, rel_id=slide_ids[SLIDE_INDEX].get(OFFICE_REL_ID))
        notes_part = resolve_part(archive, part, type_suffix='/notesSlide')
        updated = {part: slide._element, notes_part: slide.notes_slide._element}
        for entry in archive.infolist():
            xml = updated.get(entry.filename)
            data = (etree.tostring(xml, encoding='UTF-8', xml_declaration=True, standalone=True)
                    if xml is not None else archive.read(entry))
            result.writestr(entry, data)

    with ZipFile(source) as archive, ZipFile(output) as result:
        assert result.testzip() is None
        assert {name for name in archive.namelist() if archive.read(name) != result.read(name)} == set(updated)
    verified = Presentation(output)
    assert len(verified.slides) == len(deck.slides)
    find_shape(verified.slides[SLIDE_INDEX], '두 표로 분리하면')
    print('22쪽과 발표자 노트 반영 완료')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve():
        parser.error('Use distinct input and output paths.')
    update(args.source, args.output)
