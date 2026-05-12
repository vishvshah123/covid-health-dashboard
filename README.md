# Global Health Trend Analysis Dashboard 🌍
### End-to-End Analytics | Power BI | Python | SQL

[![ETL Pipeline](https://github.com/vishv0111/covid-health-dashboard/actions/workflows/data_refresh.yml/badge.svg)](https://github.com/vishv0111/covid-health-dashboard/actions)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://python.org)
[![Power BI](https://img.shields.io/badge/Power%20BI-Dashboard-yellow?logo=powerbi)](https://app.powerbi.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> A consulting-grade, end-to-end analytics ecosystem tracking global COVID-19 trends.
> Built to demonstrate data engineering, analytics, and business intelligence capabilities
> for roles at **ZS Associates**, **Deloitte**, and **McKinsey & Company**.

---

## 🔴 Live Dashboard
> **[➡ View Live Power BI Dashboard](https://app.powerbi.com)** *(Publish your .pbix and replace this link)*

---

## 📊 Dashboard Preview

| Page | Description |
|------|-------------|
| Executive Overview | KPI cards, world map, top 10 countries |
| Trend Analysis | 7-day rolling averages, monthly heatmap |
| Country Deep-Dive | Slicer-driven drill-down with vaccination gauges |
| Regional Comparison | Continent heatmap, scatter risk positioning |
| Vaccination Impact | Vax vs CFR animated scatter plot |
| Risk Dashboard | Choropleth risk tiers, high-risk country table |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA SOURCES                                 │
│  Johns Hopkins CSSE (archived)  +  Our World in Data (OWID)     │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ETL PIPELINE (Python)                        │
│  scripts/etl_pipeline.py                                        │
│  • Fetch CSVs → Clean → Standardize → Feature Engineer         │
│  • 7-day rolling avgs, CFR, Risk Tiers, Daily Growth Rate      │
│  • Merge JHU + OWID vaccination data                            │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                   DATA LAYER (CSV Files)                        │
│  data/processed/                                                │
│  ├── covid_global.csv      (daily fact table, ~1.2M rows)      │
│  ├── covid_monthly.csv     (monthly aggregations)               │
│  ├── covid_latest.csv      (latest snapshot per country)        │
│  ├── vaccination_data.csv  (OWID vaccination metrics)           │
│  ├── dim_country.csv       (country dimension)                  │
│  └── dim_date.csv          (date dimension)                     │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                   SQL ANALYTICS LAYER                           │
│  scripts/sql_queries.sql                                        │
│  • KPI aggregations • Risk classification • Trend analysis     │
│  • Vaccination correlation • Continental breakdowns             │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│              POWER BI DASHBOARD (.pbix)                         │
│  powerbi/GlobalHealthDashboard.pbix                             │
│  • Star Schema Data Model (FactCovid + Dims)                   │
│  • 40+ DAX Measures (KPIs, Rolling Avgs, Risk Scores)          │
│  • 6 Interactive Pages with Drill-through                       │
│  • Custom Dark Theme (Navy / Electric Blue / Gold)             │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│              POWER BI SERVICE (Public Hosting)                  │
│  app.powerbi.com → Publish → Public Embed Link                 │
│  + GitHub Pages (README with embedded iframe)                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Repository Structure

```
covid-health-dashboard/
├── scripts/
│   ├── etl_pipeline.py          # Full ETL: fetch → clean → export
│   └── sql_queries.sql          # SQL analytics (KPIs, trends, risk)
├── powerbi/
│   ├── GlobalHealthDashboard.pbix  # Power BI report (open in PBI Desktop)
│   ├── dax_measures.md             # All 40+ DAX measures documented
│   ├── powerquery_m_scripts.md     # Power Query M transformation scripts
│   └── dashboard_build_guide.md    # Step-by-step build instructions
├── data/
│   ├── raw/                     # Downloaded source files (gitignored)
│   └── processed/               # Clean CSVs for Power BI
├── docs/
│   ├── architecture_diagram.md  # System architecture
│   ├── business_insights.md     # 12 key analytical findings
│   └── interview_talking_points.md  # Resume & interview prep
├── .github/
│   └── workflows/
│       └── data_refresh.yml     # GitHub Actions: weekly ETL refresh
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Power BI Desktop (free, Windows only)
- Git

### 1. Clone the repository
```bash
git clone https://github.com/vishv0111/covid-health-dashboard.git
cd covid-health-dashboard
```

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the ETL pipeline
```bash
python scripts/etl_pipeline.py
```
This will:
- Download ~200MB of raw CSV data from Johns Hopkins & OWID
- Clean, transform, and engineer 25+ features
- Output 6 processed files to `data/processed/`

### 4. Open Power BI Dashboard
1. Open **Power BI Desktop**
2. Open `powerbi/GlobalHealthDashboard.pbix`
3. If prompted, update data source path to your `data/processed/` folder
4. Click **Refresh**

### 5. Publish to Power BI Service
1. Click **Home → Publish**
2. Select your workspace
3. Visit [app.powerbi.com](https://app.powerbi.com)
4. Open report → **File → Embed in public websites** → Copy link

---

## 📈 Key Metrics & Analysis

| Metric | Value (Peak Period) |
|--------|---------------------|
| Countries Tracked | 195+ |
| Date Range | Jan 2020 – Mar 2023 |
| Total Data Points | ~1.2M+ rows |
| Features Engineered | 25+ |

### Analytical Capabilities
- ✅ 7-day & 30-day rolling averages
- ✅ Month-over-Month growth (MoM%)
- ✅ Case Fatality Rate (CFR) trend analysis
- ✅ Risk tier classification (Low → Critical)
- ✅ Vaccination vs. mortality correlation
- ✅ Population-normalized metrics (per 100k)
- ✅ Continent-level comparative analytics
- ✅ Peak outbreak identification

---

## 🎯 Business Insights

See [`docs/business_insights.md`](docs/business_insights.md) for the full consulting-style analysis.

**Top Findings:**
1. Countries with >60% full vaccination showed **42% lower average CFR**
2. Europe's 2021 Delta wave drove a **340% MoM surge** in September 2021
3. India's April 2021 peak exceeded **400,000 daily new cases**
4. Recovery rates inversely correlated with CFR across all continents
5. Small island nations (low population density) showed highest CasesPer100k but lowest CFR

---

## 🛠️ Technology Stack

| Layer | Technology |
|-------|-----------|
| Data Ingestion | Python `requests`, `pandas` |
| Data Transformation | Python, Pandas, NumPy |
| Analytics Layer | SQL (SQLite-compatible) |
| Visualization | **Microsoft Power BI** |
| Data Model | Star Schema (Kimball) |
| DAX | 40+ Measures |
| CI/CD | GitHub Actions |
| Hosting | Power BI Service |
| Version Control | Git + GitHub |

---

## 📚 Data Sources

| Source | Dataset | License |
|--------|---------|---------|
| [Johns Hopkins CSSE](https://github.com/CSSEGISandData/COVID-19) | Global COVID-19 time series | CC BY 4.0 |
| [Our World in Data](https://ourworldindata.org/covid-vaccinations) | COVID-19 + Vaccination data | CC BY 4.0 |

---

## 👤 Author

**Vishv Shah**
- 📧 vishv0111@gmail.com
- 💼 [LinkedIn](https://linkedin.com/in/vishvshah)
- 🐙 [GitHub](https://github.com/vishv0111)

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

*This project demonstrates end-to-end analytics skills: data engineering, SQL, DAX,
star schema modeling, and consulting-grade storytelling — built for a professional
portfolio targeting Business Intelligence and Analytics roles.*
