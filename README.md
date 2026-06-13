# Pratham Education Foundation — Impact Dashboard
### NSS Open Projects 2026 · Challenge 5.1

An interactive, real-time impact dashboard that converts raw field data into
actionable KPIs for a partner NGO — bridging the gap between activity measurement
and outcome-level decision making.

> *"The vast majority of Indian NGOs measure activity rather than outcomes.
> The tooling problem isn't BI software — it's the missing translation layer
> between field data and decision-relevant KPIs."*

---

## What it does

- Converts field worker logs → predicted KPI movements (OLS-fitted, 6/7 coefficients from real UDISE data)
- Tracks Activity → Output → Outcome → Impact via a live Theory of Change strip
- Shows cost-per-impact (incremental: budget ÷ children above national baseline)
- Auto-generates Insight Alerts naming the worst-performing districts
- Supports Google Sheets live field data + PostgreSQL production backend
- Non-technical interface with plain-English labels, progress bars, and a Monday Check

---

## Screenshots

> Run `python app.py` and open `http://127.0.0.1:8050`

---

## Quick start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Download source data from Kaggle
#    https://www.kaggle.com/datasets/iamsouravbanerjee/education-in-india
#    Place these files in data/:
#      - Udise_Data_students_Enrollment.csv
#      - 2015_16_Districtwise.csv
#      - 2015_16_Statewise_Secondary.csv

# 3. Build the database
python setup_db.py

# 4. Calibrate effect sizes from real data
python calibrate_effects.py

# 5. Run the dashboard
python app.py
# Open http://127.0.0.1:8050
```

---

## Project structure

```
nss_dashboard/
├── app.py                    # Main Dash dashboard
├── setup_db.py               # CSV → SQLite/PostgreSQL pipeline
├── sheets_connector.py       # Google Sheets live data connector
├── activity_impact.py        # Activity-to-KPI translation layer + lag model
├── calibrate_effects.py      # OLS regression — fits effect sizes from UDISE data
├── requirements.txt
│
├── data/
│   ├── pratham.db            # SQLite database (built by setup_db.py)
│   ├── calibrated_effects.json  # OLS-fitted coefficients
│   ├── field_data_demo.csv   # Demo weekly field data (2,880 rows)
│   └── activity_data_demo.csv   # Demo activity log data (1,247 rows)
│
└── docs/
    ├── data_dictionary.md    # Every table, column, formula, source
    ├── kpi_tree.md           # Full KPI tree: activity → impact
    ├── kpi_workshop_output.md  # Mock KPI workshop with NGO staff
    ├── user_guide.md         # Non-technical guide for programme managers
    └── metabase_setup.md     # Metabase self-service BI setup guide
```

---

## KPI tree

```
ACTIVITY    Districts covered
    ↓
OUTPUT      Total enrollment · GPI · MDM coverage
    ↓
OUTCOME     Primary retention % · Secondary dropout % · Class 10 pass rate
    ↓
IMPACT      Literacy rate · Female literacy · SC/ST equity gap
```

---

## Data sources

| Dataset | Source | Rows |
|---------|--------|------|
| UDISE Student Enrollment 2012-20 | Kaggle / UDISE | 5,560 district×year |
| DISE 2015-16 Districtwise Quality | Kaggle / DISE | 680 districts |
| DISE 2015-16 Statewise Secondary | Kaggle / DISE | 36 states |

All public government data. No individual records. Anonymised at district level.

---

## Production deployment

**PostgreSQL backend:**
```bash
# .env
DATABASE_URL=postgresql://user:password@localhost/pratham_dashboard
python setup_db.py --postgres
```

**Google Sheets live field data:**
```bash
# .env
GOOGLE_SHEET_ID=your_sheet_id_here
# Add google_credentials.json (service account key)
# Sheet must have tabs: field_data, activity_data
```

**Metabase self-service BI:**
See `docs/metabase_setup.md`. Requires Java 11+.

---

## Performance

- Full data load: ~1 second (SQLite)
- Real-time refresh: every 60 seconds via `dcc.Interval`
- 627 districts · 8 years · 7 activity types · OLS-fitted predictions

---

## Built for

NSS Open Projects 2026 — Challenge 5.1: Interactive Real-Time Impact Dashboard for Partner NGO

**NGO:** Pratham Education Foundation (representative)  
**Focus states:** UP · Bihar · Rajasthan · Maharashtra · Gujarat · MP  
**Stack:** Python · Plotly Dash · SQLite/PostgreSQL · Google Sheets · Metabase
