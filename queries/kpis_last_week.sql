-- ============================================================================
-- Query: kpis_last_week.sql
-- Purpose: 지난주 동일 요일의 핵심 KPI 조회 (WoW 비교용)
-- Source: daily_sales 테이블 (Supabase)
-- Usage: n8n PostgreSQL Node에서 실행
-- ============================================================================

-- @target_date = CURRENT_DATE - 8 (지난주 동일 요일)

SELECT
    sale_date AS order_date,

    -- 핵심 KPI 메트릭
    orders AS total_orders,
    revenue AS total_revenue,
    0 AS unique_customers,

    -- 평균 주문 금액 (AOV)
    CASE
        WHEN orders > 0 THEN ROUND(revenue::DECIMAL / orders, 2)
        ELSE 0
    END AS avg_order_value,

    -- 총 판매 수량
    quantity_sold AS total_units_sold,

    -- 방문자 / 전환율
    COALESCE(visitors, 0) AS total_visitors,
    COALESCE(conversion_rate, 0.00) AS conversion_rate

FROM daily_sales
WHERE sale_date = CURRENT_DATE - INTERVAL '8 days';
