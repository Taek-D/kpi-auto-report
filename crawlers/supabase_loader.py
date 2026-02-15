"""
Supabase REST API 데이터 적재 모듈
market_competitors 테이블에 크롤링 결과를 upsert
"""

import logging
import os

import requests

logger = logging.getLogger(__name__)

BATCH_SIZE = 10

ALLOWED_RPC_FUNCTIONS = {
    "get_brand_kpis_yesterday",
    "get_brand_kpis_last_week",
    "get_top_products",
    "get_competitor_changes",
    "get_trend_sales_correlation",
}


class SupabaseLoader:
    """Supabase REST API를 통한 데이터 적재"""

    def __init__(self):
        self.url = os.getenv("SUPABASE_URL", "")
        self.key = os.getenv("SUPABASE_ANON_KEY", "")

        if not self.url or not self.key:
            logger.warning("[Supabase] SUPABASE_URL / SUPABASE_ANON_KEY 미설정")

    def _get_headers(self) -> dict:
        return {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates",
        }

    def upsert(self, records: list[dict]) -> dict:
        """market_competitors 테이블에 upsert (배치 처리)

        Returns:
            dict: {"success": int, "failed": int, "total": int}
        """
        if not self.url or not self.key:
            logger.error("[Supabase] API 키가 설정되지 않았습니다.")
            return {"success": 0, "failed": len(records), "total": len(records)}

        endpoint = f"{self.url}/rest/v1/market_competitors"
        stats = {"success": 0, "failed": 0, "total": len(records)}

        for i in range(0, len(records), BATCH_SIZE):
            batch = records[i : i + BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1
            try:
                response = requests.post(
                    endpoint,
                    headers=self._get_headers(),
                    json=batch,
                    timeout=15,
                )
                response.raise_for_status()
                stats["success"] += len(batch)
                logger.info(f"[Supabase] 배치 {batch_num}: {len(batch)}건 적재 성공")
            except requests.RequestException as e:
                stats["failed"] += len(batch)
                logger.error(f"[Supabase] 배치 {batch_num} 적재 실패: {e}")

        logger.info(
            f"[Supabase] 적재 완료 - 성공: {stats['success']}, "
            f"실패: {stats['failed']}, 전체: {stats['total']}"
        )
        return stats

    def fetch_brand_sales(self, days: int = 30) -> list[dict]:
        """brand_daily_sales 테이블에서 최근 N일 데이터 조회 (예측 분석용)"""
        if not self.url or not self.key:
            logger.error("[Supabase] API 키가 설정되지 않았습니다.")
            return []

        endpoint = f"{self.url}/rest/v1/brand_daily_sales"
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
        }
        params = {
            "select": "*",
            "order": "sale_date.desc,brand,channel",
            "limit": days * 15,  # 3 brands x 5 channels x days
        }

        try:
            response = requests.get(endpoint, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            logger.info(f"[Supabase] brand_daily_sales {len(data)}건 조회 완료")
            return data
        except requests.RequestException as e:
            logger.error(f"[Supabase] brand_daily_sales 조회 실패: {e}")
            return []

    def call_rpc(self, function_name: str, params: dict | None = None) -> list[dict]:
        """Supabase RPC 함수 호출"""
        if function_name not in ALLOWED_RPC_FUNCTIONS:
            logger.error(f"[Supabase] 허용되지 않은 RPC 함수: {function_name}")
            return []

        if not self.url or not self.key:
            logger.error("[Supabase] API 키가 설정되지 않았습니다.")
            return []

        endpoint = f"{self.url}/rest/v1/rpc/{function_name}"
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                endpoint,
                headers=headers,
                json=params or {},
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()
            logger.info(f"[Supabase] RPC {function_name}: {len(data)}건 반환")
            return data
        except requests.RequestException as e:
            logger.error(f"[Supabase] RPC {function_name} 호출 실패: {e}")
            return []

    def fetch_competitors(self, limit: int = 1000) -> list[dict]:
        """market_competitors 테이블에서 데이터 조회 (분석용)"""
        if not self.url or not self.key:
            logger.error("[Supabase] API 키가 설정되지 않았습니다.")
            return []

        endpoint = f"{self.url}/rest/v1/market_competitors"
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
        }
        params = {
            "select": "*",
            "order": "crawl_date.desc,source,category,ranking",
            "limit": limit,
        }

        try:
            response = requests.get(endpoint, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            logger.info(f"[Supabase] {len(data)}건 조회 완료")
            return data
        except requests.RequestException as e:
            logger.error(f"[Supabase] 데이터 조회 실패: {e}")
            return []

    def fetch_competitors_extended(self, weeks: int = 8) -> list[dict]:
        """market_competitors 테이블에서 최근 N주 데이터 조회 (장기 추이 분석용)"""
        if not self.url or not self.key:
            logger.error("[Supabase] API 키가 설정되지 않았습니다.")
            return []

        endpoint = f"{self.url}/rest/v1/market_competitors"
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
        }
        params = {
            "select": "*",
            "order": "crawl_date.asc,source,category,ranking",
            "limit": weeks * 15,  # ~13 products/week
        }

        try:
            response = requests.get(endpoint, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            logger.info(f"[Supabase] 경쟁사 {weeks}주 데이터 {len(data)}건 조회 완료")
            return data
        except requests.RequestException as e:
            logger.error(f"[Supabase] 경쟁사 확장 데이터 조회 실패: {e}")
            return []

    def fetch_ab_test(self) -> list[dict]:
        """ab_test_results 테이블에서 A/B 테스트 데이터 조회"""
        if not self.url or not self.key:
            logger.error("[Supabase] API 키가 설정되지 않았습니다.")
            return []

        endpoint = f"{self.url}/rest/v1/ab_test_results"
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
        }
        params = {
            "select": "*",
            "order": "test_date.asc,variant",
        }

        try:
            response = requests.get(endpoint, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            logger.info(f"[Supabase] A/B 테스트 데이터 {len(data)}건 조회 완료")
            return data
        except requests.RequestException as e:
            logger.error(f"[Supabase] A/B 테스트 데이터 조회 실패: {e}")
            return []

    def fetch_search_trends(self, days: int = 30) -> list[dict]:
        """search_trends 테이블에서 최근 N일 데이터 조회 (트렌드 분석용)"""
        if not self.url or not self.key:
            logger.error("[Supabase] API 키가 설정되지 않았습니다.")
            return []

        endpoint = f"{self.url}/rest/v1/search_trends"
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
        }
        params = {
            "select": "*",
            "order": "trend_date.desc,brand,source",
            "limit": days * 16,  # 8 product_groups x 2 sources x days
        }

        try:
            response = requests.get(endpoint, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            logger.info(f"[Supabase] search_trends {len(data)}건 조회 완료")
            return data
        except requests.RequestException as e:
            logger.error(f"[Supabase] search_trends 조회 실패: {e}")
            return []

    def upsert_trends(self, records: list[dict]) -> dict:
        """search_trends 테이블에 upsert (배치 처리)

        Returns:
            dict: {"success": int, "failed": int, "total": int}
        """
        if not self.url or not self.key:
            logger.error("[Supabase] API 키가 설정되지 않았습니다.")
            return {"success": 0, "failed": len(records), "total": len(records)}

        endpoint = f"{self.url}/rest/v1/search_trends"
        params = {"on_conflict": "trend_date,brand,product_group,keyword,source"}
        stats = {"success": 0, "failed": 0, "total": len(records)}

        for i in range(0, len(records), BATCH_SIZE):
            batch = records[i : i + BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1
            try:
                response = requests.post(
                    endpoint,
                    headers=self._get_headers(),
                    params=params,
                    json=batch,
                    timeout=15,
                )
                response.raise_for_status()
                stats["success"] += len(batch)
                logger.info(f"[Supabase] 트렌드 배치 {batch_num}: {len(batch)}건 적재 성공")
            except requests.RequestException as e:
                stats["failed"] += len(batch)
                logger.error(f"[Supabase] 트렌드 배치 {batch_num} 적재 실패: {e}")

        logger.info(
            f"[Supabase] 트렌드 적재 완료 - 성공: {stats['success']}, "
            f"실패: {stats['failed']}, 전체: {stats['total']}"
        )
        return stats
