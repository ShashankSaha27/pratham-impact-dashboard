"""
calibrate_effects.py — Fit OLS regression coefficients for the activity→KPI map.

Uses UDISE district-level data to estimate how strongly each "activity proxy"
correlates with each outcome KPI. Replaces hardcoded effect sizes in
activity_impact.py with data-fitted ones.

WHAT WE REGRESS:
  mdm_pct             → primary_retention_pct   (MDM monitoring → retention)
  girls_toilet_pct    → gpi                     (girls safety → gender parity)
  girls_toilet_pct    → sec_dropout_pct (inv)   (toilet → girls stay in school)
  ptr                 → primary_retention_pct   (teacher quality → retention)
  literacy_rate       → primary_retention_pct   (community awareness → retention)
  female_lit          → gpi                     (community mobilisation → GPI)

Each regression is cross-sectional (one obs per district, 2015-16 data).
We control for state fixed effects to absorb unobserved state-level variation.

OUTPUT:  data/calibrated_effects.json
  {
    "mdm_monitoring":   {"coefficient": 0.23, "r2": 0.31, "p_value": 0.001,
                         "ci_low": 0.18, "ci_high": 0.28, "n": 634,
                         "method": "OLS with state FE", "fitted": true},
    ...
  }

Usage:
    python calibrate_effects.py
    python calibrate_effects.py --verbose   # print full regression tables
"""

import sys, json
import numpy as np
import pandas as pd
import sqlalchemy
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

DATA_DIR    = Path(r"C:\project\nss_dashboard\data")
SQLITE_PATH = DATA_DIR / "pratham.db"
OUT_PATH    = DATA_DIR / "calibrated_effects.json"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{SQLITE_PATH}")
VERBOSE     = "--verbose" in sys.argv


def load_merged():
    """Merge enrollment (2015-16) with district_quality for cross-sectional regression."""
    engine = sqlalchemy.create_engine(DATABASE_URL)
    enr = pd.read_sql(
        "SELECT state_name, district_name, primary_retention_pct, sec_dropout_pct, gpi "
        "FROM enrollment WHERE ac_year = '2015-16'",
        engine
    )
    dist = pd.read_sql(
        "SELECT state_name, district_name, ptr, girls_toilet_pct, mdm_pct, "
        "literacy_rate, female_lit FROM district_quality",
        engine
    )
    # Normalise join keys
    enr["district_name"]  = enr["district_name"].str.strip().str.upper()
    dist["district_name"] = dist["district_name"].str.strip().str.upper()
    enr["state_name"]     = enr["state_name"].str.strip().str.title()
    dist["state_name"]    = dist["state_name"].str.strip().str.title()

    merged = enr.merge(dist, on=["state_name","district_name"], how="inner")
    print(f"Merged dataset: {len(merged):,} districts")
    return merged


def ols_with_state_fe(df, x_col, y_col, clip_y=None):
    """
    OLS regression of y_col ~ x_col with state dummy fixed effects.
    Returns dict with coefficient, r2, p_value, ci_low, ci_high, n.
    Uses only rows where both columns are non-null and finite.
    """
    from scipy import stats

    sub = df[[x_col, y_col, "state_name"]].dropna()
    sub = sub[np.isfinite(sub[x_col]) & np.isfinite(sub[y_col])]
    if clip_y:
        sub = sub[(sub[y_col] >= clip_y[0]) & (sub[y_col] <= clip_y[1])]
    if len(sub) < 30:
        return None

    # Partial out state fixed effects (within-state demeaning)
    sub = sub.copy()
    for col in [x_col, y_col]:
        state_means = sub.groupby("state_name")[col].transform("mean")
        sub[f"{col}_dm"] = sub[col] - state_means

    x = sub[f"{x_col}_dm"].values
    y = sub[f"{y_col}_dm"].values

    slope, intercept, r, p, se = stats.linregress(x, y)
    n   = len(sub)
    # 95% CI: slope ± t * se
    from scipy.stats import t as t_dist
    t_crit = t_dist.ppf(0.975, df=n - 2)
    ci_low  = slope - t_crit * se
    ci_high = slope + t_crit * se

    if VERBOSE:
        print(f"  {x_col:20s} -> {y_col:25s}  "
              f"coef={slope:+.4f}  R²={r**2:.3f}  p={p:.4f}  n={n}  "
              f"95%CI=[{ci_low:+.4f}, {ci_high:+.4f}]")

    return {
        "coefficient": round(float(slope), 6),
        "r2":          round(float(r**2), 4),
        "p_value":     round(float(p), 6),
        "ci_low":      round(float(ci_low), 6),
        "ci_high":     round(float(ci_high), 6),
        "n":           int(n),
        "method":      "OLS within-state demeaning (state FE)",
        "fitted":      True,
    }


def assign_confidence(r2, p_value, n):
    """Map regression quality to confidence tier."""
    if p_value > 0.05 or n < 50:
        return "low"
    if r2 >= 0.15 and p_value < 0.01:
        return "high"
    return "medium"


def main():
    print("=== Calibrating activity effect sizes from UDISE data ===\n")
    df = load_merged()

    # ── Regression specs ─────────────────────────────────────────────────────
    # (activity_type_key, x_col, y_col, clip_y_range, interpretation_note)
    specs = [
        ("mdm_monitoring",
         "mdm_pct", "primary_retention_pct", (20, 120),
         "MDM coverage -> primary retention"),

        ("community_mobilisation",
         "female_lit", "gpi", (0.5, 2.0),
         "Female literacy (community awareness proxy) -> GPI"),

        ("girls_safety_audit",
         "girls_toilet_pct", "gpi", (0.5, 2.0),
         "Girls toilet coverage -> GPI"),

        ("girls_safety_audit_dropout",    # secondary fit for same activity
         "girls_toilet_pct", "sec_dropout_pct", (0, 80),
         "Girls toilet coverage -> secondary dropout (inverse)"),

        ("teacher_training",
         "ptr", "primary_retention_pct", (20, 120),
         "PTR -> primary retention (teacher quality channel)"),

        ("literacy_camp",
         "literacy_rate", "primary_retention_pct", (20, 120),
         "District literacy (community mobilisation proxy) -> retention"),

        ("enrollment_drive",
         "mdm_pct", "gpi", (0.5, 2.0),
         "MDM coverage -> GPI (enrollment drive attracts girls)"),
    ]

    results = {}
    if VERBOSE:
        print("Regression results (within-state demeaned OLS):")

    for key, x_col, y_col, clip_y, note in specs:
        if VERBOSE:
            print(f"\n  [{note}]")
        res = ols_with_state_fe(df, x_col, y_col, clip_y)
        if res is None:
            print(f"  SKIP {key}: insufficient data")
            continue
        res["x_col"]      = x_col
        res["y_col"]      = y_col
        res["note"]       = note
        res["confidence"] = assign_confidence(res["r2"], res["p_value"], res["n"])
        results[key] = res

    # ── Print summary table ───────────────────────────────────────────────────
    print(f"\n{'Activity key':30s}  {'KPI':25s}  {'coef':>8s}  {'R²':>6s}  "
          f"{'p':>8s}  {'CI':>20s}  {'conf':>8s}")
    print("-" * 115)
    for key, r in results.items():
        ci_str = f"[{r['ci_low']:+.4f}, {r['ci_high']:+.4f}]"
        print(f"  {key:28s}  {r['y_col']:25s}  {r['coefficient']:+8.4f}  "
              f"{r['r2']:6.3f}  {r['p_value']:8.4f}  {ci_str:>22s}  {r['confidence']:>8s}")

    # ── Write JSON ────────────────────────────────────────────────────────────
    OUT_PATH.write_text(json.dumps(results, indent=2))
    print(f"\nCalibrated effects written to: {OUT_PATH}")
    print("\nRe-run the dashboard to pick up fitted coefficients automatically.")
    print("activity_impact.py loads this file at startup if present.")

    # ── Quick interpretation ──────────────────────────────────────────────────
    print("\n=== Interpretation ===")
    for key, r in results.items():
        coef = r["coefficient"]
        sign = "+" if coef > 0 else ""
        interp = "improves" if coef > 0 else "worsens"
        if r["y_col"] == "sec_dropout_pct":
            interp = "reduces dropout by" if coef < 0 else "increases dropout by"
            sign = ""
        p_flag = "***" if r["p_value"] < 0.001 else ("**" if r["p_value"] < 0.01 else
                 ("*" if r["p_value"] < 0.05 else "(ns)"))
        print(f"  {r['note']}")
        print(f"    1-unit increase in {r['x_col']} {interp} {r['y_col']} "
              f"by {sign}{abs(coef):.4f}  R²={r['r2']:.3f} {p_flag}")


if __name__ == "__main__":
    main()
