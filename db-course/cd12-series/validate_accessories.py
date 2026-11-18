"""Offline regression for changed CD12 cleanup controls, code and Colab anchors."""
import json,ast,re,sys,types,builtins
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile
from lxml import etree as E
ROOT=Path(__file__).resolve().parent/'output'
notebooks=[json.loads((ROOT/f'part{i}.ipynb').read_text()) for i in (1,2,3)]
for p,n in enumerate(notebooks,1):
 ids={c['id'] for c in n['cells']};assert len(ids)==len(n['cells'])
 for c in n['cells']:
  if c['cell_type']=='code':ast.parse('\n'.join('# '+l if l.startswith(('!','%')) else l for l in ''.join(c['source']).splitlines()))
 with ZipFile(ROOT/f'part{p}.pptx') as z:
  original=ZipFile(ROOT.parent/f'part{p}.pptx')
  for f in original.namelist():
   if f.startswith('ppt/media/') or re.match(r'ppt/(slideMasters|slideLayouts|theme)/',f):assert original.read(f)==z.read(f),f
  for f in z.namelist():
   if re.match(r'ppt/slides/_rels/slide\d+.xml.rels$',f):
    for r in E.fromstring(z.read(f)):
     target=r.get('Target','');a=re.search(r'#scrollTo=([^&]+)',target)
     if a:assert a[1] in ids,(p,target)
 print(f'Part {p}: syntax, unique anchors, links, media/theme preservation OK')

class NotFound(Exception):pass
class WaiterError(Exception):pass
class FakeRDS:
 def __init__(self,status='available',tag=True,exists=True):
  self.calls=[];self.status=status;self.tag=tag;self.exists=exists;self.exceptions=types.SimpleNamespace(DBInstanceNotFoundFault=NotFound);self.meta=types.SimpleNamespace(region_name='test')
 def describe_db_instances(self,**kw):
  if not self.exists:raise NotFound()
  return {'DBInstances':[{'DBInstanceStatus':self.status,'DBInstanceArn':'test','DeletionProtection':False}]}
 def list_tags_for_resource(self,**kw):return {'TagList':[{'Key':'course','Value':'cd12-shop-lab'}] if self.tag else []}
 def stop_db_instance(self,**kw):self.calls.append(('stop',kw))
 def delete_db_instance(self,**kw):self.calls.append(('delete',kw))
 def get_waiter(self,name):return self
 def wait(self,**kw):self.calls.append(('wait',kw))
def run(p,answers=(),secrets=None,**kw):
 r=FakeRDS(**kw);s={'AWS_ACCESS_KEY':'fake','AWS_SECRET_KEY':'fake'};s.update(secrets or {})
 modules={'boto3':types.SimpleNamespace(Session=lambda **k:types.SimpleNamespace(client=lambda t:r)),
 'google':types.ModuleType('google'),'google.colab':types.SimpleNamespace(userdata=types.SimpleNamespace(get=lambda k:s.get(k))),
 'botocore':types.ModuleType('botocore'),'botocore.exceptions':types.SimpleNamespace(WaiterError=WaiterError)}
 code=''.join(next(c['source'] for c in notebooks[p-1]['cells'] if c['id'] in ('shop-delete-run','m-delete-run','l-delete-run')))
 answers=iter(answers)
 with patch.dict(sys.modules,modules),patch.object(builtins,'input',lambda prompt:next(answers)),patch.object(builtins,'print',lambda *a,**k:None):
  try:exec(compile(code,'cleanup','exec'),{})
  except SystemExit:pass
 return r.calls
for p in (1,2):
 assert [x[0] for x in run(p,['STOP'])]==['stop']
 assert not run(p,['DELETE'])
 assert not run(p,['STOP'],status='stopped')
 assert not run(p,secrets={'DB_HOST':'shared'})
 assert not run(p,exists=False)
assert [x[0] for x in run(3,['DELETE','cd12-shop-lab'])]==['delete','wait']
assert not run(3,['DELETE','wrong'])
assert not run(3,['DELETE'],tag=False)
assert not run(3,secrets={'DB_HOST':'shared'})
assert not run(3,exists=False)
assert not run(3,[''])
print('Cleanup: 16 offline cases passed; no AWS calls made')
# Execute only the added portable UPDATE migration on SQLite fixtures.
# This does not claim to validate the original PostgreSQL DDL or AWS runtime.
import sqlite3,contextlib
class SQL(str):
 def format(self,*args):return SQL(str(self).format(*args))
class Identifier(str):pass
for part in (1,2,3):
 name_col='product_name' if part==3 else 'name';id_col='id' if part==1 else 'product_id'
 db=sqlite3.connect(':memory:');db.execute(f'CREATE TABLE products({id_col} INTEGER PRIMARY KEY,{name_col} TEXT,price INT,stock INT'+(')' if part==1 else ',category TEXT)'))
 rows=[(101,'무선 마우스',999,0),(102,'강의자가 등록한 상품',32900,4),(103,'리본 헤어핀',24900,2)]
 db.executemany('INSERT INTO products VALUES ('+','.join('?' for _ in range(4 if part==1 else 5))+')',[r if part==1 else r+('기존',) for r in rows])
 class Cursor:
  def execute(self,q,args=()):
   q=str(q)
   if 'information_schema.columns' in q:
    self.rows=([{'column_name':id_col},{'column_name':name_col}] if ' IN (' in q else ([{'one':1}] if part>1 else []))
   else:db.execute(q.replace('%s','?'),args);self.rows=[]
  def fetchall(self):return self.rows
  def fetchone(self):return self.rows[0] if self.rows else None
 @contextlib.contextmanager
 def transaction(schema):yield Cursor()
 source=''.join(next(c['source'] for c in notebooks[part-1]['cells'] if c['id'] in ('shop-tables-run','m-tables-run','l-schema-run')))
 start=source.index('# 이전 차시의 예제 상품');end=source.index('\n\n',source.index('(category,pid,new_name))',start))
 env={'transaction':transaction,'sql':types.SimpleNamespace(SQL=SQL,Identifier=Identifier),'SHOP_SCHEMA':'shop','MODEL_SCHEMA':'shop'}
 for _ in range(2):exec(source[start:end],env)
 after=db.execute('SELECT * FROM products ORDER BY 1').fetchall()
 assert after[0][1:4]==('진주 귀걸이',999,0)
 assert after[1][1:4]==('강의자가 등록한 상품',32900,4)
 assert after[2][1:4]==('리본 헤어핀',24900,2)
 if part>1:assert after[0][4]=='귀걸이' and after[1][4]=='기존' and after[2][4]=='헤어핀'
print('Seed migration: all three column layouts preserve price/stock/custom products; rerun OK (SQLite fixture)')
