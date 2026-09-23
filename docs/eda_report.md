# Exploratory Data Analysis

Generated from the supplied datasets and normalized SQLite database.

## coverage
- Rows: 399,858
- Year range: 1980–2023

## incidence_rate
- Rows: 84,945
- Year range: 1980–2023

## reported_cases
- Rows: 84,869
- Year range: 1980–2023

## vaccine_introduction
- Rows: 138,320
- Year range: 1940–2023

## vaccine_schedule
- Rows: 8,052
- Year range: 2019–2023

- `coverage.coverage` missing: 169,381 / 399,858 (42.4%)
- `coverage.target_number` missing: 320,828 / 399,858 (80.2%)
- `coverage.doses` missing: 320,531 / 399,858 (80.2%)
- `incidence_rate.incidence_rate` missing: 23,361 / 84,945 (27.5%)
- `reported_cases.cases` missing: 19,399 / 84,869 (22.9%)

## MCV1 vs measles incidence
- Aligned observations: 7,280
- Pearson correlation: -0.2144
- Interpretation: descriptive association only; not causal effectiveness evidence.


## Important source limitations
The supplied data does not contain gender, education, urban/rural classification, population density, monthly/weekly timestamps, or vaccine sales/orders/inventory. Those questions are therefore not fabricated into the application.
