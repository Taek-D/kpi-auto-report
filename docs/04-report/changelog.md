# Changelog - 앳홈 KPI Auto Report v2

All notable changes to this project are documented here.

---

## [2026-02-15] - Ad Performance Analysis + Storytelling Enhancement Complete

### Added
- **ad_performance_analyzer.py** - New ad performance analysis module
  - Channel-wise ROAS/CPC/ROI efficiency analysis with S/A/B/C grades
  - Budget reallocation simulation (ROAS-weighted proportional, min 10% constraint)
  - Growth opportunity detection (4-quadrant matrix: scale-up/maintain/improve/reduce)
  - 3 visualization charts:
    1. `ad_roas_comparison.png` - Horizontal bar chart with grade color coding
    2. `ad_budget_simulation.png` - Current vs optimal budget grouped bar chart
    3. `ad_opportunity_matrix.png` - Scatter plot with 4 quadrants labeled
- **Dashboard ad performance section** (7th section)
  - ROAS efficiency table with channel breakdown
  - Growth opportunity signal cards
  - Integrated with trend analysis for seasonal budget recommendations

### Changed
- **dashboard_generator.py** - Storytelling enhancement
  - `_build_actions()` completely rewritten with 4-step structure
  - [발견] Discovery → [근거] Evidence → [제안] Recommendation → [효과] Expected Impact
  - Connected trend analysis (peak season) with ad budget recommendations
  - Added `_build_ad_performance_section()` method
  - Updated `_assemble_html()` to 7 sections (was 6)
- **main.py** - CLI integration
  - Added `--ad-perf` flag for ad performance analysis
  - Added `ad_perf()` function with lazy import
  - Updated docstring and help text
- **README.md** - Documentation updates
  - Added "광고 퍼포먼스 분석" section (L521-550)
  - Updated chart count: 15 → 18 visualization types
  - Updated dashboard sections: 6 → 7
  - Added CLI usage example for `--ad-perf`
  - Updated tech stack with "Ad Analytics" (Pandas + numpy)
- **CLAUDE.md** - Project reference updates
  - Updated Key Files list with `ad_performance_analyzer.py`
  - Updated dashboard description to mention 7 sections + storytelling
  - Added `--ad-perf` to CLI Commands
  - Enhanced Analysis Capabilities section with ad analysis + storytelling
  - Updated visualization count to 18 charts

### Fixed
- Gap Analysis G-1: Incorporated conversion_rate into growth opportunity text output
- Initial match rate: 98% → 100% (all 58 requirements met)

### Metrics
- **PDCA Completion**: Plan → Design → Do → Check → Act
- **Design Match Rate**: 98% → 100%
- **Code Quality**: 95% convention compliance (2 minor duplications noted)
- **Architecture Compliance**: 100% (modular, integrates with existing analyzers)
- **Total Lines of Code**: ad_performance_analyzer.py (~500 lines)

### JD Skills Demonstrated
- Advanced data analysis (efficiency grading, weighted reallocation algorithm)
- Matplotlib visualization (4-quadrant scatter plot with grade color mapping)
- Business intelligence (ROAS analysis, budget optimization simulation)
- Storytelling framework (data-driven narrative structure with evidence + recommendations)
- Full-stack feature integration (analyzer → CLI → dashboard)

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
| 2026-02-15 | ad-perf (광고 분석 + 스토리텔링) | ✅ COMPLETED |
| 2026-02-13 | crawlers (competitor monitoring) | ✅ COMPLETED |
| TBD | n8n workflow integration | 📋 Planned |
| TBD | Slack daily reports | 📋 Planned |
| TBD | Web dashboard | 📋 Planned |

---

## PDCA Cycle Status

### Completed Cycles
- **ad-perf** (2026-02-15): Plan ✅ → Design ✅ → Do ✅ → Check ✅ → Act ✅ (Match Rate: 100%, 58/58 requirements)
- **crawlers** (2026-02-13): Plan ✅ → Design ✅ → Do ✅ → Check ✅ → Act ✅

### Current Focus
- Integration with n8n daily scheduling
- Shared utility module extraction (chart_utils.py refactoring)

---

*Last updated: 2026-02-15*
