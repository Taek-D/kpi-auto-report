# SQL 쿼리 상세 가이드

## 개요

이 문서는 앳홈 KPI Auto Report에서 사용되는 SQL 쿼리의 설계 원칙, 최적화 전략, 그리고 각 쿼리의 상세 분석을 제공합니다.

**도메인**: 앳홈 (미닉스/톰/프로티원) 3개 브랜드 x 5개 채널

---

## 쿼리 설계 원칙

### 1. 성능 우선
- **목표**: 각 쿼리 실행 시간 < 5초
- **전략**: 복합 인덱스 (sale_date, brand), CTE 사용, 불필요한 JOIN 제거

### 2. 브랜드별 분석
- 모든 쿼리는 brand 별 집계를 기본으로 함
- `PARTITION BY brand`를 활용한 브랜드 내 비중/순위 계산

### 3. 재사용성
- **파라미터화**: `CURRENT_DATE - 1` (하드코딩 방지)
- **모듈화**: 각 쿼리는 단일 책임

---

## Query 1: brand_kpis_yesterday.sql

### 목적
어제 날짜의 브랜드별 KPI(매출, 주문 수, ROAS 등)를 채널별 매출 비중과 함께 조회합니다.

### 핵심 기법

#### Window Function: SUM OVER PARTITION BY

```sql
-- 채널별 매출 비중 계산
ROUND(
    (revenue / NULLIF(SUM(revenue) OVER (PARTITION BY brand), 0)) * 100, 1
) AS channel_share_pct
```

**동작 방식:**
| brand | channel | revenue | share_pct |
|-------|---------|---------|-----------|
| minix | coupang | 4,120,000 | 33.2% |
| minix | gs_home | 3,500,000 | 28.2% |
| minix | own_mall | 2,850,000 | 23.0% |

#### JSONB 집계 (channel_breakdown)

```sql
jsonb_agg(
    jsonb_build_object(
        'channel', b.channel,
        'revenue', b.revenue,
        'share_pct', ...
    ) ORDER BY b.revenue DESC
) AS channel_breakdown
```

**결과**: 각 브랜드의 채널별 매출을 JSON 배열로 반환 (n8n에서 바로 사용 가능)

---

## Query 2: brand_kpis_last_week.sql

### 목적
지난주 동일 요일의 브랜드별 KPI를 조회하여 WoW 비교 기준 데이터를 제공합니다.

### 핵심 로직

```sql
WHERE sale_date = CURRENT_DATE - INTERVAL '8 days'
```

**왜 8일?**
- 오늘: 2026-02-13 (목요일)
- 어제: 2026-02-12 (수요일)
- 지난주 수요일: 2026-02-05 (8일 전)

### WoW 계산 (n8n transform.js에서 수행)

```javascript
const wowRevenue = ((yesterday.total_revenue - lastWeek.total_revenue)
                    / lastWeek.total_revenue) * 100;
// 미닉스: ((12,430,000 - 8,250,000) / 8,250,000) * 100 = 50.7% ↑
```

---

## Query 3: top_products_by_brand.sql

### 목적
브랜드별 매출 상위 제품 + 전체 Top 5를 순위와 함께 조회합니다.

### 핵심 기법

#### 이중 Window Function: 전체 순위 + 브랜드 내 순위

```sql
-- 전체 순위
RANK() OVER (ORDER BY pds.revenue DESC) AS overall_rank,

-- 브랜드 내 순위
RANK() OVER (
    PARTITION BY p.brand
    ORDER BY pds.revenue DESC
) AS brand_rank
```

**출력 예시:**
| overall_rank | brand | product_name | revenue | brand_rank |
|-------------|-------|-------------|---------|-----------|
| 1 | thome | 톰 더글로우 프로 | 5,960,000 | 1 |
| 2 | minix | 미닉스 식기세척기 | 4,590,000 | 1 |
| 3 | minix | 미닉스 미니건조기 | 3,490,000 | 2 |

#### 매출 비중 계산 (전체 + 브랜드 내)

```sql
-- 전체 매출 대비 비중
ROUND((pds.revenue / NULLIF(SUM(pds.revenue) OVER (), 0)) * 100, 1) AS revenue_share_pct,

-- 브랜드 내 매출 비중
ROUND((pds.revenue / NULLIF(SUM(pds.revenue) OVER (PARTITION BY p.brand), 0)) * 100, 1) AS brand_share_pct
```

---

## Query 4: channel_performance.sql

### 목적
채널별 매출, ROAS, 전환율을 비교하고 WoW 변동을 분석합니다.

### 핵심 기법

#### CTE 기반 WoW 비교

```sql
WITH yesterday_channels AS (...),
     last_week_channels AS (...)
SELECT
    y.channel,
    y.revenue AS current_revenue,
    lw.revenue AS prev_revenue,
    ROUND(((y.revenue - lw.revenue) / NULLIF(lw.revenue, 0)) * 100, 1) AS revenue_wow_pct,
    RANK() OVER (ORDER BY y.revenue DESC) AS current_rank
FROM yesterday_channels y
LEFT JOIN last_week_channels lw ON y.channel = lw.channel
```

**결과 예시:**
| channel | current_revenue | revenue_wow | rank | roas |
|---------|----------------|------------|------|------|
| coupang | 8,640,000 | +9.2% | 1 | 6.44 |
| gs_home | 8,700,000 | N/A | 2 | 0.00 |
| own_mall | 5,950,000 | +8.4% | 3 | 8.27 |

---

## Query 5: competitor_changes.sql

### 목적
경쟁사 순위/가격 변동을 감지합니다 (크롤링 데이터 기반).

### 핵심 기법

#### LAG 대체: Self-JOIN으로 전주 비교

```sql
FROM market_competitors curr
LEFT JOIN market_competitors prev
    ON curr.source = prev.source
    AND curr.product_name = prev.product_name
    AND prev.crawl_date = CURRENT_DATE - INTERVAL '8 days'
WHERE curr.crawl_date = CURRENT_DATE - INTERVAL '1 day'
```

#### 순위 변동 계산

```sql
-- 양수 = 순위 상승, 음수 = 순위 하락
(COALESCE(prev.ranking, curr.ranking) - curr.ranking) AS ranking_change
```

**결과 예시:**
| product | brand | prev_rank | curr_rank | change |
|---------|-------|-----------|-----------|--------|
| 미닉스 음식물처리기 | 앳홈(미닉스) | 4 | 3 | +1 (상승) |
| 톰 더글로우 프로 | 앳홈(톰) | 4 | 3 | +1 (상승) |

---

## 고급 SQL 패턴

### 1. LAG/LEAD (시계열 분석)

```sql
-- 일별 매출 추이 (브랜드별)
SELECT
    sale_date,
    brand,
    SUM(revenue) AS daily_revenue,
    LAG(SUM(revenue)) OVER (PARTITION BY brand ORDER BY sale_date) AS prev_day_revenue,
    SUM(revenue) - LAG(SUM(revenue)) OVER (PARTITION BY brand ORDER BY sale_date) AS daily_change
FROM brand_daily_sales
GROUP BY sale_date, brand
ORDER BY brand, sale_date DESC;
```

### 2. Moving Average (7일 이동 평균, 브랜드별)

```sql
SELECT
    sale_date,
    brand,
    SUM(revenue) AS daily_revenue,
    AVG(SUM(revenue)) OVER (
        PARTITION BY brand
        ORDER BY sale_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS revenue_7d_avg
FROM brand_daily_sales
GROUP BY sale_date, brand;
```

### 3. 채널 비중 추이 (PIVOT 스타일)

```sql
SELECT
    sale_date,
    brand,
    SUM(CASE WHEN channel = 'coupang' THEN revenue ELSE 0 END) AS coupang,
    SUM(CASE WHEN channel = 'own_mall' THEN revenue ELSE 0 END) AS own_mall,
    SUM(CASE WHEN channel = 'naver' THEN revenue ELSE 0 END) AS naver,
    SUM(CASE WHEN channel = 'gs_home' THEN revenue ELSE 0 END) AS gs_home,
    SUM(CASE WHEN channel = 'oliveyoung' THEN revenue ELSE 0 END) AS oliveyoung
FROM brand_daily_sales
WHERE sale_date >= CURRENT_DATE - INTERVAL '14 days'
GROUP BY sale_date, brand
ORDER BY brand, sale_date;
```

---

## 성능 최적화 체크리스트

### 인덱스 전략

```sql
-- 이미 스키마에 포함된 인덱스
CREATE INDEX idx_brand_daily_sales_date_brand ON brand_daily_sales(sale_date, brand);
CREATE INDEX idx_brand_daily_sales_date_channel ON brand_daily_sales(sale_date, channel);
CREATE INDEX idx_product_daily_sales_date ON product_daily_sales(sale_date DESC);
CREATE INDEX idx_market_competitors_date ON market_competitors(crawl_date DESC);
```

### EXPLAIN ANALYZE 활용

```sql
EXPLAIN ANALYZE
SELECT * FROM brand_daily_sales
WHERE sale_date = '2026-02-12' AND brand = 'minix';
```

**읽는 법:**
- `Seq Scan`: 전체 스캔 (느림) > 인덱스 추가 필요
- `Index Scan`: 인덱스 사용 (빠름)
- `Cost`: 낮을수록 좋음

---

## 인터뷰 대비 Q&A

### Q1: Window Function과 GROUP BY의 차이는?

**A:**
- `GROUP BY`: 행을 집계하여 결과 행 수 감소
- `Window Function`: 집계하되 원본 행 수 유지

### Q2: RANK vs DENSE_RANK vs ROW_NUMBER?

**A:**
```
점수: [100, 90, 90, 80]
RANK():       [1, 2, 2, 4]  -- 건너뜀
DENSE_RANK(): [1, 2, 2, 3]  -- 연속
ROW_NUMBER(): [1, 2, 3, 4]  -- 고유
```

### Q3: 왜 JSONB를 사용했나요?

**A:** `channel_breakdown`은 브랜드별 채널 매출 비중을 JSON 배열로 반환합니다. n8n Code Node에서 JavaScript 객체로 바로 파싱할 수 있어, 중간 변환 없이 Slack 메시지에 채널 정보를 포함할 수 있습니다.

### Q4: 크롤링 데이터의 정합성은 어떻게 보장하나요?

**A:** `market_competitors` 테이블에 `UNIQUE(crawl_date, source, product_name)` 제약조건이 있어 동일 날짜/소스/제품의 중복 데이터를 방지합니다. 또한 Self-JOIN으로 전주 대비 변동을 계산할 때 `COALESCE`로 NULL 처리하여 신규 진입 제품도 올바르게 표시합니다.

---

## 참고 자료

- [PostgreSQL Window Functions](https://www.postgresql.org/docs/current/tutorial-window.html)
- [PostgreSQL JSONB Functions](https://www.postgresql.org/docs/current/functions-json.html)
- [SQL Performance Explained](https://use-the-index-luke.com/)

---

**다음**: [Slack 연동 가이드](SLACK_INTEGRATION.md)
