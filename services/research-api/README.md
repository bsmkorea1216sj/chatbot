# BSM AI 리서치 GCP 전환 — 구현 시작 버전

실제 배포·카페24 상품 등록·결제 연동은 아직 완료되지 않았습니다.
현재 구현: FastAPI 웹/API, Firebase Google 토큰 검증, Firestore 작업 예약/정산,
Cloud Tasks 인증 worker, Gemini 2.5 Flash 검색 grounding 호출과 인용 연결,
무료 3회, 계정별 결과 조회, HTML 화면/진행상태/다운로드.
카페24 결제 연동은 아직 구현 전이며 구매 버튼은 닫혀 있습니다.
50% 원가 예산은 서버 내부 운영 정책이며 고객 상품 설명/API 응답에 노출하지 않습니다.
고객에는 리서치 크레딧과 유형별 차감량으로 안내합니다. 정확한 제공량은 실제 사용량
측정 후 확정하며, 판매 전 확정값과 작업 범위가 표시되어야 합니다.
실제 모델 가격은 하드코딩하지 않으며 가격 버전과 환율을 운영 설정으로 받습니다.

## 대상 구조
- Cloud Run: 웹 화면/API, Firebase Auth 토큰 검증
- Firestore: 계정, 주문 연결, 결제 원장, 사용량, 작업 상태
- Cloud Tasks와 인증된 Cloud Run worker: 자료 검색/보고서 생성
- Secret Manager: Gemini와 Cafe24 자격 증명
- Cloud Storage: 비공개 보고서 및 허가된 소스 다운로드
- Colab: 개발, 배포, BSM/ai 리서치 원본 보관

## 다음 구현의 필수 조건
1. 카페24 관리자 로그인 후 월 22,000원 이용권을 판매 대기로 등록하고 상품번호 확보.
2. 정기결제 활성화와 디지털 서비스 적용 조건 확인. 미승인 시 월 이용권 일회 결제.
3. 개발자 앱 OAuth 주문 조회 권한과 webhook 등록. 비밀 값은 채팅/로그에 출력하지 않음.
4. 결제 전 로그인 UID에 연결된 구매 요청 생성. 주문 연결은 서버가 검증;
   고객이 입력한 이메일/주문번호만으로 타인의 주문을 귀속하지 않음.
5. webhook은 조회 계기만 제공. 실제 주문의 결제금액, 상품, 취소/환불을 API 재조회.
6. 주문/회차별 키로 중복 지급 방지. Firestore 트랜잭션으로 원장/지급/예약 동시 반영.
7. 모든 모델 호출 전에 입력 크기와 최대 출력 토큰 기반 비용 상한 예약.
   실제 provider usage로 정산; 이미 발생한 API 비용은 실패해도 지우지 않음.
8. 기본 무료 체험도 작업 상한과 사용자별 동시 작업 제한. 심층 작업은 시작 전 유료 안내.
9. 판매 전 구독 기간/갱신, 추가 충전 만료, 가격/환율 갱신 기준, 환불 기준 확정.

## 검증
`python -m unittest discover -s . -p 'test_*.py'`
테스트는 정책 계산, 공개 설정 원가 미노출, 무인증 차단, Google 로그인 공급자,
가격 미설정 차단, 결과 소유자, 한글 인용 연결을 검증합니다.
실제 Firebase 로그인·Firestore 트랜잭션·Gemini 검색·결제·GCP 배포는 검증 전입니다.
자료 유형 선택은 검색 프롬프트에서 우선순위를 지정하며, 해당 유형만 검색하는
엄격한 필터는 아직 구현 전입니다. 결과 원문/유형 검수가 필요합니다.

## 실행에 필요한 설정
GOOGLE_CLOUD_PROJECT, FIREBASE_WEB_CONFIG, SERVICE_URL, TASKS_REGION, TASKS_QUEUE,
TASKS_SA, GEMINI_API_KEY, INPUT_USD_PER_MILLION, OUTPUT_USD_PER_MILLION,
KRW_PER_USD, GROUNDING_MAX_MICRO_KRW, PRICE_VERSION.
GEMINI_API_KEY는 Secret Manager로 주입합니다. Firebase Google 로그인 공급자와
웹앱 도메인을 설정하고 Firestore Native DB, Cloud Tasks 큐를 준비해야 합니다.
무료 체험 예산은 budgets/trial_pool의 granted(마이크로원)으로 별도 설정합니다.
설정 누락이나 예산 부족 시 작업은 실행되지 않습니다.
사용자 브라우저에는 Firestore 직접 쓰기 권한을 주지 않으며 서버 서비스 계정만 씁니다.
작업 예약/실행 중 중단으로 남은 예약은 운영자가 확인하고 조정해야 합니다.
이 버전은 운영 배포 전의 개발 체크포인트입니다.
