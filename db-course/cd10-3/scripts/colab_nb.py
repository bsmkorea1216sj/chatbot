"""CD10-3 RAID Colab 실습 노트북 생성: python colab_nb.py <출력.ipynb>"""
import json, sys

LAB1 = '''import pandas as pd
from itertools import combinations

def raid_table(n, size_tb):
    spec = {  # 레벨: (최소 디스크, 사용 용량(디스크 수), 장애 허용, 쓰기 1회당 I/O)
        "RAID 0":  (2, n,      "0개",          1),
        f"RAID 1 ({n}개 모두 복사)": (2, 1, f"{n-1}개", n),
        "RAID 5":  (3, n - 1,  "1개",          4),
        "RAID 6":  (4, n - 2,  "2개",          6),
        "RAID 10": (4, n // 2, "1개 (최대 n/2)", 2),
    }
    rows = []
    for level, (mn, k, ft, wp) in spec.items():
        if n >= mn:
            rows.append([level, mn, f"{k * size_tb} TB", f"{k / n:.0%}", ft, wp])
    return pd.DataFrame(rows, columns=["RAID", "최소 디스크", "사용 용량", "용량 효율", "장애 허용", "쓰기 1회당 I/O"])

display(raid_table(4, 2))          # 학생 실습 1: 2TB 디스크 4개

# RAID 10에서 디스크 2개가 동시에 고장 나면? (미러 쌍: 0-1, 2-3)
pairs = [{0, 1}, {2, 3}]
cases = []
for a, b in combinations(range(4), 2):
    same = {a, b} in pairs
    cases.append([f"디스크 {a}·{b}", "같은 쌍" if same else "다른 쌍", "❌ 데이터 손실" if same else "✅ 계속 동작"])
display(pd.DataFrame(cases, columns=["고장 디스크", "미러 쌍", "결과"]))'''

LAB2 = '''import pandas as pd

data = "DATABASE".encode()                 # 저장할 데이터 8바이트
stripes = [data[i:i + 3] for i in range(0, len(data), 3)]
rows = []
for s in stripes:
    a, b, c = (list(s) + [0, 0, 0])[:3]    # 데이터 디스크 3개 (부족하면 0)
    rows.append([a, b, c, a ^ b ^ c])      # 디스크 4 = 패리티
disks = pd.DataFrame(rows, columns=["디스크1", "디스크2", "디스크3", "디스크4(패리티)"])
print("① 저장 상태 (바이트 값)"); display(disks)

# 디스크2 고장 → 나머지와 패리티를 XOR해서 복구
recovered = disks["디스크1"] ^ disks["디스크3"] ^ disks["디스크4(패리티)"]
check = pd.DataFrame({"원래 디스크2": disks["디스크2"], "복구한 디스크2": recovered})
check["일치"] = check["원래 디스크2"] == check["복구한 디스크2"]
print("② 디스크2 고장 후 복구"); display(check)

restored = bytes(x for r, rec in zip(rows, recovered) for x in (r[0], rec, r[2]))[:len(data)]
print("③ 복구한 데이터:", restored.decode())'''

LAB3 = '''import boto3, pandas as pd
from google.colab import userdata

def secret(*names, default=None):
    for n in names:
        try:
            v = userdata.get(n)
            if v and v.strip():
                return v.strip()
        except Exception:
            pass
    return default

aws = boto3.Session(aws_access_key_id=secret("AWS_ACCESS_KEY", "AWS_ACCESS_KEY_ID"),
                    aws_secret_access_key=secret("AWS_SECRET_KEY", "AWS_SECRET_ACCESS_KEY"),
                    region_name=secret("AWS_REGION", "AWS_DEFAULT_REGION", default="ap-northeast-2"))
rds = aws.client("rds")
dbs = rds.describe_db_instances()["DBInstances"]
db = next((d for d in dbs if d["DBInstanceIdentifier"] == secret("DB_INSTANCE_ID", default="postgresql-lab-01")), dbs[0])

rows = [
    ["DB 인스턴스", db["DBInstanceIdentifier"], "조회한 RDS"],
    ["스토리지 종류", db["StorageType"], "EBS 볼륨 종류 → 가용 영역 안에서 이미 복제 (RAID를 직접 구성하지 않음)"],
    ["할당 용량", f"{db['AllocatedStorage']} GB", "디스크 크기"],
    ["IOPS", db.get("Iops", "기본값(gp2는 용량 비례)"), "초당 입출력 횟수"],
    ["Multi-AZ", db["MultiAZ"], "True면 다른 데이터센터에 대기 DB (RAID 1의 서버판)"],
    ["백업 보존 기간", f"{db['BackupRetentionPeriod']}일", "0이면 자동 백업 꺼짐 → PITR 불가"],
    ["복구 가능한 최근 시각", str(db.get("LatestRestorableTime", "-"))[:19], "PITR로 되돌릴 수 있는 가장 최근 시각"],
]
display(pd.DataFrame(rows, columns=["항목", "우리 RDS", "의미 (보호 범위)"]))'''

DEEP = '''import pandas as pd
N, IOPS = 4, 3000                         # 디스크 4개, 디스크당 3,000 IOPS (gp3 기본값)
penalty = {"RAID 0": 1, "RAID 1": 2, "RAID 10": 2, "RAID 5": 4, "RAID 6": 6}
rows = [[lv, p, N * IOPS, N * IOPS // p, f"{1 / p:.0%}"] for lv, p in penalty.items()]
display(pd.DataFrame(rows, columns=["RAID", "쓰기 1회당 I/O", "읽기 IOPS", "쓰기 IOPS", "RAID 0 대비 쓰기"]))'''

INS1 = '''> **결과 읽는 법 (실행 결과)**
> | RAID | 사용 용량 | 용량 효율 | 장애 허용 |
> |---|---|---|---|
> | RAID 0 | 8 TB | 100% | 0개 |
> | RAID 1 | 2 TB | 25% (4개 모두 복사) | 3개 |
> | RAID 5 | 6 TB | 75% | 1개 |
> | RAID 6 | 4 TB | 50% | 2개 |
> | RAID 10 | 4 TB | 50% | 1개 (최대 2개) |
>
> - RAID 10에서 2개가 동시에 고장 나는 6가지 경우 중 **같은 미러 쌍 2가지만 데이터 손실**, 나머지 4가지는 계속 동작합니다 → 학생 실습 1의 "생각할 문제" 정답.'''

INS2 = '''> **결과 읽는 법 (실행 결과)**
> - "DATABASE" 8바이트를 3개 데이터 디스크에 나눠 쓰고, 4번째 디스크에 XOR 패리티를 저장합니다 (RAID 3·5의 원리).
> - 디스크2가 고장 나도 `디스크1 ^ 디스크3 ^ 패리티`로 모든 값이 **일치(True)**하게 복구되고, 데이터가 다시 "DATABASE"로 돌아옵니다.
> - 디스크 2개가 동시에 고장 나면 이 계산으로는 복구할 수 없습니다 → 그래서 RAID 6은 패리티를 하나 더 둡니다.'''

INS3 = '''> **결과 읽는 법 (예상 · 실행 후 확인)**
> - 스토리지 종류는 gp2 또는 gp3 → **디스크 이중화는 EBS가** 이미 해 줍니다.
> - 실습용 RDS는 보통 Multi-AZ가 False → **데이터센터 장애에는 보호되지 않습니다.**
> - 백업 보존 기간이 1일 이상이면 그 기간 안에서 **실수로 지운 데이터를 PITR로 복구**할 수 있습니다 (학생 실습 제출 상황 C).'''

INS4 = '''> **결과 읽는 법 (실행 결과)**
> | RAID | 쓰기 IOPS | RAID 0 대비 |
> |---|---|---|
> | RAID 0 | 12,000 | 100% |
> | RAID 1·10 | 6,000 | 50% |
> | RAID 5 | 3,000 | 25% |
> | RAID 6 | 2,000 | 17% |
>
> - 읽기는 모두 12,000 IOPS로 같지만 **쓰기는 RAID 5·6이 크게 떨어집니다** → 쓰기가 많은 DB 서버에 RAID 10을 쓰고, AWS가 EBS에서 RAID 5·6을 권장하지 않는 이유입니다.
> - RAID 1은 일반적인 디스크 2개 미러 기준(쓰기 1번 = 2번 기록)입니다. 캐시·컨트롤러를 뺀 단순 모델입니다.'''


def md(t):
    return {"cell_type": "markdown", "metadata": {}, "source": t}


def code(t):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": t}


cells = [
    md("# CD10-3 디스크 이중화(RAID) · Colab 실습\n"
       "- 실습 1·2·심화는 **DB 접속 없이** 바로 실행됩니다.\n"
       "- 실습 3만 보안 비밀 `AWS_ACCESS_KEY`, `AWS_SECRET_KEY`가 필요합니다 (DB 비밀번호 불필요)."),
    code("!pip -q install boto3 pandas"),
    md("## 실습 1 · RAID별 용량과 장애 허용 계산 (학생 실습 1 확인)"), md(INS1), code(LAB1),
    md("## 실습 2 · XOR 패리티로 고장 난 디스크 복구 (학생 실습 2 확장)"), md(INS2), code(LAB2),
    md("## 실습 3 · 우리 RDS의 저장소는 어떻게 보호되고 있을까?"), md(INS3), code(LAB3),
    md("## 심화 · RAID별 쓰기 페널티와 쓰기 IOPS"), md(INS4), code(DEEP),
]
nb = {"cells": cells, "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3"}},
      "nbformat": 4, "nbformat_minor": 5}
out = sys.argv[1] if len(sys.argv) > 1 else "CD10-3_Colab_Lab(26).ipynb"
json.dump(nb, open(out, "w"), ensure_ascii=False, indent=1)
print("saved", out)
