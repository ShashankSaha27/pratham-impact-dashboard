"""
activity_impact.py — Activity-to-KPI mapping table and lag-based prediction model.

This is the translation layer that converts field worker activity logs into
predicted outcome KPI movements. It answers: "We ran X sessions this week —
what KPI should move, by how much, and when?"

ACTIVITY SCHEMA (one row per school visit):
  date | state | district | activity_type | sessions_held | children_reached |
  girls_reached | teachers_trained | duration_hours | school_id | data_source

ACTIVITY TYPES and their KPI targets:
  literacy_camp         → primary_retention_pct  (lag 8 weeks,  +0.12%/session)
  remedial_class        → pass_rate              (lag 16 weeks, +0.08%/session)
  enrollment_drive      → total_enrollment       (lag 2 weeks,  +3 children/session)
  community_mobilisation→ gpi                    (lag 4 weeks,  +0.003/session)
  teacher_training      → ptr (proxy quality)    (lag 12 weeks, -0.05 PTR/session)
  mdm_monitoring        → mdm_pct               (lag 2 weeks,  +0.5%/session)
  girls_safety_audit    → girls_toilet_pct       (lag 6 weeks,  +0.3%/session)
"""

from datetime import datetime, timedelta
from pathlib import Path
import copy as _copy
import json
import pandas as pd
import numpy as np

# ── Mapping table ──────────────────────────────────────────────────────────────
# Each entry: activity_type → {kpi, lag_weeks, effect_per_session, unit, direction, confidence}
ACTIVITY_KPI_MAP = {
    "literacy_camp": {
        "kpi":               "Primary Retention %",
        "kpi_key":           "retention",
        "lag_weeks":         8,
        "effect_per_session": 0.12,       # percentage points per session
        "unit":              "pp",
        "direction":         "up",
        "confidence":        "medium",
        "evidence":          "Pratham ASER correlation: 8-week literacy camp → +0.12pp retention per session",
        "emoji":             "📚",
    },
    "remedial_class": {
        "kpi":               "Class 10 Pass Rate",
        "kpi_key":           "passrate",
        "lag_weeks":         16,
        "effect_per_session": 0.08,
        "unit":              "pp",
        "direction":         "up",
        "confidence":        "low",
        "evidence":          "Estimated; verify with board exam data after one cycle",
        "emoji":             "✏️",
    },
    "enrollment_drive": {
        "kpi":               "Total Enrollment",
        "kpi_key":           "enrollment",
        "lag_weeks":         2,
        "effect_per_session": 3.0,        # children per session
        "unit":              "children",
        "direction":         "up",
        "confidence":        "high",
        "evidence":          "Direct count; children enrolled within 2 weeks of drive",
        "emoji":             "🏫",
    },
    "community_mobilisation": {
        "kpi":               "Gender Parity Index",
        "kpi_key":           "gpi",
        "lag_weeks":         4,
        "effect_per_session": 0.003,
        "unit":              "GPI points",
        "direction":         "up",
        "confidence":        "medium",
        "evidence":          "Community awareness → girls enrollment increases within 4 weeks",
        "emoji":             "🤝",
    },
    "teacher_training": {
        "kpi":               "Pupil-Teacher Ratio (quality proxy)",
        "kpi_key":           "ptr",
        "lag_weeks":         12,
        "effect_per_session": -0.05,      # negative = PTR improves (goes down)
        "unit":              "PTR points",
        "direction":         "down",      # lower PTR = better
        "confidence":        "low",
        "evidence":          "Teacher quality proxy; classroom attendance improves within 12 weeks",
        "emoji":             "👩‍🏫",
    },
    "mdm_monitoring": {
        "kpi":               "MDM Coverage %",
        "kpi_key":           "mdm",
        "lag_weeks":         2,
        "effect_per_session": 0.5,
        "unit":              "pp",
        "direction":         "up",
        "confidence":        "high",
        "evidence":          "Direct: monitoring visit → school resumes MDM within 2 weeks",
        "emoji":             "🍱",
    },
    "girls_safety_audit": {
        "kpi":               "Girls Toilet Coverage %",
        "kpi_key":           "toilet",
        "lag_weeks":         6,
        "effect_per_session": 0.3,
        "unit":              "pp",
        "direction":         "up",
        "confidence":        "medium",
        "evidence":          "Safety audit → remediation follows within 6 weeks",
        "emoji":             "🚻",
    },
}

ACTIVITY_TYPES   = list(ACTIVITY_KPI_MAP.keys())
CONFIDENCE_COLOR = {"high": "#198754", "medium": "#fd7e14", "low": "#6c757d"}

_CALIBRATED_PATH = Path(r"C:\project\nss_dashboard\data\calibrated_effects.json")

# Map: activity_type → key used in calibrated_effects.json
_CALIBRATION_KEY = {
    "mdm_monitoring":          "mdm_monitoring",
    "community_mobilisation":  "community_mobilisation",
    "girls_safety_audit":      "girls_safety_audit",
    "teacher_training":        "teacher_training",
    "literacy_camp":           "literacy_camp",
    "enrollment_drive":        "enrollment_drive",
    "remedial_class":          None,   # no proxy in UDISE; stays estimated
}


def load_calibrated_effects():
    """
    Load OLS-fitted coefficients from calibrate_effects.py output.
    Returns dict keyed by activity_type, or empty dict if file not found.
    """
    if not _CALIBRATED_PATH.exists():
        return {}
    import json
    return json.loads(_CALIBRATED_PATH.read_text())


def apply_calibration(mapping_copy, calibrated):
    """
    Overwrite effect_per_session and confidence in a copy of ACTIVITY_KPI_MAP
    using fitted OLS coefficients where available.
    """
    for act_type, cal_key in _CALIBRATION_KEY.items():
        if cal_key is None or cal_key not in calibrated:
            continue
        cal = calibrated[cal_key]
        if act_type in mapping_copy:
            mapping_copy[act_type] = {
                **mapping_copy[act_type],
                "effect_per_session": round(cal["coefficient"], 6),
                "confidence":         cal["confidence"],
                "r2":                 cal["r2"],
                "p_value":            cal["p_value"],
                "ci_low":             cal["ci_low"],
                "ci_high":            cal["ci_high"],
                "n_obs":              cal["n"],
                "source":             "OLS fitted (UDISE 2015-16, within-state FE)",
                "fitted":             True,
            }
    return mapping_copy


# Apply at module load — dashboard picks up fitted coefficients automatically
_CALIBRATED = load_calibrated_effects()
ACTIVE_MAP  = apply_calibration(_copy.deepcopy(ACTIVITY_KPI_MAP), _CALIBRATED)
_N_FITTED   = sum(1 for v in ACTIVE_MAP.values() if v.get("fitted", False))
if _N_FITTED:
    print(f"[activity_impact] Loaded {_N_FITTED} OLS-fitted coefficients from {_CALIBRATED_PATH.name}")


# ── Demo activity data generator ───────────────────────────────────────────────
def generate_activity_data(weeks=12):
    """
    Generate realistic activity log data across Pratham focus states.
    Returns a DataFrame with one row per activity instance per week per district.
    """
    np.random.seed(99)
    rows = []
    states_districts = {
        "Uttar Pradesh":  ["LUCKNOW", "VARANASI", "AGRA", "SHRAVASTI", "BAHRAICH"],
        "Bihar":          ["PATNA", "GAYA", "MUZAFFARPUR", "ARARIA", "SITAMARHI"],
        "Rajasthan":      ["JAIPUR", "JODHPUR", "BARMER", "DUNGARPUR", "BANSWARA"],
        "Maharashtra":    ["PUNE", "NASHIK", "NANDURBAR", "GADCHIROLI", "OSMANABAD"],
        "Gujarat":        ["AHMEDABAD", "SURAT", "DAHOD", "NARMADA", "TAPI"],
        "Madhya Pradesh": ["BHOPAL", "INDORE", "SHEOPUR", "BARWANI", "DINDORI"],
    }
    base = datetime.now() - timedelta(weeks=weeks)

    activity_weights = {
        "literacy_camp":           0.30,
        "remedial_class":          0.20,
        "enrollment_drive":        0.15,
        "community_mobilisation":  0.15,
        "teacher_training":        0.10,
        "mdm_monitoring":          0.05,
        "girls_safety_audit":      0.05,
    }

    for week in range(weeks):
        date = (base + timedelta(weeks=week)).strftime("%Y-%m-%d")
        for state, districts in states_districts.items():
            for district in districts:
                # Each district runs 2-5 different activity types per week
                n_activities = np.random.randint(2, 6)
                chosen = np.random.choice(
                    ACTIVITY_TYPES,
                    size=n_activities,
                    replace=False,
                    p=list(activity_weights.values())
                )
                for act in chosen:
                    sessions     = int(np.random.normal(4, 1.5))
                    children     = int(np.random.normal(35, 10) * max(sessions, 1))
                    girls_pct    = 0.82 if state in ["Bihar","Uttar Pradesh"] else 0.90
                    girls        = int(children * np.random.normal(girls_pct, 0.05))
                    teachers     = int(np.random.normal(2, 0.8)) if act == "teacher_training" else 0
                    rows.append({
                        "date":             date,
                        "week_number":      week + 1,
                        "state":            state,
                        "district":         district,
                        "activity_type":    act,
                        "sessions_held":    max(1, sessions),
                        "children_reached": max(0, children),
                        "girls_reached":    max(0, girls),
                        "teachers_trained": max(0, teachers),
                        "duration_hours":   round(max(1, sessions) * np.random.uniform(1.5, 3.0), 1),
                        "data_source":      "demo_generated",
                    })

    return pd.DataFrame(rows)


# ── KPI prediction engine ──────────────────────────────────────────────────────
def compute_predicted_impacts(activity_df, weeks_lookback=4):
    """
    Given recent activity data, predict KPI movements for each activity type.

    Returns a list of prediction dicts, one per activity type that has data:
    {
      activity_type, kpi, lag_weeks, predicted_delta, sessions_total,
      children_reached, due_date, confidence, unit, direction, emoji, evidence
    }
    """
    if activity_df is None or activity_df.empty:
        return []

    if "week_number" not in activity_df.columns:
        activity_df = activity_df.copy()
        activity_df["week_number"] = 1

    latest_week = activity_df["week_number"].max()
    cutoff_week = latest_week - weeks_lookback
    recent = activity_df[activity_df["week_number"] > cutoff_week]

    predictions = []
    for act_type, mapping in ACTIVE_MAP.items():
        subset = recent[recent["activity_type"] == act_type]
        if subset.empty:
            continue

        sessions_total   = int(subset["sessions_held"].sum())
        children_reached = int(subset["children_reached"].sum())
        girls_reached    = int(subset["girls_reached"].sum()) if "girls_reached" in subset.columns else 0

        raw_delta        = sessions_total * mapping["effect_per_session"]
        predicted_delta  = round(raw_delta, 3)
        due_date         = (datetime.now() + timedelta(weeks=mapping["lag_weeks"])).strftime("%d %b %Y")

        fitted   = mapping.get("fitted", False)
        r2       = mapping.get("r2")
        ci_low   = mapping.get("ci_low")
        ci_high  = mapping.get("ci_high")
        n_obs    = mapping.get("n_obs")
        source   = mapping.get("source", "estimated (no UDISE proxy available)")

        predictions.append({
            "activity_type":    act_type,
            "label":            act_type.replace("_", " ").title(),
            "kpi":              mapping["kpi"],
            "kpi_key":          mapping["kpi_key"],
            "lag_weeks":        mapping["lag_weeks"],
            "predicted_delta":  predicted_delta,
            "sessions_total":   sessions_total,
            "children_reached": children_reached,
            "girls_reached":    girls_reached,
            "due_date":         due_date,
            "confidence":       mapping["confidence"],
            "unit":             mapping["unit"],
            "direction":        mapping["direction"],
            "emoji":            mapping["emoji"],
            "evidence":         mapping["evidence"],
            # Calibration provenance
            "fitted":           fitted,
            "r2":               r2,
            "ci_low":           ci_low,
            "ci_high":          ci_high,
            "n_obs":            n_obs,
            "source":           source,
        })

    # Sort by confidence then magnitude
    conf_order = {"high": 0, "medium": 1, "low": 2}
    predictions.sort(key=lambda x: (conf_order[x["confidence"]], -abs(x["predicted_delta"])))
    return predictions


# ── One-number Monday summary ──────────────────────────────────────────────────
def monday_summary(predictions):
    """
    Return the single most important predicted KPI movement for the ED Monday check.
    Prioritises: (1) high confidence, (2) largest magnitude, (3) soonest due.
    """
    if not predictions:
        return None
    high = [p for p in predictions if p["confidence"] == "high"]
    pool = high if high else predictions
    return max(pool, key=lambda x: abs(x["predicted_delta"]))


if __name__ == "__main__":
    df = generate_activity_data(weeks=12)
    print(f"Generated {len(df):,} activity rows")
    preds = compute_predicted_impacts(df)
    print(f"\nPredicted KPI impacts ({len(preds)} activities with data):\n")
    for p in preds:
        sign = "+" if p["direction"] == "up" else ""
        print(f"  [{p['confidence']:6s}] {p['label']:28s}  ->  {p['kpi']:30s}  "
              f"{sign}{p['predicted_delta']:+.3f} {p['unit']:12s}  due {p['due_date']}")
    mon = monday_summary(preds)
    if mon:
        print(f"\nMonday check: {mon['label']} -> {mon['kpi']} "
              f"{'+' if mon['direction']=='up' else ''}{mon['predicted_delta']:+.2f} {mon['unit']} by {mon['due_date']}")
