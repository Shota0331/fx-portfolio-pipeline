import os
import json
import requests
import pandas as pd
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.dialects.postgresql import insert

load_dotenv()

def fetch_historical_rates(start_date: str, end_date: str, base_currency="USD", symbols="EUR,JPY,GBP"):
    """
    指定した期間・複数通貨のヒストリカル為替レートを取得する関数
    """
    url = f"https://api.frankfurter.dev/v1/{start_date}..{end_date}?base={base_currency}&symbols={symbols}"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching historical rates: {e}")
        raise

def process_historical_rates_to_df(data: dict) -> pd.DataFrame:
    """
    API から返された入れ子の時系列データをフラットな DataFrame に整形する関数
    """
    base_currency = data.get("base", "USD")
    rates_by_date = data.get("rates", {})
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    
    records = []
    for date_str, symbol_dict in rates_by_date.items():
        for target_currency, rate in symbol_dict.items():
            records.append({
                "date": date_str,
                "base_currency": base_currency,
                "target_currency": target_currency,
                "rate": float(rate),
                "ingested_at": now_str
            })
            
    return pd.DataFrame(records)

def save_rates_to_csv(df: pd.DataFrame, output_dir="data/raw"):
    """
    DataFrame を期間指定の CSV ファイルとしてローカルに保存する関数
    """
    if df.empty:
        print("No data to save.")
        return None

    os.makedirs(output_dir, exist_ok=True)
    base = df["base_currency"].iloc[0]
    min_date = df["date"].min()
    max_date = df["date"].max()
    
    file_path = os.path.join(output_dir, f"rates_{base}_historical_{min_date}_{max_date}.csv")
    df.to_csv(file_path, index=False)
    print(f"Saved historical rates to CSV: {file_path} ({len(df)} rows)")
    return file_path

def get_db_engine():
    """
    SQLAlchemy Engine (psycopg3) を生成する関数
    """
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    db = os.getenv("POSTGRES_DB")
    port = os.getenv("POSTGRES_PORT", "5432")
    host = "localhost"

    connection_url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"
    return create_engine(connection_url)

def upsert_rates_to_db(df: pd.DataFrame, table_name="exchange_rates"):
    """
    PostgreSQL の ON CONFLICT を利用して、バルクでべき等性を担保した書き込みを行う関数
    """
    if df.empty:
        return

    engine = get_db_engine()
    metadata = MetaData()
    rates_table = Table(table_name, metadata, autoload_with=engine)

    records = df.to_dict(orient="records")

    stmt = insert(rates_table).values(records)
    upsert_stmt = stmt.on_conflict_do_update(
        index_elements=["date", "base_currency", "target_currency"],
        set_={
            "rate": stmt.excluded.rate,
            "ingested_at": stmt.excluded.ingested_at
        }
    )

    with engine.begin() as conn:
        conn.execute(upsert_stmt)
    
    print(f"Successfully upserted {len(df)} records into '{table_name}'.")

if __name__ == "__main__":
    # 過去180日分（約半年分）のデータを取得する
    end_date_str = date.today().strftime("%Y-%m-%d")
    start_date_str = (date.today() - timedelta(days=180)).strftime("%Y-%m-%d")

    print(f"Fetching rates from {start_date_str} to {end_date_str} for EUR, JPY, GBP...")
    raw_data = fetch_historical_rates(
        start_date=start_date_str,
        end_date=end_date_str,
        base_currency="USD",
        symbols="EUR,JPY,GBP"
    )

    df_rates = process_historical_rates_to_df(raw_data)
    print(f"Processed {len(df_rates)} rows. Preview:")
    print(df_rates.head())

    # CSV 保存 & DB への UPSERT
    save_rates_to_csv(df_rates)
    upsert_rates_to_db(df_rates)