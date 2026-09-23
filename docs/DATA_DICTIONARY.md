# Data dictionary and project traceability

## Supplied source tables
- Coverage: country/group, year, antigen, coverage category, target number, doses, coverage.
- Incidence rate: country/group, year, disease, denominator, incidence rate.
- Reported cases: country/group, year, disease, cases.
- Vaccine introduction: ISO-3, country, WHO region, year, vaccine description, introduction status.
- Vaccine schedule: ISO-3, country, WHO region, year, vaccine code, rounds, target population, geography, age and source comment.

## Cleaning
The ingestion script trims text and converts blank cells to SQL NULL. It preserves the original reported numeric values. It does not impute values because a missing vaccination report is materially different from a measured zero.

## Questions not supported by the source
Gender, education, urban/rural, population density, seasonal (sub-annual) uptake, and true vaccine demand are not present. The application surfaces these limitations rather than manufacturing values.
