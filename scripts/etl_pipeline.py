"""
=============================================================================
Global Health Trend Analysis Dashboard - ETL Pipeline
=============================================================================
Author      : Vishv Shah
Purpose     : Fetch, clean, transform, and export COVID-19 analytics datasets
              ready for Power BI ingestion.
Data Sources:
  - Johns Hopkins CSSE (archived to March 2023):
      https://github.com/CSSEGISandData/COVID-19
  - Our World in Data (OWID) COVID-19 + Vaccinations:
      https://covid.ourworldindata.org/data/owid-covid-data.csv
Outputs:
  data/processed/covid_global.csv     — daily long-format fact table
  data/processed/covid_monthly.csv    — monthly aggregated metrics
  data/processed/covid_latest.csv     — latest snapshot per country
  data/processed/dim_country.csv      — country dimension table
  data/processed/dim_date.csv         — full date dimension table
  data/processed/vaccination_data.csv — vaccination fact table
=============================================================================
"""

import pandas as pd
import numpy as np
import requests
import os
import logging
from io import StringIO
from datetime import datetime, timedelta

# ─── Logging Setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("data/etl_log.txt"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# ─── Data Source URLs ───────────────────────────────────────────────────────────
JHU_BASE = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series"
JHU_CONFIRMED  = f"{JHU_BASE}/time_series_covid19_confirmed_global.csv"
JHU_DEATHS     = f"{JHU_BASE}/time_series_covid19_deaths_global.csv"
JHU_RECOVERED  = f"{JHU_BASE}/time_series_covid19_recovered_global.csv"
OWID_DATA_URL  = "https://covid.ourworldindata.org/data/owid-covid-data.csv"

# ─── Country name normalization map (JHU → ISO standard names) ─────────────────
COUNTRY_RENAME = {
    "US": "United States",
    "Korea, South": "South Korea",
    "Taiwan*": "Taiwan",
    "Czechia": "Czech Republic",
    "Congo (Kinshasa)": "Democratic Republic of Congo",
    "Congo (Brazzaville)": "Republic of Congo",
    "Cote d'Ivoire": "Ivory Coast",
    "Burma": "Myanmar",
    "West Bank and Gaza": "Palestine",
    "Holy See": "Vatican City",
    "North Macedonia": "North Macedonia",
    "Timor-Leste": "East Timor",
    "Eswatini": "Eswatini",
}

# ─── Continent mapping ─────────────────────────────────────────────────────────
CONTINENT_MAP = {
    "United States": "North America", "Canada": "North America", "Mexico": "North America",
    "Brazil": "South America", "Argentina": "South America", "Colombia": "South America",
    "Chile": "South America", "Peru": "South America", "Venezuela": "South America",
    "Ecuador": "South America", "Bolivia": "South America", "Paraguay": "South America",
    "Uruguay": "South America", "Guyana": "South America", "Suriname": "South America",
    "China": "Asia", "India": "Asia", "Japan": "Asia", "South Korea": "Asia",
    "Indonesia": "Asia", "Pakistan": "Asia", "Bangladesh": "Asia", "Philippines": "Asia",
    "Vietnam": "Asia", "Thailand": "Asia", "Malaysia": "Asia", "Singapore": "Asia",
    "Taiwan": "Asia", "Myanmar": "Asia", "Nepal": "Asia", "Sri Lanka": "Asia",
    "Afghanistan": "Asia", "Kazakhstan": "Asia", "Uzbekistan": "Asia",
    "Iran": "Asia", "Iraq": "Asia", "Saudi Arabia": "Asia", "Turkey": "Asia",
    "Israel": "Asia", "United Arab Emirates": "Asia", "Jordan": "Asia",
    "Lebanon": "Asia", "Qatar": "Asia", "Kuwait": "Asia", "Bahrain": "Asia",
    "Germany": "Europe", "France": "Europe", "United Kingdom": "Europe",
    "Italy": "Europe", "Spain": "Europe", "Russia": "Europe", "Poland": "Europe",
    "Netherlands": "Europe", "Belgium": "Europe", "Sweden": "Europe",
    "Switzerland": "Europe", "Austria": "Europe", "Portugal": "Europe",
    "Czech Republic": "Europe", "Romania": "Europe", "Hungary": "Europe",
    "Greece": "Europe", "Ukraine": "Europe", "Denmark": "Europe", "Norway": "Europe",
    "Finland": "Europe", "Slovakia": "Europe", "Croatia": "Europe", "Serbia": "Europe",
    "Nigeria": "Africa", "South Africa": "Africa", "Egypt": "Africa",
    "Ethiopia": "Africa", "Kenya": "Africa", "Morocco": "Africa", "Tunisia": "Africa",
    "Algeria": "Africa", "Ghana": "Africa", "Tanzania": "Africa", "Uganda": "Africa",
    "Australia": "Oceania", "New Zealand": "Oceania",
}

# ─── Population data (millions) for per-100k calculations ─────────────────────
POPULATION_MAP = {
    "United States": 331002651, "India": 1380004385, "Brazil": 212559417,
    "France": 65273511, "Germany": 83783942, "United Kingdom": 67886011,
    "Russia": 145934462, "South Korea": 51269185, "Turkey": 84339067,
    "Italy": 60461826, "Spain": 46754778, "Argentina": 45195777,
    "Colombia": 50882891, "Poland": 37846611, "Iran": 83992949,
    "Indonesia": 273523615, "Mexico": 128932753, "Ukraine": 43733762,
    "China": 1439323776, "Japan": 126476461, "Australia": 25499884,
    "Canada": 37742154, "South Africa": 59308690, "Pakistan": 220892340,
    "Philippines": 109581078, "Netherlands": 17134872, "Belgium": 11589623,
    "Portugal": 10196709, "Sweden": 10099265, "Czechia": 10708981,
    "Romania": 19237691, "Chile": 19116201, "Peru": 32971854,
    "Israel": 8655535, "Switzerland": 8654622, "Austria": 9006398,
    "Hungary": 9660351, "Malaysia": 32365999, "Thailand": 69799978,
    "Nigeria": 206139589, "Egypt": 102334404, "Bangladesh": 164689383,
    "Vietnam": 97338579, "Saudi Arabia": 34813871, "Morocco": 36910560,
}


def fetch_csv(url: str, label: str) -> pd.DataFrame:
    """Download CSV from URL with error handling."""
    log.info(f"Fetching {label} from {url}")
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        df = pd.read_csv(StringIO(response.text))
        log.info(f"  → {len(df)} rows, {len(df.columns)} columns")
        return df
    except Exception as e:
        log.error(f"  ✗ Failed to fetch {label}: {e}")
        raise


def unpivot_jhu(df: pd.DataFrame, value_col_name: str) -> pd.DataFrame:
    """
    Transform JHU wide format (date columns) to long format.
    JHU format: Province/State | Country/Region | Lat | Long | 1/22/20 | ... 
    """
    id_vars = ["Province/State", "Country/Region", "Lat", "Long"]
    # Identify date columns (everything that's not an id_var)
    date_cols = [c for c in df.columns if c not in id_vars]
    
    df_long = df.melt(
        id_vars=id_vars,
        value_vars=date_cols,
        var_name="Date",
        value_name=value_col_name
    )
    
    # Parse dates
    df_long["Date"] = pd.to_datetime(df_long["Date"], format="%m/%d/%y", errors="coerce")
    
    # Aggregate to country level (remove province/state breakdown)
    df_country = (
        df_long.groupby(["Country/Region", "Date"], as_index=False)[value_col_name]
        .sum()
    )
    return df_country


def normalize_country_names(df: pd.DataFrame, col: str = "Country/Region") -> pd.DataFrame:
    """Apply country name normalization."""
    df[col] = df[col].replace(COUNTRY_RENAME)
    return df


def compute_daily_new(df: pd.DataFrame, cumulative_col: str, new_col: str) -> pd.DataFrame:
    """Compute daily new values from cumulative series."""
    df = df.sort_values(["Country", "Date"])
    df[new_col] = df.groupby("Country")[cumulative_col].diff().fillna(0).clip(lower=0)
    return df


def compute_rolling_avg(df: pd.DataFrame, col: str, window: int = 7) -> pd.DataFrame:
    """Compute N-day rolling average per country."""
    new_col = f"{col}_rolling{window}d"
    df[new_col] = (
        df.groupby("Country")[col]
        .transform(lambda x: x.rolling(window, min_periods=1).mean())
    )
    return df


def classify_risk(row: pd.Series) -> str:
    """Classify country-date risk tier based on daily growth rate."""
    gr = row.get("daily_growth_rate", 0)
    if pd.isna(gr) or gr < 0.5:
        return "Low"
    elif gr < 2.0:
        return "Medium"
    elif gr < 5.0:
        return "High"
    else:
        return "Critical"


def build_dim_date(start: str, end: str) -> pd.DataFrame:
    """Generate a complete date dimension table."""
    dates = pd.date_range(start=start, end=end, freq="D")
    dim = pd.DataFrame({"Date": dates})
    dim["Year"] = dim["Date"].dt.year
    dim["Quarter"] = dim["Date"].dt.quarter
    dim["Month"] = dim["Date"].dt.month
    dim["MonthName"] = dim["Date"].dt.strftime("%B")
    dim["Week"] = dim["Date"].dt.isocalendar().week.astype(int)
    dim["DayOfWeek"] = dim["Date"].dt.dayofweek + 1
    dim["DayName"] = dim["Date"].dt.strftime("%A")
    dim["IsWeekend"] = dim["DayOfWeek"].isin([6, 7]).astype(int)
    dim["YearMonth"] = dim["Date"].dt.strftime("%Y-%m")
    dim["YearQuarter"] = dim["Year"].astype(str) + "-Q" + dim["Quarter"].astype(str)
    dim["DateKey"] = dim["Date"].dt.strftime("%Y%m%d").astype(int)
    return dim


def build_dim_country(countries: list) -> pd.DataFrame:
    """Build country dimension with continent, population."""
    rows = []
    for c in sorted(countries):
        rows.append({
            "Country": c,
            "Continent": CONTINENT_MAP.get(c, "Other"),
            "Population": POPULATION_MAP.get(c, np.nan),
        })
    return pd.DataFrame(rows)


def run_etl():
    """Main ETL orchestration."""
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)

    log.info("=" * 60)
    log.info("GLOBAL HEALTH TREND ANALYSIS — ETL PIPELINE START")
    log.info("=" * 60)

    # ── 1. Fetch JHU raw data ─────────────────────────────────────
    log.info("\n[STEP 1] Fetching JHU Time-Series Data...")
    df_confirmed = fetch_csv(JHU_CONFIRMED, "JHU Confirmed")
    df_deaths    = fetch_csv(JHU_DEATHS,    "JHU Deaths")
    df_recovered = fetch_csv(JHU_RECOVERED, "JHU Recovered")

    # Save raw copies
    df_confirmed.to_csv("data/raw/jhu_confirmed_raw.csv", index=False)
    df_deaths.to_csv("data/raw/jhu_deaths_raw.csv", index=False)
    df_recovered.to_csv("data/raw/jhu_recovered_raw.csv", index=False)

    # ── 2. Unpivot & merge JHU ───────────────────────────────────
    log.info("\n[STEP 2] Transforming JHU data (wide → long)...")
    df_c = unpivot_jhu(df_confirmed, "Confirmed")
    df_d = unpivot_jhu(df_deaths,    "Deaths")
    df_r = unpivot_jhu(df_recovered, "Recovered")

    # Normalize country names
    for df in [df_c, df_d, df_r]:
        df.rename(columns={"Country/Region": "Country"}, inplace=True)
    df_c = normalize_country_names(df_c, "Country")
    df_d = normalize_country_names(df_d, "Country")
    df_r = normalize_country_names(df_r, "Country")

    # Merge on Country + Date
    df_merged = df_c.merge(df_d, on=["Country", "Date"], how="outer")
    df_merged = df_merged.merge(df_r, on=["Country", "Date"], how="outer")
    df_merged.fillna(0, inplace=True)

    log.info(f"  → Merged shape: {df_merged.shape}")

    # ── 3. Feature Engineering ────────────────────────────────────
    log.info("\n[STEP 3] Feature Engineering...")
    df_merged.sort_values(["Country", "Date"], inplace=True)

    # Daily new cases/deaths/recoveries
    df_merged = compute_daily_new(df_merged, "Confirmed", "NewCases")
    df_merged = compute_daily_new(df_merged, "Deaths", "NewDeaths")
    df_merged = compute_daily_new(df_merged, "Recovered", "NewRecovered")

    # 7-day rolling averages
    df_merged = compute_rolling_avg(df_merged, "NewCases",     7)
    df_merged = compute_rolling_avg(df_merged, "NewDeaths",    7)
    df_merged = compute_rolling_avg(df_merged, "NewRecovered", 7)

    # Active cases
    df_merged["ActiveCases"] = (
        df_merged["Confirmed"] - df_merged["Deaths"] - df_merged["Recovered"]
    ).clip(lower=0)

    # Case Fatality Rate (CFR)
    df_merged["CFR"] = np.where(
        df_merged["Confirmed"] > 0,
        (df_merged["Deaths"] / df_merged["Confirmed"] * 100).round(4),
        0
    )

    # Recovery Rate
    df_merged["RecoveryRate"] = np.where(
        df_merged["Confirmed"] > 0,
        (df_merged["Recovered"] / df_merged["Confirmed"] * 100).round(4),
        0
    )

    # Daily growth rate (%)
    df_merged["prev_confirmed"] = df_merged.groupby("Country")["Confirmed"].shift(1)
    df_merged["daily_growth_rate"] = np.where(
        df_merged["prev_confirmed"] > 0,
        ((df_merged["Confirmed"] - df_merged["prev_confirmed"]) / df_merged["prev_confirmed"] * 100).round(4),
        0
    )
    df_merged.drop(columns=["prev_confirmed"], inplace=True)

    # Population-normalized metrics (per 100k)
    df_merged["Population"] = df_merged["Country"].map(POPULATION_MAP)
    df_merged["CasesPer100k"] = np.where(
        df_merged["Population"] > 0,
        (df_merged["Confirmed"] / df_merged["Population"] * 100_000).round(2),
        np.nan
    )
    df_merged["DeathsPer100k"] = np.where(
        df_merged["Population"] > 0,
        (df_merged["Deaths"] / df_merged["Population"] * 100_000).round(2),
        np.nan
    )

    # Risk tier
    df_merged["RiskTier"] = df_merged.apply(classify_risk, axis=1)

    # Continent
    df_merged["Continent"] = df_merged["Country"].map(CONTINENT_MAP).fillna("Other")

    # Date parts
    df_merged["Year"]      = df_merged["Date"].dt.year
    df_merged["Month"]     = df_merged["Date"].dt.month
    df_merged["MonthName"] = df_merged["Date"].dt.strftime("%B")
    df_merged["Quarter"]   = df_merged["Date"].dt.quarter
    df_merged["YearMonth"] = df_merged["Date"].dt.strftime("%Y-%m")
    df_merged["DateKey"]   = df_merged["Date"].dt.strftime("%Y%m%d").astype(int)

    log.info(f"  → Feature-engineered shape: {df_merged.shape}")

    # ── 4. OWID Vaccination Data ──────────────────────────────────
    log.info("\n[STEP 4] Fetching Our World in Data (OWID) vaccination data...")
    try:
        df_owid = fetch_csv(OWID_DATA_URL, "OWID COVID Data")
        df_owid.to_csv("data/raw/owid_covid_raw.csv", index=False)

        vax_cols = [
            "location", "date",
            "total_vaccinations", "people_vaccinated",
            "people_fully_vaccinated", "total_boosters",
            "people_vaccinated_per_hundred",
            "people_fully_vaccinated_per_hundred",
            "new_vaccinations", "new_vaccinations_smoothed",
        ]
        existing_vax_cols = [c for c in vax_cols if c in df_owid.columns]
        df_vax = df_owid[existing_vax_cols].copy()
        df_vax.rename(columns={
            "location": "Country",
            "date": "Date",
            "people_vaccinated_per_hundred": "VaxPct1Dose",
            "people_fully_vaccinated_per_hundred": "VaxPctFull",
        }, inplace=True)
        df_vax = normalize_country_names(df_vax, "Country")
        df_vax["Date"] = pd.to_datetime(df_vax["Date"], errors="coerce")

        # Filter to only countries (not continents / aggregates)
        exclude = ["World", "High income", "Low income", "Lower middle income",
                   "Upper middle income", "Asia", "Europe", "North America",
                   "South America", "Africa", "Oceania", "European Union"]
        df_vax = df_vax[~df_vax["Country"].isin(exclude)]
        df_vax.fillna(0, inplace=True)

        df_vax.to_csv("data/processed/vaccination_data.csv", index=False)
        log.info(f"  → Vaccination data: {df_vax.shape}")
    except Exception as e:
        log.warning(f"  OWID fetch failed ({e}); vaccination table will be empty.")
        df_vax = pd.DataFrame()

    # ── 5. Merge Vaccination into Global Fact Table ───────────────
    log.info("\n[STEP 5] Merging vaccination data into global fact...")
    if not df_vax.empty:
        vax_merge_cols = ["Country", "Date", "VaxPct1Dose", "VaxPctFull",
                          "total_vaccinations", "people_vaccinated", "people_fully_vaccinated"]
        vax_merge_cols = [c for c in vax_merge_cols if c in df_vax.columns]
        df_merged = df_merged.merge(df_vax[vax_merge_cols], on=["Country", "Date"], how="left")
        df_merged["VaxPct1Dose"] = df_merged["VaxPct1Dose"].fillna(0)
        df_merged["VaxPctFull"]  = df_merged["VaxPctFull"].fillna(0)

    # ── 6. Validation ─────────────────────────────────────────────
    log.info("\n[STEP 6] Data Validation...")
    assert df_merged["Country"].notna().all(), "Null countries found!"
    assert df_merged["Date"].notna().all(),    "Null dates found!"
    assert df_merged["Confirmed"].ge(0).all(), "Negative confirmed cases!"
    log.info("  ✓ All validations passed")
    log.info(f"  → Date range: {df_merged['Date'].min()} to {df_merged['Date'].max()}")
    log.info(f"  → Countries: {df_merged['Country'].nunique()}")
    log.info(f"  → Total rows: {len(df_merged)}")

    # ── 7. Export Processed Tables ────────────────────────────────
    log.info("\n[STEP 7] Exporting processed tables...")

    # 7a. Full global daily fact table
    df_merged.to_csv("data/processed/covid_global.csv", index=False)
    log.info(f"  ✓ covid_global.csv — {len(df_merged)} rows")

    # 7b. Monthly aggregations
    monthly_agg = {
        "Confirmed":     "max",
        "Deaths":        "max",
        "Recovered":     "max",
        "NewCases":      "sum",
        "NewDeaths":     "sum",
        "NewRecovered":  "sum",
        "CFR":           "last",
        "RecoveryRate":  "last",
        "ActiveCases":   "last",
    }
    monthly_agg_filtered = {k: v for k, v in monthly_agg.items() if k in df_merged.columns}
    df_monthly = (
        df_merged.groupby(["Country", "Continent", "Year", "Month", "MonthName", "YearMonth"])
        .agg(monthly_agg_filtered)
        .reset_index()
    )
    df_monthly.to_csv("data/processed/covid_monthly.csv", index=False)
    log.info(f"  ✓ covid_monthly.csv — {len(df_monthly)} rows")

    # 7c. Latest snapshot per country
    df_latest = df_merged.loc[df_merged.groupby("Country")["Date"].idxmax()].copy()
    df_latest.to_csv("data/processed/covid_latest.csv", index=False)
    log.info(f"  ✓ covid_latest.csv — {len(df_latest)} rows")

    # 7d. Dimension tables
    all_countries = df_merged["Country"].unique().tolist()
    dim_country = build_dim_country(all_countries)
    dim_country.to_csv("data/processed/dim_country.csv", index=False)
    log.info(f"  ✓ dim_country.csv — {len(dim_country)} rows")

    dim_date = build_dim_date(
        str(df_merged["Date"].min().date()),
        str(df_merged["Date"].max().date())
    )
    dim_date.to_csv("data/processed/dim_date.csv", index=False)
    log.info(f"  ✓ dim_date.csv — {len(dim_date)} rows")

    log.info("\n" + "=" * 60)
    log.info("ETL PIPELINE COMPLETE")
    log.info("=" * 60)
    return df_merged


if __name__ == "__main__":
    run_etl()
