"""CD12-1 교안의 Colab 버튼·문구를 새 노트북 셀(1 DB 생성 · 2 표 만들기 · 3 자동 검증 · 4 웹앱 실행 · 5 삭제)과 1:1로 맞춘다.
접근은 Colab 보안 비밀(AWS 키·DB_PASSWORD)만, 실습 후 5번 셀로 AWS RDS 삭제.
python deck_cell_links.py <in.pptx> <out.pptx>"""
import sys, copy
from pptx import Presentation
from pptx.util import Inches

src, out = sys.argv[1:3]
prs = Presentation(src)
NB = 'https://colab.research.google.com/drive/1URPntHhY0jY96psj9cK0Khrzq3gLb8KX'
CELL = {1: ('1. DB 생성', 'shop-db-create'), 2: ('2. 표 만들기', 'shop-tables'), 3: ('3. 자동 검증', 'shop-verify'),
        4: ('4. 웹앱 실행', 'shop-webapp'), 5: ('5. 삭제', 'shop-delete'), 'submit': ('제출', 'shop-submit')}
# 슬라이드(본문 첫 글자) → 버튼이 가리킬 셀
PAGE = [('요구사항 | 학생이 직접 확인할 네 가지', [3]), ('업무 영역 | 상품 화면에서 배송 조회까지', [4]),
        ('4.1. 주요 엔티티 정의 및 속성', [2]), ('4.2. 엔티티 간 관계 명시', [2]), ('4.3. 무결성 제약 조건', [2]),
        ('쿠팡 사례 | 주문목록에서 배송조회까지', [4]), ('5.1. 주요 트랜잭션 식별 및 프로세스', [3]),
        ('5.2. 트랜잭션 처리 및 동시성 제어', [3]), ('트랜잭션 | 마지막 마우스 1개 주문', [3]),
        ('Colab 실습 | 쇼핑몰 DB에서 웹앱까지', [1, 4]), ('제출 화면', ['submit']), ('실습 끝내기', [5])]


def txt(sl):
    return ' '.join(sh.text_frame.text for sh in sl.shapes if sh.has_text_frame)


def buttons(sl):
    out = []
    for sh in sl.shapes:
        if not sh.has_text_frame or not sh.text_frame.text.strip().startswith('Colab ·'):
            continue
        out.append(sh)
    return sorted(out, key=lambda s: s.left)


def set_button(sh, key):
    label, anchor = CELL[key]
    url = f'{NB}#scrollTo={anchor}'
    run = sh.text_frame.paragraphs[0].runs[0]
    run.text = f'Colab · {label}'
    for r in sh.text_frame.paragraphs[0].runs[1:]:
        r.text = ''
    # 글자 링크와 도형 클릭 링크가 같은 관계(rId)를 공유하므로 관계의 주소만 바꾼다
    part = sh.part
    rids = set()
    h = run._r.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}hlinkClick')
    if h is not None:
        rids.add(h.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'))
    try:
        hc = sh.click_action._hlink
        if hc is not None:
            rids.add(hc.rId)
    except Exception:
        pass
    rids.discard(None)
    if not rids:
        run.hyperlink.address = url
    from pptx.opc.constants import RELATIONSHIP_TYPE as RT
    R_ID = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
    for rid in rids:
        if rid in part.rels:
            part.rels[rid]._target = url
        else:                                            # 다른 쪽에서 복제한 버튼: 이 쪽에 새 링크 관계를 만들어 연결
            new = part.relate_to(url, RT.HYPERLINK, is_external=True)
            for el in sh._element.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}hlinkClick'):
                if el.get(R_ID) == rid:
                    el.set(R_ID, new)


def fix_notes(sl, keys):
    url = f'{NB}#scrollTo={CELL[keys[0]][1]}'
    for p in sl.notes_slide.notes_text_frame.paragraphs:
        for r in p.runs:
            for old in ('shop-run-guide', 'shop-aws-guide', 'shop-clean-guide', 'shop-run', 'shop-submit'):
                if f'{NB}#scrollTo={old}' in r.text:
                    r.text = r.text.replace(f'{NB}#scrollTo={old}', url)


template = None
for sl in prs.slides:
    if buttons(sl):
        template = buttons(sl)[0]
        break

done = []
for key_text, keys in PAGE:
    sl = next((s for s in prs.slides if key_text in txt(s)), None)
    if sl is None:
        print('  ! 슬라이드 없음:', key_text); continue
    bs = buttons(sl)
    if not bs and template is not None:                 # 버튼이 없는 쪽(4.3)은 같은 모양으로 복제
        el = copy.deepcopy(template._element)
        sl.shapes._spTree.append(el)
        bs = buttons(sl)
        bs[0].left, bs[0].top = Inches(0.98), Inches(6.66)
    for sh, key in zip(bs, keys):
        set_button(sh, key)
    fix_notes(sl, keys)
    done.append((key_text[:12], [CELL[k][0] for k in keys]))


def para_replace(sl, old, new):
    for sh in sl.shapes:
        if sh.has_text_frame:
            for p in sh.text_frame.paragraphs:
                if old in p.text and p.runs:
                    p.runs[0].text = p.text.replace(old, new)
                    for r in p.runs[1:]:
                        r.text = ''
                    return True
    return False


s13 = next(s for s in prs.slides if 'AWS 실습 범위' in txt(s))
para_replace(s13, 'Colab은 보안 비밀로 RDS에 IAM 인증하고, 웹 화면을 띄웁니다.',
             'Colab 보안 비밀(AWS 키·DB 비밀번호)만으로 AWS에 실습 RDS를 만들고, 실습 후 삭제합니다.')

s31 = next(s for s in prs.slides if 'Colab 실습 | 쇼핑몰 DB에서 웹앱까지' in txt(s))
para_replace(s31, '노트북에서 AWS 연결부터 실행한 뒤 실제 웹앱에서 주문과 취소를 실습합니다.',
             'AWS에 실습 RDS를 만들고 → 표·검증·웹앱으로 실습한 뒤 → RDS를 삭제합니다.')
tbl = next(sh for sh in s31.shapes if sh.has_table).table
ROWS = [('1. DB 생성', '보안 비밀에 AWS 키와 DB_PASSWORD 등록 → AWS에 RDS 생성(5~15분) → ④ 연결 확인'),
        ('2. 표 만들기', '표 5개와 관계(FK)를 만들고 ⑤ 출력으로 확인합니다.'),
        ('3. 자동 검증', '주문·품절·취소를 검증합니다. ⑥ 통과 = 검증 성공'),
        ('4. 웹앱 실행', '열린 웹앱에서 직접 주문·취소하고 제출 화면을 캡처합니다.'),
        ('5. 삭제', 'DELETE를 입력해 AWS의 실습 RDS를 삭제합니다 (요금 중지).')]
tr_list = tbl._tbl.tr_lst
while len(tbl.rows) < len(ROWS) + 1:                    # 행 추가: 마지막 행 복제
    tbl._tbl.append(copy.deepcopy(tr_list[-1]))
for i, (a, b) in enumerate(ROWS, start=1):
    for j, v in enumerate((a, b)):
        cell = tbl.cell(i, j)
        runs = cell.text_frame.paragraphs[0].runs
        runs[0].text = v
        for r in runs[1:]:
            r.text = ''
for row in list(tbl.rows)[1:]:
    row.height = Inches(0.5)
n31 = s31.notes_slide.notes_text_frame
n31.text = ('【슬라이드 핵심】 Colab 보안 비밀만으로 AWS에 실습 RDS를 만들고, 표·검증·웹앱으로 실습한 뒤 삭제한다. 각 교안 페이지의 Colab 버튼이 해당 셀로 이동한다.\n'
            '【강의 설명】 학생은 Colab 왼쪽 열쇠 아이콘에 AWS_ACCESS_KEY, AWS_SECRET_KEY, DB_PASSWORD(8자 이상, 새 RDS 관리자 비밀번호)를 등록하고 노트북 액세스를 켠다. '
            '1번 셀은 RDS가 없으면 AWS에 새로 만들고(5~15분, 진행 상태 표시) 보안 그룹에 현재 Colab IP만 허용한 뒤, AWS 공식 인증서로 TLS(verify-full) 접속해 ④ 연결 확인을 출력한다. '
            '2번 셀은 표 5개와 관계(⑤), 3번 셀은 주문·품절·취소 자동 검증(⑥ 통과), 4번 셀은 웹앱(⑦)을 연다. 제출 후 5번 셀에서 DELETE를 입력하면 RDS가 삭제되어 요금이 멈춘다. '
            '앞 셀을 건너뛰면 “1번 셀부터 실행하세요”처럼 안내하고 멈춘다. 출력에는 키·비밀번호가 표시되지 않는다.\n'
            f'【연결】 {NB}#scrollTo=shop-db-create')

s34 = next(s for s in prs.slides if '실습 끝내기' in txt(s))
para_replace(s34, 'Colab 3단계 정리 셀을 실행하고 DELETE LAB을 입력합니다.', 'Colab 5. 삭제 셀을 실행하고 DELETE를 입력합니다.')
para_replace(s34, '현재 런타임에서 만든 스키마와 표만 삭제합니다. 웹앱 미리보기도 종료됩니다.',
             '웹앱 미리보기를 끄고 AWS의 실습 RDS(cd12-shop-lab)를 삭제합니다.')
para_replace(s34, '별도로 만든 전용 RDS 인스턴스는 스냅샷 보존 여부를 확인한 뒤 AWS 콘솔에서 삭제합니다.',
             'RDS는 켜져 있는 동안 요금이 나오므로 제출 후 바로 삭제합니다. 다음 실습 때 1번 셀이 새로 만듭니다.')
n34 = s34.notes_slide.notes_text_frame
if '5. 삭제 셀' not in n34.text:
    n34.add_paragraph().text = ('【삭제】 5. 삭제 셀은 런타임을 다시 시작했어도 단독으로 실행된다. Colab 보안 비밀의 AWS 키로 실습 RDS를 찾아 DELETE 입력 시 삭제(최종 스냅샷 없음)한다. '
                                '삭제 요청 후 5~10분 뒤 사라지며, 이미 없으면 “이미 삭제됐습니다”를 출력한다.')
prs.save(out)
print('ok', done)
