"""12-1 → 12-2 → 12-3 이어하기 (최종 삭제는 12-3 마지막) — CD12-1 노트북 수정.
 - 2번 셀: 웹앱 실습 데이터를 고정 스키마 `shop`에 저장(있으면 이어서 사용) → 12-2가 이어받음
 - 5번 셀: '삭제' → '마무리': STOP(기본, RDS 중지·다음 수업에서 1번 셀이 다시 시작) / DELETE(과정을 그만둘 때만)
 - 안내 마크다운·제출 문구 수정, 출력(실행 결과) 모두 지움
python continue_chain.py <in.ipynb> <out.ipynb>"""
import json, sys

src, out = sys.argv[1:3]
nb = json.load(open(src))
S = lambda c: ''.join(c['source']) if isinstance(c['source'], list) else c['source']
C = {c['metadata'].get('id'): c for c in nb['cells']}

FINAL_CELL = r'''# @title 5. 마무리 · RDS 중지 (다음 수업에서 이어서) · 최종 삭제는 12-3 마지막 (교안 __PAGE__쪽)
# 런타임을 다시 시작했어도 이 셀만 실행하면 됩니다 (Colab 보안 비밀의 AWS 키 사용).
import boto3
from google.colab import userdata

def _secret(name, default=None):
    try:
        value = userdata.get(name)
    except Exception:
        value = None
    return value.strip() if value and value.strip() else default

stop = globals().get("stop_preview")
if stop is not None:
    stop()                                                # 웹앱 미리보기 종료

if _secret("DB_HOST"):
    print("공용 RDS(DB_HOST)를 쓰는 중이라 중지·삭제하지 않습니다.")
else:
    instance = _secret("DB_INSTANCE_ID", "cd12-shop-lab")
    rds = boto3.Session(aws_access_key_id=_secret("AWS_ACCESS_KEY"), aws_secret_access_key=_secret("AWS_SECRET_KEY"),
                        aws_session_token=_secret("AWS_SESSION_TOKEN"),
                        region_name=_secret("AWS_REGION", "ap-northeast-2")).client("rds")
    try:
        status = rds.describe_db_instances(DBInstanceIdentifier=instance)["DBInstances"][0]["DBInstanceStatus"]
    except rds.exceptions.DBInstanceNotFoundFault:
        status = None
    if status is None:
        print(f"RDS {instance}가 없습니다. 다음 수업의 1번 셀이 새로 만듭니다.")
    else:
        answer = input(f"다음 수업까지 RDS {instance}를 중지하려면 STOP, 과정을 그만두고 완전히 지우려면 DELETE (그대로 두려면 Enter): ").strip().upper()
        if answer == "STOP":
            if status == "stopped":
                print("이미 중지돼 있습니다.")
            elif status != "available":
                print(f"지금 상태({status})에서는 중지할 수 없습니다. 잠시 뒤 이 셀을 다시 실행하세요.")
            else:
                rds.stop_db_instance(DBInstanceIdentifier=instance)
                print(f"RDS {instance} 중지 요청 완료 · 실습 데이터(shop 스키마)는 그대로 남습니다.")
                print("   다음 수업의 1번 셀이 다시 시작합니다. 중지 중에는 인스턴스 요금이 멈추고 저장공간 요금만 나옵니다.")
                print("   ※ AWS는 중지 7일 뒤 자동으로 다시 시작하므로, 수업 간격이 길면 콘솔에서 다시 중지하세요. 최종 삭제는 12-3 마지막 셀.")
        elif answer == "DELETE":
            rds.delete_db_instance(DBInstanceIdentifier=instance, SkipFinalSnapshot=True, DeleteAutomatedBackups=True)
            print(f"RDS {instance} 삭제 요청 완료 · 이어서 할 데이터도 함께 지워집니다. 다음 수업의 1번 셀이 새로 만듭니다.")
        else:
            print("그대로 둡니다. 켜져 있는 동안 요금이 나오므로 수업이 끝나면 STOP으로 중지하세요.")
'''

FINAL_MD = '''## 5. 마무리 (교안 __PAGE__쪽)

제출이 끝나면 실행합니다. **12-2·12-3에서 이 RDS와 데이터를 이어서 쓰므로** `STOP`을 입력해 RDS를 **중지**합니다(인스턴스 요금 중지, 데이터 유지). 다음 수업의 1번 셀이 다시 시작합니다. 과정을 그만둘 때만 `DELETE`(완전 삭제)를 입력하세요. **최종 삭제는 12-3 마지막 셀**에서 합니다.'''

if __name__ == '__main__':
    # 2번 셀: 고정 스키마 shop
    code = S(C['shop-tables-run'])
    if 'SHOP_SCHEMA = "shop"' not in code:
        a = 'def new_lab_schema():\n    name = "cd12_shop_" + uuid4().hex[:16]'
        assert code.count(a) == 1
        code = code.replace(a, 'def new_lab_schema(name=None):\n    name = name or "cd12_shop_" + uuid4().hex[:16]')
        b = '''if "shop_schema" not in globals() or shop_schema not in owned_schemas:
    shop_schema = new_lab_schema()
'''
        assert code.count(b) == 1
        code = code.replace(b, '''SHOP_SCHEMA = "shop"                     # 12-2·12-3에서 이어서 쓰는 고정 스키마
with transaction() as cur:
    cur.execute("SELECT to_regclass(%s) IS NOT NULL AS shop, to_regclass(%s) IS NOT NULL AS extended",
                (SHOP_SCHEMA + ".products", SHOP_SCHEMA + ".payments"))
    state = cur.fetchone()
if state["extended"]:
    raise SystemExit("⚠️ 이 RDS의 shop 스키마는 이미 12-2 모델로 확장됐습니다. 12-1을 처음부터 다시 하려면 5번 셀에서 DELETE 후 1번 셀부터 실행하세요.")
how = "이어서 사용" if state["shop"] else "새로 생성"
if not state["shop"]:
    new_lab_schema(SHOP_SCHEMA)
shop_schema = SHOP_SCHEMA
''')
        code = code.replace('print("⑤ 실습 스키마 준비:", shop_schema)', 'print("⑤ 실습 스키마 준비:", shop_schema, f"({how} · 12-2에서 이어서 사용)")')
        C['shop-tables-run']['source'] = code
    # 5번 셀: 마무리
    C['shop-delete-run']['source'] = FINAL_CELL.replace('__PAGE__', '34')
    C['shop-delete']['source'] = FINAL_MD.replace('__PAGE__', '34')
    intro = S(C['shop-intro'])
    intro = intro.replace('| 5. 삭제 | AWS의 실습 RDS 삭제 (요금 중지) | 34쪽 |', '| 5. 마무리 | RDS 중지(STOP) → 12-2에서 이어서 · 최종 삭제는 12-3 | 34쪽 |')
    intro = intro.replace('실습이 끝나면 5번 셀이 **삭제**합니다.', '실습이 끝나면 5번 셀로 **중지**하고 12-2·12-3에서 이어서 씁니다(최종 삭제는 12-3).')
    C['shop-intro']['source'] = intro
    sub = S(C['shop-submit']).replace('제출 후 **5번 셀로 RDS를 삭제**하세요.', '제출 후 **5번 셀에서 STOP**으로 RDS를 중지하세요(12-2에서 이어서 사용).')
    C['shop-submit']['source'] = sub
    for c in nb['cells']:
        if c['cell_type'] == 'code':
            c['outputs'] = []; c['execution_count'] = None
    json.dump(nb, open(out, 'w'), ensure_ascii=False, indent=1)
    print('ok')
