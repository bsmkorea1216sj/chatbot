"""Update the latest CD12 PPTX/ipynb in place locally, preserving slide parts/media.
Inputs part1..3.{pptx,ipynb}; outputs output/part1..3.*. No AWS calls.
"""
import json,re,copy
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from lxml import etree as E
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output'; OUT.mkdir(exist_ok=True)
NB_IDS=['1URPntHhY0jY96psj9cK0Khrzq3gLb8KX','1bUdKHLpCey3gCNt-3Qyx-8SCy9QCZfTY','16zKCRFtxxvxd3m9DJeg2F73dIiQWhCVN']
URLS=['https://colab.research.google.com/drive/'+x for x in NB_IDS]
REPLACE={
 '무선 마우스':'진주 귀걸이','접이식 키보드':'실버 목걸이','노트북 거치대':'리본 헤어핀',
 '린넨 셔츠':'체인 팔찌','와이드 팬츠':'큐빅 반지','캔버스 백':'플라워 브로치',
 '마우스':'귀걸이','여성 의류 및 관련 상품':'여성 액세서리 상품',
 '여성 의류':'여성 액세서리','미니 쇼핑몰':'액세서리몰','가상 쇼핑몰':'여성 액세서리몰',
 "'주변기기'":"'여성 액세서리'", "'의류'":"'팔찌·반지'", "'잡화'":"'브로치'",
 'S, M, L, XL':'체인 길이(cm)',
 '과정을 그만둘 때만 `DELETE`(완전 삭제)를 입력하세요. ':'',
 'DELETE는 과정을 그만둘 때만':'최종 삭제는 12-3 마지막 셀',
 '실습 후 삭제합니다.':'12-1·2에서는 중지하고, 12-3 마지막에 삭제합니다.',
 '인스턴스 요금 중지, 데이터 유지':'인스턴스 요금 중지, 저장공간·백업 비용 유지',
 '중지 중에는 인스턴스 요금이 멈추고 저장공간 요금만 나옵니다.':'중지 중에도 저장공간·백업 요금은 발생할 수 있습니다.',
}
def repl(s):
 for a,b in REPLACE.items():s=s.replace(a,b)
 return s

# Known seed rows only: preserve all IDs, historical prices, stock and user products.
REBRAND='''
# 이전 차시의 예제 상품을 여성 액세서리로 전환합니다. 주문·가격·재고는 보존합니다.
with transaction({schema}) as cur:
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema=%s AND table_name='products' AND column_name IN ('id','product_id','name','product_name')", ({schema},))
    product_cols = {{r['column_name'] for r in cur.fetchall()}}
    id_col = 'product_id' if 'product_id' in product_cols else 'id'
    name_col = 'product_name' if 'product_name' in product_cols else 'name'
    seeds = [(101,'무선 마우스','진주 귀걸이','귀걸이'), (102,'접이식 키보드','실버 목걸이','목걸이'),
             (103,'노트북 거치대','리본 헤어핀','헤어핀'), (201,'린넨 셔츠','체인 팔찌','팔찌'),
             (202,'와이드 팬츠','큐빅 반지','반지'), (203,'캔버스 백','플라워 브로치','브로치')]
    for pid, old_name, new_name, category in seeds:
        cur.execute(sql.SQL("UPDATE products SET {{}}=%s WHERE {{}}=%s AND {{}} IN (%s,%s)").format(
            sql.Identifier(name_col), sql.Identifier(id_col), sql.Identifier(name_col)),
            (new_name, pid, old_name, new_name))
        cur.execute("SELECT 1 FROM information_schema.columns WHERE table_schema=%s AND table_name='products' AND column_name='category'", ({schema},))
        if cur.fetchone():
            cur.execute(sql.SQL("UPDATE products SET category=%s WHERE {{}}=%s AND {{}}=%s").format(
                sql.Identifier(id_col), sql.Identifier(name_col)), (category,pid,new_name))
'''
ROADMAP='''
## 여성 액세서리 쇼핑몰 · 12장 연속 실습

| 파트 | 같은 쇼핑몰에서 하는 일 | 종료 방식 |
|---|---|---|
| [12-1: DB·웹앱]({u0}) | 진주 귀걸이(101) 1개 주문 → 품절 → 취소·재고 복구, 웹 화면 확인 | STOP, 데이터 유지 |
| [12-2: 개념 모델]({u1}) | 같은 상품·주문을 7개 엔티티로 확장, 결제·배송·리뷰와 CRUD 확인 | STOP, 데이터 유지 |
| [12-3: 논리·물리 모델]({u2}) | 같은 shop의 키·제약·인덱스 적용, 별도 대량 데이터로 성능 비교 | 마지막 8번 셀에서 최종 DELETE |

**이어하기 조건:** 세 파일에서 같은 AWS 계정·리전·`DB_INSTANCE_ID`(기본 `cd12-shop-lab`)·`DB_PASSWORD`를 사용합니다. 각 파일의 1번 셀부터 순서대로 실행하세요. Colab 런타임이 달라도 RDS의 `shop` 데이터는 유지됩니다. 앞 차시를 생략해도 예제는 생성되지만, 앞 차시의 주문 이력은 생기지 않습니다.

**공통 상품:** 101 진주 귀걸이 19,900원(초기 재고 1), 102 실버 목걸이 32,900원(5), 103 리본 헤어핀 24,900원(3). 12-2부터 팔찌·반지·브로치를 추가합니다. 귀걸이 1개는 한 쌍을 판매하는 상품 단위입니다. 가격·재고는 학습용 가상 값입니다. 기존 데이터를 이어 쓰면 남아 있는 재고를 사용합니다.
'''.format(u0=URLS[0],u1=URLS[1],u2=URLS[2])

def notebooks():
 for p in (1,2,3):
  n=json.loads((ROOT/f'part{p}.ipynb').read_text())
  for c in n['cells']:
   c['id']=c.get('id') or c.get('metadata',{}).get('id')
   s=repl(''.join(c['source']))
   cid=c['id']
   if s.strip()=='hf':
    c['cell_type']='markdown';c.pop('execution_count',None);c.pop('outputs',None)
    s='> 12-3은 12-2의 여성 액세서리몰 DB를 이어받습니다. 아래 안내를 확인하고 1번 셀부터 실행하세요.'
   if cid in ('shop-intro','m-intro','l-intro'):
    s=s.replace('미니','여성 액세서리')+'\n'+ROADMAP
   if c['cell_type']=='code':
    # Unexpanded part1 must not invite early deletion after completing part2.
    s=s.replace('12-1을 처음부터 다시 하려면 5번 셀에서 DELETE 후 1번 셀부터 실행하세요.',
                '기존 주문을 보존하려면 12-2 또는 12-3에서 이어서 실행하세요. 초기화가 필요하면 12-3 마지막 셀에서 최종 삭제 후 새로 시작합니다.')
    if cid=='shop-tables-run':
     marker='with transaction(shop_schema) as cur:\n    cur.execute("SELECT id, name, price, stock FROM products ORDER BY id")'
     assert marker in s
     s=s.replace(marker,REBRAND.format(schema='SHOP_SCHEMA')+'\n'+marker)
     # Brand the actual app title and its UI (text only).
     s=s.replace('<strong>액세서리몰</strong>','<strong>여성 액세서리몰</strong>')
    if cid in ('m-tables-run','l-schema-run'):
     marker='model_schema = MODEL_SCHEMA' if p==2 else 'logical_schema = MODEL_SCHEMA'
     assert marker in s
     s=s.replace(marker,REBRAND.format(schema='MODEL_SCHEMA')+'\n'+marker)
    if p<3 and 'delete-run' in cid:
     s=s.replace('STOP, 과정을 그만두고 완전히 지우려면 DELETE','STOP')
     s=re.sub(r'        elif answer == "DELETE":\n.*?(?=        else:)', '', s, flags=re.S)
     assert 'delete_db_instance' not in s
    if p==3 and 'delete-run' in cid:
     s=s.replace('status = rds.describe_db_instances(DBInstanceIdentifier=instance)["DBInstances"][0]["DBInstanceStatus"]',
      'db = rds.describe_db_instances(DBInstanceIdentifier=instance)["DBInstances"][0]\n        status = db["DBInstanceStatus"]')
     s=s.replace('        elif answer == "DELETE":\n            rds.delete_db_instance', '''        elif answer == "DELETE":
            tags = {t['Key']: t['Value'] for t in rds.list_tags_for_resource(ResourceName=db['DBInstanceArn'])['TagList']}
            if tags.get('course') != 'cd12-shop-lab':
                raise SystemExit('실습 course 태그가 없어 자동 삭제를 멈춥니다. RDS 콘솔에서 대상을 확인하세요.')
            if db.get('DeletionProtection'):
                raise SystemExit('삭제 방지가 켜져 있습니다. RDS 콘솔에서 대상을 확인하세요.')
            print(f'삭제 대상: {instance} / {rds.meta.region_name} / shop 전체 데이터. 최종 스냅샷을 만들지 않습니다.')
            if input('위 RDS 식별자를 정확히 다시 입력하세요: ').strip() != instance:
                raise SystemExit('식별자가 다릅니다. 삭제하지 않았습니다.')
            if status not in ('available', 'stopped', 'failed', 'incompatible-restore', 'incompatible-network'):
                raise SystemExit(f'현재 상태({status})를 확인하고 잠시 뒤 재실행하세요.')
            rds.delete_db_instance''')
     s=s.replace('5~10분 뒤 사라지며 요금이 멈춥니다.', '삭제 완료 후 이 인스턴스의 요금이 종료됩니다.')
     s += '''\n# 삭제 완료 여부를 다시 확인합니다. 재실행 시 이미 없으면 성공으로 안내합니다.
if not _secret("DB_HOST") and globals().get("answer") == "DELETE":
    from botocore.exceptions import WaiterError
    try:
        rds.get_waiter('db_instance_deleted').wait(DBInstanceIdentifier=instance, WaiterConfig={'Delay':30,'MaxAttempts':60})
        print('확인 완료: 실습 RDS가 삭제됐습니다. 기존 수동 스냅샷·다른 AWS 리소스 비용은 콘솔에서 별도로 확인하세요.')
    except WaiterError:
        print('아직 삭제 중이거나 상태 확인에 실패했습니다. RDS 콘솔에서 삭제 완료 여부를 확인하세요.')
'''
    c['execution_count']=None;c['outputs']=[]
   if c['cell_type']=='markdown' and cid in ('shop-delete','m-delete','l-delete'):
    s=s.replace('`DELETE`를 입력하면', '`DELETE`와 대상 RDS 식별자를 차례로 입력하면')
    s=s.replace('**최종 삭제**되어 요금이 멈춥니다', '**최종 삭제**됩니다. 삭제 완료 후 이 인스턴스의 사용 요금이 종료됩니다')
    s+='\n\nAWS 안내: [RDS 중지·7일 후 자동 시작](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_StopInstance.html) · [RDS 삭제와 백업](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_DeleteInstance.html). 중지 중에도 저장공간·백업 비용이 발생할 수 있고, 기존 수동 스냅샷은 별도로 확인합니다.\n'
   c['source']=s.splitlines(keepends=True)
  # Navigation stays inside existing intro/finish cells, anchors remain stable.
  for c in n['cells']:
   if c['cell_type']=='markdown' and c['id'] in ('shop-delete','m-delete'):
    c['source']+=['\n\n다음 실습: [12-'+str(p+1)+' 여성 액세서리몰 이어하기]('+URLS[p]+')\n']
  (OUT/f'part{p}.ipynb').write_text(json.dumps(n,ensure_ascii=False,indent=1)+'\n')

NS={'a':'http://schemas.openxmlformats.org/drawingml/2006/main','p':'http://schemas.openxmlformats.org/presentationml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}

def patch_decks():
 for p in (1,2,3):
  with ZipFile(ROOT/f'part{p}.pptx') as z:
   parts={i.filename:z.read(i.filename) for i in z.infolist()}
  changes=[]
  for fn,b in list(parts.items()):
   if not re.match(r'ppt/(slides/slide|notesSlides/notesSlide)\d+.xml$',fn):continue
   root=E.fromstring(b);changed=False
   for t in root.findall('.//a:t',NS):
    old=t.text or '';new=repl(old)
    if old=='시나리오 기반 설계 실습':new='여성 액세서리몰 설계 실습'
    if p==1 and fn=='ppt/slides/slide6.xml':
     new=new.replace('목표 · 상품을 고르고 주문한 뒤 배송 상태까지 확인하는 웹앱을 만든다.',
      '목표 · 귀걸이·목걸이·헤어핀을 주문하고 배송 상태를 확인한다.')
    if p==1 and fn=='ppt/slides/slide31.xml':
     new=new.replace('AWS에 RDS 생성 → 표·검증·웹앱 실습 → STOP으로 중지 (12-2에서 이어서)',
      '여성 액세서리몰: 12-1 웹앱·STOP → 12-2 결제·리뷰 → 12-3 최적화·최종 삭제')
    if p==2 and fn=='ppt/slides/slide29.xml':
     new=new.replace('12-1의 RDS·shop 데이터를 이어받아 → 개념 모델 확장·과제·퀴즈·CRUD 확인 → 중지(STOP)',
      '여성 액세서리몰: 12-1 상품·주문 유지 → 결제·배송·리뷰 확장 → STOP → 12-3')
    if p==3 and fn=='ppt/slides/slide56.xml':
     new=new.replace('12-2의 RDS·shop을 이어받아 → 릴레이션 스키마·제약·성능 설계 확인 → 최종 삭제',
      '여성 액세서리몰: 12-2 주문 유지 → 제약·인덱스 적용 → 성능 비교 → 최종 삭제')
    new=new.replace('5~10분 뒤 RDS 콘솔에서 사라진 것을 확인하세요.', '삭제 완료 메시지와 RDS 콘솔을 확인하세요.')
    new=new.replace('스냅샷 없이 삭제되어 요금이 멈춥니다.', '최종 스냅샷 없이 삭제됩니다.')
    if p==3 and fn=='ppt/slides/slide59.xml':
     new=new.replace('Colab 8. 마무리 셀을 실행하고 DELETE를 입력합니다.',
      'Colab 8번 셀: DELETE 입력 후 RDS 식별자를 다시 입력합니다.')
    if new!=old:t.text=new;changed=True
   if changed:
    parts[fn]=E.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True);changes.append(fn)
  # Fix observed unreadable Korean glyphs on the inherited goal/summary pages.
  # Keep each existing paragraph, run, font size and layout; set explicit CJK face.
  if p in (2,3):
   for sn in (3,27 if p==2 else 54):
    fn=f'ppt/slides/slide{sn}.xml';root=E.fromstring(parts[fn])
    for sp in root.findall('.//p:sp',NS):
     if not sp.findall('.//a:t',NS):continue
     for run in sp.findall('.//a:r',NS):
      pr=run.find('a:rPr',NS)
      if pr is None:pr=E.Element('{'+NS['a']+'}rPr');run.insert(0,pr)
      ea=pr.find('a:ea',NS)
      if ea is None:ea=E.SubElement(pr,'{'+NS['a']+'}ea')
      ea.set('typeface','Noto Sans CJK KR')
      for fill in pr.findall('a:solidFill',NS):pr.remove(fill)
      fill=E.SubElement(pr,'{'+NS['a']+'}solidFill')
      E.SubElement(fill,'{'+NS['a']+'}srgbClr',val='FFFFFF' if sn==3 else '111111')
    parts[fn]=E.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True)
  # Link next-part guidance inside existing, preserved text boxes. No shape overlap.
  if p<3:
   fn=f'ppt/slides/slide{34 if p==1 else 31}.xml';root=E.fromstring(parts[fn]);relfn=fn.replace('slides/','slides/_rels/')+'.rels'
   rr=E.fromstring(parts[relfn]);rns='http://schemas.openxmlformats.org/package/2006/relationships'
   rid='rIdNextAccessories';E.SubElement(rr,'{'+rns+'}Relationship',Id=rid,Type=NS['r']+'/hyperlink',Target=URLS[p],TargetMode='External')
   candidates=[t for t in root.findall('.//a:t',NS) if ('다시 시작해' in (t.text or '') or '다음 수업' in (t.text or '') or '12-2의 1번' in (t.text or ''))]
   if not candidates:
    candidates=[t for t in root.findall('.//a:t',NS) if ('12-'+str(p+1)) in (t.text or '') and '※' not in t.text]
   if candidates:
    run=candidates[0].getparent();pr=run.find('a:rPr',NS)
    if pr is None:pr=E.Element('{'+NS['a']+'}rPr');run.insert(0,pr)
    for h in pr.findall('a:hlinkClick',NS):pr.remove(h)
    E.SubElement(pr,'{'+NS['a']+'}hlinkClick',{'{'+NS['r']+'}id':rid})
   parts[fn]=E.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True)
   parts[relfn]=E.tostring(rr,xml_declaration=True,encoding='UTF-8',standalone=True)
  # Notes supplement the scenario without changing any original lecturer notes.
  for fn,b in list(parts.items()):
   if not re.match(r'ppt/notesSlides/notesSlide\d+.xml$',fn):continue
   root=E.fromstring(b)
   bodies=[sp for sp in root.findall('.//p:sp',NS) if sp.find('.//p:ph[@type="body"]',NS) is not None]
   if not bodies:continue
   tb=bodies[0].find('p:txBody',NS)
   if tb is None:continue
   para=E.SubElement(tb,'{'+NS['a']+'}p');run=E.SubElement(para,'{'+NS['a']+'}r');t=E.SubElement(run,'{'+NS['a']+'}t')
   t.text='【연결】여성 액세서리몰 공통 사례: 진주 귀걸이(101)·실버 목걸이(102)·리본 헤어핀(103). 12-1 DB·웹앱, 12-2 결제·배송·리뷰 확장, 12-3 논리·물리 설계. 같은 RDS와 shop 데이터를 유지하며 최종 삭제는 12-3 마지막 셀에서만 수행한다. 상품·가격은 학습용 가상 데이터다.'
   parts[fn]=E.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True)
  with ZipFile(OUT/f'part{p}.pptx','w',ZIP_DEFLATED) as z:
   for fn,b in parts.items():z.writestr(fn,b)
  print('deck',p,'changed',len(changes),'XML parts; preserved media')

if __name__=='__main__':notebooks();patch_decks()
