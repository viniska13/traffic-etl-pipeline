# 🚦 Automated Transit ETL Pipeline & Cloud Data Warehouse

An automated, serverless cloud data pipeline that continuously extracts, transforms, and loads urban traffic telemetry into a Cloud PostgreSQL Data Warehouse.

## Architecture Flow
```text
[ Open Telemetry / API ] 
         │ (Extract)
         ▼
[ Python ETL Engine ] ──── (Transform: Congestion Rules)
         │ (Load)
         ▼
[ Neon Cloud PostgreSQL ] ───> Scheduled Hourly via GitHub Actions
```
1.Tech Stack
*Language: Python 3.10 (Pandas, Psycopg2)

*Database: Cloud PostgreSQL (Neon.tech)

*Automation / Orchestration: GitHub Actions (CI/CD Cron Jobs)

*Data Modeling: Time-Series Fact Tables & SQL Analytics

2.Key Engineering Features
*Serverless Ingestion: Runs hourly via scheduled GitHub Actions workflows without local server dependency.

*Data Quality & Hygiene: Enforces relational schemas, timestamps, and metric categorizations (HEAVY_CONGESTION, MODERATE_FLOW, SMOOTH_TRAFFIC).

*Secrets Security: Secures cloud database credentials using encrypted GitHub Repository Secrets (DATABASE_URL).
