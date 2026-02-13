"""
경쟁사 데이터 분석 및 시각화 모듈
Pandas 분석 + matplotlib/seaborn 차트 생성
"""

import logging
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import pandas as pd
import seaborn as sns

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).parent.parent / "output"

# 한글 폰트 설정
def _setup_korean_font():
    font_candidates = ["Malgun Gothic", "NanumGothic", "AppleGothic", "DejaVu Sans"]
    available = {f.name for f in fm.fontManager.ttflist}
    for font_name in font_candidates:
        if font_name in available:
            plt.rcParams["font.family"] = font_name
            plt.rcParams["axes.unicode_minus"] = False
            logger.info(f"[분석] 한글 폰트: {font_name}")
            return
    logger.warning("[분석] 한글 폰트를 찾을 수 없습니다. 기본 폰트를 사용합니다.")

_setup_korean_font()

# 앳홈 브랜드 하이라이트 색상
ATHOME_BRANDS = {"앳홈(미닉스)", "앳홈(톰)", "앳홈(프로티원)"}
COLOR_ATHOME = "#FF6B35"
COLOR_COMPETITOR = "#4A90D9"


class CompetitorAnalyzer:
    """경쟁사 데이터 분석 및 시각화"""

    def __init__(self, data: list[dict]):
        self.df = pd.DataFrame(data)
        if not self.df.empty:
            self.df["crawl_date"] = pd.to_datetime(self.df["crawl_date"])
            self.df["price"] = pd.to_numeric(self.df["price"], errors="coerce").fillna(0)
            self.df["ranking"] = pd.to_numeric(self.df["ranking"], errors="coerce")
            self.df["review_count"] = pd.to_numeric(self.df["review_count"], errors="coerce").fillna(0)
            self.df["avg_rating"] = pd.to_numeric(self.df["avg_rating"], errors="coerce")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def _brand_color(self, brand: str) -> str:
        return COLOR_ATHOME if brand in ATHOME_BRANDS else COLOR_COMPETITOR

    def summary_stats(self) -> str:
        """콘솔 출력용 요약 통계"""
        if self.df.empty:
            return "[분석] 데이터가 없습니다."

        lines = ["=" * 60, "[경쟁사 분석 요약]", "=" * 60]
        dates = sorted(self.df["crawl_date"].unique())

        if len(dates) >= 2:
            latest = self.df[self.df["crawl_date"] == dates[-1]]
            prev = self.df[self.df["crawl_date"] == dates[-2]]
            lines.append(f"\n기간: {dates[-2].strftime('%Y-%m-%d')} → {dates[-1].strftime('%Y-%m-%d')}")

            for source in sorted(latest["source"].unique()):
                lines.append(f"\n--- {source.upper()} ---")
                src_latest = latest[latest["source"] == source]
                src_prev = prev[prev["source"] == source]

                for _, row in src_latest.iterrows():
                    name = row["product_name"]
                    prev_row = src_prev[src_prev["product_name"] == name]

                    rank_str = f"순위: {int(row['ranking'])}" if pd.notna(row["ranking"]) else "순위: -"
                    price_str = f"가격: {int(row['price']):,}원"

                    if not prev_row.empty:
                        prev_r = prev_row.iloc[0]
                        rank_change = int(prev_r["ranking"] - row["ranking"]) if pd.notna(prev_r["ranking"]) and pd.notna(row["ranking"]) else 0
                        price_change = int(row["price"] - prev_r["price"])
                        review_growth = int(row["review_count"] - prev_r["review_count"])

                        rank_arrow = f"(▲{rank_change})" if rank_change > 0 else f"(▼{abs(rank_change)})" if rank_change < 0 else "(→)"
                        price_arrow = f"(+{price_change:,})" if price_change > 0 else f"({price_change:,})" if price_change < 0 else "(→)"

                        is_athome = " *" if row["brand"] in ATHOME_BRANDS else "  "
                        lines.append(f"  {is_athome} {name}")
                        lines.append(f"     {rank_str} {rank_arrow} | {price_str} {price_arrow} | 리뷰: +{review_growth}")
                    else:
                        is_athome = " *" if row["brand"] in ATHOME_BRANDS else "  "
                        lines.append(f"  {is_athome} {name}")
                        lines.append(f"     {rank_str} | {price_str} | 리뷰: {int(row['review_count'])}")
        else:
            latest = self.df[self.df["crawl_date"] == dates[-1]]
            lines.append(f"\n날짜: {dates[-1].strftime('%Y-%m-%d')} (비교 데이터 없음)")
            for _, row in latest.iterrows():
                lines.append(f"  {row['product_name']}: 순위 {row['ranking']}, {int(row['price']):,}원")

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)

    def plot_price_trend(self) -> str | None:
        """가격 추이 라인 차트"""
        if self.df.empty:
            return None

        fig, ax = plt.subplots(figsize=(12, 6))
        coupang = self.df[self.df["source"] == "coupang"]

        for product in coupang["product_name"].unique():
            prod_data = coupang[coupang["product_name"] == product].sort_values("crawl_date")
            brand = prod_data.iloc[0]["brand"]
            color = self._brand_color(brand)
            linewidth = 2.5 if brand in ATHOME_BRANDS else 1.5
            ax.plot(
                prod_data["crawl_date"],
                prod_data["price"],
                marker="o",
                label=product,
                color=color,
                linewidth=linewidth,
                alpha=0.9 if brand in ATHOME_BRANDS else 0.6,
            )

        ax.set_title("경쟁사 가격 추이 (쿠팡)", fontsize=14, fontweight="bold")
        ax.set_xlabel("날짜")
        ax.set_ylabel("가격 (원)")
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{int(x):,}"))
        ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()

        path = OUTPUT_DIR / "price_trend.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        logger.info(f"[분석] 가격 추이 차트 저장: {path}")
        return str(path)

    def plot_ranking_comparison(self) -> str | None:
        """자사 vs 경쟁사 순위 비교 (수평 바 차트)"""
        if self.df.empty:
            return None

        latest_date = self.df["crawl_date"].max()
        latest = self.df[(self.df["crawl_date"] == latest_date) & (self.df["source"] == "coupang")]
        latest = latest.sort_values("ranking")

        fig, ax = plt.subplots(figsize=(10, 6))
        colors = [self._brand_color(b) for b in latest["brand"]]
        bars = ax.barh(
            latest["product_name"],
            latest["ranking"],
            color=colors,
            edgecolor="white",
        )

        for bar, (_, row) in zip(bars, latest.iterrows()):
            ax.text(
                bar.get_width() + 0.1,
                bar.get_y() + bar.get_height() / 2,
                f"{int(row['ranking'])}위",
                va="center",
                fontsize=9,
            )

        ax.set_title(f"쿠팡 검색 순위 비교 ({latest_date.strftime('%Y-%m-%d')})", fontsize=14, fontweight="bold")
        ax.set_xlabel("순위 (낮을수록 좋음)")
        ax.invert_xaxis()
        ax.invert_yaxis()

        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor=COLOR_ATHOME, label="앳홈 브랜드"),
            Patch(facecolor=COLOR_COMPETITOR, label="경쟁사"),
        ]
        ax.legend(handles=legend_elements, loc="lower right")
        ax.grid(True, axis="x", alpha=0.3)
        plt.tight_layout()

        path = OUTPUT_DIR / "ranking_comparison.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        logger.info(f"[분석] 순위 비교 차트 저장: {path}")
        return str(path)

    def plot_review_growth(self) -> str | None:
        """주간 리뷰 증가량 (그룹 바 차트)"""
        if self.df.empty:
            return None

        dates = sorted(self.df["crawl_date"].unique())
        if len(dates) < 2:
            logger.warning("[분석] 리뷰 성장 차트에 최소 2개 날짜 필요")
            return None

        latest = self.df[(self.df["crawl_date"] == dates[-1]) & (self.df["source"] == "coupang")]
        prev = self.df[(self.df["crawl_date"] == dates[-2]) & (self.df["source"] == "coupang")]
        merged = latest.merge(prev[["product_name", "review_count"]], on="product_name", suffixes=("", "_prev"))
        merged["review_growth"] = merged["review_count"] - merged["review_count_prev"]
        merged = merged.sort_values("review_growth", ascending=False)

        fig, ax = plt.subplots(figsize=(10, 6))
        colors = [self._brand_color(b) for b in merged["brand"]]
        bars = ax.bar(range(len(merged)), merged["review_growth"], color=colors)
        ax.set_xticks(range(len(merged)))
        ax.set_xticklabels(merged["product_name"], rotation=45, ha="right", fontsize=8)

        for bar, val in zip(bars, merged["review_growth"]):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 5,
                f"+{int(val)}",
                ha="center",
                va="bottom",
                fontsize=9,
            )

        ax.set_title("주간 리뷰 증가량 (쿠팡)", fontsize=14, fontweight="bold")
        ax.set_ylabel("리뷰 증가 수")

        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor=COLOR_ATHOME, label="앳홈 브랜드"),
            Patch(facecolor=COLOR_COMPETITOR, label="경쟁사"),
        ]
        ax.legend(handles=legend_elements)
        ax.grid(True, axis="y", alpha=0.3)
        plt.tight_layout()

        path = OUTPUT_DIR / "review_growth.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        logger.info(f"[분석] 리뷰 성장 차트 저장: {path}")
        return str(path)

    def plot_dashboard(self) -> str | None:
        """종합 대시보드 (2x2 subplot)"""
        if self.df.empty:
            return None

        dates = sorted(self.df["crawl_date"].unique())
        latest_date = dates[-1]
        coupang = self.df[self.df["source"] == "coupang"]
        latest_cp = coupang[coupang["crawl_date"] == latest_date].sort_values("ranking")

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle("앳홈 경쟁사 모니터링 대시보드", fontsize=16, fontweight="bold", y=0.98)

        # [0,0] 가격 비교 (바 차트)
        ax = axes[0, 0]
        colors = [self._brand_color(b) for b in latest_cp["brand"]]
        ax.barh(latest_cp["product_name"], latest_cp["price"], color=colors)
        ax.set_title("제품별 가격 비교 (쿠팡)")
        ax.set_xlabel("가격 (원)")
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{int(x):,}"))
        ax.invert_yaxis()

        # [0,1] 순위 분포 (점 그래프)
        ax = axes[0, 1]
        for _, row in latest_cp.iterrows():
            color = self._brand_color(row["brand"])
            size = 150 if row["brand"] in ATHOME_BRANDS else 80
            ax.scatter(row["ranking"], row["category"], s=size, c=color, zorder=5, edgecolors="white")
            ax.annotate(
                row["product_name"][:10],
                (row["ranking"], row["category"]),
                textcoords="offset points",
                xytext=(5, 5),
                fontsize=7,
            )
        ax.set_title("카테고리별 순위 분포")
        ax.set_xlabel("순위")
        ax.grid(True, alpha=0.3)

        # [1,0] 리뷰 수 비교
        ax = axes[1, 0]
        colors = [self._brand_color(b) for b in latest_cp["brand"]]
        bars = ax.bar(range(len(latest_cp)), latest_cp["review_count"], color=colors)
        ax.set_xticks(range(len(latest_cp)))
        ax.set_xticklabels(latest_cp["product_name"], rotation=45, ha="right", fontsize=7)
        ax.set_title("리뷰 수 비교")
        ax.set_ylabel("리뷰 수")
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{int(x):,}"))

        # [1,1] 평점 비교
        ax = axes[1, 1]
        rated = latest_cp[latest_cp["avg_rating"].notna()]
        colors = [self._brand_color(b) for b in rated["brand"]]
        ax.barh(rated["product_name"], rated["avg_rating"], color=colors)
        ax.set_title("평점 비교")
        ax.set_xlabel("평점")
        ax.set_xlim(3.5, 5.0)
        ax.invert_yaxis()

        plt.tight_layout(rect=[0, 0, 1, 0.96])

        path = OUTPUT_DIR / "competitor_dashboard.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        logger.info(f"[분석] 종합 대시보드 저장: {path}")
        return str(path)

    def generate_all(self) -> list[str]:
        """모든 차트 생성 후 파일 경로 목록 반환"""
        paths = []
        for method in [self.plot_price_trend, self.plot_ranking_comparison, self.plot_review_growth, self.plot_dashboard]:
            result = method()
            if result:
                paths.append(result)
        return paths
