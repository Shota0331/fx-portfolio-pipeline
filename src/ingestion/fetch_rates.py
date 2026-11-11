import os
import json
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.dialects.postgresql import insert

# .env ファイルから環境変数を読み込む
load_dotenv()

def fetch_latest_rates(base_currency="USD", target_currency="EUR"):
    """
    指定した通貨ペアの最新レートを取得する関数
    """
    url = f"https://api.frankfurter.dev/v1/latest?base={base_currency}&symbols={target_currency}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching exchange rates: {e}")
        raise

def process_rates_to_df(data):
    """
    取得した JSON データを Pandas DataFrame に整形する関数
    """
    record = {
        "date": data.get("date"),
        "base_currency": data.get("base"),
        "target_currency": list(data.get("rates", {}).keys())[0],
        "rate": list(data.get("rates", {}).values())[0],
        "ingested_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }
    return pd.DataFrame([record])

def save_rates_to_csv(df, output_dir="data/raw"):
    """
    DataFrame を CSV ファイルとしてローカルに保存する関数
    """
    os.makedirs(output_dir, exist_ok=True)
    base = df["base_currency"].iloc[0]
    target = df["target_currency"].iloc[0]
    date_str = df["date"].iloc[0]
    
    file_path = os.path.join(output_dir, f"rates_{base}_{target}_{date_str}.csv")
    df.to_csv(file_path, index=False)
    print(f"Saved exchange rate to CSV: {file_path}")
    return file_path

def get_db_engine():
    """
    .env の環境変数を用いて SQLAlchemy Engine (psycopg3) を生成する関数
    """
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    db = os.getenv("POSTGRES_DB")
    port = os.getenv("POSTGRES_PORT", "5432")
    host = "localhost"

    connection_url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"
    return create_engine(connection_url)

def upsert_rates_to_db(df, table_name="exchange_rates"):
    """
    PostgreSQL の ON CONFLICT 構文を利用して、べき等性を担保した書き込みを行う関数
    """
    engine = get_db_engine()
    metadata = MetaData()
    # 既存のテーブル定義（主キー情報など）を DB から自動読み込み（リフレクション）
    rates_table = Table(table_name, metadata, autoload_with=engine)

    # DataFrame の行を辞書リストに変換
    records = df.to_dict(orient="records")

    # PostgreSQL 固有の INSERT 文を構築
    stmt = insert(rates_table).values(records)

    # 複合主キーが競合した場合、rate と ingested_at を最新の値で上書き更新する (UPSERT)
    upsert_stmt = stmt.on_conflict_do_update(
        index_elements=["date", "base_currency", "target_currency"],
        set_={
            "rate": stmt.excluded.rate,
            "ingested_at": stmt.excluded.ingested_at
        }
    )

    # トランザクションを実行してコミット
    with engine.begin() as conn:
        conn.execute(upsert_stmt)
    
    print(f"Successfully upserted data into PostgreSQL table: '{table_name}'")

if __name__ == "__main__":
    rates_data = fetch_latest_rates()
    df_rates = process_rates_to_df(rates_data)
    save_rates_to_csv(df_rates)
    
    # べき等性を持つ UPSERT 関数を実行
    upsert_rates_to_db(df_rates)