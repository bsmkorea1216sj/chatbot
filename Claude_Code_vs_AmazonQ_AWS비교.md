# Claude Code vs Amazon Q Developer
## AWS 클라우드 관리·제어 기능 비교 보고서

> 작성일: 2026년 6월  
> 대상: AWS 클라우드 관리자, DevOps 엔지니어, 개발팀 의사결정자

---

> ⚠️ **중요 공지**: 2026년 4월 30일, AWS는 Amazon Q Developer IDE 플러그인 및 유료 구독의
> **2027년 4월 30일부로 서비스 종료**를 공식 발표했습니다.
> 2026년 5월 15일부터 신규 가입이 차단되었으며,
> AWS는 후속 제품인 **Kiro**로의 전환을 권장하고 있습니다.

---

## 목차

1. 제품 개요 및 포지셔닝
2. AWS 서비스 연동 범위
3. IaC(Infrastructure as Code) 지원
4. CLI / 터미널 통합 방식
5. 코드 생성 및 디버깅 능력
6. 보안·IAM 관련 기능
7. 비용 최적화 기능
8. 멀티클라우드 지원 여부
9. 가격 정책
10. 실제 AWS 작업 자동화 능력
11. 종합 비교 요약
12. 선택 가이드

---

## 1. 제품 개요 및 포지셔닝

### Claude Code (Anthropic)

Claude Code는 Anthropic이 개발한 **터미널 우선(Terminal-first) 에이전틱 코딩 어시스턴트**입니다.
CLI 기반으로 동작하며, "Agent Loop(Context → Thought → Action → Observation)" 패턴을
핵심 아키텍처로 채택합니다. 단순한 코드 자동완성 도구가 아니라, 코드베이스 전체를 이해하고
멀티스텝 작업을 자율적으로 수행할 수 있는 에이전트로 설계되었습니다.

2026년 5월에는 **Claude Platform on AWS**가 정식 출시(GA)되면서, AWS 계정을 통해
Anthropic의 네이티브 Claude 플랫폼을 직접 사용할 수 있게 되었습니다.
IAM 인증, CloudTrail 감사 로깅, AWS 청구서 통합이 지원되며, AWS 기존 약정(Commit)과
상계(retire)도 가능합니다. 사용자 만족도 평가에서 **92% Excellent** 등급을 받고 있습니다.

### Amazon Q Developer (AWS)

Amazon Q Developer는 AWS가 자체 개발한 **AWS 에코시스템 특화 AI 개발 어시스턴트**입니다.
IDE 플러그인, AWS 콘솔, Slack/Teams 등 다양한 채널에서 사용 가능하며,
AWS 서비스에 대한 깊은 맥락 이해를 바탕으로 코드 생성, 인프라 관리, 운영 자동화를 지원합니다.

단, **2026년 5월부로 신규 가입이 중단**되었으며, 기존 사용자는 2027년 4월까지 사용 가능하고
이후에는 후속 제품인 **Kiro**(스펙 기반 에이전틱 IDE)로 전환해야 합니다.
사용자 만족도는 89%로 Claude Code보다 다소 낮습니다.

---

## 2. AWS 서비스 연동 범위

### Claude Code

Claude Code는 **AWS MCP(Model Context Protocol) 서버**를 통해 AWS 서비스와 연동합니다.
2026년 5월 AWS MCP Server가 GA로 출시되면서 다음을 지원합니다.

| 항목 | 수치 |
|------|------|
| MCP 서버 수 | 45개 이상 |
| 지원 AWS 서비스 | 300개 이상 |
| API 액션 | 15,000개 이상 |
| CloudWatch 전용 도구 | 31개 |
| IAM 전용 도구 | 29개 |

**설치 방법**: `claude mcp add aws-mcp-server` 명령 한 줄로 연동 완료.
`/mcp` 명령으로 서버 상태를 대화형으로 관리합니다.

### Amazon Q Developer

Amazon Q Developer는 **AWS 네이티브 서비스**로서 AWS 콘솔과 긴밀하게 통합되어 있습니다.
별도의 플러그인 설정 없이 AWS 계정의 리소스 정보를 직접 조회하고,
자연어로 인프라를 관리할 수 있습니다.

- EC2: 실행 중인 인스턴스 목록 조회, 상태 확인, 리사이징 제안
- Cost Explorer: 비용 데이터 자연어 조회 및 시각화
- Lambda/ECS/RDS: 에러 진단 및 단계별 해결 가이드 제공
- CloudFormation/CDK/Terraform: IaC 코드 생성 및 검토
- AWS Management Console: 콘솔 내 에러에 대해 즉각적인 맥락 설명 및 수정 방법 제시

> **핵심 차이**: Amazon Q Developer는 AWS 콘솔 내에서 계정 리소스에 **네이티브로 직접 접근**하는
> 반면, Claude Code는 MCP를 통한 **확장형 연동** 방식을 채택합니다.

---

## 3. IaC(Infrastructure as Code) 지원

### Claude Code

Claude Code는 **도구 중립적(Tool-agnostic)** IaC 지원을 제공합니다.
Terraform, CloudFormation, AWS CDK, Pulumi 등 주요 IaC 도구 모두를 지원하며,
조직별 커스텀 "Skills"을 통해 내부 명명 규칙, 태깅 전략, 보안 요구사항을 학습시킬 수 있습니다.

- Terraform 코드 생성 후 `terraform validate`를 자동 실행하여 자기수정(self-healing) 루프 구현
- AWS IaC MCP 서버를 통해 CDK/CloudFormation 문서 참조, 배포 검증, 모범 사례 적용
- 보안 감사(Security Audit), 비용 추정(Cost Estimation), 드리프트 탐지(Drift Detection)를 단일 AI 워크플로우로 통합
- GitHub Actions, CodePipeline 등 CI/CD 파이프라인 코드 자동 생성

### Amazon Q Developer

Amazon Q Developer는 **AWS 중심 IaC 생성**에 특화되어 있습니다.
자연어 프롬프트만으로 CloudFormation, CDK, Terraform 템플릿을 생성하며,
처음부터 작성할 필요 없이 AWS 모범 사례가 적용된 배포 가능한 코드를 즉시 제공합니다.

- CDK v1 → CDK v2 마이그레이션 자동화 지원 (전용 변환 기능)
- IDE의 `/review` 명령으로 IaC 코드 종합 리뷰 수행
- IAM 정책, 보안 그룹 규칙, 태깅 등 보안 기본값 자동 권장
- EKS, Lambda 등 특정 서비스에 특화된 Terraform 자동화 에이전트 존재

> **핵심 차이**: Claude Code는 IaC 도구의 다양성과 자율적 에이전틱 실행에 강점이 있고,
> Amazon Q Developer는 AWS 공식 문서와 깊이 연동된 정확한 AWS 특화 IaC 생성에 강점이 있습니다.

---

## 4. CLI / 터미널 통합 방식

### Claude Code

Claude Code는 태생부터 **터미널 중심(Terminal-first)** 도구입니다.

- 터미널에서 직접 코드 편집, 파일 시스템 접근, 명령 실행이 가능한 에이전틱 루프
- `claude mcp add` 명령으로 MCP 서버를 동적으로 연결·관리
- CLAUDE.md 파일에 AWS 계정 컨텍스트(리전, VPC ID, 태깅 기준, IaC 규칙)를 정의하면 이후 모든 작업에 자동 반영
- 멀티파일 변경, 커맨드 실행, 결과 확인을 하나의 에이전트 루프 안에서 처리
- **1M 토큰 컨텍스트 윈도우**로 대규모 코드베이스 전체를 한 번에 이해

### Amazon Q Developer

Amazon Q Developer는 **멀티채널 통합** 방식으로 CLI, IDE, 웹 콘솔 등 다양한 환경을 지원합니다.

- **Q CLI**: 터미널에서 자연어 채팅, 명령어 자동완성, 인라인 제안(Ghost Text) 제공
- **q translate 명령**: 자연어 영어를 바로 실행 가능한 셸 명령으로 변환
  - 예: "copy files to S3" → 완성된 AWS CLI 명령 자동 생성
- **IDE 플러그인**: VS Code, JetBrains 등에서 인라인 코드 제안 및 Q 채팅 패널 제공
- **AWS Console 통합**: 콘솔 내 어디서든 Q 버튼 클릭으로 맥락 인식 도움말 요청 가능
- **Slack/Microsoft Teams 연동**: 채팅 앱에서 직접 AWS 운영 질문 처리 가능

> 참고: Amazon Q CLI는 2026년 5월부터 **Kiro CLI**로 전환되고 있으며,
> 이후 기능 업데이트는 Kiro에서만 제공됩니다.

---

## 5. 코드 생성 및 디버깅 능력

### Claude Code

| 항목 | 내용 |
|------|------|
| 컨텍스트 윈도우 | 1M 토큰 (Amazon Q의 5배) |
| 에이전틱 코딩 | 멀티파일 자율 수정 가능 |
| 디버깅 방식 | 실행→에러→수정→재실행 자동화 루프 |
| 언어/프레임워크 | 모든 언어·프레임워크 동등 지원 |
| 벤치마크 | SWE-bench 업계 최상위 수준 |

### Amazon Q Developer

| 항목 | 내용 |
|------|------|
| 컨텍스트 윈도우 | 200K 토큰 |
| AWS 특화 코드 | Boto3, AWS SDK 정확도 탁월 |
| 코드 변환 | Java 8/11 → Java 21, Spark SQL → Athena SQL |
| 실시간 자동완성 | IDE 인라인 즉시 제안 |
| 보안 스캔 | 하드코딩 시크릿 실시간 탐지 |

---

## 6. 보안·IAM 관련 기능

### Claude Code

- AWS MCP 서버 API 호출 시 `aws:ViaAWSMCPService`, `aws:CalledViaAWSMCP` 조건 키 자동 부여
- IAM 정책으로 MCP 서버의 작업 범위(읽기 전용 vs 변경 허용)를 세밀하게 제한 가능
- Claude Platform on AWS: IAM 인증, CloudTrail 감사 로깅 완전 통합
- IaC 코드 생성 시 IAM 최소 권한 원칙 적용, 보안 그룹 규칙, 암호화 기본값 자동 권장
- Terraform Skills에 조직의 IAM 정책 표준을 인코딩하면 모든 생성 코드에 일관되게 적용

### Amazon Q Developer

- **IAM 권한 제어**: `q:PassRequest` 권한으로 Q Developer가 사용자 대신 AWS API 호출 시 범위를 IAM 정책으로 정밀 제한
- **CloudTrail 완전 통합**: 모든 Q Developer 액션이 CloudTrail에 기록되어 감사 추적 가능
- **IAM Identity Center(SSO) 지원**: Pro 플랜에서 조직 차원의 중앙화된 접근 관리
- **보안 컴플라이언스**: SOC, ISO, HIPAA, PCI 인증 완료
- **실시간 시크릿 탐지**: 코드 자동완성 중 하드코딩된 API 키, 비밀번호를 즉시 경고
- **Pro 플랜 데이터 격리**: 사용자 입력이 모델 학습에 사용되지 않음을 보장

---

## 7. 비용 최적화 기능

### Claude Code

- Terraform 생성 시 Infracost 연동을 통한 비용 추정(Cost Estimation) 자동화 가능
- AWS 리소스 설계 단계에서 Graviton 인스턴스 사용, CloudWatch 로그 보존 기간 설정 등 비용 절감 모범 사례 자동 반영 (Skills 설정 시)
- AWS 비용 데이터를 MCP 서버를 통해 조회하고 자연어로 분석하는 워크플로우 구성 가능
- 멀티클라우드 환경에서 클라우드 간 비용 비교 분석 가능

### Amazon Q Developer

- **자연어 비용 조회**: Cost Explorer 데이터를 자연어 질문으로 즉시 조회
  - 예: "지난달 US East 리전에서 가장 비용이 많이 든 서비스는?"
- **비용 시각화(Artifacts)**: 2026년 2월 출시 기능으로 비용 데이터를 테이블·차트로 시각화
- **최적화 권장사항 통합**: Cost Optimization Hub, AWS Compute Optimizer, Savings Plans 권장사항을 하나의 인터페이스에서 확인
- **유휴 리소스 탐지**: 사용하지 않는 인스턴스, 과잉 프로비저닝된 리소스를 자동으로 식별하고 리사이징 제안
- **IaC 생성 시 비용 절감 기본값**: Graviton 인스턴스, 비용 효율적인 스토리지 클래스 자동 권장

---

## 8. 멀티클라우드 지원 여부

### Claude Code — 강력한 멀티클라우드 지원

| 클라우드 | 지원 방식 |
|----------|-----------|
| AWS | Claude Platform on AWS + AWS MCP 서버 완전 통합 |
| GCP | Vertex AI를 통해 Claude Code 네이티브 실행, GCP IAM 사용 |
| Azure | Claude Managed Agents + Azure Active Directory 연동 |
| 멀티클라우드 | AWS, Azure, GCP, 엣지 위치 전반 배포 파이프라인 구성 가능 |

### Amazon Q Developer — AWS 단독 특화

- AWS 서비스·리소스에 대한 깊은 맥락 이해는 탁월하나, Azure나 GCP 리소스에 대한 네이티브 연동 없음
- Terraform을 통해 멀티클라우드 IaC 코드를 생성할 수는 있으나, 다른 클라우드 콘솔과의 직접 연동은 미지원
- AWS 에코시스템 내에서의 최적화에 집중된 포지셔닝

---

## 9. 가격 정책

### Claude Code 가격 정책

| 플랜 | 월 비용 | 주요 내용 |
|------|---------|-----------|
| Pro | $20/월 | Claude Code 포함, 개인용 기본 플랜 |
| Max 5x | $100/월 | Pro 대비 5배 사용량, 대규모 작업 적합 |
| Max 20x | $200/월 | Pro 대비 20배 사용량, 헤비 유저용 |
| Team Standard | $25/시트 | 팀용 기본 플랜 |
| Team Premium | $125/시트 | Claude Code 포함, 팀용 프리미엄 |
| Enterprise | 협의 | API 사용량 기반 맞춤형 계약 |
| Claude Platform on AWS | AWS Marketplace 소비 기반 | Claude Consumption Units로 과금, AWS 청구서 통합 |

### Amazon Q Developer 가격 정책

| 플랜 | 월 비용 | 주요 내용 |
|------|---------|-----------|
| Free Tier | $0 | 월 50회 에이전틱 요청, 코드 제안, 보안 스캔 |
| Pro | $19/유저/월 | 무제한 채팅, 4,000 LOC 변환, IP 보호, SSO |
| LOC 초과 사용 | $0.003/LOC | Pro 플랜 변환 한도 초과 시 추가 과금 |

> ⚠️ Amazon Q Developer는 2026년 5월 15일부터 신규 가입이 중단되었습니다.

---

## 10. 실제 AWS 작업 자동화 능력

### Claude Code

**배포 자동화**
- Terraform/CDK 코드 생성 → 검증 → 플랜 확인 → 배포까지 에이전틱 루프 내에서 자동 수행
- GitHub Actions, CodePipeline 등 CI/CD 파이프라인 코드를 자동 생성하고 디버깅
- CLAUDE.md에 배포 규칙(리전, VPC, 태깅)을 정의하면 이후 모든 배포에 일관되게 적용
- 멀티파일 인프라 코드 변경 작업을 단일 에이전트 세션에서 일괄 처리

**모니터링**
- AWS MCP 서버의 CloudWatch 도구(31개)를 통해 메트릭 조회, 로그 분석, 알람 설정을 자연어로 제어
- 이상 징후 탐지 → 원인 분석 → 알람 설정 → 수정 코드 생성까지 연속적으로 자동화

**트러블슈팅**
- 1M 토큰 컨텍스트로 복잡한 에러 로그, 스택 트레이스, 코드베이스를 동시에 분석
- 에러 원인 추적 → 코드 수정 → 테스트 실행 → 결과 검증을 자율적으로 수행

### Amazon Q Developer

**배포 자동화**
- AWS 콘솔 내 Q Developer를 통해 CloudFormation 스택 배포를 자연어로 제어
- "이 아키텍처를 배포해줘"라는 요청만으로 IaC 코드 생성부터 배포 가이드까지 제공
- CodeCatalyst 연동으로 CI/CD 파이프라인을 콘솔에서 직접 관리

**모니터링**
- AWS 콘솔에서 발생하는 에러에 대해 즉각적인 맥락 설명과 단계별 해결책 제공
- GuardDuty, CloudTrail 로그를 분석하여 보안 이슈와 운영 이상을 자동 탐지
- Slack/Teams에서 자연어로 리소스 상태를 조회하고 알림 수신 가능

**트러블슈팅**
- AWS 콘솔 내 에러 메시지 옆에 Q 버튼으로 즉각적인 진단 및 처방 제공
- AWS 서비스별 전문화된 트러블슈팅 가이드(AWS 공식 문서 기반) 제공
- `q:PassRequest` 권한을 통해 Q가 사용자 대신 AWS API를 호출하여 실제 리소스 상태 확인 및 진단

---

## 11. 종합 비교 요약

| 항목 | Claude Code | Amazon Q Developer |
|------|-------------|-------------------|
| **포지셔닝** | 범용 에이전틱 AI, AWS 통합 확장 | AWS 네이티브 AI (→ Kiro로 전환 중) |
| **AWS 연동** | MCP 서버 기반 (45+ 서버, 300+ 서비스) | 네이티브 콘솔 직접 연동 |
| **IaC 지원** | Terraform, CDK, CloudFormation, Pulumi (도구 중립) | CloudFormation, CDK, Terraform (AWS 특화) |
| **터미널 통합** | 터미널 퍼스트, 에이전틱 루프 | CLI + IDE 플러그인 멀티채널 |
| **컨텍스트 윈도우** | 1M 토큰 | 200K 토큰 |
| **보안·IAM** | MCP 조건 키, IAM 세분화 제어 | 네이티브 IAM, CloudTrail, SOC/ISO/HIPAA |
| **비용 최적화** | IaC 설계 단계 비용 절감, 간접 지원 | FinOps 전용 기능, Cost Explorer 직접 통합 |
| **멀티클라우드** | AWS + GCP + Azure 완전 지원 | AWS 전용 |
| **가격** | $20~$200/월 (플랜별), 토큰 기반 | $0 / $19/유저/월, 정액제 |
| **가용성** | 현재 적극 개발·확장 중 | 신규 가입 중단, 2027.4 서비스 종료 |
| **사용자 만족도** | 92% (Excellent) | 89% (Great) |

---

## 12. 선택 가이드

### Claude Code를 선택해야 하는 경우

- ✅ 복잡한 멀티스텝 코딩 및 자율 에이전틱 작업이 필요한 경우
- ✅ 멀티클라우드 환경 (AWS + GCP + Azure) 동시 운영
- ✅ 대규모 레거시 코드베이스 분석 (1M 토큰 컨텍스트 활용)
- ✅ 터미널 중심 워크플로우를 선호하는 팀
- ✅ Terraform, Pulumi 등 다양한 IaC 도구 사용 환경
- ✅ 장기적으로 안정적인 서비스 사용이 필요한 경우

### Amazon Q Developer를 선택해야 하는 경우

- ✅ 순수 AWS 단일 클라우드 환경 (단, 신규 가입 불가)
- ✅ AWS 콘솔 중심 워크플로우를 가진 팀
- ✅ 예측 가능한 정액제 비용 ($19/월) 관리가 중요한 경우
- ✅ FinOps 기능이 핵심 요구사항인 경우
- ⚠️ **주의**: 현재 신규 가입이 불가능하므로, 실질적으로는 후속 제품 **Kiro** 도입 검토 필요

---

## 참고 자료

- [Claude Platform on AWS is now generally available - AWS](https://aws.amazon.com/about-aws/whats-new/2026/05/claude-platform-aws/)
- [Amazon Q Developer end-of-support announcement - AWS Blog](https://aws.amazon.com/blogs/devops/amazon-q-developer-end-of-support-announcement/)
- [The AWS MCP Server is now generally available - AWS Blog](https://aws.amazon.com/blogs/aws/the-aws-mcp-server-is-now-generally-available/)
- [Amazon Q Developer vs Claude Code (2026) - Augment Code](https://www.augmentcode.com/tools/amazon-q-developer-vs-claude-code)
- [AI for Software Development – Amazon Q Developer Features](https://aws.amazon.com/q/developer/features/)
- [Claude Code Pricing In 2026 - CloudZero](https://www.cloudzero.com/blog/claude-code-pricing/)
- [What Is Kiro? AWS's New AI Coding Platform Explained - CloudVisor](https://cloudvisor.co/what-is-kiro/)

---

*본 문서는 2026년 6월 기준으로 작성되었습니다. 각 제품의 기능 및 가격은 변경될 수 있습니다.*
