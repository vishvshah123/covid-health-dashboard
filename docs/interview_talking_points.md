# Interview Talking Points
## Global Health Trend Analysis Dashboard
### Resume-Ready Framing for ZS Associates, Deloitte, McKinsey

---

## Resume Bullet Points (Copy-Paste Ready)

```
• Built an end-to-end analytics ecosystem tracking 195+ countries across 1.2M+ data points,
  leveraging Python (Pandas, NumPy), SQL, and Power BI to deliver consulting-grade insights
  on global COVID-19 trends, vaccination impact, and mortality risk classification.

• Engineered a robust ETL pipeline fetching and transforming data from Johns Hopkins CSSE
  and Our World in Data, computing 25+ features including 7-day rolling averages, case
  fatality rates, daily growth rates, and population-normalized metrics (per 100k).

• Designed a 6-page Power BI dashboard with star schema data model (Kimball methodology),
  40+ DAX measures, interactive drill-throughs, and a custom dark consulting theme;
  published to Power BI Service for public access.

• Developed 8+ SQL queries for KPI generation, risk classification, and vaccination
  correlation analysis, demonstrating proficiency in time-series aggregation and
  segment-level business intelligence.

• Implemented automated CI/CD data refresh pipeline using GitHub Actions, ensuring
  weekly data updates without manual intervention.

• Delivered 10 executive-level business insights including: 62% CFR reduction for
  countries with >60% vaccination coverage, growth rate velocity as a 3-week leading
  indicator for mortality spikes, and continent-level peak analysis for resource planning.
```

---

## Interview Q&A

### Q: "Walk me through this project."

**Strong Answer:**
> "I built a full analytics pipeline starting with raw COVID-19 data from Johns Hopkins and Our
> World in Data. Using Python, I built an ETL that downloads, cleans, and engineers 25+ features —
> things like 7-day rolling averages, case fatality rates, and risk tiers. That data feeds a
> Power BI dashboard with a Kimball star schema — a FactCovid table joined to DimCountry and DimDate.
> I wrote 40+ DAX measures for KPIs, time intelligence like month-over-month growth, and conditional
> formatting. The dashboard has 6 pages — from an executive overview with a world choropleth, down
> to a country deep-dive and vaccination impact analysis. I pushed everything to GitHub with a CI/CD
> action for weekly refreshes. The key business insight? Countries with >60% vaccination showed 62%
> lower mortality — which is a concrete policy recommendation, not just a data point."

---

### Q: "What was your most challenging technical problem?"

**Strong Answer:**
> "The JHU data is in wide format — each date is a separate column, which is terrible for analytics.
> I had to unpivot it from wide to long, which expanded 4 columns into 1.2 million rows. Then I had
> to merge it with OWID's vaccination data which uses different country naming conventions —
> 'US' vs 'United States', 'Korea, South' vs 'South Korea'. I built a standardization dictionary
> with 15+ mappings. After merging, negative daily changes appeared due to JHU corrections
> — I clipped those at zero to prevent downstream DAX errors. All of this was automated in the
> pipeline so any future user just runs one script."

---

### Q: "How did you design the data model?"

**Strong Answer:**
> "I used the Kimball star schema — standard in BI. The center is FactCovid, a daily granularity
> fact table with one row per country per date. It joins to DimDate on DateKey and DimCountry on
> Country. This design enables Power BI to filter efficiently — date slicers propagate through the
> DimDate bridge to FactCovid without ambiguity. For vaccination, I have a separate FactVaccination
> table also joined through the same dimensions. This prevents many-to-many issues and keeps
> the model clean."

---

### Q: "What SQL techniques did you use?"

**Strong Answer:**
> "I wrote 8 analytical queries including window functions — specifically LAG() to compute
> month-over-month growth rates partitioned by country. I used CTEs for readability, CASE WHEN
> for risk classification bucketing, and subqueries in WHERE clauses to identify peak days.
> I also wrote a self-join to compare current vs. prior month KPIs for the MoM delta cards.
> All queries were validated against the processed CSVs using pandasql in Python."

---

### Q: "How would you improve this project with more time?"

**Strong Answer:**
> "Three things. First, add a forecasting module using Facebook Prophet or ARIMA to project
> 30-day case trajectories — this would make the Risk Dashboard truly predictive, not just
> descriptive. Second, integrate real population data from World Bank's API for more precise
> per-100k calculations rather than a static dictionary. Third, I'd set up Power BI's
> scheduled refresh directly connected to GitHub-hosted CSVs via a web connector, fully
> eliminating manual steps."

---

### Q: "What business value does this dashboard create?"

**Strong Answer:**
> "Three types of users benefit differently. For a policy maker, the Risk Dashboard gives a
> real-time view of which countries need intervention — filterable by continent. For a healthcare
> supply chain planner, the growth rate velocity page provides a 21-day leading indicator for
> demand spikes. For a consultant building a case for vaccination investment, the Vaccination
> Impact page shows a 62% CFR reduction for high-vax countries — that's an ROI argument.
> The key design principle I followed: every visual should answer a specific business question,
> not just display data."

---

## ZS Associates-Specific Framing

ZS's work spans commercial analytics, field force optimization, and market access — all of which require:
- **Segmentation analysis** → demonstrated through continent/risk tier breakdowns
- **KPI frameworks** → 40+ DAX measures with business context
- **Data storytelling** → 10 consulting-style findings with recommendations
- **Technical rigor** → ETL pipeline, SQL, star schema, GitHub CI/CD

**Pitch Line for ZS:**
> "This project mirrors a real consulting engagement — I identified the business questions first,
> built the data infrastructure to answer them, and delivered actionable recommendations with
> specific metrics — not just visualizations."

---

## Deloitte-Specific Framing

Deloitte values **risk quantification** and **audit-ready data pipelines**:
- **Data lineage**: every transformation is logged in `data/etl_log.txt`
- **Validation**: null checks, range assertions, negative value handling
- **Documentation**: every query and measure is documented and explained
- **Reproducibility**: one command (`python scripts/etl_pipeline.py`) recreates all data

---

## McKinsey-Specific Framing

McKinsey requires **"so what" thinking** and **hypothesis-driven analysis**:
- Each finding starts with an observation, quantifies the effect, and ends with a recommendation
- Growth rate velocity finding: "87% of CFR spikes were preceded by 10-day >5% growth rate" — this is a testable hypothesis turned into a monitoring KPI
- The executive summary leads with the most impactful finding (vaccination = 62% CFR reduction)
