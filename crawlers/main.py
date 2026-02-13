"""
경쟁사 크롤링 파이프라인 CLI
크롤링 → Supabase 적재 → Pandas 분석 → 시각화

Usage:
    python -m crawlers.main --all              # 전체 파이프라인
    python -m crawlers.main --crawl            # 크롤링 + 적재만
    python -m crawlers.main --analyze          # 분석만 (Supabase 기존 데이터)
    python -m crawlers.main --crawl --source coupang  # 쿠팡만 크롤링
    python -m crawlers.main --report weekly    # 주간 요약 리포트
    python -m crawlers.main --report monthly   # 월간 요약 리포트 + 차트
    python -m crawlers.main --predict          # ML 매출 예측 분석
    python -m crawlers.main --insight          # 비즈니스 인사이트 분석
    python -m crawlers.main --abtest           # A/B 테스트 분석
"""

import argparse
import io
import logging
import sys

from dotenv import load_dotenv

# Windows cp949 인코딩 문제 해결 (이모지 출력)
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

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


def report(report_type: str) -> None:
    """주간/월간 요약 리포트 생성"""
    from .report_generator import WeeklyReportGenerator, MonthlyReportGenerator

    if report_type == "weekly":
        logger.info("=" * 40 + " 주간 리포트 생성 " + "=" * 40)
        generator = WeeklyReportGenerator()
        result = generator.generate()
        print(result)

    elif report_type == "monthly":
        logger.info("=" * 40 + " 월간 리포트 생성 " + "=" * 40)
        generator = MonthlyReportGenerator()
        result = generator.generate()
        print(result)

    else:
        logger.error(f"알 수 없는 리포트 유형: {report_type}")


def predict() -> None:
    """ML 매출 예측 분석"""
    from .predictor import RevenuePredictor

    logger.info("=" * 40 + " 매출 예측 분석 " + "=" * 40)
    predictor = RevenuePredictor()
    result = predictor.run(days=30)
    print(result)


def insight() -> None:
    """비즈니스 인사이트 분석"""
    from .insight_analyzer import InsightAnalyzer

    logger.info("=" * 40 + " 인사이트 분석 " + "=" * 40)
    analyzer = InsightAnalyzer()
    result = analyzer.run(days=30)
    print(result)


def abtest() -> None:
    """A/B 테스트 분석"""
    from .ab_test_analyzer import ABTestAnalyzer

    logger.info("=" * 40 + " A/B 테스트 분석 " + "=" * 40)
    analyzer = ABTestAnalyzer()
    result = analyzer.run()
    print(result)


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
  python -m crawlers.main --report weekly         주간 요약 리포트
  python -m crawlers.main --report monthly        월간 요약 리포트 + 차트
  python -m crawlers.main --predict               ML 매출 예측 분석
  python -m crawlers.main --insight               비즈니스 인사이트 분석
  python -m crawlers.main --abtest                A/B 테스트 분석
        """,
    )
    parser.add_argument("--all", action="store_true", help="전체 파이프라인 실행 (크롤링+적재+분석)")
    parser.add_argument("--crawl", action="store_true", help="크롤링 + Supabase 적재")
    parser.add_argument("--analyze", action="store_true", help="Supabase 데이터 분석 + 시각화")
    parser.add_argument("--source", choices=["coupang", "naver"], help="특정 소스만 크롤링")
    parser.add_argument("--report", choices=["weekly", "monthly"], help="주간/월간 요약 리포트 생성")
    parser.add_argument("--predict", action="store_true", help="ML 매출 예측 분석")
    parser.add_argument("--insight", action="store_true", help="비즈니스 인사이트 분석 (채널 믹스, 경쟁사 상관, 요일 패턴)")
    parser.add_argument("--abtest", action="store_true", help="A/B 테스트 분석 (통계 검정 + 비즈니스 해석)")

    args = parser.parse_args()

    if not any([args.all, args.crawl, args.analyze, args.report, args.predict, args.insight, args.abtest]):
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

    # 주간/월간 리포트
    if args.report:
        report(args.report)

    # ML 예측
    if args.predict:
        predict()

    # 인사이트 분석
    if args.insight:
        insight()

    # A/B 테스트 분석
    if args.abtest:
        abtest()

    logger.info("파이프라인 완료")


if __name__ == "__main__":
    main()
