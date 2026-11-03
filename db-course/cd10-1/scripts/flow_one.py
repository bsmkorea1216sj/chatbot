"""RDS Proxy 흐름도 1장 생성 (build.py 실행 후): python db-course/cd10-1/scripts/flow_one.py"""
import copy
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

OUTDIR = Path(__file__).resolve().parent.parent / 'output'
F = str(OUTDIR / 'CD10-1_PostgreSQL(26).pptx')
prs = Presentation(F)
src = prs.slides[3]
s = prs.slides.add_slide(src.slide_layout)
for ph in list(s.placeholders):
    ph._element.getparent().remove(ph._element)

keep = [sh for sh in src.shapes if sh.has_text_frame and sh.text_frame.text.strip()]
for sh in (keep[0], keep[1], keep[-1]):
    s.shapes._spTree.append(copy.deepcopy(sh._element))
tag, title, foot = [sh for sh in s.shapes if sh.has_text_frame]
for sh, t in ((tag, '현업 사례 · 흐름도'), (title, 'RDS Proxy: 연결 풀링과 연결 고정(pinning) 흐름'),
              (foot, '핵심: Proxy는 연결 수(Server Process)를 줄이고, 느린 SELECT는 실행계획(Planner/Executor)에서 해결합니다.')):
    p = sh.text_frame.paragraphs[0]
    p.runs[0].text = t
    for r in p.runs[1:]:
        r._r.getparent().remove(r._r)

FONT = 'NanumGothic'
NAVY, WHITE, TXT = RGBColor(0x1B, 0x2A, 0x6B), RGBColor(0xFF, 0xFF, 0xFF), RGBColor(0x1A, 0x23, 0x32)


def box(x, y, w, h, fill, lines, color=TXT, size=13, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    b = s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    b.fill.solid(); b.fill.fore_color.rgb = fill
    if line:
        b.line.color.rgb = line; b.line.width = Pt(1.25)
    else:
        b.line.fill.background()
    b.shadow.inherit = False
    tf = b.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    for m in ('margin_left', 'margin_right'):
        setattr(tf, m, Inches(0.08))
    for i, (txt, bold) in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run(); r.text = txt
        r.font.size = Pt(size if bold else size - 2); r.font.bold = bold
        r.font.name = FONT; r.font.color.rgb = color
    return b


def arrow(x, y, label=None):
    a = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(y), Inches(0.45), Inches(0.32))
    a.fill.solid(); a.fill.fore_color.rgb = RGBColor(0x8A, 0x9B, 0xB5); a.line.fill.background()
    a.shadow.inherit = False


rows = [
    ('① 직접 연결', RGBColor(0x6B, 0x72, 0x80),
     [('학생 1,000명', True), ('클라이언트 연결 1,000개', False)],
     [('Proxy 없음', True), ('연결 1개 = 백엔드 1개', False)], RGBColor(0xF1, 0xF3, 0xF6),
     [('백엔드 프로세스 1,000개', True), ('max_connections·메모리 한계 도달', False)], RGBColor(0xFE, 0xE2, 0xE2)),
    ('② 연결 풀링', RGBColor(0x1A, 0x56, 0xDB),
     [('학생 1,000명', True), ('클라이언트 연결 1,000개', False)],
     [('RDS Proxy', True), ('트랜잭션이 끝나면 연결 반환 → 재사용', False)], RGBColor(0xFF, 0xF0, 0xD9),
     [('백엔드 프로세스 수십 개', True), ('적은 프로세스로 안정 처리', False)], RGBColor(0xDC, 0xF5, 0xE3)),
    ('③ 연결 고정', RGBColor(0xB4, 0x53, 0x09),
     [('세션 상태 변경', True), ('SET · 임시 테이블 · Prepared Statement', False)],
     [('RDS Proxy', True), ('세션 상태 보존 → 연결을 그 클라이언트에 고정', False)], RGBColor(0xFF, 0xF0, 0xD9),
     [('고정된 백엔드는 공유 불가', True), ('고정 ↑ → 풀링 효과 ↓', False)], RGBColor(0xFE, 0xF3, 0xC7)),
]
y = 2.45
for label, lc, cl, mid, mfill, db, dfill in rows:
    box(0.9, y + 0.2, 1.55, 0.55, lc, [(label, True)], color=WHITE, size=13)
    box(2.65, y, 2.55, 0.95, RGBColor(0xEE, 0xF4, 0xFF), cl, line=RGBColor(0xA8, 0xC4, 0xF8))
    arrow(5.3, y + 0.32)
    box(5.85, y, 2.75, 0.95, mfill, mid, line=RGBColor(0xF5, 0xA6, 0x23))
    arrow(8.7, y + 0.32)
    box(9.25, y, 2.75, 0.95, dfill, db, line=RGBColor(0xC9, 0xD1, 0xDE))
    y += 1.05

hdr = [(2.65, 2.55, 'Client Processes'), (5.85, 2.75, 'RDS Proxy (연결 풀)'), (9.25, 2.75, 'PostgreSQL Server Processes')]
for x, w, t in hdr:
    tb = s.shapes.add_textbox(Inches(x), Inches(2.17), Inches(w), Inches(0.26))
    p = tb.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = t; r.font.size = Pt(11); r.font.bold = True; r.font.name = FONT
    r.font.color.rgb = RGBColor(0x4A, 0x55, 0x68)

box(0.9, 5.62, 11.1, 0.74, NAVY,
    [('토론 정답  ·  Proxy가 줄이는 것은 연결 수(Server Process) — 느린 SELECT 자체는 Planner/Executor 문제', True),
     ('→ EXPLAIN ANALYZE로 실행계획 확인 (SQL 처리 5단계에서 학습)', False)], color=WHITE, size=14,
    shape=MSO_SHAPE.RECTANGLE)

s.notes_slide.notes_text_frame.text = (
    "【슬라이드 핵심】 앞 슬라이드(현업 사례 RDS Proxy)를 세 가지 흐름으로 그린 다이어그램.\n"
    "【강의 설명】\n① 직접 연결: 학생 1,000명이 바로 접속하면 Postmaster가 연결마다 백엔드를 만들어 1,000개가 됩니다. max_connections를 넘거나 백엔드마다 쓰는 Local Memory 때문에 메모리가 부족해집니다.\n"
    "② 연결 풀링: Proxy가 클라이언트 1,000개를 받아 DB 쪽에는 수십 개 연결만 유지합니다. 트랜잭션이 끝나면 연결을 풀에 돌려 다른 클라이언트가 재사용합니다.\n"
    "③ 연결 고정(pinning): 클라이언트가 SET, 임시 테이블, Prepared Statement처럼 세션 상태를 바꾸면 그 연결을 남과 나눌 수 없어 Proxy가 연결을 그 클라이언트에 묶어 둡니다. 고정이 늘수록 ②의 이점이 사라져 ①에 가까워집니다.\n"
    "④ 아래 남색 상자: Proxy는 연결 수(Server Process) 문제만 해결합니다. 쿼리 하나가 느린 것은 Planner/Executor 문제이며, EXPLAIN ANALYZE로 확인합니다(SQL 처리 5단계).\n"
    "【연결】 2. Server Processes(슬라이드 12~13), Colab 실습 1(슬라이드 42).\n"
    "【출처】 https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/rds-proxy.howitworks.html")


lst = prs.slides._sldIdLst
for el in list(lst)[:-1]:
    prs.part.drop_rel(el.rId); lst.remove(el)
prs.save(str(OUTDIR / 'CD10-1_RDS_Proxy_흐름도(26).pptx')); print('ok', len(prs.slides))
