# 앳홈 KPI Daily Auto-Report System

> **매일 아침, 앳홈 3개 브랜드의 KPI 리포트가 Slack으로 자동 도착합니다.**

앳홈(미닉스/톰/프로티원) 브랜드별 매출을 수집하고, WoW 분석 + 이상 탐지 + 경쟁사 모니터링을 수행한 뒤 Slack으로 전송하는 자동화 파이프라인입니다. Python 크롤링(requests+BS4) + Pandas 분석 + scipy 통계 검정 + 시각화까지 포함한 데이터 분석 프로젝트입니다.

## 시스템 아키텍처

```
┌──────────────┐
│   Schedule   │  매일 08:00 KST
│  (Cron)      │
└──────┬───────┘
       │
       ├──────────────┬──────────────┬──────────────┐
       ▼              ▼              ▼              ▼
┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐
│  Yesterday │ │  Last Week │ │    Top     │ │ Competitor │
│ Brand KPIs │ │ Brand KPIs │ │  Products  │ │  Changes   │
└─────┬──────┘ └─────┬──────┘ └─────┬──────┘ └─────┬──────┘
      │              │              │              │
      └──────┬───────┴──────────────┴──────────────┘
             ▼
      ┌──────────────┐
      │    Merge     │  4개 데이터 소스 동기화
      │ Collect All  │
      └──────┬───────┘
             ▼
      ┌──────────────┐
      │  WoW Analysis│  브랜드별 분석 + 이상 탐지
      │  & Anomaly   │  + 경쟁사 모니터링
      └──────┬───────┘
             ▼
      ┌──────────────┐
      │    Slack     │  Webhook으로 리포트 전송
      │  Send Alert  │
      └──────────────┘
```

**8개 노드** | 병렬 데이터 수집 | 브랜드별 WoW 분석 | 경쟁사 모니터링 | 이상 탐지 알림

## 앳홈 브랜드

| 브랜드 | 카테고리 | 주요 제품 | 핵심 채널 |
|--------|---------|---------|----------|
| 미닉스 (minix) | 소형가전 | 더플렌더, 미니건조기, 식기세척기, 음식물처리기 | 쿠팡, GS홈쇼핑 |
| 톰 (thome) | 뷰티디바이스 | 더글로우 프로, 더글로우, LED 마스크 | GS홈쇼핑, 쿠팡 |
| 프로티원 (protione) | 건강기능식품 | 프로틴 바, 쉐이크, 비타민 | 쿠팡, 올리브영 |

## 핵심 기능

- **브랜드별 일일 KPI**: 매출, 주문 수, ROAS, 채널별 매출 비중
- **WoW 비교 분석**: 브랜드별 전주 동일 요일 대비 증감률 (%) 및 트렌드 아이콘 (↑↓→)
- **이상 탐지**: 브랜드별 차등 임계값 (톰은 홈쇼핑 방송일 변동 감안하여 완화)
- **매출 Top 5 제품**: 일일 매출 기준 상위 제품 (브랜드 태그 + 평점)
- **경쟁사 모니터링**: 쿠팡/네이버 순위 변동, 가격 변동 알림 (8주 추이)
- **경쟁사 크롤링**: Python으로 쿠팡(BeautifulSoup) + 네이버 쇼핑(API) 자동 수집
- **비즈니스 인사이트 분석**: 채널 믹스 변동, 경쟁사-매출 상관, 요일별 패턴, 액션 추천
- **A/B 테스트 통계 분석**: 실험 설계 검증 → 가설 검정(t-test, Mann-Whitney U) → Cohen's d → ROI/Go-No-Go 의사결정
- **ML 매출 예측**: scikit-learn Random Forest 기반 브랜드별 매출 예측 (R²=0.74, MAPE=3.9%)
- **검색 트렌드-매출 상관 분석**: Google Trends + Naver DataLab 검색량 수집 → Pearson/Spearman 상관, 선행 지표(lead-lag), 성수기 탐지
- **광고 퍼포먼스 분석**: 채널별 ROAS/CPC/ROI 효율 등급(S/A/B/C), 예산 재배분 시뮬레이션, 성장 기회 탐지(스케일업/개선/축소)
- **인사이트 스토리텔링**: 발견 → 근거 → 제안 → 예상 효과 4단계 구조 비즈니스 액션 추천
- **KPI 통합 대시보드**: 브라우저에서 바로 열 수 있는 단일 HTML 대시보드 (7개 섹션, 인라인 차트)
- **데이터 시각화**: matplotlib/seaborn 기반 18종 분석 차트 자동 생성
- **주간/월간 요약 리포트**: Supabase RPC → Pandas → 브랜드별 WoW/MoM 변화율 + 채널 비중 분석
- **n8n-크롤러 연동**: Execute Command 노드로 Python 크롤링 자동 실행 + Slack 결과 알림

## Slack 메시지 예시

```
📊 앳홈 Daily KPI 리포트 | 2026-02-13

전체 실적 (어제 기준)
━━━━━━━━━━━━━━━━━━━━━
💰 총 매출: ₩29,920,000 (+18.5% ↑)
📦 총 주문: 434건 (+17.2% ↑)

브랜드별 실적
━━━━━━━━━━━━━━━━━━━━━
🏠 미닉스
  매출: ₩12,430,000 (+50.7% ↑)
  주문: 131건 | ROAS: 6.9 (coupang 33.2%, gs_home 28.2%)

💆 톰
  매출: ₩11,260,000 (+102.2% ↑)
  주문: 103건 | ROAS: 6.1 (gs_home 46.2%, coupang 20.8%)

💪 프로티원
  매출: ₩6,230,000 (+7.8% ↑)
  주문: 200건 | ROAS: 5.8 (coupang 35.0%, oliveyoung 26.5%)

🏆 매출 Top 5 제품
1. 톰 더글로우 프로 [톰]: ₩5,960,000 ★4.8
2. 미닉스 식기세척기 [미닉스]: ₩4,590,000 ★4.6
3. 미닉스 미니건조기 [미닉스]: ₩3,490,000 ★4.8
4. 미닉스 더플렌더 [미닉스]: ₩2,670,000 ★4.7
5. 톰 더글로우 [톰]: ₩2,376,000 ★4.6

🔍 경쟁사 모니터링
📈 미닉스 음식물처리기 [coupang] 4위→3위 (상승)
📈 톰 더글로우 프로 [coupang] 4위→3위 (상승)
💰 린클 루펜 SLW-03 [린클] ₩10,000 인하

⏰ 리포트 생성: 08:00:12
```

## 기술 스택

| 구분 | 기술 | 용도 |
|------|------|------|
| Database | PostgreSQL (Supabase) | 브랜드별 KPI + 경쟁사 데이터 저장 |
| API | Supabase REST API (RPC) | 4개 서버리스 함수 호출 |
| Workflow | n8n (Docker) | 8노드 자동화 파이프라인 |
| Messaging | Slack Incoming Webhooks | 리포트 전송 |
| Query | SQL (Window Functions, CTEs, JSONB) | 데이터 분석 쿼리 |
| Crawling | Python (requests + BeautifulSoup4) | 쿠팡 검색 결과 스크래핑 |
| API Client | Python (requests + Naver API) | 네이버 쇼핑 검색 API |
| Analysis | Python (Pandas) | 경쟁사 데이터 전처리 + WoW 분석 |
| Statistics | Python (scipy) | A/B 테스트 통계 검정 파이프라인 (Power Analysis → t-test → Mann-Whitney U → Cohen's d) |
| ML | Python (scikit-learn) | 매출 예측 (Random Forest, Feature Engineering, Cross Validation) |
| Trend Data | Python (pytrends + Naver DataLab API) | Google Trends / Naver 검색 트렌드 수집 |
| Ad Analytics | Python (Pandas + numpy) | 광고 효율 분석, 예산 시뮬레이션, 기회 탐지 |
| Visualization | Python (matplotlib + seaborn) | 18종 분석 차트 자동 생성 |

## 프로젝트 구조

```
KPI_Auto_Report(Athome)/
├── requirements.txt            # Python 의존성
├── docker-compose.yml          # n8n Docker 컨테이너 설정
├── .env.example                # 환경변수 템플릿
├── KPI_Auto_Report_PRD.md      # 제품 요구사항 문서 (v2)
├── crawlers/                   # Python 경쟁사 크롤링 & 분석 패키지
│   ├── config.py               # 크롤링 대상 설정 (제품, 카테고리, 브랜드 매핑)
│   ├── coupang_crawler.py      # 쿠팡 검색 스크래핑 (requests + BeautifulSoup)
│   ├── naver_crawler.py        # 네이버 쇼핑 API 클라이언트
│   ├── supabase_loader.py      # Supabase REST API 데이터 적재 + RPC 호출
│   ├── analyzer.py             # Pandas 분석 + matplotlib/seaborn 시각화
│   ├── report_generator.py     # 주간/월간 요약 리포트 (Pandas + matplotlib)
│   ├── insight_analyzer.py     # 비즈니스 인사이트 (채널 믹스, 경쟁사 상관, 요일 패턴)
│   ├── ab_test_analyzer.py     # A/B 테스트 통계 분석 파이프라인 (scipy)
│   ├── demand_forecaster.py    # ML 매출 예측 (scikit-learn Random Forest)
│   ├── trend_collector.py      # 검색 트렌드 수집 (Google Trends + Naver DataLab)
│   ├── trend_analyzer.py       # 트렌드-매출 상관 분석 + 차트 4종
│   ├── dashboard_generator.py  # KPI 통합 대시보드 HTML 생성 (7개 섹션 + 스토리텔링)
│   ├── ad_performance_analyzer.py # 광고 퍼포먼스 분석 (ROAS 효율 + 예산 시뮬레이션 + 기회 탐지)
│   └── main.py                 # CLI 진입점 (argparse)
├── schema/                     # DB 스키마 DDL + 샘플 데이터 + RPC 함수
│   ├── brand_daily_sales.sql   # 브랜드x채널 일일 매출 + RPC 2개
│   ├── products.sql            # 제품 마스터 + 제품별 매출 + RPC 1개
│   ├── market_competitors.sql  # 경쟁사 크롤링 데이터 + RPC 1개
│   ├── competitor_extended.sql # 경쟁사 8주 확장 데이터 (장기 추이 분석)
│   ├── ab_test_sample.sql      # A/B 테스트 시뮬레이션 데이터 (14일)
│   ├── search_trends.sql       # 검색 트렌드 테이블 + 샘플 30일 + RPC 함수
│   ├── summary_functions.sql   # 주간/월간 요약 RPC 함수 2개
├── queries/                    # SQL 쿼리 원본 (학습/문서용)
│   ├── brand_kpis_yesterday.sql # 브랜드별 어제 KPI + 채널 비중
│   ├── brand_kpis_last_week.sql # 지난주 동일 요일 브랜드별 KPI
│   ├── top_products_by_brand.sql# 브랜드별 상위 제품 (이중 RANK)
│   ├── channel_performance.sql  # 채널별 매출/ROAS/전환율 WoW
│   └── competitor_changes.sql   # 경쟁사 순위/가격 변동 감지
├── n8n/                        # n8n 워크플로우
│   ├── workflow.json           # 일일 KPI 8노드 워크플로우
│   ├── transform.js            # 브랜드별 WoW + 이상 탐지 + 경쟁사
│   ├── slack_send.js           # Slack Webhook 전송
│   ├── workflow_crawler.json   # 주간 크롤링 4노드 워크플로우
│   └── crawler_notify.js       # 크롤링 결과 Slack 알림
├── output/                     # 시각화 차트 출력 디렉토리
│   ├── price_trend.png         # 경쟁사 가격 추이
│   ├── ranking_comparison.png  # 검색 순위 비교
│   ├── review_growth.png       # 주간 리뷰 증가량
│   ├── competitor_dashboard.png# 종합 대시보드 (2x2)
│   ├── monthly_report.png      # 월간 브랜드별 매출 bar chart
│   ├── channel_mix_trend.png   # 채널 비중 변화 stacked area chart
│   ├── weekday_heatmap.png     # 브랜드x요일 매출 히트맵
│   ├── ab_test_conversion.png  # A/B 전환율 비교 + 신뢰구간
│   ├── ab_test_daily.png       # A/B 일별 전환율 추이
│   ├── forecast_actual_vs_pred.png  # ML 실제 vs 예측 매출 비교
│   ├── forecast_feature_importance.png # ML Feature Importance Top 10
│   ├── trend_sales_overlay.png     # 트렌드 vs 매출 듀얼축 라인 (1x3 브랜드별)
│   ├── trend_correlation_heatmap.png # 트렌드-매출 상관 히트맵 (Pearson r)
│   ├── trend_lead_lag.png          # 선행 지표 lag별 상관계수 바차트
│   ├── trend_peak_season.png       # 성수기 트렌드 area + 피크 구간 강조
│   ├── ad_roas_comparison.png      # 채널별 ROAS 효율 등급 수평 바
│   ├── ad_budget_simulation.png   # 현재 vs 최적 예산 배분 grouped bar
│   ├── ad_opportunity_matrix.png  # ROAS vs 광고비 기회 매트릭스 산점도
│   └── dashboard.html              # KPI 통합 대시보드 (단일 HTML)
├── docs/
│   ├── SETUP.md                # 설치/설정 가이드
│   ├── SQL_GUIDE.md            # SQL 쿼리 상세 가이드
│   └── SLACK_INTEGRATION.md    # Slack 메시지 포맷 가이드
└── tests/
    └── TEST_RESULTS.md         # 테스트 결과
```

## 빠른 시작

### 1. 환경변수 설정

```bash
cp .env.example .env
# .env 파일을 열어서 Supabase, Slack 정보 입력
```

### 2. n8n 실행

```bash
docker-compose up -d
# http://localhost:5678 접속
```

### 3. Supabase 테이블 생성

Supabase SQL Editor에서 순서대로 실행:
```bash
1. schema/products.sql
2. schema/brand_daily_sales.sql
3. schema/market_competitors.sql
4. schema/search_trends.sql
```

### 4. 워크플로우 설정

1. n8n UI에서 **Import from File** > `n8n/workflow.json`
2. **"WoW Analysis"** 노드 > `n8n/transform.js` 붙여넣기
3. **"Slack Send"** 노드 > `n8n/slack_send.js` 붙여넣기
4. `SLACK_WEBHOOK_URL`을 실제 URL로 교체
5. **Execute Workflow**로 테스트

### 5. RPC 함수 테스트

```sql
-- 일일 KPI
SELECT * FROM get_brand_kpis_yesterday();
SELECT * FROM get_brand_kpis_last_week();
SELECT * FROM get_top_products();
SELECT * FROM get_competitor_changes();

-- 주간/월간 요약
SELECT * FROM get_trend_sales_correlation(30);
SELECT * FROM get_weekly_summary('2026-02-12'::date);
SELECT * FROM get_monthly_summary(2026, 2);
```

## Python 경쟁사 크롤링 & 분석

### 설치

```bash
pip install -r requirements.txt
```

### 사용법

```bash
# 전체 파이프라인 (크롤링 → Supabase 적재 → 분석 + 시각화)
python -m crawlers.main --all

# 크롤링 + 적재만
python -m crawlers.main --crawl

# 분석 + 시각화만 (Supabase 기존 데이터 사용)
python -m crawlers.main --analyze

# 특정 소스만 크롤링
python -m crawlers.main --crawl --source coupang
python -m crawlers.main --crawl --source naver

# 주간/월간 요약 리포트
python -m crawlers.main --report weekly
python -m crawlers.main --report monthly

# 비즈니스 인사이트 분석 (채널 믹스, 경쟁사 상관, 요일 패턴)
python -m crawlers.main --insight

# A/B 테스트 통계 분석 (실험 설계 검증 → 가설 검정 → Go/No-Go)
python -m crawlers.main --abtest

# ML 매출 예측 (Random Forest + Feature Importance + 브랜드별 예측)
python -m crawlers.main --forecast

# 검색 트렌드 수집 (Google Trends + Naver DataLab, API 키 필요)
python -m crawlers.main --trend-collect

# 트렌드-매출 상관 분석 (Pearson/Spearman + 선행 지표 + 성수기 탐지)
python -m crawlers.main --trend

# KPI 통합 대시보드 HTML (브라우저에서 바로 열기)
python -m crawlers.main --dashboard

# 광고 퍼포먼스 분석 (ROAS 효율 + 예산 재배분 + 기회 탐지)
python -m crawlers.main --ad-perf
```

### 크롤링 대상

| 카테고리 | 소스 | 수집 항목 |
|---------|------|----------|
| 음식물처리기 | 쿠팡, 네이버 | 순위, 가격, 리뷰 수, 평점 |
| 식기세척기 | 쿠팡, 네이버 | 순위, 가격, 리뷰 수, 평점 |
| 소형건조기 | 쿠팡, 네이버 | 순위, 가격, 리뷰 수, 평점 |
| 뷰티디바이스 | 쿠팡, 네이버 | 순위, 가격, 리뷰 수, 평점 |

### 시각화 차트 (18종)

| 구분 | 차트 | 파일명 | 설명 |
|------|------|--------|------|
| 경쟁사 | 가격 추이 | `price_trend.png` | 경쟁사별 가격 변동 라인 차트 |
| 경쟁사 | 순위 비교 | `ranking_comparison.png` | 자사 vs 경쟁사 순위 (수평 바) |
| 경쟁사 | 리뷰 성장 | `review_growth.png` | 주간 리뷰 증가량 (그룹 바) |
| 경쟁사 | 종합 대시보드 | `competitor_dashboard.png` | 2x2 서브플롯 전체 요약 |
| 리포트 | 월간 리포트 | `monthly_report.png` | 브랜드별 월간 매출 bar chart |
| 인사이트 | 채널 믹스 | `channel_mix_trend.png` | 브랜드별 채널 비중 stacked area chart |
| 인사이트 | 요일 히트맵 | `weekday_heatmap.png` | 브랜드x요일 평균 매출 히트맵 |
| A/B 테스트 | 전환율 비교 | `ab_test_conversion.png` | A/B 전환율 + 95% 신뢰구간 bar chart |
| A/B 테스트 | 일별 추이 | `ab_test_daily.png` | A vs B 일별 전환율 라인 차트 |
| ML 예측 | 실제 vs 예측 | `forecast_actual_vs_pred.png` | 브랜드별 실제/예측 매출 bar+line |
| ML 예측 | Feature Importance | `forecast_feature_importance.png` | Top 10 feature 중요도 수평 bar |
| 트렌드 | 트렌드 vs 매출 | `trend_sales_overlay.png` | 듀얼축 라인 (1x3 브랜드별) |
| 트렌드 | 상관 히트맵 | `trend_correlation_heatmap.png` | 브랜드 x 소스 Pearson r |
| 트렌드 | 선행 지표 | `trend_lead_lag.png` | lag별 상관계수 바차트 |
| 트렌드 | 성수기 탐지 | `trend_peak_season.png` | 트렌드 area + 피크 구간 강조 |
| 광고 | ROAS 비교 | `ad_roas_comparison.png` | 브랜드x채널 ROAS 수평 바 (효율 등급 색상) |
| 광고 | 예산 시뮬레이션 | `ad_budget_simulation.png` | 현재 vs 최적 예산 배분 grouped bar |
| 광고 | 기회 매트릭스 | `ad_opportunity_matrix.png` | ROAS vs 광고비 산점도 (4사분면) |

> 차트에서 주황색 = 미닉스, 파란색 = 톰, 초록색 = 프로티원으로 구분됩니다.

### 크롤링 기술 세부사항

- **쿠팡**: requests + BeautifulSoup4, User-Agent 로테이션(5종), 2~4초 랜덤 딜레이, 3회 재시도
- **네이버**: 공식 쇼핑 검색 API (`openapi.naver.com`), Client ID/Secret 인증
- **적재**: Supabase REST API upsert (`Prefer: resolution=merge-duplicates`), 10건씩 배치 처리
- **분석**: Pandas DataFrame 변환, WoW 비교, matplotlib/seaborn 한글 폰트 지원

## 주간/월간 요약 리포트

Supabase RPC 함수를 통해 브랜드별 집계 데이터를 조회하고, Pandas로 가공하여 Slack 포맷 텍스트와 차트를 생성합니다.

### 주간 리포트 (`--report weekly`)

- 7일간 브랜드별 매출/주문/ROAS 합계
- 전주 대비 WoW 변화율 (%)
- Best/Worst 채널 자동 판별
- 채널별 매출 비중 (share_pct)

### 월간 리포트 (`--report monthly`)

- 해당 월 브랜드별 합계
- 전월 대비 MoM 변화율 (%)
- `output/monthly_report.png` 차트 자동 생성

### RPC 함수 (7개)

| 함수 | 용도 | 반환 |
|------|------|------|
| `get_brand_kpis_yesterday()` | 어제 브랜드별 KPI | 매출, 주문, ROAS, 채널 breakdown |
| `get_brand_kpis_last_week()` | 지난주 동일 요일 KPI | WoW 비교용 |
| `get_top_products()` | 매출 상위 5개 제품 | 제품명, 매출, 평점 |
| `get_competitor_changes()` | 경쟁사 순위/가격 변동 | 전주 대비 변동 |
| `get_trend_sales_correlation(p_days)` | 트렌드-매출 상관 데이터 | 브랜드별 트렌드+매출 JOIN |
| `get_weekly_summary(p_end_date)` | 주간 브랜드별 집계 | WoW%, 채널 비중 JSONB |
| `get_monthly_summary(p_year, p_month)` | 월간 브랜드별 집계 | MoM%, 채널 비중 JSONB |

## 비즈니스 인사이트 분석

`--insight` 옵션으로 데이터 기반 "So What?" 분석을 수행합니다.

### 분석 항목

| 분석 | 내용 | 인사이트 예시 |
|------|------|-------------|
| 채널 믹스 변동 | 주간 채널별 매출 비중 변화 | "톰 GS홈쇼핑 비중 0%→18.1% (방송 효과)" |
| 경쟁사-매출 상관 | 경쟁사 가격 변동 vs 자사 매출 | "스마트카라 1월 할인 기간(₩549K) 식별" |
| 요일별 패턴 | 브랜드별 요일-매출 히트맵 | "프로티원 목요일 주문 집중 → 수요일 딜 등록" |
| 액션 추천 | 분석 결과 → 구체적 액션 아이템 | "쿠팡 광고비 ₩557K→₩641K 증액 권장" |

### 출력 예시

```
🔍 앳홈 비즈니스 인사이트 분석

📊 채널 믹스 변동 분석
  [톰]
    GS홈쇼핑: 0.0% → 18.1% (↑18.1%p) ⚠️
    쿠팡: 38.6% → 31.6% (↓7.0%p) ⚠️

🏢 경쟁사-매출 상관 분석
  [스마트카라 가격 변동]
    가격 범위: ₩549,000 ~ ₩599,000 (차이: ₩50,000)
    할인 기간: 01/06 ~ 01/20

  [앳홈 제품 순위 변화]
    미닉스 음식물처리기: 5위 → 3위 (↑2)
    톰 더글로우 프로: 5위 → 3위 (↑2)
```

## A/B 테스트 통계 분석

`--abtest` 옵션으로 미닉스 자사몰 결제 페이지 A/B 테스트의 전체 통계 분석 파이프라인을 실행합니다. 실험 설계 검증(Power Analysis, SRM)부터 가설 검정(Welch's t-test, Mann-Whitney U), 효과 크기(Cohen's d), 비즈니스 해석(ROI, Go/No-Go)까지 실무 동일 프로세스를 구현했습니다.

> 시뮬레이션 데이터 기반이지만, 실무 운영 데이터 투입 시 동일 파이프라인으로 즉시 분석 가능한 구조입니다.

### 실험 설계

| 항목 | 내용 |
|------|------|
| 대상 | 미닉스 자사몰 결제 페이지 |
| 배경 | 전환율(0.87%)이 업계 평균(1.2%) 대비 낮음 |
| Control (A) | 기존 결제 페이지 |
| Treatment (B) | 개선 결제 페이지 (원클릭 결제 + 리뷰 위젯) |
| 기간 | 14일 (2주, 요일 효과 포함) |

### 통계 분석 파이프라인

| 단계 | 방법 | 용도 | 판정 기준 |
|------|------|------|----------|
| 1. 실험 설계 검증 | Power Analysis, SRM (chi-squared) | 샘플 충분성 + 배분 편향 체크 | power=0.8, p>0.05 |
| 2. 전환율 비교 | Welch's t-test | 두 그룹 평균 차이 (비등분산) | p<0.05 |
| 3. 매출 비교 | Mann-Whitney U test | 비정규 분포 대응 (단측) | p<0.05 |
| 4. 효과 크기 | Cohen's d | 실질적 의미 판단 | d>0.2 (small) |
| 5. 신뢰구간 | 95% CI | 전환율 차이 범위 | CI가 0 미포함 |
| 6. 비즈니스 해석 | ROI + Go/No-Go | 의사결정 프레임워크 | ROI>100% |

### 출력 예시

```
🧪 A/B 테스트 분석: 미닉스 자사몰 결제 페이지 개선

📊 통계 분석 결과
  전환율: 0.88% → 1.07% (+22.6%)
  Welch's t-test: p=0.0000 ✅ 통계적으로 유의미
  일 매출 증가분: +₩2,135,714/일

💼 비즈니스 해석
  연 매출 증가 예상: +₩7.8억
  ROI: 15,591% (개발비 ₩500만 기준)
  의사결정: ✅ GO - 전체 트래픽 적용 권장
```

## ML 매출 예측 (Demand Forecasting)

`--forecast` 옵션으로 브랜드별 일일 매출을 학습하여 예측 모델을 구축합니다. Feature Engineering → 모델 학습(Random Forest) → 교차 검증 → Feature Importance 분석까지 ML 파이프라인 전체를 구현했습니다.

> 시뮬레이션 데이터 기반이지만, 실무 운영 데이터 투입 시 동일 파이프라인으로 즉시 예측 가능한 구조입니다.

### Feature Engineering (11개)

| 카테고리 | Feature | 설명 |
|---------|---------|------|
| 시간 | day_of_week, is_weekend, week_of_month, month, day_of_month | 요일/주말/주차 패턴 |
| 범주 | brand_enc, channel_enc | 브랜드/채널 인코딩 |
| Lag | revenue_lag_1d, revenue_lag_7d | 전일/전주 동요일 매출 |
| 통계 | revenue_rolling_7d | 7일 이동평균 |
| 마케팅 | roas_feature | 광고 수익률 |

### 모델 성능

| 지표 | 값 | 해석 |
|------|-----|------|
| R² | 0.74 | 매출 변동의 74% 설명 (우수) |
| MAPE | 3.9% | 평균 예측 오차 3.9% |
| CV R² | 0.91 (±0.10) | 5-Fold 교차검증 안정적 |

### Feature Importance

전주 동요일 매출(revenue_lag_7d)이 82.7%로 압도적 — 주간 패턴이 매출 예측의 핵심 요인. GS홈쇼핑 방송일 등 외부 이벤트 feature 추가 시 정확도 향상 가능.

### 비즈니스 활용

- 다음 주 예상 매출 기반 재고 발주량 사전 조정
- 예측 대비 실적 하회 시 이상 탐지 (예측 기반 동적 임계값)
- 채널별 예측 매출로 광고 예산 사전 배분 최적화

## 검색 트렌드-매출 상관 분석

`--trend` 옵션으로 Google Trends / Naver DataLab 검색 트렌드와 내부 매출 데이터의 상관 분석을 수행합니다. `--trend-collect`로 실제 API 데이터를 수집하거나, 샘플 데이터(30일)로 바로 분석할 수 있습니다.

> Data Mart Presentation의 "외부 검색 트렌드 x 내부 매출 상관 분석" 아키텍처를 실제 구현한 모듈입니다.

### 분석 항목

| 분석 | 방법 | 인사이트 예시 |
|------|------|-------------|
| 상관 분석 | Pearson/Spearman per brand per source | "미닉스 x Google r=0.72 (강한 양의 상관)" |
| 선행 지표 | lag -7~+7일 cross-correlation | "검색이 매출보다 3일 선행 (r=0.68)" |
| 성수기 탐지 | 75th percentile 초과 기간 | "02/01~02/05 설 연휴 성수기 (5일)" |
| 비즈니스 추천 | 상관/선행/성수기 결합 | "검색량 급증 시 3일 후 프로모션 준비" |

### 데이터 소스

| 소스 | 방법 | 비고 |
|------|------|------|
| Google Trends | pytrends 라이브러리 | 5개씩 배치, 2초 딜레이, 실패 시 graceful skip |
| Naver DataLab | REST API (검색어 트렌드) | Client ID/Secret 필요, 5개 keywordGroups/요청 |

### 출력 예시

```
📈 검색 트렌드-매출 상관 분석

📊 상관 분석 (검색 트렌드 vs 매출)
  [미닉스 x Google Trends] Pearson r=0.721**, Spearman r=0.685 (n=7)
  [톰 x Naver DataLab] Pearson r=0.534*, Spearman r=0.498 (n=7)

⏱️ 선행 지표 분석
  [미닉스] 검색이 매출보다 3일 선행 (r=0.684)
  [프로티원] 동시 상관 최대 (lag=0, r=0.512)

🔥 성수기 탐지
  [미닉스] 02/01~02/05 (5일) 평균 트렌드 78.3
  [톰] 01/20~01/23 (4일) 평균 트렌드 65.1

🎯 비즈니스 액션 추천
  1. [광고] 미닉스: Google Trends 검색량과 매출 강한 상관 → 트렌드 상승 시 광고비 증액
  2. [타이밍] 미닉스: 검색 3일 선행 → 검색량 급증 감지 시 프로모션 사전 준비
  3. [재고] 미닉스: 02/01~02/05 성수기 → 해당 기간 재고 사전 확보
```

## 광고 퍼포먼스 분석

`--ad-perf` 옵션으로 채널별 광고 효율 분석, 예산 재배분 시뮬레이션, 성장 기회 탐지를 수행합니다. JD 요구 "광고/마케팅 퍼포먼스 데이터 분석"에 직접 대응하는 모듈입니다.

### 분석 항목

| 분석 | 내용 | 인사이트 예시 |
|------|------|-------------|
| 채널별 광고 효율 | ROAS, CPC, ROI% + S/A/B/C 등급 | "[S등급] 미닉스 자사몰: ROAS 8.9, CPC ₩76" |
| 예산 재배분 시뮬레이션 | ROAS 가중 비례 배분 (최소 10%) | "최적 재배분 시 예상 매출 +7.5%" |
| 성장 기회 탐지 | High ROAS + Low Spend = 스케일업 | "미닉스 자사몰: ROAS 8.9, 광고비 비중 8.6%" |

### 출력 예시

```
📈 광고 퍼포먼스 분석
=======================================================
💰 채널별 ROAS 랭킹
  [S등급] 미닉스 자사몰: ROAS 8.9 | CPC ₩76 | ROI 791%
  [A등급] 미닉스 쿠팡: ROAS 7.1 | CPC ₩68 | ROI 610%

📊 예산 재배분 시뮬레이션
  현재 총 광고비: ₩3,710,000 → 예상 매출: ₩29,920,000
  최적 재배분 시: ₩3,710,000 → 예상 매출: ₩32,150,000 (+7.5%)

🎯 성장 기회
  🟢 스케일업: 미닉스 자사몰 (ROAS 8.9, 광고비 비중 8.6%)
  🟡 유지: 프로티원 쿠팡 (ROAS 6.2, 적정 수준)
  🔴 개선필요: 톰 네이버 (ROAS 4.0, 광고비 비중 7.8%)
```

## KPI 통합 대시보드

`--dashboard` 옵션으로 브라우저에서 바로 열 수 있는 단일 HTML 대시보드를 생성합니다. Supabase에서 데이터를 조회하고, matplotlib 차트를 base64로 인라인 임베딩하여 외부 의존성 없는 self-contained 파일(`output/dashboard.html`)을 출력합니다.

### 대시보드 구성 (7개 섹션)

| 섹션 | 내용 | 데이터 소스 |
|------|------|------------|
| 헤더 + KPI 요약 | 총 매출/주문/ROAS, WoW% | RPC: yesterday + last_week |
| 브랜드별 KPI 카드 | 3개 브랜드 매출/주문/ROAS + 채널 비중 mini bar | RPC + brand_daily_sales |
| 검색 트렌드 상관 | 상관 히트맵, 선행 지표, 성수기 탐지 | search_trends + brand_daily_sales |
| 채널 믹스 & 요일 | 채널 비중 추이 차트, 요일별 매출 히트맵 | brand_daily_sales |
| 광고 퍼포먼스 | ROAS 효율 등급 테이블 + 기회 신호 카드 | brand_daily_sales |
| 매출 Top 5 제품 | 브랜드 태그 + 평점 테이블 | RPC: top_products |
| 비즈니스 액션 추천 | 발견→근거→제안→효과 스토리텔링 | 전체 분석 결과 통합 |

### 사용법

```bash
python -m crawlers.main --dashboard
start output/dashboard.html   # 브라우저에서 열기
```

## n8n 크롤링 워크플로우

매주 월요일 07:00에 Python 크롤링 파이프라인을 자동 실행하는 n8n 워크플로우입니다.

```
Schedule (Mon 07:00) → Execute Command → Parse Result → Slack Notify
```

- `workflow_crawler.json`: 4노드 워크플로우 정의
- `crawler_notify.js`: stdout 파싱 + Slack 알림 코드
- 크롤링 결과 (수집 건수, 적재 성공/실패, 차트 생성) 자동 알림

## 이상 탐지 기준

| 브랜드 | 매출 Critical | 주문 Warning | 비고 |
|--------|-------------|-------------|------|
| 미닉스 | WoW -20% | WoW -15% | 기본 |
| 톰 | WoW -30% | WoW -25% | GS홈쇼핑 방송일 변동 감안 |
| 프로티원 | WoW -20% | WoW -15% | 기본 |

## SQL 주요 기법

- **Window Functions**: RANK() OVER (PARTITION BY brand), SUM() OVER (PARTITION BY), LAG(), FIRST_VALUE()
- **CTE (WITH절)**: 복잡한 쿼리를 브랜드별 집계 > 전체 합계 > UNION으로 분해
- **JSONB**: 채널별 매출 breakdown을 JSON 배열로 반환 (jsonb_agg + jsonb_build_object)
- **Self-JOIN**: 경쟁사 전주 대비 순위/가격 변동 비교
- **복합 인덱스**: (sale_date, brand), (sale_date, channel)
- **서브쿼리 패턴**: Window Function → jsonb_agg() 변환 시 서브쿼리 우선 계산 필수

## 경쟁사 모니터링

| 카테고리 | 앳홈 제품 | 경쟁사 |
|---------|---------|--------|
| 음식물처리기 | 미닉스 음식물처리기 | 스마트카라, 린클 |
| 뷰티디바이스 | 톰 더글로우 프로 | LG 프라엘, 페이스팩토리 |

## 배운 점

### 기술적
- n8n 워크플로우 설계: 일일 KPI 8노드 (병렬) + 크롤링 4노드 (직렬)
- Supabase RPC + JSONB 반환 (채널별 breakdown, WoW/MoM 변화율)
- SQL Window Functions 실전 활용 (이중 RANK, PARTITION BY, FIRST_VALUE)
- 브랜드별 차등 이상 탐지 임계값 설계
- 경쟁사 크롤링 데이터 모델링 (Self-JOIN 비교, 8주 장기 추이)
- Python 크롤링 파이프라인 (requests + BeautifulSoup + rate limiting)
- Pandas 데이터 전처리 + matplotlib/seaborn 시각화 (한글 폰트 처리)
- scipy 통계 검정 파이프라인 (Power Analysis → Welch's t-test → Mann-Whitney U → Cohen's d → SRM)
- A/B 테스트 전체 분석 프로세스 설계: 실험 설계 검증 → 가설 검정 → 효과 크기 → 비즈니스 해석(ROI/Go-No-Go)
- scikit-learn ML 파이프라인: Feature Engineering(Lag, Rolling, Encoding) → Random Forest → Cross Validation
- Feature Importance 분석: 전주 동요일 매출(82.7%)이 예측 핵심 → 주간 패턴 중요성 확인
- 외부 트렌드 데이터 연동: Google Trends (pytrends) + Naver DataLab REST API 수집 파이프라인
- Cross-correlation 분석: lead-lag -7~+7일 시계열 상관 분석으로 선행 지표 탐지
- 성수기 탐지: 75th percentile 기반 피크 구간 자동 식별
- 광고 퍼포먼스 분석: ROAS/CPC/ROI 효율 등급 + ROAS 가중 예산 재배분 시뮬레이션 + 기회 매트릭스 산점도
- 인사이트 스토리텔링: 발견→근거→제안→효과 4단계 구조로 데이터 기반 의사결정 프레임워크 구현
- CLI 도구 설계 (argparse, 모듈별 실행, lazy import 패턴)
- Window Function을 jsonb_agg() 안에서 직접 사용 불가 → 서브쿼리 패턴 학습

### 비즈니스
- 멀티브랜드 KPI 모니터링 체계 설계
- 채널 믹스 변동 분석으로 채널 전략 의사결정 지원
- 경쟁사 가격 변동과 자사 매출 상관 분석 (8주 크로스 체크)
- 요일별 매출 패턴 분석 → 프로모션 타이밍 최적화
- A/B 테스트 통계 분석 파이프라인 구축 (실험 설계 → 검정 → 효과 크기 → Go/No-Go 의사결정)
- 분석 결과를 구체적 액션 아이템(광고비 증액, 딜 등록, 리타게팅)으로 변환
- 검색 트렌드-매출 상관으로 "검색이 매출을 선행하는가?" 정량적 검증 → 프로모션 타이밍 최적화

## 보안 점검 (Security Audit)

OWASP Top 10 기준 보안 취약점 점검을 수행했습니다 (2026-02-15).

### 점검 결과 요약

| 항목 | 판정 | 근거 |
|------|------|------|
| SQL Injection | **PASS** | RPC 함수 6개 모두 PL/pgSQL 파라미터 바인딩, 동적 SQL 없음 |
| XSS | **PASS** | Slack mrkdwn 렌더링, 사용자 입력 미포함, `eval()` 미사용 |
| 인증 우회 | **PASS** | CLI 전용 파이프라인, argparse choices 제한 |
| 시크릿 관리 | **FIXED** | workflow.json JWT 하드코딩 → 플레이스홀더 교체 완료 |
| TLS 설정 | **FIXED** | `NODE_TLS_REJECT_UNAUTHORIZED=0` 제거 (MITM 방어) |
| RPC 입력 검증 | **FIXED** | `ALLOWED_RPC_FUNCTIONS` 화이트리스트 추가 (Path Traversal 방지) |

### 수정 이력

- `n8n/workflow.json`: Supabase JWT 토큰 8곳 → `YOUR_SUPABASE_ANON_KEY` 플레이스홀더 교체
- `docker-compose.yml`: `NODE_TLS_REJECT_UNAUTHORIZED=0` 제거
- `crawlers/supabase_loader.py`: RPC 함수명 화이트리스트 검증 추가

### 남은 권장 사항

- Supabase RLS (Row Level Security) 정책 활성화
- `requirements.txt` 버전 상한 추가 (`requests>=2.31.0,<3.0.0`)
- CI/CD에 `pip-audit` 통합 (의존성 취약점 자동 스캔)

> 상세 보안 리포트: `docs/02-design/security-spec.md`

## 향후 계획

- [x] Supabase 테이블/RPC 함수 생성 + 샘플 데이터 적재
- [x] Python 크롤링 스크립트 (쿠팡/네이버 자동 크롤링)
- [x] 데이터 시각화 (matplotlib/seaborn 15종 차트)
- [x] ML 매출 예측 (Random Forest, Feature Engineering, R²=0.74)
- [x] 주간/월간 요약 리포트 (Supabase RPC + Pandas + WoW/MoM 분석)
- [x] n8n에서 Python 크롤링 스크립트 연동 (Execute Command 노드)
- [x] 비즈니스 인사이트 분석 (채널 믹스, 경쟁사 상관, 요일 패턴, 액션 추천)
- [x] A/B 테스트 통계 분석 파이프라인 (실험 설계 → 가설 검정 → Go/No-Go)
- [x] 경쟁사 8주 장기 추이 데이터 (가격 할인/복원 패턴 반영)
- [x] 보안 점검 (OWASP Top 10 기준, SQL Injection/XSS/시크릿 관리)
- [x] 검색 트렌드-매출 상관 분석 (Google Trends + Naver DataLab, Pearson/Spearman, 선행 지표, 성수기 탐지)
- [x] 광고 퍼포먼스 분석 (ROAS 효율 등급 + 예산 재배분 시뮬레이션 + 성장 기회 탐지)
- [x] 인사이트 스토리텔링 강화 (발견→근거→제안→효과 4단계 구조)
- [ ] Supabase RLS 정책 활성화
- [ ] Tableau/Looker Studio 대시보드 연동

## 라이선스

이 프로젝트는 포트폴리오 목적으로 제작되었습니다.

---

**Built for 앳홈 automated business intelligence**
