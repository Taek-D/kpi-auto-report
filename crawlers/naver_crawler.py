"""
네이버 쇼핑 검색 API 클라이언트
공식 API: https://openapi.naver.com/v1/search/shop.json
"""

import logging
import os
import time
from datetime import date

import requests

from .config import BRAND_MAPPING, MAX_RESULTS_PER_KEYWORD, REQUEST_DELAY_MAX, REQUEST_DELAY_MIN

logger = logging.getLogger(__name__)

import random

MAX_RETRIES = 3


class NaverShoppingCrawler:
    """네이버 쇼핑 검색 API 크롤러"""

    def __init__(self):
        self.client_id = os.getenv("NAVER_CLIENT_ID", "")
        self.client_secret = os.getenv("NAVER_CLIENT_SECRET", "")
        self.api_url = "https://openapi.naver.com/v1/search/shop.json"
        self.session = requests.Session()

        if not self.client_id or not self.client_secret:
            logger.warning("[네이버] NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 미설정")

    def _get_headers(self) -> dict:
        return {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
        }

    def _identify_brand(self, product_name: str) -> str:
        for keyword, brand in BRAND_MAPPING.items():
            if keyword in product_name:
                return brand
        return "기타"

    def search(self, keyword: str, category: str) -> list[dict]:
        """네이버 쇼핑 API로 검색 후 상품 정보 반환"""
        logger.info(f"[네이버] 검색: '{keyword}' (카테고리: {category})")

        params = {
            "query": keyword,
            "display": MAX_RESULTS_PER_KEYWORD,
            "sort": "sim",
        }

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
                time.sleep(delay)

                response = self.session.get(
                    self.api_url,
                    headers=self._get_headers(),
                    params=params,
                    timeout=10,
                )
                response.raise_for_status()
                data = response.json()
                break
            except requests.RequestException as e:
                logger.warning(f"[네이버] API 요청 실패 (시도 {attempt}/{MAX_RETRIES}): {e}")
                if attempt == MAX_RETRIES:
                    logger.error(f"[네이버] 최대 재시도 초과: '{keyword}'")
                    return []

        items = data.get("items", [])
        today = date.today().isoformat()
        results = []

        for rank, item in enumerate(items, start=1):
            title = item.get("title", "").replace("<b>", "").replace("</b>", "")
            price = int(item.get("lprice", 0))
            mall_name = item.get("mallName", "")

            results.append({
                "crawl_date": today,
                "source": "naver",
                "category": category,
                "product_name": title[:200],
                "brand": self._identify_brand(title) if self._identify_brand(title) != "기타" else mall_name,
                "price": price,
                "ranking": rank,
                "review_count": 0,  # 네이버 검색 API에서 리뷰 수 미제공
                "avg_rating": None,
            })

        logger.info(f"[네이버] '{keyword}' → {len(results)}개 상품 수집")
        return results

    def crawl_all(self, targets: list[dict]) -> list[dict]:
        """설정된 모든 타겟에 대해 크롤링 실행"""
        if not self.client_id or not self.client_secret:
            logger.error("[네이버] API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")
            return []

        all_results = []
        for target in targets:
            results = self.search(target["keyword"], target["category"])
            all_results.extend(results)

        logger.info(f"[네이버] 전체 수집 완료: {len(all_results)}개 상품")
        return all_results
