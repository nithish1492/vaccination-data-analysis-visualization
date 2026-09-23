# Vaccination Data Analysis and Visualization — Full Stack Portal

A PyCharm-ready Python project built from the supplied project description and five supplied Excel datasets.

## Run
1. Extract this ZIP.
2. Open the extracted folder in PyCharm.
3. Create/select a Python 3.10+ interpreter.
4. For the portal, run: `python -m pip install -r requirements.txt`. For the full cleaning/EDA toolchain, also run: `python -m pip install -r requirements-dev.txt`.
5. Run `run.py`.
6. Open `http://127.0.0.1:8000`.

The prebuilt `vaccination.db` is included, so the portal starts immediately. Raw Excel sources are also included for reproducibility.

## What is implemented
- SQL/SQLite normalized analytical database.
- Data cleaning pipeline with missing-value preservation and source-row integrity.
- Coverage, disease incidence, reported cases, vaccine introduction and schedule analysis.
- Interactive premium healthcare-style frontend.
- Coverage trends, disease trends, scatter/correlation analysis, dose drop-off, introduction timelines, schedule explorer, country explorer.
- Scenario views for low coverage, measles campaign, target-volume projection and outbreak response.
- Explicit data-availability guardrails: gender, education, urban/rural, seasonality and population density are not fabricated because they are absent from the supplied files.
- Power BI-ready SQL views/queries and dashboard mapping in `powerbi/`.
- EDA and cleaning scripts in `scripts/`.

## Interpretation
Coverage vs disease analysis is observational. A correlation or pre/post change does not establish causal vaccine effectiveness. The source data contains annual observations and different incidence denominators; the portal preserves the denominator text rather than silently converting rates.

## Source
The supplied project document defines the objective, cleaning, SQL, Power BI, EDA, visualization and business questions. The supplied Excel files are the sole data source for the application.


## Vercel deployment

This project is Vercel-ready as a FastAPI application. The deployable portal uses the bundled `vaccination.db` SQLite database and the existing ImmunoScope frontend. Raw Excel files, documentation, SQL scripts, Power BI assets and development artifacts are excluded from the Vercel bundle via `.vercelignore`; they remain available in the GitHub repository.

For local development, continue to run `python run.py` and open `http://127.0.0.1:8000`.

For Vercel, connect this repository to a Vercel project and deploy from the repository root. The FastAPI entry point is `api/index.py`. After deployment, verify `/`, `/api/summary`, and `/api/filters`.

The application uses SQLite for the self-contained demo deployment. Because Vercel function storage is not a persistent writable database, the deployed application treats the bundled database as read-only. For a production system requiring live writes or scheduled database updates, use an external managed database.
