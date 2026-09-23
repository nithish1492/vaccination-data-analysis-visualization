-- Power BI / SQL analysis layer
-- Connect Power BI to vaccination.db using an SQLite connector/ODBC driver,
-- or export these queries to your SQL environment.
SELECT year, antigen, antigen_description, coverage_category, AVG(coverage) AS avg_coverage
FROM coverage WHERE group_name='COUNTRIES' AND coverage IS NOT NULL
GROUP BY year,antigen,antigen_description,coverage_category;

SELECT c.year,c.code,c.name,c.antigen,c.coverage,
       i.disease,i.incidence_rate,i.denominator
FROM coverage c JOIN incidence_rate i ON c.code=i.code AND c.year=i.year
WHERE c.group_name='COUNTRIES' AND i.group_name='COUNTRIES'
  AND c.coverage IS NOT NULL AND i.incidence_rate IS NOT NULL;

SELECT year,disease,disease_description,SUM(cases) AS reported_cases
FROM reported_cases WHERE group_name='COUNTRIES' AND cases IS NOT NULL
GROUP BY year,disease,disease_description;

SELECT who_region,description,MIN(year) first_introduction_year,
       COUNT(DISTINCT iso_3_code) countries
FROM vaccine_introduction
WHERE intro LIKE 'Yes%' GROUP BY who_region,description;

SELECT year,vaccine_code,vaccine_description,schedule_rounds,
       target_pop_description,geoarea,COUNT(*) records
FROM vaccine_schedule
GROUP BY year,vaccine_code,vaccine_description,schedule_rounds,target_pop_description,geoarea;
