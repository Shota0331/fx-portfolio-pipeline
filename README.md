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
