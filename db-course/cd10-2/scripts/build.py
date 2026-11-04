"""CD10-2 보강판 초안 생성: python build.py <원본.pptx> <출력.pptx>"""
import copy, sys
from pathlib import Path
from pptx import Presentation
from pptx.util import Pt, Emu
from pptx.dml.color import RGBColor

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cd102_new import NEW
from notes_102 import N

A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
prs = Presentation(sys.argv[1])
orig = list(prs.slides)
layout = orig[3].slide_layout


def set_lines(shape, lines, size=None):
    tf = shape.text_frame
    first = tf.paragraphs[0]
    for p in tf.paragraphs[1:]:
        p._p.getparent().remove(p._p)
    for r in first.runs[1:]:
        r._r.getparent().remove(r._r)
    tmpl = copy.deepcopy(first._p)
    first.runs[0].text = lines[0]
    prev = first._p
    for ln in lines[1:]:
        np_ = copy.deepcopy(tmpl)
        prev.addnext(np_)
        prev = np_
        np_.findall(A + 'r')[0].find(A + 't').text = ln
    if size:
        for p in tf.paragraphs:
            for r in p.runs:
                r.font.size = Pt(size)


def clone(tmpl_slide, texts):
    s = prs.slides.add_slide(layout)
    for ph in list(s.placeholders):
        ph._element.getparent().remove(ph._element)
    for el in tmpl_slide.shapes._spTree.iterchildren():
        if el.tag.endswith('}sp'):
            s.shapes._spTree.append(copy.deepcopy(el))
    shapes = [sh for sh in s.shapes if sh.has_text_frame and sh.text_frame.text.strip()]
    assert len(shapes) == len(texts), (len(shapes), len(texts))
    for sh, t in zip(shapes, texts):
        set_lines(sh, [x if x else ' ' for x in t], size=14) if isinstance(t, list) else set_lines(sh, [t])
    return s


def para_replace(slide, start, new):
    for sh in slide.shapes:
        if sh.has_text_frame:
            for p in sh.text_frame.paragraphs:
                if p.text.strip().startswith(start):
                    p.runs[0].text = new
                    for r in p.runs[1:]:
                        r._r.getparent().remove(r._r)
                    return
    raise KeyError(start)


def sub_replace(slide, old, new):
    for sh in slide.shapes:
        if sh.has_text_frame:
            for r in (r for p in sh.text_frame.paragraphs for r in p.runs):
                if old in r.text:
                    r.text = r.text.replace(old, new)
                    return
    raise KeyError(old)


# 1) 원본 본문 오류 수정 (원본 번호 기준)
S = lambda n: orig[n - 1]
para_replace(S(7), '해당 열의 데이터를 정렬한 후', '해당 열의 데이터를 정렬한 후 별도의 저장 공간(인덱스 파일)에 열의 값과 행의 물리적 주소를 저장함. (자주 쓰는 인덱스는 메모리에 캐싱됨)')
sub_replace(S(9), '속도나 느려질', '속도가 느려질')
sub_replace(S(15), '=‘', "='")
sub_replace(S(15), '’', "'")
sub_replace(S(16), '소요시간 추력', '소요시간 출력')
for sh in S(16).shapes:
    if sh.has_table:
        for row in sh.table.rows:
            if row.cells[0].text.strip() == 'FORMAT':
                r = row.cells[2].text_frame.paragraphs[0].runs
                r[0].text = 'TEXT'
                for x in r[1:]:
                    x.text = ''

# 2) 노트 (원본 노트의 링크는 【출처】로 보존)
for i, s in enumerate(orig, 1):
    tf = s.notes_slide.notes_text_frame
    old = tf.text.strip()
    txt = N[i]
    if old and old.split()[0].startswith('http') and old.split()[0] not in txt:
        txt += '\n【원본 메모】 ' + old.replace('\n', ' ')
    tf.text = txt

# 3) 추가 슬라이드 생성·배치
sld = prs.slides._sldIdLst
ids = list(sld)
order = {i + 1: [ids[i]] for i in range(len(ids))}
for tnum, after, texts, note in NEW:
    ns = clone(orig[tnum - 1], texts)
    ns.notes_slide.notes_text_frame.text = note
    order[after].append(list(sld)[-1])
for el in list(sld):
    sld.remove(el)
for k in sorted(order):
    for el in order[k]:
        sld.append(el)

# 4) 약어 주석 (원본 번호 기준 페이지)
G = {
    'BT': 'B-tree: Balanced Tree (균형 트리)', 'GIST': 'GiST: Generalized Search Tree (범용 검색 트리)',
    'GIN': 'GIN: Generalized Inverted Index (범용 역인덱스)', 'BRIN': 'BRIN: Block Range Index (블록 범위 인덱스)',
    'FTS': 'FTS: Full-Text Search (전체 텍스트 검색)', 'GIS': 'GIS: Geographic Information System (지리 정보 시스템)',
    'IP': 'IP: Internet Protocol (인터넷 주소 체계)', 'JSONB': 'JSONB: JSON Binary (이진 형식으로 저장하는 JSON)',
    'FMT': 'JSON: JavaScript Object Notation · XML: eXtensible Markup Language · YAML: YAML Ain\'t Markup Language (데이터 표현 형식)',
    'HEAP': 'Heap: 테이블의 실제 행이 저장된 영역(파일) · Heap Fetches: 인덱스만으로 부족해 테이블을 확인한 횟수',
    'WM': 'work_mem: 정렬·해시 연산 1회당 쓰는 지역 메모리 크기',
}
FN = {3: [['BT', 'GIST'], ['GIN', 'BRIN']], 12: [['FTS', 'GIS'], 'IP'], 13: ['JSONB', 'FTS'], 16: ['FMT']}
DARK = {3}
for n, keys in FN.items():
    s = orig[n - 1]
    lines = ['   '.join('※ ' + G[x] for x in k) if isinstance(k, list) else '※ ' + G[k] for k in keys]
    h = 150000 * len(lines) + 60000
    tb = s.shapes.add_textbox(Emu(914400), Emu(6858000 - h - 60000), Emu(9900000), Emu(h))
    tb.name = '약어 주석'
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_top = tf.margin_bottom = Emu(0)
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        r = p.add_run()
        r.text = ln
        r.font.size = Pt(10.5)
        r.font.name = 'NanumGothic'
        r.font.color.rgb = RGBColor(0xDD, 0xE6, 0xF5) if n in DARK else RGBColor(0x3A, 0x44, 0x5C)

prs.save(sys.argv[2])
print('saved', sys.argv[2], len(prs.slides), 'slides')
