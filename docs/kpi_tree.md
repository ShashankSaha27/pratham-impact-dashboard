# KPI Tree — Pratham Education Foundation (Demo)
## Activity → Output → Outcome → Impact

*NSS Open Projects 2026 · Challenge 5.1*

---

## How to read this tree

Each level answers a different question:

| Level | Question | Measured by |
|-------|----------|-------------|
| **Activity** | What did we do? | Inputs deployed |
| **Output** | Who did we reach? | Enrollment & coverage |
| **Outcome** | Did behaviour or performance change? | Retention, pass rate, quality |
| **Impact** | Did lives structurally improve? | Literacy, equity, social change |

The causal logic: *Activities produce Outputs; sustained Outputs create Outcomes; Outcomes accumulate into Impact.*

---

## The Full KPI Tree

```
PRATHAM EDUCATION FOUNDATION
│
├── ACTIVITY (What we do)
│   ├── Districts covered
│   │     Source: count of distinct district_name in filtered UDISE data
│   │     Unit: number of districts
│   │     Dashboard: Theory of Change strip — "Schools reached"
│   │
│   ├── Schools reached
│   │     Source: SCHTOT column, 2015-16 District dataset
│   │     Unit: number of schools
│   │
│   └── Budget deployed
│         Source: User-entered in "Annual Budget (₹ Crore)" field
│         Unit: ₹ Crore
│         Dashboard: Budget input → feeds all cost-per-impact cards
│
├── OUTPUT (Who we reached)
│   ├── Total Enrollment
│   │     Formula: SUM(class_1_boys … class_12_girls)
│   │     Source: UDISE ac_year × state_name × district_name
│   │     Unit: number of children
│   │     Target: growing YoY
│   │     National avg: varies by state (used for benchmarking)
│   │     Dashboard: "Total Enrollment" KPI card + Trend chart
│   │
│   ├── Girls Enrolled
│   │     Formula: SUM(class_1_girls … class_12_girls)
│   │     Unit: number of girls
│   │     Dashboard: "Total Enrollment" card subtitle + Gender by Class chart
│   │
│   ├── Gender Parity Index (GPI)
│   │     Formula: total_girls / total_boys
│   │     Unit: ratio (1.0 = parity)
│   │     Target: ≥ 1.00  |  National avg: 1.01
│   │     Dashboard: "Gender Parity Index" KPI card + Equity bubble chart
│   │
│   └── Mid-Day Meal Coverage
│         Formula: MDMTOT / SCHTOT × 100
│         Source: 2015-16 District dataset
│         Unit: % of schools with MDM
│         Dashboard: "Mid-Day Meal Coverage" KPI card
│
├── OUTCOME (What changed)
│   ├── Primary Retention Rate                    ← CORE OUTCOME
│   │     Formula: Class5_enrollment / Class1_enrollment × 100
│   │     Unit: %
│   │     Target: ≥ 90%  |  National avg: 82%
│   │     Interpretation: % of children who entered Class 1 still in school at Class 5
│   │     Dashboard: "Primary Retention" KPI card + Funnel chart
│   │
│   ├── Secondary Dropout Rate
│   │     Formula: (1 − Class8 / Class6) × 100, clipped at 0
│   │     Unit: % (lower is better)
│   │     Target: ≤ 10%  |  National avg: 17%
│   │     Dashboard: "Secondary Dropout" KPI card + Insight Alerts
│   │
│   ├── Class 10 Pass Rate                        ← TRUE OUTCOME
│   │     Formula: passed_gen / appeared_gen × 100
│   │     Source: 2015-16 Statewise Secondary dataset
│   │     Unit: %
│   │     Target: ≥ 85%  |  National avg: 73%
│   │     Disaggregated by: Boys / Girls / SC / ST
│   │     Dashboard: "Class 10 Pass Rate" KPI card + Pass Rate charts
│   │
│   ├── Class 10-11 Transition Rate
│   │     Formula: Class11_enrollment / Class10_enrollment × 100
│   │     Unit: %
│   │     Target: ≥ 100% (all passers continue)
│   │     Dashboard: "Class 10-11 Transition %" line chart
│   │
│   ├── Pupil-Teacher Ratio (PTR)
│   │     Formula: ENRTOT / TCHTOT
│   │     Source: 2015-16 District dataset
│   │     Unit: students per teacher (lower is better)
│   │     Target: ≤ 30:1  |  National avg: 26:1
│   │     Dashboard: "Pupil-Teacher Ratio" KPI card + PTR scatter chart
│   │
│   └── Girls Toilet Coverage
│         Formula: SGTOILTOT / SCHTOT × 100
│         Source: 2015-16 District dataset
│         Unit: % of schools with girls toilet
│         Target: ≥ 95%  |  National avg: 92%
│         Note: Key driver of girls' secondary dropout
│         Dashboard: "Girls Toilet Coverage" KPI card + Equity bubble chart
│
└── IMPACT (Structural change)
    ├── District Literacy Rate
    │     Source: Census 2011, OVERALL_LI column
    │     Unit: %
    │     National avg: 72.9%
    │     Note: Literacy is the lagging indicator — it reflects 10+ years of education investment
    │     Dashboard: "Overall Literacy" KPI card
    │
    ├── Female Literacy Rate
    │     Source: Census 2011, FEMALE_LIT column
    │     Unit: %
    │     National avg: 64.6%
    │     Dashboard: "Female Literacy" KPI card
    │
    ├── Equity Gap Closure (SC/ST vs General pass rate)
    │     Formula: pass_rate_general − pass_rate_SC, pass_rate_general − pass_rate_ST
    │     Unit: percentage points gap (lower is better)
    │     Dashboard: "Equity Gap — General vs SC vs ST" bar chart
    │
    └── Primary Repeater Rate
          Formula: SUM(class_1-5 repeaters) / SUM(class_1-5 boys) × 100
          Source: C1_BR … C5_BR / C1_B … C5_B, 2015-16 District dataset
          Unit: % (lower is better)
          Note: High repetition is a leading indicator of eventual dropout
          Dashboard: "Primary Repeater Rate" KPI card
```

---

## Cost-per-Impact Bridge

These KPIs connect the Activity level (budget) to each Output and Outcome, enabling a donor-ready return-on-investment narrative.

| Cost Metric | Formula | What it tells a donor |
|-------------|---------|----------------------|
| **Cost per child enrolled** | Budget ÷ Total enrollment | Programme efficiency at scale |
| **Cost per child retained (Cl 5)** | Budget ÷ Children retained to Class 5 | Cost of keeping one child in school |
| **Cost per girl enrolled** | Budget ÷ Girls enrolled | Gender equity programme efficiency |
| **Cost per Class 10 passer** | Budget ÷ Passed board exam | Cost of one verifiable learning outcome |
| **Incremental cost per retained child** | Budget ÷ (retained − national baseline × total) | True SROI — cost above what would have happened anyway |

---

## Data Sources

| Dataset | Coverage | Granularity | Key KPIs sourced |
|---------|----------|-------------|-----------------|
| UDISE Enrollment | 2012-13 to 2019-20 | District × Year | Enrollment, GPI, Retention, Dropout, Transition |
| Education in India (Kaggle) — District | 2015-16 | District | PTR, Girls Toilet, MDM, Repeater Rate, Single-Teacher |
| Education in India (Kaggle) — Secondary | 2015-16 | State | Class 10 Pass Rate (Boys/Girls/SC/ST) |
| Census 2011 | Point-in-time | District | Literacy Rate, Female Literacy, Population |

---

## What this tree does NOT yet measure

These are genuine gaps that field data collection could fill:

| Missing KPI | Why it matters | How to collect |
|-------------|---------------|----------------|
| Learning levels (reading/arithmetic) | Pass rate ≠ learning; ASER data shows this gap | ASER annual survey or internal testing |
| Attendance rate | A child enrolled ≠ a child attending | Daily/weekly field log → Google Sheet |
| Teacher attendance | PTR is meaningless if teachers are absent | Monthly school visit checklist |
| Parent awareness of education | Behavioural outcome | Annual beneficiary survey |
| Income change for families | Long-term impact | 3-year longitudinal tracking |
