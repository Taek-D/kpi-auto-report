# E-commerce KPI Daily Auto-Report System

> **매일 아침, Slack으로 KPI 리포트가 자동 도착합니다.**

PostgreSQL(Supabase)에서 KPI를 조회하고, WoW 분석 + 이상 탐지를 수행한 뒤 Slack으로 전송하는 n8n 기반 자동화 파이프라인입니다.

## 시스템 아키텍처

```
┌──────────────┐
│   Schedule   │  매일 08:00 KST
│  (Cron)      │
└──────┬───────┘
       │
       ├──────────────────┬──────────────────┐
       ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Supabase    │  │  Supabase    │  │  Supabase    │
│  Yesterday   │  │  Last Week   │  │ Top Products │
│  KPIs        │  │  KPIs        │  │              │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                  │
       └────────┬────────┴──────────────────┘
                ▼
       ┌──────────────┐
       │    Merge     │  3개 데이터 소스 동기화
       │ Collect All  │
       └──────┬───────┘
              ▼
       ┌──────────────┐
       │  WoW Analysis│  변화율 계산 + 이상 탐지
       │  & Anomaly   │
       └──────┬───────┘
              ▼
       ┌──────────────┐
       │    Slack     │  Webhook으로 리포트 전송
       │  Send Alert  │
       └──────────────┘
```

**7개 노드** | 병렬 데이터 수집 | WoW 분석 | 이상 탐지 알림

## 핵심 기능

- **일일 KPI 리포트**: 매출, 주문 수, 평균 주문 금액, 전환율
- **WoW 비교 분석**: 전주 동일 요일 대비 증감률 (%) 및 트렌드 아이콘 (↑↓→)
- **이상 탐지**: 매출 -20% 이상 하락(Critical), 주문 -15%(Warning), 전환율 -10%p(Warning)
- **매출 Top 3 제품**: 일일 매출 기준 상위 제품 랭킹

## Slack 메시지 예시

```
📊 일일 E-commerce KPI 리포트 | 2026-02-13

핵심 지표 (어제 기준)
━━━━━━━━━━━━━━━━━━━━━
💰 매출: ₩12,500,000 (+8.3% ↑)
📦 주문 수: 342건 (+5.2% ↑)
🛒 평균 주문 금액: ₩36,549 (+2.9% ↑)
📈 전환율: 3.2% (+0.4%p ↑)

🏆 매출 상위 3개 제품
1. 무선 이어폰 Pro: ₩2,340,000 (156개 판매)
2. 스마트워치 S3: ₩1,890,000 (63개 판매)
3. USB-C 허브 7in1: ₩1,230,000 (205개 판매)
```

## 기술 스택

| 구분 | 기술 | 용도 |
|------|------|------|
| Database | PostgreSQL (Supabase) | KPI 데이터 저장 |
| API | Supabase REST API (RPC) | 서버리스 함수 호출 |
| Workflow | n8n (Docker) | 7노드 자동화 파이프라인 |
| Messaging | Slack Incoming Webhooks | 리포트 전송 |
| Query | SQL (Window Functions, CTEs) | 데이터 분석 쿼리 |

## 프로젝트 구조

```
KPI_Auto_Report/
├── docker-compose.yml       # n8n Docker 컨테이너 설정
├── .env.example             # 환경변수 템플릿
├── schema/
│   └── daily_summary.sql    # DB 스키마 DDL
├── queries/                 # SQL 쿼리 (Supabase RPC 함수 원본)
│   ├── kpis_yesterday.sql   # 어제 KPI 조회
│   ├── kpis_last_week.sql   # 전주 동일 요일 KPI
│   └── top_products.sql     # 매출 상위 제품
├── n8n/                     # n8n 워크플로우
│   ├── workflow.json        # 7노드 워크플로우 정의
│   ├── transform.js         # WoW 분석 + 이상 탐지 + 메시지 포맷팅
│   └── slack_send.js        # Slack Webhook 전송
└── docs/
    ├── SETUP.md
    ├── SQL_GUIDE.md
    └── SLACK_INTEGRATION.md
```

## 빠른 시작

### 1. 환경변수 설정

```bash
cp .env.example .env
# .env 파일을 열어서 Supabase, Slack 정보 입력
```

### 2. n8n 실행

```bash
docker-compose up -d
# http://localhost:5678 접속 (기본 ID: admin / PW: changeme)
```

### 3. 워크플로우 설정

1. n8n UI에서 **Import from File** → `n8n/workflow.json` 선택
2. **"WoW Analysis & Anomaly Detection"** 노드 → `n8n/transform.js` 내용 붙여넣기
3. **"Slack: Send KPI Alert"** 노드 → `n8n/slack_send.js` 내용 붙여넣기
4. `slack_send.js` 내 `SLACK_WEBHOOK_URL`을 실제 Webhook URL로 교체
5. **Execute Workflow**로 테스트

### 4. Supabase RPC 함수

Supabase SQL Editor에서 아래 3개 함수를 생성해야 합니다:

```sql
-- 어제 KPI 조회
CREATE OR REPLACE FUNCTION get_kpis_yesterday()
RETURNS TABLE(...) AS $$ ... $$;

-- 전주 동일 요일 KPI
CREATE OR REPLACE FUNCTION get_kpis_last_week()
RETURNS TABLE(...) AS $$ ... $$;

-- 매출 상위 제품
CREATE OR REPLACE FUNCTION get_top_products()
RETURNS TABLE(...) AS $$ ... $$;
```

SQL 원본은 `queries/` 폴더를 참조하세요.

## 주요 KPI

| 지표 | 설명 | 계산식 |
|------|------|--------|
| 총 매출 | 일일 총 매출액 | `SUM(order_amount)` |
| 총 주문 수 | 완료된 주문 건수 | `COUNT(DISTINCT order_id)` |
| 평균 주문 금액 (AOV) | 건당 평균 금액 | `revenue / orders` |
| 전환율 | 방문자 대비 주문 비율 | `orders / visitors * 100` |
| WoW 변화율 | 전주 동요일 대비 증감 | `(current - previous) / previous * 100` |

## 이상 탐지 기준

| 수준 | 조건 | 알림 |
|------|------|------|
| Critical | 매출 WoW -20% 이상 하락 | 🚨 즉시 대응 필요 |
| Warning | 주문 수 WoW -15% 이상 하락 | ⚠️ 모니터링 필요 |
| Warning | 전환율 WoW -10%p 이상 하락 | ⚠️ 모니터링 필요 |

## 데이터 파이프라인 상세

```
08:00 KST
    │
    ▼
[Schedule Trigger]
    │
    ├─► Supabase RPC: get_kpis_yesterday()   ──┐
    ├─► Supabase RPC: get_kpis_last_week()   ──┼─► [Merge: Append]
    └─► Supabase RPC: get_top_products()     ──┘        │
                                                         ▼
                                               [WoW Analysis Code]
                                                  - 변화율 계산
                                                  - 이상 탐지
                                                  - Slack 메시지 포맷팅
                                                         │
                                                         ▼
                                               [Slack Send Code]
                                                  - this.helpers.httpRequest()
                                                  - Webhook POST
```

## SQL 주요 기법

- **CTE (WITH절)**: 복잡한 쿼리를 단계별로 분해
- **Window Functions**: `LAG()` 전주 비교, `RANK()` 제품 순위
- **날짜 필터**: `CURRENT_DATE - INTERVAL '1 day'`
- **0 나눗셈 방지**: `NULLIF(COUNT(b), 0)`

## 배운 점

### 기술적
- n8n 워크플로우 자동화 및 Code 노드 활용
- Supabase REST API (RPC) 서버리스 함수 설계
- SQL Window Functions (LAG, RANK, OVER)
- Docker Compose를 활용한 n8n 배포
- Slack Incoming Webhooks 연동

### 비즈니스
- 의미 있는 KPI 지표 선정 및 임계값 설계
- WoW 분석으로 주간 트렌드 파악
- 이상 탐지 자동화로 빠른 의사결정 지원

## 향후 계획

- [ ] 주간/월간 요약 리포트 추가
- [ ] 예측 분석 (ML 기반 트렌드 예측)
- [ ] Grafana 대시보드 연동
- [ ] 멀티 채널 알림 (이메일, Teams)

## 라이선스

이 프로젝트는 포트폴리오 목적으로 제작되었습니다.

---

**Built for automated business intelligence**
