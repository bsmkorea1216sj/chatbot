"""CD10-2 Colab 실습 노트북 생성: python colab_nb.py <출력.ipynb>  (셀 원고: lab_cells.py)"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lab_cells as L


def md(t):
    return {"cell_type": "markdown", "metadata": {}, "source": t}


def code(t):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": t}


cells = [
    md("# CD10-2 인덱스·스캔·조인 · Colab 실습\n"
       "**보안 비밀(왼쪽 열쇠)**: `AWS_ACCESS_KEY`, `AWS_SECRET_KEY` (필수), "
       "`DB_PASSWORD`(없으면 입력칸 표시), `DB_HOST`·`DB_PORT`(없으면 RDS 자동 조회) (선택)\n\n"
       "1. 바로 아래 pip 셀을 먼저 실행합니다.\n"
       "2. 각 실습 셀은 **접속까지 스스로** 하므로 어느 실습부터 실행해도 됩니다 (처음 한 번 비밀번호 입력).\n"
       "3. 실습 테이블 `cd10_orders`(주문 10만 행), `cd10_customers`(고객 1만 행)는 접속한 DB에 한 번만 만들어집니다."),
    code("!pip -q install boto3 psycopg2-binary pandas requests"),
    md("## 실습 1 · 인덱스 전후: Seq Scan → Index Scan\n① 인덱스 전·후 실행계획 트리 → ② 비교 표 (스캔 방식, 결과 행, 읽은 페이지 수, 실행시간)"),
    md(L.INS1),
    code(L.LAB1),
    md("## 실습 2 · 조회 범위에 따른 조인 방식 변화\n고객 1명 → 9,000명으로 범위를 넓히면 Planner가 고르는 조인 방식이 어떻게 바뀌는지 표로 확인합니다."),
    md(L.INS2),
    code(L.LAB2),
    md("## 심화 · B-tree와 BRIN 인덱스 크기 비교\n같은 컬럼(order_id)에 두 인덱스를 만들고 테이블 크기와 비교합니다."),
    md(L.INS3),
    code(L.DEEP),
    code('# 실습용 테이블 정리가 필요할 때만 주석을 풀고 실행\n'
         '# cur.execute("DROP TABLE IF EXISTS cd10_orders, cd10_customers")\n'
         'conn.close()\nprint("연결 종료")'),
]
nb = {"cells": cells, "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3"}},
      "nbformat": 4, "nbformat_minor": 5}
out = sys.argv[1] if len(sys.argv) > 1 else "CD10-2_Colab_Lab(26).ipynb"
json.dump(nb, open(out, "w"), ensure_ascii=False, indent=1)
print("saved", out)
