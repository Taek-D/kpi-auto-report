# Changelog - 앳홈 KPI Auto Report v2

All notable changes to this project are documented here.

---

## [2026-02-13] - Crawlers Feature Complete

### Added
- **crawlers/ package** (843 LOC, 6 modules)
  - `config.py` - CRAWL_TARGETS (4 categories × 2 sources), BRAND_MAPPING, configurable constants
  - `coupang_crawler.py` - HTML scraper with BeautifulSoup (128 lines)
  - `naver_crawler.py` - Official Shopping API client (110 lines)
  - `supabase_loader.py` - REST API batch upsert (85 lines)
  - `analyzer.py` - Pandas analysis + 4 matplotlib/seaborn charts (315 lines)
  - `main.py` - CLI with argparse (130 lines)
  - `__init__.py` - Package marker
- **requirements.txt** - 6 production dependencies (requests, beautifulsoup4, pandas, matplotlib, seaborn, python-dotenv)
- **Documentation**
  - Gap analysis: `docs/03-analysis/crawlers.analysis.md` (99% match rate)
  - Completion report: `docs/04-report/crawlers.report.md`

### Features
- Crawl 4 product categories across Coupang (HTML scrape) and Naver Shopping (official API)
- Extract 9 data fields per product: crawl_date, source, category, product_name, brand, price, ranking, review_count, avg_rating
- Supabase REST API integration with batch upsert (10 per batch)
- Pandas-based Week-over-Week (WoW) analysis
- 4 visualization types:
  1. Price Trend (line chart)
  2. Ranking Comparison (horizontal bar)
  3. Review Growth (grouped bar)
  4. Competitor Dashboard (2×2 subplot: price distribution, rating, reviews, scatter)
- CLI with flexible execution modes: `--all`, `--crawl`, `--analyze`, `--source {coupang|naver}`
- Rate limiting (2-4s delays), User-Agent rotation (5 agents), 3-retry logic
- Korean font detection with fallback (Malgun Gothic, NanumGothic, AppleGothic, DejaVu Sans)

### Technical Details
- 88 functional requirements verified (100% pass rate)
- 1 minor style issue (import order in naver_crawler.py:17)
- Error handling at 4 levels: request, item, batch, pipeline
- Logging with timestamps and severity levels
- Configurable via config.py (no hardcoded values)

### Architecture
```
crawlers/ → config.py → [Coupang/Naver] → SupabaseLoader → CompetitorAnalyzer → output/
```

### JD Skills Demonstrated
- Python (843 LOC, 6 modules, OOP)
- Web scraping (requests + BeautifulSoup with HTML parsing)
- REST API integration (Naver Shopping + Supabase)
- Data processing (Pandas DataFrames, type conversion, WoW analysis)
- Data visualization (matplotlib + seaborn, 4 chart types, Korean typography)
- Error handling (retry logic, per-item error tracking, graceful degradation)
- CLI design (argparse, flexible modes, helpful usage)
- Database integration (PostgreSQL schema understanding, upsert operations, batch processing)

---

## Project Milestones

| Date | Feature | Status |
|------|---------|--------|
| 2026-02-13 | crawlers (competitor monitoring) | ✅ COMPLETED |
| TBD | n8n workflow integration | 📋 Planned |
| TBD | Slack daily reports | 📋 Planned |
| TBD | Web dashboard | 📋 Planned |

---

## PDCA Cycle Status

### Completed Cycles
- **crawlers**: Plan ✅ → Design ✅ → Do ✅ → Check ✅ → Act ✅

### Current Focus
- Integration with n8n daily scheduling

---

*Last updated: 2026-02-13*
