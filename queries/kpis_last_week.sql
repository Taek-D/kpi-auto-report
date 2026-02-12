-- ============================================================================
-- Query: kpis_last_week.sql
-- Purpose: 지난주 동일 요일의 핵심 KPI 조회 (WoW 비교용)
-- Usage: n8n PostgreSQL Node에서 실행
-- ============================================================================

-- 변수 설정
-- @target_date = CURRENT_DATE - 8 (지난주 동일 요일)
-- 예: 오늘이 수요일(2026-02-12)이면 지난주 수요일(2026-02-05) 데이터 조회

WITH last_week_kpis AS (
    SELECT 
        -- 날짜
        order_date,
        
        -- 핵심 KPI 메트릭
        COUNT(DISTINCT order_id) AS total_orders,
        SUM(order_amount) AS total_revenue,
        COUNT(DISTINCT customer_id) AS unique_customers,
        
        -- 평균 주문 금액 (AOV)
        ROUND(
            SUM(order_amount) / NULLIF(COUNT(DISTINCT order_id), 0), 
            2
        ) AS avg_order_value,
        
        -- 총 주문 수량
        SUM(quantity) AS total_units_sold
        
    FROM orders
    WHERE order_date = CURRENT_DATE - INTERVAL '8 days'
    GROUP BY order_date
)

SELECT
    lk.order_date,
    lk.total_orders,
    lk.total_revenue,
    lk.unique_customers,
    lk.avg_order_value,
    lk.total_units_sold,

    -- 방문자/전환율: daily_summary 테이블에서 JOIN
    COALESCE(ds.total_visitors, 0) AS total_visitors,
    COALESCE(ds.conversion_rate, 0.00) AS conversion_rate

FROM last_week_kpis lk
LEFT JOIN daily_summary ds ON ds.summary_date = lk.order_date;

-- ============================================================================
-- 결과 예시:
-- ============================================================================
-- order_date   | total_orders | total_revenue | avg_order_value | ...
-- 2026-02-05   | 450          | 15000000      | 33333.33        | ...
-- ============================================================================

-- ============================================================================
-- WoW 변화율 계산 방법 (n8n Transform Node에서 수행)
-- ============================================================================
-- wow_revenue_pct = ((yesterday.revenue - lastweek.revenue) / lastweek.revenue) * 100
-- 예: ((18750000 - 15000000) / 15000000) * 100 = 25% ↑
-- ============================================================================

-- ============================================================================
-- 개선 옵션: daily_summary 테이블 활용
-- ============================================================================
/*
SELECT 
    summary_date AS order_date,
    total_orders,
    total_revenue,
    avg_order_value,
    total_visitors,
    conversion_rate
FROM daily_summary
WHERE summary_date = CURRENT_DATE - INTERVAL '8 days';
*/
