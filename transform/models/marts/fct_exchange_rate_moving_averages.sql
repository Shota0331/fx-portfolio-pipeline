{{ config(materialized='table') }}

with rates as (
    select * from {{ ref('stg_exchange_rates') }}
),

with_moving_averages as (
    select
        rate_date,
        base_currency,
        target_currency,
        exchange_rate,
        -- 通貨ペアごとに過去 7 営業日の移動平均を計算
        round(
            avg(exchange_rate) over (
                partition by base_currency, target_currency
                order by rate_date
                rows between 6 preceding and current row
            ), 5
        ) as ma_7_days,
        -- 通貨ペアごとに過去 30 営業日の移動平均を計算
        round(
            avg(exchange_rate) over (
                partition by base_currency, target_currency
                order by rate_date
                rows between 29 preceding and current row
            ), 5
        ) as ma_30_days
    from rates
)

select * from with_moving_averages
order by target_currency, rate_date desc