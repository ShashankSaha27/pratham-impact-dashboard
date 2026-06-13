# Mock KPI Workshop Output
## Pratham Education Foundation × NSS Challenge 5.1
### Session date: June 2026 | Participants: Programme Director, M&E Lead, State Coordinator (UP)

---

## Workshop objective

Agree on the 6-8 KPIs that will appear on the board dashboard, their definitions,
data owners, and what "good" looks like. Everything else goes to an analyst view.

---

## Part 1 — What decisions does this dashboard need to support?

*Answers from participants:*

| Decision | Who makes it | How often |
|----------|-------------|-----------|
| Which districts to intensify in next quarter | Programme Director | Quarterly |
| Whether to request emergency budget reallocation | ED + Finance | Ad-hoc |
| Which states to report as "on track" to donors | M&E Lead | Monthly |
| Where to deploy the next batch of field coordinators | State Coordinator | Monthly |
| Is our girls' programme working in UP? | State Coordinator | Weekly |

**Workshop conclusion:** The dashboard must answer "where are we falling behind and by how much?" — not just "what is the number."

---

## Part 2 — Activity → Output → Outcome → Impact mapping

*Participants mapped their work to the four levels:*

### ACTIVITY (what we control)
- Field coordinator visits per district per month
- Teacher training sessions delivered
- Community mobilisation events held
- **Agreed dashboard KPI:** Districts covered (proxy for activity reach)

### OUTPUT (what we produce)
- Children enrolled in programme schools
- Girls enrolled specifically
- Gender parity achieved
- **Agreed dashboard KPIs:** Total enrollment, GPI, MDM coverage

### OUTCOME (what changes)
- Children retained through primary school ← *"This is our core outcome"* (Programme Director)
- Children passing Class 10 ← *"This is the proof of learning"* (M&E Lead)
- Secondary dropout reduced
- **Agreed dashboard KPIs:** Primary retention %, Class 10 pass rate, secondary dropout %

### IMPACT (structural change)
- District literacy rate improves over 10 years
- Equity gap between General/SC/ST narrows
- **Agreed dashboard KPIs:** Female literacy rate, SC/ST equity gap

---

## Part 3 — KPI definitions agreed

| KPI | Formula agreed | Data source | Owner | Target | Rationale |
|-----|---------------|-------------|-------|--------|-----------|
| Total Enrollment | Sum of all class enrollments | UDISE annual | M&E Lead | YoY growth | Baseline reach metric |
| GPI | Girls enrolled / Boys enrolled | UDISE annual | State Coordinator | 1.00 | Core gender equity metric |
| Primary Retention | Class 5 enrollment / Class 1 enrollment × 100 | UDISE annual | M&E Lead | 90% | *"If a child reaches Class 5, they almost always finish school"* |
| Secondary Dropout | (1 − Class8/Class6) × 100 | UDISE annual | State Coordinator | <10% | Critical transition point for girls |
| Class 10 Pass Rate | Passed / Appeared × 100 | Board results (state) | M&E Lead | 85% | Only verifiable learning outcome available |
| Girls Toilet Coverage | Schools with toilets / Total schools × 100 | DISE infrastructure | Programme Director | 95% | *"No toilet = girls stop coming at puberty"* |

**Rejected KPIs (too hard to get or already covered):**
- Teacher attendance — not in UDISE (action: add to field data collection)
- Learning levels — not available (action: run ASER-style test annually)
- Household income — too expensive to track (defer to 3-year eval)

---

## Part 4 — Data quality rules agreed

| Rule | What to do |
|------|-----------|
| Retention > 120% | Flag as anomaly, exclude from averages, notify district |
| PTR > 100 | Data entry error, flag and exclude |
| Zero enrollment district | Exclude from charts, count in "data quality" banner |
| Missing pass rate | Show "—", do not interpolate |

*"We would rather show a gap than show a wrong number."* — M&E Lead

---

## Part 5 — Cadence agreed

| KPI level | Update cadence | Who updates |
|-----------|---------------|-------------|
| Activity (field visits, teacher training) | Weekly | Field coordinators via Google Sheet |
| Output (enrollment, GPI) | Annual (UDISE release) | M&E Lead |
| Outcome (retention, pass rate) | Annual | M&E Lead |
| Impact (literacy, equity) | Every 3 years (Census) | M&E Lead |

**Monday check agreed:** Primary Retention Rate for Pratham focus states, current year vs previous year, flagging any district >5pp below target.

---

## Part 6 — Actions from workshop

| Action | Owner | By when |
|--------|-------|---------|
| Set up Google Sheet template for field coordinators | Tech team | Week 1 |
| Confirm pass rate data source with state education dept | M&E Lead | Week 2 |
| Define district-level targets (not just national) | Programme Director | Week 3 |
| Train field coordinators on weekly data entry | State Coordinator | Month 1 |
| First board presentation using dashboard | ED | Month 2 |

---

*This document captures the KPI agreements from the workshop. The dashboard at http://127.0.0.1:8050 implements all agreed KPIs as of this date.*
