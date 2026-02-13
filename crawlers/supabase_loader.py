"""
Supabase REST API 데이터 적재 모듈
market_competitors 테이블에 크롤링 결과를 upsert
"""

import logging
import os

import requests

logger = logging.getLogger(__name__)

BATCH_SIZE = 10


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
