"""
ml_forecasting_engine.py

Phase 11 — ML-Based Enrolment Forecasting Engine

Replaces Phase 10's weighted moving-average with a Gradient Boosting
model trained across ALL ~67 k schools simultaneously.

WHY ML OVER PER-SCHOOL ARIMA
─────────────────────────────
With only 7 annual data points per school, a per-school ARIMA(1,1,0)
is essentially computing a differenced trend line — barely better than
a moving average.  A cross-school Gradient Boosting model, by contrast,
trains on ~300 k+ samples and can learn:
  • District-level demographic shifts
  • Management-type effects on retention
  • Non-linear interactions (gaps × school-type → enrolment change)
  • Momentum / mean-reversion patterns across the full panel

PREDICTION TARGET
─────────────────
The model predicts the GROWTH RATE  (next_year − current) / current ,
clipped to [−0.30, +0.30]  (same cap Phase 10 uses).

Projection then follows Phase 10's compound formula:
    projected_T+k = base_enrolment × (1 + g_ml)^k

This avoids autoregressive divergence — a single growth prediction
is compounded for T+1, T+2, T+3 just like the WMA.

Creates and populates:
  - ml_enrolment_forecast : ML-projected enrolment + gaps for T+1..T+3

Prerequisites: Phases 1–4 must be complete (gap & risk columns populated).
Idempotent — safe to re-run.  Deterministic (random_state = 42).
"""

import os
import sys
import time
import warnings

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, r2_score

warnings.filterwarnings("ignore")

# ═══════════════════════════════════════════════════════════════════════════
# 1.  TABLE DDL
# ═══════════════════════════════════════════════════════════════════════════

CREATE_TABLE_SQL = text("""
    CREATE TABLE IF NOT EXISTS ml_enrolment_forecast (
        id                         INT AUTO_INCREMENT PRIMARY KEY,
        school_id                  VARCHAR(50)  NOT NULL,
        base_year                  VARCHAR(20)  NOT NULL,
        forecast_year              VARCHAR(20)  NOT NULL,
        years_ahead                INT,
        base_enrolment             INT,
        ml_growth_rate             FLOAT,
        projected_enrolment        INT,
        projected_classrooms_req   INT,
        projected_teachers_req     INT,
        current_classrooms         INT,
        current_teachers           INT,
        projected_classroom_gap    INT,
        projected_teacher_gap      INT,
        school_category            INT,
        model_version              VARCHAR(20)  DEFAULT 'v1.0'
    )
""")

INDEX_STMTS = [
    ("idx_ml_fc_school",
     "CREATE INDEX idx_ml_fc_school "
     "ON ml_enrolment_forecast (school_id, base_year)"),
    ("idx_ml_fc_year",
     "CREATE INDEX idx_ml_fc_year "
     "ON ml_enrolment_forecast (forecast_year, years_ahead)"),
]

# ═══════════════════════════════════════════════════════════════════════════
# 2.  DATA EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════

EXTRACT_SQL = text("""
    SELECT
        y.school_id,
        y.academic_year,
        y.total_enrolment,
        CAST(s.school_category AS UNSIGNED)      AS school_category,
        s.district,
        s.management_type,
        IFNULL(i.total_class_rooms, 0)           AS total_class_rooms,
        IFNULL(i.usable_class_rooms, 0)          AS usable_class_rooms,
        IFNULL(i.classroom_gap, 0)               AS classroom_gap,
        IFNULL(i.risk_score, 0)                  AS risk_score,
        IFNULL(i.teacher_deficit_ratio, 0)       AS teacher_deficit_ratio,
        IFNULL(i.classroom_deficit_ratio, 0)     AS classroom_deficit_ratio,
        IFNULL(t.total_teachers, 0)              AS total_teachers,
        IFNULL(t.teacher_gap, 0)                 AS teacher_gap
    FROM yearly_metrics y
    JOIN schools s
        ON y.school_id = s.school_id
    LEFT JOIN infrastructure_details i
        ON y.school_id = i.school_id AND y.academic_year = i.academic_year
    LEFT JOIN teacher_metrics t
        ON y.school_id = t.school_id AND y.academic_year = t.academic_year
    ORDER BY y.school_id, y.academic_year
""")

P10_STATS_SQL = text("""
    SELECT
        years_ahead,
        SUM(projected_classroom_gap)  AS cr_gap,
        SUM(projected_teacher_gap)    AS tr_gap,
        ROUND(AVG(avg_growth_rate), 4) AS mean_growth
    FROM enrolment_forecast
    GROUP BY years_ahead
    ORDER BY years_ahead
""")

# ═══════════════════════════════════════════════════════════════════════════
# 3.  FEATURES
# ═══════════════════════════════════════════════════════════════════════════

GROWTH_CAP = 0.30          # same cap as Phase 10
MIN_ENROL_TRAIN = 10       # exclude tiny schools from training

FEATURE_COLS = [
    "total_enrolment",
    "enrolment_lag1",
    "enrolment_lag2",
    "growth_rate",
    "growth_rate_lag1",
    "school_category",
    "total_teachers",
    "total_class_rooms",
    "usable_class_rooms",
    "classroom_gap",
    "teacher_gap",
    "risk_score",
    "teacher_deficit_ratio",
    "classroom_deficit_ratio",
    "district_code",
    "management_code",
    "enrolment_3yr_mean",
    "enrolment_volatility",
    "teacher_per_student",
    "rooms_per_student",
]


def build_features(df):
    """Engineer features + growth-rate target from the raw panel."""
    df = df.sort_values(["school_id", "academic_year"]).copy()

    df["school_category"] = (
        pd.to_numeric(df["school_category"], errors="coerce")
        .fillna(6).astype(int)
    )

    grp = df.groupby("school_id", sort=False)

    # ── Lag enrolments ───────────────────────────────────────────────
    df["enrolment_lag1"] = grp["total_enrolment"].shift(1)
    df["enrolment_lag2"] = grp["total_enrolment"].shift(2)
    df["enrolment_lag3"] = grp["total_enrolment"].shift(3)

    # ── Growth rates (clipped to ± cap so features stay in-range) ────
    safe_lag1 = df["enrolment_lag1"].clip(lower=1)
    df["growth_rate"]      = ((df["total_enrolment"] - df["enrolment_lag1"]) / safe_lag1).clip(-GROWTH_CAP, GROWTH_CAP)
    df["growth_rate_lag1"] = grp["growth_rate"].shift(1).clip(-GROWTH_CAP, GROWTH_CAP)

    # ── WMA growth (Phase 10 replica — baseline comparison) ──────────
    d1 = df["total_enrolment"] - df["enrolment_lag1"]
    d2 = df["enrolment_lag1"]  - df["enrolment_lag2"]
    d3 = df["enrolment_lag2"]  - df["enrolment_lag3"]
    df["wma_growth"] = (
        (3 * d1.fillna(0) + 2 * d2.fillna(0) + d3.fillna(0))
        / (6 * safe_lag1)
    ).clip(-GROWTH_CAP, GROWTH_CAP)

    # ── Rolling stats ────────────────────────────────────────────────
    df["enrolment_3yr_mean"] = grp["total_enrolment"].transform(
        lambda x: x.rolling(3, min_periods=1).mean()
    )
    df["enrolment_volatility"] = (
        grp["total_enrolment"]
        .transform(lambda x: x.rolling(3, min_periods=2).std())
        .fillna(0)
    ).clip(upper=500)   # cap volatility to prevent extreme feature values

    # ── Ratio features ───────────────────────────────────────────────
    safe_enrl = df["total_enrolment"].clip(lower=1)
    df["teacher_per_student"] = df["total_teachers"]      / safe_enrl
    df["rooms_per_student"]   = df["usable_class_rooms"]  / safe_enrl

    # ── Encode categoricals ──────────────────────────────────────────
    le_dist = LabelEncoder()
    le_mgmt = LabelEncoder()
    df["district_code"]   = le_dist.fit_transform(df["district"].fillna("UNK").astype(str))
    df["management_code"] = le_mgmt.fit_transform(df["management_type"].fillna("UNK").astype(str))

    # ── Target: clipped growth rate  ─────────────────────────────────
    next_enrl = grp["total_enrolment"].shift(-1)
    df["target_growth"] = ((next_enrl - df["total_enrolment"]) / safe_enrl).clip(
        -GROWTH_CAP, GROWTH_CAP
    )

    # keep raw next-year enrolment for MAE evaluation
    df["target_enrolment"] = next_enrl

    # ── Fill NaN in feature columns ──────────────────────────────────
    for col in FEATURE_COLS:
        df[col] = df[col].fillna(0)

    return df, le_dist, le_mgmt


# ═══════════════════════════════════════════════════════════════════════════
# 4.  NORM HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def _norms(cats):
    c = np.asarray(cats, dtype=int)
    cr = np.where(np.isin(c, [1,2,3]), 30, np.where(np.isin(c, [4,5]), 35, 40))
    ptr = np.where(np.isin(c, [1,2,3,4,5]), 30, 35)
    return cr, ptr

def _fy(base, k):
    p = base.split("-")
    return f"{int(p[0])+k}-{int(p[1])+k:02d}"


# ═══════════════════════════════════════════════════════════════════════════
# 5.  MAIN ENGINE
# ═══════════════════════════════════════════════════════════════════════════

def run():
    load_dotenv()
    DB = os.getenv("DATABASE_URL")
    if not DB:
        print("ERROR  DATABASE_URL not found"); sys.exit(1)

    eng = create_engine(DB, echo=False, pool_recycle=280, pool_pre_ping=True,
                        connect_args={"connect_timeout": 30})
    SEP = "=" * 65

    # ── 1 ── Table + indexes ─────────────────────────────────────────
    print("Step 1/8 — Ensuring table + indexes …")
    with eng.begin() as c:
        c.execute(CREATE_TABLE_SQL)
    for nm, ddl in INDEX_STMTS:
        try:
            with eng.begin() as c: c.execute(text(ddl))
            print(f"  {nm} created.")
        except Exception:
            print(f"  {nm} exists.")
    print()

    # ── 2 ── Extract ─────────────────────────────────────────────────
    print("Step 2/8 — Pulling data from DB …")
    t0 = time.time()
    with eng.connect() as c:
        raw = pd.read_sql(EXTRACT_SQL, c)
    yrs = sorted(raw["academic_year"].unique())
    print(f"  {len(raw):,} rows | {raw['school_id'].nunique():,} schools | {len(yrs)} years")
    print(f"  Extracted in {time.time()-t0:.1f}s\n")

    # ── 3 ── Features ────────────────────────────────────────────────
    print("Step 3/8 — Engineering 20 features …")
    df, _, _ = build_features(raw)
    vg = df["target_growth"].dropna()
    print(f"  Target growth-rate (clipped ±{GROWTH_CAP}):")
    print(f"    mean={vg.mean():.4f}  median={vg.median():.4f}  "
          f"std={vg.std():.4f}  [p5={vg.quantile(.05):.3f}  "
          f"p95={vg.quantile(.95):.3f}]\n")

    # ── 4 ── Split ───────────────────────────────────────────────────
    latest = yrs[-1]
    test_src = yrs[-2]

    has_target = df[df["target_growth"].notna()].copy()
    # Filter small schools from training (too noisy)
    trainable = has_target[
        (has_target["academic_year"] != test_src)
        & (has_target["total_enrolment"] >= MIN_ENROL_TRAIN)
    ]
    testable = has_target[has_target["academic_year"] == test_src]

    X_tr = trainable[FEATURE_COLS].values.astype(np.float64)
    y_tr = trainable["target_growth"].values.astype(np.float64)
    X_te = testable[FEATURE_COLS].values.astype(np.float64)
    y_te_growth  = testable["target_growth"].values.astype(np.float64)
    y_te_actual  = testable["target_enrolment"].values.astype(np.float64)
    y_te_current = testable["total_enrolment"].values.astype(np.float64)

    print(f"Step 4/8 — Temporal split")
    print(f"  Train : {len(X_tr):>9,} (enrolment ≥ {MIN_ENROL_TRAIN})")
    print(f"  Test  : {len(X_te):>9,} ({test_src} → {latest})\n")

    # ── 5 ── Train ───────────────────────────────────────────────────
    print("Step 5/8 — Training GradientBoostingRegressor (huber loss) …")
    model = GradientBoostingRegressor(
        loss="huber",               # robust to outlier growth rates
        n_estimators=500,
        max_depth=4,
        learning_rate=0.03,
        subsample=0.8,
        min_samples_leaf=100,
        random_state=42,
        validation_fraction=0.1,
        n_iter_no_change=30,
        tol=1e-5,
    )
    t0 = time.time()
    model.fit(X_tr, y_tr)
    n_trees = model.n_estimators_
    print(f"  {n_trees} trees in {time.time()-t0:.1f}s\n")

    # ── 6 ── Evaluate ────────────────────────────────────────────────
    print("Step 6/8 — Evaluation")

    # ML growth predictions on test set
    g_ml = model.predict(X_te).clip(-GROWTH_CAP, GROWTH_CAP)
    enrl_ml = np.maximum(0, np.round(y_te_current * (1 + g_ml)))

    # Phase-10 WMA baseline
    g_wma = testable["wma_growth"].fillna(0).clip(-GROWTH_CAP, GROWTH_CAP).values
    enrl_wma = np.maximum(0, np.round(y_te_current * (1 + g_wma)))

    # Growth-rate metrics
    gr_r2_ml  = r2_score(y_te_growth, g_ml)
    gr_mae_ml = mean_absolute_error(y_te_growth, g_ml)
    gr_r2_wma = r2_score(y_te_growth, g_wma.clip(-GROWTH_CAP, GROWTH_CAP))
    gr_mae_wma= mean_absolute_error(y_te_growth, g_wma.clip(-GROWTH_CAP, GROWTH_CAP))

    # Enrolment metrics
    em_r2_ml  = r2_score(y_te_actual, enrl_ml)
    em_mae_ml = mean_absolute_error(y_te_actual, enrl_ml)
    em_mape_ml= np.mean(np.abs((y_te_actual - enrl_ml) / np.clip(y_te_actual, 1, None))) * 100
    em_r2_wma = r2_score(y_te_actual, enrl_wma)
    em_mae_wma= mean_absolute_error(y_te_actual, enrl_wma)
    em_mape_wma=np.mean(np.abs((y_te_actual - enrl_wma) / np.clip(y_te_actual, 1, None))) * 100

    tr_pred = model.predict(X_tr).clip(-GROWTH_CAP, GROWTH_CAP)
    gr_r2_train = r2_score(y_tr, tr_pred)

    print()
    print(f"  {'Metric':<30} {'ML (GBR)':>12}  {'Phase10 (WMA)':>14}")
    print(f"  {'-'*30} {'-'*12}  {'-'*14}")
    print(f"  {'Growth R² (test)':<30} {gr_r2_ml:>12.6f}  {gr_r2_wma:>14.6f}")
    print(f"  {'Growth MAE (test)':<30} {gr_mae_ml:>12.6f}  {gr_mae_wma:>14.6f}")
    print(f"  {'Enrolment R² (test)':<30} {em_r2_ml:>12.6f}  {em_r2_wma:>14.6f}")
    print(f"  {'Enrolment MAE (test)':<30} {em_mae_ml:>12,.0f}  {em_mae_wma:>14,.0f}")
    print(f"  {'Enrolment MAPE (test)':<30} {em_mape_ml:>11.2f}%  {em_mape_wma:>13.2f}%")
    print(f"  {'Growth R² (train)':<30} {gr_r2_train:>12.6f}")

    d_mae  = (em_mae_wma - em_mae_ml) / em_mae_wma * 100
    d_mape = (em_mape_wma - em_mape_ml) / em_mape_wma * 100
    a1 = "▼ better" if d_mae  > 0 else "▲ worse "
    a2 = "▼ better" if d_mape > 0 else "▲ worse "
    print(f"\n  ML vs Phase 10:")
    print(f"    MAE  {a1}  {d_mae:+.2f}%")
    print(f"    MAPE {a2}  {d_mape:+.2f}%")

    # Feature importance
    print(f"\n  Feature importance (top 10):")
    imp = model.feature_importances_
    for f, v in sorted(zip(FEATURE_COLS, imp), key=lambda x: -x[1])[:10]:
        print(f"    {f:<25} {v:.4f}  {'█'*int(v*60)}")
    print()

    # ── 7 ── Forecast T+1, T+2, T+3  (compound, no autoregression) ──
    print(f"Step 7/8 — Compound forecast from {latest} …")
    df_base = df[df["academic_year"] == latest].copy().reset_index(drop=True)
    n = len(df_base)
    base_e = df_base["total_enrolment"].values.astype(np.float64)
    cr_norm, ptr_norm = _norms(df_base["school_category"].values)

    # One growth prediction per school — then compound
    X_base = df_base[FEATURE_COLS].values.astype(np.float64)
    g_pred_raw = model.predict(X_base)
    # ── Bias calibration: shift predictions so mean matches training mean ──
    train_mean = float(np.mean(y_tr))
    pred_bias  = float(np.mean(g_pred_raw)) - train_mean
    g_pred = (g_pred_raw - pred_bias).clip(-GROWTH_CAP, GROWTH_CAP)
    print(f"  Bias correction: pred_mean {np.mean(g_pred_raw):+.4f} → "
          f"{np.mean(g_pred):+.4f}  (shift {-pred_bias:+.4f})")

    all_rows = []
    for k in [1, 2, 3]:
        proj = np.maximum(0, np.round(base_e * np.power(1 + g_pred, k))).astype(int)
        cr_req = np.ceil(proj / cr_norm).astype(int)
        tr_req = np.ceil(proj / ptr_norm).astype(int)
        cr_gap = np.maximum(0, cr_req - df_base["usable_class_rooms"].values)
        tr_gap = np.maximum(0, tr_req - df_base["total_teachers"].values)
        fy = _fy(latest, k)

        sid = df_base["school_id"].values
        ucr = df_base["usable_class_rooms"].values
        tt  = df_base["total_teachers"].values
        cat = df_base["school_category"].values

        for i in range(n):
            all_rows.append({
                "school_id":                str(sid[i]),
                "base_year":                latest,
                "forecast_year":            fy,
                "years_ahead":              k,
                "base_enrolment":           int(base_e[i]),
                "ml_growth_rate":           float(g_pred[i]),
                "projected_enrolment":      int(proj[i]),
                "projected_classrooms_req": int(cr_req[i]),
                "projected_teachers_req":   int(tr_req[i]),
                "current_classrooms":       int(ucr[i]),
                "current_teachers":         int(tt[i]),
                "projected_classroom_gap":  int(cr_gap[i]),
                "projected_teacher_gap":    int(tr_gap[i]),
                "school_category":          int(cat[i]),
                "model_version":            "v1.0",
            })

    df_out = pd.DataFrame(all_rows)
    print(f"  {len(df_out):,} rows ({n:,} schools × 3 horizons)\n")

    # ── 8 ── Write ───────────────────────────────────────────────────
    print("Step 8/8 — Writing to database …")
    with eng.begin() as c:
        c.execute(text("DELETE FROM ml_enrolment_forecast"))

    B = 5000
    w = 0
    for s in range(0, len(df_out), B):
        df_out.iloc[s:s+B].to_sql(
            "ml_enrolment_forecast", eng,
            if_exists="append", index=False, method="multi",
        )
        w += min(B, len(df_out) - s)
    print(f"  {w:,} rows written.\n")

    # ═════════════════════════════════════════════════════════════════
    #  SUMMARY
    # ═════════════════════════════════════════════════════════════════
    print(SEP)
    print("  ML Forecasting Engine — Summary")
    print(SEP)
    avg_g = float(np.mean(g_pred))
    print(f"  Mean ML growth rate : {avg_g:+.4f}")
    print(f"  Median              : {float(np.median(g_pred)):+.4f}")
    print()
    for k in [1, 2, 3]:
        m = df_out["years_ahead"] == k
        cr = df_out.loc[m, "projected_classroom_gap"].sum()
        tr = df_out.loc[m, "projected_teacher_gap"].sum()
        print(f"  T+{k}  {df_out.loc[m, 'forecast_year'].iloc[0]}  "
              f"|  cr_gap: {cr:>10,}  |  tr_gap: {tr:>10,}")

    # Phase 10 comparison
    try:
        with eng.connect() as c:
            p10 = pd.read_sql(P10_STATS_SQL, c)
        if len(p10):
            print(f"\n  Phase 10 (WMA) vs Phase 11 (ML):")
            print(f"  {'':2}{'Horizon':>7} {'ML cr_gap':>12} {'P10 cr_gap':>12}"
                  f" {'Δ':>9}  {'ML tr_gap':>12} {'P10 tr_gap':>12} {'Δ':>9}")
            print(f"  {'-'*82}")
            for _, r in p10.iterrows():
                k = int(r["years_ahead"])
                mc = int(df_out.loc[df_out.years_ahead==k, "projected_classroom_gap"].sum())
                mt = int(df_out.loc[df_out.years_ahead==k, "projected_teacher_gap"].sum())
                pc, pt = int(r["cr_gap"]), int(r["tr_gap"])
                print(f"  T+{k:>5} {mc:>12,} {pc:>12,} {mc-pc:>+9,}"
                      f"  {mt:>12,} {pt:>12,} {mt-pt:>+9,}")
    except Exception:
        pass

    # Top 10 districts
    print(f"\n  Top 10 districts — T+3 ML classroom gap:")
    tq = text("""
        SELECT s.district,
               SUM(m.projected_enrolment) AS enrl,
               SUM(m.projected_classroom_gap) AS cr,
               SUM(m.projected_teacher_gap) AS tr,
               ROUND(AVG(m.ml_growth_rate),4) AS g
        FROM ml_enrolment_forecast m
        JOIN schools s ON m.school_id = s.school_id
        WHERE m.years_ahead = 3
        GROUP BY s.district ORDER BY cr DESC LIMIT 10
    """)
    with eng.connect() as c:
        td = pd.read_sql(tq, c)
    print(f"  {'-'*61}")
    for _, d in td.iterrows():
        print(f"    {str(d['district']):22s}"
              f"  enrl: {int(d['enrl']):>9,}"
              f"  cr: {int(d['cr']):>6,}"
              f"  tr: {int(d['tr']):>6,}"
              f"  g: {d['g']:+.4f}")
    print(f"  {'-'*61}")
    print(SEP)


if __name__ == "__main__":
    print("=" * 65)
    print("  School AI BAV — ML Forecasting Engine  (Phase 11)")
    print("=" * 65 + "\n")
    run()
