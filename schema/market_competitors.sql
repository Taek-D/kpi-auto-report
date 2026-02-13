-- ============================================================================
-- Table: market_competitors
-- Purpose: 경쟁사 크롤링 데이터 저장 (쿠팡/네이버 순위/가격/리뷰)
-- 경쟁사: 스마트카라, 린클(음식물처리기), LG 프라엘, 페이스팩토리(뷰티디바이스)
-- Created: 2026-02-13
-- ============================================================================

-- 기존 테이블 삭제 (재생성 시)
DROP TABLE IF EXISTS market_competitors CASCADE;

-- 경쟁사 모니터링 테이블
CREATE TABLE market_competitors (
    id SERIAL PRIMARY KEY,
    crawl_date DATE NOT NULL,
    source VARCHAR(20) NOT NULL CHECK (source IN ('coupang', 'naver', 'oliveyoung')),
    category VARCHAR(50) NOT NULL,
    product_name VARCHAR(200) NOT NULL,
    brand VARCHAR(100) NOT NULL,
    price DECIMAL(12, 2) NOT NULL DEFAULT 0,
    ranking INTEGER DEFAULT NULL,
    review_count INTEGER NOT NULL DEFAULT 0,
    avg_rating DECIMAL(3, 2) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(crawl_date, source, product_name)
);

-- 인덱스
CREATE INDEX idx_market_competitors_date ON market_competitors(crawl_date DESC);
CREATE INDEX idx_market_competitors_category ON market_competitors(category);
CREATE INDEX idx_market_competitors_brand ON market_competitors(brand);

-- ============================================================================
-- 샘플 데이터: 어제 (2026-02-12) 크롤링 결과
-- ============================================================================

-- 소형가전 카테고리 (쿠팡)
INSERT INTO market_competitors (crawl_date, source, category, product_name, brand, price, ranking, review_count, avg_rating) VALUES
('2026-02-12', 'coupang', '음식물처리기', '스마트카라 PCS-400',      '스마트카라',  599000, 1, 15420, 4.6),
('2026-02-12', 'coupang', '음식물처리기', '린클 루펜 SLW-03',        '린클',       498000, 2, 8930,  4.5),
('2026-02-12', 'coupang', '음식물처리기', '미닉스 음식물처리기',      '앳홈(미닉스)', 690000, 3, 2150,  4.9),
('2026-02-12', 'coupang', '식기세척기',   '미닉스 식기세척기',        '앳홈(미닉스)', 459000, 5, 1820,  4.6),
('2026-02-12', 'coupang', '소형건조기',   '미닉스 미니건조기',        '앳홈(미닉스)', 349000, 3, 3450,  4.8);

-- 뷰티디바이스 카테고리 (쿠팡)
INSERT INTO market_competitors (crawl_date, source, category, product_name, brand, price, ranking, review_count, avg_rating) VALUES
('2026-02-12', 'coupang', '뷰티디바이스', 'LG 프라엘 더마 LED 마스크',  'LG',           398000, 1, 12300, 4.7),
('2026-02-12', 'coupang', '뷰티디바이스', '페이스팩토리 LED 마스크',     '페이스팩토리', 189000, 2, 6780,  4.4),
('2026-02-12', 'coupang', '뷰티디바이스', '톰 더글로우 프로',           '앳홈(톰)',     298000, 3, 4520,  4.8),
('2026-02-12', 'coupang', '뷰티디바이스', '톰 더글로우',               '앳홈(톰)',     198000, 6, 2890,  4.6);

-- 네이버 쇼핑 순위
INSERT INTO market_competitors (crawl_date, source, category, product_name, brand, price, ranking, review_count, avg_rating) VALUES
('2026-02-12', 'naver', '음식물처리기', '스마트카라 PCS-400',      '스마트카라',  589000, 1, 8920,  4.5),
('2026-02-12', 'naver', '음식물처리기', '미닉스 음식물처리기',      '앳홈(미닉스)', 690000, 2, 1280,  4.9),
('2026-02-12', 'naver', '뷰티디바이스', 'LG 프라엘 더마 LED 마스크',  'LG',         389000, 1, 7650,  4.7),
('2026-02-12', 'naver', '뷰티디바이스', '톰 더글로우 프로',           '앳홈(톰)',   298000, 2, 2340,  4.8);

-- ============================================================================
-- 샘플 데이터: 지난주 (2026-02-05) 크롤링 결과
-- ============================================================================

-- 소형가전 카테고리 (쿠팡)
INSERT INTO market_competitors (crawl_date, source, category, product_name, brand, price, ranking, review_count, avg_rating) VALUES
('2026-02-05', 'coupang', '음식물처리기', '스마트카라 PCS-400',      '스마트카라',  599000, 1, 15100, 4.6),
('2026-02-05', 'coupang', '음식물처리기', '린클 루펜 SLW-03',        '린클',       508000, 2, 8720,  4.5),
('2026-02-05', 'coupang', '음식물처리기', '미닉스 음식물처리기',      '앳홈(미닉스)', 690000, 4, 2050,  4.8),
('2026-02-05', 'coupang', '식기세척기',   '미닉스 식기세척기',        '앳홈(미닉스)', 459000, 6, 1720,  4.6),
('2026-02-05', 'coupang', '소형건조기',   '미닉스 미니건조기',        '앳홈(미닉스)', 349000, 4, 3280,  4.7);

-- 뷰티디바이스 카테고리 (쿠팡)
INSERT INTO market_competitors (crawl_date, source, category, product_name, brand, price, ranking, review_count, avg_rating) VALUES
('2026-02-05', 'coupang', '뷰티디바이스', 'LG 프라엘 더마 LED 마스크',  'LG',           398000, 1, 12050, 4.7),
('2026-02-05', 'coupang', '뷰티디바이스', '페이스팩토리 LED 마스크',     '페이스팩토리', 189000, 2, 6580,  4.4),
('2026-02-05', 'coupang', '뷰티디바이스', '톰 더글로우 프로',           '앳홈(톰)',     298000, 4, 4280,  4.7),
('2026-02-05', 'coupang', '뷰티디바이스', '톰 더글로우',               '앳홈(톰)',     198000, 7, 2750,  4.6);

-- 네이버 쇼핑 순위
INSERT INTO market_competitors (crawl_date, source, category, product_name, brand, price, ranking, review_count, avg_rating) VALUES
('2026-02-05', 'naver', '음식물처리기', '스마트카라 PCS-400',      '스마트카라',  589000, 1, 8650,  4.5),
('2026-02-05', 'naver', '음식물처리기', '미닉스 음식물처리기',      '앳홈(미닉스)', 690000, 3, 1180,  4.8),
('2026-02-05', 'naver', '뷰티디바이스', 'LG 프라엘 더마 LED 마스크',  'LG',         389000, 1, 7420,  4.7),
('2026-02-05', 'naver', '뷰티디바이스', '톰 더글로우 프로',           '앳홈(톰)',   298000, 3, 2180,  4.7);

-- ============================================================================
-- RPC 함수: get_competitor_changes()
-- 경쟁사 순위/가격 변동 감지 (어제 vs 지난주)
-- ============================================================================

CREATE OR REPLACE FUNCTION get_competitor_changes()
RETURNS TABLE(
    source TEXT,
    category TEXT,
    product_name TEXT,
    brand TEXT,
    current_price DECIMAL,
    prev_price DECIMAL,
    price_change DECIMAL,
    current_ranking INTEGER,
    prev_ranking INTEGER,
    ranking_change INTEGER,
    current_reviews INTEGER,
    review_growth INTEGER,
    current_rating DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        curr.source::TEXT,
        curr.category::TEXT,
        curr.product_name::TEXT,
        curr.brand::TEXT,
        curr.price AS current_price,
        prev.price AS prev_price,
        (curr.price - COALESCE(prev.price, curr.price)) AS price_change,
        curr.ranking AS current_ranking,
        prev.ranking AS prev_ranking,
        (COALESCE(prev.ranking, curr.ranking) - curr.ranking) AS ranking_change,
        curr.review_count AS current_reviews,
        (curr.review_count - COALESCE(prev.review_count, curr.review_count)) AS review_growth,
        curr.avg_rating AS current_rating
    FROM market_competitors curr
    LEFT JOIN market_competitors prev
        ON curr.source = prev.source
        AND curr.product_name = prev.product_name
        AND prev.crawl_date = CURRENT_DATE - INTERVAL '8 days'
    WHERE curr.crawl_date = CURRENT_DATE - INTERVAL '1 day'
    ORDER BY curr.source, curr.category, curr.ranking;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 데이터 검증 쿼리
-- ============================================================================

-- 순위 변동 확인
SELECT
    curr.source,
    curr.category,
    curr.product_name,
    curr.brand,
    curr.ranking AS current_rank,
    prev.ranking AS prev_rank,
    COALESCE(prev.ranking, 0) - curr.ranking AS rank_change,
    curr.price,
    prev.price AS prev_price,
    curr.price - COALESCE(prev.price, curr.price) AS price_change
FROM market_competitors curr
LEFT JOIN market_competitors prev
    ON curr.source = prev.source
    AND curr.product_name = prev.product_name
    AND prev.crawl_date = '2026-02-05'
WHERE curr.crawl_date = '2026-02-12'
ORDER BY curr.source, curr.category, curr.ranking;
