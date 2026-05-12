"""Data loading and caching for the dashboard."""
import pandas as pd
import numpy as np
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "processed")

def _path(f): return os.path.join(DATA_DIR, f)

def load_global():
    df = pd.read_csv(_path("covid_global.csv"), parse_dates=["Date"])
    df["NewCases"]  = df["NewCases"].clip(lower=0)
    df["NewDeaths"] = df["NewDeaths"].clip(lower=0)
    for c in ["VaxPctFull","VaxPct1Dose"]:
        if c not in df.columns:
            df[c] = 0
    df["VaxPctFull"] = df["VaxPctFull"].fillna(0)
    return df

def load_latest():
    df = pd.read_csv(_path("covid_latest.csv"), parse_dates=["Date"])
    # Pull best vaccination figures from global (max per country)
    gl = pd.read_csv(_path("covid_global.csv"), usecols=["Country","VaxPctFull","VaxPct1Dose",
                     "Recovered","RecoveryRate"] if "VaxPctFull" in open(_path("covid_global.csv")).readline() else ["Country"])
    if "VaxPctFull" in gl.columns:
        vax_max = gl.groupby("Country")[["VaxPctFull","VaxPct1Dose"]].max().reset_index()
        df = df.merge(vax_max, on="Country", how="left", suffixes=("_x",""))
        if "VaxPctFull_x" in df.columns: df.drop(columns=["VaxPctFull_x","VaxPct1Dose_x"], inplace=True, errors="ignore")
    for c in ["VaxPctFull","VaxPct1Dose","CasesPer100k","DeathsPer100k"]:
        if c not in df.columns: df[c] = 0
    return df.fillna(0)

def load_monthly():
    return pd.read_csv(_path("covid_monthly.csv"))

def load_dim_country():
    return pd.read_csv(_path("dim_country.csv"))

def get_global_kpis(df_latest):
    total_cases    = int(df_latest["Confirmed"].sum())
    total_deaths   = int(df_latest["Deaths"].sum())
    # JHU stopped tracking recovered; estimate as Cases - Deaths
    total_recovered= total_cases - total_deaths
    # Active cases effectively 0 for historical snapshot ending in 2023
    active         = 0
    cfr            = round(total_deaths / total_cases * 100, 2) if total_cases else 0
    recovery_rate  = round(total_recovered / total_cases * 100, 2) if total_cases else 0
    countries      = int(df_latest["Country"].nunique())
    avg_vax        = round(df_latest[df_latest["VaxPctFull"]>0]["VaxPctFull"].mean(), 1)
    return {
        "total_cases": total_cases,
        "total_deaths": total_deaths,
        "total_recovered": total_recovered,
        "active": active,
        "cfr": cfr,
        "recovery_rate": recovery_rate,
        "countries": countries,
        "avg_vax": avg_vax,
    }

def fmt(n):
    if n >= 1_000_000_000: return f"{n/1_000_000_000:.2f}B"
    if n >= 1_000_000:     return f"{n/1_000_000:.1f}M"
    if n >= 1_000:         return f"{n/1_000:.1f}K"
    return str(n)
