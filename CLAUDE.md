# MIIM Daily Report - Agentic AI 자동화 시스템

## 프로젝트 개요
야후 파이낸스(yfinance)로 TSLA, NVDA, PLTR, SPCX 주가를 수집하고
MIIM 공식 P = w1(D·M) + w2·ln(Intelligence) - w3(Y) + ε 으로
각 종목 적정가·괴리율·투자 시그널을 계산한 뒤,
빅데이터 김교수 스타일의 MIIM 데일리 리포트 HTML을 Claude AI로 생성해서
AWS S3 버킷에 업로드하고 CloudFront URL로 퍼블릭 배포하는
Agentic AI 자동화 시스템

## MIIM 가중치
- w1 = 0.45 (모멘텀)
- w2 = 0.50 (지능/AI 프리미엄)
- w3 = 0.25 (금리)

## 아키텍처
- Lambda 함수 3개: collector(수집+계산), writer(HTML생성), publisher(S3업로드)
- DynamoDB 테이블 2개: miim-prices(주가), miim-posts(발행목록)
- EventBridge: 매일 08:30 KST(23:30 UTC 전날) 자동 트리거
- S3 정적 웹앱 + CloudFront 배포
- Secrets Manager: API 키 관리

## 작업 순서 10단계

### Step 1: AWS 인프라 배포
```bash
cd infrastructure
python deploy_infrastructure.py
```

### Step 2: Secrets Manager에 API 키 등록
```bash
aws secretsmanager create-secret \
  --name "miim/anthropic-api-key" \
  --secret-string '{"api_key":"YOUR_ANTHROPIC_API_KEY"}'
```

### Step 3: DynamoDB 테이블 생성 확인
```bash
aws dynamodb list-tables | grep miim
```

### Step 4: S3 버킷 및 CloudFront 설정
```bash
python infrastructure/setup_s3_cloudfront.py
```

### Step 5: Lambda 함수 패키징
```bash
cd lambda
./package_lambdas.sh
```

### Step 6: Lambda 함수 배포
```bash
python infrastructure/deploy_lambdas.py
```

### Step 7: EventBridge 스케줄 설정
```bash
python infrastructure/setup_eventbridge.py
```

### Step 8: 수동 테스트 실행
```bash
python test_pipeline.py
```

### Step 9: CloudFront URL 확인
```bash
python infrastructure/get_cloudfront_url.py
```

### Step 10: 완료 조건 체크리스트 확인
```bash
python verify_deployment.py
```

## 코딩 규칙
- 모든 API 키는 AWS Secrets Manager에서만 로드 (하드코딩 절대 금지)
- 각 Lambda 함수는 단일 책임 원칙 준수
- DynamoDB 작업은 항상 try-except로 감싸기
- 로그는 CloudWatch Logs로 전송
- 환경변수는 Lambda 환경 변수로 관리

## 완료 조건 체크리스트
- [ ] DynamoDB miim-prices 테이블 생성됨
- [ ] DynamoDB miim-posts 테이블 생성됨
- [ ] S3 버킷 생성 및 정적 웹호스팅 활성화됨
- [ ] CloudFront 배포 생성됨
- [ ] collector Lambda 함수 배포됨
- [ ] writer Lambda 함수 배포됨
- [ ] publisher Lambda 함수 배포됨
- [ ] EventBridge 규칙 생성됨 (매일 23:30 UTC)
- [ ] Secrets Manager에 Anthropic API 키 등록됨
- [ ] 수동 테스트 파이프라인 성공
- [ ] CloudFront URL로 HTML 접근 가능
- [ ] TSLA, NVDA, PLTR, SPCX 4종목 데이터 수집됨
- [ ] MIIM 적정가/괴리율/시그널 계산됨
- [ ] 빅데이터 김교수 스타일 HTML 리포트 생성됨
