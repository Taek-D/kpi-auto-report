"""
트렌드-매출 상관 분석 모듈
검색 트렌드(Google Trends + Naver DataLab)와 내부 매출 데이터의 상관 분석.
Pearson/Spearman 상관, 선행 지표(lead-lag) 분석, 성수기 탐지, 비즈니스 추천.
차트 4종: overlay, heatmap, lead-lag, peak season.
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

BRAND_COLORS = {
    "minix": "#FF6B35",
    "thome": "#4A90D9",
    "protione": "#7ED321",
}

SOURCE_LABELS = {
    "google_trends": "Google Trends",
    "naver_datalab": "Naver DataLab",
}


def _setup_korean_font():
    font_candidates = ["Malgun Gothic", "NanumGothic", "AppleGothic", "DejaVu Sans"]
    available = {f.name for f in fm.fontManager.ttflist}
    for font_name in font_candidates:
        if font_name in available:
            plt.rcParams["font.family"] = font_name
            plt.rcParams["axes.unicode_minus"] = False
            return


_setup_korean_font()


class TrendAnalyzer:
    """검색 트렌드-매출 상관 분석기"""

    def __init__(self):
        self.loader = SupabaseLoader()

    def run(self, days: int = 30) -> str:
        """전체 트렌드 분석 파이프라인"""
        # 1. 데이터 조회
        trend_data = self.loader.fetch_search_trends(days=days)
        sales_data = self.loader.fetch_brand_sales(days=days)

        if not trend_data:
            return "[트렌드] 트렌드 데이터가 없습니다. Supabase 연결 또는 schema/search_trends.sql 적용을 확인해주세요."

        df_trend = pd.DataFrame(trend_data)
        df_trend["trend_date"] = pd.to_datetime(df_trend["trend_date"])
        df_trend["trend_value"] = pd.to_numeric(df_trend["trend_value"], errors="coerce").fillna(0)

        df_sales = None
        if sales_data:
            df_sales = pd.DataFrame(sales_data)
            df_sales["sale_date"] = pd.to_datetime(df_sales["sale_date"])
            df_sales["revenue"] = pd.to_numeric(df_sales["revenue"], errors="coerce").fillna(0)
            df_sales["orders"] = pd.to_numeric(df_sales["orders"], errors="coerce").fillna(0)

        lines = [
            "📈 검색 트렌드-매출 상관 분석",
            "=" * 55,
            "",
        ]

        # 2. 상관 분석
        corr_results = self._correlation_analysis(df_trend, df_sales)
        lines.extend(corr_results["lines"])

        # 3. 선행 지표 분석
        lead_results = self._lead_lag_analysis(df_trend, df_sales)
        lines.extend(lead_results["lines"])

        # 4. 성수기 탐지
        peak_results = self._peak_season_detection(df_trend)
        lines.extend(peak_results["lines"])

        # 5. 비즈니스 추천
        recommendations = self._generate_recommendations(corr_results, lead_results, peak_results)
        lines.extend(recommendations)

        # 6. 시각화
        self._plot_trend_sales_overlay(df_trend, df_sales)
        self._plot_correlation_heatmap(corr_results)
        self._plot_lead_lag(lead_results)
        self._plot_peak_season(df_trend, peak_results)

        lines.append("[차트] output/trend_sales_overlay.png - 트렌드 vs 매출 듀얼축")
        lines.append("[차트] output/trend_correlation_heatmap.png - 상관관계 히트맵")
        lines.append("[차트] output/trend_lead_lag.png - 선행 지표 분석")
        lines.append("[차트] output/trend_peak_season.png - 성수기 탐지")

        return "\n".join(lines)

    def _correlation_analysis(self, df_trend: pd.DataFrame, df_sales: pd.DataFrame | None) -> dict:
        """Pearson/Spearman 상관 분석: 브랜드 x 소스별"""
        lines = [
            "📊 상관 분석 (검색 트렌드 vs 매출)",
            "━" * 45,
        ]

        results = {}  # {(brand, source): {"pearson_r": r, "spearman_r": r, ...}}

        if df_sales is None or df_sales.empty:
            lines.append("  매출 데이터가 없어 상관 분석을 건너뜁니다.")
            lines.append("")
            return {"lines": lines, "results": results}

        # 브랜드별 일별 매출 집계
        daily_sales = df_sales.groupby(["sale_date", "brand"])["revenue"].sum().reset_index()

        # 브랜드별 일별 트렌드 평균
        daily_trend = df_trend.groupby(["trend_date", "brand", "source"])["trend_value"].mean().reset_index()

        for brand in sorted(df_trend["brand"].unique()):
            label = BRAND_LABELS.get(brand, brand)
            brand_sales = daily_sales[daily_sales["brand"] == brand].set_index("sale_date")["revenue"]

            for source in sorted(df_trend["source"].unique()):
                source_label = SOURCE_LABELS.get(source, source)
                brand_trend = daily_trend[
                    (daily_trend["brand"] == brand) & (daily_trend["source"] == source)
                ].set_index("trend_date")["trend_value"]

                # 날짜 기준 inner join
                common_dates = brand_sales.index.intersection(brand_trend.index)

                if len(common_dates) < 3:
                    continue

                s_vals = brand_sales.loc[common_dates].values
                t_vals = brand_trend.loc[common_dates].values

                pearson_r, pearson_p = stats.pearsonr(t_vals, s_vals)
                spearman_r, spearman_p = stats.spearmanr(t_vals, s_vals)

                results[(brand, source)] = {
                    "pearson_r": pearson_r,
                    "pearson_p": pearson_p,
                    "spearman_r": spearman_r,
                    "spearman_p": spearman_p,
                    "n": len(common_dates),
                }

                sig = "**" if pearson_p < 0.01 else ("*" if pearson_p < 0.05 else "")
                lines.append(
                    f"  [{label} x {source_label}] "
                    f"Pearson r={pearson_r:.3f}{sig}, "
                    f"Spearman r={spearman_r:.3f} (n={len(common_dates)})"
                )

        if not results:
            lines.append("  매출/트렌드 날짜 겹침 부족으로 상관 분석 불가 (최소 3일 필요)")

        lines.append("")
        return {"lines": lines, "results": results}

    def _lead_lag_analysis(self, df_trend: pd.DataFrame, df_sales: pd.DataFrame | None) -> dict:
        """선행 지표 분석: lag -7~+7일 cross-correlation"""
        lines = [
            "⏱️ 선행 지표 분석 (검색이 매출보다 N일 선행?)",
            "━" * 45,
        ]

        results = {}  # {brand: {"best_lag": int, "best_corr": float, "lags": dict}}

        if df_sales is None or df_sales.empty:
            lines.append("  매출 데이터가 없어 선행 분석을 건너뜁니다.")
            lines.append("")
            return {"lines": lines, "results": results}

        daily_sales = df_sales.groupby(["sale_date", "brand"])["revenue"].sum().reset_index()
        daily_trend = df_trend.groupby(["trend_date", "brand"])["trend_value"].mean().reset_index()

        for brand in sorted(df_trend["brand"].unique()):
            label = BRAND_LABELS.get(brand, brand)

            brand_sales = daily_sales[daily_sales["brand"] == brand].sort_values("sale_date")
            brand_trend = daily_trend[daily_trend["brand"] == brand].sort_values("trend_date")

            if len(brand_sales) < 5 or len(brand_trend) < 5:
                continue

            # 시계열 정렬 (trend_date를 기준)
            sales_ts = brand_sales.set_index("sale_date")["revenue"]
            trend_ts = brand_trend.set_index("trend_date")["trend_value"]

            lag_corrs = {}
            best_lag = 0
            best_corr = -1

            for lag in range(-7, 8):
                # lag > 0: 트렌드가 매출보다 lag일 선행
                shifted_trend = trend_ts.copy()
                shifted_trend.index = shifted_trend.index + pd.Timedelta(days=lag)

                common = sales_ts.index.intersection(shifted_trend.index)
                if len(common) < 3:
                    continue

                r, _ = stats.pearsonr(shifted_trend.loc[common].values, sales_ts.loc[common].values)
                lag_corrs[lag] = r

                if abs(r) > abs(best_corr):
                    best_corr = r
                    best_lag = lag

            results[brand] = {
                "best_lag": best_lag,
                "best_corr": best_corr,
                "lags": lag_corrs,
            }

            if best_lag > 0:
                lines.append(f"  [{label}] 검색이 매출보다 {best_lag}일 선행 (r={best_corr:.3f})")
            elif best_lag < 0:
                lines.append(f"  [{label}] 매출이 검색보다 {abs(best_lag)}일 선행 (r={best_corr:.3f})")
            else:
                lines.append(f"  [{label}] 동시 상관 최대 (lag=0, r={best_corr:.3f})")

        if not results:
            lines.append("  데이터 부족으로 선행 분석 불가")

        lines.append("")
        return {"lines": lines, "results": results}

    def _peak_season_detection(self, df_trend: pd.DataFrame) -> dict:
        """성수기 식별: 75th percentile 초과 기간 탐지"""
        lines = [
            "🔥 성수기 탐지 (트렌드 75th percentile 초과)",
            "━" * 45,
        ]

        results = {}  # {brand: [{"start": date, "end": date, "avg_val": float}]}

        for brand in sorted(df_trend["brand"].unique()):
            label = BRAND_LABELS.get(brand, brand)
            brand_data = df_trend[df_trend["brand"] == brand]

            # 일별 평균 트렌드
            daily_avg = brand_data.groupby("trend_date")["trend_value"].mean().sort_index()

            if daily_avg.empty:
                continue

            threshold = daily_avg.quantile(0.75)
            peak_dates = daily_avg[daily_avg > threshold].index.tolist()

            # 연속 기간 그룹핑
            peak_periods = []
            if peak_dates:
                current_start = peak_dates[0]
                current_end = peak_dates[0]

                for date in peak_dates[1:]:
                    if (date - current_end).days <= 2:  # 2일 갭까지 허용
                        current_end = date
                    else:
                        period_data = daily_avg.loc[current_start:current_end]
                        peak_periods.append({
                            "start": current_start,
                            "end": current_end,
                            "avg_val": period_data.mean(),
                            "days": (current_end - current_start).days + 1,
                        })
                        current_start = date
                        current_end = date

                # 마지막 기간
                period_data = daily_avg.loc[current_start:current_end]
                peak_periods.append({
                    "start": current_start,
                    "end": current_end,
                    "avg_val": period_data.mean(),
                    "days": (current_end - current_start).days + 1,
                })

            results[brand] = peak_periods

            if peak_periods:
                lines.append(f"\n  [{label}] 기준선: {threshold:.1f}")
                for p in peak_periods:
                    start_str = p["start"].strftime("%m/%d")
                    end_str = p["end"].strftime("%m/%d")
                    lines.append(
                        f"    {start_str}~{end_str} ({p['days']}일) "
                        f"평균 트렌드 {p['avg_val']:.1f}"
                    )
            else:
                lines.append(f"  [{label}] 뚜렷한 성수기 패턴 없음")

        lines.append("")
        return {"lines": lines, "results": results}

    def _generate_recommendations(self, corr: dict, lead: dict, peak: dict) -> list[str]:
        """분석 결과 기반 비즈니스 추천"""
        lines = [
            "🎯 비즈니스 액션 추천",
            "━" * 45,
        ]

        rec_num = 1

        # 상관 기반 추천
        for (brand, source), vals in corr.get("results", {}).items():
            label = BRAND_LABELS.get(brand, brand)
            source_label = SOURCE_LABELS.get(source, source)

            if vals["pearson_r"] > 0.5 and vals["pearson_p"] < 0.05:
                lines.append(
                    f"  {rec_num}. [광고] {label}: {source_label} 검색량과 매출 강한 상관 "
                    f"(r={vals['pearson_r']:.2f}) → 검색 트렌드 상승 시 광고비 증액 권장"
                )
                rec_num += 1

        # 선행 지표 기반 추천
        for brand, vals in lead.get("results", {}).items():
            label = BRAND_LABELS.get(brand, brand)
            best_lag = vals["best_lag"]

            if best_lag >= 2 and vals["best_corr"] > 0.3:
                lines.append(
                    f"  {rec_num}. [타이밍] {label}: 검색 트렌드가 매출 {best_lag}일 선행 → "
                    f"검색량 급증 감지 시 {best_lag}일 후 프로모션 준비"
                )
                rec_num += 1

        # 성수기 기반 추천
        for brand, periods in peak.get("results", {}).items():
            label = BRAND_LABELS.get(brand, brand)

            long_peaks = [p for p in periods if p["days"] >= 3]
            if long_peaks:
                p = long_peaks[0]
                lines.append(
                    f"  {rec_num}. [재고] {label}: {p['start'].strftime('%m/%d')}~{p['end'].strftime('%m/%d')} "
                    f"성수기 ({p['days']}일) → 해당 기간 재고 사전 확보 및 프로모션 집중"
                )
                rec_num += 1

        if rec_num == 1:
            lines.append("  매출 데이터 추가 축적 후 더 정확한 추천 가능")

        lines.append("")
        return lines

    # ==================== 차트 4종 ====================

    def _plot_trend_sales_overlay(self, df_trend: pd.DataFrame, df_sales: pd.DataFrame | None) -> None:
        """트렌드 vs 매출 듀얼축 라인차트 (1x3 브랜드별)"""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        brands = sorted(df_trend["brand"].unique())
        fig, axes = plt.subplots(1, len(brands), figsize=(6 * len(brands), 5))
        if len(brands) == 1:
            axes = [axes]

        for ax, brand in zip(axes, brands):
            label = BRAND_LABELS.get(brand, brand)
            color = BRAND_COLORS.get(brand, "#333")

            # 트렌드 (일별 평균)
            brand_trend = df_trend[df_trend["brand"] == brand]
            daily_trend = brand_trend.groupby("trend_date")["trend_value"].mean().sort_index()

            ax.plot(daily_trend.index, daily_trend.values, "-", color=color, linewidth=2, label="검색 트렌드")
            ax.set_ylabel("트렌드 지수", color=color)
            ax.tick_params(axis="y", labelcolor=color)

            # 매출 (듀얼축)
            if df_sales is not None and not df_sales.empty:
                brand_sales = df_sales[df_sales["brand"] == brand]
                daily_rev = brand_sales.groupby("sale_date")["revenue"].sum().sort_index()

                if not daily_rev.empty:
                    ax2 = ax.twinx()
                    ax2.bar(daily_rev.index, daily_rev.values / 10000, alpha=0.3, color=color, label="매출 (만원)", width=0.8)
                    ax2.set_ylabel("매출 (만원)", color="gray")
                    ax2.tick_params(axis="y", labelcolor="gray")

            ax.set_title(f"{label}", fontsize=12, fontweight="bold")
            ax.tick_params(axis="x", rotation=45)
            ax.grid(True, alpha=0.3)
            ax.legend(loc="upper left", fontsize=8)

        fig.suptitle("검색 트렌드 vs 매출 추이", fontsize=14, fontweight="bold", y=1.02)
        plt.tight_layout()
        path = OUTPUT_DIR / "trend_sales_overlay.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        logger.info(f"[트렌드] 오버레이 차트 저장: {path}")

    def _plot_correlation_heatmap(self, corr_results: dict) -> None:
        """상관관계 히트맵: 브랜드 x 소스 Pearson r"""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        results = corr_results.get("results", {})
        if not results:
            logger.warning("[트렌드] 상관 데이터 없음 — 히트맵 건너뜀")
            return

        brands = sorted(set(b for b, _ in results.keys()))
        sources = sorted(set(s for _, s in results.keys()))

        data = np.full((len(brands), len(sources)), np.nan)
        for i, brand in enumerate(brands):
            for j, source in enumerate(sources):
                if (brand, source) in results:
                    data[i, j] = results[(brand, source)]["pearson_r"]

        fig, ax = plt.subplots(figsize=(8, 5))
        im = ax.imshow(data, cmap="RdYlGn", aspect="auto", vmin=-1, vmax=1)

        ax.set_xticks(range(len(sources)))
        ax.set_xticklabels([SOURCE_LABELS.get(s, s) for s in sources])
        ax.set_yticks(range(len(brands)))
        ax.set_yticklabels([BRAND_LABELS.get(b, b) for b in brands])

        for i in range(len(brands)):
            for j in range(len(sources)):
                val = data[i, j]
                if not np.isnan(val):
                    color = "white" if abs(val) > 0.5 else "black"
                    ax.text(j, i, f"{val:.3f}", ha="center", va="center", fontsize=12, fontweight="bold", color=color)

        ax.set_title("검색 트렌드-매출 상관계수 (Pearson r)", fontsize=13, fontweight="bold")
        fig.colorbar(im, ax=ax, label="Pearson r", shrink=0.8)

        plt.tight_layout()
        path = OUTPUT_DIR / "trend_correlation_heatmap.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        logger.info(f"[트렌드] 상관 히트맵 저장: {path}")

    def _plot_lead_lag(self, lead_results: dict) -> None:
        """선행 지표 바차트: lag별 상관계수"""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        results = lead_results.get("results", {})
        if not results:
            logger.warning("[트렌드] 선행 분석 데이터 없음 — 바차트 건너뜀")
            return

        brands = sorted(results.keys())
        fig, axes = plt.subplots(1, len(brands), figsize=(5 * len(brands), 4))
        if len(brands) == 1:
            axes = [axes]

        for ax, brand in zip(axes, brands):
            label = BRAND_LABELS.get(brand, brand)
            color = BRAND_COLORS.get(brand, "#333")
            lag_data = results[brand]["lags"]
            best_lag = results[brand]["best_lag"]

            if not lag_data:
                continue

            lags = sorted(lag_data.keys())
            corrs = [lag_data[l] for l in lags]

            bar_colors = [color if l == best_lag else "#CCCCCC" for l in lags]
            ax.bar(lags, corrs, color=bar_colors, edgecolor="white", width=0.8)

            ax.axhline(y=0, color="black", linewidth=0.5)
            ax.axvline(x=0, color="red", linewidth=0.8, linestyle="--", alpha=0.5)

            if best_lag != 0:
                ax.annotate(
                    f"최적 lag={best_lag}",
                    xy=(best_lag, lag_data[best_lag]),
                    xytext=(best_lag, lag_data[best_lag] + 0.15),
                    fontsize=9, fontweight="bold", color=color,
                    ha="center",
                    arrowprops=dict(arrowstyle="->", color=color),
                )

            ax.set_title(f"{label}", fontsize=11, fontweight="bold")
            ax.set_xlabel("Lag (일) — 양수: 트렌드 선행")
            ax.set_ylabel("Pearson r")
            ax.set_ylim(-1, 1)
            ax.grid(True, axis="y", alpha=0.3)

        fig.suptitle("선행 지표 분석 (Cross-Correlation)", fontsize=13, fontweight="bold", y=1.02)
        plt.tight_layout()
        path = OUTPUT_DIR / "trend_lead_lag.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        logger.info(f"[트렌드] 선행 지표 차트 저장: {path}")

    def _plot_peak_season(self, df_trend: pd.DataFrame, peak_results: dict) -> None:
        """성수기 area chart + 피크 구간 강조"""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        brands = sorted(df_trend["brand"].unique())
        fig, axes = plt.subplots(len(brands), 1, figsize=(12, 4 * len(brands)), sharex=True)
        if len(brands) == 1:
            axes = [axes]

        for ax, brand in zip(axes, brands):
            label = BRAND_LABELS.get(brand, brand)
            color = BRAND_COLORS.get(brand, "#333")

            brand_data = df_trend[df_trend["brand"] == brand]
            daily_avg = brand_data.groupby("trend_date")["trend_value"].mean().sort_index()

            if daily_avg.empty:
                continue

            # Area chart
            ax.fill_between(daily_avg.index, daily_avg.values, alpha=0.3, color=color)
            ax.plot(daily_avg.index, daily_avg.values, color=color, linewidth=1.5, label=f"{label} 평균 트렌드")

            # 75th percentile 기준선
            threshold = daily_avg.quantile(0.75)
            ax.axhline(y=threshold, color="red", linewidth=1, linestyle="--", alpha=0.6, label=f"75th pctl ({threshold:.0f})")

            # 피크 구간 강조
            peak_periods = peak_results.get("results", {}).get(brand, [])
            for p in peak_periods:
                ax.axvspan(p["start"], p["end"], alpha=0.2, color="red", label=None)

            ax.set_ylabel("트렌드 지수")
            ax.set_title(f"{label}", fontsize=11, fontweight="bold")
            ax.legend(loc="upper right", fontsize=8)
            ax.grid(True, alpha=0.3)
            ax.set_ylim(0, 100)

        axes[-1].tick_params(axis="x", rotation=45)

        fig.suptitle("성수기 탐지 (트렌드 75th percentile 초과 구간)", fontsize=13, fontweight="bold", y=1.01)
        plt.tight_layout()
        path = OUTPUT_DIR / "trend_peak_season.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        logger.info(f"[트렌드] 성수기 차트 저장: {path}")
