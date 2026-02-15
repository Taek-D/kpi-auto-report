"""
검색 트렌드 수집 모듈 (Google Trends + Naver DataLab)
외부 검색 트렌드 데이터를 수집하여 Supabase에 적재.
두 API 모두 실패해도 기존 샘플 데이터로 분석은 계속 가능.
"""

import logging
import os
import time
from datetime import datetime, timedelta

import requests

from .config import TREND_KEYWORDS
from .supabase_loader import SupabaseLoader

logger = logging.getLogger(__name__)


class TrendCollector:
    """Google Trends + Naver DataLab 검색 트렌드 수집기"""

    def __init__(self):
        self.loader = SupabaseLoader()
        self.naver_client_id = os.getenv("NAVER_DATALAB_CLIENT_ID", "")
        self.naver_client_secret = os.getenv("NAVER_DATALAB_CLIENT_SECRET", "")

    def run(self) -> str:
        """전체 트렌드 수집 파이프라인"""
        lines = [
            "📈 검색 트렌드 수집",
            "=" * 55,
            "",
        ]

        all_records = []

        # 1. Google Trends 수집
        google_records = self._collect_google_trends()
        all_records.extend(google_records)
        lines.append(f"  Google Trends: {len(google_records)}건 수집")

        # 2. Naver DataLab 수집
        naver_records = self._collect_naver_datalab()
        all_records.extend(naver_records)
        lines.append(f"  Naver DataLab: {len(naver_records)}건 수집")

        # 3. Supabase 적재
        if all_records:
            stats = self.loader.upsert_trends(all_records)
            lines.append(f"\n  적재 결과: 성공 {stats['success']}건 / 실패 {stats['failed']}건")
        else:
            lines.append("\n  수집된 데이터가 없습니다. API 키를 확인해주세요.")
            lines.append("  (샘플 데이터로 --trend 분석은 가능합니다)")

        lines.append("")
        return "\n".join(lines)

    def _collect_google_trends(self) -> list[dict]:
        """Google Trends 데이터 수집 (pytrends)"""
        try:
            from pytrends.request import TrendReq
        except ImportError:
            logger.warning("[Google Trends] pytrends 미설치. pip install pytrends")
            return []

        records = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        timeframe = f"{start_date.strftime('%Y-%m-%d')} {end_date.strftime('%Y-%m-%d')}"

        try:
            pytrends = TrendReq(hl="ko", tz=540)
        except Exception as e:
            logger.error(f"[Google Trends] 초기화 실패: {e}")
            return []

        # 브랜드별 키워드를 5개씩 배치 처리
        all_keywords = []
        for brand, groups in TREND_KEYWORDS.items():
            for product_group, keyword in groups.items():
                all_keywords.append((brand, product_group, keyword))

        for i in range(0, len(all_keywords), 5):
            batch = all_keywords[i : i + 5]
            keywords = [kw for _, _, kw in batch]

            try:
                pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo="KR")
                df = pytrends.interest_over_time()

                if df.empty:
                    logger.warning(f"[Google Trends] 배치 {i // 5 + 1}: 데이터 없음")
                    continue

                for brand, product_group, keyword in batch:
                    if keyword not in df.columns:
                        continue

                    for date_idx, row in df.iterrows():
                        records.append({
                            "trend_date": date_idx.strftime("%Y-%m-%d"),
                            "brand": brand,
                            "product_group": product_group,
                            "keyword": keyword,
                            "source": "google_trends",
                            "trend_value": float(row[keyword]),
                        })

                logger.info(f"[Google Trends] 배치 {i // 5 + 1}: {len(batch)}개 키워드 수집 완료")

            except Exception as e:
                logger.warning(f"[Google Trends] 배치 {i // 5 + 1} 실패 (graceful skip): {e}")

            # rate limiting
            if i + 5 < len(all_keywords):
                time.sleep(2)

        logger.info(f"[Google Trends] 총 {len(records)}건 수집")
        return records

    def _collect_naver_datalab(self) -> list[dict]:
        """Naver DataLab 검색어 트렌드 수집"""
        if not self.naver_client_id or not self.naver_client_secret:
            logger.warning("[Naver DataLab] NAVER_DATALAB_CLIENT_ID/SECRET 미설정")
            return []

        records = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        url = "https://openapi.naver.com/v1/datalab/search"
        headers = {
            "X-Naver-Client-Id": self.naver_client_id,
            "X-Naver-Client-Secret": self.naver_client_secret,
            "Content-Type": "application/json",
        }

        # 키워드를 5개씩 배치 (API 제한)
        all_keywords = []
        for brand, groups in TREND_KEYWORDS.items():
            for product_group, keyword in groups.items():
                all_keywords.append((brand, product_group, keyword))

        for i in range(0, len(all_keywords), 5):
            batch = all_keywords[i : i + 5]

            keyword_groups = []
            for _, product_group, keyword in batch:
                keyword_groups.append({
                    "groupName": product_group,
                    "keywords": [keyword],
                })

            body = {
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": end_date.strftime("%Y-%m-%d"),
                "timeUnit": "date",
                "keywordGroups": keyword_groups,
            }

            try:
                response = requests.post(url, headers=headers, json=body, timeout=15)
                response.raise_for_status()
                data = response.json()

                for result in data.get("results", []):
                    group_name = result.get("title", "")

                    # group_name으로 brand 매칭
                    matched = [(b, pg, kw) for b, pg, kw in batch if pg == group_name]
                    if not matched:
                        continue

                    brand, product_group, keyword = matched[0]

                    for point in result.get("data", []):
                        records.append({
                            "trend_date": point["period"],
                            "brand": brand,
                            "product_group": product_group,
                            "keyword": keyword,
                            "source": "naver_datalab",
                            "trend_value": float(point["ratio"]),
                        })

                logger.info(f"[Naver DataLab] 배치 {i // 5 + 1}: {len(batch)}개 키워드 수집 완료")

            except requests.RequestException as e:
                logger.warning(f"[Naver DataLab] 배치 {i // 5 + 1} 실패 (graceful skip): {e}")

            # rate limiting
            if i + 5 < len(all_keywords):
                time.sleep(1)

        logger.info(f"[Naver DataLab] 총 {len(records)}건 수집")
        return records
