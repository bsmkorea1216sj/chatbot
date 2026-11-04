"""CD10-3 기준본(31장) 약어·용어 주석 보강: python footnotes3.py <in.pptx> <out.pptx>
이미 '※' 주석이 있는 페이지는 건너뜀."""
import sys
from pptx import Presentation
from pptx.util import Pt, Emu
from pptx.dml.color import RGBColor

G = {
    'RAID': 'RAID: Redundant Array of Inexpensive/Independent Disks (여러 디스크를 묶어 안정성·성능을 높이는 기술)',
    'AWS': 'AWS: Amazon Web Services · Aurora: AWS의 클라우드 전용 관계형 DB (MySQL·PostgreSQL 호환)',
    'AZ': '가용 영역(AZ, Availability Zone): 전원·네트워크가 분리된 독립 데이터센터 묶음',
    'STRIPE': '스트라이핑(Striping): 데이터를 블록으로 나눠 여러 디스크에 번갈아 저장하는 방식',
    'MIRROR': '미러링(Mirroring): 같은 데이터를 여러 디스크에 똑같이 복사하는 방식',
    'IO': 'I/O: Input/Output (입출력)', 'NECK': '병목: 한 곳에 작업이 몰려 전체가 느려지는 현상',
    'PARITY': '패리티(Parity): 잃은 데이터를 계산(XOR)으로 되살리기 위한 검증 값',
    'N1': 'N−1: 디스크 N개 중 1개 분량을 패리티에 사용 (사용 용량 = N−1개)',
    'DUAL': '이중 패리티: 서로 다른 방식으로 계산한 패리티 2개(P, Q) → 디스크 2개 고장까지 복구',
    'N2': 'N−2: 디스크 N개 중 2개 분량을 패리티에 사용 (사용 용량 = N−2개)',
    'R10': 'RAID 10(1+0): 먼저 미러링(1) 후 스트라이핑(0) · RAID 0+1은 순서가 반대(먼저 나누고 복사)',
    'ONEDRIVE': 'OneDrive: Microsoft의 클라우드 저장소',
    'B321': '3-2-1 백업: 복사본 3개, 서로 다른 저장 매체 2종류, 1개는 다른 장소(클라우드 등)에 보관',
    'XOR': 'XOR: eXclusive OR (배타적 논리합: 두 비트가 같으면 0, 다르면 1)',
    'BACKUP': '백업 vs 복제: 복제(RAID·Multi-AZ)는 실수도 함께 복사, 백업은 과거 시점의 사본을 따로 보관',
}
PLAN = {
    3: (['RAID'], 'foot'),
    4: (['AWS', 'AZ'], 'row'),
    8: (['STRIPE'], 'foot'),
    10: (['MIRROR'], 'foot'),
    13: ([['IO', 'NECK']], 'foot'),
    15: (['PARITY', 'N1'], 'foot'),
    17: (['DUAL'], 'foot'),
    18: (['N2'], 'foot'),
    19: (['R10'], 'foot'),
    24: (['ONEDRIVE', 'B321'], 'box:9.2,3.0,3.3,1.3'),
    30: (['XOR', 'BACKUP'], 'row'),
}
DARK = {3}


def add(slide, n, keys, mode):
    lines = ['   '.join('※ ' + G[x] for x in k) if isinstance(k, list) else '※ ' + G[k] for k in keys]
    left, width = 914400, 9900000
    if mode.startswith('box:'):
        x, y, w, hh = (float(v) for v in mode[4:].split(','))
        left, top, width, h = int(x * 914400), int(y * 914400), int(w * 914400), int(hh * 914400)
    elif mode == 'row':
        top, h = 5600000, 440000
    else:
        h = 150000 * len(lines) + 60000
        top = 6858000 - h - 60000
    tb = slide.shapes.add_textbox(Emu(left), Emu(top), Emu(width), Emu(h))
    tb.name = '약어 주석'
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_top = tf.margin_bottom = Emu(0)
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        r = p.add_run(); r.text = ln
        r.font.size = Pt(10.5); r.font.name = 'NanumGothic'
        r.font.color.rgb = RGBColor(0xDD, 0xE6, 0xF5) if n in DARK else RGBColor(0x3A, 0x44, 0x5C)


prs = Presentation(sys.argv[1])
done = []
for n, (keys, mode) in PLAN.items():
    s = prs.slides[n - 1]
    if any(sh.has_text_frame and sh.text_frame.text.lstrip().startswith('※') for sh in s.shapes):
        continue
    add(s, n, keys, mode)
    done.append(n)
prs.save(sys.argv[2])
print('footnotes added:', done)
