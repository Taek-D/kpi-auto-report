-- ============================================================================
-- Query: top_products_by_brand.sql
-- Purpose: 브랜드별 매출 상위 제품 + 전체 상위 5개
-- Source: product_daily_sales + products 테이블 (Supabase)
-- Usage: Supabase RPC get_top_products() 함수 원본
-- ============================================================================

-- 전체 상위 5개 제품 (매출 기준)
WITH ranked_products AS (
    SELECT
        p.brand,
        p.product_name,
        pds.revenue AS total_revenue,
        pds.quantity_sold AS units_sold,
        pds.orders AS order_count,
        pds.avg_rating,
        pds.review_count,

        -- Window Function: 매출 기준 전체 순위
        RANK() OVER (ORDER BY pds.revenue DESC) AS overall_rank,

        -- Window Function: 브랜드 내 순위
        RANK() OVER (
            PARTITION BY p.brand
            ORDER BY pds.revenue DESC
        ) AS brand_rank,

        -- 매출 비중 (전체 대비)
        ROUND(
            (pds.revenue::DECIMAL / NULLIF(SUM(pds.revenue) OVER (), 0)) * 100, 1
        ) AS revenue_share_pct,

        -- 브랜드 내 매출 비중
        ROUND(
            (pds.revenue::DECIMAL / NULLIF(SUM(pds.revenue) OVER (PARTITION BY p.brand), 0)) * 100, 1
        ) AS brand_share_pct

    FROM product_daily_sales pds
    JOIN products p ON p.product_id = pds.product_id
    WHERE pds.sale_date = CURRENT_DATE - INTERVAL '1 day'
      AND pds.revenue > 0
)

SELECT
    overall_rank,
    brand,
    product_name,
    total_revenue,
    units_sold,
    order_count,
    avg_rating,
    review_count,
    revenue_share_pct,
    brand_rank,
    brand_share_pct
FROM ranked_products
WHERE overall_rank <= 5
ORDER BY overall_rank;
