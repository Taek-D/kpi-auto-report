-- ============================================================================
-- Table: ab_test_results
-- Purpose: 미닉스 자사몰 결제 페이지 A/B 테스트 결과
-- Scenario: 기존(A) vs 개선(B) 결제 페이지 (원클릭 결제 + 리뷰 위젯)
-- Period: 2026-01-27 ~ 2026-02-09 (14일)
-- Background: 미닉스 자사몰 전환율(0.87%)이 업계 평균(1.2%) 대비 낮음
-- Created: 2026-02-13
-- ============================================================================

DROP TABLE IF EXISTS ab_test_results CASCADE;

CREATE TABLE ab_test_results (
    id SERIAL PRIMARY KEY,
    test_date DATE NOT NULL,
    variant VARCHAR(10) NOT NULL CHECK (variant IN ('control', 'treatment')),
    visitors INTEGER NOT NULL DEFAULT 0,
    conversions INTEGER NOT NULL DEFAULT 0,
    revenue DECIMAL(12, 2) NOT NULL DEFAULT 0,
    avg_order_value DECIMAL(10, 2) NOT NULL DEFAULT 0,
    bounce_rate DECIMAL(5, 2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(test_date, variant)
);

CREATE INDEX idx_ab_test_date ON ab_test_results(test_date);
CREATE INDEX idx_ab_test_variant ON ab_test_results(variant);

-- ============================================================================
-- Sample Data: 14 days x 2 variants = 28 rows
-- Control (A): 기존 결제 페이지 - 전환율 ~0.87%
-- Treatment (B): 개선 결제 페이지 - 전환율 ~1.05% (+20% 개선)
-- Pattern: 주말 트래픽 +15%, Treatment 점진적 학습 효과
-- ============================================================================

INSERT INTO ab_test_results (test_date, variant, visitors, conversions, revenue, avg_order_value, bounce_rate) VALUES
-- Day 1: 2026-01-27 (월)
('2026-01-27', 'control',   1850, 16, 7680000, 480000, 42.3),
('2026-01-27', 'treatment', 1860, 18, 8820000, 490000, 38.1),

-- Day 2: 2026-01-28 (화)
('2026-01-28', 'control',   1920, 17, 8160000, 480000, 41.8),
('2026-01-28', 'treatment', 1910, 19, 9310000, 490000, 37.5),

-- Day 3: 2026-01-29 (수)
('2026-01-29', 'control',   1880, 16, 7520000, 470000, 42.5),
('2026-01-29', 'treatment', 1890, 20, 9800000, 490000, 36.8),

-- Day 4: 2026-01-30 (목)
('2026-01-30', 'control',   1950, 17, 8330000, 490000, 41.2),
('2026-01-30', 'treatment', 1940, 21, 10290000, 490000, 36.2),

-- Day 5: 2026-01-31 (금)
('2026-01-31', 'control',   2010, 18, 8640000, 480000, 40.8),
('2026-01-31', 'treatment', 2020, 22, 10780000, 490000, 35.9),

-- Day 6: 2026-02-01 (토) - 주말 트래픽 상승
('2026-02-01', 'control',   2250, 20, 9600000, 480000, 40.5),
('2026-02-01', 'treatment', 2240, 25, 12250000, 490000, 35.2),

-- Day 7: 2026-02-02 (일) - 주말
('2026-02-02', 'control',   2180, 19, 9120000, 480000, 41.0),
('2026-02-02', 'treatment', 2190, 24, 11760000, 490000, 35.5),

-- Day 8: 2026-02-03 (월)
('2026-02-03', 'control',   1870, 16, 7680000, 480000, 42.1),
('2026-02-03', 'treatment', 1880, 20, 9800000, 490000, 36.5),

-- Day 9: 2026-02-04 (화)
('2026-02-04', 'control',   1900, 17, 8160000, 480000, 41.5),
('2026-02-04', 'treatment', 1910, 21, 10290000, 490000, 36.0),

-- Day 10: 2026-02-05 (수)
('2026-02-05', 'control',   1930, 17, 7990000, 470000, 41.8),
('2026-02-05', 'treatment', 1920, 21, 10290000, 490000, 36.3),

-- Day 11: 2026-02-06 (목)
('2026-02-06', 'control',   1960, 17, 8330000, 490000, 41.3),
('2026-02-06', 'treatment', 1950, 21, 10290000, 490000, 35.8),

-- Day 12: 2026-02-07 (금)
('2026-02-07', 'control',   2040, 18, 8640000, 480000, 40.6),
('2026-02-07', 'treatment', 2050, 22, 10780000, 490000, 35.4),

-- Day 13: 2026-02-08 (토) - 주말
('2026-02-08', 'control',   2280, 20, 9600000, 480000, 40.2),
('2026-02-08', 'treatment', 2270, 25, 12250000, 490000, 34.8),

-- Day 14: 2026-02-09 (일) - 주말
('2026-02-09', 'control',   2200, 19, 9120000, 480000, 40.8),
('2026-02-09', 'treatment', 2210, 24, 11760000, 490000, 35.0);

-- ============================================================================
-- 데이터 검증
-- ============================================================================
SELECT
    variant,
    COUNT(*) AS days,
    SUM(visitors) AS total_visitors,
    SUM(conversions) AS total_conversions,
    ROUND(SUM(conversions)::DECIMAL / SUM(visitors) * 100, 2) AS conversion_rate_pct,
    SUM(revenue) AS total_revenue,
    ROUND(AVG(avg_order_value), 0) AS avg_aov,
    ROUND(AVG(bounce_rate), 1) AS avg_bounce_rate
FROM ab_test_results
GROUP BY variant;
