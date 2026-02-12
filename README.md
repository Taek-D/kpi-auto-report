# E-commerce KPI Daily Auto-Report System

> **Project Code**: `ecommerce-kpi-reporter`  
> **Version**: 1.0  
> **Status**: In Development

## 📊 프로젝트 개요

E-commerce 비즈니스 KPI를 매일 아침 8시에 Slack으로 자동 전송하는 경량 보고 시스템입니다. 정적 분석(Coupang Dashboard)에서 자동화된 모니터링으로의 진화를 보여주는 프로젝트입니다.

### 핵심 기능

- 📈 **일일 KPI 자동 전송**: 매일 아침 8시 Slack 메시지로 핵심 지표 전달
- 🔄 **전주 대비 성과**: WoW(Week-over-Week) 비교 분석
- ⚠️ **이상 탐지**: 전환율/매출 급락 시 자동 알림
- 🏆 **상위 제품 분석**: 일일 매출 Top 3 제품 리포트

## 🏗️ 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                     n8n Workflow                             │
│                                                              │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌─────────┐ │
│  │  Cron    │──▶│PostgreSQL│──▶│ Python   │──▶│  Slack  │ │
│  │ Trigger  │   │  Query   │   │Transform │   │  Send   │ │
│  │ 08:00    │   │  Node    │   │  Node    │   │ Message │ │
│  └──────────┘   └──────────┘   └──────────┘   └─────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 빠른 시작

### 사전 요구사항

- PostgreSQL (Supabase)
- n8n (Docker 또는 npm)
- Slack Workspace (Webhook 설정 필요)

### 설치 방법

상세한 설치 가이드는 [`docs/SETUP.md`](docs/SETUP.md)를 참조하세요.

## 📁 프로젝트 구조

```
KPI_Auto_Report(Athome)/
├── schema/                 # 데이터베이스 스키마
│   └── daily_summary.sql
├── queries/               # SQL 쿼리 파일
│   ├── kpis_yesterday.sql
│   ├── kpis_last_week.sql
│   └── top_products.sql
├── n8n/                   # n8n 워크플로우
│   ├── workflow.json
│   └── transform.js
├── docs/                  # 문서
│   ├── SETUP.md
│   ├── SQL_GUIDE.md
│   └── SLACK_INTEGRATION.md
└── tests/                 # 테스트 결과
    └── TEST_RESULTS.md
```

## 💻 핵심 기술 스택

- **데이터베이스**: PostgreSQL (Supabase)
- **워크플로우 자동화**: n8n
- **메시징**: Slack API (Incoming Webhooks)
- **쿼리 언어**: SQL (Window Functions, CTEs)

## 📊 주요 KPI

1. **총 매출** (₩): 일일 총 매출액
2. **총 주문 수** (#): 완료된 주문 건수
3. **평균 주문 금액** (₩): AOV (Average Order Value)
4. **전환율** (%): 방문자 대비 주문 전환율
5. **WoW 변화율** (%): 전주 동일 요일 대비 증감률

## 🎯 이 프로젝트가 특별한 이유

| 측면 | Marketing ROI 프로젝트 | Finance Close Pack | **이 프로젝트** |
|------|----------------------|-------------------|---------------------|
| **도메인** | 외부 광고 플랫폼 | 월간 재무 KPI | **내부 커머스 KPI** |
| **빈도** | 일일 | 월간 | **일일** |
| **도구** | Google Apps Script | Airflow | **n8n (경량)** |
| **데이터 소스** | 광고 API | MySQL | **PostgreSQL** |
| **초점** | 마케팅 ROI 최적화 | 재무 보고 | **비즈니스 모니터링** |

## 📚 문서

- [설치 가이드](docs/SETUP.md)
- [SQL 쿼리 설명](docs/SQL_GUIDE.md)
- [Slack 연동 가이드](docs/SLACK_INTEGRATION.md)
- [테스트 결과](tests/TEST_RESULTS.md)

## 🧪 테스트

```bash
# SQL 쿼리 테스트
psql -U user -d database -f queries/kpis_yesterday.sql

# n8n 워크플로우 수동 실행
# n8n UI에서 "Execute Workflow" 버튼 클릭
```

## 📖 배운 점

### 기술적 스킬
- ✅ SQL Window Functions (LAG, RANK)
- ✅ n8n 워크플로우 자동화
- ✅ PostgreSQL 스키마 설계
- ✅ Slack API 연동

### 비즈니스 스킬
- ✅ 의미 있는 KPI 선정
- ✅ 이상 탐지 로직 구현
- ✅ 비기술 이해관계자를 위한 커뮤니케이션

## 🛠️ 향후 계획

- [ ] 실시간 스트리밍 (현재는 일일 배치)
- [ ] 예측 분석 (ML 기반 트렌드 예측)
- [ ] 멀티 채널 통합 (네이버, G마켓 등)

## 📝 라이선스

이 프로젝트는 포트폴리오 목적으로 제작되었습니다.

## 👤 작성자

**택** - Data Analyst Portfolio Project

---

**Built with ❤️ for automated business intelligence**
