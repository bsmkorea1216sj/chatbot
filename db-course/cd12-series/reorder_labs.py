"""Move CD12 practice blocks after theory, preserving existing PPTX objects and notebook cells."""
import json
import re
import sys
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree as ET

root = Path(sys.argv[1])
output = root / 'sequenced'
output.mkdir(exist_ok=True)
blocks = {1: [31, 33, 34], 2: [29, 30, 17, 18, 31], 3: [56, 57, 58, 59]}
summary = {1: 35, 2: 27, 3: 54}
links = {1: 31, 2: 29, 3: 56}
cells = {
    1: ('1URPntHhY0jY96psj9cK0Khrzq3gLb8KX', ['shop-db-create','shop-tables','shop-verify','shop-webapp','shop-delete']),
    2: ('1bUdKHLpCey3gCNt-3Qyx-8SCy9QCZfTY', ['m-db-create','m-tables','m-assign1','m-transaction','m-crud','m-assign2','m-delete']),
    3: ('16zKCRFtxxvxd3m9DJeg2F73dIiQWhCVN', ['l-db-create','l-schema','l-integrity','l-assign1','l-fillfactor','l-index','l-partition','l-assign2','l-physical','l-delete']),
}
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
page_pattern = re.compile(r'(?<![\d.])\d+(?:\s*[~·]\s*\d+)*(?=쪽|페이지)')

def xml(e):
    return ET.tostring(e, encoding='UTF-8', xml_declaration=True, standalone=True)

def slide_no(path):
    return int(re.search(r'slide(\d+)\.xml$', path)[1])

def reorganize(part):
    with ZipFile(root / f'readback{part}.pptx') as source:
        parts = {name: source.read(name) for name in source.namelist()}
    presentation = ET.fromstring(parts['ppt/presentation.xml'])
    slide_list = presentation.find('{*}sldIdLst')
    rels = {e.get('Id'): e.get('Target') for e in ET.fromstring(parts['ppt/_rels/presentation.xml.rels'])}
    old_order = [slide_no(rels[next(v for k,v in e.attrib.items() if k.endswith('}id'))]) for e in slide_list]
    lookup = dict(zip(old_order, slide_list))
    order = [n for n in old_order if n not in blocks[part]]
    pivot = order.index(summary[part])
    order[pivot:pivot] = blocks[part]
    slide_list[:] = [lookup[n] for n in order]
    parts['ppt/presentation.xml'] = xml(presentation)
    pages = {old: order.index(n)+1 for old,n in enumerate(old_order,1)}
    new_guide_page = order.index(links[part])+1

    def remap(match):
        expression = match[0].replace(' ', '')
        groups = []
        for group in expression.split('·'):
            numbers = [int(x) for x in group.split('~')]
            if not all(n in pages for n in numbers):
                return match[0]
            groups.append('~'.join(str(pages[n]) for n in numbers))
        return '·'.join(groups)

    for n in order:
        slide = f'ppt/slides/slide{n}.xml'
        relations_path = f'ppt/slides/_rels/slide{n}.xml.rels'
        relationships = ET.fromstring(parts[relations_path])
        linked = {e.get('Id') for e in relationships if '://colab.research.google.com/' in e.get('Target','')}
        content = ET.fromstring(parts[slide])
        theory = n not in blocks[part]
        if theory:
            for shape in content.findall('.//{*}sp'):
                ids = {v for h in shape.findall('.//{*}hlinkClick') for k,v in h.attrib.items() if k.endswith('}id')}
                if ids & linked:
                    shape.getparent().remove(shape)
            for relationship in list(relationships):
                if relationship.get('Id') in linked:
                    relationships.remove(relationship)
            parts[relations_path] = xml(relationships)
        for t in content.findall('.//{*}t'):
            if t.text is None:
                continue
            t.text = page_pattern.sub(remap,t.text)
            if n == links[part] and re.fullmatch(r'\d+(?:[~·]\d+)*', t.text):
                t.text = remap(re.match(r'.+',t.text))
            t.text = t.text.replace('🔎퀴즈 ① 정답', '핵심 확인').replace('🔎퀴즈 ② 정답', '핵심 확인').replace('🔎퀴즈 ③ 정답', '핵심 확인') if theory else t.text
            if theory:
                t.text = t.text.replace('AWS RDS PostgreSQL에 표 5개를 만들고 Colab에서 웹앱을 엽니다.',
                                        'PostgreSQL 테이블 5개가 상품 주문과 배송 조회 화면을 뒷받침합니다.')
                t.text = t.text.replace('실습 표 5개 ERD · Colab 2. 표 만들기 셀이 이대로 생성',
                                        '쇼핑몰 테이블 5개의 개체 관계도(ERD)')
                t.text = t.text.replace(' · Colab 3번 셀에서 재고 부족 시 전체 롤백을 확인',
                                        ' · 재고 부족 시 결제 트랜잭션 전체를 되돌림')
            if n == links[part] and t.text == ('확인 항목' if part == 1 else '셀'):
                t.text = '실습 단계 (클릭)'
            if part == 1 and n == 13:
                t.text = t.text.replace('AWS 실습 범위','쇼핑몰 구현 범위')
                if t.text.startswith('Colab 보안 비밀'):
                    t.text = '웹 화면은 상품과 주문 정보를 보여 주고, 데이터베이스는 재고와 배송 상태를 저장합니다.'
            if part == 1 and n in (33,34) and t.text=='이후 계획':
                t.text = '실습 결과 제출' if n==33 else '실습 마무리'
            if part == 1 and n == 32 and t.text=='6. 결론 및 향후 계획':
                t.text = '6. 설계 검증과 실습'
            if part == 2 and n == 20 and t.text.startswith('관계 및 트랜잭션 모델링 결과를'):
                t.text = '관계를 통합하고, 트랜잭션별로 어떤 표를 생성(C)·조회(R)·수정(U)·삭제(D)하는지 기록함'
            if part == 2 and n == 30:
                t.text = t.text.replace('앞 쪽 ERD',f'{pages[13]}쪽 ERD')
            if part == 3 and n == 57:
                t.text = t.text.replace('앞 쪽의 제약',f'{pages[20]}쪽의 제약')
        if n == links[part]:
            notebook_id, anchors = cells[part]
            table = content.find('.//{*}tbl')
            rows = table.findall('{*}tr')[1:]
            assert len(rows) == len(anchors)
            for idx, (row, anchor) in enumerate(zip(rows, anchors), 1):
                run = row.find('{*}tc').find('.//{*}r')
                props = run.find('{*}rPr')
                if props is None:
                    props = ET.Element(f'{{{A}}}rPr')
                    run.insert(0, props)
                rid = f'rIdPracticeStep{idx}'
                ET.SubElement(relationships, f'{{{ET.QName(relationships).namespace}}}Relationship',
                              Id=rid, Type=R+'/hyperlink', TargetMode='External',
                              Target=f'https://colab.research.google.com/drive/{notebook_id}#scrollTo={anchor}')
                ET.SubElement(props,f'{{{A}}}hlinkClick', {f'{{{R}}}id':rid})
            parts[relations_path] = xml(relationships)
        parts[slide] = xml(content)
        for r in relationships:
            if not r.get('Type','').endswith('/notesSlide'):
                continue
            note_path = 'ppt/'+r.get('Target').removeprefix('../')
            note = ET.fromstring(parts[note_path])
            for t in note.findall('.//{*}t'):
                if not t.text:
                    continue
                t.text=page_pattern.sub(remap,t.text)
                if theory and 'https://colab.research.google.com/' in t.text:
                    t.text=f'실습 진입은 설명을 마친 뒤 {new_guide_page}쪽에서 합니다.'
            parts[note_path]=xml(note)
    assert order[pivot:pivot+len(blocks[part])] == blocks[part]
    assert sorted(order) == sorted(old_order)
    with ZipFile(output/f'part{part}.pptx','w',ZIP_DEFLATED) as target:
        for name,data in parts.items():
            target.writestr(name,data)

    notebook_path = root / ('current1.ipynb' if part==1 else f'readback{part}.ipynb')
    notebook = json.loads(notebook_path.read_text())
    for cell in notebook['cells']:
        original=''.join(cell['source'])
        revised=page_pattern.sub(remap,original)
        revised=re.sub(r'(?m)(^quiz\(.*?,\s*\d+,\s*)(\d+)(\)$)',
                       lambda m: m[1]+str(pages[int(m[2])])+m[3], revised)
        revised=revised.replace('교안 각 페이지의 **Colab 버튼**이 아래 셀로 바로 이동합니다.',
                                f'교안 설명이 끝나면 **{new_guide_page}쪽부터** 실습을 시작합니다. 실습 구간의 Colab 버튼으로 이동하세요.')
        if part==1:
            revised=revised.replace(f'13·{new_guide_page}쪽',f'{new_guide_page}쪽')
        if revised!=original:
            cell['source']=revised.splitlines(keepends=True)
    (output/f'part{part}.ipynb').write_text(json.dumps(notebook,ensure_ascii=False,indent=1)+'\n')
    print(part, 'practice',new_guide_page, 'through',order.index(blocks[part][-1])+1, 'page mapping',pages)

for part in (1,2,3):
    reorganize(part)
