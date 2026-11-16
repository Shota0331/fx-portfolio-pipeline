.PHONY: up down ingest transform test pipeline dashboard clean

# PostgreSQL コンテナの起動
up:
	docker compose up -d

# PostgreSQL コンテナの停止
down:
	docker compose down

# Python データ取得・UPSERT スクリプトの実行（Extract & Load）
ingest:
	.venv/bin/python src/ingestion/fetch_rates.py

# dbt モデルの実行（Transform）
transform:
	set -a && . ./.env && set +a && cd transform && ../.venv/bin/dbt run --profiles-dir .

# dbt データ品質テストの実行
test:
	set -a && . ./.env && set +a && cd transform && ../.venv/bin/dbt test --profiles-dir .

# E2E バッチパイプライン全体の連続実行（DB起動 -> 取得 -> 変換 -> テスト）
pipeline: up ingest transform test
	@echo "✅ Full E2E pipeline completed successfully!"

# Streamlit ダッシュボードの起動
dashboard:
	.venv/bin/streamlit run src/dashboard/app.py

# dbt のビルド成果物とログの削除
clean:
	rm -rf transform/target transform/dbt_packages transform/logs logs