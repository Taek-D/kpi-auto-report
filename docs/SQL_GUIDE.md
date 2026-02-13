# SQL 쿼리 상세 가이드

## 📋 개요

이 문서는 프로젝트에서 사용되는 SQL 쿼리의 설계 원칙, 최적화 전략, 그리고 각 쿼리의 상세 분석을 제공합니다.

---

## 🎯 쿼리 설계 원칙

### 1. 성능 우선
- **목표**: 각 쿼리 실행 시간 \< 5초
- **전략**: 인덱스 활용, CTE 사용, 불필요한 JOIN 제거

### 2. 가독성
- **명확한 별칭**: 단순 `o`, `p` 대신 `yesterday_kpis`, `product_sales`
- **주석 포함**: 각 계산 로직 설명

### 3. 재사용성
- **파라미터화**: `CURRENT_DATE - 1` (하드코딩 방지)
- **모듈화**: 각 쿼리는 단일 책임

---

## 📊 Query 1: kpis_yesterday.sql

### 목적
어제 날짜의 핵심 KPI(매출, 주문 수, AOV, 전환율 등)를 조회합니다.

### 쿼리 구조

```sql
SELECT
    sale_date AS order_date,
    orders AS total_orders,
    revenue AS total_revenue,
    CASE
        WHEN orders > 0 THEN ROUND(revenue::DECIMAL / orders, 2)
        ELSE 0
    END AS avg_order_value,
    quantity_sold AS total_units_sold,
    COALESCE(visitors, 0) AS total_visitors,
    COALESCE(conversion_rate, 0.00) AS conversion_rate
FROM daily_sales
WHERE sale_date = CURRENT_DATE - INTERVAL '1 day';
```

**데이터 소스**: `daily_sales` 테이블 (Supabase)

### 핵심 포인트

#### 1. `CASE WHEN` AOV 계산
```sql
CASE WHEN orders > 0 THEN ROUND(revenue::DECIMAL / orders, 2) ELSE 0 END
```
- **문제**: 주문이 0건이면 `0으로 나누기` 에러 발생
- **해결**: `CASE WHEN`으로 0 방지, `::DECIMAL` 캐스팅으로 정밀도 확보

#### 2. `COALESCE` NULL 처리
```sql
COALESCE(visitors, 0) AS total_visitors
```
- **이유**: 방문자/전환율이 NULL일 수 있음 (데이터 미수집 날짜)
- **효과**: NULL → 0으로 기본값 제공

#### 3. `CURRENT_DATE - INTERVAL '1 day'`
- **장점**: 하드코딩 방지, 자동으로 어제 날짜 계산
- **대안**: `CURRENT_DATE - 1` (PostgreSQL 특정 문법)

### 성능 최적화

```sql
-- 인덱스 추가 (한 번만 실행)
CREATE INDEX idx_daily_sales_date ON daily_sales(sale_date);
```

**Before**: 전체 테이블 스캔 (느림)
**After**: 인덱스 스캔 (빠름)

---

## 📉 Query 2: kpis_last_week.sql

### 목적
지난주 동일 요일의 KPI를 조회하여 WoW 비교 기준 데이터를 제공합니다.

**데이터 소스**: `daily_sales` 테이블 (Supabase) — Query 1과 동일 구조

### 핵심 로직

```sql
WHERE sale_date = CURRENT_DATE - INTERVAL '8 days'
```

**왜 8일?**
- 오늘: 2026-02-13 (목요일)
- 어제: 2026-02-12 (수요일)
- 지난주 수요일: 2026-02-05 (8일 전)

### WoW 계산 방법 (n8n에서 수행)

```javascript
const wowRevenue = ((yesterday.revenue - lastweek.revenue) / lastweek.revenue) * 100;
// 예: ((18,750,000 - 15,000,000) / 15,000,000) * 100 = 25% ↑
```

---

## 🏆 Query 3: top_products.sql

### 목적
어제 날짜 기준 매출 상위 3개 제품을 순위와 함께 조회합니다.

### 쿼리 구조 (CTE + Window Functions)

**데이터 소스**: `product_sales` + `products` 테이블 (Supabase)

```sql
WITH ranked_products AS (
    SELECT
        p.product_name,
        ps.revenue AS total_revenue,
        ps.quantity_sold AS units_sold,
        ps.orders AS order_count,

        -- 평균 단가
        CASE
            WHEN ps.quantity_sold > 0 THEN ROUND(ps.revenue::DECIMAL / ps.quantity_sold, 2)
            ELSE 0
        END AS avg_unit_price,

        -- Window Function: 매출 기준 순위
        RANK() OVER (ORDER BY ps.revenue DESC) AS revenue_rank,

        -- 매출 비중 계산
        ROUND(
            (ps.revenue::DECIMAL / NULLIF(SUM(ps.revenue) OVER (), 0)) * 100, 2
        ) AS revenue_share_pct

    FROM product_sales ps
    JOIN products p ON p.product_id = ps.product_id
    WHERE ps.revenue > 0
)

SELECT * FROM ranked_products
WHERE revenue_rank <= 3
ORDER BY revenue_rank;
```

### Window Functions 심층 분석

#### 1. `RANK() OVER (ORDER BY ...)`

```sql
RANK() OVER (ORDER BY total_revenue DESC) AS revenue_rank
```

**동작 방식:**
| product_name | total_revenue | revenue_rank |
|--------------|---------------|--------------|
| 무선 이어폰 | 4,500,000 | 1 |
| 스마트워치 | 3,200,000 | 2 |
| 블루투스 스피커 | 2,100,000 | 3 |

**RANK vs ROW_NUMBER:**
- `RANK()`: 동점이면 같은 순위 (1, 2, 2, 4)
- `ROW_NUMBER()`: 항상 고유 (1, 2, 3, 4)

#### 2. Window Aggregation

```sql
SUM(total_revenue) OVER () AS total_sum
```

- **OVER ()**: 전체 행 대상 집계 (GROUP BY 없이)
- **용도**: 각 행에서 전체 합계 참조 (비중 계산)

**예시:**
```sql
SELECT 
    product_name,
    total_revenue,
    SUM(total_revenue) OVER () AS total_sum,
    ROUND((total_revenue / SUM(total_revenue) OVER ()) * 100, 2) AS share_pct
FROM product_sales;
```

| product_name | total_revenue | total_sum | share_pct |
|--------------|---------------|-----------|-----------|
| 무선 이어폰 | 4,500,000 | 18,750,000 | 24.00 |
| 스마트워치 | 3,200,000 | 18,750,000 | 17.07 |

---

## 🔍 고급 SQL 패턴

### 1. LAG/LEAD (시계열 분석)

```sql
-- 전날 대비 변화 분석
SELECT 
    order_date,
    total_revenue,
    LAG(total_revenue) OVER (ORDER BY order_date) AS prev_day_revenue,
    total_revenue - LAG(total_revenue) OVER (ORDER BY order_date) AS daily_change
FROM daily_summary
ORDER BY order_date DESC
LIMIT 7;
```

**출력:**
| order_date | total_revenue | prev_day_revenue | daily_change |
|------------|---------------|------------------|--------------|
| 2026-02-12 | 18,750,000 | 17,500,000 | +1,250,000 |

### 2. Moving Average (7일 이동 평균)

```sql
SELECT 
    order_date,
    total_revenue,
    AVG(total_revenue) OVER (
        ORDER BY order_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS revenue_7d_avg
FROM daily_summary;
```

### 3. Cumulative Sum (누적 합계)

```sql
SELECT 
    order_date,
    total_revenue,
    SUM(total_revenue) OVER (
        ORDER BY order_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS revenue_cumulative
FROM daily_summary
WHERE order_date >= '2026-02-01';
```

---

## ⚡ 성능 최적화 체크리스트

### 1. 인덱스 전략

```sql
-- 필수 인덱스
CREATE INDEX idx_daily_sales_date ON daily_sales(sale_date);
CREATE INDEX idx_product_sales_revenue ON product_sales(revenue DESC);
```

### 2. EXPLAIN ANALYZE 활용

```sql
EXPLAIN ANALYZE
SELECT * FROM daily_sales WHERE sale_date = '2026-02-12';
```

**읽는 법:**
- `Seq Scan`: 전체 스캔 (느림) → 인덱스 추가 필요
- `Index Scan`: 인덱스 사용 (빠름) ✅
- `Cost`: 낮을수록 좋음

### 3. Materialized View (옵션)

```sql
-- 일일 집계 결과 저장
CREATE MATERIALIZED VIEW mv_daily_kpis AS
SELECT 
    order_date,
    COUNT(DISTINCT order_id) AS total_orders,
    SUM(order_amount) AS total_revenue
FROM orders
GROUP BY order_date;

-- 리프레시 (매일 08:10 실행)
REFRESH MATERIALIZED VIEW mv_daily_kpis;
```

---

## 🎓 인터뷰 대비 Q&A

### Q1: Window Function과 GROUP BY의 차이는?

**A:** 
- `GROUP BY`: 행을 집계하여 결과 행 수 감소
- `Window Function`: 집계하되 원본 행 수 유지

```sql
-- GROUP BY: 1개 행만 반환
SELECT product_name, SUM(revenue) FROM sales GROUP BY product_name;

-- Window: 모든 행 유지 + 합계 추가
SELECT product_name, revenue, SUM(revenue) OVER (PARTITION BY product_name) FROM sales;
```

### Q2: RANK vs DENSE_RANK vs ROW_NUMBER?

**A:**
```
점수: [100, 90, 90, 80]

RANK():       [1, 2, 2, 4]  -- 건너뜀
DENSE_RANK(): [1, 2, 2, 3]  -- 연속
ROW_NUMBER(): [1, 2, 3, 4]  -- 고유
```

### Q3: CTE vs Subquery 언제 사용?

**A:**
- **CTE**: 가독성, 재사용, 디버깅 쉬움 (권장)
- **Subquery**: 일회성, 짧은 쿼리

---

## 📚 추가 학습 자료

- [PostgreSQL Window Functions 공식 문서](https://www.postgresql.org/docs/current/tutorial-window.html)
- [SQL Performance Explained](https://use-the-index-luke.com/)
- [Mode Analytics SQL Tutorial](https://mode.com/sql-tutorial/)

---

**다음**: [Slack 연동 가이드](SLACK_INTEGRATION.md)
