import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine

# 環境変数の読み込み
load_dotenv()

# ページ全体の設定
st.set_page_config(
    page_title="FX Exchange Rate & Moving Averages Dashboard",
    layout="wide"
)

@st.cache_resource
def get_db_engine():
    """
    SQLAlchemy Engine をキャッシュして再利用する関数
    """
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    db = os.getenv("POSTGRES_DB")
    port = os.getenv("POSTGRES_PORT", "5432")
    host = "localhost"

    connection_url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"
    return create_engine(connection_url)

@st.cache_data(ttl=600)
def load_mart_data() -> pd.DataFrame:
    """
    dbt が作成した分析マートテーブルからデータを読み込む関数（10分間キャッシュ）
    """
    engine = get_db_engine()
    query = """
    SELECT
        rate_date,
        base_currency,
        target_currency,
        exchange_rate,
        ma_7_days,
        ma_30_days
    FROM public.fct_exchange_rate_moving_averages
    ORDER BY rate_date ASC
    """
    df = pd.read_sql(query, engine)
    df["rate_date"] = pd.to_datetime(df["rate_date"])
    return df

# --- メイン UI 構築 ---
st.title("📈 FX Exchange Rate & Moving Averages Pipeline")

try:
    df = load_mart_data()
except Exception as e:
    st.error(f"Database connection error: {e}")
    st.stop()

if df.empty:
    st.warning("No data available. Please run the ingestion pipeline and `dbt run` first.")
    st.stop()

# サイドバー：通貨ペアと期間のフィルタリング
st.sidebar.header("Filter Settings")
currencies = sorted(df["target_currency"].unique().tolist())
selected_currency = st.sidebar.selectbox("Target Currency (vs. USD)", currencies, index=currencies.index("JPY") if "JPY" in currencies else 0)

# 選択された通貨でデータを絞り込み
filtered_df = df[df["target_currency"] == selected_currency].sort_values("rate_date")

# 最新日と前日比の KPI メトリクス表示
latest_row = filtered_df.iloc[-1]
prev_row = filtered_df.iloc[-2] if len(filtered_df) >= 2 else latest_row

rate_diff = latest_row["exchange_rate"] - prev_row["exchange_rate"]
ma7_diff = latest_row["exchange_rate"] - latest_row["ma_7_days"]

st.subheader(f"USD / {selected_currency} Summary (As of {latest_row['rate_date'].strftime('%Y-%m-%d')})")

col1, col2, col3 = st.columns(3)
col1.metric(
    label=f"Latest Spot Rate (USD/{selected_currency})",
    value=f"{latest_row['exchange_rate']:,.4f}",
    delta=f"{rate_diff:+.4f} (vs. Previous Day)"
)
col2.metric(
    label="7-Day Moving Average (7d MA)",
    value=f"{latest_row['ma_7_days']:,.4f}",
    delta=f"{ma7_diff:+.4f} (Spread vs. Spot)"
)
col3.metric(
    label="30-Day Moving Average (30d MA)",
    value=f"{latest_row['ma_30_days']:,.4f}"
)

st.divider()

# 時系列折れ線グラフ（実レート vs 7日移動平均 vs 30日移動平均）
st.subheader(f"Time-Series Trend: Spot Rate vs. Moving Averages")

chart_df = filtered_df.set_index("rate_date")[["exchange_rate", "ma_7_days", "ma_30_days"]]
chart_df.columns = ["Spot Rate", "7-Day MA", "30-Day MA"]

st.line_chart(chart_df, height=450)

# データテーブルの詳細表示（折りたたみ式）
with st.expander("View Underlying Mart Table Data"):
    display_df = filtered_df.sort_values("rate_date", ascending=False).copy()
    display_df["rate_date"] = display_df["rate_date"].dt.strftime("%Y-%m-%d")
    st.dataframe(display_df, use_container_width=True, hide_index=True)