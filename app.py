import dash
from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from data_loader import load_global, load_latest, load_monthly, load_dim_country, get_global_kpis, fmt

# ── Load Data ──────────────────────────────────────────────────────────────────
df_global  = load_global()
df_latest  = load_latest()
df_monthly = load_monthly()
df_country = load_dim_country()
kpis       = get_global_kpis(df_latest)
countries  = sorted(df_global["Country"].unique())
continents = sorted(df_latest["Continent"].dropna().unique())

PLOTLY_BASE = dict(
    paper_bgcolor="rgba(255,255,255,1)", plot_bgcolor="rgba(255,255,255,1)",
    font=dict(family="Segoe UI, Arial, sans-serif", color="#323130"),
    colorway=["#118DFF","#12239E","#E66C37","#41A9C9","#B32824","#D9B300","#00B4D8"],
    margin=dict(l=40, r=20, t=40, b=40),
    hoverlabel=dict(bgcolor="#FFFFFF", font_color="#323130", bordercolor="#C8C6C4"),
    legend=dict(bgcolor="rgba(255,255,255,0)", font=dict(size=11, color="#605E5C")),
)
AXIS_STYLE = dict(gridcolor="#E1DFDD", linecolor="#C8C6C4", showgrid=True, zeroline=False)

def apply_theme(fig, height=None, **extra):
    """Apply dark theme to any figure without key conflicts."""
    fig.update_layout(**PLOTLY_BASE)
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(**AXIS_STYLE)
    if height:
        fig.update_layout(height=height)
    if extra:
        fig.update_layout(**extra)
    return fig

# ── KPI Card helper ────────────────────────────────────────────────────────────
def kpi_card(icon, label, value, delta=None, delta_dir="neutral", color="#00B4D8"):
    delta_el = html.Span(delta, className=f"kpi-delta {delta_dir}") if delta else html.Span()
    return html.Div([
        html.Span(icon, className="kpi-icon"),
        html.Div(label, className="kpi-label"),
        html.Div(value, className="kpi-value", style={"color": color}),
        delta_el,
    ], className="kpi-card")

# ── Layout ─────────────────────────────────────────────────────────────────────
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
app.title = "Global Health Trend Analysis Dashboard"
server = app.server

app.layout = html.Div(id="app-shell", children=[

    # Header
    html.Div(id="header", children=[
        dbc.Row([
            dbc.Col([
                html.Div("🌍 Global Health Trend Analysis Dashboard", className="header-title"),
                html.Div("COVID-19 Analytics · Jan 2020 – Mar 2023 · 201 Countries", className="header-subtitle"),
            ], width="auto"),
            dbc.Col([
                html.Span([html.Span(className="live-dot"), "LIVE ANALYTICS"], className="header-badge"),
            ], className="d-flex align-items-center justify-content-end"),
        ], align="center"),
    ]),

    # KPI Row
    html.Div(style={"padding": "20px 24px 0"}, children=[
        dbc.Row([
            dbc.Col(kpi_card("🦠", "Total Cases",   fmt(kpis["total_cases"]),    color="#00B4D8"), xs=6, md=4, lg=2, className="mb-3"),
            dbc.Col(kpi_card("💀", "Total Deaths",  fmt(kpis["total_deaths"]),   color="#FF6B6B"), xs=6, md=4, lg=2, className="mb-3"),
            dbc.Col(kpi_card("💚", "Recovered",     fmt(kpis["total_recovered"]),color="#06D6A0"), xs=6, md=4, lg=2, className="mb-3"),
            dbc.Col(kpi_card("⚡", "Active Cases",  fmt(kpis["active"]),         color="#FFD60A"), xs=6, md=4, lg=2, className="mb-3"),
            dbc.Col(kpi_card("📊", "Fatality Rate", f"{kpis['cfr']}%",           color="#FF9A3C"), xs=6, md=4, lg=2, className="mb-3"),
            dbc.Col(kpi_card("💉", "Avg Vax Rate",  f"{kpis['avg_vax']}%",       color="#C77DFF"), xs=6, md=4, lg=2, className="mb-3"),
        ], className="g-3"),
    ]),

    # Tabs
    html.Div(style={"padding": "8px 24px 0"}, children=[
        dbc.Tabs(id="main-tabs", active_tab="tab-overview", className="custom-tabs", children=[
            dbc.Tab(label="🌍 Overview",     tab_id="tab-overview"),
            dbc.Tab(label="📈 Trends",       tab_id="tab-trends"),
            dbc.Tab(label="🔬 Country Dive", tab_id="tab-country"),
            dbc.Tab(label="🌐 Regions",      tab_id="tab-regions"),
            dbc.Tab(label="💉 Vaccination",  tab_id="tab-vax"),
            dbc.Tab(label="⚠️ Risk",         tab_id="tab-risk"),
        ]),
        html.Div(id="tab-content", style={"paddingTop": "16px"}),
    ]),

    # Footer
    html.Div(id="footer", children=[
        html.P("Global Health Trend Analysis Dashboard · Built by Vishv Shah · Data: Johns Hopkins CSSE + Our World in Data (CC BY 4.0)"),
    ]),
])


# ── Tab Router ─────────────────────────────────────────────────────────────────
@app.callback(Output("tab-content", "children"), Input("main-tabs", "active_tab"))
def render_tab(tab):
    if tab == "tab-overview":  return build_overview()
    if tab == "tab-trends":    return build_trends()
    if tab == "tab-country":   return build_country()
    if tab == "tab-regions":   return build_regions()
    if tab == "tab-vax":       return build_vax()
    if tab == "tab-risk":      return build_risk()
    return html.Div("Select a tab")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
def build_overview():
    # World map
    map_fig = px.choropleth(
        df_latest.sort_values("Confirmed", ascending=False),
        locations="Country", locationmode="country names",
        color="Confirmed", hover_name="Country",
        hover_data={"Deaths": True, "CFR": ":.2f", "Confirmed": ":,"},
        color_continuous_scale=[[0,"#0D1117"],[0.2,"#023E8A"],[0.5,"#0077B6"],[0.8,"#00B4D8"],[1,"#90E0EF"]],
        labels={"Confirmed": "Total Cases"},
        title="Global COVID-19 Confirmed Cases",
    )
    apply_theme(map_fig, height=420,
        coloraxis_colorbar=dict(title="Cases", tickfont=dict(color="#323130")),
        geo=dict(bgcolor="rgba(255,255,255,1)", lakecolor="#FFFFFF",
                 landcolor="#F3F2F1", showocean=True, oceancolor="#E1DFDD",
                 showframe=False, showcoastlines=True, coastlinecolor="#C8C6C4"))
    map_fig.update_traces(marker_line_color="#FFFFFF", marker_line_width=0.3)

    # Top 15 bar
    top15 = df_latest.nlargest(15, "Confirmed")[["Country","Confirmed","Deaths","CFR"]].copy()
    bar_fig = px.bar(top15, x="Confirmed", y="Country", orientation="h",
        color="CFR", color_continuous_scale=["#06D6A0","#FFD60A","#FF6B6B"],
        hover_data={"Deaths": ":,", "CFR": ":.2f%"},
        title="Top 15 Countries by Total Cases",
        labels={"Confirmed": "Confirmed Cases", "CFR": "CFR%"})
    apply_theme(bar_fig, height=420,
        yaxis=dict(autorange="reversed", gridcolor="#E1DFDD"),
        coloraxis_colorbar=dict(title="CFR%", tickfont=dict(color="#323130")))
    bar_fig.update_traces(marker_line_width=0)

    # Global daily trend (aggregated)
    daily = df_global.groupby("Date").agg(NewCases=("NewCases","sum"), NewDeaths=("NewDeaths","sum")).reset_index()
    daily["MA7"] = daily["NewCases"].rolling(7).mean()
    trend_fig = go.Figure()
    trend_fig.add_trace(go.Bar(x=daily["Date"], y=daily["NewCases"], name="Daily New Cases",
        marker_color="rgba(0,180,216,0.25)", hovertemplate="%{x|%b %d, %Y}<br>Cases: %{y:,}<extra></extra>"))
    trend_fig.add_trace(go.Scatter(x=daily["Date"], y=daily["MA7"], name="7-Day Average",
        line=dict(color="#00B4D8", width=2.5), hovertemplate="%{x|%b %d, %Y}<br>7D Avg: %{y:,.0f}<extra></extra>"))
    apply_theme(trend_fig, height=300, title="Global Daily New Cases",
        barmode="overlay", legend=dict(orientation="h", yanchor="bottom", y=1.02))

    return html.Div(className="fade-in", children=[
        html.Div(className="chart-card", children=[dcc.Graph(figure=map_fig, config={"displayModeBar": False})]),
        dbc.Row([
            dbc.Col(html.Div(className="chart-card", children=[dcc.Graph(figure=trend_fig, config={"displayModeBar": False})]), md=7),
            dbc.Col(html.Div(className="chart-card", children=[dcc.Graph(figure=bar_fig,   config={"displayModeBar": False})]), md=5),
        ], className="g-3"),
    ])


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — TRENDS
# ══════════════════════════════════════════════════════════════════════════════
def build_trends():
    daily = df_global.groupby("Date").agg(
        NewCases=("NewCases","sum"), NewDeaths=("NewDeaths","sum"),
        Confirmed=("Confirmed","sum"), Deaths=("Deaths","sum"),
    ).reset_index()
    daily["CasesMA7"]  = daily["NewCases"].rolling(7).mean()
    daily["DeathsMA7"] = daily["NewDeaths"].rolling(7).mean()
    daily["CFR"]       = (daily["Deaths"] / daily["Confirmed"] * 100).round(3)

    # Cases + Deaths dual axis
    fig1 = make_subplots(specs=[[{"secondary_y": True}]])
    fig1.add_trace(go.Scatter(x=daily["Date"], y=daily["CasesMA7"], name="New Cases (7D MA)",
        fill="tozeroy", fillcolor="rgba(0,180,216,0.12)", line=dict(color="#00B4D8", width=2)), secondary_y=False)
    fig1.add_trace(go.Scatter(x=daily["Date"], y=daily["DeathsMA7"], name="New Deaths (7D MA)",
        line=dict(color="#FF6B6B", width=2, dash="dot")), secondary_y=True)
    apply_theme(fig1, height=340, title="Global Case & Death Trajectory (7-Day MA)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02))
    fig1.update_yaxes(title_text="New Cases", gridcolor="#E1DFDD", secondary_y=False)
    fig1.update_yaxes(title_text="New Deaths", gridcolor="#E1DFDD", secondary_y=True, showgrid=False)

    # CFR over time
    fig2 = px.area(daily, x="Date", y="CFR", title="Global Case Fatality Rate Over Time (%)",
        color_discrete_sequence=["#FF9A3C"])
    fig2.update_traces(fillcolor="rgba(255,154,60,0.1)", line_width=2)
    apply_theme(fig2, height=280)

    # Continent monthly
    if "Continent" in df_global.columns:
        cont_m = df_global.groupby(["YearMonth","Continent"]).agg(NewCases=("NewCases","sum")).reset_index()
        cont_m = cont_m[cont_m["Continent"].notna() & (cont_m["Continent"] != "Other")]
        fig3 = px.bar(cont_m, x="YearMonth", y="NewCases", color="Continent", barmode="stack",
            title="Monthly New Cases by Continent",
            color_discrete_sequence=["#00B4D8","#06D6A0","#FFD60A","#FF6B6B","#FF9A3C","#C77DFF"])
        apply_theme(fig3, height=320,
            xaxis=dict(tickangle=45, nticks=20))
    else:
        fig3 = go.Figure()
        apply_theme(fig3, title="Continent data unavailable")

    return html.Div(className="fade-in", children=[
        html.Div(className="chart-card", children=[dcc.Graph(figure=fig1, config={"displayModeBar": False})]),
        dbc.Row([
            dbc.Col(html.Div(className="chart-card", children=[dcc.Graph(figure=fig2, config={"displayModeBar": False})]), md=5),
            dbc.Col(html.Div(className="chart-card", children=[dcc.Graph(figure=fig3, config={"displayModeBar": False})]), md=7),
        ], className="g-3"),
    ])


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — COUNTRY DEEP-DIVE
# ══════════════════════════════════════════════════════════════════════════════
def build_country():
    controls = html.Div(className="filter-panel", children=[
        dbc.Row([
            dbc.Col([html.Div("Select Countries", className="control-label"),
                dcc.Dropdown(id="country-select", options=[{"label":c,"value":c} for c in countries],
                    value=["United States","India","Brazil","United Kingdom","France"],
                    multi=True, style={"background":"#161B22","color":"#E6EDF3"})
            ], md=9),
            dbc.Col([html.Div("Metric", className="control-label"),
                dcc.Dropdown(id="metric-select",
                    options=[{"label":"New Cases","value":"NewCases"},{"label":"New Deaths","value":"NewDeaths"},
                             {"label":"CFR %","value":"CFR"},{"label":"Recovery Rate %","value":"RecoveryRate"},
                             {"label":"Cases per 100k","value":"CasesPer100k"}],
                    value="NewCases", clearable=False, style={"background":"#161B22","color":"#E6EDF3"})
            ], md=3),
        ])
    ])
    return html.Div(className="fade-in", children=[
        controls,
        html.Div(className="chart-card", children=[dcc.Graph(id="country-trend", config={"displayModeBar": False})]),
        html.Div(className="chart-card", children=[dcc.Graph(id="country-bar",   config={"displayModeBar": False})]),
    ])

@app.callback(
    Output("country-trend","figure"), Output("country-bar","figure"),
    Input("country-select","value"), Input("metric-select","value")
)
def update_country(sel_countries, metric):
    if not sel_countries: sel_countries = ["United States"]
    filt = df_global[df_global["Country"].isin(sel_countries)].copy()
    metric_labels = {"NewCases":"New Cases","NewDeaths":"New Deaths","CFR":"CFR %",
                     "RecoveryRate":"Recovery Rate %","CasesPer100k":"Cases per 100k"}
    label = metric_labels.get(metric, metric)

    fig1 = px.line(filt, x="Date", y=metric, color="Country", title=f"{label} — Country Comparison",
        color_discrete_sequence=["#00B4D8","#06D6A0","#FFD60A","#FF6B6B","#FF9A3C","#C77DFF"])
    fig1.update_traces(line_width=2)
    apply_theme(fig1, height=340)

    snap = df_latest[df_latest["Country"].isin(sel_countries)].copy()
    fig2 = px.bar(snap.sort_values(metric, ascending=False), x="Country", y=metric,
        title=f"Latest {label} by Country", color="Country",
        color_discrete_sequence=["#00B4D8","#06D6A0","#FFD60A","#FF6B6B","#FF9A3C","#C77DFF"])
    fig2.update_traces(marker_line_width=0)
    apply_theme(fig2, height=280, showlegend=False)
    return fig1, fig2


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — REGIONAL COMPARISON
# ══════════════════════════════════════════════════════════════════════════════
def build_regions():
    cont_snap = df_latest.groupby("Continent").agg(
        TotalCases=("Confirmed","sum"), TotalDeaths=("Deaths","sum"),
        Countries=("Country","nunique"), AvgCFR=("CFR","mean"),
        AvgRecovery=("RecoveryRate","mean"),
    ).reset_index().sort_values("TotalCases", ascending=False)
    cont_snap = cont_snap[cont_snap["Continent"].notna() & (cont_snap["Continent"] != "Other")]

    pie = px.pie(cont_snap, values="TotalCases", names="Continent",
        title="Cases Share by Continent", hole=0.55,
        color_discrete_sequence=["#00B4D8","#06D6A0","#FFD60A","#FF6B6B","#FF9A3C","#C77DFF"])
    pie.update_traces(textfont_color="#E6EDF3", marker_line_color="#0D1117", marker_line_width=2)
    apply_theme(pie, height=360)

    cfr_bar = px.bar(cont_snap, x="Continent", y="AvgCFR",
        title="Average Case Fatality Rate by Continent (%)",
        color="AvgCFR", color_continuous_scale=["#06D6A0","#FFD60A","#FF6B6B"])
    cfr_bar.update_traces(marker_line_width=0)
    apply_theme(cfr_bar, height=320, showlegend=False)

    scatter = px.scatter(df_latest[df_latest["CasesPer100k"]>0], x="CasesPer100k", y="CFR",
        size="Confirmed", color="Continent", hover_name="Country",
        title="Cases per 100k vs CFR — Country Scatter",
        color_discrete_sequence=["#00B4D8","#06D6A0","#FFD60A","#FF6B6B","#FF9A3C","#C77DFF"],
        size_max=40, opacity=0.8)
    apply_theme(scatter, height=400)

    return html.Div(className="fade-in", children=[
        dbc.Row([
            dbc.Col(html.Div(className="chart-card", children=[dcc.Graph(figure=pie,     config={"displayModeBar":False})]), md=5),
            dbc.Col(html.Div(className="chart-card", children=[dcc.Graph(figure=cfr_bar, config={"displayModeBar":False})]), md=7),
        ], className="g-3"),
        html.Div(className="chart-card", children=[dcc.Graph(figure=scatter, config={"displayModeBar":False})]),
    ])


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — VACCINATION IMPACT
# ══════════════════════════════════════════════════════════════════════════════
def build_vax():
    vax_df = df_latest[df_latest["VaxPctFull"] > 0].copy()
    vax_scatter = px.scatter(vax_df, x="VaxPctFull", y="CFR",
        size="Confirmed", color="Continent", hover_name="Country",
        title="Vaccination Rate (Full) vs Case Fatality Rate",
        labels={"VaxPctFull":"Fully Vaccinated %","CFR":"Case Fatality Rate %"},
        color_discrete_sequence=["#00B4D8","#06D6A0","#FFD60A","#FF6B6B","#FF9A3C","#C77DFF"],
        size_max=45, opacity=0.85, trendline="ols")
    apply_theme(vax_scatter, height=400)

    # Vax rate by continent bar
    cont_vax = vax_df.groupby("Continent")["VaxPctFull"].mean().reset_index().sort_values("VaxPctFull")
    vax_bar = px.bar(cont_vax, x="VaxPctFull", y="Continent", orientation="h",
        title="Average Full Vaccination Rate by Continent (%)",
        color="VaxPctFull", color_continuous_scale=["#FF6B6B","#FFD60A","#06D6A0"])
    vax_bar.update_traces(marker_line_width=0)
    apply_theme(vax_bar, height=340)

    # Bucketed analysis
    vax_df["VaxBucket"] = pd.cut(vax_df["VaxPctFull"],
        bins=[0,30,60,101], labels=["Low (<30%)","Medium (30-60%)","High (>60%)"])
    bucket_stats = vax_df.groupby("VaxBucket", observed=True).agg(
        Countries=("Country","count"), AvgCFR=("CFR","mean"),
        AvgCasesPer100k=("CasesPer100k","mean")).reset_index()
    bucket_fig = px.bar(bucket_stats, x="VaxBucket", y="AvgCFR",
        title="Average CFR by Vaccination Coverage Tier",
        color="VaxBucket", color_discrete_sequence=["#FF6B6B","#FFD60A","#06D6A0"],
        text="AvgCFR", text_auto=".2f")
    bucket_fig.update_traces(marker_line_width=0, textfont_color="#E6EDF3")
    apply_theme(bucket_fig, height=300, showlegend=False)

    insight = html.Div(className="insight-box", children=[html.P([
        html.Strong("Key Finding: "),
        "Countries with ", html.Strong(">60% full vaccination coverage"), " show significantly ",
        html.Strong("lower average Case Fatality Rates"), " — demonstrating the measurable mortality ",
        "reduction impact of widespread vaccination programs. This correlation is a core analytical ",
        "finding suitable for policy recommendation."
    ])])

    return html.Div(className="fade-in", children=[
        html.Div(className="chart-card", children=[dcc.Graph(figure=vax_scatter, config={"displayModeBar":False}), insight]),
        dbc.Row([
            dbc.Col(html.Div(className="chart-card", children=[dcc.Graph(figure=bucket_fig, config={"displayModeBar":False})]), md=5),
            dbc.Col(html.Div(className="chart-card", children=[dcc.Graph(figure=vax_bar,    config={"displayModeBar":False})]), md=7),
        ], className="g-3"),
    ])


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 6 — RISK DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
def build_risk():
    risk_colors = {"Low":"#06D6A0","Medium":"#FFD60A","High":"#FF9A3C","Critical":"#FF6B6B"}
    risk_order  = {"Critical":0,"High":1,"Medium":2,"Low":3}

    risk_map = px.choropleth(df_latest, locations="Country", locationmode="country names",
        color="RiskTier", hover_name="Country",
        hover_data={"Confirmed":":,","Deaths":":,","CFR":":.2f","daily_growth_rate":":.2f"},
        color_discrete_map=risk_colors,
        category_orders={"RiskTier":["Critical","High","Medium","Low"]},
        title="Global Risk Tier Classification")
    apply_theme(risk_map, height=400,
        geo=dict(bgcolor="rgba(255,255,255,1)", lakecolor="#FFFFFF",
                 landcolor="#F3F2F1", showocean=True, oceancolor="#E1DFDD",
                 showframe=False, showcoastlines=True, coastlinecolor="#C8C6C4"),
        legend=dict(title="Risk Tier"))
    risk_map.update_traces(marker_line_color="#FFFFFF", marker_line_width=0.4)

    # Donut
    risk_counts = df_latest["RiskTier"].value_counts().reset_index()
    risk_counts.columns = ["RiskTier","Count"]
    donut = px.pie(risk_counts, values="Count", names="RiskTier", hole=0.6,
        color="RiskTier", color_discrete_map=risk_colors, title="Risk Tier Distribution")
    donut.update_traces(textfont_color="#E6EDF3", marker_line_color="#0D1117", marker_line_width=2)
    apply_theme(donut, height=340)

    # High risk table
    high_risk = df_latest[df_latest["RiskTier"].isin(["Critical","High"])].copy()
    high_risk["Risk"] = high_risk["RiskTier"]
    high_risk = high_risk.sort_values("ActiveCases", ascending=False).head(20)
    tbl = dash_table.DataTable(
        data=high_risk[["Country","Continent","ActiveCases","CFR","daily_growth_rate","RiskTier"]].to_dict("records"),
        columns=[
            {"name":"Country",       "id":"Country"},
            {"name":"Continent",     "id":"Continent"},
            {"name":"Active Cases",  "id":"ActiveCases",       "type":"numeric","format":{"specifier":","} },
            {"name":"CFR %",         "id":"CFR",               "type":"numeric","format":{"specifier":".2f"}},
            {"name":"Growth Rate %", "id":"daily_growth_rate", "type":"numeric","format":{"specifier":".2f"}},
            {"name":"Risk Tier",     "id":"RiskTier"},
        ],
        style_table={"overflowX":"auto"},
        style_header={"backgroundColor":"#F3F2F1","color":"#323130","fontWeight":"600",
                      "fontSize":"11px","textTransform":"uppercase","border":"1px solid #E1DFDD"},
        style_cell={"backgroundColor":"#FFFFFF","color":"#323130","border":"1px solid #E1DFDD",
                    "fontFamily":"Segoe UI","fontSize":"13px","padding":"10px 14px"},
        style_data_conditional=[
            {"if":{"filter_query":'{RiskTier} = "Critical"'},"color":"#B32824","fontWeight":"700"},
            {"if":{"filter_query":'{RiskTier} = "High"'},    "color":"#E66C37","fontWeight":"600"},
        ],
        page_size=10, sort_action="native",
    )

    return html.Div(className="fade-in", children=[
        html.Div(className="chart-card", children=[dcc.Graph(figure=risk_map, config={"displayModeBar":False})]),
        dbc.Row([
            dbc.Col(html.Div(className="chart-card", children=[dcc.Graph(figure=donut, config={"displayModeBar":False})]), md=4),
            dbc.Col(html.Div(className="chart-card", children=[
                html.Div("High & Critical Risk Countries", className="chart-title"),
                html.Div("Sorted by Active Cases — Top 20", className="chart-subtitle"),
                tbl
            ]), md=8),
        ], className="g-3"),
    ])


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8050)
