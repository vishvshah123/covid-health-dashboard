-- =============================================================================
-- Global Health Trend Analysis Dashboard — SQL Analytics Layer
-- =============================================================================
-- Engine   : SQLite / DuckDB / pandas-compatible SQL (via pandasql)
-- Tables   : covid_global, covid_monthly, covid_latest, dim_country, dim_date
-- =============================================================================


-- ─────────────────────────────────────────────────────────────────────────────
-- Section 1: KPI Aggregates (used by Power BI KPI Cards)
-- ─────────────────────────────────────────────────────────────────────────────

-- 1.1 Global Totals (Latest Snapshot)
SELECT
    SUM(Confirmed)   AS GlobalConfirmed,
    SUM(Deaths)      AS GlobalDeaths,
    SUM(Recovered)   AS GlobalRecovered,
    SUM(ActiveCases) AS GlobalActive,
    ROUND(AVG(CFR), 2) AS GlobalCFR_Pct,
    ROUND(AVG(RecoveryRate), 2) AS GlobalRecoveryRate_Pct
FROM covid_latest;


-- 1.2 Global New Cases This Month vs Last Month (MoM)
SELECT
    cm1.YearMonth,
    SUM(cm1.NewCases)  AS CurrentMonthCases,
    SUM(cm0.NewCases)  AS PrevMonthCases,
    ROUND(
        (SUM(cm1.NewCases) - SUM(cm0.NewCases)) * 100.0
        / NULLIF(SUM(cm0.NewCases), 0), 2
    ) AS MoM_GrowthPct
FROM covid_monthly cm1
LEFT JOIN covid_monthly cm0
  ON cm1.Country = cm0.Country
 AND cm1.Year   = cm0.Year
 AND cm1.Month  = cm0.Month + 1
GROUP BY cm1.YearMonth
ORDER BY cm1.YearMonth DESC
LIMIT 3;


-- ─────────────────────────────────────────────────────────────────────────────
-- Section 2: Top Affected Countries
-- ─────────────────────────────────────────────────────────────────────────────

-- 2.1 Top 10 Countries by Total Confirmed Cases
SELECT
    cl.Country,
    dc.Continent,
    cl.Confirmed,
    cl.Deaths,
    cl.Recovered,
    cl.ActiveCases,
    cl.CFR,
    cl.RecoveryRate,
    cl.CasesPer100k,
    cl.DeathsPer100k
FROM covid_latest cl
LEFT JOIN dim_country dc ON cl.Country = dc.Country
ORDER BY cl.Confirmed DESC
LIMIT 10;


-- 2.2 Top 10 Countries by Deaths
SELECT
    Country,
    Deaths,
    Confirmed,
    ROUND(Deaths * 100.0 / NULLIF(Confirmed, 0), 2) AS CFR_Pct
FROM covid_latest
ORDER BY Deaths DESC
LIMIT 10;


-- 2.3 Top 10 Countries by Cases per 100,000 Population
SELECT
    Country,
    Confirmed,
    Deaths,
    CasesPer100k,
    DeathsPer100k,
    CFR
FROM covid_latest
WHERE CasesPer100k IS NOT NULL
ORDER BY CasesPer100k DESC
LIMIT 10;


-- ─────────────────────────────────────────────────────────────────────────────
-- Section 3: Trend Analysis
-- ─────────────────────────────────────────────────────────────────────────────

-- 3.1 Global Daily New Cases (7-day rolling average)
SELECT
    Date,
    SUM(NewCases)                     AS DailyGlobalNewCases,
    SUM(NewDeaths)                    AS DailyGlobalNewDeaths,
    AVG(NewCases_rolling7d)           AS Avg7d_NewCases,
    AVG(NewDeaths_rolling7d)          AS Avg7d_NewDeaths
FROM covid_global
GROUP BY Date
ORDER BY Date;


-- 3.2 Monthly Global Summary
SELECT
    YearMonth,
    Year,
    Month,
    SUM(NewCases)    AS MonthlyNewCases,
    SUM(NewDeaths)   AS MonthlyNewDeaths,
    AVG(CFR)         AS AvgCFR,
    AVG(RecoveryRate) AS AvgRecoveryRate
FROM covid_monthly
GROUP BY YearMonth, Year, Month
ORDER BY Year, Month;


-- 3.3 Peak Day Analysis — Country with Highest Single-Day Cases
SELECT
    Country,
    Date,
    NewCases AS PeakDailyNewCases,
    Confirmed,
    Deaths
FROM covid_global
WHERE (Country, NewCases) IN (
    SELECT Country, MAX(NewCases)
    FROM covid_global
    GROUP BY Country
)
ORDER BY PeakDailyNewCases DESC
LIMIT 20;


-- ─────────────────────────────────────────────────────────────────────────────
-- Section 4: Continent-Level Analysis
-- ─────────────────────────────────────────────────────────────────────────────

-- 4.1 Continent Summary — Latest Snapshot
SELECT
    dc.Continent,
    COUNT(DISTINCT cl.Country)   AS CountryCount,
    SUM(cl.Confirmed)            AS TotalConfirmed,
    SUM(cl.Deaths)               AS TotalDeaths,
    SUM(cl.Recovered)            AS TotalRecovered,
    SUM(cl.ActiveCases)          AS TotalActive,
    ROUND(AVG(cl.CFR), 2)       AS AvgCFR,
    ROUND(AVG(cl.RecoveryRate), 2) AS AvgRecoveryRate,
    ROUND(AVG(cl.CasesPer100k), 2) AS AvgCasesPer100k
FROM covid_latest cl
LEFT JOIN dim_country dc ON cl.Country = dc.Country
GROUP BY dc.Continent
ORDER BY TotalConfirmed DESC;


-- 4.2 Monthly New Cases by Continent
SELECT
    cm.YearMonth,
    cm.Year,
    cm.Month,
    dc.Continent,
    SUM(cm.NewCases)  AS MonthlyNewCases,
    SUM(cm.NewDeaths) AS MonthlyNewDeaths
FROM covid_monthly cm
LEFT JOIN dim_country dc ON cm.Country = dc.Country
WHERE dc.Continent IS NOT NULL
GROUP BY cm.YearMonth, cm.Year, cm.Month, dc.Continent
ORDER BY cm.YearMonth, dc.Continent;


-- ─────────────────────────────────────────────────────────────────────────────
-- Section 5: Vaccination Correlation Analysis
-- ─────────────────────────────────────────────────────────────────────────────

-- 5.1 Vaccination vs. CFR — Country Scatter Data
SELECT
    cg.Country,
    dc.Continent,
    MAX(cg.VaxPctFull)   AS FullyVaxPct,
    MAX(cg.VaxPct1Dose)  AS AtLeast1DoseVaxPct,
    AVG(cg.CFR)          AS AvgCFR,
    MAX(cg.Confirmed)    AS TotalCases,
    MAX(cg.Deaths)       AS TotalDeaths,
    MAX(cg.CasesPer100k) AS CasesPer100k
FROM covid_global cg
LEFT JOIN dim_country dc ON cg.Country = dc.Country
WHERE cg.VaxPctFull > 0
GROUP BY cg.Country, dc.Continent
ORDER BY FullyVaxPct DESC;


-- 5.2 High Vaccination vs Low Vaccination — Average CFR Comparison
SELECT
    CASE
        WHEN VaxPctFull >= 60 THEN 'High Vaccination (≥60%)'
        WHEN VaxPctFull >= 30 THEN 'Medium Vaccination (30–60%)'
        ELSE 'Low Vaccination (<30%)'
    END AS VaxCategory,
    COUNT(DISTINCT Country)       AS Countries,
    ROUND(AVG(CFR), 4)           AS AvgCFR,
    ROUND(AVG(CasesPer100k), 2)  AS AvgCasesPer100k,
    ROUND(AVG(DeathsPer100k), 2) AS AvgDeathsPer100k
FROM covid_latest
WHERE VaxPctFull IS NOT NULL
GROUP BY VaxCategory
ORDER BY AvgCFR DESC;


-- ─────────────────────────────────────────────────────────────────────────────
-- Section 6: Risk Classification
-- ─────────────────────────────────────────────────────────────────────────────

-- 6.1 Current Risk Tier Distribution
SELECT
    RiskTier,
    COUNT(DISTINCT Country) AS CountryCount,
    SUM(Confirmed)          AS TotalConfirmed,
    SUM(ActiveCases)        AS TotalActive
FROM covid_latest
GROUP BY RiskTier
ORDER BY
    CASE RiskTier
        WHEN 'Critical' THEN 1
        WHEN 'High'     THEN 2
        WHEN 'Medium'   THEN 3
        WHEN 'Low'      THEN 4
    END;


-- 6.2 Countries in High / Critical Risk (Ranked by Active Cases)
SELECT
    Country,
    Continent,
    ActiveCases,
    CFR,
    daily_growth_rate,
    RiskTier,
    CasesPer100k
FROM covid_latest
WHERE RiskTier IN ('High', 'Critical')
ORDER BY ActiveCases DESC
LIMIT 30;


-- ─────────────────────────────────────────────────────────────────────────────
-- Section 7: Recovery Analysis
-- ─────────────────────────────────────────────────────────────────────────────

-- 7.1 Fastest Recovering Countries (Highest Recovery Rate, Minimum 10k Cases)
SELECT
    Country,
    Continent,
    Confirmed,
    Recovered,
    Deaths,
    RecoveryRate,
    CFR
FROM covid_latest
WHERE Confirmed >= 10000
ORDER BY RecoveryRate DESC
LIMIT 20;


-- 7.2 Countries with Highest Mortality (Sorted by CFR, Minimum 10k Cases)
SELECT
    Country,
    Continent,
    Confirmed,
    Deaths,
    CFR,
    DeathsPer100k
FROM covid_latest
WHERE Confirmed >= 10000
ORDER BY CFR DESC
LIMIT 20;


-- ─────────────────────────────────────────────────────────────────────────────
-- Section 8: Time-Series Forecasting Prep
-- ─────────────────────────────────────────────────────────────────────────────

-- 8.1 Last 90 Days Global Daily Cases (for forecasting baseline)
SELECT
    Date,
    SUM(NewCases)  AS GlobalNewCases,
    SUM(NewDeaths) AS GlobalNewDeaths,
    AVG(CFR)       AS GlobalCFR
FROM covid_global
WHERE Date >= DATE('now', '-90 days')
GROUP BY Date
ORDER BY Date;


-- 8.2 Monthly Growth Rate by Country (for trend pattern)
SELECT
    Country,
    YearMonth,
    NewCases,
    NewDeaths,
    ROUND(
        (NewCases - LAG(NewCases, 1) OVER (PARTITION BY Country ORDER BY YearMonth))
        * 100.0
        / NULLIF(LAG(NewCases, 1) OVER (PARTITION BY Country ORDER BY YearMonth), 0),
    2) AS MoM_CasesGrowthPct
FROM covid_monthly
ORDER BY Country, YearMonth;
