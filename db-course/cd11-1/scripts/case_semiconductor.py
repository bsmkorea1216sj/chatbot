"""11-1 보강본 6쪽 사례를 'Palantir × 반도체 공정 데이터(Athinia)'로 교체, 5쪽 사례 연결 문구 수정.
python case_semiconductor.py <in.pptx> <out.pptx>   (서식 유지: 문단별 첫 run만 교체)"""
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

prs = Presentation(sys.argv[1])
S5, S6 = prs.slides[4], prs.slides[5]


def by_text(s, start):
    return next(sh for sh in s.shapes if sh.has_text_frame and sh.text_frame.text.strip().startswith(start))


def set_paras(sh, texts):
    ps = sh.text_frame.paragraphs
    assert len(ps) == len(texts), (sh.shape_id, len(ps), len(texts))
    for p, t in zip(ps, texts):
        p.runs[0].text = t
        for r in p.runs[1:]:
            r.text = ''


set_paras(by_text(S5, '사례 연결'), ['사례 연결: Palantir 반도체 공정 데이터(Athinia) 사례로 현실 세계 → 개념 세계 → 컴퓨터 세계를 이어서 확인'])

set_paras(by_text(S6, '데이터의 구분 사례'), ['데이터의 구분 사례 · Palantir와 반도체 공정 데이터'])
set_paras(by_text(S6, '공개 보도 기반'), [
    '공개 발표 기반 사례 · Athinia',
    'Merck KGaA·Palantir의 반도체 데이터 협업 플랫폼(2021) — Micron이 공급사와 공정·소재 데이터 공유에 도입(2022)'])
set_paras(by_text(S6, '1 현실 세계'), [
    '1 현실 세계', '반도체 팹의 실제 대상과 사건',
    '• 웨이퍼·로트·공정 장비', '• 소재 배치(포토레지스트 등)·공급사', '• 공정 진행·결함 발생·수율 변화',
    '예: 같은 소재도 납품 배치마다 품질이 조금씩 달라 팹 수율에 영향'])
set_paras(by_text(S6, '2 개념 세계'), [
    '2 개념 세계', '업무 의미로 추상화한 객체',
    '• Wafer / Lot / Tool / ProcessStep', '• MaterialBatch / Supplier', '• 관계: 로트–장비, 로트–소재',
    'Palantir Foundry Ontology 관점: 객체, 속성, 링크, 액션으로 공정 지도를 만든다'])
set_paras(by_text(S6, '3 컴퓨터 세계'), [
    '3 컴퓨터 세계', 'DB·분석 시스템이 처리하는 데이터',
    '• 장비 센서·계측·검사 레코드', '• lot_id, batch_id, 시간, 결함 수', '• 수율(%)과 품질 예측 점수',
    '예: Athinia(Foundry 기반)에서 제조사·공급사가 데이터를 공유해 수율·품질 분석'])
set_paras(by_text(S6, '수업 연결'), [
    '수업 연결',
    '같은 웨이퍼 로트도 현실 세계에서는 ‘웨이퍼·장비·소재’, 개념 세계에서는 ‘객체·속성·관계’, 컴퓨터 세계에서는 ‘레코드·필드·수율 값’으로 표현이 달라진다.'])

src = by_text(S6, '출처')
set_paras(src, ['출처: Merck KGaA 보도자료(2021.12.07, Athinia 출범·Palantir Foundry 기반), Micron·Athinia 보도자료(PR Newswire, 2022.07), ASNA·Athinia 보도자료(2024.07)'])
src.top, src.height, src.width = Inches(6.86), Inches(0.3), Inches(10.9)

# 약어·용어 주석: 출처 줄 위, 본문(수업 연결 상자) 아래
if not any(sh.has_text_frame and sh.text_frame.text.startswith('※') for sh in S6.shapes):
    tb = S6.shapes.add_textbox(Inches(0.55), Inches(6.58), Inches(12.1), Inches(0.26))
    tf = tb.text_frame; tf.word_wrap = True
    tf.margin_top = tf.margin_bottom = Inches(0)
    r = tf.paragraphs[0].add_run()
    r.text = '※ 팹(Fab): Fabrication plant (반도체 제조 공장) · 로트(Lot): 같은 공정을 함께 거치는 웨이퍼 묶음 · 수율(Yield): 투입 대비 정상 칩 비율'
    r.font.size = Pt(10.5); r.font.name = 'Malgun Gothic'; r.font.color.rgb = RGBColor(0x3A, 0x44, 0x5C)

S6.notes_slide.notes_text_frame.text = (
    '【슬라이드 핵심】 같은 반도체 공정 데이터가 현실 세계(웨이퍼·장비·소재) → 개념 세계(객체·속성·관계) → 컴퓨터 세계(레코드·필드·수율 값)로 표현이 바뀐다.\n'
    '【강의 설명】 Athinia는 Merck KGaA와 Palantir가 2021년 12월 만든 반도체 데이터 협업 플랫폼으로 Palantir Foundry 위에서 동작한다. '
    '반도체 제조사와 소재 공급사가 데이터 소유권을 유지한 채 공정·소재 데이터를 공유·분석해 수율과 품질을 높이는 것이 목표다. '
    'Micron은 2022년 7월 공급사와 공정·제조 데이터를 공유하는 데 Athinia를 도입한다고 발표했다. '
    '현실의 소재 배치·로트·장비를 개념 세계의 MaterialBatch·Lot·Tool 객체와 링크로 정의하고, 컴퓨터 세계에서는 batch_id·lot_id·센서값·결함 수·수율 레코드로 저장한다는 흐름을 짚는다.\n'
    '【연결】 5쪽 데이터의 구분, 7쪽 개체·개체 타입·레코드 타입, 9쪽 Palantir Ontology\n'
    '【출처】 Merck KGaA 보도자료 “Athinia to Accelerate the Use of AI and Big Data to Solve Critical Semiconductor Challenges”(2021.12.07); '
    'PR Newswire “Micron to Select Athinia for Pioneering Data Collaboration”(2022.07); ASNA·Athinia 보도자료(2024.07)')

prs.save(sys.argv[2])
print('ok')
