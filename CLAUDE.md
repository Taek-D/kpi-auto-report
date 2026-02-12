# E-commerce KPI Daily Auto-Report System

## Project Overview

n8n 기반 E-commerce KPI 자동 리포트 시스템. 매일 아침 PostgreSQL에서 KPI를 조회하여 Slack으로 전송.

## Tech Stack

- **Database**: PostgreSQL (Supabase)
- **Workflow**: n8n (JSON workflow + JavaScript Function Node)
- **Messaging**: Slack API (Incoming Webhooks)
- **Query Language**: SQL (Window Functions, CTEs)

## Project Structure

```
KPI_Auto_Report(Athome)/
├── schema/                 # DB 스키마 정의
│   └── daily_summary.sql   # daily_summary 테이블 DDL
├── queries/                # SQL 쿼리 파일 (n8n에서 실행)
│   ├── kpis_yesterday.sql  # 어제 KPI 조회
│   ├── kpis_last_week.sql  # 지난주 동일 요일 KPI (WoW 비교용)
│   └── top_products.sql    # 매출 상위 3개 제품
├── n8n/                    # n8n 워크플로우
│   ├── workflow.json       # 워크플로우 정의 (import용)
│   └── transform.js        # Function Node 로직 (WoW 계산, 이상 탐지, Slack 포맷팅)
├── docs/                   # 문서
│   ├── SETUP.md
│   ├── SQL_GUIDE.md
│   └── SLACK_INTEGRATION.md
└── tests/
    └── TEST_RESULTS.md
```

## SQL Conventions

- CTE(WITH절) 사용하여 쿼리 가독성 확보
- Window Functions 적극 활용: LAG(), RANK(), OVER()
- 날짜 필터: `CURRENT_DATE - INTERVAL '1 day'` 형식
- 금액은 DECIMAL(14,2), 비율은 DECIMAL(5,2)
- NULLIF로 나눗셈 0 방지: `SUM(a) / NULLIF(COUNT(b), 0)`
- 한글 주석으로 쿼리 목적 명시

## JavaScript Conventions (n8n Function Node)

- n8n 입력: `$input.all()[index].json` 형식
- 반환: `{ json: { ... } }` 형식
- 숫자 포맷: `Number(val).toLocaleString('ko-KR')`
- 함수 선언식 사용 (`function name()`, 화살표 함수 아님)
- 각 섹션을 `// ===` 블록 주석으로 구분

## Key Business Logic

### KPI Metrics
1. 총 매출 (total_revenue): SUM(order_amount)
2. 총 주문 수 (total_orders): COUNT(DISTINCT order_id)
3. 평균 주문 금액 (avg_order_value): revenue / orders
4. 전환율 (conversion_rate): orders / visitors * 100
5. WoW 변화율: ((current - previous) / previous) * 100

### Anomaly Detection Thresholds
- Revenue drop > 20% WoW -> Critical
- Orders drop > 15% WoW -> Warning
- Conversion rate drop > 10%p WoW -> Warning

## Data Flow

```
Cron (08:00) -> PostgreSQL (3 queries parallel) -> JS Transform -> Slack Message
```

## Testing

- SQL 쿼리: psql로 직접 실행하여 검증
- n8n: UI에서 "Execute Workflow" 수동 실행
- 이상 탐지: transform.js 로직 수동 검증

## Important Notes

- 환경변수로 관리: DB 자격증명, Slack Webhook URL
- queries/ 의 SQL 파일은 n8n PostgreSQL Node에서 참조
- transform.js는 n8n Function Node에 붙여넣어 사용
- workflow.json은 n8n에 import하여 사용
