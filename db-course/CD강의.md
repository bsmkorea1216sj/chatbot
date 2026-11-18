# CD강의 작업 기록 (26)

클라우드데이터베이스(CD) 교안과 실습의 작업 기록입니다. [현재 상태](STATUS.md), [전체 변경 이력](LOG.md), [인수인계](HANDOFF.md)에서 이전 차시 작업도 확인할 수 있습니다. 교안과 코랩 기준본은 [Google Drive](https://drive.google.com/drive/folders/1WL8_UI8wvOyqXormXoXFx4L9ykGRkxdS)에 있습니다.

CD 작업은 이 저장소의 `db-course/`에서 관리하고, 클라우드 아키텍처(CA) 작업은 `cloud_architecture`에서 관리합니다. 다른 강의의 제작 기준을 적용한 경우 CD 변경 사항은 여기에 기록합니다.

## 2026-11-18 작업 기록 · 클라우드데이터베이스 12-1~3

[클라우드 아키텍처 교안의 약어 표기 기준](https://github.com/bsmkorea1216sj/cloud_architecture/blob/main/CA%EA%B0%95%EC%9D%98.md)을 클라우드데이터베이스 12장에 적용했다. 여성 액세서리 쇼핑몰을 공통 사례로 사용하며, 개념과 사례 설명을 마친 뒤에 Colab 실습과 과제를 진행한다. 실습 안내표의 단계 이름은 해당 코랩 셀로 연결하고, 코랩의 교안 쪽수도 실제 순서에 맞췄다.

| 차시 | 실습 시작 | 실습 흐름 |
|---|---:|---|
| [12-1 DB·웹앱 교안](https://docs.google.com/presentation/d/1Gu6kZNfazuj6jpYexa_Jd7aVNd0XVwmu/edit) · [Colab](https://colab.research.google.com/drive/1URPntHhY0jY96psj9cK0Khrzq3gLb8KX) | 32쪽 | 상품 주문·품절·취소와 재고 복구를 웹앱에서 확인하고 RDS 중지 |
| [12-2 개념 모델링 교안](https://docs.google.com/presentation/d/1VBrZI-xw8Nk5BPrE5m9cQudmQDjx7dfB/edit) · [Colab](https://colab.research.google.com/drive/1bUdKHLpCey3gCNt-3Qyx-8SCy9QCZfTY) | 25쪽 | 같은 RDS의 `shop`을 이어받아 결제·배송·리뷰와 CRUD를 확인하고 RDS 중지 |
| [12-3 논리·물리 모델링 교안](https://docs.google.com/presentation/d/15z0sVLvy--Je1DqqJD9ZxK24g03mDOaJ/edit) · [Colab](https://colab.research.google.com/drive/16zKCRFtxxvxd3m9DJeg2F73dIiQWhCVN) | 54쪽 | 논리 제약과 물리 설계를 비교하고, 마지막 8번 셀에서 실습 RDS 최종 삭제 |

- 약어가 나오는 70쪽(12-1 15쪽, 12-2 17쪽, 12-3 38쪽) 하단에 영문 원어와 한글 뜻을 표기했다. 예를 들어 `FK: Foreign Key (외래키)`로 표시한다.
- **12-3 필팩터 강의 설명 기록.** 테이블에 새 행을 넣을 때 `100`은 갱신 공간을 따로 예약하지 않고, `90`과 `80`은 각각 약 10%, 20%를 남긴다. 귀걸이 재고를 1개에서 0개로 바꿀 때 PostgreSQL은 새 행 버전을 저장한다. 같은 페이지에 자리가 있고 `stock`이 일반 인덱스에 쓰이지 않으면 새 인덱스 항목 없이 HOT(Heap-Only Tuple) 갱신을 할 수 있다. 낮은 필팩터는 같은 페이지 갱신 가능성을 높이는 대신 초기 페이지 수를 늘린다. [PostgreSQL 필팩터 문서](https://www.postgresql.org/docs/current/sql-createtable.html) · [HOT 문서](https://www.postgresql.org/docs/current/storage-hot.html)
- 교안 29·30쪽의 Colab 4번 셀에서는 같은 2만 행을 넣고 10%를 갱신하여 **100과 80**의 페이지 수와 HOT 비율을 비교한다. 7번 셀의 **90**은 쇼핑몰 물리 설계에 적용하는 설정값이다. 이 설명은 인수인계용으로 기록했다.
- 교안 3개와 Colab 3개를 기존 Drive 링크에 저장하고 재다운로드 대조를 마쳤다. 이번 교안과 코랩 개편의 전체 AWS 실서버 실행은 미검증이다. [수정 스크립트와 작업 기록](https://github.com/bsmkorea1216sj/chatbot/tree/claude/setup-claude-cli-AS1R6/db-course/cd12-series)
