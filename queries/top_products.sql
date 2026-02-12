-- ============================================================================
-- Query: top_products.sql
-- Purpose: 어제 날짜 기준 매출 상위 3개 제품 조회
-- Usage: n8n PostgreSQL Node에서 실행
-- ============================================================================

WITH product_sales AS (
    SELECT 
        product_id,
        product_name,
        
        -- 매출 합계
        SUM(order_amount) AS total_revenue,
        
        -- 판매 수량
        SUM(quantity) AS units_sold,
        
        -- 주문 건수
        COUNT(DISTINCT order_id) AS order_count,
        
        -- 평균 단가
        ROUND(AVG(unit_price), 2) AS avg_unit_price
        
    FROM orders
    WHERE order_date = CURRENT_DATE - INTERVAL '1 day'
    GROUP BY product_id, product_name
),

ranked_products AS (
    SELECT 
        product_id,
        product_name,
        total_revenue,
        units_sold,
        order_count,
        avg_unit_price,
        
        -- Window Function: 매출 기준 순위
        RANK() OVER (ORDER BY total_revenue DESC) AS revenue_rank,
        
        -- 매출 비중 계산
        ROUND(
            (total_revenue / SUM(total_revenue) OVER ()) * 100, 
            2
        ) AS revenue_share_pct
        
    FROM product_sales
)

SELECT 
    revenue_rank AS rank,
    product_name,
    total_revenue,
    units_sold,
    order_count,
    avg_unit_price,
    revenue_share_pct
    
FROM ranked_products
WHERE revenue_rank <= 3
ORDER BY revenue_rank;

-- ============================================================================
-- 결과 예시:
-- ============================================================================
-- rank | product_name        | total_revenue | units_sold | revenue_share_pct
-- 1    | 무선 이어폰 Pro     | 4500000      | 150        | 24.00
-- 2    | 스마트워치 Ultra    | 3200000      | 80         | 17.07
-- 3    | 블루투스 스피커     | 2100000      | 210        | 11.20
-- ============================================================================

-- ============================================================================
-- 추가 분석: 지난주 순위와 비교 (고급 버전)
-- ============================================================================
/*
WITH yesterday_products AS (
    SELECT 
        product_name,
        SUM(order_amount) AS total_revenue,
        RANK() OVER (ORDER BY SUM(order_amount) DESC) AS rank
    FROM orders
    WHERE order_date = CURRENT_DATE - INTERVAL '1 day'
    GROUP BY product_name
),

last_week_products AS (
    SELECT 
        product_name,
        RANK() OVER (ORDER BY SUM(order_amount) DESC) AS last_week_rank
    FROM orders
    WHERE order_date = CURRENT_DATE - INTERVAL '8 days'
    GROUP BY product_name
)

SELECT 
    y.rank,
    y.product_name,
    y.total_revenue,
    l.last_week_rank,
    (l.last_week_rank - y.rank) AS rank_change  -- 양수면 순위 상승
FROM yesterday_products y
LEFT JOIN last_week_products l ON y.product_name = l.product_name
WHERE y.rank <= 3
ORDER BY y.rank;
*/
