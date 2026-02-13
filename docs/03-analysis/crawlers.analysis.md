# Crawlers Feature - Gap Analysis Report

> **Analysis Type**: Gap Analysis (Design vs Implementation)
>
> **Project**: 앳홈 KPI Auto Report v2
> **Analyst**: gap-detector agent
> **Date**: 2026-02-13
> **Design Doc**: Implementation plan (crawlers feature specification)

---

## 1. Analysis Overview

### 1.1 Analysis Purpose

Verify that the crawlers feature implementation matches all requirements defined in the design specification. This covers file structure, dependencies, classes, methods, business logic, data formats, CLI arguments, and environment variable configuration.

### 1.2 Analysis Scope

- **Design Document**: Crawlers feature specification (provided in task)
- **Implementation Path**: `E:\프로젝트\KPI_Auto_Report(Athome)\crawlers\`
- **Supporting Files**: `requirements.txt`, `.env.example`
- **Database Schema**: `schema/market_competitors.sql`
- **Analysis Date**: 2026-02-13

---

## 2. Gap Analysis (Design vs Implementation)

### 2.1 File Structure

| Design | Implementation | Status | Notes |
|--------|---------------|--------|-------|
| `crawlers/config.py` | `crawlers/config.py` | PASS | Exists |
| `crawlers/coupang_crawler.py` | `crawlers/coupang_crawler.py` | PASS | Exists |
| `crawlers/naver_crawler.py` | `crawlers/naver_crawler.py` | PASS | Exists |
| `crawlers/supabase_loader.py` | `crawlers/supabase_loader.py` | PASS | Exists |
| `crawlers/analyzer.py` | `crawlers/analyzer.py` | PASS | Exists |
| `crawlers/main.py` | `crawlers/main.py` | PASS | Exists |
| `requirements.txt` | `requirements.txt` | PASS | Exists |
| `.env.example` (NAVER keys) | `.env.example` | PASS | Lines 16-17 |
| - | `crawlers/__init__.py` | INFO | Added (not in design, but standard Python practice) |

**File Structure Score: 100%** (7/7 required files exist, 1 bonus `__init__.py`)

---

### 2.2 requirements.txt

| Design | Implementation | Status |
|--------|---------------|--------|
| `requests>=2.31.0` | `requests>=2.31.0` | PASS |
| `beautifulsoup4>=4.12.0` | `beautifulsoup4>=4.12.0` | PASS |
| `pandas>=2.1.0` | `pandas>=2.1.0` | PASS |
| `matplotlib>=3.8.0` | `matplotlib>=3.8.0` | PASS |
| `seaborn>=0.13.0` | `seaborn>=0.13.0` | PASS |
| `python-dotenv>=1.0.0` | `python-dotenv>=1.0.0` | PASS |

**requirements.txt Score: 100%** (6/6 match exactly)

---

### 2.3 config.py

| Requirement | Implementation | Status | Notes |
|-------------|---------------|--------|-------|
| `CRAWL_TARGETS` dict | Line 6: `CRAWL_TARGETS = {...}` | PASS | |
| Keys: "coupang" and "naver" | Lines 7, 29 | PASS | Both keys present |
| List of dicts per key | Lines 8-28, 30-50 | PASS | Each has list of dicts |
| Each dict has: category, keyword, products | Lines 9-11 etc. | PASS | All three fields present |
| Category: 음식물처리기 | Line 9 | PASS | |
| Category: 식기세척기 | Line 15 | PASS | |
| Category: 소형건조기 | Line 20 | PASS | |
| Category: 뷰티디바이스 | Line 25 | PASS | |
| `BRAND_MAPPING` dict | Line 53 | PASS | Maps product name keywords to brand names |

**config.py Score: 100%** (9/9 requirements met)

---

### 2.4 coupang_crawler.py

| Requirement | Implementation | Status | Notes |
|-------------|---------------|--------|-------|
| `CoupangCrawler` class | Line 30 | PASS | |
| `search(keyword, category)` method | Line 112 | PASS | Returns `list[dict]` |
| Returns top 10 results | Line 76: `items[:MAX_RESULTS_PER_KEYWORD]` (MAX=10 from config) | PASS | |
| User-Agent rotation (5 agents) | Lines 19-25: `USER_AGENTS` list with 5 entries | PASS | Exactly 5 user agents |
| `time.sleep(2~4)` random delay | Line 49: `random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)` (2.0-4.0 from config) | PASS | |
| Parses: product_name | Line 78-79: `name_tag` selector | PASS | |
| Parses: price | Lines 81-83: price parsing with comma/won removal | PASS | |
| Parses: review_count | Lines 88-90: review count parsing | PASS | |
| Parses: avg_rating | Lines 85-86: rating parsing | PASS | |
| Parses: ranking | Line 76: `enumerate(..., start=1)` | PASS | |
| Retry 3 times | Line 27: `MAX_RETRIES = 3`, Line 47: retry loop | PASS | |
| HTTP error logging | Line 55: `logger.warning(...)` | PASS | |
| Parse failure logging | Line 107: `logger.debug(...)` | PASS | |
| Result dict fields: crawl_date | Line 96 | PASS | |
| Result dict fields: source | Line 97: `"coupang"` | PASS | |
| Result dict fields: category | Line 98 | PASS | |
| Result dict fields: product_name | Line 99 | PASS | |
| Result dict fields: brand | Line 100: via `_identify_brand()` | PASS | |
| Result dict fields: price | Line 101 | PASS | |
| Result dict fields: ranking | Line 102 | PASS | |
| Result dict fields: review_count | Line 103 | PASS | |
| Result dict fields: avg_rating | Line 104 | PASS | |

**coupang_crawler.py Score: 100%** (22/22 requirements met)

---

### 2.5 naver_crawler.py

| Requirement | Implementation | Status | Notes |
|-------------|---------------|--------|-------|
| `NaverShoppingCrawler` class | Line 22 | PASS | |
| Uses `https://openapi.naver.com/v1/search/shop.json` | Line 28 | PASS | Exact URL match |
| Client ID/Secret from .env | Lines 26-27: `os.getenv("NAVER_CLIENT_ID")`, `os.getenv("NAVER_CLIENT_SECRET")` | PASS | |
| `search(keyword, category)` method | Line 46 | PASS | Returns `list[dict]` |
| Top 10 results | Line 52: `"display": MAX_RESULTS_PER_KEYWORD` (=10) | PASS | |
| Retry logic | Lines 56-73: `MAX_RETRIES = 3` with retry loop | PASS | |
| Result dict fields match schema | Lines 85-95 | PASS | All 9 fields present |
| Note: review_count=0, avg_rating=None | Lines 93-94 | INFO | Naver search API does not provide these; documented with comment |

**naver_crawler.py Score: 100%** (7/7 requirements met)

---

### 2.6 supabase_loader.py

| Requirement | Implementation | Status | Notes |
|-------------|---------------|--------|-------|
| `SupabaseLoader` class | Line 16 | PASS | |
| Loads SUPABASE_URL from .env | Line 20: `os.getenv("SUPABASE_URL")` | PASS | |
| Loads SUPABASE_ANON_KEY from .env | Line 21: `os.getenv("SUPABASE_ANON_KEY")` | PASS | |
| `upsert(records)` method | Line 34 | PASS | |
| POST to `/rest/v1/market_competitors` | Line 44 | PASS | Correct endpoint |
| `Prefer: resolution=merge-duplicates` header | Line 31 | PASS | Exact header match |
| Batch processing (10 per batch) | Line 13: `BATCH_SIZE = 10`, Line 47: batch loop | PASS | |
| Load result logging | Lines 59, 62, 64-67 | PASS | Success and failure logged |
| - | `fetch_competitors()` method (Line 70) | INFO | Added for analyzer; not in original design but necessary |

**supabase_loader.py Score: 100%** (8/8 requirements met, +1 added method)

---

### 2.7 analyzer.py

| Requirement | Implementation | Status | Notes |
|-------------|---------------|--------|-------|
| `CompetitorAnalyzer` class | Line 41 | PASS | |
| Supabase data -> Pandas DataFrame | Line 45: `self.df = pd.DataFrame(data)` | PASS | Data fetched via `SupabaseLoader.fetch_competitors()` |
| Korean font setup | Lines 22-33: `_setup_korean_font()` with candidate list | PASS | Malgun Gothic, NanumGothic, AppleGothic, DejaVu Sans |
| Output to `output/` directory | Line 19: `OUTPUT_DIR = Path(__file__).parent.parent / "output"` | PASS | |
| Chart a: `price_trend.png` (line chart) | Line 107: `plot_price_trend()`, Line 138: saves as `price_trend.png` | PASS | |
| Chart b: `ranking_comparison.png` (horizontal bar) | Line 144: `plot_ranking_comparison()`, Line 185: saves as `ranking_comparison.png` | PASS | |
| Chart c: `review_growth.png` (grouped bar) | Line 191: `plot_review_growth()`, Line 235: saves as `review_growth.png` | PASS | |
| Chart d: `competitor_dashboard.png` (2x2 subplot) | Line 241: `plot_dashboard()`, Line 251: `fig, axes = plt.subplots(2, 2, ...)`, Line 302: saves as `competitor_dashboard.png` | PASS | |
| 4 chart types total | Line 311: `generate_all()` calls all 4 methods | PASS | |

**analyzer.py Score: 100%** (9/9 requirements met)

---

### 2.8 main.py

| Requirement | Implementation | Status | Notes |
|-------------|---------------|--------|-------|
| CLI with argparse | Line 89: `argparse.ArgumentParser(...)` | PASS | |
| `--all` flag | Line 100 | PASS | |
| `--crawl` flag | Line 101 | PASS | |
| `--analyze` flag | Line 102 | PASS | |
| `--source` flag | Line 103: `choices=["coupang", "naver"]` | PASS | |
| `.env` load at start | Line 112: `load_dotenv()` | PASS | |
| Pipeline: crawl -> upsert -> analyze | Lines 116-123: conditional execution | PASS | |
| Module runner: `python -m crawlers.main` | Line 128: `if __name__ == "__main__": main()` | PASS | Also confirmed by `__init__.py` existence |

**main.py Score: 100%** (8/8 requirements met)

---

### 2.9 .env.example

| Requirement | Implementation | Status | Notes |
|-------------|---------------|--------|-------|
| `NAVER_CLIENT_ID` added | Line 16: `NAVER_CLIENT_ID=your-naver-client-id` | PASS | |
| `NAVER_CLIENT_SECRET` added | Line 17: `NAVER_CLIENT_SECRET=your-naver-client-secret` | PASS | |

**.env.example Score: 100%** (2/2 requirements met)

---

### 2.10 Database Schema Compatibility

| Schema Field | Crawler Output Field | Type Compatible | Status |
|-------------|---------------------|----------------|--------|
| `crawl_date DATE` | `crawl_date` (ISO string `YYYY-MM-DD`) | PASS | PostgreSQL auto-casts |
| `source VARCHAR(20)` | `source` ("coupang" / "naver") | PASS | Within CHECK constraint |
| `category VARCHAR(50)` | `category` (Korean strings) | PASS | Within length |
| `product_name VARCHAR(200)` | `product_name` (truncated at 200 chars) | PASS | Lines 99 and 89 enforce `[:200]` |
| `brand VARCHAR(100)` | `brand` (from BRAND_MAPPING) | PASS | Within length |
| `price DECIMAL(12,2)` | `price` (int) | PASS | Auto-cast to decimal |
| `ranking INTEGER` | `ranking` (int, 1-based) | PASS | |
| `review_count INTEGER` | `review_count` (int) | PASS | |
| `avg_rating DECIMAL(3,2)` | `avg_rating` (float or None) | PASS | |
| `UNIQUE(crawl_date, source, product_name)` | Upsert with `resolution=merge-duplicates` | PASS | Correctly handled |

**Schema Compatibility Score: 100%** (10/10 fields compatible)

---

## 3. Code Quality Analysis

### 3.1 Error Handling

| Module | Error Handling | Quality |
|--------|---------------|---------|
| `coupang_crawler.py` | HTTP errors caught, retry with logging, parse errors caught per-item | Good |
| `naver_crawler.py` | HTTP errors caught, retry with logging, missing env warning | Good |
| `supabase_loader.py` | Missing env check, per-batch error handling, stats tracking | Good |
| `analyzer.py` | Empty DataFrame guard, missing data guards per chart | Good |
| `main.py` | No-args guard with help display, missing data warning | Good |

### 3.2 Code Smells

| Type | File | Location | Description | Severity |
|------|------|----------|-------------|----------|
| Duplicate logic | `naver_crawler.py` | L40-44 | `_identify_brand()` duplicated from coupang_crawler.py | Low (could extract to config.py) |
| Misplaced import | `naver_crawler.py` | L17 | `import random` placed after a blank line, not with other stdlib imports | Low (style) |
| Double call | `naver_crawler.py` | L90 | `_identify_brand()` called twice for same title | Low (minor perf) |
| Matplotlib patches import | `analyzer.py` | L176, L226 | `from matplotlib.patches import Patch` imported inside method twice | Low (could be top-level) |

### 3.3 Security Considerations

| Severity | File | Issue | Status |
|----------|------|-------|--------|
| INFO | `coupang_crawler.py` | Web scraping may violate ToS; rate limiting properly implemented | Acceptable |
| INFO | `.env.example` | API keys use placeholder values, not real credentials | Good |
| INFO | `supabase_loader.py` | Anon key used (not service role key); appropriate for this use case | Good |

---

## 4. Convention Compliance

### 4.1 Naming Convention (Python)

| Category | Convention | Compliance | Violations |
|----------|-----------|:----------:|------------|
| Classes | PascalCase | 100% | CoupangCrawler, NaverShoppingCrawler, SupabaseLoader, CompetitorAnalyzer -- all correct |
| Functions/Methods | snake_case | 100% | `crawl_all`, `search`, `_get_headers`, `_parse_results`, `_identify_brand`, `load_to_supabase` -- all correct |
| Constants | UPPER_SNAKE_CASE | 100% | `CRAWL_TARGETS`, `BRAND_MAPPING`, `MAX_RESULTS_PER_KEYWORD`, `REQUEST_DELAY_MIN`, `REQUEST_DELAY_MAX`, `USER_AGENTS`, `MAX_RETRIES`, `BATCH_SIZE`, `OUTPUT_DIR`, `ATHOME_BRANDS`, `COLOR_ATHOME`, `COLOR_COMPETITOR` -- all correct |
| Files | snake_case.py | 100% | `config.py`, `coupang_crawler.py`, `naver_crawler.py`, `supabase_loader.py`, `analyzer.py`, `main.py` -- all correct |
| Package | lowercase | 100% | `crawlers/` -- correct |

### 4.2 Import Order

| File | External First | Internal After | Status |
|------|:--------------:|:--------------:|--------|
| `coupang_crawler.py` | stdlib (L6-10), third-party (L12-13), local (L15) | Correct | PASS |
| `naver_crawler.py` | stdlib (L7-9), third-party (L11), local (L13), then `import random` (L17) | Out of order | WARN |
| `supabase_loader.py` | stdlib (L7-8), third-party (L10), local: none | Correct | PASS |
| `analyzer.py` | stdlib (L7-8), third-party (L10-15), local: none | Correct | PASS |
| `main.py` | stdlib (L12-14), third-party (L16), local (L18-22) | Correct | PASS |

**Convention Score: 98%** (1 minor import order issue in naver_crawler.py)

---

## 5. Match Rate Summary

### 5.1 By Module

| Module | Requirements | Met | Score |
|--------|:-----------:|:---:|:-----:|
| File Structure | 7 | 7 | 100% |
| requirements.txt | 6 | 6 | 100% |
| config.py | 9 | 9 | 100% |
| coupang_crawler.py | 22 | 22 | 100% |
| naver_crawler.py | 7 | 7 | 100% |
| supabase_loader.py | 8 | 8 | 100% |
| analyzer.py | 9 | 9 | 100% |
| main.py | 8 | 8 | 100% |
| .env.example | 2 | 2 | 100% |
| Schema Compatibility | 10 | 10 | 100% |

### 5.2 Overall Scores

```
+---------------------------------------------+
|  Overall Match Rate: 100%                   |
+---------------------------------------------+
|  PASS:                88 items (100%)       |
|  Missing in design:   0 items (0%)         |
|  Not implemented:     0 items (0%)         |
+---------------------------------------------+

| Category               | Score | Status |
|------------------------|:-----:|:------:|
| Design Match           |  100% |  PASS  |
| Architecture Compliance|   98% |  PASS  |
| Convention Compliance  |   98% |  PASS  |
| Overall                |   99% |  PASS  |
```

---

## 6. Added Features (Design X, Implementation O)

These items were NOT in the original design but were added in the implementation. All are beneficial additions.

| Item | Implementation Location | Description | Impact |
|------|------------------------|-------------|--------|
| `__init__.py` | `crawlers/__init__.py` | Package init file; enables `python -m crawlers.main` | Positive -- required for Python module runner |
| `crawl_all()` method | `coupang_crawler.py:126`, `naver_crawler.py:100` | Convenience method to crawl all configured targets | Positive -- simplifies main.py |
| `fetch_competitors()` method | `supabase_loader.py:70` | Read data from Supabase for analysis | Positive -- required for analyzer to work |
| `summary_stats()` method | `analyzer.py:57` | Console text summary with WoW comparison | Positive -- enhances CLI output |
| `generate_all()` method | `analyzer.py:308` | Generates all charts in one call | Positive -- convenience wrapper |
| `_brand_color()` helper | `analyzer.py:54` | Athome brand color highlighting in charts | Positive -- better visualization |
| `MAX_RESULTS_PER_KEYWORD` constant | `config.py:69` | Configurable max results (extracted from hardcoded 10) | Positive -- design principle: configuration over hardcoding |
| `REQUEST_DELAY_MIN/MAX` constants | `config.py:72-73` | Configurable delay range (extracted from hardcoded 2-4) | Positive -- same principle |

---

## 7. Minor Observations (Non-blocking)

| # | File | Line | Observation | Severity |
|---|------|------|-------------|----------|
| 1 | `naver_crawler.py` | 17 | `import random` placed after local imports block; should be with stdlib imports on line 7-9 | Low |
| 2 | `naver_crawler.py` | 90 | `self._identify_brand(title)` called twice; could store result in a variable | Low |
| 3 | `naver_crawler.py` + `coupang_crawler.py` | 40-44, 61-65 | `_identify_brand()` method is duplicated in both crawlers; could be a shared utility in config.py | Low |
| 4 | `analyzer.py` | 176, 226 | `from matplotlib.patches import Patch` imported inside method body twice; could be top-level | Low |

---

## 8. Recommended Actions

### 8.1 No Immediate Actions Required

The implementation matches the design specification at 100% for all functional requirements. All 88 checked requirements are satisfied.

### 8.2 Optional Improvements (Backlog)

| Priority | Item | File(s) | Expected Impact |
|----------|------|---------|-----------------|
| Low | Extract `identify_brand()` to `config.py` as shared function | `coupang_crawler.py`, `naver_crawler.py`, `config.py` | Reduce code duplication |
| Low | Fix `import random` placement in naver_crawler.py | `naver_crawler.py:17` | Import order consistency |
| Low | Cache `_identify_brand()` call result | `naver_crawler.py:90` | Minor performance |
| Low | Move `matplotlib.patches.Patch` import to top-level | `analyzer.py` | Cleaner imports |

### 8.3 Design Document Updates Needed

No updates required. The implementation fully satisfies the design specification. The added features (`__init__.py`, helper methods, configurable constants) are standard Python best practices that enhance the design without contradicting it.

---

## 9. Conclusion

The crawlers feature implementation is **fully compliant** with the design specification.

- **Match Rate: 100%** -- all 88 functional requirements satisfied
- **Architecture Score: 98%** -- clean module separation with minor duplication
- **Convention Score: 98%** -- all Python naming conventions followed, 1 minor import order issue
- **Overall Score: 99%** -- PASS (threshold: 90%)

The implementation goes beyond the minimum design requirements with sensible additions such as configurable constants, shared helper methods, and a package `__init__.py` file. No gaps, no missing features, no contradictions found.

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-02-13 | Initial gap analysis | gap-detector agent |
