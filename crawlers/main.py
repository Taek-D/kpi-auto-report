"""
경쟁사 크롤링 파이프라인 CLI
크롤링 → Supabase 적재 → Pandas 분석 → 시각화

Usage:
    python -m crawlers.main --all              # 전체 파이프라인
    python -m crawlers.main --crawl            # 크롤링 + 적재만
    python -m crawlers.main --analyze          # 분석만 (Supabase 기존 데이터)
    python -m crawlers.main --crawl --source coupang  # 쿠팡만 크롤링
"""

import argparse
import logging
import sys

from dotenv import load_dotenv

from .analyzer import CompetitorAnalyzer
from .config import CRAWL_TARGETS
from .coupang_crawler import CoupangCrawler
from .naver_crawler import NaverShoppingCrawler
from .supabase_loader import SupabaseLoader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def crawl(source: str | None = None) -> list[dict]:
    """크롤링 실행 → 결과 리스트 반환"""
    all_records = []

    if source is None or source == "coupang":
        logger.info("=" * 40 + " 쿠팡 크롤링 시작 " + "=" * 40)
        crawler = CoupangCrawler()
        results = crawler.crawl_all(CRAWL_TARGETS["coupang"])
        all_records.extend(results)

    if source is None or source == "naver":
        logger.info("=" * 40 + " 네이버 크롤링 시작 " + "=" * 40)
        crawler = NaverShoppingCrawler()
        results = crawler.crawl_all(CRAWL_TARGETS["naver"])
        all_records.extend(results)

    logger.info(f"크롤링 완료: 총 {len(all_records)}건 수집")
    return all_records


def load_to_supabase(records: list[dict]) -> dict:
    """Supabase에 데이터 적재"""
    if not records:
        logger.warning("적재할 데이터가 없습니다.")
        return {"success": 0, "failed": 0, "total": 0}

    loader = SupabaseLoader()
    return loader.upsert(records)


def analyze() -> None:
    """Supabase 데이터 분석 + 시각화"""
    logger.info("=" * 40 + " 데이터 분석 시작 " + "=" * 40)

    loader = SupabaseLoader()
    data = loader.fetch_competitors()

    if not data:
        logger.error("분석할 데이터가 없습니다.")
        return

    analyzer = CompetitorAnalyzer(data)

    # 콘솔 요약 출력
    print(analyzer.summary_stats())

    # 차트 생성
    chart_paths = analyzer.generate_all()
    if chart_paths:
        print(f"\n[차트] 생성된 차트 ({len(chart_paths)}개):")
        for p in chart_paths:
            print(f"  → {p}")
    else:
        print("\n[경고] 차트를 생성하지 못했습니다.")


def main():
    parser = argparse.ArgumentParser(
        description="앳홈 경쟁사 크롤링 & 분석 파이프라인",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m crawlers.main --all                   전체 파이프라인
  python -m crawlers.main --crawl                 크롤링 + 적재만
  python -m crawlers.main --crawl --source naver  네이버만 크롤링
  python -m crawlers.main --analyze               분석 + 시각화만
        """,
    )
    parser.add_argument("--all", action="store_true", help="전체 파이프라인 실행 (크롤링+적재+분석)")
    parser.add_argument("--crawl", action="store_true", help="크롤링 + Supabase 적재")
    parser.add_argument("--analyze", action="store_true", help="Supabase 데이터 분석 + 시각화")
    parser.add_argument("--source", choices=["coupang", "naver"], help="특정 소스만 크롤링")

    args = parser.parse_args()

    if not any([args.all, args.crawl, args.analyze]):
        parser.print_help()
        sys.exit(1)

    # .env 로드
    load_dotenv()
    logger.info("환경 변수 로드 완료")

    # 크롤링
    if args.all or args.crawl:
        records = crawl(source=args.source)
        stats = load_to_supabase(records)
        print(f"\n[적재] 적재 결과: 성공 {stats['success']}건 / 실패 {stats['failed']}건 / 전체 {stats['total']}건")

    # 분석
    if args.all or args.analyze:
        analyze()

    logger.info("파이프라인 완료")


if __name__ == "__main__":
    main()
