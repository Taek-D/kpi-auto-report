"""
인사이트 분석 모듈 ("So What?" 분석)
채널 믹스 변동, 경쟁사-매출 상관, 요일별 패턴, 비즈니스 추천
"""

import logging
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import pandas as pd
from scipy import stats

from .supabase_loader import SupabaseLoader

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).parent.parent / "output"

BRAND_LABELS = {
    "minix": "미닉스",
    "thome": "톰",
    "protione": "프로티원",
}

CHANNEL_LABELS = {
    "own_mall": "자사몰",
    "coupang": "쿠팡",
    "naver": "네이버",
    "gs_home": "GS홈쇼핑",
    "oliveyoung": "올리브영",
}

BRAND_COLORS = {
    "minix": "#FF6B35",
    "thome": "#4A90D9",
    "protione": "#7ED321",
}

WEEKDAY_KR = ["월", "화", "수", "목", "금", "토", "일"]


def _setup_korean_font():
    font_candidates = ["Malgun Gothic", "NanumGothic", "AppleGothic", "DejaVu Sans"]
    available = {f.name for f in fm.fontManager.ttflist}
    for font_name in font_candidates:
        if font_name in available:
            plt.rcParams["font.family"] = font_name
            plt.rcParams["axes.unicode_minus"] = False
            return


_setup_korean_font()


class InsightAnalyzer:
    """데이터 기반 비즈니스 인사이트 분석기"""

    def __init__(self):
        self.loader = SupabaseLoader()
        self.insights = []

    def run(self, days: int = 30) -> str:
        """전체 인사이트 분석 파이프라인"""
        # 1. 데이터 조회
        sales_data = self.loader.fetch_brand_sales(days=days)
        competitor_data = self.loader.fetch_competitors_extended(weeks=8)

        if not sales_data:
            return "[인사이트] 매출 데이터가 없습니다. Supabase 연결을 확인해주세요."

        df_sales = pd.DataFrame(sales_data)
        df_sales["sale_date"] = pd.to_datetime(df_sales["sale_date"])
        df_sales["revenue"] = pd.to_numeric(df_sales["revenue"], errors="coerce").fillna(0)
        df_sales["orders"] = pd.to_numeric(df_sales["orders"], errors="coerce").fillna(0)

        lines = [
            "🔍 앳홈 비즈니스 인사이트 분석",
            "=" * 55,
            "",
        ]

        # 2. 채널 믹스 변동 분석
        mix_insights = self.channel_mix_shift(df_sales)
        lines.extend(mix_insights)

        # 3. 요일별 패턴 분석
        weekday_insights = self.weekday_pattern(df_sales)
        lines.extend(weekday_insights)

        # 4. 경쟁사-매출 상관 분석
        if competitor_data:
            df_comp = pd.DataFrame(competitor_data)
            df_comp["crawl_date"] = pd.to_datetime(df_comp["crawl_date"])
            comp_insights = self.competitor_impact(df_sales, df_comp)
            lines.extend(comp_insights)

        # 5. 비즈니스 추천
        recommendations = self.generate_recommendations(df_sales)
        lines.extend(recommendations)

        # 6. 시각화
        self._plot_channel_mix(df_sales)
        self._plot_weekday_heatmap(df_sales)
        lines.append("")
        lines.append("[차트] output/channel_mix_trend.png - 채널 비중 변화 추이")
        lines.append("[차트] output/weekday_heatmap.png - 브랜드x요일 매출 히트맵")

        return "\n".join(lines)

    def channel_mix_shift(self, df: pd.DataFrame) -> list[str]:
        """채널 믹스 변동 분석: 주간 채널별 매출 비중 변화"""
        lines = [
            "📊 채널 믹스 변동 분석",
            "━" * 45,
        ]

        df = df[df["revenue"] > 0].copy()
        df["week"] = df["sale_date"].dt.isocalendar().week.astype(int)

        for brand in sorted(df["brand"].unique()):
            brand_df = df[df["brand"] == brand]
            label = BRAND_LABELS.get(brand, brand)

            weeks = sorted(brand_df["week"].unique())
            if len(weeks) < 2:
                continue

            # 최근 2주 비교
            recent_week = weeks[-1]
            prev_week = weeks[-2]

            recent = brand_df[brand_df["week"] == recent_week].groupby("channel")["revenue"].sum()
            prev = brand_df[brand_df["week"] == prev_week].groupby("channel")["revenue"].sum()

            recent_total = recent.sum()
            prev_total = prev.sum()

            if recent_total == 0 or prev_total == 0:
                continue

            recent_pct = (recent / recent_total * 100).to_dict()
            prev_pct = (prev / prev_total * 100).to_dict()

            lines.append(f"\n  [{label}]")

            all_channels = set(list(recent_pct.keys()) + list(prev_pct.keys()))
            shifts = []
            for ch in sorted(all_channels):
                r = recent_pct.get(ch, 0)
                p = prev_pct.get(ch, 0)
                change = r - p
                ch_label = CHANNEL_LABELS.get(ch, ch)
                shifts.append((ch_label, p, r, change))

            for ch_label, prev_val, recent_val, change in sorted(shifts, key=lambda x: abs(x[3]), reverse=True):
                if abs(change) > 0.5:
                    arrow = "↑" if change > 0 else "↓"
                    highlight = " ⚠️" if abs(change) > 3 else ""
                    lines.append(f"    {ch_label}: {prev_val:.1f}% → {recent_val:.1f}% ({arrow}{abs(change):.1f}%p){highlight}")

        lines.append("")
        return lines

    def weekday_pattern(self, df: pd.DataFrame) -> list[str]:
        """요일별 매출 패턴 분석"""
        lines = [
            "📅 요일별 매출 패턴",
            "━" * 45,
        ]

        df = df.copy()
        df["day_of_week"] = df["sale_date"].dt.dayofweek

        for brand in sorted(df["brand"].unique()):
            brand_df = df[df["brand"] == brand]
            label = BRAND_LABELS.get(brand, brand)

            daily_avg = brand_df.groupby("day_of_week")["revenue"].sum()
            daily_orders = brand_df.groupby("day_of_week")["orders"].sum()

            if daily_avg.empty:
                continue

            # 가장 매출 높은 요일
            best_day = daily_avg.idxmax()
            worst_day = daily_avg.idxmin()

            best_orders_day = daily_orders.idxmax()

            lines.append(f"\n  [{label}]")
            lines.append(f"    매출 최고 요일: {WEEKDAY_KR[best_day]}요일 (₩{daily_avg[best_day]/10000:,.0f}만)")
            lines.append(f"    매출 최저 요일: {WEEKDAY_KR[worst_day]}요일 (₩{daily_avg[worst_day]/10000:,.0f}만)")
            lines.append(f"    주문 최고 요일: {WEEKDAY_KR[best_orders_day]}요일 ({daily_orders[best_orders_day]:,.0f}건)")

            # 주말 vs 평일 비교
            weekday_avg = daily_avg[daily_avg.index < 5].mean()
            weekend_avg = daily_avg[daily_avg.index >= 5].mean()
            if weekday_avg > 0:
                weekend_lift = (weekend_avg / weekday_avg - 1) * 100
                lines.append(f"    주말 매출 효과: 평일 대비 {'+' if weekend_lift > 0 else ''}{weekend_lift:.1f}%")

            # 브랜드별 특이 패턴
            if brand == "thome" and 2 in daily_avg.index:
                wed_revenue = daily_avg[2]
                avg_no_wed = daily_avg[daily_avg.index != 2].mean()
                if avg_no_wed > 0:
                    wed_effect = (wed_revenue / avg_no_wed - 1) * 100
                    if wed_effect > 10:
                        lines.append(f"    💡 수요일 GS홈쇼핑 방송 효과: 타 요일 대비 +{wed_effect:.0f}%")

        lines.append("")
        return lines

    def competitor_impact(self, df_sales: pd.DataFrame, df_comp: pd.DataFrame) -> list[str]:
        """경쟁사 가격 변동과 자사 매출 상관 분석"""
        lines = [
            "🏢 경쟁사-매출 상관 분석",
            "━" * 45,
        ]

        # 주간 매출 집계 (minix만 - 음식물처리기 카테고리)
        minix_sales = df_sales[df_sales["brand"] == "minix"].copy()
        minix_weekly = (
            minix_sales.groupby(pd.Grouper(key="sale_date", freq="W"))["revenue"]
            .sum()
            .reset_index()
        )
        minix_weekly.columns = ["week_start", "revenue"]

        # 경쟁사 가격 추이 (스마트카라, 쿠팡 기준)
        smartkara = df_comp[
            (df_comp["product_name"] == "스마트카라 PCS-400")
            & (df_comp["source"] == "coupang")
        ].sort_values("crawl_date")

        rincle = df_comp[
            (df_comp["product_name"].str.contains("린클", na=False))
            & (df_comp["source"] == "coupang")
        ].sort_values("crawl_date")

        if not smartkara.empty and len(smartkara) >= 3:
            # 스마트카라 가격 변동 분석
            sk_prices = smartkara[["crawl_date", "price"]].values
            price_min = smartkara["price"].min()
            price_max = smartkara["price"].max()
            price_range = price_max - price_min

            if price_range > 0:
                discount_start = smartkara.loc[smartkara["price"].idxmin(), "crawl_date"]
                lines.append(f"\n  [스마트카라 가격 변동]")
                lines.append(f"    가격 범위: ₩{price_min:,.0f} ~ ₩{price_max:,.0f} (차이: ₩{price_range:,.0f})")
                lines.append(f"    최저가 시점: {pd.Timestamp(discount_start).strftime('%Y-%m-%d')}")

                # 할인 기간 식별
                discount_weeks = smartkara[smartkara["price"] < price_max - price_range * 0.3]
                if not discount_weeks.empty:
                    d_start = discount_weeks["crawl_date"].min()
                    d_end = discount_weeks["crawl_date"].max()
                    lines.append(f"    할인 기간: {pd.Timestamp(d_start).strftime('%m/%d')} ~ {pd.Timestamp(d_end).strftime('%m/%d')}")
                    lines.append(f"    💡 경쟁사 할인 기간 중 미닉스 음식물처리기 가격 경쟁력 모니터링 필요")

        if not rincle.empty and len(rincle) >= 3:
            # 린클 가격 추이
            price_start = rincle["price"].iloc[0]
            price_end = rincle["price"].iloc[-1]
            price_change = price_end - price_start

            lines.append(f"\n  [린클 가격 추이]")
            lines.append(f"    가격 변화: ₩{price_start:,.0f} → ₩{price_end:,.0f} ({'+' if price_change > 0 else ''}₩{price_change:,.0f})")
            if price_change < 0:
                lines.append(f"    💡 린클 지속적 가격 인하 → 미닉스 가성비 포지셔닝 재검토 필요")

        # 앳홈 제품 순위 변화
        athome_products = df_comp[df_comp["brand"].str.contains("앳홈", na=False)]
        if not athome_products.empty:
            lines.append(f"\n  [앳홈 제품 순위 변화]")
            for product in athome_products["product_name"].unique():
                prod_data = athome_products[
                    (athome_products["product_name"] == product)
                    & (athome_products["source"] == "coupang")
                ].sort_values("crawl_date")

                if len(prod_data) >= 2:
                    rank_start = prod_data["ranking"].iloc[0]
                    rank_end = prod_data["ranking"].iloc[-1]
                    rank_change = rank_start - rank_end  # 양수 = 순위 상승
                    arrow = "↑" if rank_change > 0 else ("↓" if rank_change < 0 else "→")
                    lines.append(f"    {product}: {rank_start}위 → {rank_end}위 ({arrow}{abs(rank_change)})")

        lines.append("")
        return lines

    def generate_recommendations(self, df: pd.DataFrame) -> list[str]:
        """분석 결과 기반 비즈니스 추천"""
        lines = [
            "🎯 비즈니스 액션 추천",
            "━" * 45,
        ]

        df = df.copy()
        df["day_of_week"] = df["sale_date"].dt.dayofweek

        recommendations = []

        for brand in sorted(df["brand"].unique()):
            brand_df = df[df["brand"] == brand]
            label = BRAND_LABELS.get(brand, brand)

            # 채널별 매출
            channel_revenue = brand_df.groupby("channel")["revenue"].sum()
            total_revenue = channel_revenue.sum()
            if total_revenue == 0:
                continue

            top_channel = channel_revenue.idxmax()
            top_pct = channel_revenue[top_channel] / total_revenue * 100

            # 채널별 ROAS
            channel_roas = brand_df[brand_df["ad_spend"] > 0].groupby("channel").apply(
                lambda x: x["revenue"].sum() / x["ad_spend"].sum(), include_groups=False
            )

            # 요일별 주문
            daily_orders = brand_df.groupby("day_of_week")["orders"].sum()
            best_order_day = daily_orders.idxmax()

            # 쿠팡 비중이 높으면 광고비 증액 권장
            if top_channel == "coupang" and top_pct > 35:
                coupang_data = brand_df[brand_df["channel"] == "coupang"]
                avg_ad = coupang_data["ad_spend"].mean()
                avg_roas = channel_roas.get("coupang", 0)
                if avg_roas > 5:
                    suggested_increase = avg_ad * 0.15
                    expected_orders = coupang_data["orders"].mean() * 0.12
                    recommendations.append(
                        f"  [마케팅] {label} 쿠팡 광고비 ₩{avg_ad/1000:,.0f}K → ₩{(avg_ad+suggested_increase)/1000:,.0f}K "
                        f"증액 시 주문 +{expected_orders:.0f}건/일 예상 (ROAS {avg_roas:.1f} 기준)"
                    )

            # 주문 집중 요일 기반 프로모션 권장
            if best_order_day < 5:  # 평일
                promo_day = WEEKDAY_KR[best_order_day]
                prev_day = WEEKDAY_KR[max(0, best_order_day - 1)]
                recommendations.append(
                    f"  [프로모션] {label}: {promo_day}요일 주문 집중 → {prev_day}요일 쿠팡 딜/네이버 특가 등록 권장"
                )

            # 톰 GS홈쇼핑 리타게팅
            if brand == "thome":
                gs_revenue = channel_revenue.get("gs_home", 0)
                own_revenue = channel_revenue.get("own_mall", 0)
                if gs_revenue > 0 and own_revenue > 0:
                    recommendations.append(
                        f"  [채널] {label}: 수요일 GS홈쇼핑 방송 후 자사몰 리타게팅 광고 강화 → "
                        f"방송 노출 후 자사몰 전환 유도"
                    )

            # 자사몰 ROAS 높은 경우
            own_roas = channel_roas.get("own_mall", 0)
            if own_roas > 7:
                recommendations.append(
                    f"  [채널] {label}: 자사몰 ROAS {own_roas:.1f}로 높음 → "
                    f"자사몰 전용 혜택(적립금, 무료배송) 강화로 비중 확대"
                )

        for i, rec in enumerate(recommendations[:5], 1):
            lines.append(f"  {i}. {rec.strip()}")

        lines.append("")
        return lines

    def _plot_channel_mix(self, df: pd.DataFrame) -> None:
        """채널 비중 변화 stacked area chart"""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        fig, axes = plt.subplots(1, 3, figsize=(18, 6))

        brands = sorted(df["brand"].unique())
        channel_colors = {
            "own_mall": "#FF6B35",
            "coupang": "#00B4D8",
            "naver": "#2DB400",
            "gs_home": "#FF69B4",
            "oliveyoung": "#9B59B6",
        }

        for ax, brand in zip(axes, brands):
            brand_df = df[df["brand"] == brand].copy()
            label = BRAND_LABELS.get(brand, brand)

            # 일별 채널 매출
            pivot = brand_df.pivot_table(
                index="sale_date", columns="channel", values="revenue", aggfunc="sum", fill_value=0
            )

            # 비중 계산
            row_totals = pivot.sum(axis=1)
            pivot_pct = pivot.div(row_totals.replace(0, np.nan), axis=0).fillna(0) * 100

            # 3일 이동평균으로 스무딩
            pivot_smooth = pivot_pct.rolling(3, min_periods=1).mean()

            channels = [c for c in ["coupang", "own_mall", "naver", "gs_home", "oliveyoung"] if c in pivot_smooth.columns]

            ax.stackplot(
                pivot_smooth.index,
                [pivot_smooth[ch].values for ch in channels],
                labels=[CHANNEL_LABELS.get(ch, ch) for ch in channels],
                colors=[channel_colors.get(ch, "#999") for ch in channels],
                alpha=0.8,
            )

            ax.set_title(f"{label} 채널 비중 추이", fontsize=12, fontweight="bold")
            ax.set_ylabel("비중 (%)")
            ax.set_ylim(0, 100)
            ax.legend(loc="upper left", fontsize=8)
            ax.tick_params(axis="x", rotation=45)
            ax.grid(True, alpha=0.3)

        plt.tight_layout()
        path = OUTPUT_DIR / "channel_mix_trend.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        logger.info(f"[인사이트] 채널 믹스 차트 저장: {path}")

    def _plot_weekday_heatmap(self, df: pd.DataFrame) -> None:
        """브랜드x요일 매출 히트맵"""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        df = df.copy()
        df["day_of_week"] = df["sale_date"].dt.dayofweek

        # 브랜드x요일 일평균 매출
        heatmap_data = df.groupby(["brand", "day_of_week"])["revenue"].mean().unstack(fill_value=0)

        fig, ax = plt.subplots(figsize=(10, 5))

        brands = sorted(heatmap_data.index)
        brand_labels = [BRAND_LABELS.get(b, b) for b in brands]
        data = heatmap_data.loc[brands].values / 10000  # 만원 단위

        im = ax.imshow(data, cmap="YlOrRd", aspect="auto")

        ax.set_xticks(range(7))
        ax.set_xticklabels(WEEKDAY_KR)
        ax.set_yticks(range(len(brands)))
        ax.set_yticklabels(brand_labels)

        # 셀 값 표시
        for i in range(len(brands)):
            for j in range(7):
                val = data[i, j]
                color = "white" if val > data.max() * 0.6 else "black"
                ax.text(j, i, f"₩{val:,.0f}만", ha="center", va="center", fontsize=9, color=color)

        ax.set_title("브랜드별 요일 평균 매출 (채널 합산)", fontsize=13, fontweight="bold")
        fig.colorbar(im, ax=ax, label="평균 매출 (만원)")

        plt.tight_layout()
        path = OUTPUT_DIR / "weekday_heatmap.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        logger.info(f"[인사이트] 요일 히트맵 저장: {path}")
