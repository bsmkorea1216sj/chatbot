# (템플릿 원본 번호, 삽입 위치(원본 번호 뒤), 텍스트, 노트)
# 템플릿 4·26: [tag,title,sub,label1,body1,label2,body2,label3,body3,footer] / 템플릿 25: [tag,title,sub,code_lines,footer]
NEW = [
(4, 15, ["현업 사례 · AWS EBS", "AWS EBS: RAID 5·6을 권장하지 않는 이유",
  "클라우드 디스크(EBS)를 여러 개 묶을 때는 어떤 RAID를 쓸까?",
  "공개 사례", "AWS 문서는 EBS 볼륨을 묶을 때 성능은 RAID 0, 이중화는 RAID 1을 안내하고, RAID 5·6은 패리티 쓰기가 볼륨의 IOPS를 소모해 권장하지 않습니다.",
  "교안 연결", "RAID 5는 쓰기 1번마다 데이터·패리티를 읽고 다시 써야 해서(쓰기 페널티) 디스크 I/O가 늘어납니다.",
  "토론", "EBS 볼륨은 이미 가용 영역 안에서 복제됩니다. 그 위에 RAID 1을 또 하는 것은 언제 의미가 있을까요?",
  "출처: AWS 문서 · Amazon EBS and RAID configuration"],
 "【슬라이드 핵심】 AWS는 EBS에서 RAID 0(성능)·RAID 1(이중화)을 안내하고, RAID 5·6은 패리티 쓰기가 IOPS를 소모해 권장하지 않음.\n"
 "【강의 설명】 바로 앞 RAID 5의 단점 '패리티 계산으로 쓰기 성능 저하'가 클라우드에서는 'IOPS(초당 입출력 횟수) 비용'으로 나타납니다. RAID 5는 작은 쓰기 1번에 '옛 데이터 읽기·옛 패리티 읽기·새 데이터 쓰기·새 패리티 쓰기' 4번의 I/O가 필요합니다(Colab 심화에서 계산).\n"
 "토론 정답 방향: EBS는 같은 가용 영역 안에서 이미 복제되므로 디스크 하나 고장에는 강합니다. 그래도 볼륨 자체 장애·실수에 대비하려면 RAID 1보다 스냅샷(백업)과 다른 가용 영역 복제(Multi-AZ)가 더 효과적입니다.\n"
 "【연결】 RAID 5 장단점, Colab 심화(쓰기 페널티), RDS Multi-AZ 사례.\n"
 "【출처】 AWS 문서 'RAID configuration on Linux / Amazon EBS' (수업 전 원문 문구 확인 권장)"),
(4, 19, ["현업 사례 · RDS Multi-AZ", "RDS Multi-AZ: 서버와 데이터센터를 미러링한다",
  "RAID 1은 디스크를 복제한다. 서버나 데이터센터가 멈추면?",
  "공개 사례", "RDS Multi-AZ는 다른 가용 영역에 대기(Standby) DB를 두고 동기식으로 복제하며, 장애 시 자동으로 대기 DB로 전환(Failover)합니다.",
  "교안 연결", "RAID 1이 '디스크 2개에 같은 데이터'라면 Multi-AZ는 'DB 서버 2대(서로 다른 데이터센터)에 같은 데이터'입니다.",
  "토론", "Multi-AZ에서 운영자가 실수로 주문 테이블을 삭제하면 대기 DB는 어떻게 될까요?",
  "출처: AWS 문서 · Amazon RDS Multi-AZ deployments"],
 "【슬라이드 핵심】 RDS Multi-AZ = 다른 가용 영역(데이터센터)에 동기식 대기 DB + 자동 장애 전환. RAID 1의 개념을 서버·데이터센터 단위로 확장한 것.\n"
 "【강의 설명】 보호 범위를 단계로 정리합니다: 디스크 고장 → RAID(또는 EBS 복제), 서버·데이터센터 고장 → Multi-AZ(4번 Aurora 사례도 같은 계열), 사람의 실수·데이터 손상 → 백업과 특정 시점 복구(PITR, 10-1 WAL 단원).\n"
 "토론 정답: 동기식 복제라 삭제도 즉시 대기 DB에 복제됩니다. 미러링은 '실수'까지 복제하므로 되살리려면 백업·PITR이 필요합니다(학생 실습 제출의 상황 C와 같은 답).\n"
 "【연결】 RAID 1·10, 4번 Aurora 사례, 학생 실습 제출 상황 C, Colab 실습 3(우리 RDS의 MultiAZ·백업 보존 기간 확인).\n"
 "【출처】 https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZ.html"),
(25, 25, ["Colab 실습 · 3", "우리 RDS의 저장소는 어떻게 보호되고 있을까?",
  "AWS 키로 RDS 저장소 설정을 조회합니다. (DB 비밀번호 불필요)",
  ["rds = aws.client('rds')",
   "db = rds.describe_db_instances(",
   "       DBInstanceIdentifier='postgresql-lab-01')['DBInstances'][0]",
   "rows = [['스토리지 종류', db['StorageType']],",
   "        ['할당 용량(GB)', db['AllocatedStorage']],",
   "        ['IOPS', db.get('Iops', '기본값')],",
   "        ['Multi-AZ', db['MultiAZ']],",
   "        ['백업 보존(일)', db['BackupRetentionPeriod']]]",
   "display(pd.DataFrame(rows, columns=['항목', '우리 RDS']))"],
  "기록: 우리 RDS는 디스크(EBS)·서버(Multi-AZ)·실수(백업) 중 어디까지 보호되고 있는지 적습니다."],
 "【슬라이드 핵심】 boto3로 우리 RDS의 스토리지 종류·용량·IOPS·Multi-AZ·백업 보존 기간을 조회해 RAID·이중화 개념과 연결.\n"
 "【강의 설명】 RDS는 사용자가 RAID를 직접 구성하지 않습니다. 디스크 이중화는 EBS가, 서버 이중화는 Multi-AZ가, 실수 복구는 자동 백업(PITR)이 맡습니다. 실습 RDS는 비용 때문에 Multi-AZ가 꺼져 있을 가능성이 높습니다. 그렇다면 '데이터센터 장애에는 보호되지 않는다'가 정답입니다.\n"
 "【연결】 AWS EBS 사례, RDS Multi-AZ 사례, 10-1 PITR.\n"
 "【자료】 CD10-3_Colab_Lab(26).ipynb 실습 3"),
(25, 25, ["Colab 실습 · 심화", "RAID별 쓰기 페널티와 실제 쓰기 성능",
  "디스크 4개(각 3,000 IOPS)일 때 RAID별 쓰기 성능을 계산합니다.",
  ["N, IOPS = 4, 3000                  # 디스크 4개, 디스크당 3,000 IOPS",
   "penalty = {'RAID 0': 1, 'RAID 1': 2, 'RAID 10': 2,",
   "           'RAID 5': 4, 'RAID 6': 6}  # 쓰기 1번에 필요한 디스크 I/O",
   "rows = []",
   "for level, p in penalty.items():",
   "    rows.append([level, p, N * IOPS, N * IOPS // p])",
   "display(pd.DataFrame(rows, columns=['RAID', '쓰기 1회당 I/O',",
   "                                    '읽기 IOPS', '쓰기 IOPS']))"],
  "확인: RAID 5·6의 쓰기 IOPS가 RAID 10보다 얼마나 낮은지 비교하고 AWS EBS 사례와 연결합니다."],
 "【슬라이드 핵심】 쓰기 페널티(쓰기 1번에 필요한 실제 디스크 I/O 수): RAID 0=1, RAID 1·10=2, RAID 5=4, RAID 6=6.\n"
 "【강의 설명】 디스크 4개 × 3,000 IOPS = 12,000 IOPS를 기준으로 쓰기 IOPS는 RAID 0 12,000, RAID 10 6,000, RAID 5 3,000, RAID 6 2,000입니다. 그래서 쓰기가 많은 DB 서버에는 RAID 10을 많이 쓰고, AWS가 EBS에서 RAID 5·6을 권장하지 않습니다. 실제 장비는 캐시·컨트롤러 성능에 따라 달라지는 단순화된 모델이라는 점을 함께 알려 줍니다.\n"
 "【연결】 RAID 5·6 단점, RAID 10 사용 사례(DB 서버), AWS EBS 사례."),
]
