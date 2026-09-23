
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import sqlite3, os, math, statistics
from typing import Optional

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(BASE, "vaccination.db")
FRONTEND = os.path.join(BASE, "frontend")

app = FastAPI(title="Vaccination Intelligence Portal", version="1.0.0")

def get_conn():
    c=sqlite3.connect(DB)
    c.row_factory=sqlite3.Row
    return c

def rows(sql, params=()):
    with get_conn() as c:
        return [dict(r) for r in c.execute(sql, params).fetchall()]

def row(sql, params=()):
    with get_conn() as c:
        r=c.execute(sql,params).fetchone()
        return dict(r) if r else {}

def safe_num(v):
    if v is None: return None
    try:
        x=float(v)
        return None if math.isnan(x) or math.isinf(x) else x
    except: return None

@app.get("/api/summary")
def summary():
    return row("""
    SELECT
      (SELECT count(*) FROM countries) countries,
      (SELECT count(*) FROM coverage) coverage_records,
      (SELECT count(*) FROM incidence_rate) incidence_records,
      (SELECT count(*) FROM reported_cases) case_records,
      (SELECT count(*) FROM vaccine_introduction) introduction_records,
      (SELECT count(*) FROM vaccine_schedule) schedule_records,
      (SELECT min(year) FROM coverage WHERE group_name='COUNTRIES') coverage_start,
      (SELECT max(year) FROM coverage WHERE group_name='COUNTRIES') coverage_end
    """)

@app.get("/api/filters")
def filters():
    return {
      "countries": rows("SELECT code,name FROM countries ORDER BY name"),
      "antigens": rows("SELECT DISTINCT antigen code, antigen_description name FROM coverage WHERE group_name='COUNTRIES' AND antigen IS NOT NULL ORDER BY name"),
      "diseases": rows("SELECT DISTINCT disease code, disease_description name FROM incidence_rate WHERE group_name='COUNTRIES' AND disease IS NOT NULL ORDER BY name"),
      "who_regions": rows("SELECT DISTINCT who_region code, who_region name FROM vaccine_introduction WHERE who_region IS NOT NULL ORDER BY who_region"),
      "years": rows("SELECT DISTINCT year FROM coverage WHERE group_name='COUNTRIES' AND year IS NOT NULL ORDER BY year")
    }

@app.get("/api/trends")
def trends(antigen: str="MCV1", category: str="WUENIC", country: Optional[str]=None):
    where=["group_name='COUNTRIES'","antigen=?","coverage_category=?","coverage IS NOT NULL"]
    params=[antigen,category]
    if country:
        where.append("code=?"); params.append(country)
    return rows(f"""SELECT year, ROUND(AVG(coverage),2) coverage, COUNT(*) records
                    FROM coverage WHERE {' AND '.join(where)}
                    GROUP BY year ORDER BY year""",params)

@app.get("/api/disease-trend")
def disease_trend(disease: str="MEASLES", country: Optional[str]=None):
    where=["group_name='COUNTRIES'","disease=?","cases IS NOT NULL"]; params=[disease]
    if country: where.append("code=?"); params.append(country)
    return rows(f"""SELECT year, ROUND(SUM(cases),2) cases, COUNT(*) records
                    FROM reported_cases WHERE {' AND '.join(where)}
                    GROUP BY year ORDER BY year""",params)

@app.get("/api/incidence-trend")
def incidence_trend(disease: str="MEASLES", country: Optional[str]=None):
    where=["group_name='COUNTRIES'","disease=?","incidence_rate IS NOT NULL"]; params=[disease]
    if country: where.append("code=?"); params.append(country)
    return rows(f"""SELECT year, ROUND(AVG(incidence_rate),4) incidence_rate, COUNT(*) records
                    FROM incidence_rate WHERE {' AND '.join(where)}
                    GROUP BY year ORDER BY year""",params)

@app.get("/api/correlation")
def correlation(antigen: str="MCV1", disease: str="MEASLES", category: str="WUENIC"):
    data=rows("""
      SELECT c.code,c.name,c.year,c.coverage,i.incidence_rate
      FROM coverage c JOIN incidence_rate i
      ON c.code=i.code AND c.year=i.year
      WHERE c.group_name='COUNTRIES' AND c.coverage_category=? AND c.antigen=?
      AND i.group_name='COUNTRIES' AND i.disease=?
      AND c.coverage IS NOT NULL AND i.incidence_rate IS NOT NULL
    """,(category,antigen,disease))
    vals=[(x["coverage"],x["incidence_rate"]) for x in data]
    if len(vals)<2: corr=None
    else:
        xs=[v[0] for v in vals]; ys=[v[1] for v in vals]
        mx=sum(xs)/len(xs); my=sum(ys)/len(ys)
        den=((sum((x-mx)**2 for x in xs)*sum((y-my)**2 for y in ys))**0.5)
        corr=(sum((x-mx)*(y-my) for x,y in vals)/den) if den else None
    return {"correlation":corr,"n":len(vals),"interpretation":"Association only; correlation does not establish vaccine effectiveness or causality.","data":data[:1500]}

@app.get("/api/dropoff")
def dropoff(category: str="WUENIC", country: Optional[str]=None):
    # Dose 1 vs dose 2 for measles; also show any directly available 1st/2nd dose antigen pairs.
    antigens=[("MCV1","MCV2"),("BCG","BCG")] # second is handled separately below
    where="group_name='COUNTRIES' AND coverage_category=? AND coverage IS NOT NULL"
    params=[category]
    extra=""
    if country: extra=" AND code=?"; params.append(country)
    q=rows(f"""SELECT antigen, year, AVG(coverage) coverage FROM coverage
               WHERE {where}{extra} AND antigen IN ('MCV1','MCV2')
               GROUP BY antigen,year ORDER BY year""",params)
    by={}
    for r in q: by.setdefault(r["year"],{})[r["antigen"]]=r["coverage"]
    out=[]
    for y,v in by.items():
        if "MCV1" in v and "MCV2" in v:
            out.append({"year":y,"dose1":v["MCV1"],"dose2":v["MCV2"],"dropoff":round(v["MCV1"]-v["MCV2"],2)})
    return {"series":out,"definition":"MCV1 minus MCV2 average coverage for aligned country-year observations.","note":"The supplied data does not provide a universal dose-order field for every antigen; this view uses the explicit MCV1/MCV2 codes."}

@app.get("/api/high-incidence")
def high_incidence(antigen: str="MCV1", disease: str="MEASLES", threshold: float=80, category: str="WUENIC", year: Optional[int]=None):
    if year is None:
        year=row("SELECT max(year) y FROM coverage WHERE group_name='COUNTRIES' AND coverage_category=? AND antigen=?",(category,antigen)).get("y")
    return rows("""SELECT c.code,c.name,ROUND(c.coverage,2) coverage,ROUND(i.incidence_rate,4) incidence_rate,i.denominator
      FROM coverage c JOIN incidence_rate i ON c.code=i.code AND c.year=i.year
      WHERE c.group_name='COUNTRIES' AND c.year=? AND c.coverage_category=? AND c.antigen=?
      AND i.group_name='COUNTRIES' AND i.disease=? AND c.coverage>=? AND c.coverage IS NOT NULL AND i.incidence_rate IS NOT NULL
      ORDER BY i.incidence_rate DESC LIMIT 25""",(year,category,antigen,disease,threshold))

@app.get("/api/regions")
def regions(year: Optional[int]=None, antigen: str="MCV1", category: str="WUENIC"):
    if year is None: year=row("SELECT max(year) y FROM coverage WHERE group_name='COUNTRIES' AND coverage_category=? AND antigen=?",(category,antigen)).get("y")
    return rows("""SELECT substr(c.name,1,0) dummy, c.code,c.name, ROUND(c.coverage,2) coverage
      FROM coverage c WHERE c.group_name='COUNTRIES' AND c.year=? AND c.coverage_category=? AND c.antigen=? AND c.coverage IS NOT NULL
      ORDER BY c.coverage ASC LIMIT 30""",(year,category,antigen))

@app.get("/api/introduction-impact")
def introduction_impact(vaccine: str="Measles-containing vaccine", disease: str="MEASLES"):
    # Countries with a Yes introduction record. Compare first available disease cases before/after by country, without claiming causality.
    intro=rows("""SELECT iso_3_code code,country_name name,MIN(year) intro_year
                  FROM vaccine_introduction
                  WHERE description LIKE ? AND intro LIKE 'Yes%'
                  GROUP BY iso_3_code,country_name""",("%"+vaccine+"%",))
    out=[]
    for x in intro:
        before=row("""SELECT AVG(cases) v FROM reported_cases WHERE group_name='COUNTRIES' AND code=? AND disease=? AND year BETWEEN ? AND ? AND cases IS NOT NULL""",(x["code"],disease,x["intro_year"]-3,x["intro_year"]-1)).get("v")
        after=row("""SELECT AVG(cases) v FROM reported_cases WHERE group_name='COUNTRIES' AND code=? AND disease=? AND year BETWEEN ? AND ? AND cases IS NOT NULL""",(x["code"],disease,x["intro_year"]+1,x["intro_year"]+3)).get("v")
        if before is not None and after is not None:
            pct=(before-after)/before*100 if before else None
            out.append({"code":x["code"],"name":x["name"],"intro_year":x["intro_year"],"before_avg_cases":round(before,2),"after_avg_cases":round(after,2),"change_percent":round(pct,2) if pct is not None else None})
    out.sort(key=lambda z:(z["change_percent"] is None,z["change_percent"] if z["change_percent"] is not None else 0),reverse=True)
    return {"rows":out[:100],"note":"Pre/post descriptive comparison only. Introduction timing is observational and does not control for confounding."}

@app.get("/api/disease-reduction")
def disease_reduction():
    return rows("""WITH a AS (
      SELECT disease,disease_description,AVG(cases) avg_cases_early
      FROM reported_cases WHERE group_name='COUNTRIES' AND cases IS NOT NULL AND year BETWEEN 2000 AND 2005
      GROUP BY disease,disease_description),
    b AS (
      SELECT disease,AVG(cases) avg_cases_late
      FROM reported_cases WHERE group_name='COUNTRIES' AND cases IS NOT NULL AND year BETWEEN 2018 AND 2023
      GROUP BY disease)
    SELECT a.disease,a.disease_description,ROUND(a.avg_cases_early,2) avg_cases_2000_2005,
      ROUND(b.avg_cases_late,2) avg_cases_2018_2023,
      ROUND((a.avg_cases_early-b.avg_cases_late)*100.0/NULLIF(a.avg_cases_early,0),2) reduction_percent
    FROM a JOIN b USING(disease) ORDER BY reduction_percent DESC""")

@app.get("/api/target-coverage")
def target_coverage(antigen: str="MCV1", category: str="WUENIC"):
    return rows("""SELECT year,ROUND(SUM(doses),0) doses,ROUND(SUM(target_number),0) target_number,
      ROUND(SUM(doses)*100.0/NULLIF(SUM(target_number),0),2) derived_dose_to_target_pct,
      COUNT(*) records_with_rows,
      SUM(CASE WHEN target_number IS NOT NULL AND doses IS NOT NULL THEN 1 ELSE 0 END) complete_records
      FROM coverage WHERE group_name='COUNTRIES' AND antigen=? AND coverage_category=?
      GROUP BY year ORDER BY year""",(antigen,category))

@app.get("/api/schedule-impact")
def schedule_impact(vaccine_code: str="MM"):
    return rows("""SELECT year, schedule_rounds, target_pop_description, COUNT(*) records
      FROM vaccine_schedule WHERE vaccine_code=? GROUP BY year,schedule_rounds,target_pop_description
      ORDER BY year,schedule_rounds""",(vaccine_code,))

@app.get("/api/introduction-timelines")
def introduction_timelines():
    return rows("""SELECT who_region,description,MIN(year) first_year,MAX(year) last_year,
      COUNT(DISTINCT iso_3_code) countries
      FROM vaccine_introduction WHERE intro LIKE 'Yes%' AND description IS NOT NULL
      GROUP BY who_region,description ORDER BY description,who_region""")

@app.get("/api/antigen-correlation")
def antigen_correlation(disease: str="MEASLES", category: str="WUENIC"):
    ant=rows("SELECT DISTINCT antigen,antigen_description FROM coverage WHERE group_name='COUNTRIES' AND coverage_category=? AND antigen IS NOT NULL",(category,))
    result=[]
    for a in ant:
        d=rows("""SELECT c.coverage,i.incidence_rate FROM coverage c JOIN incidence_rate i
          ON c.code=i.code AND c.year=i.year WHERE c.group_name='COUNTRIES' AND c.coverage_category=? AND c.antigen=?
          AND i.group_name='COUNTRIES' AND i.disease=? AND c.coverage IS NOT NULL AND i.incidence_rate IS NOT NULL
          LIMIT 50000""",(category,a["antigen"],disease))
        if len(d)<10: continue
        xs=[z["coverage"] for z in d]; ys=[z["incidence_rate"] for z in d]; mx=sum(xs)/len(xs); my=sum(ys)/len(ys)
        den=(sum((x-mx)**2 for x in xs)*sum((y-my)**2 for y in ys))**0.5
        corr=sum((x-mx)*(y-my) for x,y in zip(xs,ys))/den if den else None
        result.append({"antigen":a["antigen"],"description":a["antigen_description"],"correlation":round(corr,4) if corr is not None else None,"n":len(d)})
    return sorted(result,key=lambda z:(z["correlation"] is None,abs(z["correlation"] or 0)),reverse=True)

@app.get("/api/availability-gaps")
def availability_gaps(vaccine: str="Measles-containing vaccine", year: Optional[int]=None):
    if year is None: year=row("SELECT max(year) y FROM vaccine_introduction").get("y")
    return rows("""SELECT who_region,COUNT(DISTINCT iso_3_code) countries,
      SUM(CASE WHEN intro LIKE 'Yes%' THEN 1 ELSE 0 END) introduced_records,
      SUM(CASE WHEN intro='No' THEN 1 ELSE 0 END) no_records,
      SUM(CASE WHEN intro='ND' THEN 1 ELSE 0 END) nd_records
      FROM vaccine_introduction WHERE description LIKE ? AND year=? GROUP BY who_region ORDER BY who_region""",("%"+vaccine+"%",year))

@app.get("/api/high-priority-gaps")
def high_priority_gaps(antigens: str="MCV1,HEPB"):
    codes=[x.strip() for x in antigens.split(",") if x.strip()]
    placeholders=",".join(["?"]*len(codes))
    return rows(f"""SELECT antigen,antigen_description,year,ROUND(AVG(coverage),2) avg_coverage,
      COUNT(*) observations FROM coverage WHERE group_name='COUNTRIES' AND coverage_category='WUENIC'
      AND antigen IN ({placeholders}) AND coverage IS NOT NULL GROUP BY antigen,antigen_description,year ORDER BY antigen,year""",codes)

@app.get("/api/geographic-prevalence")
def geographic_prevalence(disease: str="MEASLES"):
    return rows("""SELECT name,code,ROUND(AVG(incidence_rate),4) avg_incidence,
      COUNT(*) observations FROM incidence_rate WHERE group_name='COUNTRIES' AND disease=? AND incidence_rate IS NOT NULL
      GROUP BY code,name ORDER BY avg_incidence DESC LIMIT 30""",(disease,))

@app.get("/api/country")
def country(code: str):
    return {
      "country": row("SELECT code,name FROM countries WHERE code=?",(code,)),
      "coverage": rows("""SELECT year,antigen,antigen_description,coverage_category,ROUND(coverage,2) coverage
        FROM coverage WHERE group_name='COUNTRIES' AND code=? AND coverage IS NOT NULL ORDER BY year DESC,antigen LIMIT 500""",(code,)),
      "incidence": rows("""SELECT year,disease,disease_description,denominator,incidence_rate
        FROM incidence_rate WHERE group_name='COUNTRIES' AND code=? AND incidence_rate IS NOT NULL ORDER BY year DESC,disease""",(code,)),
      "introductions": rows("""SELECT year,description,intro,who_region FROM vaccine_introduction WHERE iso_3_code=? ORDER BY year DESC""",(code,)),
      "schedule": rows("""SELECT year,vaccine_code,vaccine_description,schedule_rounds,target_pop_description,geoarea,age_administered
        FROM vaccine_schedule WHERE iso_3_code=? ORDER BY year DESC,vaccine_code,schedule_rounds""",(code,))
    }

@app.get("/api/scenario/low-coverage")
def scenario_low_coverage(year: int=2023, antigen: str="MCV1", threshold: float=80):
    return {"year":year,"antigen":antigen,"threshold":threshold,"countries":rows("""SELECT code,name,ROUND(coverage,2) coverage
      FROM coverage WHERE group_name='COUNTRIES' AND year=? AND coverage_category='WUENIC' AND antigen=? AND coverage IS NOT NULL AND coverage<?
      ORDER BY coverage ASC""",(year,antigen,threshold))}

@app.get("/api/scenario/measles")
def scenario_measles_campaign(launch_year: int=2018):
    return {"launch_year":launch_year,"trend":rows("""SELECT year,ROUND(SUM(cases),0) cases,COUNT(*) observations
      FROM reported_cases WHERE group_name='COUNTRIES' AND disease='MEASLES' AND cases IS NOT NULL AND year BETWEEN ? AND ?
      GROUP BY year ORDER BY year""",(launch_year-5,launch_year+5)),
      "note":"Descriptive before/after trend around the selected year; not an impact evaluation."}

@app.get("/api/scenario/demand")
def scenario_demand(antigen: str="MCV1", category: str="WUENIC", horizon: int=3):
    # Linear projection of observed target_number, only where annual aggregate exists. Explicitly not a demand forecast.
    data=rows("""SELECT year,SUM(target_number) target_number FROM coverage
      WHERE group_name='COUNTRIES' AND antigen=? AND coverage_category=? AND target_number IS NOT NULL
      GROUP BY year ORDER BY year""",(antigen,category))
    if len(data)<3: return {"observed":data,"projection":[],"note":"Insufficient observed target-number history for a projection."}
    xs=[float(x["year"]) for x in data]; ys=[float(x["target_number"]) for x in data]
    xbar=sum(xs)/len(xs); ybar=sum(ys)/len(ys)
    den=sum((x-xbar)**2 for x in xs)
    slope=(sum((x-xbar)*(y-ybar) for x,y in zip(xs,ys))/den) if den else 0.0
    intercept=ybar-slope*xbar
    proj=[{"year":int(xs[-1]+i),"projected_target_number":round(slope*(xs[-1]+i)+intercept,0)} for i in range(1,horizon+1)]
    return {"observed":data,"projection":proj,"note":"Projection of reported target_number, not a vaccine-demand forecast. The supplied datasets do not contain sales, orders, inventory, or demand variables."}

@app.get("/api/scenario/outbreak")
def scenario_outbreak(year: int=2023, disease: str="MEASLES"):
    return {"year":year,"disease":disease,"countries":rows("""SELECT c.code,c.name,ROUND(i.incidence_rate,4) incidence_rate,i.denominator
      FROM incidence_rate i JOIN countries c ON c.code=i.code
      WHERE i.group_name='COUNTRIES' AND i.disease=? AND i.year=? AND i.incidence_rate IS NOT NULL
      ORDER BY i.incidence_rate DESC LIMIT 25""",(disease,year))}

@app.get("/api/limitations")
def limitations():
    return {
      "available": [
        "Country/year vaccination coverage by antigen and coverage category",
        "Disease incidence rates and reported cases by country/year",
        "Vaccine introduction status, WHO region and year",
        "Vaccine schedule rounds, target population, geography and age administered",
        "Target number and doses where reported"
      ],
      "not_available": [
        "Gender-specific vaccination rates",
        "Education-level vaccination rates",
        "Urban vs rural vaccination rates",
        "Monthly/weekly/daily timestamps for seasonal uptake",
        "Population density",
        "Vaccine sales, orders, inventory or consumption needed for a true demand forecast"
      ],
      "interpretation": "The application never fabricates these missing dimensions. Any association between coverage and disease measures is descriptive and does not establish causal vaccine effectiveness."
    }

@app.get("/")
def home():
    return FileResponse(os.path.join(FRONTEND,"index.html"))

app.mount("/static", StaticFiles(directory=FRONTEND), name="static")
