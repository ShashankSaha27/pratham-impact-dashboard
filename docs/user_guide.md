# User Guide — Pratham Education Impact Dashboard
### For programme managers and NGO staff — no technical knowledge needed

---

## What is this dashboard?

This dashboard turns raw government school data into plain-English numbers that answer three questions a board or donor cares about:

1. **Are we reaching enough children?** (Enrollment & demographic reach)
2. **Are children staying in school and learning?** (Retention, pass rate, dropout)
3. **Is our money being spent effectively?** (Cost-per-impact)

You do **not** need to know anything about data, spreadsheets, or technology to read it.

---

## Starting the dashboard

1. Double-click the terminal window that is already running, OR ask your tech team to run `python app.py`
2. Open any web browser (Chrome, Edge, Firefox)
3. Go to: **http://127.0.0.1:8050**
4. The dashboard loads automatically — it refreshes every 60 seconds

---

## The page from top to bottom

### 1. Header bar
Shows the NGO name, tagline, and the time data was last refreshed. If the time is not updating, ask your tech team to check the data connection.

---

### 2. Theory of Change strip
A chain of boxes: **Activity → Output → Output → Outcome → Outcome → Outcome → Impact**

Each box shows a live number from your selected filters. This strip answers: *"Is our causal chain intact?"*

- If **Enrollment** is high but **Retention** is low → children are joining but leaving early
- If **Retention** is high but **Pass Rate** is low → children are staying but not learning
- If **Pass Rate** is high but **Literacy** is still low → it takes years for outcomes to show in census data

---

### 3. Insight Alerts (red / amber / green boxes)

These are auto-generated findings. You do not need to read every chart — the alerts tell you what needs attention.

| Colour | Meaning |
|--------|---------|
| 🔴 Red | Critical — more than 20% below target, act now |
| 🟠 Amber | Warning — approaching threshold, monitor closely |
| 🟢 Green | On track — meeting or exceeding target |

Each alert names the **specific districts** that are worst-performing, so you know exactly where to focus.

---

### 4. Filters (Year / State / District / Budget)

Use these to zoom in on your programme area.

| Filter | What to do |
|--------|-----------|
| **Academic Years** | Select the years your programme was active |
| **State / Programme Area** | Select the states you work in |
| **District** | Auto-fills when you select states; narrow further if needed |
| **Annual Budget (₹ Crore)** | Type your programme's annual spend — this powers the cost cards below |

**Tip:** Start with all years and your focus states. Narrow to specific districts only when an alert flags a problem.

---

### 5. Programme Targets — Edit Targets button

Click **Edit Targets** to set your own goals. Defaults are:

| KPI | Default target | What it means |
|-----|---------------|---------------|
| GPI | 1.00 | Equal girls and boys |
| Primary Retention | 90% | 9 in 10 Class-1 children reach Class 5 |
| Secondary Dropout | 10% | No more than 1 in 10 leave between Class 6-8 |
| Class 10 Pass Rate | 85% | 85 in 100 students pass board exams |
| Girls Toilet Coverage | 95% | Nearly all schools have a girls toilet |
| Pupil-Teacher Ratio | 30 | No more than 30 students per teacher |

These targets update all the progress bars, alert thresholds, and benchmark lines on charts.

---

### 6. Programme Progress bars

Six horizontal bars — one per KPI. Each bar shows:
- **Current value** on the left
- **Target** on the right
- **National average** as a reference point
- Colour: 🟢 Green (≥90% of target) · 🟡 Amber (70-90%) · 🔴 Red (<70%)

A bar that is red and below the national average means your programme area is performing worse than India overall — this is the highest-priority finding.

---

### 7. Cost-per-Impact cards (orange section)

Once you enter a budget, four cards appear:

| Card | Plain-English meaning |
|------|----------------------|
| **Cost per child enrolled** | For every rupee spent, how many children are in school |
| **Cost per child retained** | What it costs to keep one child in school through Class 5 |
| **Cost per girl enrolled** | Cost of the gender equity component |
| **Cost per Class 10 passer** | What it costs to produce one verified board-exam pass |

Each card also shows an **incremental cost** — what it costs to achieve results *above* what would have happened nationally without the programme. This is the number to use in donor reports.

---

### 8. Output KPI cards (blue section)

| Card | What to look for |
|------|-----------------|
| **Total Enrollment** | Should grow year-on-year. Arrow (▲/▼) shows change vs prior year |
| **Gender Parity Index** | Should be close to 1.00. Below 0.90 in any district is a red flag |
| **Primary Retention** | Should be above 90%. National average is 82% |
| **Secondary Dropout** | Should be below 10%. National average is 17% |

Each card shows a small note: *"national avg: X"* — this is the India-wide benchmark. If your number is above the national average, your programme is outperforming the baseline.

---

### 9. Outcome KPI cards (quality section)

| Card | What to look for |
|------|-----------------|
| **Class 10 Pass Rate** | Above 85% target. National average 73% |
| **Pupil-Teacher Ratio** | Lower is better. Above 40:1 signals a teacher shortage |
| **Mid-Day Meal Coverage** | Higher is better. MDM is proven to improve attendance |
| **Girls Toilet Coverage** | Below 80% is directly linked to girls dropping out at secondary level |

---

### 10. Impact KPI cards (structural section)

| Card | What to look for |
|------|-----------------|
| **Overall Literacy** | Census 2011 benchmark. Slow to change — reflects 10 years of work |
| **Female Literacy** | The long-term impact of girls' education investment |
| **Primary Repeater Rate** | Children repeating grades is an early warning sign of dropout |
| **Single-Teacher Schools** | High % means quality risk — one teacher cannot run a full school |

---

### 11. Charts

#### Enrollment Trend
- Blue = boys, Pink = girls (stacked bars)
- Green dotted line = year-on-year growth % (read on right axis)
- **What to look for:** Green line staying positive. A dip means enrollment fell that year.

#### Enrollment by Class & Gender
- A sharp drop between any two classes is a **dropout hotspot**
- If girls drop sharply at Class 6-8, this is early marriage / safety-related dropout

#### Top 15 Districts by Enrollment
- Darker = more children. These are your highest-reach districts.
- Compare with the alert panel — are your biggest districts also your worst performers?

#### Enrollment Funnel (Class 1 to 12)
- Shows how many children are left at each grade level
- The percentage shown is "out of every 100 children who started Class 1"
- A funnel that narrows sharply at Class 6 or Class 9 signals a transition dropout problem

#### Class 10 to 11 Transition
- Below the 100% dotted line means students are stopping after board exams
- A declining trend is serious — it suggests economic pressure is pulling children out after Class 10

#### Class 10 Pass Rate — Boys vs Girls
- The red dotted line is your target; the grey dashed line is the national average
- States where girls score lower than boys need gender-specific support
- States below the national average line need urgent programme attention

#### Equity Gap — General vs SC vs ST
- Compares board exam pass rates across social groups
- A large gap between General and ST means marginalised children are being left behind
- This chart is the most important one for equity-focused reporting to donors

#### PTR vs Literacy Scatter
- Each dot is a district. Higher PTR (right) = more crowded classrooms
- Dots in the bottom-right corner (high PTR, low literacy) are your priority districts
- The red line is your PTR target; grey dashed line is the national average

#### Equity Bubble Chart (Girls Toilet vs GPI)
- Bubble size = district population
- Colour = Mid-Day Meal coverage (darker green = better)
- Districts below the grey horizontal line (GPI < 1.0) have fewer girls than boys in school
- Districts in the bottom-left (low toilet coverage, low GPI) are the clearest equity failures

---

## Common questions

**Q: An alert says "⚠ Secondary Dropout Exceeds Target" — what should I do?**
The alert names the specific districts. Visit those districts first. Common causes: distance to secondary school, cost of uniforms/fees, early marriage for girls, child labour for boys.

**Q: My cost-per-child number seems very high. Is that normal?**
Check your budget entry (₹ Crore) and the number of districts selected. If you're selecting all of India but running a programme in 5 districts, the cost will appear low. Narrow filters to your actual programme area.

**Q: The pass rate shows "—" (a dash).**
Pass rate data is only available for 2015-16 (from the government dataset). Select years that include 2015-16, or check that your selected states have data in the source file.

**Q: GPI is above 1.0 — is that bad?**
No. GPI > 1.0 means more girls than boys are enrolled in that area, which is a positive outcome in historically low-enrolment regions. However, check the enrollment funnel — girls may enroll more at primary level but drop at secondary.

**Q: The dashboard is slow.**
Select fewer districts (under 50) or fewer years. The full national dataset has over 100,000 rows.

**Q: How do I update the data?**
Replace the CSV files in the `data/` folder with new versions and restart the app (`python app.py`). Column names must remain the same. For live updates, ask your tech team about connecting to a Google Sheet.

---

## Glossary

| Term | Plain-English meaning |
|------|-----------------------|
| **GPI** | Gender Parity Index — ratio of girls to boys enrolled (1.0 = equal) |
| **PTR** | Pupil-Teacher Ratio — how many students per teacher |
| **MDM** | Mid-Day Meal — free school lunch programme |
| **SC / ST** | Scheduled Caste / Scheduled Tribe — India's constitutionally protected marginalised groups |
| **UDISE** | Unified District Information System for Education — India's official school census |
| **National avg** | The India-wide average for that indicator, used as a baseline benchmark |
| **Incremental cost** | Cost to achieve results above what would have happened without the programme |
| **YoY** | Year-on-Year — comparing this year to the previous year |

---

*For data definitions and column-level documentation, see `data_dictionary.md`.*
*For the full KPI logic and Theory of Change, see `kpi_tree.md`.*
