"""CD10-3 RAID 보강판 생성: python build.py <기준본.pptx> <출력.pptx>"""
import copy, sys
from pathlib import Path
from pptx import Presentation
from pptx.util import Pt, Emu, Inches
from pptx.dml.color import RGBColor

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from cd103_new import NEW
from notes_103 import N

_src = (HERE.parents[1] / 'cd10-1' / 'scripts' / 'pgadmin_labs.py').read_text(encoding='utf-8')
_h = {}
exec(_src.split('# 39 · 세션 관찰')[0].replace("prs = Presentation(sys.argv[1])", "prs = None"), _h)
find, set_lines, panel = _h['find'], _h['set_lines'], _h['panel']

prs = Presentation(sys.argv[1])
orig = list(prs.slides)


def clone(tmpl_slide, texts):
    s = prs.slides.add_slide(tmpl_slide.slide_layout)
    for ph in list(s.placeholders):
        ph._element.getparent().remove(ph._element)
    for el in tmpl_slide.shapes._spTree.iterchildren():
        if el.tag.endswith('}sp'):
            s.shapes._spTree.append(copy.deepcopy(el))
    shapes = [sh for sh in s.shapes if sh.has_text_frame and sh.text_frame.text.strip()]
    assert len(shapes) == len(texts), (len(shapes), len(texts))
    for sh, t in zip(shapes, texts):
        set_lines(sh, [x if x else ' ' for x in t], size=12.5) if isinstance(t, list) else set_lines(sh, [t])
    return s


def sub_all(slide, old, new):
    n = 0
    for sh in slide.shapes:
        if sh.has_text_frame:
            for r in (r for p in sh.text_frame.paragraphs for r in p.runs):
                if old in r.text:
                    r.text = r.text.replace(old, new)
                    n += 1
    return n


G = {
    'IO': 'I/O: Input/Output (입출력)',
    'XOR': 'XOR: eXclusive OR (배타적 논리합: 두 비트가 같으면 0, 다르면 1)',
    'NAS': 'NAS: Network Attached Storage (네트워크 연결 저장소)', 'DB': 'DB: Database (데이터베이스)',
    'TB': 'TB: Terabyte (테라바이트, 약 1,000GB)',
    'EBS': 'EBS: Elastic Block Store (AWS의 클라우드 디스크)',
    'IOPS': 'IOPS: Input/Output Operations Per Second (초당 입출력 횟수)',
    'AZ': 'AZ: Availability Zone (가용 영역, 서로 독립된 데이터센터 묶음)',
    'RDS': 'RDS: Relational Database Service (AWS 관리형 관계형 DB 서비스)',
    'PITR': 'PITR: Point-In-Time Recovery (특정 시점 복구)',
    'GP3': 'gp2·gp3: General Purpose SSD (범용 SSD 볼륨) · io1·io2: Provisioned IOPS SSD (성능 보장형)',
}


def footnote(slide, keys, mode):
    lines = ['   '.join('※ ' + G[x] for x in k) if isinstance(k, list) else '※ ' + G[k] for k in keys]
    if mode == 'row':
        top, h = 5600000, 440000
    elif mode == 'code':
        top, h = 6500000, 340000
    else:
        h = 150000 * len(lines) + 60000
        top = 6858000 - h - 60000
    tb = slide.shapes.add_textbox(Emu(914400), Emu(top), Emu(9900000), Emu(h))
    tb.name = '약어 주석'
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_top = tf.margin_bottom = Emu(0)
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        r = p.add_run(); r.text = ln
        r.font.size = Pt(10.5); r.font.name = 'NanumGothic'; r.font.color.rgb = RGBColor(0x3A, 0x44, 0x5C)


# 1) 원본 본문 수정
for n in (2, 7):
    sub_all(orig[n - 1], 'Independent Disk', 'Independent Disks')

# 2) 노트 (기존 노트 보존)
for i, s in enumerate(orig, 1):
    tf = s.notes_slide.notes_text_frame
    old = tf.text.strip()
    txt = N[i]
    if old:
        rest = old.split(None, 1)[1] if old.split()[0].startswith('http') and old.split()[0] in txt else old
        if rest:
            txt += '\n【기존 메모】 ' + rest
    tf.text = txt

# 5) 추가 슬라이드
sld = prs.slides._sldIdLst
ids = list(sld)
order = {i + 1: [ids[i]] for i in range(len(ids))}
NEW_FN = [([['EBS'], 'IOPS'], 'row'), ([['AZ', 'RDS'], 'PITR'], 'row'), ([['RDS', 'PITR'], 'GP3'], 'code'), (['IOPS'], 'code')]
NEW_PANEL = [None, None,
             ('실행 결과 (예상 · 실행 후 확인)', [('스토리지 종류: gp2 또는 gp3', 'b'), ('→ EBS 볼륨: AZ 안에서 이미 복제', 'n'),
                                     ('Multi-AZ: False (실습용)', 'b'), ('→ 데이터센터 장애에는 보호 안 됨', 'n'),
                                     ('백업 보존: N일', 'b'), ('→ 이 기간 안에서 PITR로 실수 복구 가능', 'n')]),
             ('계산 결과 (디스크 4개 × 3,000 IOPS)', [('RAID 0 · 쓰기 12,000 IOPS', 'b'), ('RAID 1·10 · 쓰기 6,000 IOPS', 'b'),
                                               ('RAID 5 · 쓰기 3,000 IOPS', 'b'), ('RAID 6 · 쓰기 2,000 IOPS', 'b'),
                                               ('읽기는 모두 12,000 IOPS (단순 모델)', 's')])]
for (tnum, after, texts, note), (fk, fm), pn in zip(NEW, NEW_FN, NEW_PANEL):
    ns = clone(orig[tnum - 1], texts)
    ns.notes_slide.notes_text_frame.text = note
    if pn:
        c = [sh for sh in ns.shapes if sh.has_text_frame and sh.text_frame.text.strip()][3]
        c.width = Inches(6.75)
        panel(ns, 8.05, 3.0, 4.35, 3.45, pn[0], pn[1])
    footnote(ns, fk, fm)
    order[after].append(list(sld)[-1])
# 3) 학생 실습 2(XOR) 결과 패널
s25 = orig[24]
code = find(s25, 'a, b, c = 12, 25, 37')
code.width = Inches(6.75)
panel(s25, 8.05, 3.0, 4.35, 3.45, '실행 결과', [
    ('원본: 25 · 복구값: 25 · 일치: True', 'b'),
    ('12 ^ 25 ^ 37 = 56 (패리티)', 'n'), ('12 ^ 37 ^ 56 = 25 → 사라진 b 복구', 'n'),
    ('같은 값을 두 번 XOR하면 사라진다', 'b'), ('그래서 남은 값 + 패리티로 잃은 값을 되찾음', 'n')])

# 4) 약어 주석 (원본)
for n, keys, mode in [(7, ['IO'], 'foot'), (12, ['XOR'], 'foot'), (14, ['XOR'], 'foot'),
                      (21, [['NAS', 'DB']], 'foot'), (24, ['TB'], 'row'), (25, ['XOR'], 'code')]:
    footnote(orig[n - 1], keys, mode)

for el in list(sld):
    sld.remove(el)
for k in sorted(order):
    for el in order[k]:
        sld.append(el)

prs.save(sys.argv[2])
print('saved', sys.argv[2], len(prs.slides), 'slides')
