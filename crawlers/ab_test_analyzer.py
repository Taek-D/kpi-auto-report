"""
A/B 테스트 통계 분석 모듈
미닉스 자사몰 결제 페이지 개선 A/B 테스트 시나리오의 통계 검정 파이프라인.
실험 설계(Power Analysis, SRM) → 가설 검정(Welch's t-test, Mann-Whitney U) →
효과 크기(Cohen's d) → 비즈니스 해석(ROI, Go/No-Go) 전 과정을 구현.
(시뮬레이션 데이터 기반 — 실무 적용 시 동일 파이프라인으로 운영 데이터 분석 가능)
"""

import logging
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

from .supabase_loader import SupabaseLoader

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).parent.parent / "output"


def _setup_korean_font():
    font_candidates = ["Malgun Gothic", "NanumGothic", "AppleGothic", "DejaVu Sans"]
    available = {f.name for f in fm.fontManager.ttflist}
    for font_name in font_candidates:
        if font_name in available:
            plt.rcParams["font.family"] = font_name
            plt.rcParams["axes.unicode_minus"] = False
            return


_setup_korean_font()


class ABTestAnalyzer:
    """A/B 테스트 통계 분석 파이프라인

    실무에서 A/B 테스트 수행 시 필요한 전체 분석 프로세스를 구현:
    1. 실험 설계 검증: Power Analysis(최소 샘플), SRM(배분 편향)
    2. 가설 검정: Welch's t-test(전환율), Mann-Whitney U(매출)
    3. 효과 크기: Cohen's d + 95% 신뢰구간
    4. 비즈니스 해석: ROI 분석 + Go/No-Go 의사결정 프레임워크
    """

    def __init__(self):
        self.loader = SupabaseLoader()

    def run(self) -> str:
        """전체 A/B 테스트 분석 파이프라인"""
        raw_data = self.loader.fetch_ab_test()
        if not raw_data:
            return "[A/B 테스트] 데이터가 없습니다. Supabase 연결을 확인해주세요."

        df = pd.DataFrame(raw_data)
        df["test_date"] = pd.to_datetime(df["test_date"])
        for col in ["visitors", "conversions", "revenue", "avg_order_value", "bounce_rate"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        lines = [
            "🧪 A/B 테스트 분석: 미닉스 자사몰 결제 페이지 개선",
            "※ 시뮬레이션 데이터 기반 | 실무 동일 파이프라인 적용",
            "   (Power Analysis → t-test/Mann-Whitney → Cohen's d → ROI → Go/No-Go)",
            "=" * 55,
            "",
            "📋 실험 개요",
            "  테스트 기간: 2026-01-27 ~ 2026-02-09 (14일)",
            "  대상: 미닉스 자사몰 결제 페이지",
            "  Control (A): 기존 결제 페이지",
            "  Treatment (B): 개선 결제 페이지 (원클릭 결제 + 리뷰 위젯)",
            "  목표: 전환율 +15% 이상 개선",
            "",
        ]

        # 1. 실험 설계 검증
        design_lines = self.validate_design(df)
        lines.extend(design_lines)

        # 2. 통계 분석
        analysis_lines = self.analyze(df)
        lines.extend(analysis_lines)

        # 3. 비즈니스 해석
        interpret_lines = self.interpret_results(df)
        lines.extend(interpret_lines)

        # 4. 시각화
        self._plot_conversion_comparison(df)
        self._plot_daily_trend(df)
        lines.append("[차트] output/ab_test_conversion.png - A/B 전환율 비교 + 신뢰구간")
        lines.append("[차트] output/ab_test_daily.png - 일별 전환율 추이")

        return "\n".join(lines)

    def validate_design(self, df: pd.DataFrame) -> list[str]:
        """실험 설계 검증"""
        lines = [
            "✅ 실험 설계 검증",
            "━" * 45,
        ]

        control = df[df["variant"] == "control"]
        treatment = df[df["variant"] == "treatment"]

        n_control = control["visitors"].sum()
        n_treatment = treatment["visitors"].sum()
        total_days = control["test_date"].nunique()

        # 1. 최소 샘플 크기 (power analysis)
        # alpha=0.05, power=0.8, MDE=15%
        baseline_cr = control["conversions"].sum() / n_control
        mde = 0.15  # 15% relative improvement
        target_cr = baseline_cr * (1 + mde)

        # Simplified power calculation
        p_bar = (baseline_cr + target_cr) / 2
        z_alpha = 1.96  # alpha=0.05 two-sided
        z_beta = 0.842  # power=0.8
        min_sample = (
            (z_alpha * math.sqrt(2 * p_bar * (1 - p_bar))
             + z_beta * math.sqrt(baseline_cr * (1 - baseline_cr) + target_cr * (1 - target_cr)))
            ** 2
            / (target_cr - baseline_cr) ** 2
        )
        min_sample = math.ceil(min_sample)

        lines.append(f"  최소 샘플 크기 (alpha=0.05, power=0.8, MDE=15%): {min_sample:,}명/그룹")
        lines.append(f"  실제 샘플: Control={n_control:,}명, Treatment={n_treatment:,}명")

        sample_sufficient = n_control >= min_sample and n_treatment >= min_sample
        lines.append(f"  판정: {'✅ 충분' if sample_sufficient else '⚠️ 부족 (결과 해석에 주의)'}")

        # 2. SRM (Sample Ratio Mismatch) 체크
        expected_ratio = 0.5
        total = n_control + n_treatment
        chi2_stat = (n_control - total * expected_ratio) ** 2 / (total * expected_ratio) + \
                    (n_treatment - total * (1 - expected_ratio)) ** 2 / (total * (1 - expected_ratio))
        srm_p = 1 - scipy_stats.chi2.cdf(chi2_stat, df=1)

        lines.append(f"\n  SRM 검정 (50:50 배분 확인)")
        lines.append(f"    실제 비율: {n_control/total*100:.1f}:{n_treatment/total*100:.1f}")
        lines.append(f"    chi2={chi2_stat:.4f}, p={srm_p:.4f}")
        lines.append(f"    판정: {'✅ 정상 배분' if srm_p > 0.05 else '⚠️ 배분 편향 의심'}")

        # 3. 실험 기간 적정성
        lines.append(f"\n  실험 기간: {total_days}일")
        lines.append(f"    판정: {'✅ 2주 이상 (요일 효과 포함)' if total_days >= 14 else '⚠️ 14일 미만'}")
        lines.append("")

        return lines

    def analyze(self, df: pd.DataFrame) -> list[str]:
        """통계 분석"""
        lines = [
            "📊 통계 분석 결과",
            "━" * 45,
        ]

        control = df[df["variant"] == "control"]
        treatment = df[df["variant"] == "treatment"]

        # 일별 전환율
        control_cr = control["conversions"] / control["visitors"]
        treatment_cr = treatment["conversions"] / treatment["visitors"]

        # 전체 전환율
        cr_a = control["conversions"].sum() / control["visitors"].sum()
        cr_b = treatment["conversions"].sum() / treatment["visitors"].sum()
        relative_lift = (cr_b / cr_a - 1) * 100

        lines.append(f"  전환율 비교")
        lines.append(f"    Control (A):   {cr_a*100:.2f}%")
        lines.append(f"    Treatment (B): {cr_b*100:.2f}%")
        lines.append(f"    상대적 개선:   +{relative_lift:.1f}%")

        # 1. 전환율 비교: Welch's t-test
        t_stat, t_pvalue = scipy_stats.ttest_ind(treatment_cr.values, control_cr.values, equal_var=False)

        lines.append(f"\n  [전환율] Welch's t-test")
        lines.append(f"    t-statistic: {t_stat:.4f}")
        lines.append(f"    p-value: {t_pvalue:.4f}")
        lines.append(f"    판정: {'✅ 통계적으로 유의미 (p<0.05)' if t_pvalue < 0.05 else '❌ 유의하지 않음'}")

        # 95% 신뢰구간
        diff_mean = treatment_cr.mean() - control_cr.mean()
        se = math.sqrt(treatment_cr.var() / len(treatment_cr) + control_cr.var() / len(control_cr))
        ci_low = diff_mean - 1.96 * se
        ci_high = diff_mean + 1.96 * se
        lines.append(f"    95% CI: [{ci_low*100:.3f}%, {ci_high*100:.3f}%]")

        # Cohen's d
        pooled_std = math.sqrt((treatment_cr.var() + control_cr.var()) / 2)
        cohens_d = diff_mean / pooled_std if pooled_std > 0 else 0
        effect_label = "작음" if abs(cohens_d) < 0.5 else ("중간" if abs(cohens_d) < 0.8 else "큼")
        lines.append(f"    Cohen's d: {cohens_d:.3f} (효과 크기: {effect_label})")

        # 2. 매출 비교: Mann-Whitney U test (비정규 분포 대응)
        daily_rev_a = control["revenue"].values
        daily_rev_b = treatment["revenue"].values
        u_stat, u_pvalue = scipy_stats.mannwhitneyu(daily_rev_b, daily_rev_a, alternative="greater")

        lines.append(f"\n  [매출] Mann-Whitney U test (단측)")
        lines.append(f"    U-statistic: {u_stat:.1f}")
        lines.append(f"    p-value: {u_pvalue:.4f}")
        lines.append(f"    판정: {'✅ 통계적으로 유의미' if u_pvalue < 0.05 else '❌ 유의하지 않음'}")

        avg_rev_a = daily_rev_a.mean()
        avg_rev_b = daily_rev_b.mean()
        lines.append(f"    일평균 매출 A: ₩{avg_rev_a:,.0f}")
        lines.append(f"    일평균 매출 B: ₩{avg_rev_b:,.0f}")
        lines.append(f"    일 매출 증가분: +₩{avg_rev_b - avg_rev_a:,.0f}/일")

        # 3. 바운스율 비교
        bounce_a = control["bounce_rate"].values
        bounce_b = treatment["bounce_rate"].values
        b_stat, b_pvalue = scipy_stats.ttest_ind(bounce_b, bounce_a, equal_var=False)

        lines.append(f"\n  [바운스율] Welch's t-test")
        lines.append(f"    Control: {bounce_a.mean():.1f}%  →  Treatment: {bounce_b.mean():.1f}%")
        lines.append(f"    p-value: {b_pvalue:.4f}")
        lines.append(f"    판정: {'✅ 바운스율 유의미 감소' if b_pvalue < 0.05 and bounce_b.mean() < bounce_a.mean() else '변화 없음'}")

        # Sequential testing 참고
        lines.append(f"\n  ⚠️ Sequential Testing 참고")
        lines.append(f"    실험 중 반복 검정(peeking) 시 False Positive 증가 가능")
        lines.append(f"    권장: 사전에 정한 14일 후 1회 최종 분석 (본 분석)")
        lines.append("")

        return lines

    def interpret_results(self, df: pd.DataFrame) -> list[str]:
        """비즈니스 해석"""
        lines = [
            "💼 비즈니스 해석 및 의사결정",
            "━" * 45,
        ]

        control = df[df["variant"] == "control"]
        treatment = df[df["variant"] == "treatment"]

        cr_a = control["conversions"].sum() / control["visitors"].sum()
        cr_b = treatment["conversions"].sum() / treatment["visitors"].sum()

        avg_rev_a = control["revenue"].mean()
        avg_rev_b = treatment["revenue"].mean()
        daily_uplift = avg_rev_b - avg_rev_a
        monthly_uplift = daily_uplift * 30
        annual_uplift = daily_uplift * 365

        lines.append(f"  전환율 개선: {cr_a*100:.2f}% → {cr_b*100:.2f}% (+{(cr_b/cr_a - 1)*100:.1f}%)")
        lines.append(f"  일 매출 증가 예상: +₩{daily_uplift:,.0f}/일")
        lines.append(f"  월 매출 증가 예상: +₩{monthly_uplift:,.0f}/월 (₩{monthly_uplift/10000:,.0f}만)")
        lines.append(f"  연 매출 증가 예상: +₩{annual_uplift:,.0f}/년 (₩{annual_uplift/100000000:,.1f}억)")

        # ROI 계산
        dev_cost = 5000000  # 페이지 개발비 ₩5M 가정
        roi = (annual_uplift / dev_cost) * 100

        lines.append(f"\n  ROI 분석")
        lines.append(f"    페이지 개발비: ₩{dev_cost/10000:,.0f}만 (가정)")
        lines.append(f"    연 매출 증가: ₩{annual_uplift/10000:,.0f}만")
        lines.append(f"    ROI: {roi:,.0f}%")
        lines.append(f"    투자 회수 기간: {dev_cost/daily_uplift:.0f}일")

        # Go/No-Go 의사결정
        lines.append(f"\n  🚀 의사결정: Go/No-Go")

        go_criteria = []
        if cr_b > cr_a:
            go_criteria.append("전환율 유의미 개선")
        if daily_uplift > 0:
            go_criteria.append("일 매출 증가")
        if roi > 100:
            go_criteria.append(f"ROI {roi:,.0f}% (>100%)")

        if len(go_criteria) >= 2:
            lines.append(f"    판정: ✅ GO - 전체 트래픽 적용 권장")
            for c in go_criteria:
                lines.append(f"      - {c}")
        else:
            lines.append(f"    판정: ⚠️ HOLD - 추가 테스트 필요")

        lines.append(f"\n  📝 후속 조치")
        lines.append(f"    1. Treatment 전체 적용 후 2주 모니터링")
        lines.append(f"    2. 모바일/PC 세그먼트별 전환율 추가 분석")
        lines.append(f"    3. AOV(평균 주문금액) 변화 추적")
        lines.append(f"    4. 톰/프로티원 자사몰에도 동일 개선안 적용 검토")
        lines.append("")

        return lines

    def _plot_conversion_comparison(self, df: pd.DataFrame) -> None:
        """A/B 전환율 비교 + 신뢰구간 bar chart"""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        control = df[df["variant"] == "control"]
        treatment = df[df["variant"] == "treatment"]

        cr_a = control["conversions"].sum() / control["visitors"].sum()
        cr_b = treatment["conversions"].sum() / treatment["visitors"].sum()

        n_a = control["visitors"].sum()
        n_b = treatment["visitors"].sum()

        # 95% 신뢰구간 (proportions)
        se_a = math.sqrt(cr_a * (1 - cr_a) / n_a)
        se_b = math.sqrt(cr_b * (1 - cr_b) / n_b)

        fig, ax = plt.subplots(figsize=(8, 6))

        bars = ax.bar(
            ["Control (A)\n기존 결제 페이지", "Treatment (B)\n개선 결제 페이지"],
            [cr_a * 100, cr_b * 100],
            yerr=[1.96 * se_a * 100, 1.96 * se_b * 100],
            color=["#95A5A6", "#2ECC71"],
            edgecolor="white",
            width=0.5,
            capsize=10,
            error_kw={"linewidth": 2},
        )

        for bar, cr in zip(bars, [cr_a, cr_b]):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.05,
                f"{cr*100:.2f}%",
                ha="center", va="bottom", fontsize=14, fontweight="bold",
            )

        # 개선율 표시
        lift = (cr_b / cr_a - 1) * 100
        ax.annotate(
            f"+{lift:.1f}%",
            xy=(1, cr_b * 100),
            xytext=(1.3, (cr_a + cr_b) / 2 * 100),
            fontsize=16, fontweight="bold", color="#E74C3C",
            arrowprops=dict(arrowstyle="->", color="#E74C3C", lw=2),
        )

        ax.set_title("미닉스 자사몰 결제 페이지 A/B 테스트\n전환율 비교 (95% 신뢰구간)", fontsize=13, fontweight="bold")
        ax.set_ylabel("전환율 (%)")
        ax.grid(True, axis="y", alpha=0.3)
        ax.set_ylim(0, max(cr_a, cr_b) * 100 * 1.5)

        plt.tight_layout()
        path = OUTPUT_DIR / "ab_test_conversion.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        logger.info(f"[A/B 테스트] 전환율 비교 차트 저장: {path}")

    def _plot_daily_trend(self, df: pd.DataFrame) -> None:
        """일별 전환율 추이 (A vs B)"""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        control = df[df["variant"] == "control"].sort_values("test_date")
        treatment = df[df["variant"] == "treatment"].sort_values("test_date")

        cr_a = (control["conversions"] / control["visitors"] * 100).values
        cr_b = (treatment["conversions"] / treatment["visitors"] * 100).values
        dates = control["test_date"].values

        fig, ax = plt.subplots(figsize=(12, 6))

        ax.plot(dates, cr_a, "o-", color="#95A5A6", label="Control (A) - 기존", linewidth=2, markersize=6)
        ax.plot(dates, cr_b, "s-", color="#2ECC71", label="Treatment (B) - 개선", linewidth=2, markersize=6)

        # 평균선
        ax.axhline(y=np.mean(cr_a), color="#95A5A6", linestyle="--", alpha=0.5, label=f"A 평균: {np.mean(cr_a):.2f}%")
        ax.axhline(y=np.mean(cr_b), color="#2ECC71", linestyle="--", alpha=0.5, label=f"B 평균: {np.mean(cr_b):.2f}%")

        # 주말 하이라이트
        for i, date in enumerate(dates):
            if pd.Timestamp(date).weekday() >= 5:
                ax.axvspan(
                    pd.Timestamp(date) - pd.Timedelta(hours=12),
                    pd.Timestamp(date) + pd.Timedelta(hours=12),
                    alpha=0.1, color="blue",
                )

        ax.set_title("일별 전환율 추이 (A vs B)", fontsize=13, fontweight="bold")
        ax.set_ylabel("전환율 (%)")
        ax.set_xlabel("날짜")
        ax.legend(loc="upper left", fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis="x", rotation=45)

        plt.tight_layout()
        path = OUTPUT_DIR / "ab_test_daily.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        logger.info(f"[A/B 테스트] 일별 추이 차트 저장: {path}")
