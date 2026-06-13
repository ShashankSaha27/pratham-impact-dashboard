"""
sheets_connector.py — Google Sheets live data connector

HOW TO SET UP (one-time, 10 minutes):
======================================
1. Go to https://console.cloud.google.com
2. Create a project → Enable "Google Sheets API" and "Google Drive API"
3. Create a Service Account → download the JSON key file
4. Save the key file as:  C:\project\nss_dashboard\google_credentials.json
5. Share your Google Sheet with the service account email (viewer is enough)
6. Set SHEET_ID in your .env file (the long ID from the sheet URL)
7. Run:  python sheets_connector.py --test

SHEET STRUCTURE EXPECTED:
==========================
The connector expects ONE tab named "field_data" with these columns:
  date | state | district | school_id | class | boys_enrolled | girls_enrolled | teacher_present | mdm_served

This is the "live field data" format that field workers update weekly.
The rest of the dashboard (UDISE historical data) stays in the SQLite database.

For a full demo without real credentials, run:  python sheets_connector.py --demo
This generates a sample CSV that simulates what a Google Sheet would return.
"""

import os, sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

CREDENTIALS_FILE  = Path(r"C:\project\nss_dashboard\google_credentials.json")
SHEET_ID          = os.getenv("GOOGLE_SHEET_ID", "")
DEMO_CSV          = Path(r"C:\project\nss_dashboard\data\field_data_demo.csv")
ACTIVITY_DEMO_CSV = Path(r"C:\project\nss_dashboard\data\activity_data_demo.csv")

PRATHAM_STATES    = ["Uttar Pradesh", "Bihar", "Rajasthan", "Maharashtra", "Gujarat", "Madhya Pradesh"]
SAMPLE_DISTRICTS  = {
    "Uttar Pradesh": ["LUCKNOW", "VARANASI", "AGRA", "KANPUR", "ALLAHABAD"],
    "Bihar":         ["PATNA", "GAYA", "MUZAFFARPUR", "BHAGALPUR", "DARBHANGA"],
    "Rajasthan":     ["JAIPUR", "JODHPUR", "UDAIPUR", "AJMER", "KOTA"],
    "Maharashtra":   ["PUNE", "NASHIK", "AURANGABAD", "NAGPUR", "SOLAPUR"],
    "Gujarat":       ["AHMEDABAD", "SURAT", "VADODARA", "RAJKOT", "GANDHINAGAR"],
    "Madhya Pradesh":["BHOPAL", "INDORE", "GWALIOR", "JABALPUR", "UJJAIN"],
}

# ── Demo data generator ───────────────────────────────────────────────────────
def generate_demo_field_data(weeks=12):
    """Generates realistic field data for 12 weeks across Pratham focus states."""
    np.random.seed(42)
    rows = []
    base_date = datetime.now() - timedelta(weeks=weeks)

    for week in range(weeks):
        report_date = (base_date + timedelta(weeks=week)).strftime("%Y-%m-%d")
        for state, districts in SAMPLE_DISTRICTS.items():
            for district in districts:
                for class_num in range(1, 9):
                    boys   = int(np.random.normal(35, 8))
                    girls  = int(np.random.normal(32, 9))
                    # Bihar and UP have lower GPI
                    if state in ["Bihar", "Uttar Pradesh"]:
                        girls = int(girls * 0.88)

                    rows.append({
                        "date":            report_date,
                        "week_number":     week + 1,
                        "state":           state,
                        "district":        district,
                        "class":           class_num,
                        "boys_enrolled":   max(0, boys),
                        "girls_enrolled":  max(0, girls),
                        "teacher_present": np.random.choice([1, 0], p=[0.87, 0.13]),
                        "mdm_served":      np.random.choice([1, 0], p=[0.82, 0.18]),
                        "data_source":     "demo_generated",
                    })

    df = pd.DataFrame(rows)
    df.to_csv(DEMO_CSV, index=False)
    print(f"Demo field data written: {len(df):,} rows -> {DEMO_CSV}")
    return df

# ── Live Google Sheets loader ─────────────────────────────────────────────────
def load_from_sheets():
    """Load live field data from Google Sheet. Returns DataFrame."""
    if not CREDENTIALS_FILE.exists():
        raise FileNotFoundError(
            f"Credentials not found at {CREDENTIALS_FILE}\n"
            "Run with --demo to use generated sample data instead."
        )
    if not SHEET_ID:
        raise ValueError("Set GOOGLE_SHEET_ID in your .env file.")

    import gspread
    gc  = gspread.service_account(filename=str(CREDENTIALS_FILE))
    sh  = gc.open_by_key(SHEET_ID)
    ws  = sh.worksheet("field_data")
    df  = pd.DataFrame(ws.get_all_records())
    df["data_source"] = "google_sheets_live"
    print(f"Loaded {len(df):,} rows from Google Sheet (last row: {df['date'].max()})")
    return df

# ── Unified loader (used by app.py) ──────────────────────────────────────────
def load_field_data():
    """
    Returns field data DataFrame from the best available source:
    1. Google Sheets (if credentials + SHEET_ID configured)
    2. Demo CSV (if demo data has been generated)
    3. Empty DataFrame with correct schema
    """
    if CREDENTIALS_FILE.exists() and SHEET_ID:
        try:
            return load_from_sheets()
        except Exception as e:
            print(f"Google Sheets unavailable ({e}), falling back to demo data")

    if DEMO_CSV.exists():
        df = pd.read_csv(DEMO_CSV)
        df["data_source"] = "demo_csv"
        return df

    # Return empty with correct schema so app doesn't crash
    return pd.DataFrame(columns=[
        "date","week_number","state","district","class",
        "boys_enrolled","girls_enrolled","teacher_present","mdm_served","data_source"
    ])


# ── Activity data loader ──────────────────────────────────────────────────────
def load_activity_data():
    """
    Load structured activity data (activity_type, sessions_held, children_reached…).
    Falls back to demo CSV generated by activity_impact.generate_activity_data().
    The Google Sheets version expects a second tab named 'activity_data'.
    """
    # Try live Google Sheets tab first
    if CREDENTIALS_FILE.exists() and SHEET_ID:
        try:
            import gspread
            gc  = gspread.service_account(filename=str(CREDENTIALS_FILE))
            sh  = gc.open_by_key(SHEET_ID)
            ws  = sh.worksheet("activity_data")
            df  = pd.DataFrame(ws.get_all_records())
            df["data_source"] = "google_sheets_live"
            return df
        except Exception:
            pass  # fall through to demo CSV

    if ACTIVITY_DEMO_CSV.exists():
        return pd.read_csv(ACTIVITY_DEMO_CSV)

    # Generate and cache demo data on first call
    try:
        from activity_impact import generate_activity_data
        df = generate_activity_data(weeks=12)
        df.to_csv(ACTIVITY_DEMO_CSV, index=False)
        return df
    except Exception:
        return pd.DataFrame(columns=[
            "date","week_number","state","district","activity_type",
            "sessions_held","children_reached","girls_reached",
            "teachers_trained","duration_hours","data_source"
        ])

# ── KPI aggregation for field data ───────────────────────────────────────────
def compute_field_kpis(df):
    """Aggregate raw field data into weekly KPIs for the live section of the dashboard."""
    if df.empty:
        return {}

    df["date"] = pd.to_datetime(df["date"])
    latest_week = df["week_number"].max()
    prev_week   = latest_week - 1

    cur = df[df["week_number"] == latest_week]
    prv = df[df["week_number"] == prev_week] if prev_week >= 1 else cur

    total_cur    = cur["boys_enrolled"].sum() + cur["girls_enrolled"].sum()
    total_prv    = prv["boys_enrolled"].sum() + prv["girls_enrolled"].sum()
    gpi_cur      = (cur["girls_enrolled"].sum() / max(cur["boys_enrolled"].sum(), 1))
    teacher_att  = cur["teacher_present"].mean() * 100
    mdm_cov      = cur["mdm_served"].mean() * 100
    yoy_change   = ((total_cur - total_prv) / max(total_prv, 1)) * 100

    return {
        "field_enrollment":     int(total_cur),
        "field_gpi":            round(gpi_cur, 3),
        "field_teacher_att":    round(teacher_att, 1),
        "field_mdm_coverage":   round(mdm_cov, 1),
        "field_wow_change":     round(yoy_change, 1),
        "field_as_of":          cur["date"].max().strftime("%d %b %Y"),
        "field_data_source":    cur["data_source"].iloc[0] if not cur.empty else "none",
        "weeks_of_data":        int(df["week_number"].max()),
    }

if __name__ == "__main__":
    if "--test" in sys.argv:
        df = load_from_sheets()
        print(df.head())
        print(compute_field_kpis(df))
    elif "--demo" in sys.argv or True:   # default: generate demo data
        df = generate_demo_field_data(weeks=12)
        print("\nSample rows:")
        print(df.head(3).to_string())
        print("\nField KPIs:")
        kpis = compute_field_kpis(df)
        for k, v in kpis.items():
            print(f"  {k}: {v}")
