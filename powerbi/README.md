# Power BI integration

The project description explicitly calls for Power BI connected to the SQL database and interactive reports. The supplied build includes the normalized SQLite database and `sql/analysis_queries.sql` with Power BI-ready analytical queries.

## Suggested report pages
1. Executive overview — KPI cards, MCV1 trend, measles incidence, coverage-vs-incidence scatter.
2. Coverage — year/antigen/category slicers, trend lines, dose drop-off, target vs doses.
3. Disease burden — reported cases and incidence by disease/country/year.
4. Introduction — WHO-region introduction timelines and descriptive pre/post cases.
5. Schedule — rounds, target populations, age and geography.
6. Geography — country coverage and incidence tables/maps if a Power BI map visual is available.

## Important
Do not label a correlation as causal effectiveness. Preserve incidence denominators. Do not create gender, education, urban/rural, seasonality, density, or demand fields because they are absent from the supplied data.
