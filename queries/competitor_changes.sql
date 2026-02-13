-- ============================================================================
-- Query: competitor_changes.sql
-- Purpose: 경쟁사 순위/가격 변동 감지 (어제 vs 지난주)
-- Source: market_competitors 테이블 (Supabase)
-- Usage: Supabase RPC get_competitor_changes() 함수 원본
-- ============================================================================

-- LAG() OVER로 전일 대비 변동 감지
WITH ranked_changes AS (
    SELECT
        curr.source,
        curr.category,
        curr.product_name,
        curr.brand,

        -- 가격 변동
        curr.price AS current_price,
        prev.price AS prev_price,
        (curr.price - COALESCE(prev.price, curr.price)) AS price_change,
        CASE
            WHEN prev.price IS NOT NULL AND prev.price > 0
            THEN ROUND(((curr.price - prev.price) / prev.price) * 100, 1)
            ELSE 0
        END AS price_change_pct,

        -- 순위 변동 (양수 = 상승, 음수 = 하락)
        curr.ranking AS current_ranking,
        prev.ranking AS prev_ranking,
        (COALESCE(prev.ranking, curr.ranking) - curr.ranking) AS ranking_change,

        -- 리뷰 성장
        curr.review_count AS current_reviews,
        (curr.review_count - COALESCE(prev.review_count, curr.review_count)) AS review_growth,

        -- 평점
        curr.avg_rating AS current_rating,
        prev.avg_rating AS prev_rating,

        -- 앳홈 자사 제품 여부
        CASE
            WHEN curr.brand LIKE '%앳홈%' THEN true
            ELSE false
        END AS is_athome

    FROM market_competitors curr
    LEFT JOIN market_competitors prev
        ON curr.source = prev.source
        AND curr.product_name = prev.product_name
        AND prev.crawl_date = CURRENT_DATE - INTERVAL '8 days'
    WHERE curr.crawl_date = CURRENT_DATE - INTERVAL '1 day'
)

SELECT *
FROM ranked_changes
ORDER BY
    source,
    category,
    current_ranking;
