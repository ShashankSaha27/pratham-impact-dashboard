# Metabase Setup Guide
## Connect Metabase to the Pratham Dashboard Database

Metabase gives non-technical staff a self-service way to explore the data,
ask ad-hoc questions ("Which 5 districts have the lowest GPI in Bihar?"),
and build their own charts — without writing any code.

---

## Step 1 — Install Java

Metabase requires Java 11+.

Download: https://adoptium.net/temurin/releases/?version=11
- Choose: Windows x64 → JDK → .msi installer
- Install with defaults
- Verify: open a new terminal and run `java -version`

---

## Step 2 — Download Metabase

```
# In PowerShell, from C:\project\nss_dashboard\
Invoke-WebRequest -Uri "https://downloads.metabase.com/v0.50.0/metabase.jar" -OutFile "metabase.jar"
```

---

## Step 3 — Run Metabase

```
# SQLite backend (development)
java -jar metabase.jar

# Or with PostgreSQL
set MB_DB_TYPE=postgres
set MB_DB_DBNAME=pratham_dashboard
set MB_DB_PORT=5432
set MB_DB_USER=postgres
set MB_DB_PASS=yourpassword
set MB_DB_HOST=localhost
java -jar metabase.jar
```

Open: http://localhost:3000
Complete the setup wizard (create admin account).

---

## Step 4 — Connect to the Pratham database

In Metabase setup wizard, choose "Add a database":

**For SQLite (development):**
- Database type: H2 (SQLite is accessed via H2 file path)
- Connection string: `file:C:/project/nss_dashboard/data/pratham`
- Display name: Pratham Education Data

**For PostgreSQL (production):**
- Database type: PostgreSQL
- Host: localhost
- Port: 5432
- Database name: pratham_dashboard
- Username/Password: your credentials

---

## Step 5 — Key tables to explore

| Table | What it contains | Good first question |
|-------|-----------------|---------------------|
| `enrollment` | District × year enrollment + KPIs | "Which states have GPI below 0.9?" |
| `district_quality` | PTR, toilets, MDM, literacy | "Which districts have PTR above 40?" |
| `secondary_results` | State-level Class 10 pass rates | "Which states have ST pass rate below 50%?" |
| `kpi_summary` (view) | Pre-aggregated state × year KPIs | "Show retention trend by state" |

---

## Step 6 — Suggested Metabase questions to save

These map directly to the Pratham KPI tree:

1. **Monday check**: `SELECT state_name, ROUND(AVG(primary_retention_pct),1) as retention FROM enrollment WHERE ac_year = '2019-20' GROUP BY state_name ORDER BY retention ASC LIMIT 10`

2. **GPI alert**: `SELECT state_name, district_name, ROUND(AVG(gpi),3) as gpi FROM enrollment GROUP BY state_name, district_name HAVING gpi < 0.9 ORDER BY gpi ASC`

3. **Equity gap**: `SELECT statname, pass_rate, pass_rate_sc, pass_rate_st, ROUND(pass_rate - pass_rate_st, 1) as equity_gap FROM secondary_results ORDER BY equity_gap DESC`

4. **Data quality**: `SELECT state_name, SUM(dq_retention_anomaly) as anomalies, COUNT(*) as total FROM enrollment GROUP BY state_name ORDER BY anomalies DESC`

---

## Metabase vs Dash — when to use which

| Use case | Metabase | Dash (this app) |
|----------|----------|-----------------|
| ED Monday check | Yes — saved question, email digest | Yes — Insight Alerts |
| Ad-hoc exploration | Yes — drag-and-drop | No |
| Cost-per-impact with live budget input | No | Yes |
| Theory of Change visual | No | Yes |
| Automated insight alerts | Partial (subscriptions) | Yes — real-time |
| Non-technical staff self-service | Yes | Partial |

**Recommendation**: Run both. Metabase for exploration and email digests to the board. Dash for the board meeting presentation view.
