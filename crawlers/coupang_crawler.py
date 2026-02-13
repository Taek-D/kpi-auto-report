"""
쿠팡 검색 결과 크롤러 - requests + BeautifulSoup4
검색 키워드별 상위 상품의 가격/순위/리뷰 수집
"""

import logging
import random
import time
from datetime import date
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from .config import BRAND_MAPPING, MAX_RESULTS_PER_KEYWORD, REQUEST_DELAY_MAX, REQUEST_DELAY_MIN

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]

MAX_RETRIES = 3


class CoupangCrawler:
    """쿠팡 검색 결과 스크래핑 크롤러"""

    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://www.coupang.com/np/search"

    def _get_headers(self) -> dict:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

    def _request(self, url: str) -> requests.Response | None:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
                time.sleep(delay)
                response = self.session.get(url, headers=self._get_headers(), timeout=15)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                logger.warning(f"[쿠팡] 요청 실패 (시도 {attempt}/{MAX_RETRIES}): {e}")
                if attempt == MAX_RETRIES:
                    logger.error(f"[쿠팡] 최대 재시도 초과: {url}")
                    return None
        return None

    def _identify_brand(self, product_name: str) -> str:
        for keyword, brand in BRAND_MAPPING.items():
            if keyword in product_name:
                return brand
        return "기타"

    def _parse_results(self, html: str, category: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        items = soup.select("li.search-product")
        if not items:
            items = soup.select("li[class*='search-product']")

        results = []
        today = date.today().isoformat()

        for rank, item in enumerate(items[:MAX_RESULTS_PER_KEYWORD], start=1):
            try:
                name_tag = item.select_one("div.name, a.search-product-link div.name")
                name = name_tag.get_text(strip=True) if name_tag else None

                price_tag = item.select_one("strong.price-value, em.sale strong")
                price_text = price_tag.get_text(strip=True) if price_tag else "0"
                price = int(price_text.replace(",", "").replace("원", "") or "0")

                rating_tag = item.select_one("em.rating")
                rating = float(rating_tag.get_text(strip=True)) if rating_tag else None

                review_tag = item.select_one("span.rating-total-count, span.count")
                review_text = review_tag.get_text(strip=True) if review_tag else "(0)"
                review_count = int(review_text.strip("()").replace(",", "") or "0")

                if not name:
                    continue

                results.append({
                    "crawl_date": today,
                    "source": "coupang",
                    "category": category,
                    "product_name": name[:200],
                    "brand": self._identify_brand(name),
                    "price": price,
                    "ranking": rank,
                    "review_count": review_count,
                    "avg_rating": rating,
                })
            except (ValueError, AttributeError) as e:
                logger.debug(f"[쿠팡] 상품 파싱 스킵 (rank={rank}): {e}")
                continue

        return results

    def search(self, keyword: str, category: str) -> list[dict]:
        """키워드로 쿠팡 검색 후 상위 상품 정보 반환"""
        encoded = quote(keyword)
        url = f"{self.base_url}?q={encoded}&sorter=scoreDesc"
        logger.info(f"[쿠팡] 크롤링: '{keyword}' (카테고리: {category})")

        response = self._request(url)
        if not response:
            return []

        results = self._parse_results(response.text, category)
        logger.info(f"[쿠팡] '{keyword}' → {len(results)}개 상품 수집")
        return results

    def crawl_all(self, targets: list[dict]) -> list[dict]:
        """설정된 모든 타겟에 대해 크롤링 실행"""
        all_results = []
        for target in targets:
            results = self.search(target["keyword"], target["category"])
            all_results.extend(results)
        logger.info(f"[쿠팡] 전체 수집 완료: {len(all_results)}개 상품")
        return all_results
