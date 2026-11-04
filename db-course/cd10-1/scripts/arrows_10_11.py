"""10-1 기준본 10번(도형 화살표 굵게)·11번(이미지 위 굵은 화살표 덧그리기): python arrows_10_11.py <in.pptx> <out.pptx>"""
import sys
from lxml import etree
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR

A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
COLOR = '1F3A68'
prs = Presentation(sys.argv[1])

# 10번: 기존 화살표(선) 8개 → 3pt, 큰 화살촉, 진한 남색
s10 = prs.slides[9]
n10 = 0
for ln in s10.shapes._spTree.iter(A + 'ln'):
    ends = [ln.find(A + 'headEnd'), ln.find(A + 'tailEnd')]
    if not any(e is not None and e.get('type') not in (None, 'none') for e in ends):
        continue
    xfrm = ln.getparent().find(A + 'xfrm')
    ext = xfrm.find(A + 'ext') if xfrm is not None else None
    short = ext is not None and max(int(ext.get('cx')), int(ext.get('cy'))) < 300000   # 약 0.33inch 미만
    ln.set('w', '25400' if short else '38100')
    for f in ln.findall(A + 'solidFill') + ln.findall(A + 'schemeClr') + ln.findall(A + 'noFill'):
        ln.remove(f)
    fill = etree.SubElement(ln, A + 'solidFill')
    etree.SubElement(fill, A + 'srgbClr', val=COLOR)
    ln.remove(fill); ln.insert(0, fill)          # solidFill은 ln의 첫 자식이어야 함
    for e in ends:
        if e is not None and e.get('type') not in (None, 'none'):
            e.set('w', 'med' if short else 'lg'); e.set('len', 'med' if short else 'lg')
    n10 += 1

# 11번: 이미지 속 가는 화살표 위에 같은 위치로 굵은 화살표 덧그리기 (단위: inch)
s11 = prs.slides[10]


def style(shape, head=True):
    ln = shape.line
    ln.width = Pt(3); ln.color.rgb = RGBColor.from_string(COLOR)
    if head:
        x = ln._get_or_add_ln()
        t = etree.SubElement(x, A + 'tailEnd'); t.set('type', 'triangle'); t.set('w', 'lg'); t.set('len', 'lg')
    shape.name = '굵은 화살표(덧그림)'


for x1, y1, x2, y2 in [(4.37, 2.10, 5.46, 2.10),     # EC2/Lambda/Colab → Postmaster
                       (3.55, 2.35, 3.55, 3.10),     # EC2 → API (Query and result)
                       (6.45, 2.52, 6.45, 2.93)]:    # Postmaster → Postgres Server
    c = s11.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    style(c)
# Postgres Server → 아래 → 오른쪽 → 위 (Archiver) : 직선 3개, 마지막에만 화살촉
for (x1, y1, x2, y2), head in [((6.45, 3.60, 6.45, 5.77), False),
                               ((6.45, 5.77, 7.52, 5.77), False),
                               ((7.52, 5.77, 7.52, 5.57), True)]:
    c = s11.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    style(c, head)

prs.save(sys.argv[2])
print('slide10 arrows thickened:', n10, '/ slide11 overlay lines: 6')
