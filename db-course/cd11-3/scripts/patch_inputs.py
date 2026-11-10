"""input() 방식 미션을 기존(강의자가 실행·수정한) 노트북과 교안에 반영.
python patch_inputs.py <기존.ipynb> <새 생성.ipynb> <출력.ipynb> <기존.pptx> <출력.pptx>"""
import json, sys
from pptx import Presentation
from pptx.util import Pt
from pptx.dml.color import RGBColor

old_nb, gen_nb, out_nb, in_pptx, out_pptx = sys.argv[1:6]

# ── 노트북: 미션 관련 셀만 교체 (셀 ID·다른 셀·출력 유지)
old, gen = json.load(open(old_nb)), json.load(open(gen_nb))
src = lambda c: ''.join(c['source']) if isinstance(c['source'], list) else c['source']
gmd = {c['metadata'].get('id'): i for i, c in enumerate(gen['cells']) if c['metadata'].get('id', '').startswith('mission_')}
changed = []
for i, c in enumerate(old['cells']):
    cid = c['metadata'].get('id', '')
    if i == 0 and src(c).startswith('# CD11-3'):
        c['source'] = gen['cells'][0]['source']; changed.append('intro')
    elif c['cell_type'] == 'code' and src(c).startswith('# 미션 확인 함수'):
        g = next(x for x in gen['cells'] if x['cell_type'] == 'code' and src(x).startswith('# 미션 확인 함수'))
        c['source'] = g['source']; c['outputs'] = []; c['execution_count'] = None; changed.append('checks')
    elif cid in gmd:
        c['source'] = gen['cells'][gmd[cid]]['source']
        nxt = old['cells'][i + 1]
        assert nxt['cell_type'] == 'code', cid
        nxt['source'] = gen['cells'][gmd[cid] + 1]['source']; nxt['outputs'] = []; nxt['execution_count'] = None
        changed.append(cid)
json.dump(old, open(out_nb, 'w'), ensure_ascii=False, indent=1)
print('notebook cells replaced:', changed)

# ── 교안: Colab 안내(16)·미션 정답(19·20) 문구를 입력값 형식으로
NAVY, TXT = RGBColor(0x10, 0x29, 0x50), RGBColor(0x1A, 0x23, 0x32)
prs = Presentation(in_pptx)
S = lambda n: prs.slides[n - 1]
done, missed = [], []


def find(s, start):
    return next((sh for sh in s.shapes if sh.has_text_frame and sh.text_frame.text.strip().startswith(start)), None)


def set_first(s, start, text):
    sh = find(s, start)
    if sh is None:
        missed.append(start); return
    r = sh.text_frame.paragraphs[0].runs
    r[0].text = text
    for x in r[1:]:
        x.text = ''
    done.append(start[:12])


def set_card(s, start, title, lines):
    sh = find(s, start)
    if sh is None:
        missed.append(start); return
    tf = sh.text_frame
    ps = tf.paragraphs
    ps[0].runs[0].text = title
    for x in ps[0].runs[1:]:
        x.text = ''
    size = ps[1].runs[0].font.size if len(ps) > 1 and ps[1].runs else Pt(12)
    for p in ps[1:]:
        p._p.getparent().remove(p._p)
    for ln in lines:
        p = tf.add_paragraph(); p.alignment = 1; p.space_before = Pt(2)
        r = p.add_run(); r.text = ln; r.font.size = size; r.font.color.rgb = TXT
        r.font.name = 'Malgun Gothic' if ln.startswith('→') else 'Courier New'
    done.append(start[:12])


set_first(S(16), '교안의 🎯 버튼', '교안 🎯 버튼 ↔ 노트북 🎯 미션 셀 · 실행 후 입력칸에 답을 넣으면 ✅/❌로 확인합니다.')
sh = find(S(16), '① 테이블 만들기')
if sh is not None:
    for p in sh.text_frame.paragraphs:
        for r in p.runs:
            r.text = r.text.replace('PK·FK 빈칸 채우기', 'PK·FK 정하기')
set_first(S(19), 'Colab에서 ❌가', 'Colab 입력칸에 넣을 값입니다. ❌가 나오면 이 페이지와 비교하세요.')
set_card(S(19), '미션 2 · PK·FK', '미션 2 · PK·FK 입력값', ['① orders', '② menu', '③ order_id, menu_id', '④ orders(order_id)',
         '→ 주문상세는 두 키를 합친 복합 PK, 결제는 주문을 가리킨다'])
set_card(S(19), '미션 3 · 계산으로', '미션 3 · 계산식 입력값', ['① SUM(m.unit_price * i.qty)', '② SUM(m.unit_price * i.qty) / 11',
         '→ 합계 5,500 · 부가세 500 (영수증과 일치)'])
set_card(S(20), '미션 4 · 나눠 낸', '미션 4 · 결제 입력값', ['① 카드 · 3000', '② 현금 · 2500', '→ 결제 2행 · 합계 5,500 = 주문 합계'])
set_card(S(20), '미션 5 · 다중 선택', '미션 5 · 입력값', ['① F4   (대학(석사))', '② f.field_name', '→ 어학연수 1 · 대학(학사) 1 · 대학(석사) 1'])
set_card(S(20), '📝 과제', '📝 과제 · 회원·포인트 확장 (입력칸 ①~④)', [
    '① member_id TEXT PRIMARY KEY, card_no TEXT, points INTEGER',
    '② order_id TEXT REFERENCES orders(order_id), member_id TEXT REFERENCES members(member_id),',
    '   earned INTEGER, PRIMARY KEY (order_id, member_id)',
    "③ 'CJ5505', '010****5505', 384      ④ 'B0001', 'CJ5505', 28"])
prs.save(out_pptx)
print('deck updated:', done, '| not found:', missed)
