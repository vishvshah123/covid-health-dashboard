# Power BI Dashboard — Build Guide
## Global Health Trend Analysis Dashboard

This guide walks you through building the **consulting-grade Power BI report** step-by-step.
Follow the pages in order after loading the processed data.

---

## Step 1: Load Data

1. Open **Power BI Desktop**
2. Go to **Home → Get Data → Text/CSV**
3. Load all files from `data/processed/` in this order:
   - `covid_global.csv` → rename query to **FactCovid**
   - `vaccination_data.csv` → rename to **FactVaccination**
   - `covid_monthly.csv` → rename to **CovidMonthly**
   - `covid_latest.csv` → rename to **CovidLatest**
   - `dim_country.csv` → rename to **DimCountry**
   - `dim_date.csv` → rename to **DimDate**

4. In **Power Query Editor**, apply the M scripts from `powerquery_m_scripts.md`
5. Click **Close & Apply**

---

## Step 2: Build Data Model

In **Model View**:
- Connect `FactCovid[DateKey]` → `DimDate[DateKey]` (Many-to-One)
- Connect `FactCovid[Country]` → `DimCountry[Country]` (Many-to-One)
- Connect `FactVaccination[Country]` → `DimCountry[Country]` (Many-to-One)
- Hide all foreign key columns from Report View

---

## Step 3: Import DAX Measures

Create a new **Measures Table** (empty table named "Measures"):
1. Modeling → New Table → `Measures = {}`
2. Add all measures from `dax_measures.md` to this table

---

## Step 4: Apply Theme

1. **View → Themes → Browse for themes**
2. Select the JSON file from `powerbi/theme_dark.json`
   (Copy the JSON from `powerquery_m_scripts.md` and save as `theme_dark.json`)

---

## Step 5: Build Dashboard Pages

### Page 1: Executive Overview
**Background:** #0D1117 (set via Format → Canvas background)

**Layout:**
```
┌──────────────────────────────────────────────────────────────┐
│  🌍 GLOBAL HEALTH TREND ANALYSIS          [Date Slicer]      │
├──────────┬──────────┬──────────┬──────────┬──────────────────┤
│  KPI     │  KPI     │  KPI     │  KPI     │  KPI             │
│ Confirmed│ Deaths   │ Recovered│ Active   │ CFR %            │
├──────────┴──────────┴──────────┴──────────┴──────────────────┤
│                                                              │
│         CHOROPLETH WORLD MAP (Confirmed Cases)               │
│              [ArcGIS / Shape Map visual]                     │
│                                                              │
├─────────────────────────┬────────────────────────────────────┤
│  Top 10 Countries       │  Global Daily New Cases            │
│  (Horizontal Bar Chart) │  (Line + Area Chart, 7D MA)        │
└─────────────────────────┴────────────────────────────────────┘
```

**Visuals:**
- **5 KPI Cards** with:
  - Value: `[Total Confirmed Cases]`, `[Total Deaths]`, etc.
  - Trend line from `DimDate`
  - Conditional color formatting
- **Shape Map** (or Filled Map):
  - Location: `DimCountry[Country]`
  - Color saturation: `[Total Confirmed Cases]`
  - Tooltips: Country, Confirmed, Deaths, CFR, Risk Tier
- **Horizontal Bar Chart** (Top 10):
  - Axis: `FactCovid[Country]`
  - Value: `[Total Confirmed Cases]`
  - Color by `DimCountry[Continent]`
  - Apply TopN filter: Top 10 by `[Total Confirmed Cases]`
- **Line + Area Chart** (Global Trend):
  - X-axis: `DimDate[Date]`
  - Values: `SUM(FactCovid[NewCases])`, `[7D Rolling Avg New Cases]`

---

### Page 2: Trend Analysis
**Visuals:**
- **Line Chart** — Daily New Cases over time:
  - X: `DimDate[Date]`
  - Values: `[7D Rolling Avg New Cases]`, `[7D Rolling Avg New Deaths]`
  - Legend: Metric name
- **Area Chart** — Cumulative cases:
  - X: `DimDate[Date]`
  - Y: `[Cumulative Confirmed]`
- **Stacked Column** — Monthly New Cases by Continent:
  - X: `DimDate[YearMonth]`
  - Values: `SUM(FactCovid[NewCases])`
  - Legend: `DimCountry[Continent]`
- **Ribbon Chart** — Continent ranking over months:
  - X: `DimDate[YearMonth]`
  - Values: `SUM(FactCovid[Confirmed])`
  - Legend: `DimCountry[Continent]`
- **Slicers**: Year, Continent, Country (multi-select)

---

### Page 3: Country Deep-Dive
**Visuals:**
- **Country Slicer** (Search enabled): `DimCountry[Country]`
- **KPI Cards** (Country-specific):
  - Total Cases, Deaths, CFR %, Recovery %, Active Cases
  - With "vs previous month" subtitle
- **Line Chart** — Country daily new cases:
  - X: `DimDate[Date]`
  - Values: `SUM(FactCovid[NewCases])`, `[7D Rolling Avg New Cases]`
- **Dual-axis Line Chart** — CFR vs Recovery Rate over time:
  - Primary Y: `AVERAGE(FactCovid[CFR])`
  - Secondary Y: `AVERAGE(FactCovid[RecoveryRate])`
- **Table** — Monthly breakdown:
  - Columns: Month, New Cases, New Deaths, CFR, Recovery Rate, Risk Tier
  - Conditional formatting on CFR and Risk Tier
- **Gauge Chart** — Vaccination completion:
  - Value: `[Avg Fully Vaccinated %]`
  - Max: 100

---

### Page 4: Regional Comparison
**Visuals:**
- **Matrix / Heatmap** — Countries vs Months (New Cases):
  - Rows: `DimCountry[Country]`
  - Columns: `DimDate[YearMonth]`
  - Values: `SUM(FactCovid[NewCases])`
  - Conditional formatting: Red gradient
- **Bar Chart** — Continent comparison by CFR:
  - Axis: `DimCountry[Continent]`
  - Values: `[Case Fatality Rate %]`
- **Scatter Chart** — Country risk positioning:
  - X: `[Case Fatality Rate %]`
  - Y: `SUM(FactCovid[CasesPer100k])`
  - Size: `SUM(FactCovid[Confirmed])`
  - Color: `DimCountry[Continent]`
- **Treemap** — Cases by Continent → Country:
  - Group: `DimCountry[Continent]`, `DimCountry[Country]`
  - Values: `[Total Confirmed Cases]`

---

### Page 5: Vaccination Impact
**Visuals:**
- **Scatter Plot** — Vaccination vs CFR:
  - X: `[Avg Fully Vaccinated %]`
  - Y: `[Case Fatality Rate %]`
  - Size: `[Total Confirmed Cases]`
  - Color: `DimCountry[Continent]`
  - Play axis: `DimDate[Year]` (animated)
- **Bar Chart** — Vax rate by Continent:
  - Axis: `DimCountry[Continent]`
  - Values: `[Avg Fully Vaccinated %]`
- **Line Chart** — Global vax rollout over time:
  - X: `DimDate[Date]`
  - Values: `AVERAGE(FactVaccination[VaxPctFull])`
- **Table** — Top 20 Vaccinated Countries vs CFR:
  - Country, Fully Vax %, CFR %, Cases Per 100k

---

### Page 6: Risk Dashboard
**Visuals:**
- **Shape Map** — Risk Tier choropleth:
  - Location: `DimCountry[Country]`
  - Color by: `CovidLatest[RiskTier]`
  - Color rules: Critical=Red, High=Orange, Medium=Yellow, Low=Green
- **Donut Chart** — Risk tier distribution:
  - Values: `COUNT(FactCovid[Country])`
  - Legend: `FactCovid[RiskTier]`
- **Table** — High/Critical risk countries:
  - Country, Continent, Active Cases, CFR, Growth Rate, Risk Tier
  - Sorted by Active Cases DESC
- **KPI Card** — Critical risk countries: `[Critical Risk Countries]`
- **KPI Card** — High risk countries: `[High Risk Countries]`
- **Gauge** — Global CFR vs target (2%):
  - Value: `[Case Fatality Rate %]`
  - Target: 2.0

---

## Step 6: Add Page Navigation

Add **buttons with bookmarks** for page navigation:
1. Insert → Shapes → Rectangle (styled as nav button)
2. Add text: "Overview | Trends | Country | Regions | Vaccination | Risk"
3. Action → Page Navigation → target page

---

## Step 7: Publish to Power BI Service

1. **Home → Publish** → Select your workspace
2. Sign in to **app.powerbi.com**
3. Open the report → **File → Embed in public websites**
4. Copy the **iframe embed code** or **public URL**
5. Add the URL to `README.md` in the `## Live Dashboard` section
