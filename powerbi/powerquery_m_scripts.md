# Power Query M Scripts — Global Health Trend Analysis Dashboard
## Power BI · Data Transformation Layer

> Use these scripts in **Power Query Editor → Advanced Editor** for each query.
> Data files must be loaded from `data/processed/` folder relative to the `.pbix` file.

---

## Query 1: FactCovid (Main Fact Table)

```m
let
    // ── Source ──────────────────────────────────────────────────────────────
    Source = Csv.Document(
        File.Contents(
            Text.Combine({
                Text.From(
                    Path.Combine(
                        Text.BeforeDelimiter(
                            Excel.CurrentWorkbook(){[Name="Sheet1"]}[Content]{0}[Column1],
                            "powerbi"
                        ),
                        "data\processed\covid_global.csv"
                    )
                )
            })
        ),
        [Delimiter=",", Columns=32, Encoding=65001, QuoteStyle=QuoteStyle.None]
    ),
    
    // ── Promote Headers ─────────────────────────────────────────────────────
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    
    // ── Change Types ────────────────────────────────────────────────────────
    #"Changed Types" = Table.TransformColumnTypes(#"Promoted Headers", {
        {"Country",              type text},
        {"Date",                 type date},
        {"Confirmed",            Int64.Type},
        {"Deaths",               Int64.Type},
        {"Recovered",            Int64.Type},
        {"NewCases",             Int64.Type},
        {"NewDeaths",            Int64.Type},
        {"NewRecovered",         Int64.Type},
        {"NewCases_rolling7d",   type number},
        {"NewDeaths_rolling7d",  type number},
        {"ActiveCases",          Int64.Type},
        {"CFR",                  type number},
        {"RecoveryRate",         type number},
        {"daily_growth_rate",    type number},
        {"CasesPer100k",         type number},
        {"DeathsPer100k",        type number},
        {"RiskTier",             type text},
        {"Continent",            type text},
        {"VaxPctFull",           type number},
        {"VaxPct1Dose",          type number},
        {"Year",                 Int64.Type},
        {"Month",                Int64.Type},
        {"MonthName",            type text},
        {"Quarter",              Int64.Type},
        {"YearMonth",            type text},
        {"DateKey",              Int64.Type}
    }),

    // ── Remove nulls in critical columns ───────────────────────────────────
    #"Filtered Rows" = Table.SelectRows(#"Changed Types", each 
        [Country] <> null and [Country] <> "" and [Date] <> null
    ),

    // ── Replace negative values (data quality) ─────────────────────────────
    #"Replace Negatives" = Table.TransformColumns(#"Filtered Rows", {
        {"NewCases",    each if _ < 0 then 0 else _, Int64.Type},
        {"NewDeaths",   each if _ < 0 then 0 else _, Int64.Type},
        {"ActiveCases", each if _ < 0 then 0 else _, Int64.Type}
    }),

    // ── Add DateKey if missing ──────────────────────────────────────────────
    #"Add DateKey" = Table.AddColumn(#"Replace Negatives", "DateKeyCalc",
        each Date.Year([Date]) * 10000 + Date.Month([Date]) * 100 + Date.Day([Date]),
        Int64.Type
    )

in
    #"Add DateKey"
```

---

## Query 2: FactVaccination

```m
let
    Source = Csv.Document(
        File.Contents("[YOUR_PATH]\data\processed\vaccination_data.csv"),
        [Delimiter=",", Columns=10, Encoding=65001, QuoteStyle=QuoteStyle.None]
    ),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Types" = Table.TransformColumnTypes(#"Promoted Headers", {
        {"Country",                          type text},
        {"Date",                             type date},
        {"total_vaccinations",               Int64.Type},
        {"people_vaccinated",                Int64.Type},
        {"people_fully_vaccinated",          Int64.Type},
        {"total_boosters",                   Int64.Type},
        {"VaxPct1Dose",                      type number},
        {"VaxPctFull",                       type number},
        {"new_vaccinations",                 Int64.Type},
        {"new_vaccinations_smoothed",        type number}
    }),
    #"Replaced Errors" = Table.ReplaceErrorValues(#"Changed Types", {
        {"total_vaccinations", 0},
        {"people_vaccinated", 0},
        {"VaxPct1Dose", 0},
        {"VaxPctFull", 0}
    }),
    #"Fill Down Vaccinations" = Table.FillDown(#"Replaced Errors", {
        "VaxPct1Dose", "VaxPctFull"
    })
in
    #"Fill Down Vaccinations"
```

---

## Query 3: DimDate (Date Dimension)

```m
let
    // ── Parameters ──────────────────────────────────────────────────────────
    StartDate = #date(2020, 1, 22),
    EndDate   = #date(2023, 3, 10),
    
    // ── Generate date list ──────────────────────────────────────────────────
    DateList = List.Dates(StartDate, Duration.Days(EndDate - StartDate) + 1, #duration(1, 0, 0, 0)),
    DateTable = Table.FromList(DateList, Splitter.SplitByNothing(), {"Date"}, null, ExtraValues.Error),
    
    // ── Change type ─────────────────────────────────────────────────────────
    #"Changed Type" = Table.TransformColumnTypes(DateTable, {{"Date", type date}}),

    // ── Add date attributes ─────────────────────────────────────────────────
    #"Add Year" = Table.AddColumn(#"Changed Type", "Year",
        each Date.Year([Date]), Int64.Type),
    
    #"Add Quarter" = Table.AddColumn(#"Add Year", "Quarter",
        each Date.QuarterOfYear([Date]), Int64.Type),
    
    #"Add Month" = Table.AddColumn(#"Add Quarter", "Month",
        each Date.Month([Date]), Int64.Type),
    
    #"Add MonthName" = Table.AddColumn(#"Add Month", "MonthName",
        each Date.MonthName([Date]), type text),
    
    #"Add Week" = Table.AddColumn(#"Add MonthName", "WeekOfYear",
        each Date.WeekOfYear([Date]), Int64.Type),
    
    #"Add DayOfWeek" = Table.AddColumn(#"Add Week", "DayOfWeek",
        each Date.DayOfWeek([Date], Day.Monday) + 1, Int64.Type),
    
    #"Add DayName" = Table.AddColumn(#"Add DayOfWeek", "DayName",
        each Date.DayOfWeekName([Date]), type text),
    
    #"Add IsWeekend" = Table.AddColumn(#"Add DayName", "IsWeekend",
        each if Date.DayOfWeek([Date], Day.Monday) >= 5 then 1 else 0, Int64.Type),
    
    #"Add YearMonth" = Table.AddColumn(#"Add IsWeekend", "YearMonth",
        each Text.From(Date.Year([Date])) & "-" & Text.PadStart(Text.From(Date.Month([Date])), 2, "0"),
        type text),
    
    #"Add YearQuarter" = Table.AddColumn(#"Add YearMonth", "YearQuarter",
        each Text.From(Date.Year([Date])) & "-Q" & Text.From(Date.QuarterOfYear([Date])),
        type text),
    
    #"Add DateKey" = Table.AddColumn(#"Add YearQuarter", "DateKey",
        each Date.Year([Date]) * 10000 + Date.Month([Date]) * 100 + Date.Day([Date]),
        Int64.Type),

    #"Add ShortDate" = Table.AddColumn(#"Add DateKey", "ShortMonthYear",
        each Text.Start(Date.MonthName([Date]), 3) & " " & Text.From(Date.Year([Date])),
        type text)

in
    #"Add ShortDate"
```

---

## Query 4: DimCountry

```m
let
    Source = Csv.Document(
        File.Contents("[YOUR_PATH]\data\processed\dim_country.csv"),
        [Delimiter=",", Columns=3, Encoding=65001, QuoteStyle=QuoteStyle.None]
    ),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Types" = Table.TransformColumnTypes(#"Promoted Headers", {
        {"Country",    type text},
        {"Continent",  type text},
        {"Population", Int64.Type}
    }),
    #"Fill Continent" = Table.ReplaceValue(#"Changed Types", null, "Other",
        Replacer.ReplaceValue, {"Continent"}),
    
    // ── Add ISO Region groupings ────────────────────────────────────────────
    #"Add Region" = Table.AddColumn(#"Fill Continent", "Region",
        each if [Continent] = "Asia" then
                (if List.Contains({"China","Japan","South Korea","Taiwan","Singapore"}, [Country])
                 then "East Asia" else "South/SE Asia")
             else if [Continent] = "Europe" then
                (if List.Contains({"Germany","France","United Kingdom","Italy","Spain"}, [Country])
                 then "Western Europe" else "Eastern Europe")
             else [Continent],
        type text)
in
    #"Add Region"
```

---

## Query 5: CovidMonthly (Monthly Aggregation)

```m
let
    Source = Csv.Document(
        File.Contents("[YOUR_PATH]\data\processed\covid_monthly.csv"),
        [Delimiter=",", Columns=14, Encoding=65001, QuoteStyle=QuoteStyle.None]
    ),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Types" = Table.TransformColumnTypes(#"Promoted Headers", {
        {"Country",      type text},
        {"Continent",    type text},
        {"Year",         Int64.Type},
        {"Month",        Int64.Type},
        {"MonthName",    type text},
        {"YearMonth",    type text},
        {"Confirmed",    Int64.Type},
        {"Deaths",       Int64.Type},
        {"Recovered",    Int64.Type},
        {"NewCases",     Int64.Type},
        {"NewDeaths",    Int64.Type},
        {"NewRecovered", Int64.Type},
        {"CFR",          type number},
        {"RecoveryRate", type number}
    })
in
    #"Changed Types"
```

---

## Data Model Relationships

Set these relationships in **Model View** → Manage Relationships:

| From Table → Column | To Table → Column | Cardinality | Active |
|---------------------|-------------------|-------------|--------|
| FactCovid[DateKey] | DimDate[DateKey] | Many-to-One (N:1) | ✅ Yes |
| FactCovid[Country] | DimCountry[Country] | Many-to-One (N:1) | ✅ Yes |
| FactVaccination[DateKey] | DimDate[DateKey] | Many-to-One (N:1) | ✅ Yes |
| FactVaccination[Country] | DimCountry[Country] | Many-to-One (N:1) | ✅ Yes |
| CovidMonthly[Country] | DimCountry[Country] | Many-to-One (N:1) | ✅ Yes |

---

## Theme JSON (Import in Power BI via View → Themes → Browse)

```json
{
  "name": "GlobalHealthDark",
  "dataColors": ["#00B4D8","#0077B6","#90E0EF","#FFD60A","#FF6B6B","#06D6A0","#FF9A3C","#C77DFF"],
  "background": "#0D1117",
  "foreground": "#E6EDF3",
  "tableAccent": "#00B4D8",
  "visualStyles": {
    "*": {
      "*": {
        "background": [{"color": {"solid": {"color": "#161B22"}}}],
        "foreground": [{"color": {"solid": {"color": "#E6EDF3"}}}]
      }
    },
    "card": {
      "*": {
        "background": [{"color": {"solid": {"color": "#21262D"}}}],
        "border": [{"color": {"solid": {"color": "#30363D"}}}]
      }
    },
    "map": {
      "*": {
        "background": [{"color": {"solid": {"color": "#0D1117"}}}]
      }
    }
  }
}
```
