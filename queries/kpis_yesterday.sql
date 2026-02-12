-- ============================================================================
-- Query: kpis_yesterday.sql
-- Purpose: 어제(yesterday) 날짜의 핵심 KPI 조회
-- Usage: n8n PostgreSQL Node에서 실행
-- ============================================================================

-- 변수 설정 (PostgreSQL에서는 주석으로 설명만)
-- @target_date = CURRENT_DATE - 1 (어제)

WITH yesterday_kpis AS (
    SELECT 
        -- 날짜
        order_date,
        
        -- 핵심 KPI 메트릭
        COUNT(DISTINCT order_id) AS total_orders,
        SUM(order_amount) AS total_revenue,
        COUNT(DISTINCT customer_id) AS unique_customers,
        
        -- 평균 주문 금액 (AOV - Average Order Value)
        ROUND(
            SUM(order_amount) / NULLIF(COUNT(DISTINCT order_id), 0), 
            2
        ) AS avg_order_value,
        
        -- 총 주문 수량
        SUM(quantity) AS total_units_sold
        
    FROM orders
    WHERE order_date = CURRENT_DATE - INTERVAL '1 day'
    GROUP BY order_date
)

SELECT
    yk.order_date,
    yk.total_orders,
    yk.total_revenue,
    yk.unique_customers,
    yk.avg_order_value,
    yk.total_units_sold,

    -- 방문자/전환율: daily_summary 테이블에서 JOIN
    COALESCE(ds.total_visitors, 0) AS total_visitors,
    COALESCE(ds.conversion_rate, 0.00) AS conversion_rate

FROM yesterday_kpis yk
LEFT JOIN daily_summary ds ON ds.summary_date = yk.order_date;

-- ============================================================================
-- 결과 예시:
-- ============================================================================
-- order_date   | total_orders | total_revenue | avg_order_value | ...
-- 2026-02-12   | 520          | 18750000      | 36057.69        | ...
-- ============================================================================

-- ============================================================================
-- 개선 옵션: daily_summary 테이블 활용 (더 빠른 조회)
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
WHERE summary_date = CURRENT_DATE - INTERVAL '1 day';
*/
