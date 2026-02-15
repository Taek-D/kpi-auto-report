"""
매출 예측 모듈 (ML 기반 Demand Forecasting)
브랜드별 일일 매출을 학습하여 다음 7일 예측.
Feature Engineering + Random Forest + 교차 검증 + Feature Importance 분석.
(시뮬레이션 데이터 기반 — 실무 운영 데이터 투입 시 동일 파이프라인으로 예측 가능)
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
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import LabelEncoder

from .supabase_loader import SupabaseLoader

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).parent.parent / "output"

BRAND_LABELS = {"minix": "미닉스", "thome": "톰", "protione": "프로티원"}


def _setup_korean_font():
    font_candidates = ["Malgun Gothic", "NanumGothic", "AppleGothic", "DejaVu Sans"]
    available = {f.name for f in fm.fontManager.ttflist}
    for font_name in font_candidates:
        if font_name in available:
            plt.rcParams["font.family"] = font_name
            plt.rcParams["axes.unicode_minus"] = False
            return


_setup_korean_font()


class DemandForecaster:
    """브랜드별 매출 예측 모델

    파이프라인: 데이터 조회 → Feature Engineering → 학습/평가 → 예측 → 시각화
    모델: Random Forest Regressor (해석 가능성 + 비선형 패턴 학습)
    """

    def __init__(self):
        self.loader = SupabaseLoader()
        self.model = None
        self.le_brand = LabelEncoder()
        self.le_channel = LabelEncoder()
        self.feature_names = []

    def run(self) -> str:
        """전체 예측 파이프라인 실행"""
        raw_data = self.loader.fetch_brand_sales(days=60)
        if not raw_data:
            return "[예측] 데이터가 없습니다. Supabase 연결을 확인해주세요."

        df = pd.DataFrame(raw_data)
        df["sale_date"] = pd.to_datetime(df["sale_date"])
        for col in ["revenue", "orders", "ad_spend", "roas"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        lines = [
            "📈 매출 예측 분석 (ML Demand Forecasting)",
            "※ 시뮬레이션 데이터 기반 | 실무 운영 데이터 투입 시 동일 파이프라인 적용 가능",
            "=" * 60,
            "",
        ]

        # 1. 데이터 요약
        data_lines = self._data_summary(df)
        lines.extend(data_lines)

        # 2. Feature Engineering
        df_features = self._engineer_features(df)
        feat_lines = self._feature_summary(df_features)
        lines.extend(feat_lines)

        # 3. 학습 / 평가
        train_lines, df_pred = self._train_evaluate(df_features)
        lines.extend(train_lines)

        # 4. 브랜드별 예측 결과
        pred_lines = self._brand_predictions(df_features, df_pred)
        lines.extend(pred_lines)

        # 5. 시각화
        self._plot_actual_vs_predicted(df_pred)
        self._plot_feature_importance()
        lines.append("")
        lines.append("[차트] output/forecast_actual_vs_pred.png - 실제 vs 예측 매출 비교")
        lines.append("[차트] output/forecast_feature_importance.png - Feature Importance Top 10")

        return "\n".join(lines)

    def _data_summary(self, df: pd.DataFrame) -> list[str]:
        """데이터 요약"""
        lines = [
            "📋 데이터 요약",
            "━" * 50,
        ]
        date_min = df["sale_date"].min().strftime("%Y-%m-%d")
        date_max = df["sale_date"].max().strftime("%Y-%m-%d")
        n_days = df["sale_date"].nunique()
        n_brands = df["brand"].nunique()
        n_channels = df["channel"].nunique()

        lines.append(f"  기간: {date_min} ~ {date_max} ({n_days}일)")
        lines.append(f"  브랜드: {n_brands}개, 채널: {n_channels}개")
        lines.append(f"  총 레코드: {len(df):,}건")

        for brand in sorted(df["brand"].unique()):
            label = BRAND_LABELS.get(brand, brand)
            brand_rev = df[df["brand"] == brand]["revenue"].sum()
            lines.append(f"    {label}: 총 매출 ₩{brand_rev/10000:,.0f}만")

        lines.append("")
        return lines

    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Feature Engineering"""
        df = df.copy()

        # 시간 기반 features
        df["day_of_week"] = df["sale_date"].dt.dayofweek
        df["week_of_month"] = (df["sale_date"].dt.day - 1) // 7 + 1
        df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
        df["month"] = df["sale_date"].dt.month
        df["day_of_month"] = df["sale_date"].dt.day

        # 브랜드/채널 인코딩
        df["brand_enc"] = self.le_brand.fit_transform(df["brand"])
        df["channel_enc"] = self.le_channel.fit_transform(df["channel"])

        # Lag features (브랜드+채널 그룹별)
        df = df.sort_values(["brand", "channel", "sale_date"])
        for lag in [1, 7]:
            df[f"revenue_lag_{lag}d"] = (
                df.groupby(["brand", "channel"])["revenue"]
                .shift(lag)
            )

        # Rolling mean (7일 이동평균)
        df["revenue_rolling_7d"] = (
            df.groupby(["brand", "channel"])["revenue"]
            .transform(lambda x: x.rolling(7, min_periods=1).mean())
        )

        # 채널 ROAS를 feature로 활용
        df["roas_feature"] = df["roas"].fillna(0)

        # NaN 행 제거 (lag feature로 인한 첫 7일)
        df = df.dropna(subset=["revenue_lag_1d", "revenue_lag_7d"])

        return df

    def _feature_summary(self, df: pd.DataFrame) -> list[str]:
        """Feature Engineering 요약"""
        self.feature_names = [
            "day_of_week", "week_of_month", "is_weekend", "month", "day_of_month",
            "brand_enc", "channel_enc",
            "revenue_lag_1d", "revenue_lag_7d", "revenue_rolling_7d",
            "roas_feature",
        ]
        lines = [
            "⚙️ Feature Engineering",
            "━" * 50,
            f"  총 Features: {len(self.feature_names)}개",
            f"  학습 데이터: {len(df):,}건 (lag feature로 인한 초기 데이터 제외)",
            "",
            "  Feature 목록:",
            "    [시간] day_of_week, week_of_month, is_weekend, month, day_of_month",
            "    [범주] brand_enc, channel_enc",
            "    [Lag]  revenue_lag_1d(전일), revenue_lag_7d(전주 동일 요일)",
            "    [통계] revenue_rolling_7d(7일 이동평균)",
            "    [마케팅] roas_feature(광고 수익률)",
            "",
        ]
        return lines

    def _train_evaluate(self, df: pd.DataFrame) -> tuple[list[str], pd.DataFrame]:
        """모델 학습 및 평가"""
        lines = [
            "🤖 모델 학습 및 평가",
            "━" * 50,
        ]

        X = df[self.feature_names].values
        y = df["revenue"].values

        # 시계열 특성상 최근 7일을 테스트셋으로 분리
        dates = df["sale_date"].unique()
        dates_sorted = np.sort(dates)
        test_cutoff = dates_sorted[-7]  # 최근 7일

        train_mask = df["sale_date"] < test_cutoff
        test_mask = df["sale_date"] >= test_cutoff

        X_train, X_test = X[train_mask], X[test_mask]
        y_train, y_test = y[train_mask], y[test_mask]

        lines.append(f"  Train: {len(X_train):,}건 | Test: {len(X_test):,}건 (최근 7일)")
        lines.append(f"  모델: Random Forest Regressor")
        lines.append(f"    n_estimators=100, max_depth=10, min_samples_leaf=3")

        # 학습
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_leaf=3,
            random_state=42,
            n_jobs=-1,
        )
        self.model.fit(X_train, y_train)

        # 평가
        y_pred = self.model.predict(X_test)

        mae = mean_absolute_error(y_test, y_pred)
        rmse = math.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        mape = np.mean(np.abs((y_test - y_pred) / np.where(y_test == 0, 1, y_test))) * 100

        lines.append(f"\n  📊 Test Set 평가 지표")
        lines.append(f"    MAE:  ₩{mae:,.0f} (평균 절대 오차)")
        lines.append(f"    RMSE: ₩{rmse:,.0f} (평균 제곱근 오차)")
        lines.append(f"    R²:   {r2:.4f} (결정 계수)")
        lines.append(f"    MAPE: {mape:.1f}% (평균 절대 백분율 오차)")

        # 교차 검증 (시계열이므로 참고용)
        cv_scores = cross_val_score(
            RandomForestRegressor(n_estimators=100, max_depth=10, min_samples_leaf=3, random_state=42),
            X_train, y_train, cv=5, scoring="r2",
        )
        lines.append(f"\n  🔄 5-Fold Cross Validation (Train set)")
        lines.append(f"    R² 평균: {cv_scores.mean():.4f} (±{cv_scores.std():.4f})")
        lines.append(f"    각 fold: {', '.join(f'{s:.3f}' for s in cv_scores)}")

        # R² 해석
        if r2 >= 0.9:
            interpretation = "매우 우수 — 매출 변동의 90% 이상 설명"
        elif r2 >= 0.7:
            interpretation = "우수 — 주요 패턴 포착 성공"
        elif r2 >= 0.5:
            interpretation = "보통 — 기본 패턴은 학습, 추가 feature 필요"
        else:
            interpretation = "개선 필요 — 외부 요인(프로모션, 방송일) 변수 추가 권장"

        lines.append(f"\n  💡 모델 해석: {interpretation}")

        # Feature Importance
        importances = self.model.feature_importances_
        feat_imp = sorted(
            zip(self.feature_names, importances),
            key=lambda x: x[1],
            reverse=True,
        )

        lines.append(f"\n  🏆 Feature Importance Top 5")
        for fname, imp in feat_imp[:5]:
            bar = "█" * int(imp * 50)
            lines.append(f"    {fname:25s} {imp:.3f} {bar}")

        lines.append("")

        # 예측 결과 DataFrame
        df_test = df[test_mask].copy()
        df_test["predicted_revenue"] = y_pred

        return lines, df_test

    def _brand_predictions(self, df_full: pd.DataFrame, df_pred: pd.DataFrame) -> list[str]:
        """브랜드별 예측 결과 요약"""
        lines = [
            "📊 브랜드별 예측 결과 (테스트 기간)",
            "━" * 50,
        ]

        for brand in sorted(df_pred["brand"].unique()):
            label = BRAND_LABELS.get(brand, brand)
            brand_data = df_pred[df_pred["brand"] == brand]

            actual_total = brand_data["revenue"].sum()
            pred_total = brand_data["predicted_revenue"].sum()
            error_pct = abs(pred_total - actual_total) / actual_total * 100 if actual_total > 0 else 0

            lines.append(f"\n  [{label}]")
            lines.append(f"    실제 매출 합계:   ₩{actual_total/10000:,.0f}만")
            lines.append(f"    예측 매출 합계:   ₩{pred_total/10000:,.0f}만")
            lines.append(f"    오차율:           {error_pct:.1f}%")

            # 채널별 상세
            for channel in sorted(brand_data["channel"].unique()):
                ch_data = brand_data[brand_data["channel"] == channel]
                ch_actual = ch_data["revenue"].mean()
                ch_pred = ch_data["predicted_revenue"].mean()
                lines.append(
                    f"      {channel:12s} 실제 ₩{ch_actual/10000:,.1f}만/일 → 예측 ₩{ch_pred/10000:,.1f}만/일"
                )

        # 비즈니스 활용 제안
        lines.append(f"\n  💼 비즈니스 활용")
        lines.append(f"    1. 다음 주 예상 매출 기반 재고 발주량 사전 조정")
        lines.append(f"    2. 예측 대비 실적 하회 시 이상 탐지 (예측 기반 동적 임계값)")
        lines.append(f"    3. 채널별 예측 매출로 광고 예산 사전 배분 최적화")
        lines.append(f"    4. 실제 운영 시: 프로모션/방송일 feature 추가로 정확도 향상 가능")
        lines.append("")

        return lines

    def _plot_actual_vs_predicted(self, df_pred: pd.DataFrame) -> None:
        """실제 vs 예측 매출 비교 차트"""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        brands = sorted(df_pred["brand"].unique())
        fig, axes = plt.subplots(1, len(brands), figsize=(6 * len(brands), 5))
        if len(brands) == 1:
            axes = [axes]

        brand_colors = {"minix": "#FF6B35", "thome": "#4A90D9", "protione": "#7ED321"}

        for ax, brand in zip(axes, brands):
            label = BRAND_LABELS.get(brand, brand)
            brand_data = df_pred[df_pred["brand"] == brand]

            # 채널 합산 일별 매출
            daily = brand_data.groupby("sale_date").agg(
                actual=("revenue", "sum"),
                predicted=("predicted_revenue", "sum"),
            ).reset_index()

            color = brand_colors.get(brand, "#666")
            dates = daily["sale_date"]

            ax.bar(dates, daily["actual"] / 10000, alpha=0.6, color=color, label="실제", width=0.4)
            ax.plot(dates, daily["predicted"] / 10000, "o--", color="#E74C3C", label="예측", linewidth=2, markersize=8)

            ax.set_title(f"{label} 실제 vs 예측 매출", fontsize=12, fontweight="bold")
            ax.set_ylabel("매출 (만원)")
            ax.legend(fontsize=9)
            ax.tick_params(axis="x", rotation=45)
            ax.grid(True, axis="y", alpha=0.3)

        plt.tight_layout()
        path = OUTPUT_DIR / "forecast_actual_vs_pred.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        logger.info(f"[예측] 실제 vs 예측 차트 저장: {path}")

    def _plot_feature_importance(self) -> None:
        """Feature Importance 차트"""
        if self.model is None:
            return

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        importances = self.model.feature_importances_
        feat_imp = sorted(
            zip(self.feature_names, importances),
            key=lambda x: x[1],
            reverse=True,
        )[:10]

        names = [f[0] for f in feat_imp]
        values = [f[1] for f in feat_imp]

        # Feature 이름 한글 매핑
        name_map = {
            "revenue_lag_1d": "전일 매출",
            "revenue_lag_7d": "전주 동요일 매출",
            "revenue_rolling_7d": "7일 이동평균",
            "day_of_week": "요일",
            "channel_enc": "채널",
            "brand_enc": "브랜드",
            "is_weekend": "주말 여부",
            "week_of_month": "월 내 주차",
            "month": "월",
            "day_of_month": "일",
            "roas_feature": "ROAS",
        }
        display_names = [name_map.get(n, n) for n in names]

        fig, ax = plt.subplots(figsize=(10, 6))

        colors = ["#E74C3C" if v > 0.1 else "#3498DB" if v > 0.05 else "#95A5A6" for v in values]
        bars = ax.barh(range(len(names)), values, color=colors, edgecolor="white")

        ax.set_yticks(range(len(names)))
        ax.set_yticklabels(display_names, fontsize=11)
        ax.invert_yaxis()
        ax.set_xlabel("Importance", fontsize=11)
        ax.set_title("매출 예측 Feature Importance (Random Forest)", fontsize=13, fontweight="bold")

        # 값 표시
        for bar, val in zip(bars, values):
            ax.text(bar.get_width() + 0.005, bar.get_y() + bar.get_height() / 2,
                    f"{val:.3f}", va="center", fontsize=10)

        ax.grid(True, axis="x", alpha=0.3)

        plt.tight_layout()
        path = OUTPUT_DIR / "forecast_feature_importance.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        logger.info(f"[예측] Feature Importance 차트 저장: {path}")
