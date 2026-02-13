# 앳홈 KPI Daily Auto-Report System

> **매일 아침, 앳홈 3개 브랜드의 KPI 리포트가 Slack으로 자동 도착합니다.**

앳홈(미닉스/톰/프로티원) 브랜드별 매출을 수집하고, WoW 분석 + 이상 탐지 + 경쟁사 모니터링을 수행한 뒤 Slack으로 전송하는 자동화 파이프라인입니다. Python 크롤링 + Pandas 분석 + 시각화까지 포함한 풀스택 데이터 프로젝트입니다.

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
- **경쟁사 모니터링**: 쿠팡/네이버 순위 변동, 가격 변동 알림
- **경쟁사 크롤링**: Python으로 쿠팡(BeautifulSoup) + 네이버 쇼핑(API) 자동 수집
- **데이터 시각화**: matplotlib/seaborn 기반 4종 분석 차트 자동 생성

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
| Visualization | Python (matplotlib + seaborn) | 4종 분석 차트 자동 생성 |

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
│   ├── supabase_loader.py      # Supabase REST API 데이터 적재 (upsert)
│   ├── analyzer.py             # Pandas 분석 + matplotlib/seaborn 시각화
│   └── main.py                 # CLI 진입점 (argparse)
├── schema/                     # DB 스키마 DDL + 샘플 데이터 + RPC 함수
│   ├── brand_daily_sales.sql   # 브랜드x채널 일일 매출 + RPC 2개
│   ├── products.sql            # 제품 마스터 + 제품별 매출 + RPC 1개
│   └── market_competitors.sql  # 경쟁사 크롤링 데이터 + RPC 1개
├── queries/                    # SQL 쿼리 원본 (학습/문서용)
│   ├── brand_kpis_yesterday.sql # 브랜드별 어제 KPI + 채널 비중
│   ├── brand_kpis_last_week.sql # 지난주 동일 요일 브랜드별 KPI
│   ├── top_products_by_brand.sql# 브랜드별 상위 제품 (이중 RANK)
│   ├── channel_performance.sql  # 채널별 매출/ROAS/전환율 WoW
│   └── competitor_changes.sql   # 경쟁사 순위/가격 변동 감지
├── n8n/                        # n8n 워크플로우
│   ├── workflow.json           # 8노드 워크플로우 정의
│   ├── transform.js            # 브랜드별 WoW + 이상 탐지 + 경쟁사
│   └── slack_send.js           # Slack Webhook 전송
├── output/                     # 시각화 차트 출력 디렉토리
│   ├── price_trend.png         # 경쟁사 가격 추이
│   ├── ranking_comparison.png  # 검색 순위 비교
│   ├── review_growth.png       # 주간 리뷰 증가량
│   └── competitor_dashboard.png# 종합 대시보드 (2x2)
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
SELECT * FROM get_brand_kpis_yesterday();
SELECT * FROM get_brand_kpis_last_week();
SELECT * FROM get_top_products();
SELECT * FROM get_competitor_changes();
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
```

### 크롤링 대상

| 카테고리 | 소스 | 수집 항목 |
|---------|------|----------|
| 음식물처리기 | 쿠팡, 네이버 | 순위, 가격, 리뷰 수, 평점 |
| 식기세척기 | 쿠팡, 네이버 | 순위, 가격, 리뷰 수, 평점 |
| 소형건조기 | 쿠팡, 네이버 | 순위, 가격, 리뷰 수, 평점 |
| 뷰티디바이스 | 쿠팡, 네이버 | 순위, 가격, 리뷰 수, 평점 |

### 시각화 차트 (4종)

| 차트 | 파일명 | 설명 |
|------|--------|------|
| 가격 추이 | `output/price_trend.png` | 경쟁사별 가격 변동 라인 차트 |
| 순위 비교 | `output/ranking_comparison.png` | 자사 vs 경쟁사 순위 (수평 바) |
| 리뷰 성장 | `output/review_growth.png` | 주간 리뷰 증가량 (그룹 바) |
| 종합 대시보드 | `output/competitor_dashboard.png` | 2x2 서브플롯 전체 요약 |

> 차트에서 주황색 = 앳홈 브랜드, 파란색 = 경쟁사로 구분됩니다.

### 크롤링 기술 세부사항

- **쿠팡**: requests + BeautifulSoup4, User-Agent 로테이션(5종), 2~4초 랜덤 딜레이, 3회 재시도
- **네이버**: 공식 쇼핑 검색 API (`openapi.naver.com`), Client ID/Secret 인증
- **적재**: Supabase REST API upsert (`Prefer: resolution=merge-duplicates`), 10건씩 배치 처리
- **분석**: Pandas DataFrame 변환, WoW 비교, matplotlib/seaborn 한글 폰트 지원

## 이상 탐지 기준

| 브랜드 | 매출 Critical | 주문 Warning | 비고 |
|--------|-------------|-------------|------|
| 미닉스 | WoW -20% | WoW -15% | 기본 |
| 톰 | WoW -30% | WoW -25% | GS홈쇼핑 방송일 변동 감안 |
| 프로티원 | WoW -20% | WoW -15% | 기본 |

## SQL 주요 기법

- **Window Functions**: RANK() OVER (PARTITION BY brand), SUM() OVER (PARTITION BY), LAG()
- **CTE (WITH절)**: 복잡한 쿼리를 브랜드별 집계 > 전체 합계 > UNION으로 분해
- **JSONB**: 채널별 매출 breakdown을 JSON 배열로 반환
- **Self-JOIN**: 경쟁사 전주 대비 순위/가격 변동 비교
- **복합 인덱스**: (sale_date, brand), (sale_date, channel)

## 경쟁사 모니터링

| 카테고리 | 앳홈 제품 | 경쟁사 |
|---------|---------|--------|
| 음식물처리기 | 미닉스 음식물처리기 | 스마트카라, 린클 |
| 뷰티디바이스 | 톰 더글로우 프로 | LG 프라엘, 페이스팩토리 |

## 배운 점

### 기술적
- n8n 8노드 워크플로우 설계 (4개 병렬 HTTP Request)
- Supabase RPC + JSONB 반환 (채널별 breakdown)
- SQL Window Functions 실전 활용 (이중 RANK, PARTITION BY)
- 브랜드별 차등 이상 탐지 임계값 설계
- 경쟁사 크롤링 데이터 모델링 (Self-JOIN 비교)
- Python 크롤링 파이프라인 (requests + BeautifulSoup + rate limiting)
- Pandas 데이터 전처리 + matplotlib/seaborn 시각화 (한글 폰트 처리)
- CLI 도구 설계 (argparse, 모듈별 실행)

### 비즈니스
- 멀티브랜드 KPI 모니터링 체계 설계
- 채널별 매출 비중 분석으로 마케팅 의사결정 지원
- 경쟁사 순위/가격 변동 자동 알림으로 빠른 대응
- 시각화 차트를 통한 경쟁사 동향 직관적 파악

## 향후 계획

- [x] Supabase 테이블/RPC 함수 생성 + 샘플 데이터 적재
- [x] Python 크롤링 스크립트 (쿠팡/네이버 자동 크롤링)
- [x] 데이터 시각화 (matplotlib/seaborn 4종 차트)
- [ ] 주간/월간 요약 리포트 추가
- [ ] n8n에서 Python 크롤링 스크립트 연동 (Execute Command 노드)
- [ ] Tableau/Looker Studio 대시보드 연동
- [ ] 예측 분석 (ML 기반 트렌드 예측)

## 라이선스

이 프로젝트는 포트폴리오 목적으로 제작되었습니다.

---

**Built for 앳홈 automated business intelligence**
