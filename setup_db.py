"""
setup_db.py — Load CSV data into SQLite (dev) or PostgreSQL (production)

Usage:
    python setup_db.py                  # SQLite (default, no setup needed)
    python setup_db.py --postgres       # PostgreSQL (set DATABASE_URL in .env)

PostgreSQL one-time setup:
    1. Install PostgreSQL: https://www.postgresql.org/download/
    2. Create database:  createdb pratham_dashboard
    3. Set .env:         DATABASE_URL=postgresql://user:password@localhost/pratham_dashboard
    4. Run:              python setup_db.py --postgres

Metabase connection (after Java is installed):
    1. Download: https://www.metabase.com/start/oss/jar
    2. Run:      java -jar metabase.jar
    3. Open:     http://localhost:3000
    4. Connect to the database using the settings below
"""

import sys, sqlite3, os
import pandas as pd
import numpy as np
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

USE_POSTGRES = "--postgres" in sys.argv
DATA_DIR = Path(r"C:\project\nss_dashboard\data")
SQLITE_PATH = Path(r"C:\project\nss_dashboard\data\pratham.db")

# ── Connection factory ────────────────────────────────────────────────────────
def get_engine():
    if USE_POSTGRES:
        import sqlalchemy
        url = os.getenv("DATABASE_URL", "postgresql://localhost/pratham_dashboard")
        print(f"Connecting to PostgreSQL: {url}")
        return sqlalchemy.create_engine(url)
    else:
        import sqlalchemy
        print(f"Using SQLite: {SQLITE_PATH}")
        return sqlalchemy.create_engine(f"sqlite:///{SQLITE_PATH}")

# ── Load and transform UDISE ──────────────────────────────────────────────────
def build_enrollment():
    print("Loading UDISE enrollment data...")
    boys_cols  = [f"class_{i}_boys"  for i in range(1, 13)]
    girls_cols = [f"class_{i}_girls" for i in range(1, 13)]
    all_cols   = boys_cols + girls_cols

    raw = pd.read_csv(DATA_DIR / "Udise_Data_students_Enrollment.csv",
                      encoding="utf-8-sig").dropna(subset=["district_name"])
    for c in all_cols:
        raw[c] = pd.to_numeric(raw[c], errors="coerce").fillna(0).astype(int)

    df = raw.groupby(["ac_year","state_name","district_name"])[all_cols].sum().reset_index()
    df["total_boys"]       = df[boys_cols].sum(axis=1)
    df["total_girls"]      = df[girls_cols].sum(axis=1)
    df["total_enrollment"] = df["total_boys"] + df["total_girls"]
    df["gpi"]              = (df["total_girls"] / df["total_boys"].replace(0, np.nan)).round(3)

    c1  = (df["class_1_boys"]  + df["class_1_girls"]).replace(0, np.nan)
    c5  =  df["class_5_boys"]  + df["class_5_girls"]
    c6  = (df["class_6_boys"]  + df["class_6_girls"]).replace(0, np.nan)
    c8  =  df["class_8_boys"]  + df["class_8_girls"]
    c10 = (df["class_10_boys"] + df["class_10_girls"]).replace(0, np.nan)
    c11 =  df["class_11_boys"] + df["class_11_girls"]

    df["primary_retention_pct"] = ((c5/c1)*100).clip(0,200).round(1)
    df["sec_dropout_pct"]       = (((1 - c8/c6)*100).clip(0)).round(1)
    df["hs_transition_pct"]     = ((c11/c10)*100).clip(0,300).round(1)

    # Data quality flags
    df["dq_retention_anomaly"] = (df["primary_retention_pct"] > 120).astype(int)
    df["dq_dropout_anomaly"]   = (df["sec_dropout_pct"] > 80).astype(int)

    print(f"  Enrollment rows: {len(df):,}  |  Anomalies flagged: {df['dq_retention_anomaly'].sum()}")
    return df

# ── Load district quality ─────────────────────────────────────────────────────
def build_district():
    print("Loading district quality data...")
    dist = pd.read_csv(DATA_DIR / "2015_16_Districtwise.csv", encoding="utf-8-sig")
    dist["ptr"]              = (dist["ENRTOT"] / dist["TCHTOT"].replace(0, np.nan)).round(1)
    dist["girls_toilet_pct"] = (dist["SGTOILTOT"] / dist["SCHTOT"].replace(0, np.nan)*100).round(1)
    dist["mdm_pct"]          = (dist["MDMTOT"]    / dist["SCHTOT"].replace(0, np.nan)*100).round(1)
    rep_num = dist[["C1_BR","C2_BR","C3_BR","C4_BR","C5_BR"]].sum(axis=1)
    rep_den = dist[["C1_B","C2_B","C3_B","C4_B","C5_B"]].sum(axis=1).replace(0, np.nan)
    dist["repeater_rate_pct"] = (rep_num/rep_den*100).round(1)
    dist["single_tch_pct"]   = (dist["STCHTOT"] / dist["SCHTOT"].replace(0, np.nan)*100).round(1)

    out = dist[["STATNAME","DISTNAME","OVERALL_LI","FEMALE_LIT","MALE_LIT",
                "ptr","girls_toilet_pct","mdm_pct","repeater_rate_pct",
                "single_tch_pct","TOTPOPULAT","SEXRATIO"]].copy()
    out.columns = ["state_name","district_name","literacy_rate","female_lit","male_lit",
                   "ptr","girls_toilet_pct","mdm_pct","repeater_rate_pct",
                   "single_tch_pct","population","sex_ratio"]
    out["state_name"]    = out["state_name"].str.strip().str.title()
    out["district_name"] = out["district_name"].str.strip().str.upper()

    # Data quality flags
    out["dq_ptr_anomaly"] = ((out["ptr"] > 100) | (out["ptr"] < 5)).astype(int)
    print(f"  District rows: {len(out):,}  |  PTR anomalies: {out['dq_ptr_anomaly'].sum()}")
    return out

# ── Load secondary pass rates ─────────────────────────────────────────────────
def build_secondary():
    print("Loading secondary exam data...")
    sec = pd.read_csv(DATA_DIR / "2015_16_Statewise_Secondary.csv", encoding="utf-8-sig")
    sec["pass_rate"]       = (sec["pass_b_gen_py10"].fillna(0)+sec["pass_g_gen_py10"].fillna(0)) / \
                              (sec["apr_b_gen_py10"].fillna(0)+sec["apr_g_gen_py10"].fillna(0)).replace(0,np.nan)*100
    sec["pass_rate_boys"]  = sec["pass_b_gen_py10"]/sec["apr_b_gen_py10"].replace(0,np.nan)*100
    sec["pass_rate_girls"] = sec["pass_g_gen_py10"]/sec["apr_g_gen_py10"].replace(0,np.nan)*100
    sec["pass_rate_sc"]    = (sec["pass_b_sc_py10"].fillna(0)+sec["pass_g_sc_py10"].fillna(0)) / \
                              (sec["apr_b_sc_py10"].fillna(0)+sec["apr_g_sc_py10"].fillna(0)).replace(0,np.nan)*100
    sec["pass_rate_st"]    = (sec["pass_b_st_py10"].fillna(0)+sec["pass_g_st_py10"].fillna(0)) / \
                              (sec["apr_b_st_py10"].fillna(0)+sec["apr_g_st_py10"].fillna(0)).replace(0,np.nan)*100
    sec["appeared"]        = sec["apr_b_gen_py10"].fillna(0)+sec["apr_g_gen_py10"].fillna(0)
    sec["passed"]          = sec["pass_b_gen_py10"].fillna(0)+sec["pass_g_gen_py10"].fillna(0)

    for col in ["pass_rate","pass_rate_boys","pass_rate_girls","pass_rate_sc","pass_rate_st"]:
        sec[col] = sec[col].round(1)

    out = sec[["statname","pass_rate","pass_rate_boys","pass_rate_girls",
               "pass_rate_sc","pass_rate_st","appeared","passed"]].copy()
    out["statname"] = out["statname"].str.strip().str.title()
    print(f"  Secondary rows: {len(out):,}")
    return out

# ── Write to database ─────────────────────────────────────────────────────────
def main():
    engine = get_engine()

    enrollment = build_enrollment()
    district   = build_district()
    secondary  = build_secondary()

    print("\nWriting to database...")
    enrollment.to_sql("enrollment", engine, if_exists="replace", index=False, chunksize=5000)
    print(f"  enrollment: {len(enrollment):,} rows written")

    district.to_sql("district_quality", engine, if_exists="replace", index=False)
    print(f"  district_quality: {len(district):,} rows written")

    secondary.to_sql("secondary_results", engine, if_exists="replace", index=False)
    print(f"  secondary_results: {len(secondary):,} rows written")

    # Summary view (useful for Metabase quick questions)
    if not USE_POSTGRES:
        conn = sqlite3.connect(SQLITE_PATH)
        conn.execute("""
            CREATE VIEW IF NOT EXISTS kpi_summary AS
            SELECT
                ac_year, state_name,
                SUM(total_enrollment)               AS total_enrollment,
                SUM(total_girls)                    AS total_girls,
                SUM(total_boys)                     AS total_boys,
                ROUND(AVG(gpi), 3)                  AS avg_gpi,
                ROUND(AVG(primary_retention_pct),1) AS avg_retention_pct,
                ROUND(AVG(sec_dropout_pct),1)       AS avg_dropout_pct,
                SUM(dq_retention_anomaly)           AS anomaly_count
            FROM enrollment
            GROUP BY ac_year, state_name
        """)
        conn.commit()
        conn.close()
        print("  kpi_summary view created")

    print(f"\nDone. Database ready at: {SQLITE_PATH if not USE_POSTGRES else 'PostgreSQL'}")
    print("\nMetabase connection settings:")
    if USE_POSTGRES:
        print("  Type: PostgreSQL")
        print("  Host: localhost  Port: 5432  Database: pratham_dashboard")
    else:
        print("  Type: SQLite (H2 file path in Metabase)")
        print(f"  File: {SQLITE_PATH}")
    print("\nGoogle Sheets: see sheets_connector.py for live sync instructions")

if __name__ == "__main__":
    main()
