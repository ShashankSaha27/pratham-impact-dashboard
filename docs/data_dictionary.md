# Data Dictionary
## Pratham Education Foundation — Impact Dashboard
### NSS Open Projects 2026 · Challenge 5.1

---

## Database: `pratham.db` (SQLite) / `pratham_dashboard` (PostgreSQL)

---

## Table: `enrollment`

Source: UDISE (Unified District Information System for Education), 2012–2020.
One row per district per academic year. 5,560 rows total.

| Column | Type | Formula / Source | Example | Notes |
|--------|------|-----------------|---------|-------|
| `ac_year` | TEXT | UDISE release year | `2019-20` | 8 years: 2012-13 to 2019-20 |
| `state_name` | TEXT | UDISE state field, title-cased | `Uttar Pradesh` | 36 states + UTs |
| `district_name` | TEXT | UDISE district field, uppercased | `VARANASI` | 680 unique districts |
| `class_1_boys` ... `class_12_boys` | INT | Raw UDISE enrollment count | `3420` | 12 columns, one per class |
| `class_1_girls` ... `class_12_girls` | INT | Raw UDISE enrollment count | `3198` | 12 columns, one per class |
| `total_boys` | INT | SUM(class_1_boys ... class_12_boys) | `28400` | All classes, boys |
| `total_girls` | INT | SUM(class_1_girls ... class_12_girls) | `26100` | All classes, girls |
| `total_enrollment` | INT | total_boys + total_girls | `54500` | Primary KPI for reach |
| `gpi` | FLOAT | total_girls / total_boys | `0.919` | Gender Parity Index. 1.0 = parity. Target: >=1.00 |
| `primary_retention_pct` | FLOAT | (class_5 / class_1) x 100, clipped 0-200 | `78.4` | % of Class 1 cohort reaching Class 5. Target: 90%. National avg: 82% |
| `sec_dropout_pct` | FLOAT | (1 - class_8 / class_6) x 100, clipped 0-100 | `22.1` | % of Class 6 students who leave before Class 8. Target: <10%. National avg: 17% |
| `hs_transition_pct` | FLOAT | (class_11 / class_10) x 100, clipped 0-300 | `64.3` | % of Class 10 students who continue to Class 11 |
| `dq_retention_anomaly` | INT | 1 if primary_retention_pct > 120 | `0` | Data quality flag. Exclude from averages if 1 |
| `dq_dropout_anomaly` | INT | 1 if sec_dropout_pct > 80 | `0` | Data quality flag. Likely data entry error |

---

## Table: `district_quality`

Source: DISE (District Information System for Education), 2015-16 Districtwise file.
One row per district. 680 rows total.

| Column | Type | Formula / Source | Example | Notes |
|--------|------|-----------------|---------|-------|
| `state_name` | TEXT | DISE STATNAME, title-cased | `Bihar` | |
| `district_name` | TEXT | DISE DISTNAME, uppercased | `GAYA` | Join key to enrollment table |
| `literacy_rate` | FLOAT | DISE OVERALL_LI | `63.7` | % of population who can read/write. National avg: 72.9% |
| `female_lit` | FLOAT | DISE FEMALE_LIT | `53.2` | Female literacy %. National avg: 64.6% |
| `male_lit` | FLOAT | DISE MALE_LIT | `74.1` | Male literacy % |
| `ptr` | FLOAT | ENRTOT / TCHTOT | `31.4` | Pupil-Teacher Ratio. Lower = better. Target: <=30. National avg: 26 |
| `girls_toilet_pct` | FLOAT | (SGTOILTOT / SCHTOT) x 100 | `87.3` | % of schools with separate girls toilet. Target: 95%. National avg: 92% |
| `mdm_pct` | FLOAT | (MDMTOT / SCHTOT) x 100 | `91.2` | % of schools serving Mid-Day Meal. Target: 95% |
| `repeater_rate_pct` | FLOAT | SUM(class 1-5 repeaters) / SUM(class 1-5 enrolled) x 100 | `4.1` | % of students repeating a grade |
| `single_tch_pct` | FLOAT | (STCHTOT / SCHTOT) x 100 | `12.3` | % of schools with only one teacher |
| `population` | INT | DISE TOTPOPULAT | `3842000` | District population (Census 2011 basis) |
| `sex_ratio` | INT | DISE SEXRATIO | `912` | Females per 1,000 males |
| `dq_ptr_anomaly` | INT | 1 if ptr > 100 or ptr < 5 | `0` | Data quality flag. PTR outside plausible range |

---

## Table: `secondary_results`

Source: DISE 2015-16 Statewise Secondary file (state board exam results).
One row per state. 36 rows total.

| Column | Type | Formula / Source | Example | Notes |
|--------|------|-----------------|---------|-------|
| `statname` | TEXT | DISE statname, title-cased | `Rajasthan` | Join key to enrollment (state level only) |
| `pass_rate` | FLOAT | (pass_b_gen + pass_g_gen) / (apr_b_gen + apr_g_gen) x 100 | `71.4` | Class 10 overall pass rate. Target: 85%. National avg: 73% |
| `pass_rate_boys` | FLOAT | pass_b_gen / apr_b_gen x 100 | `68.9` | Class 10 pass rate, boys only |
| `pass_rate_girls` | FLOAT | pass_g_gen / apr_g_gen x 100 | `74.2` | Class 10 pass rate, girls only |
| `pass_rate_sc` | FLOAT | (pass_b_sc + pass_g_sc) / (apr_b_sc + apr_g_sc) x 100 | `61.3` | Class 10 pass rate, Scheduled Caste students |
| `pass_rate_st` | FLOAT | (pass_b_st + pass_g_st) / (apr_b_st + apr_g_st) x 100 | `58.7` | Class 10 pass rate, Scheduled Tribe students |
| `appeared` | INT | apr_b_gen + apr_g_gen | `284000` | Total students who sat Class 10 exam |
| `passed` | INT | pass_b_gen + pass_g_gen | `202800` | Total students who passed Class 10 exam |

---

## View: `kpi_summary`

Pre-aggregated state x year KPIs. Created by `setup_db.py`. Used by Metabase.

| Column | Formula |
|--------|---------|
| `ac_year` | From enrollment |
| `state_name` | From enrollment |
| `total_enrollment` | SUM(total_enrollment) |
| `total_girls` | SUM(total_girls) |
| `total_boys` | SUM(total_boys) |
| `avg_gpi` | AVG(gpi) |
| `avg_retention_pct` | AVG(primary_retention_pct) |
| `avg_dropout_pct` | AVG(sec_dropout_pct) |
| `anomaly_count` | SUM(dq_retention_anomaly) |

---

## File: `field_data_demo.csv` / Google Sheet tab `field_data`

Source: `sheets_connector.generate_demo_field_data()` or live Google Sheet.
One row per class per school visit per week. 2,880 demo rows.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `date` | DATE | Week start date | `2026-03-10` |
| `week_number` | INT | Sequential week (1-12) | `7` |
| `state` | TEXT | State name | `Bihar` |
| `district` | TEXT | District name (uppercase) | `PATNA` |
| `class` | INT | Class number (1-8) | `4` |
| `boys_enrolled` | INT | Boys present this visit | `33` |
| `girls_enrolled` | INT | Girls present this visit | `28` |
| `teacher_present` | INT | 1 = teacher present, 0 = absent | `1` |
| `mdm_served` | INT | 1 = mid-day meal served, 0 = not | `1` |
| `data_source` | TEXT | `google_sheets_live` or `demo_csv` | `demo_csv` |

---

## File: `activity_data_demo.csv` / Google Sheet tab `activity_data`

Source: `activity_impact.generate_activity_data()` or live Google Sheet.
One row per activity instance per district per week. 1,247 demo rows.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `date` | DATE | Activity date | `2026-03-10` |
| `week_number` | INT | Sequential week (1-12) | `7` |
| `state` | TEXT | State name | `Uttar Pradesh` |
| `district` | TEXT | District name | `SHRAVASTI` |
| `activity_type` | TEXT | One of 7 types (see below) | `literacy_camp` |
| `sessions_held` | INT | Number of sessions this week | `4` |
| `children_reached` | INT | Total children across all sessions | `142` |
| `girls_reached` | INT | Girls specifically | `118` |
| `teachers_trained` | INT | Teachers trained (teacher_training only) | `0` |
| `duration_hours` | FLOAT | Total hours across all sessions | `9.5` |
| `data_source` | TEXT | Source identifier | `demo_generated` |

**Activity types and their KPI mappings:**

| `activity_type` | KPI it affects | Lag | Coefficient | R2 | Confidence |
|----------------|---------------|-----|-------------|----|-----------|
| `literacy_camp` | Primary Retention % | 8 weeks | +0.301 pp per 1pp literacy | 0.054 | medium |
| `remedial_class` | Class 10 Pass Rate | 16 weeks | +0.08 pp/session (estimated) | n/a | low |
| `enrollment_drive` | Total Enrollment / GPI | 2 weeks | +0.0006 GPI pts per 1pp MDM | 0.011 | medium |
| `community_mobilisation` | GPI | 4 weeks | +0.0006 per 1pp female lit | 0.011 | medium |
| `teacher_training` | PTR (quality proxy) | 12 weeks | -0.159 per 1 PTR unit | 0.007 | medium |
| `mdm_monitoring` | MDM Coverage % | 2 weeks | +0.190 pp per 1pp MDM | 0.031 | medium |
| `girls_safety_audit` | Girls Toilet Coverage % | 6 weeks | +0.0012 GPI per 1pp toilet | 0.009 | medium |

---

## File: `calibrated_effects.json`

Output of `calibrate_effects.py`. Loaded by `activity_impact.py` at startup.
Re-run `python calibrate_effects.py` after loading new UDISE data.

| Field | Description |
|-------|-------------|
| `coefficient` | OLS slope (within-state demeaned) |
| `r2` | R-squared of the regression |
| `p_value` | Two-tailed p-value |
| `ci_low` / `ci_high` | 95% confidence interval on the coefficient |
| `n` | Number of districts used in regression (max 627) |
| `method` | `OLS within-state demeaning (state FE)` |
| `confidence` | `high` (p<0.01, R2>=0.15) / `medium` (p<0.05) / `low` (p>=0.05) |
| `fitted` | `true` = data-fitted, `false` = assumed estimate |

---

## National benchmarks (hardcoded in `app.py` NATIONAL_AVG)

| KPI | National average | Source |
|-----|-----------------|--------|
| GPI | 1.01 | UDISE 2019-20 |
| Primary retention | 82% | UDISE 2019-20 |
| Secondary dropout | 17% | UDISE 2019-20 |
| Class 10 pass rate | 73% | DISE 2015-16 |
| PTR | 26 | DISE 2015-16 |
| Girls toilet coverage | 92% | DISE 2015-16 |
| Literacy rate | 72.9% | Census 2011 |
| Female literacy | 64.6% | Census 2011 |

---

## Data quality rules (agreed in KPI workshop, implemented in `setup_db.py`)

| Rule | Flag column | Dashboard action |
|------|------------|-----------------|
| Retention > 120% | `dq_retention_anomaly = 1` | Excluded from averages, counted in header banner |
| Dropout > 80% | `dq_dropout_anomaly = 1` | Excluded from averages |
| PTR > 100 or < 5 | `dq_ptr_anomaly = 1` | Excluded from PTR calculations |
| Missing pass rate | NULL in secondary_results | Shown as `--`, not interpolated |
| Zero enrollment district | total_enrollment = 0 | Excluded from charts |

---

## Files on disk

| File | Purpose |
|------|---------|
| `app.py` | Main Dash dashboard application |
| `setup_db.py` | Loads CSVs, computes KPIs, writes to SQLite/PostgreSQL |
| `sheets_connector.py` | Google Sheets live data connector + demo data generator |
| `activity_impact.py` | Activity-to-KPI mapping table and lag prediction model |
| `calibrate_effects.py` | OLS regression — fits activity effect sizes from UDISE data |
| `data/pratham.db` | SQLite database (dev) |
| `data/field_data_demo.csv` | 2,880 rows demo weekly field data |
| `data/activity_data_demo.csv` | 1,247 rows demo activity log data |
| `data/calibrated_effects.json` | OLS-fitted coefficients (output of calibrate_effects.py) |
| `kpi_tree.md` | Full KPI tree: activity to impact, every node documented |
| `kpi_workshop_output.md` | Mock KPI workshop with Pratham staff |
| `user_guide.md` | Non-technical guide for programme managers |
| `metabase_setup.md` | Metabase installation and connection guide |
| `data_dictionary.md` | This file |
| `requirements.txt` | Python dependencies |
