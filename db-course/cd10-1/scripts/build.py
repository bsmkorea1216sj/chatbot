"""CD10-1 보강판 생성: python db-course/cd10-1/scripts/build.py  (pip install python-pptx)"""
import copy, os, sys
from pathlib import Path
from pptx import Presentation
from pptx.util import Pt

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from cd101_new import NEW      # 추가 슬라이드(템플릿 번호, 삽입 위치, 텍스트, 노트)
from notes_v2 import N         # 최종 45장 노트 (출력 슬라이드 번호 기준)
import fix_body                # 본문 수정 (출력 슬라이드 번호 기준)

SRC = HERE.parent / 'source' / 'CD10-1_PostgreSQL26_원본.pptx'
OUT = HERE.parent / 'output' / 'CD10-1_PostgreSQL(26).pptx'
A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'

prs = Presentation(str(SRC))
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
        if isinstance(t, list):
            set_lines(sh, [x if x else ' ' for x in t], size=13)
        else:
            set_lines(sh, [t])


# 1) 추가 슬라이드 생성 후 원본 순서 사이에 끼워 넣기
sld = prs.slides._sldIdLst
ids = list(sld)
order = {i + 1: [ids[i]] for i in range(len(ids))}
for tnum, after, texts, _note in NEW:
    clone(orig[tnum - 1], texts)
    order[after].append(list(sld)[-1])
for el in list(sld):
    sld.remove(el)
for k in sorted(order):
    for el in order[k]:
        sld.append(el)

slides = list(prs.slides)
# 2) 본문 수정
fix_body.apply(slides)
# 3) SUMMARY 글자 크기 조정 (넘침 방지)
for sh in slides[34].shapes:
    if sh.has_text_frame and 'SQL 문은' in sh.text_frame.text:
        for p in sh.text_frame.paragraphs:
            for r in p.runs:
                r.font.size = Pt(19)
            p.space_before = Pt(2)
# 4) 노트
for i, s in enumerate(slides, 1):
    s.notes_slide.notes_text_frame.text = N[i]

OUT.parent.mkdir(exist_ok=True)
prs.save(str(OUT))
print('saved', OUT, len(slides), 'slides')
