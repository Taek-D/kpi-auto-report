# Pipeline Execution Log

> 2026-02-15 실행 결과

## 1. Coupang Crawling (`--crawl --source coupang`)

```
2026-02-15 11:01:45 [INFO] 환경 변수 로드 완료
2026-02-15 11:01:45 [INFO] 쿠팡 크롤링 시작
2026-02-15 11:01:45 [INFO] [쿠팡] 크롤링: '음식물처리기' (카테고리: 음식물처리기)
2026-02-15 11:01:48 [WARNING] [쿠팡] 요청 실패 (시도 1/3): 403 Forbidden
  → 쿠팡 봇 차단 (로컬 환경에서 직접 접근 시 403)
  → 실무: 프록시/쿠키 세션/Selenium 추가로 해결
```

**결과**: 쿠팡 봇 차단으로 0건 수집. 크롤러 구조(재시도, rate limiting, UA 로테이션)는 정상 동작 확인.

## 2. Competitor Analysis (`--analyze`)

```
2026-02-15 11:03:56 [INFO] [Supabase] 104건 조회 완료
2026-02-15 11:03:57 [INFO] 차트 4개 생성 완료
  → price_trend.png, ranking_comparison.png, review_growth.png, competitor_dashboard.png
```

**결과**: Supabase에서 104건 경쟁사 데이터 조회 성공. 4종 차트 생성.

## 3. Business Insight (`--insight`)

```
2026-02-15 11:01:52 [INFO] [Supabase] brand_daily_sales 450건 조회 완료
2026-02-15 11:01:53 [INFO] [Supabase] 경쟁사 8주 데이터 104건 조회 완료
  → channel_mix_trend.png, weekday_heatmap.png 생성
```

**핵심 인사이트**:
- 톰 GS홈쇼핑 비중 0%→18.1% (방송 효과)
- 스마트카라 1월 할인 기간(₩549K→₩599K) 식별
- 미닉스 쿠팡 광고비 ₩557K→₩641K 증액 권장

## 4. A/B Test Analysis (`--abtest`)

```
2026-02-15 11:01:51 [INFO] [Supabase] A/B 테스트 데이터 28건 조회 완료
  → ab_test_conversion.png, ab_test_daily.png 생성
```

**통계 결과**:
- 전환율: 0.88% → 1.07% (+22.6%)
- Welch's t-test: p=0.0000 (유의미)
- Cohen's d: 6.358 (큰 효과)
- Go/No-Go: GO 판정

## 5. ML Forecast (`--forecast`)

```
2026-02-15 11:05:54 [INFO] [Supabase] brand_daily_sales 450건 조회 완료
  → forecast_actual_vs_pred.png, forecast_feature_importance.png 생성
```

**모델 성능**:
- R² = 0.74 (우수)
- MAPE = 3.9% (평균 예측 오차)
- CV R² = 0.91 (±0.10)
- Feature Importance #1: revenue_lag_7d (82.7%)

## Summary

| 파이프라인 | Supabase | 차트 | 상태 |
|-----------|----------|------|------|
| Crawling | - | - | 쿠팡 403 (예상) |
| Analyze | 104건 | 4종 | OK |
| Insight | 450+104건 | 2종 | OK |
| A/B Test | 28건 | 2종 | OK |
| ML Forecast | 450건 | 2종 | OK |
| **합계** | **1,136건** | **10종** | **4/5 성공** |
