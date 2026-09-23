"""SQLite-based EDA report generator. Creates docs/eda_report.md from the loaded data."""
import os, sqlite3, math, statistics
import pandas as pd
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB=os.path.join(ROOT,"vaccination.db")
OUT=os.path.join(ROOT,"docs","eda_report.md")
def main():
    c=sqlite3.connect(DB)
    lines=["# Exploratory Data Analysis\n","Generated from the supplied datasets and normalized SQLite database.\n"]
    for t in ["coverage","incidence_rate","reported_cases","vaccine_introduction","vaccine_schedule"]:
        r=c.execute(f"SELECT COUNT(*),MIN(year),MAX(year) FROM {t}").fetchone()
        lines.append(f"## {t}\n- Rows: {r[0]:,}\n- Year range: {r[1]}–{r[2]}\n")
    for t,col in [("coverage","coverage"),("coverage","target_number"),("coverage","doses"),("incidence_rate","incidence_rate"),("reported_cases","cases")]:
        r=c.execute(f"SELECT SUM(CASE WHEN {col} IS NULL THEN 1 ELSE 0 END),COUNT(*) FROM {t}").fetchone()
        lines.append(f"- `{t}.{col}` missing: {r[0]:,} / {r[1]:,} ({100*r[0]/r[1]:.1f}%)")
    d=pd.read_sql_query("""SELECT c.coverage,i.incidence_rate FROM coverage c JOIN incidence_rate i
      ON c.code=i.code AND c.year=i.year WHERE c.group_name='COUNTRIES' AND c.coverage_category='WUENIC'
      AND c.antigen='MCV1' AND i.group_name='COUNTRIES' AND i.disease='MEASLES'
      AND c.coverage IS NOT NULL AND i.incidence_rate IS NOT NULL""",c)
    lines.append(f"\n## MCV1 vs measles incidence\n- Aligned observations: {len(d):,}\n- Pearson correlation: {d.coverage.corr(d.incidence_rate):.4f}\n- Interpretation: descriptive association only; not causal effectiveness evidence.\n")
    lines.append("\n## Important source limitations\nThe supplied data does not contain gender, education, urban/rural classification, population density, monthly/weekly timestamps, or vaccine sales/orders/inventory. Those questions are therefore not fabricated into the application.\n")
    open(OUT,"w",encoding="utf-8").write("\n".join(lines))
    c.close(); print(OUT)
if __name__=="__main__": main()
