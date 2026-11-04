import requests
import json
import os
import pandas as pd
from datetime import datetime

def fetch_latest_rates(base_currency="EUR", target_currency= "JPY"):
    url = f"https://api.frankfurter.dev/v1/latest?base={base_currency}&symbols={target_currency}"
    try: #エラー（通信切断やサーバーダウン）が起きてもプログラムが不意に落ちないように保護
        response = requests.get(url, timeout=10)
        response.raise_for_status() #レスポンスのHTTPステータスコードが 4xx（クライアントエラー）や 5xx（サーバーエラー）だった場合、自動的に HTTPError を発生させます（成功の200番台なら何もしません）

        data = response.json()
        return data

    except requests.exceptions.RequestException as e:
        print(f"Error fetching exchange rates: {e}")
        raise #ログを出力した後、呼び出し元の処理にもエラーを伝播させるために例外を再送出しています。

def save_rates_to_csv(data, output_dir="data/raw"):
    """
    取得した為替データを Pandas DataFrame に整形し、CSV ファイルとして保存する関数
    """
    # 保存先ディレクトリが存在しない場合は自動作成
    os.makedirs(output_dir, exist_ok=True)

    # 必要なデータを抽出して辞書形式に整理
    record = {
        "date": data.get("date"),
        "base_currency": data.get("base"),
        "target_currency": list(data.get("rates", {}).keys())[0],
        "rate": list(data.get("rates", {}).values())[0],
        "ingested_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }

    # DataFrame に変換
    df = pd.DataFrame([record])

    # ファイル名を決定（例: rates_USD_EUR_2026-11-03.csv）
    file_name = f"rates_{record['base_currency']}_{record['target_currency']}_{record['date']}.csv"
    file_path = os.path.join(output_dir, file_name)

    # CSV として保存（インデックス番号は含めない）
    df.to_csv(file_path, index=False)
    print(f"Saved exchange rate to: {file_path}")
    return file_path

if __name__ == "__main__": #このスクリプトが直接実行された時のみ下の処理を動かし、他のファイルから関数としてインポートされた際には実行されないようにするPythonの標準的な記述
    rates_data = fetch_latest_rates()
    print("Latest Exchange Rates:")
    print(json.dumps(rates_data, indent=2))

    saved_file = save_rates_to_csv(rates_data)

