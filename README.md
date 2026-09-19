# Urban Transit Telemetry & Analytics Platform

An automated, serverless ETL pipeline that ingests urban traffic telemetry, loads it into a cloud data warehouse, and serves it through a live analytics dashboard — with zero always-on infrastructure to manage.

**Live app:** https://traffic-etl-pipeline-viniska13.streamlit.app/

---

## Overview

This project simulates a real-world traffic monitoring pipeline: telemetry data (vehicle counts, average speed, congestion status) is generated per road zone, automatically extracted and loaded into a cloud PostgreSQL warehouse on a schedule, and visualized in an interactive dashboard for zone-level analysis.

It's built to demonstrate a full, working **extract → load → visualize** pipeline using only free-tier, serverless infrastructure — no servers to provision or maintain.

## Architecture

```
 ┌─────────────────────┐      ┌──────────────────────┐      ┌────────────────────┐
 │  GitHub Actions      │      │   Neon PostgreSQL     │      │   Streamlit App      │
 │  (scheduled cron)    │ ───▶ │   (cloud data          │ ───▶ │   (Plotly            │
 │  etl_pipeline.py     │      │    warehouse)          │      │    dashboard)        │
 └─────────────────────┘      └──────────────────────┘      └────────────────────┘
      Extract + Load                 Storage                     Serve + Visualize
```

- **Ingestion:** A GitHub Actions workflow runs `etl_pipeline.py` on a schedule, generating/pulling telemetry records per monitored zone (vehicle count, average speed, congestion status).
- **Warehouse:** Records are loaded into a Neon (serverless Postgres) fact table, partitioned logically by zone and timestamp.
- **Serving layer:** `app.py` (Streamlit) queries the warehouse live and renders three views:
  - **Zone Overview** — average traffic volume and transit speed per zone
  - **Speed vs Volume Correlation** — scatter view of vehicle density against speed, color-coded by zone
  - **Raw Telemetry Explorer** — most recent fact-table rows for inspection

## Tech Stack

| Layer | Tool |
|---|---|
| Orchestration | GitHub Actions (scheduled workflow) |
| Data Warehouse | Neon (serverless PostgreSQL) |
| Transformation / Loading | Python (`etl_pipeline.py`) |
| Visualization | Streamlit + Plotly |
| Hosting | Streamlit Community Cloud |

## Monitored Zones

- Airport Corridor
- Central Junction
- Outer Ring Road
- Tech Park Belt

## Running Locally

```bash
git clone https://github.com/viniska13/traffic-etl-pipeline.git
cd traffic-etl-pipeline
pip install -r requirements.txt

# Set your Neon connection string
export NEON_DATABASE_URL="postgresql://<user>:<password>@<host>/<db>"

# Run the ETL job manually
python etl_pipeline.py

# Launch the dashboard
streamlit run app.py
```

## Project Structure

```
.
├── app.py              # Streamlit dashboard
├── etl_pipeline.py      # Extract-transform-load logic
├── requirements.txt     # Python dependencies
└── .github/workflows/    # Scheduled ETL automation
```

## Future Improvements

- [ ] Time-series view of speed/volume trends per zone
- [ ] Data quality checks (schema validation, null/range checks) on each ETL run
- [ ] Congestion-status visualization (currently only in the raw table)
- [ ] Pipeline freshness indicator (last successful sync timestamp)
- [ ] Migrate scheduling from cron to a dedicated orchestrator (Airflow/Dagster) for retry/alerting support
- [ ] Add a lightweight geographic map view of zones

## Author

**Viniska K S**
3rd-year Data Science student, T John Institute of Technology
