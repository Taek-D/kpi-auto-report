# ecommerce-kpi-reporter Design Document

> **Summary**: Plan에서 식별된 Gap 6개를 해결하는 상세 설계
>
> **Project**: E-commerce KPI Daily Auto-Report System
> **Version**: 1.0
> **Author**: 택
> **Date**: 2026-02-13
> **Status**: Draft
> **Planning Doc**: [PLAN.md](./PLAN.md)

---

## 1. Overview

### 1.1 Design Goals

Plan 단계에서 식별된 **Critical 3개 + Major 3개 Gap**을 해결하여 n8n 워크플로우가 실제로 동작하도록 만든다.

| 목표 | 설명 |
|------|------|
| 워크플로우 정합성 | workflow.json이 실제 SQL 쿼리와 transform.js를 정확히 반영 |
| 데이터 무결성 | 전환율/방문자 데이터 처리 전략 확정 |
| 방어적 코딩 | null/empty 입력에 대한 안전한 처리 |
| 환경 분리 | 환경변수를 통한 설정 외부화 |

### 1.2 Design Principles

- **현실적 접근**: visitors 테이블이 없으므로 전환율은 daily_summary 기반으로 전환
- **최소 변경**: 기존 코드 구조를 유지하면서 Gap만 정확히 해결
- **n8n 호환성**: n8n Function Node의 실제 동작 방식에 맞춘 데이터 구조

---

## 2. Architecture

### 2.1 현재 구조 (변경 없음)

```
Cron (08:00 KST)
  │
  ├──▶ PostgreSQL Node 1 ─── kpis_yesterday.sql ──┐
  ├──▶ PostgreSQL Node 2 ─── kpis_last_week.sql ──┼──▶ Transform ──▶ Slack
  └──▶ PostgreSQL Node 3 ─── top_products.sql ────┘
```

### 2.2 n8n Transform Node 입력 구조 (핵심 설계)

n8n에서 3개의 PostgreSQL 노드가 각각 다른 input index로 Transform Node에 연결됨.

```
Input 0 (Yesterday KPIs):   $input.all()[0].json = { total_orders, total_revenue, ... }
Input 1 (Last Week KPIs):   $input.all()[1].json = { total_orders, total_revenue, ... }
Input 2 (Top Products):     $input.all()[2].json = { rank, product_name, total_revenue, ... }
```

**중요**: n8n PostgreSQL Node는 결과를 **행 단위 item**으로 반환.
- Yesterday/Last Week: 1행 → `$input.all()[0].json`에 해당 행 데이터
- Top Products: 3행 → `$input.all()[2].json`은 **첫 번째 행만** 포함. 나머지는 별도 item

### 2.3 수정 대상 파일

| 파일 | 변경 유형 | 관련 Gap |
|------|----------|---------|
| `n8n/workflow.json` | 쿼리 내용 교체 | G-1 |
| `queries/kpis_yesterday.sql` | 전환율 로직 변경 | G-2 |
| `queries/kpis_last_week.sql` | 전환율 로직 변경 | G-2 |
| `n8n/transform.js` | null 방어 + topProducts 구조 수정 | G-4, G-5 |
| `.env.example` (신규) | 환경변수 템플릿 | G-6 |

---

## 3. Gap 해결 상세 설계

### 3.1 [G-1] workflow.json 쿼리 불일치 해결

**문제**: workflow.json의 PostgreSQL 노드에 placeholder 쿼리만 존재

**해결**: 각 PostgreSQL 노드의 `query` 필드에 실제 SQL 쿼리 전문을 삽입

#### 변경 사항

**postgres-yesterday 노드** (`workflow.json:24`):
```json
"query": "WITH yesterday_kpis AS (\n    SELECT \n        order_date,\n        COUNT(DISTINCT order_id) AS total_orders,\n        SUM(order_amount) AS total_revenue,\n        COUNT(DISTINCT customer_id) AS unique_customers,\n        ROUND(\n            SUM(order_amount) / NULLIF(COUNT(DISTINCT order_id), 0), \n            2\n        ) AS avg_order_value,\n        SUM(quantity) AS total_units_sold\n    FROM orders\n    WHERE order_date = CURRENT_DATE - INTERVAL '1 day'\n    GROUP BY order_date\n)\nSELECT \n    order_date,\n    total_orders,\n    total_revenue,\n    unique_customers,\n    avg_order_value,\n    total_units_sold,\n    COALESCE(ds.total_visitors, 0) AS total_visitors,\n    COALESCE(ds.conversion_rate, 0.00) AS conversion_rate\nFROM yesterday_kpis yk\nLEFT JOIN daily_summary ds ON ds.summary_date = yk.order_date;"
```

**postgres-lastweek 노드** (`workflow.json:37`):
```json
"query": "WITH last_week_kpis AS (\n    SELECT \n        order_date,\n        COUNT(DISTINCT order_id) AS total_orders,\n        SUM(order_amount) AS total_revenue,\n        COUNT(DISTINCT customer_id) AS unique_customers,\n        ROUND(\n            SUM(order_amount) / NULLIF(COUNT(DISTINCT order_id), 0), \n            2\n        ) AS avg_order_value,\n        SUM(quantity) AS total_units_sold\n    FROM orders\n    WHERE order_date = CURRENT_DATE - INTERVAL '8 days'\n    GROUP BY order_date\n)\nSELECT \n    order_date,\n    total_orders,\n    total_revenue,\n    unique_customers,\n    avg_order_value,\n    total_units_sold,\n    COALESCE(ds.total_visitors, 0) AS total_visitors,\n    COALESCE(ds.conversion_rate, 0.00) AS conversion_rate\nFROM last_week_kpis lk\nLEFT JOIN daily_summary ds ON ds.summary_date = lk.order_date;"
```

**postgres-products 노드** (`workflow.json:51`):
```json
"query": "WITH product_sales AS (\n    SELECT \n        product_id,\n        product_name,\n        SUM(order_amount) AS total_revenue,\n        SUM(quantity) AS units_sold,\n        COUNT(DISTINCT order_id) AS order_count,\n        ROUND(AVG(unit_price), 2) AS avg_unit_price\n    FROM orders\n    WHERE order_date = CURRENT_DATE - INTERVAL '1 day'\n    GROUP BY product_id, product_name\n),\nranked_products AS (\n    SELECT \n        product_id,\n        product_name,\n        total_revenue,\n        units_sold,\n        order_count,\n        avg_unit_price,\n        RANK() OVER (ORDER BY total_revenue DESC) AS revenue_rank,\n        ROUND(\n            (total_revenue / SUM(total_revenue) OVER ()) * 100, \n            2\n        ) AS revenue_share_pct\n    FROM product_sales\n)\nSELECT \n    revenue_rank AS rank,\n    product_name,\n    total_revenue,\n    units_sold,\n    order_count,\n    avg_unit_price,\n    revenue_share_pct\nFROM ranked_products\nWHERE revenue_rank <= 3\nORDER BY revenue_rank;"
```

---

### 3.2 [G-2] 전환율/방문자 Placeholder 해결

**문제**: `total_visitors=0`, `conversion_rate=0.00` 하드코딩

**해결 전략**: `daily_summary` 테이블에 visitors/conversion_rate가 이미 GENERATED 컬럼으로 존재하므로, KPI 쿼리에서 `daily_summary`를 LEFT JOIN하여 가져온다.

#### SQL 변경 - kpis_yesterday.sql

```sql
-- 변경 전 (Line 44-45)
0 AS total_visitors,
0.00 AS conversion_rate

-- 변경 후: daily_summary 테이블에서 가져오기
COALESCE(ds.total_visitors, 0) AS total_visitors,
COALESCE(ds.conversion_rate, 0.00) AS conversion_rate
FROM yesterday_kpis yk
LEFT JOIN daily_summary ds ON ds.summary_date = yk.order_date;
```

#### SQL 변경 - kpis_last_week.sql

동일한 패턴 적용:

```sql
COALESCE(ds.total_visitors, 0) AS total_visitors,
COALESCE(ds.conversion_rate, 0.00) AS conversion_rate
FROM last_week_kpis lk
LEFT JOIN daily_summary ds ON ds.summary_date = lk.order_date;
```

**COALESCE 사용 이유**: daily_summary에 해당 날짜 데이터가 없을 수 있으므로 NULL 방지.

---

### 3.3 [G-4] transform.js Null 방어 코드

**문제**: `$input.all()[0]`이 undefined일 경우 에러 발생

**해결**: 입력 검증 + 기본값 fallback 추가

#### 변경 위치: `n8n/transform.js` Line 14-16

```javascript
// 변경 전
const yesterday = $input.all()[0].json;
const lastWeek = $input.all()[1].json;
const topProducts = $input.all()[2].json;

// 변경 후
const inputs = $input.all();

const DEFAULT_KPI = {
  total_orders: 0,
  total_revenue: 0,
  avg_order_value: 0,
  conversion_rate: 0,
  unique_customers: 0,
  total_units_sold: 0,
  total_visitors: 0
};

const yesterday = (inputs[0] && inputs[0].json) ? inputs[0].json : DEFAULT_KPI;
const lastWeek = (inputs[1] && inputs[1].json) ? inputs[1].json : DEFAULT_KPI;
const topProductsRaw = inputs.slice(2);
```

#### 추가: 데이터 없음 감지

```javascript
// 데이터 없음 감지
const hasNoData = !inputs[0] || !inputs[0].json || !inputs[0].json.total_orders;

if (hasNoData) {
  return {
    json: {
      message: `📊 **일일 E-commerce KPI 리포트** | ${new Date().toISOString().split('T')[0]}\n\n⚠️ 어제 날짜에 대한 데이터가 없습니다. 데이터 소스를 확인해 주세요.`,
      metadata: {
        date: new Date().toISOString().split('T')[0],
        has_data: false
      }
    }
  };
}
```

---

### 3.4 [G-5] topProducts 입력 구조 정합성

**문제**: n8n PostgreSQL 노드는 결과를 행 단위 item으로 반환. 3행 결과 → 3개 item.
그런데 Transform Node에 3개 입력(index 0,1,2)이 이미 연결되어 있으므로, Top Products의 3행은 **index 2의 단일 입력으로** 들어오고, 그 안에 3행이 포함됨.

**해결**: n8n의 실제 동작에 맞춰 topProducts 처리 로직 수정

#### 변경 위치: `n8n/transform.js` Line 71-75

```javascript
// 변경 전
const top3Formatted = topProducts.slice(0, 3).map((p, index) => {
  const revenue = Number(p.total_revenue).toLocaleString('ko-KR');
  const units = Number(p.units_sold).toLocaleString('ko-KR');
  return `${index + 1}. **${p.product_name}**: ₩${revenue} (${units} 개 판매)`;
}).join('\n');

// 변경 후
// n8n은 input index 2로 들어온 모든 행을 inputs에서 추출
const topProducts = topProductsRaw.map(item => item.json).filter(Boolean);

const top3Formatted = topProducts.length > 0
  ? topProducts.slice(0, 3).map(function(p, index) {
      const revenue = Number(p.total_revenue || 0).toLocaleString('ko-KR');
      const units = Number(p.units_sold || 0).toLocaleString('ko-KR');
      return (index + 1) + '. **' + (p.product_name || '알 수 없음') + '**: ₩' + revenue + ' (' + units + ' 개 판매)';
    }).join('\n')
  : '데이터 없음';
```

**참고**: `inputs.slice(2)`는 index 2 이후의 모든 item을 가져옴. n8n의 Merge Node 없이 직접 연결된 경우, 3번째 입력의 모든 행이 순서대로 들어옴.

---

### 3.5 [G-6] 환경변수 설정

**문제**: .env 파일 부재

**해결**: `.env.example` 파일 생성

#### 신규 파일: `.env.example`

```env
# PostgreSQL (Supabase)
POSTGRES_HOST=db.xxxxx.supabase.co
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password-here

# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00/B00/XXX

# n8n
N8N_PORT=5678
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=your-n8n-password

# Tableau (optional)
TABLEAU_DASHBOARD_URL=https://tableau.example.com/dashboard
```

---

## 4. Data Model

### 4.1 기존 테이블 (변경 없음)

**orders**:
```sql
CREATE TABLE orders (
    order_id VARCHAR(50) PRIMARY KEY,
    order_date DATE NOT NULL,
    product_id VARCHAR(50),
    product_name VARCHAR(200),
    quantity INTEGER,
    unit_price DECIMAL(10, 2),
    order_amount DECIMAL(12, 2),
    customer_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);
```

**daily_summary** (GENERATED 컬럼 포함):
```sql
CREATE TABLE daily_summary (
    summary_date DATE PRIMARY KEY,
    total_revenue DECIMAL(14, 2) NOT NULL DEFAULT 0,
    total_orders INTEGER NOT NULL DEFAULT 0,
    total_visitors INTEGER NOT NULL DEFAULT 0,
    avg_order_value DECIMAL(10, 2) GENERATED ALWAYS AS (...) STORED,
    conversion_rate DECIMAL(5, 2) GENERATED ALWAYS AS (...) STORED,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 4.2 데이터 흐름 관계

```
orders (원천)
  │
  ├── kpis_yesterday.sql ─── LEFT JOIN ──▶ daily_summary (visitors, conversion_rate)
  ├── kpis_last_week.sql ─── LEFT JOIN ──▶ daily_summary
  └── top_products.sql ───── (orders만 사용)
```

---

## 5. Error Handling

### 5.1 transform.js 에러 처리 전략

| 상황 | 처리 방법 | 메시지 |
|------|----------|--------|
| 어제 데이터 없음 | 조기 반환 | "데이터가 없습니다" |
| 지난주 데이터 없음 | WoW "N/A" 표시 | WoW 비교 불가 |
| Top Products 없음 | "데이터 없음" 텍스트 | Top 3 영역에 표시 |
| 0으로 나누기 | calculateWoW에서 0 반환 | 이미 처리됨 |

### 5.2 WoW 계산 방어 로직

```javascript
function calculateWoW(current, previous) {
  if (!previous || previous === 0) return null;  // 0 대신 null 반환
  return ((current - previous) / previous) * 100;
}

// 포맷팅 시 null 처리
function formatWoW(value) {
  if (value === null) return 'N/A';
  return (value > 0 ? '+' : '') + value.toFixed(1) + '%';
}
```

---

## 6. Test Plan

### 6.1 테스트 범위

| 유형 | 대상 | 방법 |
|------|------|------|
| SQL 검증 | 3개 쿼리 정확성 | psql 직접 실행 |
| 로직 검증 | WoW 계산, 이상 탐지 | 수동 계산 대조 |
| 통합 검증 | n8n 워크플로우 E2E | n8n UI 실행 |
| 에러 검증 | Null 입력, 데이터 없음 | 빈 테이블로 테스트 |

### 6.2 핵심 테스트 케이스

| TC | 시나리오 | 입력 | 기대 결과 |
|----|---------|------|----------|
| TC-1 | SQL 정상 실행 | 샘플 데이터 존재 | 5개 KPI 값 반환 |
| TC-2 | WoW 정확성 | 어제=18,750,000 / 지난주=15,000,000 | +25.0% |
| TC-3a | 이상 탐지 (매출) | WoW = -25% | 🚨 Critical 표시 |
| TC-3b | 이상 탐지 (정상) | WoW = +5% | 알림 없음 |
| TC-4 | 데이터 없음 | 빈 orders 테이블 | "데이터가 없습니다" 메시지 |
| TC-5 | 지난주 데이터 없음 | 어제만 존재 | WoW = "N/A" |
| TC-6 | E2E 워크플로우 | 전체 실행 | Slack 메시지 정상 도착 |
| TC-7 | Top Products 없음 | 어제 주문 없음 | "데이터 없음" 표시 |

---

## 7. Coding Conventions

### 7.1 SQL 컨벤션 (기존 유지)

| 항목 | 규칙 |
|------|------|
| CTE | 반드시 WITH절 사용 |
| NULL 방어 | NULLIF, COALESCE 사용 |
| 날짜 | CURRENT_DATE - INTERVAL 형식 |
| 별칭 | 의미 있는 이름 (yesterday_kpis, product_sales) |
| 주석 | 한글로 쿼리 목적 명시 |

### 7.2 JavaScript 컨벤션 (기존 유지)

| 항목 | 규칙 |
|------|------|
| 함수 | 선언식 사용 (function name()) |
| 숫자 포맷 | toLocaleString('ko-KR') |
| 섹션 구분 | `// ====` 블록 주석 |
| 반환 형식 | `{ json: { ... } }` |

### 7.3 환경변수 컨벤션

| 접두사 | 용도 |
|--------|------|
| POSTGRES_ | DB 연결 정보 |
| SLACK_ | Slack 설정 |
| N8N_ | n8n 설정 |
| TABLEAU_ | 대시보드 링크 |

---

## 8. Implementation Order

Gap 해결 순서를 의존성 기반으로 정의합니다.

```
Step 1: SQL 쿼리 수정 (G-2)
  ├── kpis_yesterday.sql: daily_summary LEFT JOIN 추가
  └── kpis_last_week.sql: daily_summary LEFT JOIN 추가
       │
Step 2: transform.js 수정 (G-4, G-5)
  ├── null/empty 방어 코드 추가
  ├── topProducts 입력 구조 수정
  └── WoW null 처리 (formatWoW 함수)
       │
Step 3: workflow.json 업데이트 (G-1)
  └── 3개 PostgreSQL 노드에 실제 SQL 반영
       │
Step 4: .env.example 생성 (G-6)
  └── 환경변수 템플릿 파일 생성
       │
Step 5: 테스트 실행 (G-3)
  └── TC-1 ~ TC-7 순서대로 검증
```

### 수정 대상 요약

| 순서 | 파일 | 변경 유형 | Gap |
|------|------|----------|-----|
| 1 | queries/kpis_yesterday.sql | 수정 (JOIN 추가) | G-2 |
| 2 | queries/kpis_last_week.sql | 수정 (JOIN 추가) | G-2 |
| 3 | n8n/transform.js | 수정 (방어 코드 + 구조) | G-4, G-5 |
| 4 | n8n/workflow.json | 수정 (쿼리 교체) | G-1 |
| 5 | .env.example | 신규 생성 | G-6 |
| 6 | tests/TEST_RESULTS.md | 수정 (결과 기록) | G-3 |

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-13 | Initial draft - 6 Gap 해결 설계 | 택 |
