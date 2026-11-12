{{ config(materialized='view') }}

with source as (
    select * from {{ source('public', 'exchange_rates') }}
),

renamed as (
    select
        cast(date as date) as rate_date,
        cast(base_currency as varchar(3)) as base_currency,
        cast(target_currency as varchar(3)) as target_currency,
        cast(rate as numeric(12, 6)) as exchange_rate,
        cast(ingested_at as timestamp) as ingested_at
    from source
)

select * from renamed