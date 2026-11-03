import requests
import json

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

if __name__ == "__main__": #このスクリプトが直接実行された時のみ下の処理を動かし、他のファイルから関数としてインポートされた際には実行されないようにするPythonの標準的な記述
    rates_data = fetch_latest_rates()
    print("Latest Exchange Rates:")
    print(json.dumps(rates_data, indent=2))