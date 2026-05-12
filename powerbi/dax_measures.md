# DAX Measures — Global Health Trend Analysis Dashboard
## Power BI · Consulting-Grade Analytics Layer

> Copy each measure into Power BI Desktop via **Modeling → New Measure**.
> All measures assume the data model has tables: `FactCovid`, `FactVaccination`, `DimCountry`, `DimDate`.

---

## Table: FactCovid Columns Reference
| Column | Type | Description |
|--------|------|-------------|
| Country | Text | Country name |
| Date | Date | Observation date |
| Confirmed | Whole Number | Cumulative confirmed cases |
| Deaths | Whole Number | Cumulative deaths |
| Recovered | Whole Number | Cumulative recovered |
| NewCases | Whole Number | Daily new cases |
| NewDeaths | Whole Number | Daily new deaths |
| ActiveCases | Whole Number | Active case estimate |
| CFR | Decimal | Case fatality rate (%) |
| RecoveryRate | Decimal | Recovery rate (%) |
| NewCases_rolling7d | Decimal | 7-day rolling avg of new cases |
| NewDeaths_rolling7d | Decimal | 7-day rolling avg of new deaths |
| daily_growth_rate | Decimal | Daily growth rate (%) |
| CasesPer100k | Decimal | Cases per 100,000 population |
| DeathsPer100k | Decimal | Deaths per 100,000 population |
| RiskTier | Text | Low / Medium / High / Critical |
| Continent | Text | Geographic continent |
| VaxPctFull | Decimal | Fully vaccinated (%) |
| VaxPct1Dose | Decimal | At least 1 dose (%) |

---

## Section 1 — Core KPI Measures

```dax
-- ── Total Confirmed Cases ──────────────────────────────────────────────────
Total Confirmed Cases = 
SUM(FactCovid[Confirmed])

-- ── Total Deaths ────────────────────────────────────────────────────────────
Total Deaths = 
SUM(FactCovid[Deaths])

-- ── Total Recovered ─────────────────────────────────────────────────────────
Total Recovered = 
SUM(FactCovid[Recovered])

-- ── Active Cases ────────────────────────────────────────────────────────────
Active Cases = 
SUM(FactCovid[ActiveCases])

-- ── Case Fatality Rate (%) ──────────────────────────────────────────────────
Case Fatality Rate % = 
DIVIDE(
    SUM(FactCovid[Deaths]),
    SUM(FactCovid[Confirmed]),
    0
) * 100

-- ── Recovery Rate (%) ───────────────────────────────────────────────────────
Recovery Rate % = 
DIVIDE(
    SUM(FactCovid[Recovered]),
    SUM(FactCovid[Confirmed]),
    0
) * 100

-- ── Mortality Rate (%) ──────────────────────────────────────────────────────
Mortality Rate % = 
[Case Fatality Rate %]

-- ── Countries Affected ──────────────────────────────────────────────────────
Countries Affected = 
DISTINCTCOUNT(FactCovid[Country])
```

---

## Section 2 — Time Intelligence & Rolling Averages

```dax
-- ── 7-Day Rolling Average New Cases ────────────────────────────────────────
7D Rolling Avg New Cases = 
CALCULATE(
    AVERAGEX(
        DATESINPERIOD(DimDate[Date], LASTDATE(DimDate[Date]), -7, DAY),
        CALCULATE(SUM(FactCovid[NewCases]))
    )
)

-- ── 7-Day Rolling Average New Deaths ───────────────────────────────────────
7D Rolling Avg New Deaths = 
CALCULATE(
    AVERAGEX(
        DATESINPERIOD(DimDate[Date], LASTDATE(DimDate[Date]), -7, DAY),
        CALCULATE(SUM(FactCovid[NewDeaths]))
    )
)

-- ── 30-Day Rolling Avg New Cases ───────────────────────────────────────────
30D Rolling Avg New Cases = 
CALCULATE(
    AVERAGEX(
        DATESINPERIOD(DimDate[Date], LASTDATE(DimDate[Date]), -30, DAY),
        CALCULATE(SUM(FactCovid[NewCases]))
    )
)

-- ── Month-over-Month Cases Growth (%) ──────────────────────────────────────
MoM Cases Growth % = 
VAR CurrentMonthCases = CALCULATE(
    SUM(FactCovid[NewCases]),
    DATESMTD(DimDate[Date])
)
VAR PrevMonthCases = CALCULATE(
    SUM(FactCovid[NewCases]),
    PREVIOUSMONTH(DimDate[Date])
)
RETURN
DIVIDE(CurrentMonthCases - PrevMonthCases, PrevMonthCases, 0) * 100

-- ── Year-over-Year Cases Growth (%) ────────────────────────────────────────
YoY Cases Growth % = 
VAR CurrentYearCases = CALCULATE(
    SUM(FactCovid[Confirmed]),
    DATESYTD(DimDate[Date])
)
VAR PrevYearCases = CALCULATE(
    SUM(FactCovid[Confirmed]),
    SAMEPERIODLASTYEAR(DimDate[Date])
)
RETURN
DIVIDE(CurrentYearCases - PrevYearCases, PrevYearCases, 0) * 100

-- ── Cumulative Cases to Date ────────────────────────────────────────────────
Cumulative Confirmed = 
CALCULATE(
    SUM(FactCovid[Confirmed]),
    FILTER(
        ALL(DimDate[Date]),
        DimDate[Date] <= MAX(DimDate[Date])
    )
)

-- ── Peak Daily Cases (All Time) ─────────────────────────────────────────────
Peak Daily New Cases = 
MAXX(
    SUMMARIZE(FactCovid, FactCovid[Date], "DayCases", SUM(FactCovid[NewCases])),
    [DayCases]
)

-- ── Date of Peak Cases ──────────────────────────────────────────────────────
Peak Cases Date = 
VAR MaxCases = [Peak Daily New Cases]
RETURN
CALCULATE(
    MAX(FactCovid[Date]),
    FILTER(FactCovid, SUM(FactCovid[NewCases]) = MaxCases)
)
```

---

## Section 3 — KPI Card Variance Indicators

```dax
-- ── KPI Card: Cases vs Previous Month ──────────────────────────────────────
Cases vs Prev Month = 
VAR Current = CALCULATE(SUM(FactCovid[NewCases]), DATESMTD(DimDate[Date]))
VAR Previous = CALCULATE(SUM(FactCovid[NewCases]), PREVIOUSMONTH(DimDate[Date]))
RETURN Current - Previous

-- ── KPI Card Indicator Text ────────────────────────────────────────────────
Cases Trend Indicator = 
VAR Delta = [Cases vs Prev Month]
RETURN
IF(Delta > 0, "▲ " & FORMAT(ABS(Delta), "#,0") & " vs prev month",
   IF(Delta < 0, "▼ " & FORMAT(ABS(Delta), "#,0") & " vs prev month",
   "→ Unchanged vs prev month"))

-- ── Deaths vs Previous Month ────────────────────────────────────────────────
Deaths vs Prev Month = 
VAR Current = CALCULATE(SUM(FactCovid[NewDeaths]), DATESMTD(DimDate[Date]))
VAR Previous = CALCULATE(SUM(FactCovid[NewDeaths]), PREVIOUSMONTH(DimDate[Date]))
RETURN Current - Previous
```

---

## Section 4 — Risk & Classification

```dax
-- ── Countries in Critical Risk ──────────────────────────────────────────────
Critical Risk Countries = 
CALCULATE(
    DISTINCTCOUNT(FactCovid[Country]),
    FactCovid[RiskTier] = "Critical"
)

-- ── Countries in High Risk ──────────────────────────────────────────────────
High Risk Countries = 
CALCULATE(
    DISTINCTCOUNT(FactCovid[Country]),
    FactCovid[RiskTier] = "High"
)

-- ── Risk Score (Composite: 0-100) ─────────────────────────────────────────
Risk Score = 
VAR cfr_norm = DIVIDE([Case Fatality Rate %], 10, 0)
VAR growth_norm = DIVIDE(AVERAGE(FactCovid[daily_growth_rate]), 20, 0)
VAR active_norm = DIVIDE([Active Cases], 1000000, 0)
RETURN
MIN(
    (cfr_norm * 0.4) + (growth_norm * 0.35) + (active_norm * 0.25),
    100
) * 100

-- ── Conditional Formatting: CFR Color ──────────────────────────────────────
CFR Color = 
VAR cfr = [Case Fatality Rate %]
RETURN
SWITCH(TRUE(),
    cfr >= 5.0, "#FF4444",
    cfr >= 3.0, "#FF8C00",
    cfr >= 1.5, "#FFD700",
    "#00C49A"
)
```

---

## Section 5 — Vaccination Measures

```dax
-- ── Average Fully Vaccinated % ──────────────────────────────────────────────
Avg Fully Vaccinated % = 
AVERAGE(FactCovid[VaxPctFull])

-- ── Population Vaccinated % (Latest) ──────────────────────────────────────
Latest Vax Full % = 
CALCULATE(
    AVERAGE(FactCovid[VaxPctFull]),
    LASTDATE(DimDate[Date])
)

-- ── Vaccination vs CFR Correlation Label ────────────────────────────────────
Vax CFR Insight = 
VAR vax = [Avg Fully Vaccinated %]
VAR cfr = [Case Fatality Rate %]
RETURN
"Vax: " & FORMAT(vax, "0.0") & "% | CFR: " & FORMAT(cfr, "0.00") & "%"
```

---

## Section 6 — Continent & Regional Analysis

```dax
-- ── Continent New Cases Share (%) ──────────────────────────────────────────
Continent Cases Share % = 
DIVIDE(
    SUM(FactCovid[NewCases]),
    CALCULATE(SUM(FactCovid[NewCases]), ALL(DimCountry[Continent])),
    0
) * 100

-- ── Selected Continent Cases ───────────────────────────────────────────────
Selected Region Cases = 
CALCULATE([Total Confirmed Cases], ALLEXCEPT(DimCountry, DimCountry[Continent]))

-- ── Continent Rank by Cases ─────────────────────────────────────────────────
Continent Cases Rank = 
RANKX(
    ALL(DimCountry[Continent]),
    CALCULATE(SUM(FactCovid[Confirmed])),
    ,
    DESC,
    DENSE
)
```

---

## Section 7 — Sparkline & Trend Measures

```dax
-- ── Last 30 Days New Cases (for sparklines) ─────────────────────────────────
Last30D New Cases = 
CALCULATE(
    SUM(FactCovid[NewCases]),
    DATESINPERIOD(DimDate[Date], LASTDATE(DimDate[Date]), -30, DAY)
)

-- ── Last 30 Days New Deaths (for sparklines) ────────────────────────────────
Last30D New Deaths = 
CALCULATE(
    SUM(FactCovid[NewDeaths]),
    DATESINPERIOD(DimDate[Date], LASTDATE(DimDate[Date]), -30, DAY)
)

-- ── Trend Direction (Up/Down/Stable) ───────────────────────────────────────
Trend Direction = 
VAR Recent7D = CALCULATE(
    SUM(FactCovid[NewCases]),
    DATESINPERIOD(DimDate[Date], LASTDATE(DimDate[Date]), -7, DAY)
)
VAR Prev7D = CALCULATE(
    SUM(FactCovid[NewCases]),
    DATESINPERIOD(DimDate[Date], DATEADD(LASTDATE(DimDate[Date]), -7, DAY), -7, DAY)
)
VAR PctChange = DIVIDE(Recent7D - Prev7D, Prev7D, 0) * 100
RETURN
SWITCH(TRUE(),
    PctChange > 10,  "↑ Rising",
    PctChange < -10, "↓ Declining",
    "→ Stable"
)
```
