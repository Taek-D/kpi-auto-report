-- ============================================================================
-- Query: top_products.sql
-- Purpose: 매출 상위 3개 제품 조회
-- Source: product_sales + products 테이블 (Supabase)
-- Usage: n8n PostgreSQL Node에서 실행
-- ============================================================================

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
            (ps.revenue::DECIMAL / NULLIF(SUM(ps.revenue) OVER (), 0)) * 100,
            2
        ) AS revenue_share_pct

    FROM product_sales ps
    JOIN products p ON p.product_id = ps.product_id
    WHERE ps.revenue > 0
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
