"""Add CD12-3's final web assignment to the current PPTX and notebook."""
import argparse
import base64
import io
import json
import re
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from lxml import etree as E
from PIL import Image

parser=argparse.ArgumentParser()
parser.add_argument("deck",type=Path)
parser.add_argument("notebook",type=Path)
parser.add_argument("--hero",type=Path)
args=parser.parse_args()
home=Path(__file__).resolve().parent
nb=json.loads(args.notebook.read_text())
url="https://colab.research.google.com/drive/16zKCRFtxxvxd3m9DJeg2F73dIiQWhCVN#scrollTo=l-final-webapp"
starter=(home/"webapp_starter.py").read_text()
if args.hero:
    img=Image.open(args.hero).convert("RGB")
    img.thumbnail((1080,430))
    buf=io.BytesIO()
    img.save(buf,format="JPEG",quality=77,optimize=True)
    starter=starter.replace('HERO_IMAGE = ""','HERO_IMAGE = "data:image/jpeg;base64,'+base64.b64encode(buf.getvalue()).decode()+'"')

def new_cell(cid,kind,s):
    c={"id":cid,"cell_type":kind,"metadata":{"id":cid},"source":s.splitlines(keepends=True)}
    return c if kind=="markdown" else dict(c,execution_count=None,outputs=[])

for c in nb["cells"]:
    cid=c.get("id") or c["metadata"].get("id")
    s="".join(c["source"])
    if cid in {"l-intro","l-delete","l-delete-run"}:
        s=s.replace("57쪽","58쪽")
    if cid=="l-intro":
        row=next(x for x in s.splitlines() if x.startswith("| 8. 마무리"))
        s=s.replace(row,"| **과제 ③** | 상품 검색·카테고리·주문 조회 웹앱 완성, 실행 계획 확인 | 57쪽 |\n"+row)
    if cid=="l-physical-run":
        s=s.replace("→ 다음: 제출 후 8. 마무리(최종 삭제)","→ 다음: 과제 ③ 웹앱 완성·제출 후 8. 마무리(최종 삭제)")
    if cid=="l-submit":
        s=s.replace("과제 ①·② 결과(⑦·⑪)와","과제 ③ 웹앱 화면·실행 계획·제약 설명, 과제 ①·② 결과(⑦·⑪)와")
    c["source"]=s.splitlines(keepends=True)

pivot=next(i for i,c in enumerate(nb["cells"]) if (c.get("id") or c["metadata"].get("id"))=="l-submit")
nb["cells"][pivot:pivot]=[
    new_cell("l-final-webapp","markdown",(home/"assignment.md").read_text()),
    new_cell("l-final-webapp-run","code",starter),
    new_cell("l-final-webapp-plan","code",(home/"explain_assignment.py").read_text()),
]
(home/"updated.ipynb").write_text(json.dumps(nb,ensure_ascii=False,indent=1)+"\n")

with ZipFile(args.deck) as z:
    pkg={name:z.read(name) for name in z.namelist()}
P="http://schemas.openxmlformats.org/presentationml/2006/main"
R="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
def write(name,tree):
    pkg[name]=E.tostring(tree,encoding="UTF-8",xml_declaration=True,standalone=True)

def edit(name,mapping):
    root=E.fromstring(pkg[name])
    seen=set()
    for t in root.findall(".//{*}t"):
        if t.text in mapping:
            seen.add(t.text)
            t.text=mapping[t.text]
    assert seen==set(mapping),(name,set(mapping)-seen)
    write(name,root)
    return root

guide="ppt/slides/slide54.xml"
g=edit(guide,{
 "여성 액세서리몰: 12-2 주문 유지 → 제약·인덱스 적용 → 성능 비교 → 최종 삭제":
 "여성 액세서리몰 · 설계 적용 → 57쪽 웹앱 과제 → 제출 → 최종 삭제",
 "57쪽":"58쪽",
})
grel="ppt/slides/_rels/slide54.xml.rels"
rels=E.fromstring(pkg[grel])
rel_tag=rels[0].tag
E.SubElement(rels,rel_tag,Id="rIdFinalWebapp",Type=R+"/hyperlink",Target=url,TargetMode="External")
sub=next(t for t in g.findall(".//{*}t") if (t.text or "").startswith("여성 액세서리몰 · 설계 적용"))
run=sub.getparent()
ns=E.QName(sub).namespace
prop=run.find("{*}rPr")
if prop is None:
    prop=E.Element(f"{{{ns}}}rPr")
    run.insert(0,prop)
E.SubElement(prop,f"{{{ns}}}hlinkClick",{f"{{{R}}}id":"rIdFinalWebapp"})
write(guide,g)
write(grel,rels)

old_slide="ppt/slides/slide57.xml"
old_rel="ppt/slides/_rels/slide57.xml.rels"
new_num=1+max(int(m[1]) for k in pkg if (m:=re.fullmatch(r"ppt/slides/slide(\d+)\.xml",k)))
new_slide=f"ppt/slides/slide{new_num}.xml"
new_rel=f"ppt/slides/_rels/slide{new_num}.xml.rels"
pkg[new_slide]=pkg[old_slide]
edit(new_slide,{
 "실습 끝내기 | AWS RDS 최종 삭제 (12장 끝)":"최종 과제 ③ | 여성 액세서리몰 웹앱",
 "제출: 과제 ①·② 결과(⑦·⑪)와 5번 셀 인덱스·클러스터링 전/후 결과를 캡처합니다.":
 "상품 화면 · 귀걸이·목걸이 등 카테고리와 상품명으로 검색합니다. 카드에 가격과 재고를 표시합니다.",
 "Colab 8번 셀: DELETE 입력 후 RDS 식별자를 다시 입력합니다.":
 "주문 조회 · 주문·주문상세·상품을 키로 연결해 고객별 주문과 주문 당시 단가를 표시합니다.",
 "AWS의 실습 RDS(cd12-shop-lab)가 최종 스냅샷 없이 삭제됩니다. 12-1~12-3의 shop 데이터도 함께 지워집니다.":
 "설계 검증 · 재고나 외래키 제약이 막는 오류를 설명하고, 주문 조회 실행 계획과 인덱스의 관계를 설명합니다.",
 "런타임을 다시 시작했어도 이 셀만 실행하면 됩니다. 삭제 완료 메시지와 RDS 콘솔을 확인하세요.":
 "제출 · 상품 필터·주문 화면, 실행 계획, 제약 설명. 제출 자료를 확보한 뒤 다음 쪽의 최종 삭제를 진행합니다.",
 "※ STOP(중지)은 7일 뒤 자동으로 다시 시작되므로 12장이 끝나면 DELETE로 지웁니다 · 보안 그룹은 요금이 없어 남겨 둡니다":
 "※ 7번 셀까지 실행한 뒤 시작합니다. 화면 틀을 제공하며 학생은 두 조회 함수의 SQL을 작성합니다.",
 "Colab · 8. 마무리 (DELETE)":"Colab · 과제 ③ 웹앱",
 "※ 약어  AWS: Amazon Web Services (아마존 클라우드)  ·  RDS: Relational Database Service (관리형 관계형 데이터베이스 서비스)":
 "※ 약어  SQL: Structured Query Language (구조화 질의 언어)",
})
r=E.fromstring(pkg[old_rel])
for entry in list(r):
    typ=entry.get("Type","")
    if typ.endswith("/notesSlide"):
        r.remove(entry)
    elif typ.endswith("/hyperlink"):
        entry.set("Target",url)
write(new_rel,r)
edit(old_slide,{
 "제출: 과제 ①·② 결과(⑦·⑪)와 5번 셀 인덱스·클러스터링 전/후 결과를 캡처합니다.":
 "제출 자료 확인 · 과제 ①~③ 결과와 5번 셀의 인덱스·클러스터링 비교를 저장합니다.",
})
pname="ppt/presentation.xml"
prname="ppt/_rels/presentation.xml.rels"
pres=E.fromstring(pkg[pname])
rel=E.fromstring(pkg[prname])
rid=f"rIdSlide{new_num}FinalWeb"
E.SubElement(rel,rel[0].tag,Id=rid,Type=R+"/slide",Target=f"slides/slide{new_num}.xml")
lst=pres.find(f"{{{P}}}sldIdLst")
old_rid=next(x.get("Id") for x in rel if x.get("Target")=="slides/slide57.xml")
before=next(x for x in lst if x.get(f"{{{R}}}id")==old_rid)
assert lst.index(before)==56
lst.insert(lst.index(before),E.Element(f"{{{P}}}sldId",id=str(max(int(x.get("id")) for x in lst)+1),attrib={f"{{{R}}}id":rid}))
write(pname,pres)
write(prname,rel)
ctype="[Content_Types].xml"
types=E.fromstring(pkg[ctype])
n=next(x for x in types if x.get("PartName")=="/"+old_slide)
E.SubElement(types,n.tag,PartName="/"+new_slide,ContentType=n.get("ContentType"))
write(ctype,types)
with ZipFile(home/"updated.pptx","w",ZIP_DEFLATED) as z:
    for name,b in pkg.items():
        z.writestr(name,b)
