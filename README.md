# 앳홈 KPI Daily Auto-Report System

> **매일 아침, 앳홈 3개 브랜드의 KPI 리포트가 Slack으로 자동 도착합니다.**

앳홈(미닉스/톰/프로티원) 브랜드별 매출을 수집하고, WoW 분석 + 이상 탐지 + 경쟁사 모니터링을 수행한 뒤 Slack으로 전송하는 자동화 파이프라인입니다. Python 크롤링 + Pandas 분석 + scikit-learn 매출 예측 + 시각화까지 포함한 풀스택 데이터 프로젝트입니다.

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
- **A/B 테스트 분석**: 실험 설계 검증 + 통계 검정(t-test, Mann-Whitney U) + ROI 해석
- **매출 예측 + 비즈니스 액션**: Ridge Regression 예측 → 재고/마케팅/채널 전략 + 리스크 평가
- **데이터 시각화**: matplotlib/seaborn 기반 11종 분석 차트 자동 생성
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
| ML | Python (scikit-learn) | Ridge Regression 매출 예측 |
| Statistics | Python (scipy) | A/B 테스트 통계 검정 (t-test, Mann-Whitney U) |
| Visualization | Python (matplotlib + seaborn) | 11종 분석 차트 자동 생성 |

## 프로젝트 구조

```
KPI_Auto_Report(Athome)/
├── requirements.txt            # Python 의존성
├── docker-compose.yml          # n8n Docker 컨테이너 설정
├── .env.example                # 환경변수 템플릿
├── KPI_Auto_Report_PRD.md      # 제품 요구사항 문서 (v2)
├── crawlers/                   # Python 경쟁사 크롤링 & 분석 & ML 패키지
│   ├── config.py               # 크롤링 대상 설정 (제품, 카테고리, 브랜드 매핑)
│   ├── coupang_crawler.py      # 쿠팡 검색 스크래핑 (requests + BeautifulSoup)
│   ├── naver_crawler.py        # 네이버 쇼핑 API 클라이언트
│   ├── supabase_loader.py      # Supabase REST API 데이터 적재 + RPC 호출
│   ├── analyzer.py             # Pandas 분석 + matplotlib/seaborn 시각화
│   ├── report_generator.py     # 주간/월간 요약 리포트 (Pandas + matplotlib)
│   ├── predictor.py            # ML 매출 예측 + 비즈니스 액션 플랜
│   ├── insight_analyzer.py     # 비즈니스 인사이트 (채널 믹스, 경쟁사 상관, 요일 패턴)
│   ├── ab_test_analyzer.py     # A/B 테스트 통계 분석 (scipy)
│   └── main.py                 # CLI 진입점 (argparse)
├── schema/                     # DB 스키마 DDL + 샘플 데이터 + RPC 함수
│   ├── brand_daily_sales.sql   # 브랜드x채널 일일 매출 + RPC 2개
│   ├── products.sql            # 제품 마스터 + 제품별 매출 + RPC 1개
│   ├── market_competitors.sql  # 경쟁사 크롤링 데이터 + RPC 1개
│   ├── competitor_extended.sql # 경쟁사 8주 확장 데이터 (장기 추이 분석)
│   ├── ab_test_sample.sql      # A/B 테스트 테이블 + 14일 샘플 데이터
│   ├── summary_functions.sql   # 주간/월간 요약 RPC 함수 2개
│   └── sample_30days.sql       # 30일 샘플 데이터 (ML 학습용)
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
│   ├── revenue_prediction.png  # 실제 vs 예측 + 향후 7일 예측
│   ├── brand_forecast.png      # 브랜드별 7일 예측 합계 bar chart
│   ├── channel_mix_trend.png   # 채널 비중 변화 stacked area chart
│   ├── weekday_heatmap.png     # 브랜드x요일 매출 히트맵
│   ├── ab_test_conversion.png  # A/B 전환율 비교 + 신뢰구간
│   └── ab_test_daily.png       # A/B 일별 전환율 추이
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

# ML 매출 예측 + 비즈니스 액션 플랜
python -m crawlers.main --predict

# 비즈니스 인사이트 분석 (채널 믹스, 경쟁사 상관, 요일 패턴)
python -m crawlers.main --insight

# A/B 테스트 분석 (통계 검정 + ROI + Go/No-Go 판정)
python -m crawlers.main --abtest
```

### 크롤링 대상

| 카테고리 | 소스 | 수집 항목 |
|---------|------|----------|
| 음식물처리기 | 쿠팡, 네이버 | 순위, 가격, 리뷰 수, 평점 |
| 식기세척기 | 쿠팡, 네이버 | 순위, 가격, 리뷰 수, 평점 |
| 소형건조기 | 쿠팡, 네이버 | 순위, 가격, 리뷰 수, 평점 |
| 뷰티디바이스 | 쿠팡, 네이버 | 순위, 가격, 리뷰 수, 평점 |

### 시각화 차트 (11종)

| 구분 | 차트 | 파일명 | 설명 |
|------|------|--------|------|
| 경쟁사 | 가격 추이 | `price_trend.png` | 경쟁사별 가격 변동 라인 차트 |
| 경쟁사 | 순위 비교 | `ranking_comparison.png` | 자사 vs 경쟁사 순위 (수평 바) |
| 경쟁사 | 리뷰 성장 | `review_growth.png` | 주간 리뷰 증가량 (그룹 바) |
| 경쟁사 | 종합 대시보드 | `competitor_dashboard.png` | 2x2 서브플롯 전체 요약 |
| 리포트 | 월간 리포트 | `monthly_report.png` | 브랜드별 월간 매출 bar chart |
| ML | 매출 예측 | `revenue_prediction.png` | 실제 vs 예측 + 향후 7일 (±15% 범위) |
| ML | 예측 합계 | `brand_forecast.png` | 브랜드별 7일 예측 매출 합계 bar chart |
| 인사이트 | 채널 믹스 | `channel_mix_trend.png` | 브랜드별 채널 비중 stacked area chart |
| 인사이트 | 요일 히트맵 | `weekday_heatmap.png` | 브랜드x요일 평균 매출 히트맵 |
| A/B 테스트 | 전환율 비교 | `ab_test_conversion.png` | A/B 전환율 + 95% 신뢰구간 bar chart |
| A/B 테스트 | 일별 추이 | `ab_test_daily.png` | A vs B 일별 전환율 라인 차트 |

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

### RPC 함수 (6개)

| 함수 | 용도 | 반환 |
|------|------|------|
| `get_brand_kpis_yesterday()` | 어제 브랜드별 KPI | 매출, 주문, ROAS, 채널 breakdown |
| `get_brand_kpis_last_week()` | 지난주 동일 요일 KPI | WoW 비교용 |
| `get_top_products()` | 매출 상위 5개 제품 | 제품명, 매출, 평점 |
| `get_competitor_changes()` | 경쟁사 순위/가격 변동 | 전주 대비 변동 |
| `get_weekly_summary(p_end_date)` | 주간 브랜드별 집계 | WoW%, 채널 비중 JSONB |
| `get_monthly_summary(p_year, p_month)` | 월간 브랜드별 집계 | MoM%, 채널 비중 JSONB |

## 매출 예측 + 비즈니스 액션 (ML)

scikit-learn Ridge Regression으로 브랜드별 매출을 예측하고, **예측 결과를 비즈니스 의사결정으로 연결**합니다.

### Feature Engineering

| Feature | 설명 |
|---------|------|
| `day_of_week` | 요일 (0=월 ~ 6=일) |
| `is_weekend` | 주말 여부 (0/1) |
| `revenue_ma7` | 7일 이동평균 매출 |
| `revenue_lag7` | 전주 동일 요일 매출 |

### 파이프라인

```
Supabase (30일) → Feature Engineering → Ridge Regression (α=1.0)
→ 7일 예측 → 비즈니스 액션 플랜 + 리스크 평가 → 시각화 2종
```

### 출력 예시

```
🎯 비즈니스 액션 플랜
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [미닉스]
  [재고] 다음 주 예상 주문 171건 → 안전재고 대비 26건 여유 확보
  [마케팅] 주말 매출 +25% 패턴 → 금/토 쿠팡 광고비 +30% 배분 권장
  [채널] 쿠팡 매출 비중 40%+ → 쿠팡 로켓배송 재고 우선 확보

⚠️ 리스크 평가
  [참고] 미닉스 R²=0.75 → 중간 정확도, ±15% 버퍼 운영 권장
  [주의] 톰 R²=0.43 → 예측 정확도 낮음, 보수적 재고 운영 (±20% 버퍼)
```

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

## A/B 테스트 분석

`--abtest` 옵션으로 미닉스 자사몰 결제 페이지 A/B 테스트를 분석합니다.

### 실험 설계

| 항목 | 내용 |
|------|------|
| 대상 | 미닉스 자사몰 결제 페이지 |
| 배경 | 전환율(0.87%)이 업계 평균(1.2%) 대비 낮음 |
| Control (A) | 기존 결제 페이지 |
| Treatment (B) | 개선 결제 페이지 (원클릭 결제 + 리뷰 위젯) |
| 기간 | 14일 (2주, 요일 효과 포함) |

### 통계 분석

| 검정 | 방법 | 용도 |
|------|------|------|
| 실험 설계 검증 | Power Analysis, SRM (chi-squared) | 샘플 충분성 + 배분 편향 체크 |
| 전환율 비교 | Welch's t-test | 두 그룹 평균 차이 (비등분산) |
| 매출 비교 | Mann-Whitney U test | 비정규 분포 대응 (단측) |
| 효과 크기 | Cohen's d | 실질적 의미 판단 |
| 신뢰구간 | 95% CI | 전환율 차이 범위 |

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
- scikit-learn Ridge Regression으로 시계열 매출 예측 (Feature Engineering + 모델 평가)
- scipy 통계 검정 (Welch's t-test, Mann-Whitney U, SRM chi-squared, Power Analysis)
- A/B 테스트 실험 설계 + 통계 분석 + 비즈니스 해석 파이프라인
- CLI 도구 설계 (argparse, 모듈별 실행, lazy import 패턴)
- Window Function을 jsonb_agg() 안에서 직접 사용 불가 → 서브쿼리 패턴 학습

### 비즈니스
- 멀티브랜드 KPI 모니터링 체계 설계
- 채널 믹스 변동 분석으로 채널 전략 의사결정 지원
- 경쟁사 가격 변동과 자사 매출 상관 분석 (8주 크로스 체크)
- 요일별 매출 패턴 분석 → 프로모션 타이밍 최적화
- A/B 테스트로 자사몰 전환율 +22.6% 개선 검증, ROI 15,591% → Go 판정
- ML 예측 → 재고 계획, 마케팅 예산 배분, 채널별 전략 수립
- 분석 결과를 구체적 액션 아이템(광고비 증액, 딜 등록, 리타게팅)으로 변환

## 향후 계획

- [x] Supabase 테이블/RPC 함수 생성 + 샘플 데이터 적재
- [x] Python 크롤링 스크립트 (쿠팡/네이버 자동 크롤링)
- [x] 데이터 시각화 (matplotlib/seaborn 11종 차트)
- [x] 주간/월간 요약 리포트 (Supabase RPC + Pandas + WoW/MoM 분석)
- [x] n8n에서 Python 크롤링 스크립트 연동 (Execute Command 노드)
- [x] 매출 예측 + 비즈니스 액션 (Ridge Regression → 재고/마케팅/채널 전략)
- [x] 비즈니스 인사이트 분석 (채널 믹스, 경쟁사 상관, 요일 패턴, 액션 추천)
- [x] A/B 테스트 분석 (실험 설계 검증 + 통계 검정 + ROI + Go/No-Go)
- [x] 경쟁사 8주 장기 추이 데이터 (가격 할인/복원 패턴 반영)
- [ ] Tableau/Looker Studio 대시보드 연동

## 라이선스

이 프로젝트는 포트폴리오 목적으로 제작되었습니다.

---

**Built for 앳홈 automated business intelligence**
