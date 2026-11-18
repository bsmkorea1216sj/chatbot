# CD12 여성 액세서리몰 연속 실습 (2026-11-18 Codex)

Drive 기준본 6개를 같은 ID/파일명으로 갱신했다. 이전 상품(마우스·키보드·거치대, 의류)은 이 주제의 최신 기준이 아니다. 기존 Claude 생성기를 다시 돌릴 경우 아래 보정도 마지막에 적용할 것.

| 파트 | 교안 Drive ID | Colab Drive ID | 흐름 |
|---|---|---|---|
| 12-1 | 1Gu6kZNfazuj6jpYexa_Jd7aVNd0XVwmu | 1URPntHhY0jY96psj9cK0Khrzq3gLb8KX | 5표 DB, 웹앱 주문·품절·취소, STOP |
| 12-2 | 1VBrZI-xw8Nk5BPrE5m9cQudmQDjx7dfB | 1bUdKHLpCey3gCNt-3Qyx-8SCy9QCZfTY | shop 유지, 7개 엔티티 확장, 결제·배송·리뷰, STOP |
| 12-3 | 15z0sVLvy--Je1DqqJD9ZxK24g03mDOaJ | 16zKCRFtxxvxd3m9DJeg2F73dIiQWhCVN | 논리 열 이름 정렬·물리 설계·성능 비교, 마지막 DELETE |

## 주제와 이어하기

- 101 진주 귀걸이 19,900원/초기 재고1, 102 실버 목걸이 32,900원/5, 103 리본 헤어핀 24,900원/3. 12-2부터 201 체인 팔찌, 202 큐빅 반지, 203 플라워 브로치 추가. 학습용 가상 상품·가격이며 귀걸이 1개는 한 쌍 판매 단위.
- 같은 AWS 계정·리전·DB_INSTANCE_ID(기본 cd12-shop-lab)·DB_PASSWORD, 고정 shop 스키마를 사용. 매 파일 1번 셀부터 순서대로 실행. Colab 런타임은 바뀌어도 RDS 데이터 유지.
- 기존 예제의 알려진 ID와 기존 이름/새 이름이 모두 일치하는 행만 상품명·카테고리 전환. 가격·재고·주문·사용자가 등록한 상품 보존. 반복 실행 가능. 예전 이름이 코드에 남은 곳은 이 마이그레이션의 매칭 조건이다.
- 12-1 웹앱의 표5개는 12-2부터 확장되므로, 이후에는 12-2/3에서 진행. 12-1을 무리하게 재실행하면 기존 표를 삭제하지 않고 안내로 중단.

## 수정 내용

- 세 노트북 intro에 공통 상품·단계·조건·파트 이동 링크. 12-1/2 마지막 셀은 STOP만 허용(DELETE API 분기 제거). 최종 DELETE는 12-3 마지막 셀만 제공.
- 최종 삭제는 공용 DB_HOST 사용 시 차단. course=cd12-shop-lab 태그와 삭제방지 여부 확인, DELETE 입력 뒤 RDS 식별자 재입력, 상태 검사, 스냅샷 생략·자동백업 삭제, 삭제 완료 waiter. 기존 수동 스냅샷·다른 리소스 비용은 별도 확인 안내. 실제 삭제 실행은 하지 않았다.
- 교안 3종 전체 텍스트/노트의 예제 명칭, 개요/마무리와 연결문, 다음 파트 링크 보정. 12-2/3 학습목표·Summary의 한글 표시 문제는 해당 run의 CJK 글꼴/색을 명시해 수정. 원본 테마·이미지·레이아웃·슬라이드 순서·숨긴 정답 슬라이드는 유지.
- 12-3 맨 앞 실행 불가한 `hf` 코드 셀은 같은 셀 ID의 안내 markdown으로 변경(셀 삭제 없음). 코드 실행 출력은 비우고 셀 ID/Colab anchor 일치시킴.

## 재현과 검증

1. 최신 Drive 6개를 내려받아 part1..3.pptx / part1..3.ipynb로 같은 작업 폴더에 둔다. 기존 생성기로 새 출력이 생겼으면 그 출력을 입력으로 쓴다. 강의자 편집본을 우선한다.
2. `edit_titles.mjs`는 Artifact Tool의 imported-deck API로 기존 자막을 찾고 편집 계획을 검증한다. 재직렬화로 다른 원본 요소가 바뀌지 않도록 `update_accessories.py`가 해당 텍스트를 원본 OOXML에 국소 적용한다.
3. `python update_accessories.py` → output/의 6개 파일. `python validate_accessories.py`.
4. LibreOffice PDF 내부 미리보기로 36/31/59쪽 검토(ExportHiddenSlides=true: 12-2 20쪽 정답은 원래 숨김). 임시 PDF/이미지는 업로드하지 않는다.
5. 업로드 직전 modifiedTime 비교. 최신 원본이 바뀌었으면 다시 받아 보정. 같은 Drive ID에 media update. 저장 후 6파일 다시 내려받아 SHA256 대조.

검증 범위: 모든 코드 셀 Python 구문, 고유 셀 ID, 교안의 모든 Colab 셀 anchor, 원본 media/master/layout/theme 바이트 보존, 삭제/중지 모의16분기. 새 상품 전환 UPDATE를 SQLite fixture의 세 열 이름 구조에서 실행해 사용자 상품·가격·재고 보존과 재실행 확인. PostgreSQL DDL/실제 AWS 연결·웹앱은 이번 변경에서 실서버 재실행하지 않았다(이전 12-1 실제 AWS 확인 이력과 구분). 12-2/3 전체 실서버 실행은 다음 확인 사항.

AWS 근거: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_StopInstance.html / https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_DeleteInstance.html
