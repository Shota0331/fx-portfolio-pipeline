
# FX Exchange Rate Pipeline

An end-to-end ELT pipeline that extracts daily exchange rates from the Frankfurter API, loads them into PostgreSQL, builds 7-day and 30-day moving average models with dbt, and visualizes the trends on a Streamlit dashboard.

## Tech Stack
- **Languages**: Python, SQL
- **Orchestration / Automation**: GNU Make
- **Data Warehouse / Storage**: PostgreSQL
- **Data Transformation & Testing**: dbt
- **Visualization / UI**: Streamlit
- **Infrastructure & Containerization**: Docker, Docker Compose
- **Version Control**: Git, GitHub

## Architecture

Frankfurter API -> Python (Ingestion) -> PostgreSQL -> dbt (Staging & Mart) -> Streamlit

<img width="1437" height="833" alt="スクリーンショット 2026-11-16 23 22 23" src="https://github.com/user-attachments/assets/e4cec577-a6e2-41ea-a5d4-75c1490429a8" />
