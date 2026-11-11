"""11-1 보강본: 18쪽(사례 · 모델링 3단계) 뒤에 실생활 예제 2장 추가
  19쪽 실습 예제 · 동네 도서관 대출 (개념 → 논리 → 물리 문제 + 카드 아래 작은 정답)
  20쪽 실습 예제 정답 · pgAdmin에서 만들어 보기 (SQL, 주석에 개념·논리·물리 정답) — db-course/cd11-1/sql/library_answer.sql 과 동일
python slide_library_example.py <in.pptx> <out.pptx> <library_answer.sql>   (같은 제목 슬라이드가 있으면 그 자리에서 다시 만듦)"""
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

src, out, sql_path = sys.argv[1:4]
prs = Presentation(src)
RGB = lambda h: RGBColor.from_string(h)
TXT, SUB, NAVY = RGB('262626'), RGB('5A5A5A'), RGB('1F4E79')
T1, T2 = '실습 예제 · 동네 도서관 대출 만들기', '실습 예제 정답 · pgAdmin SQL'
ids = prs.slides._sldIdLst


def get_slide(title, pos, layout_from):
    s = next((sl for sl in prs.slides if sl.shapes.title is not None and sl.shapes.title.text_frame.text.strip() == title), None)
    if s is None:
        s = prs.slides.add_slide(layout_from.slide_layout)
        el = ids[-1]; ids.remove(el); ids.insert(pos, el)
    for sh in list(s.shapes):
        if not (sh.is_placeholder and sh.placeholder_format.idx == 0):
            sh._element.getparent().remove(sh._element)
    s.shapes.title.text_frame.text = title
    return s


anchor = next(i for i, sl in enumerate(prs.slides) if sl.shapes.title is not None and sl.shapes.title.text_frame.text.strip() == '사례')
layout_src = prs.slides[anchor - 1]                     # 17쪽 물리적 모델링(원본 템플릿 '제목 및 내용')
A = get_slide(T1, anchor + 1, layout_src)
B = get_slide(T2, anchor + 2, layout_src)


def box(s, x, y, w, h, paras, size=12, color=TXT, bold=False, anchor_=None, font='Malgun Gothic', spacing=3):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    for m in ('margin_left', 'margin_right', 'margin_top', 'margin_bottom'):
        setattr(tf, m, Inches(0.04))
    if anchor_:
        tf.vertical_anchor = anchor_
    for i, p in enumerate(paras):
        runs = p if isinstance(p, list) else [p]
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.space_after = Pt(spacing)
        for rr in runs:
            text, kw = (rr, {}) if isinstance(rr, str) else rr
            r = para.add_run(); r.text = text
            r.font.size = Pt(kw.get('size', size)); r.font.bold = kw.get('bold', bold)
            r.font.color.rgb = kw.get('color', color); r.font.name = kw.get('font', font)
    return tb


def shape(s, kind, x, y, w, h, fill, line=None, lw=1.25):
    c = s.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    c.fill.solid(); c.fill.fore_color.rgb = RGB(fill)
    if line:
        c.line.color.rgb = RGB(line); c.line.width = Pt(lw)
    else:
        c.line.fill.background()
    c.shadow.inherit = False
    return c


def bar(s, y, text, fill='0F2A4A'):
    b = shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 0.75, y, 11.85, 0.46, fill)
    tf = b.text_frame; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = text; r.font.size = Pt(12.5); r.font.bold = True; r.font.color.rgb = RGB('FFFFFF'); r.font.name = 'Malgun Gothic'


# ───────────── 19쪽: 문제
shape(A, MSO_SHAPE.ROUNDED_RECTANGLE, 0.75, 1.5, 11.85, 0.82, 'FFF3D9', 'BF9000', 1)
box(A, 0.95, 1.55, 11.5, 0.75, [
    [('상황 · ', {'bold': True, 'color': RGB('7F6000')}), '김하늘 회원이 3월 2일 『데이터베이스 첫걸음』을 빌렸고, 3월 16일까지 반납해야 합니다.'],
    '한 회원은 여러 권을 빌리고, 한 책도 여러 번 대출됩니다. 사서는 ‘아직 반납 안 된 책’을 바로 찾을 수 있어야 합니다.'], size=12.5, anchor_=MSO_ANCHOR.MIDDLE, spacing=2)

CARDS = [
    ('1  개념 모델', '업무 언어로 그리기', '7030A0', 'F3ECFA',
     ['관리할 개체 3개는?', '개체 사이 관계(1:N)는?', '대출 개체의 속성은?'],
     '정답 · 회원·도서·대출 / 회원 1:N 대출, 도서 1:N 대출 / 대출일·반납예정일·반납일'),
    ('2  논리 모델', '테이블 설계도로 바꾸기', '1F4E79', 'DEEBF7',
     ['테이블 이름과 PK는?', '관계는 어느 테이블의 FK로?', '중복되면 안 되는 값은?'],
     '정답 · members·books·loans (각 _id PK) / loans.member_id, loans.book_id FK / phone·isbn UNIQUE'),
    ('3  물리 모델', 'PostgreSQL로 구현하기', '548235', 'E2F0D9',
     ['날짜·글자·번호 자료형은?', '반납예정일 규칙은 어떻게 지킬까?', '미반납 대출을 빨리 찾으려면?'],
     '정답 · DATE·VARCHAR·SERIAL / DEFAULT 오늘+14, CHECK(due_date > loan_date) / return_date IS NULL 부분 인덱스'),
]
for x, (head, sub, line, fill, qs, ans) in zip([0.75, 4.85, 8.95], CARDS):
    c = shape(A, MSO_SHAPE.ROUNDED_RECTANGLE, x, 2.5, 3.65, 3.25, fill, line, 1.5); c.adjustments[0] = 0.06
    box(A, x + 0.2, 2.58, 3.3, 0.7, [(head, {'size': 17, 'bold': True, 'color': RGB(line)}), (sub, {'size': 11, 'bold': True, 'color': SUB})], spacing=0)
    box(A, x + 0.2, 3.3, 3.3, 1.35, [[('Q%d  ' % i, {'bold': True, 'color': RGB(line)}), q] for i, q in enumerate(qs, 1)], size=12, spacing=5)
    a = shape(A, MSO_SHAPE.ROUNDED_RECTANGLE, x + 0.15, 4.75, 3.35, 0.88, 'FFFFFF', line, 0.75)
    tf = a.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = Inches(0.07)
    r = tf.paragraphs[0].add_run(); r.text = ans; r.font.size = Pt(9); r.font.color.rgb = RGB('8A96A8'); r.font.name = 'Malgun Gothic'
for ax in (4.43, 8.53):
    shape(A, MSO_SHAPE.RIGHT_ARROW, ax, 3.95, 0.38, 0.32, '7F7F7F')
bar(A, 5.92, '직접 해 보기 → 다음 쪽 SQL을 pgAdmin Query Tool에서 실행 (주석에 개념·논리·물리 정답)')
box(A, 0.75, 6.45, 11.85, 0.3, [('※ PK: Primary Key (기본키) · FK: Foreign Key (외래키) · UNIQUE: 중복 금지 제약 · 1:N: 일대다 관계 · '
                                 'ISBN: International Standard Book Number (국제 표준 도서 번호)', {'size': 9.5, 'color': RGB('3A445C')})])
A.notes_slide.notes_text_frame.text = (
    '【슬라이드 핵심】 실생활 업무(도서관 대출)를 개념 → 논리 → 물리 모델로 단계적으로 바꾸는 연습. 각 카드의 Q를 먼저 묻고, 카드 아래 작은 정답으로 확인한다.\n'
    '【강의 설명】 개념 모델에서는 회원·도서·대출 세 개체를 찾는다. 대출은 회원과 도서를 잇는 개체로, 대출일·반납예정일·반납일을 속성으로 가진다(회원 1:N 대출, 도서 1:N 대출 = 회원과 도서의 N:M). '
    '논리 모델에서는 개체를 members·books·loans 테이블로, 관계를 loans의 member_id·book_id 외래키로 바꾸고, 연락처와 ISBN은 UNIQUE로 둔다. '
    '물리 모델에서는 PostgreSQL 자료형(SERIAL·VARCHAR·DATE)을 정하고, 반납예정일 기본값(오늘+14일)과 CHECK(due_date > loan_date)로 업무 규칙을 지키며, '
    '“아직 반납 안 된 책”을 자주 찾으므로 return_date IS NULL 조건의 부분 인덱스를 만든다.\n'
    '【연결】 14–18쪽 개념·논리·물리 모델링, 20쪽 pgAdmin 정답 SQL\n'
    '【출처】 수업용 예제(가상의 회원·도서), PostgreSQL 공식 문서 CREATE TABLE·Constraints·Partial Indexes')

# ───────────── 20쪽: 정답 SQL
sql = open(sql_path, encoding='utf-8').read().rstrip('\n').split('\n')
cut = next(i for i, l in enumerate(sql) if l.startswith('-- ③ 물리: 미반납'))
left, right = sql[:cut], ['-- 다시 하려면: DROP TABLE loans, books, members;', ''] + sql[cut:]
box(B, 0.75, 1.48, 11.85, 0.35, [[('pgAdmin ▸ ', {'bold': True, 'color': NAVY}), '실습 DB 선택 ▸ Tools ▸ Query Tool ▸ 아래 SQL 붙여넣기 ▸ 실행(F5)  ',
                                   ('· 초록색 주석이 정답 설명', {'color': RGB('548235'), 'bold': True})]], size=12.5)


def code_panel(x, y, w, h, lines):
    shape(B, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h, 'F4F6F9', 'B4BFCC', 0.75).adjustments[0] = 0.03
    paras = []
    for l in lines:
        if '--' in l:
            k = l.index('--'); code, com = l[:k], l[k:]
            paras.append(([(code, {'color': RGB('102950')})] if code else []) + [(com, {'color': RGB('548235'), 'bold': True})])
        else:
            paras.append([(l if l else ' ', {'color': RGB('102950')})])
    box(B, x + 0.1, y + 0.06, w - 0.2, h - 0.1, paras, size=9, font='Courier New', spacing=0)


code_panel(0.75, 1.9, 6.15, 4.3, left)
code_panel(7.05, 1.9, 5.55, 2.95, right)
res = B.shapes.add_table(2, 4, Inches(7.05), Inches(4.95), Inches(5.55), Inches(0.5)).table
for j, (h, v) in enumerate(zip(['name', 'title', 'loan_date', 'due_date'], ['김하늘', '데이터베이스 첫걸음', '2026-03-02', '2026-03-16'])):
    for i, t in enumerate((h, v)):
        c = res.cell(i, j); c.text = t
        c.fill.solid(); c.fill.fore_color.rgb = RGB('102950' if i == 0 else 'EDF4FD')
        r = c.text_frame.paragraphs[0].runs[0]; r.font.size = Pt(9.5); r.font.name = 'Malgun Gothic'
        r.font.bold = i == 0; r.font.color.rgb = RGB('FFFFFF') if i == 0 else TXT
res.columns[1].width = Inches(1.95)
for j in (0, 2, 3):
    res.columns[j].width = Inches(1.2)
box(B, 7.05, 5.5, 5.55, 0.7, [[('제약조건 확인 · ', {'bold': True, 'color': NAVY}), '없는 회원 9번 대출 → FK 오류'],
                              '반납예정일이 대출일보다 빠름 → CHECK 오류 · 같은 번호 가입 → UNIQUE 오류'], size=10, spacing=1)
bar(B, 6.3, '개념(회원·도서·대출) → 논리(3개 테이블 + FK) → 물리(자료형·기본값·CHECK·인덱스)가 SQL 한 장에 모두 담깁니다')
box(B, 0.75, 6.8, 11.0, 0.3, [('※ SERIAL: 자동 증가 정수 · REFERENCES: FK 지정 · DEFAULT: 값을 안 넣으면 쓰는 기본값 · 부분 인덱스: 조건에 맞는 행만 담은 인덱스',
                               {'size': 9.5, 'color': RGB('3A445C')})])
B.notes_slide.notes_text_frame.text = (
    '【슬라이드 핵심】 19쪽 예제의 정답을 pgAdmin Query Tool에서 직접 실행한다. 주석(--)이 개념·논리·물리 단계의 정답 설명이다.\n'
    '【강의 설명】 ① 개념: 회원 1:N 대출 N:1 도서. ② 논리: members·books·loans 세 테이블, loans.member_id와 loans.book_id가 FK(REFERENCES). '
    '③ 물리: SERIAL·VARCHAR·CHAR(13)·DATE 자료형, due_date 기본값 CURRENT_DATE + 14, CHECK(due_date > loan_date), 미반납 조회용 부분 인덱스 idx_loans_open. '
    '실행하면 마지막 SELECT가 “김하늘 | 데이터베이스 첫걸음 | 2026-03-02 | 2026-03-16” 한 행을 보여 준다. '
    '이어서 학생에게 일부러 잘못된 INSERT를 실행하게 한다: 없는 회원(9번) 대출은 FK 오류, 반납예정일이 대출일보다 빠르면 CHECK 오류, 같은 연락처로 가입하면 UNIQUE 오류. '
    '오류 메시지가 곧 모델링 단계에서 정한 업무 규칙이라는 점을 강조한다. 다시 실행하려면 DROP TABLE loans, books, members; 를 먼저 실행한다. '
    'PostgreSQL 16에서 실행해 결과와 세 가지 오류를 확인했다.\n'
    '【연결】 19쪽 문제, 14–18쪽 모델링 단계, 이후 Colab 실습(주문·결제)\n'
    '【출처】 PostgreSQL 공식 문서 CREATE TABLE·Constraints·Partial Indexes, pgAdmin Query Tool 문서. SQL 원본: db-course/cd11-1/sql/library_answer.sql')

prs.save(out)
print('ok, slides =', len(prs.slides), '| example at', anchor + 2, anchor + 3)
